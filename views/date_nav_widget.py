from datetime import date, timedelta

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QDialog, QVBoxLayout, QCalendarWidget,
)
from PySide6.QtCore import Signal, Qt


class DateNavWidget(QWidget):
    """Date navigation bar: [◀] [2026年3月8日 (日)] [▶]"""

    date_requested = Signal(object)  # datetime.date

    _WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = date.today()
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedWidth(40)
        self._prev_btn.clicked.connect(self._go_prev)
        layout.addWidget(self._prev_btn)

        layout.addStretch()

        self._date_btn = QPushButton()
        self._date_btn.setMinimumWidth(180)
        self._date_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; padding: 4px 12px; }"
        )
        self._date_btn.clicked.connect(self._open_calendar)
        layout.addWidget(self._date_btn)

        self._today_btn = QPushButton("今日")
        self._today_btn.setFixedWidth(50)
        self._today_btn.clicked.connect(self._go_today)
        layout.addWidget(self._today_btn)

        layout.addStretch()

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedWidth(40)
        self._next_btn.clicked.connect(self._go_next)
        layout.addWidget(self._next_btn)

        self._update_label()

    def _format_date(self, d: date) -> str:
        wd = self._WEEKDAYS[d.weekday()]
        return f"{d.year}年{d.month}月{d.day}日 ({wd})"

    def _update_label(self):
        self._date_btn.setText(self._format_date(self._current_date))

    def set_date(self, d: date):
        self._current_date = d
        self._update_label()

    def _go_prev(self):
        self.date_requested.emit(self._current_date - timedelta(days=1))

    def _go_next(self):
        self.date_requested.emit(self._current_date + timedelta(days=1))

    def _go_today(self):
        self.date_requested.emit(date.today())

    def _open_calendar(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("日付を選択")
        dlg_layout = QVBoxLayout(dlg)
        cal = QCalendarWidget()
        from PySide6.QtCore import QDate
        qd = QDate(self._current_date.year, self._current_date.month, self._current_date.day)
        cal.setSelectedDate(qd)
        dlg_layout.addWidget(cal)

        def on_clicked(qdate):
            selected = date(qdate.year(), qdate.month(), qdate.day())
            dlg.accept()
            self.date_requested.emit(selected)

        cal.clicked.connect(on_clicked)
        dlg.exec()
