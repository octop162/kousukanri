from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QLabel, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QColor, QDropEvent


class _ReorderTableWidget(QTableWidget):
    """QTableWidget subclass that handles row reorder via drag-and-drop."""

    row_dropped = Signal(int, int)  # (source_row, dest_row)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._drag_source_row: int | None = None

    def startDrag(self, supportedActions):
        self._drag_source_row = self.currentRow()
        super().startDrag(supportedActions)

    def dropEvent(self, event: QDropEvent):
        dest_row = self.indexAt(event.position().toPoint()).row()
        src_row = self._drag_source_row
        if src_row is None or dest_row < 0 or src_row == dest_row:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()
        self.row_dropped.emit(src_row, dest_row)

from models.task import Task
from models.project import Project
from models.routine import Routine
from utils.constants import DEFAULT_BLOCK_COLOR


class RoutineView(QWidget):
    """Routine preset manager — register recurring tasks and add them with one click."""

    task_add_requested = Signal(Task)
    routine_created = Signal(Routine)
    routine_changed = Signal(Routine)
    routine_deleted = Signal(str)
    routine_order_changed = Signal(list)  # list[Routine] in new order

    def __init__(self, parent=None):
        super().__init__(parent)
        self._routines: list[Routine] = []
        self._projects: list[Project] = []
        self._display_date: date = date.today()
        self._init_ui()

    # ── UI setup ──

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Registration form
        form_label = QLabel("ルーティン登録")
        layout.addWidget(form_label)

        row1 = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("タスク名")
        row1.addWidget(self._name_edit, 1)
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(150)
        self._project_combo.addItem("(なし)", None)
        row1.addWidget(self._project_combo)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self._start_edit = QLineEdit("09:00")
        self._start_edit.setFixedWidth(60)
        self._end_edit = QLineEdit("09:30")
        self._end_edit.setFixedWidth(60)
        row2.addWidget(QLabel("開始"))
        row2.addWidget(self._start_edit)
        row2.addWidget(QLabel("終了"))
        row2.addWidget(self._end_edit)
        row2.addStretch()
        self._add_btn = QPushButton("＋登録")
        self._add_btn.clicked.connect(self._on_register)
        row2.addWidget(self._add_btn)
        layout.addLayout(row2)

        # Routine table
        self._table = _ReorderTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["", "名前", "開始", "終了", "プロジェクト"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 100)

        self._table.setStyleSheet(
            "QTableWidget::item:selected { background: rgba(38, 79, 120, 100); }"
        )

        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.doubleClicked.connect(self._on_double_clicked)
        self._table.row_dropped.connect(self._on_row_dropped)
        layout.addWidget(self._table)

    # ── Helpers ──

    @staticmethod
    def _make_color_icon(color: str, size: int = 12) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    def _find_project(self, project_id: str | None) -> Project | None:
        if project_id is None:
            return None
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    @staticmethod
    def _parse_time(text: str) -> tuple[int, int] | None:
        """Parse 'HH:MM' into (hour, minute). Returns None on failure."""
        parts = text.strip().split(":")
        if len(parts) != 2:
            return None
        try:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return (h, m)
        except ValueError:
            pass
        return None

    # ── Public methods (called by controller) ──

    def update_project_list(self, projects: list[Project]):
        self._projects = projects
        current_data = self._project_combo.currentData()
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.addItem("(なし)", None)
        for p in projects:
            icon = self._make_color_icon(p.color)
            self._project_combo.addItem(icon, p.name, p.id)
        # Restore selection
        for i in range(self._project_combo.count()):
            if self._project_combo.itemData(i) == current_data:
                self._project_combo.setCurrentIndex(i)
                break
        self._project_combo.blockSignals(False)
        # Rebuild table to update project names/colors
        self._rebuild_table()

    def set_routines(self, routines: list[Routine]):
        """Set routines from controller (e.g. on startup load from DB)."""
        self._routines = list(routines)
        self._rebuild_table()

    def set_display_date(self, d: date):
        self._display_date = d

    # ── Registration ──

    def _on_register(self):
        name = self._name_edit.text().strip()
        if not name:
            return
        start = self._parse_time(self._start_edit.text())
        end = self._parse_time(self._end_edit.text())
        if start is None or end is None:
            return
        if start >= end:
            return

        project_id = self._project_combo.currentData()
        routine = Routine(
            name=name,
            project_id=project_id,
            start_hour=start[0],
            start_minute=start[1],
            end_hour=end[0],
            end_minute=end[1],
        )
        self._routines.append(routine)
        self._name_edit.clear()
        self._rebuild_table()
        self.routine_created.emit(routine)

    # ── Table ──

    def _rebuild_table(self):
        self._table.setRowCount(0)
        for routine in self._routines:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._update_row(row, routine)

    def _update_row(self, row: int, routine: Routine):
        add_item = QTableWidgetItem("＋")
        add_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
        self._table.setItem(row, 0, add_item)

        self._table.setItem(row, 1, QTableWidgetItem(routine.name))

        self._table.setItem(row, 2, QTableWidgetItem(
            f"{routine.start_hour:02d}:{routine.start_minute:02d}"))
        self._table.setItem(row, 3, QTableWidgetItem(
            f"{routine.end_hour:02d}:{routine.end_minute:02d}"))

        project = self._find_project(routine.project_id)
        proj_item = QTableWidgetItem(project.name if project else "")
        if project:
            bg = QColor(project.color)
            bg.setAlpha(80)
            from PySide6.QtGui import QBrush
            proj_item.setBackground(QBrush(bg))
        self._table.setItem(row, 4, proj_item)

    def _on_row_dropped(self, src: int, dest: int):
        if src < 0 or src >= len(self._routines) or dest < 0 or dest >= len(self._routines):
            return
        routine = self._routines.pop(src)
        self._routines.insert(dest, routine)
        for i, r in enumerate(self._routines):
            r.order = i
        self._rebuild_table()
        self.routine_order_changed.emit(list(self._routines))

    def _on_cell_clicked(self, row: int, col: int):
        if row < 0 or row >= len(self._routines):
            return
        if col == 0:
            self._add_routine_as_task(self._routines[row])

    def _on_double_clicked(self, index):
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._routines):
            return
        if col == 0:
            return  # "＋" column — handled by cellClicked
        routine = self._routines[row]

        from views.task_edit_dialog import RoutineEditDialog
        dlg = RoutineEditDialog(
            routine.name, routine.start_hour, routine.start_minute,
            routine.end_hour, routine.end_minute, routine.project_id,
            self._projects, allow_delete=True, parent=self,
        )
        if dlg.exec() != RoutineEditDialog.DialogCode.Accepted:
            return
        if dlg.deleted:
            removed = self._routines.pop(row)
            self._rebuild_table()
            self.routine_deleted.emit(removed.id)
            return
        result = dlg.get_result()
        if result is None:
            return
        routine.name = result["name"]
        routine.project_id = result["project_id"]
        routine.start_hour = result["start_hour"]
        routine.start_minute = result["start_minute"]
        routine.end_hour = result["end_hour"]
        routine.end_minute = result["end_minute"]
        self._update_row(row, routine)
        self.routine_changed.emit(routine)

    def _add_routine_as_task(self, routine: Routine):
        """Open TaskEditDialog pre-filled with routine data, then emit task_add_requested."""
        from views.task_edit_dialog import TaskEditDialog

        d = self._display_date
        start_time = datetime(d.year, d.month, d.day,
                              routine.start_hour, routine.start_minute)
        end_time = datetime(d.year, d.month, d.day,
                            routine.end_hour, routine.end_minute)

        dlg = TaskEditDialog(
            routine.name, routine.project_id,
            start_time, end_time,
            self._projects, parent=self,
        )
        dlg.setWindowTitle("ルーティンからタスク追加")
        if dlg.exec() != TaskEditDialog.DialogCode.Accepted:
            return
        result = dlg.get_result()
        if result is None:
            return

        project = self._find_project(result["project_id"])
        color = project.color if project else DEFAULT_BLOCK_COLOR

        task = Task(
            name=result["name"],
            start_time=result["start_time"],
            end_time=result["end_time"],
            color=color,
            project_id=result["project_id"],
        )
        self.task_add_requested.emit(task)
