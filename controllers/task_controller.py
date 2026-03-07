from datetime import datetime

from PySide6.QtCore import QObject, QTimer

from models.task import Task
from models.project import Project
from views.timeline_scene import TimelineScene
from utils.constants import DEFAULT_BLOCK_COLOR, SNAP_MINUTES


class TaskController(QObject):
    """Mediates between the TimelineScene and the data layer (in-memory or DB)."""

    def __init__(self, scene: TimelineScene, database=None, parent=None):
        super().__init__(parent)
        self._scene = scene
        self._db = database
        self._tasks: dict[str, Task] = {}
        self._projects: dict[str, Project] = {}
        self._list_view = None
        self._project_list_view = None
        self._timer_widget = None

        # Timer state
        self._running_task_id: str | None = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_timer_tick)

        scene.task_created.connect(self._on_task_created)
        scene.task_changed.connect(self._on_task_changed)
        scene.task_deleted.connect(self._on_task_deleted)

    def set_list_view(self, list_view):
        """Connect a TaskListView for bidirectional sync."""
        self._list_view = list_view
        list_view.task_add_requested.connect(self._on_list_add_requested)
        list_view.task_project_changed.connect(self._on_task_project_changed)

    def set_project_list_view(self, project_list_view):
        """Connect a ProjectListView for project CRUD."""
        self._project_list_view = project_list_view
        project_list_view.project_created.connect(self._on_project_created)
        project_list_view.project_changed.connect(self._on_project_changed)
        project_list_view.project_deleted.connect(self._on_project_deleted)

    def set_timer_widget(self, timer_widget):
        """Connect a TimerWidget for start/stop timer."""
        self._timer_widget = timer_widget
        timer_widget.timer_started.connect(self._on_timer_started)
        timer_widget.timer_stopped.connect(self._on_timer_stopped)
        timer_widget.timer_name_changed.connect(self._on_timer_name_changed)
        timer_widget.timer_project_changed.connect(self._on_timer_project_changed)

    # ── Timer handlers ─────────────────────────────────────────

    def _on_timer_started(self, name: str, project_id: str):
        now = datetime.now().replace(second=0, microsecond=0)
        # Snap start to 5-min
        now = now.replace(minute=(now.minute // SNAP_MINUTES) * SNAP_MINUTES)
        end = now  # will grow each tick

        pid = project_id if project_id else None
        project = self._projects.get(pid) if pid else None
        color = project.color if project else DEFAULT_BLOCK_COLOR

        task = Task(
            name=name, start_time=now, end_time=end,
            color=color, project_id=pid,
        )
        self._tasks[task.id] = task
        self._scene.add_task_block(task)
        if self._list_view is not None:
            self._list_view.add_task(task)

        self._running_task_id = task.id
        self._tick_timer.start()

    def _on_timer_tick(self):
        if self._running_task_id is None:
            return
        task = self._tasks.get(self._running_task_id)
        if task is None:
            return
        task.end_time = datetime.now().replace(second=0, microsecond=0)
        self._scene.update_task_block(task)
        if self._list_view is not None:
            self._list_view.update_task(task)

    def _on_timer_stopped(self):
        self._tick_timer.stop()
        if self._running_task_id is None:
            return
        task = self._tasks.get(self._running_task_id)
        if task is not None:
            # Snap end_time to 5-min
            now = datetime.now().replace(second=0, microsecond=0)
            minute_snapped = round(now.minute / SNAP_MINUTES) * SNAP_MINUTES
            if minute_snapped >= 60:
                from datetime import timedelta
                task.end_time = now.replace(minute=0) + timedelta(hours=1)
            else:
                task.end_time = now.replace(minute=minute_snapped)
            # Ensure end > start
            if task.end_time <= task.start_time:
                from datetime import timedelta
                task.end_time = task.start_time + timedelta(minutes=SNAP_MINUTES)
            self._scene.update_task_block(task)
            if self._list_view is not None:
                self._list_view.update_task(task)
        self._running_task_id = None

    def _on_timer_name_changed(self, name: str):
        if self._running_task_id is None:
            return
        task = self._tasks.get(self._running_task_id)
        if task is None:
            return
        task.name = name or "New Task"
        self._scene.update_task_block(task)
        if self._list_view is not None:
            self._list_view.update_task(task)

    def _on_timer_project_changed(self, project_id: str):
        if self._running_task_id is None:
            return
        task = self._tasks.get(self._running_task_id)
        if task is None:
            return
        pid = project_id if project_id else None
        project = self._projects.get(pid) if pid else None
        task.project_id = pid
        task.color = project.color if project else DEFAULT_BLOCK_COLOR
        self._scene.update_task_block(task)
        if self._list_view is not None:
            self._list_view.update_task(task)

    # ── signal handlers (from timeline) ────────────────────────

    def _on_task_created(self, task: Task):
        self._tasks[task.id] = task
        if self._db is not None:
            self._db.insert_task(task)
        if self._list_view is not None:
            self._list_view.add_task(task)

    def _on_task_changed(self, task: Task):
        self._tasks[task.id] = task
        if self._db is not None:
            self._db.update_task(task)
        if self._list_view is not None:
            self._list_view.update_task(task)

    def _on_task_deleted(self, task_id: str):
        # Guard: if the running task is deleted, stop the timer
        if self._running_task_id == task_id:
            self._tick_timer.stop()
            self._running_task_id = None
            if self._timer_widget is not None:
                self._timer_widget.force_stop()

        self._tasks.pop(task_id, None)
        if self._db is not None:
            self._db.delete_task(task_id)
        if self._list_view is not None:
            self._list_view.remove_task(task_id)

    # ── signal handler (from list view) ────────────────────────

    def _on_list_add_requested(self, task: Task):
        # Resolve overlaps before adding
        result = self._scene.resolve_overlap(task.start_time, task.end_time)
        if result is None:
            return
        task.start_time, task.end_time = result
        self._tasks[task.id] = task
        self._scene.add_task_block(task)
        if self._db is not None:
            self._db.insert_task(task)
        if self._list_view is not None:
            self._list_view.add_task(task)

    # ── signal handler (from list view: project change) ────────

    def _on_task_project_changed(self, task: Task):
        self._tasks[task.id] = task
        self._scene.update_task_block(task)

    # ── project signal handlers ────────────────────────────────

    def _sync_projects_to_views(self):
        """Push current project list to all views that need it."""
        projects = list(self._projects.values())
        self._scene.set_projects(projects)
        if self._list_view is not None:
            self._list_view.update_project_list(projects)
        if self._timer_widget is not None:
            self._timer_widget.update_project_list(projects)

    def _on_project_created(self, project: Project):
        self._projects[project.id] = project
        if self._project_list_view is not None:
            self._project_list_view.add_project(project)
        self._sync_projects_to_views()

    def _on_project_changed(self, project: Project):
        self._projects[project.id] = project
        if self._project_list_view is not None:
            self._project_list_view.update_project(project)
        self._sync_projects_to_views()
        # Update colors of all tasks belonging to this project
        for task in self._tasks.values():
            if task.project_id == project.id:
                task.color = project.color
                self._scene.update_task_block(task)
                if self._list_view is not None:
                    self._list_view.update_task(task)

    def _on_project_deleted(self, project_id: str):
        self._projects.pop(project_id, None)
        if self._project_list_view is not None:
            self._project_list_view.remove_project(project_id)
        self._sync_projects_to_views()
        # Detach tasks from deleted project (keep color as-is)
        for task in self._tasks.values():
            if task.project_id == project_id:
                task.project_id = None

    # ── DB loading ────────────────────────────────────────────

    def load_tasks(self, date=None):
        """Load tasks from DB and add them to the scene."""
        if self._db is None:
            return
        tasks = self._db.get_tasks_for_date(date)
        for task in tasks:
            self._tasks[task.id] = task
            self._scene.add_task_block(task)
            if self._list_view is not None:
                self._list_view.add_task(task)
