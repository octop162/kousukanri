import re
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QCompleter, QMessageBox, QPushButton, QHBoxLayout,
    QCheckBox,
)
from PySide6.QtCore import Qt, QModelIndex, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor, QIcon

from models.project import Project


def parse_time_text(text: str) -> tuple[int, int, int] | None:
    """Parse flexible time formats into (hour, minute, second).

    Accepts: HH:MM:SS, H:MM:SS, HH:MM, H:MM, H:M, HH:M:S, H:M:S, etc.
    Seconds default to 0 if omitted.
    """
    text = text.strip()
    # Split by : or .
    parts = re.split(r'[:.]', text)
    if len(parts) < 2 or len(parts) > 3:
        return None
    try:
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
        return None
    return (h, m, s)


def format_time(h: int, m: int, s: int) -> str:
    return f"{h:02d}:{m:02d}:{s:02d}"


def _make_color_icon(color: str, size: int = 12) -> QIcon:
    """Create a small square icon filled with the given color."""
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(color))
    return QIcon(pixmap)


class BulkEditDialog(QDialog):
    """Dialog for bulk-editing multiple tasks (name and/or project)."""

    _color_icon = staticmethod(_make_color_icon)
    _UNCHANGED = "__unchanged__"

    def __init__(self, count: int, projects: list[Project], parent=None):
        super().__init__(parent)
        self._projects = projects
        self.setWindowTitle(f"一括編集（{count}件）")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Name (empty = no change)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("変更しない")
        layout.addRow("タスク名:", self._name_edit)

        # Project (first item = no change)
        self._project_combo = QComboBox()
        self._project_combo.addItem("(変更しない)", self._UNCHANGED)
        self._project_combo.addItem("(なし)", None)
        for p in projects:
            self._project_combo.addItem(self._color_icon(p.color), p.name, p.id)
        layout.addRow("プロジェクト:", self._project_combo)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_result(self) -> dict:
        """Return dict with keys to change. Missing keys = no change."""
        result = {}
        name = self._name_edit.text().strip()
        if name:
            result["name"] = name
        project_data = self._project_combo.currentData()
        if project_data != self._UNCHANGED:
            result["project_id"] = project_data
        return result


