from datetime import datetime, date, timedelta

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton,
    QCompleter, QSizePolicy,
)
from views.flow_layout import FlowLayout
from PySide6.QtCore import Signal, QTimer, Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor, QIcon

from models.project import Project
from models.task import Task

_ROLE_NAME = Qt.ItemDataRole.UserRole
_ROLE_PID = Qt.ItemDataRole.UserRole + 1


class _TaskCompleter(QCompleter):
    """QCompleter that shows 'タスク名 — プロジェクト' in popup but inserts only the task name."""

    def pathFromIndex(self, index):
        return index.data(_ROLE_NAME) or ""


class TimerWidget(QWidget):
    """Timer bar: [task name] [project▼] [00:00:00] [+] [▶/■]"""

    timer_started = Signal(str, str)       # (name, project_id)
    timer_stopped = Signal()
    timer_name_changed = Signal(str)
    timer_project_changed = Signal(str)    # project_id or ""
    task_add_requested = Signal(Task)      # manually created task

    def __init__(self, parent=None, theme_colors: dict | None = None):
        super().__init__(parent)
        self._running = False
        self._start_time: datetime | None = None
        self._display_date: date = date.today()
        self._projects: list[Project] = []
        self._theme = theme_colors or {}
        # History: list of (task_name, project_id) unique pairs, most recent last
        self._history: list[tuple[str, str | None]] = []
        self._init_ui()

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        if self.layout():
            return self.layout().heightForWidth(width)
        return super().heightForWidth(width)

    def _init_ui(self):
        layout = FlowLayout(self, margin=4, h_spacing=6, v_spacing=4)

        # Group 1: task name input (stretches)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("何をしている？")
        self._name_edit.setMinimumWidth(200)
        self._name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._name_edit.textChanged.connect(self._on_name_changed)
        layout.addWidget(self._name_edit)

        # Completer for task name with history
        self._completer_model = QStandardItemModel()
        self._completer = _TaskCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionRole(Qt.ItemDataRole.DisplayRole)
        self._completer.setMaxVisibleItems(8)
        self._completer.activated[QModelIndex].connect(self._on_completer_activated)
        self._name_edit.setCompleter(self._completer)

        # Group 2: project, time, buttons (stays together, stretches when wrapped)
        controls = QWidget()
        controls.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(150)
        self._project_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._project_combo.addItem("(なし)", None)
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        controls_layout.addWidget(self._project_combo, 1)

        self._time_label = QLabel("00:00:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setMinimumWidth(70)
        self._time_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        controls_layout.addWidget(self._time_label)

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedWidth(40)
        self._add_btn.setStyleSheet(self._btn_style(self._theme.get("timer_add", "#3498DB")))
        self._add_btn.clicked.connect(self._on_add)
        controls_layout.addWidget(self._add_btn)

        self._toggle_btn = QPushButton("▶")
        self._toggle_btn.setFixedWidth(40)
        self._toggle_btn.setStyleSheet(self._btn_style(self._theme.get("timer_start", "#2ECC71")))
        self._toggle_btn.clicked.connect(self._on_toggle)
        controls_layout.addWidget(self._toggle_btn)

        layout.addWidget(controls)

    @staticmethod
    def _btn_style(bg: str) -> str:
        return (
            f"QPushButton {{ background-color: {bg}; color: white; font-size: 16px; "
            f"border-radius: 4px; padding: 4px; }}"
        )

    @staticmethod
    def _make_color_icon(color: str, size: int = 12) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    # ── Completer ──

    def _build_completer_items(self):
        """Build completer model from history."""
        self._completer_model.clear()
        seen = set()
        for name, pid in reversed(self._history):
            key = (name, pid)
            if key in seen:
                continue
            seen.add(key)
            proj = self._find_project(pid)
            display = f"{name} — {proj.name}" if proj else name
            item = QStandardItem(display)
            if proj:
                item.setIcon(self._make_color_icon(proj.color))
            item.setData(name, _ROLE_NAME)
            item.setData(pid, _ROLE_PID)
            self._completer_model.appendRow(item)

    def _on_completer_activated(self, index):
        """When a completer item is selected, fill name and auto-select project."""
        # Get data from the source model via the completer's completion model
        source_index = self._completer.completionModel().mapToSource(index)
        name = self._completer_model.data(source_index, _ROLE_NAME)
        pid = self._completer_model.data(source_index, _ROLE_PID)

        self._name_edit.blockSignals(True)
        self._name_edit.setText(name)
        self._name_edit.blockSignals(False)

        self._select_project(pid)

    def _select_project(self, project_id: str | None):
        self._project_combo.blockSignals(True)
        for i in range(self._project_combo.count()):
            if self._project_combo.itemData(i) == project_id:
                self._project_combo.setCurrentIndex(i)
                break
        self._project_combo.blockSignals(False)

    def _find_project(self, project_id: str | None) -> Project | None:
        if project_id is None:
            return None
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    # ── History management ──

    def add_task_to_history(self, task: Task):
        key = (task.name, task.project_id)
        # Remove duplicate if exists, then append (most recent last)
        self._history = [h for h in self._history if h != key]
        self._history.append(key)
        self._build_completer_items()

    def set_history(self, history: list[tuple[str, str | None]]):
        """Replace the entire history (called from controller)."""
        self._history = list(history)
        self._build_completer_items()

    # ── Display date ──

    def set_display_date(self, d: date):
        """Update the display date (used for creating tasks via + button)."""
        self._display_date = d

    # ── Add task ──

    def _on_add(self):
        from utils.constants import DEFAULT_BLOCK_COLOR
        from views.task_edit_dialog import TaskEditDialog

        from utils.settings import load_settings
        now = datetime.combine(self._display_date, datetime.now().time()).replace(microsecond=0)
        name = self._name_edit.text().strip() or "あたらしいタスク"
        project_id = self._project_combo.currentData()
        duration = load_settings()["default_duration_minutes"]

        dlg = TaskEditDialog(
            name, project_id,
            now, now + timedelta(minutes=duration),
            self._projects, task_history=self._history,
            parent=self,
        )
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

    # ── External start ──

    def set_and_start(self, name: str, project_id: str):
        """Fill name/project and start the timer (called externally)."""
        self._name_edit.setText(name)
        self._select_project(project_id if project_id else None)
        if not self._running:
            self._start()

    # ── Toggle ──

    def _on_toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._running = True
        self._start_time = datetime.now()
        name = self._name_edit.text().strip() or "あたらしいタスク"
        project_id = self._project_combo.currentData() or ""
        self.timer_started.emit(name, project_id)
        self._tick_timer.start()
        self._toggle_btn.setText("■")
        self._toggle_btn.setStyleSheet(self._btn_style(self._theme.get("timer_stop", "#E74C3C")))

    def _stop(self):
        self._running = False
        self._tick_timer.stop()
        self.timer_stopped.emit()
        self._reset_ui()

    def _reset_ui(self):
        self._time_label.setText("00:00:00")
        self._name_edit.clear()
        self._toggle_btn.setText("▶")
        self._toggle_btn.setStyleSheet(self._btn_style(self._theme.get("timer_start", "#2ECC71")))
        self._start_time = None

    def update_start_time(self, start_time: datetime):
        """計測中タスクの開始時間が外部で変更された場合にタイマー表示を同期する。"""
        self._start_time = start_time

    def force_stop(self):
        """Stop the timer without emitting signals (called when running task is deleted externally)."""
        self._running = False
        self._tick_timer.stop()
        self._reset_ui()

    def _on_tick(self):
        if self._start_time is None:
            return
        elapsed = datetime.now() - self._start_time
        total_sec = int(elapsed.total_seconds())
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        self._time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _on_name_changed(self, text: str):
        if self._running:
            self.timer_name_changed.emit(text)

    def _on_project_changed(self, _index: int):
        if self._running:
            project_id = self._project_combo.currentData() or ""
            self.timer_project_changed.emit(project_id)

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
        self._build_completer_items()
