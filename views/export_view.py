from datetime import date

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QTextEdit, QCheckBox, QApplication)
from PySide6.QtCore import Qt

from models.task import Task
from models.project import Project


class ExportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._simple = False
        self._last_tasks = []
        self._last_projects = []
        self._last_date = None
        layout = QVBoxLayout(self)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        layout.addWidget(self._text_edit)

        btn_layout = QHBoxLayout()
        self._simple_cb = QCheckBox("プロジェクトなし")
        self._simple_cb.toggled.connect(self._on_simple_toggled)
        btn_layout.addWidget(self._simple_cb)
        btn_layout.addStretch()
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._text_edit.toPlainText())

    def _on_simple_toggled(self, checked: bool):
        self._simple = checked
        if self._last_date is not None:
            self._render()

    def update_tasks(self, tasks: list[Task], projects: list[Project], current_date: date):
        self._last_tasks = tasks
        self._last_projects = projects
        self._last_date = current_date
        self._render()

    def _render(self):
        project_map = {p.id: p.name for p in self._last_projects}
        sorted_tasks = sorted(self._last_tasks, key=lambda t: t.start_time)

        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekday_names[self._last_date.weekday()]
        lines = [f"{self._last_date.strftime('%Y-%m-%d')} ({weekday})", ""]

        total_minutes = 0
        for task in sorted_tasks:
            start = task.start_time.strftime("%H:%M")
            end = task.end_time.strftime("%H:%M")
            duration = (task.end_time - task.start_time).total_seconds()
            total_minutes += duration / 60

            proj_label = ""
            if not self._simple and task.project_id and task.project_id in project_map:
                proj_label = f"  [{project_map[task.project_id]}]"

            lines.append(f"{start}-{end}  {task.name}{proj_label}")

        hours = int(total_minutes) // 60
        mins = int(total_minutes) % 60
        lines.append("")
        lines.append(f"合計: {hours}h {mins:02d}m")

        self._text_edit.setPlainText("\n".join(lines))