class TaskEditDialog(QDialog):
    """Unified dialog for editing task name, project, start/end time."""

    _color_icon = staticmethod(_make_color_icon)

    def __init__(self, name: str, project_id: str | None,
                 start_time: datetime, end_time: datetime,
                 projects: list[Project],
                 task_history: list[tuple[str, str | None]] | None = None,
                 allow_delete: bool = False,
                 require_confirm: bool = False,
                 parent=None):
        super().__init__(parent)
        self._projects = projects
        self._deleted = False
        self.setWindowTitle("タスク編集")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Name with completer
        self._name_edit = QLineEdit(name)
        layout.addRow("タスク名:", self._name_edit)

        # Project
        self._project_combo = QComboBox()
        self._project_combo.addItem("(なし)", None)
        selected_index = 0
        for i, p in enumerate(projects):
            self._project_combo.addItem(self._color_icon(p.color), p.name, p.id)
            if p.id == project_id:
                selected_index = i + 1
        self._project_combo.setCurrentIndex(selected_index)
        layout.addRow("プロジェクト:", self._project_combo)

        # Completer setup
        if task_history:
            self._completer_model = QStandardItemModel()
            seen = set()
            for hname, hpid in reversed(task_history):
                key = (hname, hpid)
                if key in seen:
                    continue
                seen.add(key)
                proj = self._find_project(hpid)
                display = f"{hname} — {proj.name}" if proj else hname
                item = QStandardItem()
                item.setData(display, Qt.ItemDataRole.DisplayRole)
                item.setData(hname, Qt.ItemDataRole.EditRole)
                item.setData(hpid, Qt.ItemDataRole.UserRole)
                self._completer_model.appendRow(item)

            completer = QCompleter(self._completer_model, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionRole(Qt.ItemDataRole.DisplayRole)
            completer.setMaxVisibleItems(8)
            completer.activated[QModelIndex].connect(self._on_completer_activated)
            self._name_edit.setCompleter(completer)

        # Start time (text input)
        self._start_edit = QLineEdit(
            format_time(start_time.hour, start_time.minute, start_time.second)
        )
        self._start_edit.setPlaceholderText("HH:MM:SS")
        layout.addRow("開始:", self._start_edit)

        # End time (text input)
        self._end_edit = QLineEdit(
            format_time(end_time.hour, end_time.minute, end_time.second)
        )
        self._end_edit.setPlaceholderText("HH:MM:SS")
        layout.addRow("終了:", self._end_edit)

        # Normalize on focus out
        self._start_edit.editingFinished.connect(lambda: self._normalize_field(self._start_edit))
        self._end_edit.editingFinished.connect(lambda: self._normalize_field(self._end_edit))

        # Confirm checkbox (for dangerous bulk operations)
        self._confirm_check: QCheckBox | None = None
        if require_confirm:
            self._confirm_check = QCheckBox("全日付の同名タスクに適用することを確認")
            self._confirm_check.setStyleSheet("color: #E74C3C;")
            layout.addRow(self._confirm_check)

        # Buttons
        btn_layout = QHBoxLayout()
        if allow_delete:
            delete_btn = QPushButton("削除")
            delete_btn.setStyleSheet("color: #E74C3C;")
            delete_btn.clicked.connect(self._on_delete)
            btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addRow(btn_layout)

        # Disable OK until checkbox is checked
        if self._confirm_check is not None:
            self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
            self._ok_btn.setEnabled(False)
            self._confirm_check.toggled.connect(self._ok_btn.setEnabled)

        self._start_ref = start_time
        self._end_ref = end_time

    def _normalize_field(self, field: QLineEdit):
        result = parse_time_text(field.text())
        if result:
            field.setText(format_time(*result))

    def _find_project(self, project_id: str | None) -> Project | None:
        if project_id is None:
            return None
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    def _on_completer_activated(self, index: QModelIndex):
        source_index = self._name_edit.completer().completionModel().mapToSource(index)
        name = self._completer_model.data(source_index, Qt.ItemDataRole.EditRole)
        pid = self._completer_model.data(source_index, Qt.ItemDataRole.UserRole)

        self._name_edit.blockSignals(True)
        self._name_edit.setText(name)
        self._name_edit.blockSignals(False)

        for i in range(self._project_combo.count()):
            if self._project_combo.itemData(i) == pid:
                self._project_combo.setCurrentIndex(i)
                break

    @property
    def deleted(self) -> bool:
        return self._deleted

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "確認", "このタスクを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    def _on_accept(self):
        start_parsed = parse_time_text(self._start_edit.text())
        end_parsed = parse_time_text(self._end_edit.text())
        if start_parsed is None or end_parsed is None:
            QMessageBox.warning(self, "入力エラー", "時刻の形式が正しくありません。\n例: 9:30, 14:05:30")
            return
        self.accept()

    def get_result(self) -> dict | None:
        """Return edited values, or None if start >= end."""
        name = self._name_edit.text().strip() or "あたらしいタスク"
        project_id = self._project_combo.currentData()

        start_parsed = parse_time_text(self._start_edit.text())
        end_parsed = parse_time_text(self._end_edit.text())
        if start_parsed is None or end_parsed is None:
            return None

        start = self._start_ref.replace(
            hour=start_parsed[0], minute=start_parsed[1],
            second=start_parsed[2], microsecond=0,
        )
        end = self._end_ref.replace(
            hour=end_parsed[0], minute=end_parsed[1],
            second=end_parsed[2], microsecond=0,
        )

        if start >= end:
            return None

        return {
            "name": name,
            "project_id": project_id,
            "start_time": start,
            "end_time": end,
        }


class ProjectEditDialog(QDialog):
    """Dialog for editing a project's name and color, with optional delete."""

    def __init__(self, name: str, color: str, allow_delete: bool = False, parent=None):
        super().__init__(parent)
        self._deleted = False
        self.setWindowTitle("プロジェクト編集")
        self.setMinimumWidth(280)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit(name)
        layout.addRow("プロジェクト名:", self._name_edit)

        self._color = color
        self._color_btn = QPushButton()
        self._color_btn.setFixedHeight(28)
        self._update_color_button()
        self._color_btn.clicked.connect(self._on_pick_color)
        layout.addRow("色:", self._color_btn)

        btn_layout = QHBoxLayout()
        if allow_delete:
            delete_btn = QPushButton("削除")
            delete_btn.setStyleSheet("color: #E74C3C;")
            delete_btn.clicked.connect(self._on_delete)
            btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addRow(btn_layout)

    def _update_color_button(self):
        self._color_btn.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #555; border-radius: 3px;"
        )

    def _on_pick_color(self):
        from views.color_picker_dialog import ColorPickerDialog
        dlg = ColorPickerDialog(self._color, self)
        if dlg.exec() == ColorPickerDialog.DialogCode.Accepted:
            self._color = dlg.selected_color()
            self._update_color_button()

    @property
    def deleted(self) -> bool:
        return self._deleted

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "確認", "このプロジェクトを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    def get_result(self) -> dict | None:
        name = self._name_edit.text().strip()
        if not name:
            return None
        return {"name": name, "color": self._color}


