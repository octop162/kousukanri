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
    task_delete_requested = Signal(str)  # task id
    task_start_requested = Signal(str, str)  # (name, project_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: list[Task] = []
        self._projects: list[Project] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["タスク名", "開始", "終了", "所要時間", "プロジェクト", ""]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.doubleClicked.connect(self._on_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._table)

    # ── Cell click (start button) ──

    def _on_cell_clicked(self, row: int, col: int):
        if col == 5 and 0 <= row < len(self._tasks):
            task = self._tasks[row]
            self.task_start_requested.emit(task.name, task.project_id or "")

    # ── Context menu (right-click) ──

    def _on_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._tasks):
            return
        task = self._tasks[row]
        menu = QMenu(self)
        edit_action = menu.addAction("編集")
        menu.addSeparator()
        delete_action = menu.addAction("削除")
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._open_edit_dialog(row)
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

    def add_task(self, task: Task):
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

    def _rebuild_table(self):
        self._tasks.sort(key=lambda t: t.start_time)
        self._table.setRowCount(0)
        for task in self._tasks:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._update_row(row, task)

    def _update_row(self, row: int, task: Task):
        self._table.setItem(row, 0, QTableWidgetItem(task.name))
        self._table.setItem(row, 1, QTableWidgetItem(task.start_time.strftime("%H:%M:%S")))
        self._table.setItem(row, 2, QTableWidgetItem(task.end_time.strftime("%H:%M:%S")))

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
        self._table.setItem(row, 3, QTableWidgetItem(duration_str))

        project = self._find_project(task.project_id)
        project_name = project.name if project else ""
        proj_item = QTableWidgetItem(project_name)
        if project:
            bg = QColor(project.color)
            bg.setAlpha(80)
            proj_item.setBackground(QBrush(bg))
        self._table.setItem(row, 4, proj_item)

        start_item = QTableWidgetItem("▶")
        start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, 5, start_item)
