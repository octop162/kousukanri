from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)
from PySide6.QtGui import QColor, QBrush, QDropEvent
from PySide6.QtCore import Signal, Qt

from models.project import Project


class _ReorderTableWidget(QTableWidget):
    """QTableWidget subclass that handles row reorder via drag-and-drop manually."""

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
        # Determine destination row from drop position
        dest_row = self.indexAt(event.position().toPoint()).row()
        src_row = self._drag_source_row

        if src_row is None or dest_row < 0 or src_row == dest_row:
            event.ignore()
            return

        # Don't let QTableWidget handle it (it corrupts rows)
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()

        self.row_dropped.emit(src_row, dest_row)


class ProjectListView(QWidget):
    """Project list with add form, color editing, and drag-and-drop reordering."""

    project_created = Signal(Project)
    project_changed = Signal(Project)
    project_deleted = Signal(str)
    project_order_changed = Signal(list)  # list[Project] in new order

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[Project] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Add form ──
        form = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("プロジェクト名を入力...")
        self._name_edit.returnPressed.connect(self._on_add_clicked)

        self._color_btn = QPushButton()
        self._color_btn.setFixedWidth(32)
        self._selected_color = "#4A90D9"
        self._update_color_button(self._selected_color)
        self._color_btn.clicked.connect(self._on_pick_add_color)

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedWidth(32)
        self._add_btn.clicked.connect(self._on_add_clicked)

        form.addWidget(self._name_edit)
        form.addWidget(self._color_btn)
        form.addWidget(self._add_btn)
        layout.addLayout(form)

        # ── Table ──
        self._table = _ReorderTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["プロジェクト名", "色", ""])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.row_dropped.connect(self._on_row_dropped)
        layout.addWidget(self._table)

    def _update_color_button(self, color: str):
        self._color_btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #555; border-radius: 3px;"
        )

    def _on_pick_add_color(self):
        from views.color_picker_dialog import ColorPickerDialog
        dlg = ColorPickerDialog(self._selected_color, self)
        if dlg.exec() == ColorPickerDialog.DialogCode.Accepted:
            self._selected_color = dlg.selected_color()
            self._update_color_button(self._selected_color)

    def _on_add_clicked(self):
        name = self._name_edit.text().strip()
        if not name:
            return
        order = len(self._projects)
        project = Project(name=name, color=self._selected_color, order=order)
        self._name_edit.clear()
        self.project_created.emit(project)

    def _on_cell_clicked(self, row: int, col: int):
        if row < 0 or row >= len(self._projects):
            return
        project = self._projects[row]

        if col == 1:
            # Color swatch clicked → pick new color
            from views.color_picker_dialog import ColorPickerDialog
            dlg = ColorPickerDialog(project.color, self)
            if dlg.exec() == ColorPickerDialog.DialogCode.Accepted:
                project.color = dlg.selected_color()
                self._update_row(row, project)
                self.project_changed.emit(project)
        elif col == 2:
            # Delete button clicked
            reply = QMessageBox.question(
                self, "確認", f"プロジェクト「{project.name}」を削除しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.project_deleted.emit(project.id)

    def _on_row_dropped(self, src: int, dest: int):
        """Move project from src to dest in the list and rebuild table."""
        if src < 0 or src >= len(self._projects):
            return
        if dest < 0 or dest >= len(self._projects):
            return

        project = self._projects.pop(src)
        self._projects.insert(dest, project)

        for i, p in enumerate(self._projects):
            p.order = i

        self._rebuild_table()
        self.project_order_changed.emit(list(self._projects))

    # ── Public methods (called by controller) ──

    def set_projects(self, projects: list[Project]):
        self._projects = list(projects)
        self._rebuild_table()

    def add_project(self, project: Project):
        self._projects.append(project)
        self._append_row(project)

    def update_project(self, project: Project):
        for i, p in enumerate(self._projects):
            if p.id == project.id:
                self._projects[i] = project
                self._update_row(i, project)
                return

    def remove_project(self, project_id: str):
        for i, p in enumerate(self._projects):
            if p.id == project_id:
                self._projects.pop(i)
                self._table.removeRow(i)
                # Re-number remaining
                for j, pp in enumerate(self._projects):
                    pp.order = j
                return

    # ── Table helpers ──

    def _rebuild_table(self):
        self._table.setRowCount(0)
        for project in self._projects:
            self._append_row(project)

    def _append_row(self, project: Project):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._update_row(row, project)

    def _update_row(self, row: int, project: Project):
        self._table.setItem(row, 0, QTableWidgetItem(project.name))

        color_item = QTableWidgetItem("  ")
        color_item.setBackground(QBrush(QColor(project.color)))
        self._table.setItem(row, 1, color_item)

        del_item = QTableWidgetItem("×")
        del_item.setTextAlignment(0x0084)  # AlignCenter
        self._table.setItem(row, 2, del_item)