class RoutineEditDialog(QDialog):
    """Dialog for editing a routine's name, times, and project, with optional delete."""

    _color_icon = staticmethod(_make_color_icon)

    def __init__(self, name: str, start_hour: int, start_minute: int,
                 end_hour: int, end_minute: int, project_id: str | None,
                 projects: list[Project], allow_delete: bool = False, parent=None):
        super().__init__(parent)
        self._projects = projects
        self._deleted = False
        self.setWindowTitle("ルーティン編集")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit(name)
        layout.addRow("タスク名:", self._name_edit)

        self._start_edit = QLineEdit(f"{start_hour:02d}:{start_minute:02d}")
        self._start_edit.setPlaceholderText("HH:MM")
        layout.addRow("開始:", self._start_edit)

        self._end_edit = QLineEdit(f"{end_hour:02d}:{end_minute:02d}")
        self._end_edit.setPlaceholderText("HH:MM")
        layout.addRow("終了:", self._end_edit)

        self._project_combo = QComboBox()
        self._project_combo.addItem("(なし)", None)
        selected_index = 0
        for i, p in enumerate(projects):
            self._project_combo.addItem(self._color_icon(p.color), p.name, p.id)
            if p.id == project_id:
                selected_index = i + 1
        self._project_combo.setCurrentIndex(selected_index)
        layout.addRow("プロジェクト:", self._project_combo)

        btn_layout = QHBoxLayout()
        if allow_delete:
            delete_btn = QPushButton("削除")
            delete_btn.setStyleSheet("color: #E74C3C;")
            delete_btn.clicked.connect(self._on_delete)
            btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addRow(btn_layout)

    @property
    def deleted(self) -> bool:
        return self._deleted

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "確認", "このルーティンを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    def _on_accept(self):
        start = parse_time_text(self._start_edit.text())
        end = parse_time_text(self._end_edit.text())
        if start is None or end is None:
            QMessageBox.warning(self, "入力エラー", "時刻の形式が正しくありません。\n例: 9:30, 14:05")
            return
        if (start[0], start[1]) >= (end[0], end[1]):
            QMessageBox.warning(self, "入力エラー", "開始時刻は終了時刻より前にしてください。")
            return
        self.accept()

    def get_result(self) -> dict | None:
        name = self._name_edit.text().strip()
        if not name:
            return None
        start = parse_time_text(self._start_edit.text())
        end = parse_time_text(self._end_edit.text())
        if start is None or end is None:
            return None
        if (start[0], start[1]) >= (end[0], end[1]):
            return None
        return {
            "name": name,
            "project_id": self._project_combo.currentData(),
            "start_hour": start[0],
            "start_minute": start[1],
            "end_hour": end[0],
            "end_minute": end[1],
        }
