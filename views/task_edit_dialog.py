from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QTimeEdit, QDialogButtonBox,
)
from PySide6.QtCore import QTime

from models.project import Project


class TaskEditDialog(QDialog):
    """Unified dialog for editing task name, project, start/end time."""

    def __init__(self, name: str, project_id: str | None,
                 start_time: datetime, end_time: datetime,
                 projects: list[Project], parent=None):
        super().__init__(parent)
        self.setWindowTitle("タスク編集")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Name
        self._name_edit = QLineEdit(name)
        layout.addRow("タスク名:", self._name_edit)

        # Project
        self._project_combo = QComboBox()
        self._project_combo.addItem("(なし)", None)
        selected_index = 0
        for i, p in enumerate(projects):
            self._project_combo.addItem(p.name, p.id)
            if p.id == project_id:
                selected_index = i + 1
        self._project_combo.setCurrentIndex(selected_index)
        layout.addRow("プロジェクト:", self._project_combo)

        # Start time
        self._start_edit = QTimeEdit()
        self._start_edit.setDisplayFormat("HH:mm:ss")
        self._start_edit.setTime(QTime(start_time.hour, start_time.minute, start_time.second))
        layout.addRow("開始:", self._start_edit)

        # End time
        self._end_edit = QTimeEdit()
        self._end_edit.setDisplayFormat("HH:mm:ss")
        self._end_edit.setTime(QTime(end_time.hour, end_time.minute, end_time.second))
        layout.addRow("終了:", self._end_edit)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._start_ref = start_time
        self._end_ref = end_time

    def get_result(self) -> dict | None:
        """Return edited values, or None if start >= end."""
        name = self._name_edit.text().strip() or "New Task"
        project_id = self._project_combo.currentData()

        st = self._start_edit.time()
        start = self._start_ref.replace(
            hour=st.hour(), minute=st.minute(), second=st.second(), microsecond=0,
        )
        et = self._end_edit.time()
        end = self._end_ref.replace(
            hour=et.hour(), minute=et.minute(), second=et.second(), microsecond=0,
        )

        if start >= end:
            return None

        return {
            "name": name,
            "project_id": project_id,
            "start_time": start,
            "end_time": end,
        }
