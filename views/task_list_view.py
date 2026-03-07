from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QMenu,
)
from PySide6.QtGui import QColor, QCursor
from PySide6.QtCore import Signal, Qt

from models.task import Task
from models.project import Project
from utils.constants import DEFAULT_BLOCK_COLOR


class TaskListView(QWidget):
    """Toggl-style task list with an add form at the top."""

    task_add_requested = Signal(Task)
    task_project_changed = Signal(Task)  # emitted when user changes a task's project

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: list[Task] = []
        self._projects: list[Project] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Add form ──
        form = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("タスク名を入力...")
        self._name_edit.returnPressed.connect(self._on_add_clicked)

        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(100)
        self._project_combo.addItem("(なし)", None)

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedWidth(32)
        self._add_btn.clicked.connect(self._on_add_clicked)

        form.addWidget(self._name_edit)
        form.addWidget(self._project_combo)
        form.addWidget(self._add_btn)
        layout.addLayout(form)

        # ── Table ──
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["タスク名", "開始", "終了", "所要時間", "プロジェクト"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self._table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self._table)

    # ── Cell click handler ──

    def _on_cell_clicked(self, row: int, col: int):
        if col != 4 or row < 0 or row >= len(self._tasks):
            return
        task = self._tasks[row]

        menu = QMenu(self)
        none_action = menu.addAction("(なし)")
        project_actions = {}
        for proj in self._projects:
            act = menu.addAction(proj.name)
            project_actions[act] = proj

        action = menu.exec(QCursor.pos())
        if action is None:
            return

        if action == none_action:
            task.project_id = None
            task.color = DEFAULT_BLOCK_COLOR
        elif action in project_actions:
            proj = project_actions[action]
            task.project_id = proj.id
            task.color = proj.color

        self._update_row(row, task)
        self.task_project_changed.emit(task)

    # ── Add form handler ──

    def _on_add_clicked(self):
        name = self._name_edit.text().strip() or "New Task"
        now = datetime.now().replace(second=0, microsecond=0)
        now = now.replace(minute=(now.minute // 5) * 5)
        start = now
        end = now + timedelta(minutes=30)

        project_id = self._project_combo.currentData()
        project = self._find_project(project_id)
        if project is not None:
            color = project.color
        else:
            color = DEFAULT_BLOCK_COLOR

        task = Task(
            name=name, start_time=start, end_time=end,
            color=color, project_id=project_id,
        )
        self._name_edit.clear()
        self.task_add_requested.emit(task)

    def _find_project(self, project_id: str | None) -> Project | None:
        if project_id is None:
            return None
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    # ── Project combo management ──

    def update_project_list(self, projects: list[Project]):
        self._projects = projects
        current_data = self._project_combo.currentData()
        self._project_combo.clear()
        self._project_combo.addItem("(なし)", None)
        for p in projects:
            self._project_combo.addItem(p.name, p.id)
        # Restore selection
        for i in range(self._project_combo.count()):
            if self._project_combo.itemData(i) == current_data:
                self._project_combo.setCurrentIndex(i)
                break

    # ── Public update methods (called by controller) ──

    def add_task(self, task: Task):
        self._tasks.append(task)
        self._append_row(task)

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                self._update_row(i, task)
                return

    def remove_task(self, task_id: str):
        for i, t in enumerate(self._tasks):
            if t.id == task_id:
                self._tasks.pop(i)
                self._table.removeRow(i)
                return

    # ── Table helpers ──

    def _append_row(self, task: Task):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._update_row(row, task)

    def _update_row(self, row: int, task: Task):
        self._table.setItem(row, 0, QTableWidgetItem(task.name))
        self._table.setItem(row, 1, QTableWidgetItem(task.start_time.strftime("%H:%M")))
        self._table.setItem(row, 2, QTableWidgetItem(task.end_time.strftime("%H:%M")))

        # Duration
        delta = task.end_time - task.start_time
        total_min = int(delta.total_seconds()) // 60
        h, m = divmod(total_min, 60)
        duration_str = f"{h}h {m}m" if h else f"{m}m"
        self._table.setItem(row, 3, QTableWidgetItem(duration_str))

        # Project name
        project = self._find_project(task.project_id)
        project_name = project.name if project else ""
        self._table.setItem(row, 4, QTableWidgetItem(project_name))
