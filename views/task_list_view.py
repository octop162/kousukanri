from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QBrush

from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR


class TaskListView(QWidget):
    """Task list table (no add form — that's in TaskInputWidget now)."""

    task_edited = Signal(Task)
    tasks_bulk_edited = Signal(list)  # list of Task
    task_delete_requested = Signal(str)  # task id
    task_start_requested = Signal(str, str)  # (name, project_id)
    task_apply_all_requested = Signal(str, str, str, str)  # (orig_name, orig_project_id, new_name, new_project_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: list[Task] = []
        self._projects: list[Project] = []
        self._timing_task_id: str | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["", "タスク名", "開始", "終了", "所要時間", "プロジェクト"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 100)

        # Keep cell background colors visible when selected
        self._table.setStyleSheet(
            "QTableWidget::item:selected { background: rgba(38, 79, 120, 100); }"
        )

        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.doubleClicked.connect(self._on_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._table)

    # ── Cell click (start button) ──

    def _on_cell_clicked(self, row: int, col: int):
        if col == 0 and 0 <= row < len(self._tasks):
            task = self._tasks[row]
            self.task_start_requested.emit(task.name, task.project_id or "")

    # ── Context menu (right-click) ──

    def _on_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._tasks):
            return

        selected_rows = sorted(set(idx.row() for idx in self._table.selectedIndexes()))
        if len(selected_rows) > 1:
            menu = QMenu(self)
            bulk_edit_action = menu.addAction(f"一括編集（{len(selected_rows)}件）")
            action = menu.exec(self._table.viewport().mapToGlobal(pos))
            if action == bulk_edit_action:
                self._open_bulk_edit_dialog(selected_rows)
            return

        task = self._tasks[row]
        menu = QMenu(self)
        edit_action = menu.addAction("編集")
        apply_all_action = menu.addAction("同名タスクを一括編集")
        menu.addSeparator()
        delete_action = menu.addAction("削除")
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._open_edit_dialog(row)
        elif action == apply_all_action:
            self._open_apply_all_dialog(row)
        elif action == delete_action:
            self.task_delete_requested.emit(task.id)

    # ── Double-click → edit dialog ──

    def _on_double_clicked(self, index):
        row = index.row()
        if 0 <= row < len(self._tasks):
            self._open_edit_dialog(row)

    def _open_edit_dialog(self, row: int):
        from views.task_edit_dialog import TaskEditDialog

        task = self._tasks[row]
        history = [(t.name, t.project_id) for t in self._tasks]
        dlg = TaskEditDialog(
            task.name, task.project_id,
            task.start_time, task.end_time,
            self._projects, task_history=history, allow_delete=True, parent=self,
        )
        if dlg.exec() != TaskEditDialog.DialogCode.Accepted:
            return
        if dlg.deleted:
            self.task_delete_requested.emit(task.id)
            return
        result = dlg.get_result()
        if result is None:
            return

        task.name = result["name"]
        task.start_time = result["start_time"]
        task.end_time = result["end_time"]
        task.project_id = result["project_id"]

        project = self._find_project(result["project_id"])
        task.color = project.color if project else DEFAULT_BLOCK_COLOR

        self._update_row(row, task)
        self.task_edited.emit(task)

    def _open_apply_all_dialog(self, row: int):
        """Open edit dialog for a task, then apply changes to all matching tasks."""
        from views.task_edit_dialog import TaskEditDialog

        task = self._tasks[row]
        orig_name = task.name
        orig_project_id = task.project_id
        history = [(t.name, t.project_id) for t in self._tasks]
        dlg = TaskEditDialog(
            task.name, task.project_id,
            task.start_time, task.end_time,
            self._projects, task_history=history,
            require_confirm=True, parent=self,
        )
        dlg.setWindowTitle("同名タスクを一括編集")
        if dlg.exec() != TaskEditDialog.DialogCode.Accepted:
            return
        result = dlg.get_result()
        if result is None:
            return

        task.name = result["name"]
        task.start_time = result["start_time"]
        task.end_time = result["end_time"]
        task.project_id = result["project_id"]

        project = self._find_project(result["project_id"])
        task.color = project.color if project else DEFAULT_BLOCK_COLOR

        self._update_row(row, task)
        self.task_edited.emit(task)
        self.task_apply_all_requested.emit(
            orig_name,
            orig_project_id or "",
            result["name"],
            result["project_id"] or "",
        )

    def _open_bulk_edit_dialog(self, rows: list[int]):
        from views.task_edit_dialog import BulkEditDialog

        tasks = [self._tasks[r] for r in rows if r < len(self._tasks)]
        if not tasks:
            return

        dlg = BulkEditDialog(len(tasks), self._projects, parent=self)
        if dlg.exec() != BulkEditDialog.DialogCode.Accepted:
            return
        result = dlg.get_result()
        if not result:
            return

        edited_tasks = []
        for task in tasks:
            if "name" in result:
                task.name = result["name"]
            if "project_id" in result:
                task.project_id = result["project_id"]
                project = self._find_project(result["project_id"])
                task.color = project.color if project else DEFAULT_BLOCK_COLOR
            edited_tasks.append(task)

        self._rebuild_table()
        self.tasks_bulk_edited.emit(edited_tasks)

    def _find_project(self, project_id: str | None) -> Project | None:
        if project_id is None:
            return None
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    # ── Public update methods (called by controller) ──

    def update_project_list(self, projects: list[Project]):
        self._projects = projects

    def set_tasks(self, tasks: list[Task]):
        """Replace the entire task list (used on date change)."""
        self._tasks = list(tasks)
        self._rebuild_table()

    def add_task(self, task: Task, timing: bool = False):
        if timing:
            self._timing_task_id = task.id
        self._tasks.append(task)
        self._rebuild_table()

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                break
        else:
            return
        self._rebuild_table()

    def remove_task(self, task_id: str):
        for i, t in enumerate(self._tasks):
            if t.id == task_id:
                self._tasks.pop(i)
                self._table.removeRow(i)
                return

    # ── Table helpers ──

    def stop_timing(self):
        """計測終了: タイミング表示を解除してテーブルを更新する。"""
        self._timing_task_id = None

    def _rebuild_table(self):
        self._tasks.sort(key=lambda t: t.start_time)
        self._table.setRowCount(0)
        for task in self._tasks:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._update_row(row, task)

    def _update_row(self, row: int, task: Task):
        start_item = QTableWidgetItem("▶")
        start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, 0, start_item)

        self._table.setItem(row, 1, QTableWidgetItem(task.name))
        self._table.setItem(row, 2, QTableWidgetItem(task.start_time.strftime("%H:%M:%S")))
        is_timing = task.id == self._timing_task_id
        self._table.setItem(row, 3, QTableWidgetItem("-" if is_timing else task.end_time.strftime("%H:%M:%S")))

        if is_timing:
            duration_str = "-"
        else:
            delta = task.end_time - task.start_time
            total_sec = int(delta.total_seconds())
            h, rem = divmod(total_sec, 3600)
            m, s = divmod(rem, 60)
            if h:
                duration_str = f"{h}h {m}m {s}s"
            elif m:
                duration_str = f"{m}m {s}s"
            else:
                duration_str = f"{s}s"
        self._table.setItem(row, 4, QTableWidgetItem(duration_str))

        project = self._find_project(task.project_id)
        project_name = project.name if project else ""
        proj_item = QTableWidgetItem(project_name)
        if project:
            bg = QColor(project.color)
            bg.setAlpha(80)
            proj_item.setBackground(QBrush(bg))
        self._table.setItem(row, 5, proj_item)
