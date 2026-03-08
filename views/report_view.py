import json
from datetime import date, timedelta

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QTextEdit, QApplication,
                               QCheckBox, QLabel, QDateEdit)
from PySide6.QtCore import Qt, QDate

from models.task import Task
from models.project import Project
from cli import (_aggregate_by_project, _merge_aggregates,
                 _format_report_table, _totals_to_json_list,
                 _fmt_time, _iter_date_range)


class ReportView(QWidget):
    """1日のプロジェクト別レポート（リアルタイム更新）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        opts_layout = QHBoxLayout()
        self._detail_check = QCheckBox("内訳を表示")
        self._detail_check.stateChanged.connect(self._on_detail_changed)
        opts_layout.addWidget(self._detail_check)
        self._json_check = QCheckBox("JSON")
        self._json_check.stateChanged.connect(self._on_detail_changed)
        opts_layout.addWidget(self._json_check)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        layout.addWidget(self._text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        layout.addLayout(btn_layout)

        self._last_tasks = []
        self._last_projects = []
        self._last_date = date.today()

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._text_edit.toPlainText())

    def _on_detail_changed(self):
        self._refresh()

    def update_tasks(self, tasks: list[Task], projects: list[Project], current_date: date):
        self._last_tasks = tasks
        self._last_projects = projects
        self._last_date = current_date
        self._refresh()

    def _refresh(self):
        tasks = self._last_tasks
        projects = self._last_projects
        current_date = self._last_date
        detail = self._detail_check.isChecked()
        use_json = self._json_check.isChecked()

        if not tasks:
            if use_json:
                data = {"date": current_date.isoformat(), "projects": []}
                self._text_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                self._text_edit.setPlainText(f"{current_date.isoformat()} レポート\nタスクはありません")
            return

        proj_map = {p.id: p.name for p in projects}
        totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)

        if use_json:
            grand_total = sum(totals.values())
            data = {
                "date": current_date.isoformat(),
                "total_seconds": int(grand_total),
                "total_formatted": _fmt_time(grand_total),
                "projects": _totals_to_json_list(totals, details if detail else None),
            }
            self._text_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            lines = [f"{current_date.isoformat()} レポート"]
            lines.append(_format_report_table(totals, details if detail else None))
            self._text_edit.setPlainText("\n".join(lines))


class ReportsView(QWidget):
    """期間内のプロジェクト別集計レポート（更新ボタンで手動更新）。"""

    def __init__(self, database=None, parent=None):
        super().__init__(parent)
        self._db = database
        layout = QVBoxLayout(self)

        # Period selection
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("開始:"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addDays(-29))
        period_layout.addWidget(self._start_date)

        period_layout.addWidget(QLabel("終了:"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        period_layout.addWidget(self._end_date)

        self._detail_check = QCheckBox("内訳")
        period_layout.addWidget(self._detail_check)
        self._json_check = QCheckBox("JSON")
        period_layout.addWidget(self._json_check)

        update_btn = QPushButton("更新")
        update_btn.clicked.connect(self._on_update)
        period_layout.addWidget(update_btn)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        layout.addWidget(self._text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._text_edit.toPlainText())

    def _on_update(self):
        if self._db is None:
            return
        start_date = self._start_date.date().toPython()
        end_date = self._end_date.date().toPython()
        detail = self._detail_check.isChecked()
        use_json = self._json_check.isChecked()

        proj_map = {p.id: p.name for p in self._db.get_all_projects()}
        totals = {}
        all_details = {}
        days_with_tasks = 0

        for d in _iter_date_range(start_date, end_date):
            tasks = self._db.get_tasks_for_date(d.isoformat())
            if not tasks:
                continue
            days_with_tasks += 1
            day_totals, day_details = _aggregate_by_project(tasks, proj_map, detail=detail)
            _merge_aggregates(totals, all_details, day_totals, day_details)

        days = (end_date - start_date).days + 1

        if use_json:
            grand_total = sum(totals.values())
            data = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "days": days,
                "days_with_tasks": days_with_tasks,
                "total_seconds": int(grand_total),
                "total_formatted": _fmt_time(grand_total),
                "projects": _totals_to_json_list(totals, all_details if detail else None),
            }
            self._text_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            lines = [f"{start_date.isoformat()} 〜 {end_date.isoformat()} 集計レポート（{days}日間）"]
            if not totals:
                lines.append("タスクはありません")
            else:
                lines.append(_format_report_table(totals, all_details if detail else None))
                lines.append(f"\n記録日数: {days_with_tasks}日")
            self._text_edit.setPlainText("\n".join(lines))


class ReportsByDayView(QWidget):
    """期間内の日別レポート（更新ボタンで手動更新）。"""

    def __init__(self, database=None, parent=None):
        super().__init__(parent)
        self._db = database
        layout = QVBoxLayout(self)

        # Period selection
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("開始:"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addDays(-29))
        period_layout.addWidget(self._start_date)

        period_layout.addWidget(QLabel("終了:"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        period_layout.addWidget(self._end_date)

        self._detail_check = QCheckBox("内訳")
        period_layout.addWidget(self._detail_check)
        self._json_check = QCheckBox("JSON")
        period_layout.addWidget(self._json_check)

        update_btn = QPushButton("更新")
        update_btn.clicked.connect(self._on_update)
        period_layout.addWidget(update_btn)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        layout.addWidget(self._text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)
        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._text_edit.toPlainText())

    def _on_update(self):
        if self._db is None:
            return
        start_date = self._start_date.date().toPython()
        end_date = self._end_date.date().toPython()
        detail = self._detail_check.isChecked()
        use_json = self._json_check.isChecked()

        proj_map = {p.id: p.name for p in self._db.get_all_projects()}
        grand_total = 0
        days_with_tasks = 0

        days = (end_date - start_date).days + 1
        json_days = []
        lines = [f"{start_date.isoformat()} 〜 {end_date.isoformat()} 日別レポート（{days}日間）", ""]

        for d in _iter_date_range(start_date, end_date):
            tasks = self._db.get_tasks_for_date(d.isoformat())
            if not tasks:
                continue
            days_with_tasks += 1
            totals, details = _aggregate_by_project(tasks, proj_map, detail=detail)
            day_total = sum(totals.values())
            grand_total += day_total

            if use_json:
                json_days.append({
                    "date": d.isoformat(),
                    "total_seconds": int(day_total),
                    "total_formatted": _fmt_time(day_total),
                    "projects": _totals_to_json_list(totals, details if detail else None),
                })
            else:
                lines.append(f"■ {d.isoformat()}  ({_fmt_time(day_total)})")
                lines.append(_format_report_table(totals, details if detail else None))
                lines.append("")

        if use_json:
            data = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "days": days,
                "days_with_tasks": days_with_tasks,
                "total_seconds": int(grand_total),
                "total_formatted": _fmt_time(grand_total),
                "daily": json_days,
            }
            self._text_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if days_with_tasks == 0:
                lines.append("タスクはありません")
            else:
                lines.append(f"記録日数: {days_with_tasks}日 / 合計: {_fmt_time(grand_total)}")
            self._text_edit.setPlainText("\n".join(lines))
