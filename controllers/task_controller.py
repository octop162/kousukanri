from dataclasses import dataclass as dc, replace
from datetime import datetime, date

from PySide6.QtCore import QObject, QTimer

from models.task import Task
from models.project import Project
from models.routine import Routine
from views.timeline_scene import TimelineScene
from utils.constants import DEFAULT_BLOCK_COLOR, SNAP_MINUTES


@dc
class UndoAction:
    """1レベルUndoのためのスナップショット。
    snapshots は (操作前, 操作後) のペアリスト。
    - 挿入: (None, after)  → Undoで削除
    - 更新: (before, after) → Undoでbeforeに戻す
    - 削除: (before, None)  → Undoで再挿入
    """
    kind: str              # "task_insert" | "task_update" | "task_delete" | "task_bulk_update" |
                           # "project_insert" | "project_update" | "project_delete" | "project_bulk_update" |
                           # "routine_insert" | "routine_update" | "routine_delete"
    snapshots: list        # [(before: T|None, after: T|None), ...]
    affected_date: date | None = None


class TaskController(QObject):
    """View ↔ Model/DB の仲介役。
    各ビューからのシグナルを受け取り、インメモリキャッシュとDBを更新し、
    関連ビューに変更を通知する。タイマー管理・日付切替・Undoもここで行う。
    """

    def __init__(self, scene: TimelineScene, database=None, parent=None):
        super().__init__(parent)
        self._scene = scene
        self._db = database
        # 日付ごとのタスクキャッシュ。表示済み日付のみロードされる（遅延ロード）
        self._tasks_by_date: dict[date, dict[str, Task]] = {}
        self._current_date: date = date.today()
        self._projects: dict[str, Project] = {}
        self._list_view = None
        self._project_list_view = None
        self._timer_widget = None
        self._date_nav_widget = None
        self._routine_view = None
        self._export_view = None
        self._report_view = None
        self._routines: list[Routine] = []

        # 直前の操作1つだけ保持。Undo実行後はNoneになり2回目は無効
        self._last_action: UndoAction | None = None

        # タイマー計測中のタスクID。Noneなら計測していない
        self._running_task_id: str | None = None
        # タイマー開始時の日付（日跨ぎ対応用）
        self._running_task_date: date | None = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_timer_tick)

        scene.task_created.connect(self._on_task_created)
        scene.task_changed.connect(self._on_task_changed)
        scene.task_deleted.connect(self._on_task_deleted)

    @property
    def _tasks(self) -> dict[str, Task]:
        """現在表示中の日付のタスク辞書を返す。未作成なら空dictを自動生成。"""
        return self._tasks_by_date.setdefault(self._current_date, {})

    def _tasks_for_date(self, d: date) -> dict[str, Task]:
        return self._tasks_by_date.setdefault(d, {})

    def set_list_view(self, list_view):
        """Connect a TaskListView for bidirectional sync."""
        self._list_view = list_view
        list_view.task_edited.connect(self._on_task_edited)
        list_view.tasks_bulk_edited.connect(self._on_tasks_bulk_edited)
        list_view.task_delete_requested.connect(self._on_list_delete_requested)
        list_view.task_start_requested.connect(self._on_list_start_requested)
        list_view.task_apply_all_requested.connect(self._on_task_apply_all)

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
        routine_view.routine_created.connect(self._on_routine_created)
        routine_view.routine_changed.connect(self._on_routine_changed)
        routine_view.routine_deleted.connect(self._on_routine_deleted)
        routine_view.routine_order_changed.connect(self._on_routine_order_changed)

    def set_export_view(self, export_view):
        """Connect an ExportView for text export."""
        self._export_view = export_view
        self._refresh_export_view()

    def set_report_view(self, report_view):
        """Connect a ReportView for daily report."""
        self._report_view = report_view
        self._refresh_report_view()

    def _refresh_export_view(self):
        """Push current tasks and projects to the export view and report view."""
        if self._export_view is not None:
            self._export_view.update_tasks(
                list(self._tasks.values()),
                self._sorted_projects(),
                self._current_date,
            )
        self._refresh_report_view()

    def _refresh_report_view(self):
        """Push current tasks and projects to the report view."""
        if self._report_view is None:
            return
        self._report_view.update_tasks(
            list(self._tasks.values()),
            self._sorted_projects(),
            self._current_date,
        )

    # ── Undo ──────────────────────────────────────────────────

    def _record_undo(self, kind, snapshots, affected_date=None):
        self._last_action = UndoAction(kind, snapshots, affected_date)

    def undo(self) -> bool:
        if self._last_action is None:
            return False
        if self._running_task_id is not None:
            return False  # タイマー実行中はundo禁止

        action = self._last_action
        self._last_action = None

        for before, after in action.snapshots:
            if action.kind.startswith("task_"):
                self._undo_task(before, after)
            elif action.kind.startswith("project_"):
                self._undo_project(before, after)
            elif action.kind.startswith("routine_"):
                self._undo_routine(before, after)

        # ビュー再描画
        self._reload_views_for_date()
        if action.kind.startswith("project_"):
            self._sync_projects_to_views()
            if self._project_list_view:
                self._project_list_view.set_projects(self._sorted_projects())
        if action.kind.startswith("routine_"):
            if self._routine_view:
                self._routine_view.set_routines(self._routines)
        return True

    def _undo_task(self, before, after):
        """Reverse a single task snapshot: insert→delete, update→revert, delete→re-insert."""
        if before is None and after is not None:
            # Was an insert → delete it
            task_date = after.start_time.date()
            tasks = self._tasks_for_date(task_date)
            tasks.pop(after.id, None)
            if self._db is not None:
                self._db.delete_task(after.id)
        elif before is not None and after is not None:
            # Was an update → revert to before
            task_date = before.start_time.date()
            tasks = self._tasks_for_date(task_date)
            tasks[before.id] = replace(before)
            if self._db is not None:
                self._db.update_task(before)
        elif before is not None and after is None:
            # Was a delete → re-insert
            task_date = before.start_time.date()
            tasks = self._tasks_for_date(task_date)
            tasks[before.id] = replace(before)
            if self._db is not None:
                self._db.insert_task(before)

    def _undo_project(self, before, after):
        """Reverse a single project snapshot."""
        if before is None and after is not None:
            # Was an insert → delete
            self._projects.pop(after.id, None)
            if self._db is not None:
                self._db.delete_project(after.id)
        elif before is not None and after is not None:
            # Was an update → revert
            self._projects[before.id] = replace(before)
            if self._db is not None:
                self._db.update_project(before)
        elif before is not None and after is None:
            # Was a delete → re-insert
            self._projects[before.id] = replace(before)
            if self._db is not None:
                self._db.insert_project(before)

    def _undo_routine(self, before, after):
        """Reverse a single routine snapshot."""
        if before is None and after is not None:
            # Was an insert → delete
            self._routines = [r for r in self._routines if r.id != after.id]
            if self._db is not None:
                self._db.delete_routine(after.id)
        elif before is not None and after is not None:
            # Was an update → revert to before
            for i, r in enumerate(self._routines):
                if r.id == before.id:
                    self._routines[i] = replace(before)
                    break
            if self._db is not None:
                self._db.update_routine(before)
        elif before is not None and after is None:
            # Was a delete → re-insert
            self._routines.append(replace(before))
            if self._db is not None:
                self._db.insert_routine(before)

    def stop_running_timer(self):
        """アプリ終了時に計測中タスクを停止してDBに保存する。"""
        if self._running_task_id is not None:
            if self._timer_widget is not None:
                self._timer_widget.force_stop()
            self._on_timer_stopped()

    def is_idle(self) -> bool:
        """Return True if no timer is running and no task covers current time."""
        if self._running_task_id is not None:
            return False
        now = datetime.now()
        today = now.date()
        tasks = self._tasks_by_date.get(today, {})
        for task in tasks.values():
            if task.start_time <= now <= task.end_time:
                return False
        return True

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
        # Lazy-load from DB if this date hasn't been loaded yet
        if self._db is not None and self._current_date not in self._tasks_by_date:
            date_str = self._current_date.isoformat()
            for task in self._db.get_tasks_for_date(date_str):
                self._tasks[task.id] = task

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
        today = date.today()
        if self._current_date != today:
            self.change_date(today)

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
            self._list_view.add_task(task, timing=True)
        if self._timer_widget is not None:
            self._timer_widget.add_task_to_history(task)

        self._running_task_id = task.id
        if self._db is not None:
            self._db.insert_task(task)
        self._record_undo("task_insert", [(None, replace(task))])
        self._tick_timer.start()

    def _on_timer_tick(self):
        """毎秒呼ばれ、計測中タスクの end_time を現在時刻に伸ばす。
        DB書き込みは行わない（stop時のみ書く）。
        """
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is None:
            return
        task.end_time = datetime.now().replace(microsecond=0)
        # 別の日付を表示中ならUI更新をスキップ（タスク自体はバックグラウンドで伸び続ける）
        if task_date == self._current_date:
            self._scene.update_task_block(task)
            # リストは計測終了時のみ更新（tick 中は操作を妨げない）

    def _on_timer_stopped(self):
        self._tick_timer.stop()
        if self._running_task_id is None:
            return
        task_date = self._running_task_date or self._current_date
        tasks = self._tasks_for_date(task_date)
        task = tasks.get(self._running_task_id)
        if task is not None:
            old_snapshot = replace(task)
            task.end_time = datetime.now().replace(microsecond=0)
            # Ensure end > start
            if task.end_time <= task.start_time:
                from datetime import timedelta
                task.end_time = task.start_time + timedelta(seconds=1)
            if self._db is not None:
                self._db.update_task(task)
            if task_date == self._current_date:
                self._scene.update_task_block(task)
                if self._list_view is not None:
                    self._list_view.stop_timing()
                    self._list_view.update_task(task)
            self._record_undo("task_update", [(old_snapshot, replace(task))])
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
        self._record_undo("task_insert", [(None, replace(task))])
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
        self._record_undo("task_insert", [(None, replace(task))])
        self._refresh_export_view()

    def _on_task_changed(self, task: Task):
        # Sceneから届く task は既に変更済みなので、Undo用にキャッシュから変更前を取得
        old = self._tasks.get(task.id)
        old_snapshot = replace(old) if old is not None else None
        self._tasks[task.id] = task
        if self._db is not None:
            self._db.update_task(task)
        if self._list_view is not None:
            self._list_view.update_task(task)
        self._record_undo("task_update", [(old_snapshot, replace(task))])
        self._refresh_export_view()

    def _on_task_deleted(self, task_id: str):
        # Guard: if the running task is deleted, stop the timer
        if self._running_task_id == task_id:
            self._tick_timer.stop()
            self._running_task_id = None
            self._running_task_date = None
            if self._timer_widget is not None:
                self._timer_widget.force_stop()

        deleted = self._tasks.pop(task_id, None)
        if deleted is not None:
            self._record_undo("task_delete", [(replace(deleted), None)])
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
        old = self._tasks.get(task.id)
        old_snapshot = replace(old) if old is not None else None
        self._tasks[task.id] = task
        self._scene.update_task_block(task)
        if self._db is not None:
            self._db.update_task(task)
        # 計測中タスクの開始時間が変わったらタイマー表示を同期
        if task.id == self._running_task_id and self._timer_widget is not None:
            self._timer_widget.update_start_time(task.start_time)
        self._record_undo("task_update", [(old_snapshot, replace(task))])
        self._refresh_export_view()

    def _on_task_apply_all(self, orig_name: str, orig_project_id: str,
                            new_name: str, new_project_id: str):
        """Apply name/project changes to all tasks matching original name+project."""
        if self._db is None:
            return
        orig_pid = orig_project_id or None
        new_pid = new_project_id or None
        project = self._projects.get(new_pid) if new_pid else None
        new_color = project.color if project else DEFAULT_BLOCK_COLOR

        # Get all matching tasks from DB (excluding the one already edited by _on_task_edited)
        matching = self._db.get_tasks_by_name_and_project(orig_name, orig_pid)

        snapshots = []
        updated = []
        for task in matching:
            old_snapshot = replace(task)
            task.name = new_name
            task.project_id = new_pid
            task.color = new_color
            updated.append(task)
            snapshots.append((old_snapshot, replace(task)))

        if not updated:
            return

        self._db.bulk_update_tasks(updated)
        self._record_undo("task_bulk_update", snapshots)

        # Update in-memory cache and views for tasks on currently loaded dates
        for task in updated:
            task_date = task.start_time.date()
            if task_date in self._tasks_by_date:
                cached = self._tasks_by_date[task_date].get(task.id)
                if cached is not None:
                    cached.name = new_name
                    cached.project_id = new_pid
                    cached.color = new_color

        # Refresh current date views
        for task in self._tasks.values():
            if task.name == new_name and task.project_id == new_pid:
                self._scene.update_task_block(task)
        if self._list_view is not None:
            self._list_view.set_tasks(list(self._tasks.values()))
        self._refresh_export_view()

    def _on_tasks_bulk_edited(self, tasks: list):
        snapshots = []
        for task in tasks:
            old = self._tasks.get(task.id)
            old_snapshot = replace(old) if old is not None else None
            self._tasks[task.id] = task
            self._scene.update_task_block(task)
            if self._db is not None:
                self._db.update_task(task)
            snapshots.append((old_snapshot, replace(task)))
        self._record_undo("task_bulk_update", snapshots)
        self._refresh_export_view()

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
        """リストビューからの削除要求。タイムラインのブロックも手動で除去する。
        （Sceneからの削除は scene.task_deleted 経由ではないため、ブロック除去が自動で走らない）
        """
        self._on_task_deleted(task_id)
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
        if self._db is not None:
            self._db.insert_project(project)
        if self._project_list_view is not None:
            self._project_list_view.add_project(project)
        self._sync_projects_to_views()
        self._record_undo("project_insert", [(None, replace(project))])

    def _on_project_changed(self, project: Project):
        old = self._projects.get(project.id)
        old_snapshot = replace(old) if old is not None else None
        self._projects[project.id] = project
        if self._db is not None:
            self._db.update_project(project)
        if self._project_list_view is not None:
            self._project_list_view.update_project(project)
        self._sync_projects_to_views()
        self._record_undo("project_update", [(old_snapshot, replace(project))])
        # Update colors of all tasks belonging to this project
        for task in self._tasks.values():
            if task.project_id == project.id:
                task.color = project.color
                self._scene.update_task_block(task)
                if self._list_view is not None:
                    self._list_view.update_task(task)

    def _on_project_order_changed(self, projects: list):
        """Update project order after D&D reorder."""
        snapshots = []
        for p in projects:
            if p.id in self._projects:
                old_snapshot = replace(self._projects[p.id])
                self._projects[p.id].order = p.order
                if self._db is not None:
                    self._db.update_project(self._projects[p.id])
                snapshots.append((old_snapshot, replace(self._projects[p.id])))
        self._sync_projects_to_views()
        if snapshots:
            self._record_undo("project_bulk_update", snapshots)

    def _on_project_deleted(self, project_id: str):
        deleted = self._projects.pop(project_id, None)
        if self._db is not None:
            self._db.delete_project(project_id)
        if self._project_list_view is not None:
            self._project_list_view.remove_project(project_id)
        self._sync_projects_to_views()
        # 削除されたプロジェクトに紐づくタスクのproject_idをNullに。
        # 色はそのまま残す（見た目が急に変わるのを防ぐ）
        for task in self._tasks.values():
            if task.project_id == project_id:
                task.project_id = None
        if deleted is not None:
            self._record_undo("project_delete", [(replace(deleted), None)])

    # ── routine signal handlers ────────────────────────────────

    def _on_routine_created(self, routine: Routine):
        self._routines.append(routine)
        if self._db is not None:
            self._db.insert_routine(routine)
        self._record_undo("routine_insert", [(None, replace(routine))])

    def _on_routine_changed(self, routine: Routine):
        old_snapshot = None
        for i, r in enumerate(self._routines):
            if r.id == routine.id:
                old_snapshot = replace(r)
                self._routines[i] = routine
                break
        if self._db is not None:
            self._db.update_routine(routine)
        self._record_undo("routine_update", [(old_snapshot, replace(routine))])

    def _on_routine_order_changed(self, routines: list):
        self._routines = routines
        if self._db is not None:
            self._db.update_routine_orders(routines)

    def _on_routine_deleted(self, routine_id: str):
        deleted = None
        for r in self._routines:
            if r.id == routine_id:
                deleted = replace(r)
                break
        self._routines = [r for r in self._routines if r.id != routine_id]
        if self._db is not None:
            self._db.delete_routine(routine_id)
        if deleted is not None:
            self._record_undo("routine_delete", [(deleted, None)])

    # ── DB loading ────────────────────────────────────────────

    def load_from_db(self):
        """Load all data from DB on startup: projects → tasks → routines."""
        if self._db is None:
            return

        # Projects
        for project in self._db.get_all_projects():
            self._projects[project.id] = project
        self._sync_projects_to_views()
        if self._project_list_view is not None:
            for project in self._sorted_projects():
                self._project_list_view.add_project(project)

        # Tasks for current date
        date_str = self._current_date.isoformat()
        for task in self._db.get_tasks_for_date(date_str):
            self._tasks[task.id] = task
            self._scene.add_task_block(task)
            if self._list_view is not None:
                self._list_view.add_task(task)
            if self._timer_widget is not None:
                self._timer_widget.add_task_to_history(task)

        # Routines
        self._routines = self._db.get_all_routines()
        if self._routine_view is not None:
            self._routine_view.set_routines(self._routines)

        self._refresh_export_view()
