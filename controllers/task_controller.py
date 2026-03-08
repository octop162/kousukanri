from datetime import datetime, date

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
        self._tasks_by_date: dict[date, dict[str, Task]] = {}
        self._current_date: date = date.today()
        self._projects: dict[str, Project] = {}
        self._list_view = None
        self._project_list_view = None
        self._timer_widget = None
        self._date_nav_widget = None
        self._routine_view = None
        self._export_view = None

        # Timer state
        self._running_task_id: str | None = None
        self._running_task_date: date | None = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_timer_tick)

        scene.task_created.connect(self._on_task_created)
        scene.task_changed.connect(self._on_task_changed)
        scene.task_deleted.connect(self._on_task_deleted)

    @property
    def _tasks(self) -> dict[str, Task]:
        return self._tasks_by_date.setdefault(self._current_date, {})

    def _tasks_for_date(self, d: date) -> dict[str, Task]:
        return self._tasks_by_date.setdefault(d, {})

    def set_list_view(self, list_view):
        """Connect a TaskListView for bidirectional sync."""
        self._list_view = list_view
        list_view.task_edited.connect(self._on_task_edited)
        list_view.task_delete_requested.connect(self._on_list_delete_requested)
        list_view.task_start_requested.connect(self._on_list_start_requested)

    def set_project_list_view(self, project_list_view):
        """Connect a ProjectListView for project CRUD."""
        self._project_list_view = project_list_view
        project_list_view.project_created.connect(self._on_project_created)
        project_list_view.project_changed.connect(self._on_project_changed)
        project_list_view.project_deleted.connect(self._on_project_deleted)
        project_list_view.project_order_changed.connect(self._on_project_order_changed)

    def set_timer_widget(self, timer_widget):
        """Connect a TimerWidget for start/stop timer."""
        self._timer_widget = timer_widget
        timer_widget.timer_started.connect(self._on_timer_started)
        timer_widget.timer_stopped.connect(self._on_timer_stopped)
        timer_widget.timer_name_changed.connect(self._on_timer_name_changed)
        timer_widget.timer_project_changed.connect(self._on_timer_project_changed)
        timer_widget.task_add_requested.connect(self._on_task_add_requested)

    def set_date_nav_widget(self, date_nav_widget):
        """Connect a DateNavWidget for date navigation."""
        self._date_nav_widget = date_nav_widget
        date_nav_widget.date_requested.connect(self._on_date_requested)

    def set_routine_view(self, routine_view):
        """Connect a RoutineView for one-click task creation."""
        self._routine_view = routine_view
        routine_view.task_add_requested.connect(self._on_task_add_requested)

    def set_export_view(self, export_view):
        """Connect an ExportView for text export."""
        self._export_view = export_view
        self._refresh_export_view()

    def _refresh_export_view(self):
        """Push current tasks and projects to the export view."""
        if self._export_view is None:
            return
        self._export_view.update_tasks(
            list(self._tasks.values()),
            self._sorted_projects(),
            self._current_date,
        )

    # ── Date navigation ────────────────────────────────────────

    def _on_date_requested(self, new_date):
        """Handle date change request from DateNavWidget."""
        if isinstance(new_date, datetime):
            new_date = new_date.date()
        self.change_date(new_date)

    def change_date(self, new_date: date):
        """Switch to a different date, reloading views."""
        if new_date == self._current_date:
            return
        self._current_date = new_date
        self._reload_views_for_date()

    def _reload_views_for_date(self):
        """Clear and repopulate scene and list for the current date."""
        ref = datetime(self._current_date.year, self._current_date.month, self._current_date.day)

        # Update scene
        self._scene.clear_task_blocks()
        self._scene.set_reference_date(ref)
        for task in self._tasks.values():
            self._scene.add_task_block(task)

        # Update list view
        if self._list_view is not None:
            self._list_view.set_tasks(list(self._tasks.values()))

        # Update date nav widget label
        if self._date_nav_widget is not None:
            self._date_nav_widget.set_date(self._current_date)

        # Update timer widget display date
        if self._timer_widget is not None:
            self._timer_widget.set_display_date(self._current_date)

        # Update routine view display date
        if self._routine_view is not None:
            self._routine_view.set_display_date(self._current_date)

        self._refresh_export_view()

    # ── Timer handlers ─────────────────────────────────────────

    def _on_timer_started(self, name: str, project_id: str):
        now = datetime.now().replace(microsecond=0)
        end = now  # will grow each tick

        pid = project_id if project_id else None
        project = self._projects.get(pid) if pid else None
        color = project.color if project else DEFAULT_BLOCK_COLOR

        task = Task(
            name=name, start_time=now, end_time=end,
            color=color, project_id=pid,
        )
        # Store task in the current display date's bucket
        self._running_task_date = self._current_date
        self._tasks[task.id] = task
        self._scene.add_task_block(task)
        if self._list_view is not None:
            self._list_view.add_task(task)
        if self._timer_widget is not None:
            self._timer_widget.add_task_to_history(task)

        self._running_task_id = task.id
        self._tick_timer.start()

    def _on_timer_tick(self):
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is None:
            return
        task.end_time = datetime.now().replace(microsecond=0)
        # Only update views if we're viewing the same date as the running task
        if task_date == self._current_date:
            self._scene.update_task_block(task)
            if self._list_view is not None:
                self._list_view.update_task(task)

    def _on_timer_stopped(self):
        self._tick_timer.stop()
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is not None:
            task.end_time = datetime.now().replace(microsecond=0)
            # Ensure end > start
            if task.end_time <= task.start_time:
                from datetime import timedelta
                task.end_time = task.start_time + timedelta(seconds=1)
            if task_date == self._current_date:
                self._scene.update_task_block(task)
                if self._list_view is not None:
                    self._list_view.update_task(task)
        self._running_task_id = None
        self._running_task_date = None

    def _on_timer_name_changed(self, name: str):
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is None:
            return
        task.name = name or "あたらしいタスク"
        if task_date == self._current_date:
            self._scene.update_task_block(task)
            if self._list_view is not None:
                self._list_view.update_task(task)

    def _on_timer_project_changed(self, project_id: str):
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is None:
            return
        pid = project_id if project_id else None
        project = self._projects.get(pid) if pid else None
        task.project_id = pid
        task.color = project.color if project else DEFAULT_BLOCK_COLOR
        if task_date == self._current_date:
            self._scene.update_task_block(task)
            if self._list_view is not None:
                self._list_view.update_task(task)

    # ── signal handler (from timer add button) ─────────────────

    def _on_task_add_requested(self, task: Task):
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
        if self._timer_widget is not None:
            self._timer_widget.add_task_to_history(task)
        self._refresh_export_view()

    # ── signal handlers (from timeline) ────────────────────────

    def _on_task_created(self, task: Task):
        self._tasks[task.id] = task
        if self._db is not None:
            self._db.insert_task(task)
        if self._list_view is not None:
            self._list_view.add_task(task)
        if self._timer_widget is not None:
            self._timer_widget.add_task_to_history(task)
        self._refresh_export_view()

    def _on_task_changed(self, task: Task):
        self._tasks[task.id] = task
        if self._db is not None:
            self._db.update_task(task)
        if self._list_view is not None:
            self._list_view.update_task(task)
        self._refresh_export_view()

    def _on_task_deleted(self, task_id: str):
        # Guard: if the running task is deleted, stop the timer
        if self._running_task_id == task_id:
            self._tick_timer.stop()
            self._running_task_id = None
            self._running_task_date = None
            if self._timer_widget is not None:
                self._timer_widget.force_stop()

        self._tasks.pop(task_id, None)
        if self._db is not None:
            self._db.delete_task(task_id)
        if self._list_view is not None:
            self._list_view.remove_task(task_id)
        self._refresh_export_view()

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

    # ── signal handlers (from list view) ────────────────────────

    def _on_task_edited(self, task: Task):
        self._tasks[task.id] = task
        self._scene.update_task_block(task)

    def _on_list_start_requested(self, name: str, project_id: str):
        """Start timer with given name and project from list view."""
        if self._timer_widget is None:
            return
        # If already running, stop first
        if self._running_task_id is not None:
            self._timer_widget.force_stop()
            self._on_timer_stopped()
        # Fill timer widget and start
        self._timer_widget.set_and_start(name, project_id)

    def _on_list_delete_requested(self, task_id: str):
        """Delete a task initiated from the list view."""
        self._on_task_deleted(task_id)
        # Also remove the block from the scene
        for block in self._scene._get_blocks():
            if block.task.id == task_id:
                self._scene.removeItem(block)
                break

    # ── project signal handlers ────────────────────────────────

    def _sorted_projects(self) -> list[Project]:
        return sorted(self._projects.values(), key=lambda p: p.order)

    def _sync_projects_to_views(self):
        """Push current project list to all views that need it."""
        projects = self._sorted_projects()
        self._scene.set_projects(projects)
        if self._list_view is not None:
            self._list_view.update_project_list(projects)
        if self._timer_widget is not None:
            self._timer_widget.update_project_list(projects)
        if self._routine_view is not None:
            self._routine_view.update_project_list(projects)

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

    def _on_project_order_changed(self, projects: list):
        """Update project order after D&D reorder."""
        for p in projects:
            if p.id in self._projects:
                self._projects[p.id].order = p.order
        self._sync_projects_to_views()

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
