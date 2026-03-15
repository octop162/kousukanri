from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QWidget,
                                QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                                QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QShortcut, QKeySequence

from views.timeline_view import TimelineView
from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget
from views.date_nav_widget import DateNavWidget
from views.routine_view import RoutineView


class MainWindow(QMainWindow):
    def __init__(self, scene: TimelineScene, list_view: TaskListView,
                 project_list_view: ProjectListView,
                 settings_view: SettingsView,
                 timer_widget: TimerWidget,
                 date_nav_widget: DateNavWidget = None,
                 routine_view: RoutineView = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("工数管理")
        self._base_title = "工数管理"
        icon_path = Path(__file__).parent.parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1200, 1000)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter = self._splitter

        # Left panel: date nav + timeline + zoom bar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        if date_nav_widget is not None:
            left_layout.addWidget(date_nav_widget)

        timeline_view = TimelineView(scene, self)
        left_layout.addWidget(timeline_view)

        # Zoom bar
        zoom_bar = QHBoxLayout()
        zoom_bar.setContentsMargins(4, 2, 4, 2)

        # Panel toggle button (bottom-left)
        self._btn_toggle_panel = QPushButton("◀")
        self._btn_toggle_panel.setFixedWidth(30)
        self._btn_toggle_panel.setToolTip("リストパネルを表示/非表示")
        zoom_bar.addWidget(self._btn_toggle_panel)

        btn_out = QPushButton("-")
        btn_out.setFixedWidth(30)
        self._zoom_label = QLabel("75%")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(50)
        btn_in = QPushButton("+")
        btn_in.setFixedWidth(30)

        zoom_bar.addStretch()
        zoom_bar.addWidget(btn_out)
        zoom_bar.addWidget(self._zoom_label)
        zoom_bar.addWidget(btn_in)
        zoom_bar.addStretch()
        left_layout.addLayout(zoom_bar)
        from PySide6.QtWidgets import QLayout
        left_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        btn_out.clicked.connect(timeline_view.zoom_out)
        btn_in.clicked.connect(timeline_view.zoom_in)
        timeline_view.zoom_changed.connect(self._on_zoom_changed)

        splitter.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(timer_widget)

        # Connect timer signals to update window title
        timer_widget.timer_started.connect(self._on_timer_started)
        timer_widget.timer_stopped.connect(self._on_timer_stopped)
        timer_widget.timer_name_changed.connect(self._on_timer_name_changed)

        # Upper tabs: タスク
        tab_widget = QTabWidget()
        tab_widget.addTab(list_view, "タスク")

        # Lower tabs: 定期 / プロジェクト / 設定
        lower_tab_widget = QTabWidget()
        if routine_view is not None:
            lower_tab_widget.addTab(routine_view, "定期")
        lower_tab_widget.addTab(project_list_view, "プロジェクト")
        lower_tab_widget.addTab(settings_view, "設定")

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(tab_widget)
        right_splitter.addWidget(lower_tab_widget)
        right_splitter.setSizes([500, 500])
        right_layout.addWidget(right_splitter)

        # Web UI link / server status
        from utils.settings import load_settings
        from utils.theme import get_theme_colors
        s = load_settings()
        colors = get_theme_colors(s.get("theme", "dark"))
        text_color = colors["window_text"]
        if s.get("api_server_enabled", False):
            port = s.get("api_port", 8321)
            url = f"http://127.0.0.1:{port}"
            status_label = QLabel(f'<a href="{url}" style="color: {text_color}; text-decoration: none;">{url}</a>')
            status_label.setOpenExternalLinks(True)
        else:
            status_label = QLabel("API サーバー: 停止中（設定から有効化）")
            status_label.setStyleSheet(f"color: {text_color};")
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_label.setContentsMargins(4, 6, 4, 6)
        right_layout.addWidget(status_label)
        from PySide6.QtWidgets import QLayout
        right_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self._right_panel = right_panel
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        splitter.setStretchFactor(0, 0)  # left panel: fixed width
        splitter.setStretchFactor(1, 1)  # right panel: stretches
        self._saved_splitter_sizes = [400, 800]

        # Override minimumSizeHint on panels so QSplitter does not enforce
        # the children's natural minimum (~918px combined).  This lets the
        # window shrink freely to reach the auto-toggle threshold.
        from PySide6.QtCore import QSize
        _zero = QSize(0, 0)
        right_panel.minimumSizeHint = lambda: _zero
        left_panel.minimumSizeHint = lambda: _zero

        self.setCentralWidget(splitter)

        # Panel toggle: connect and apply initial state from settings
        self._btn_toggle_panel.clicked.connect(self._toggle_panel)
        self._timeline_only = False
        if s.get("timeline_only_mode", False):
            QTimer.singleShot(0, lambda: self._apply_panel_mode(True, save=False))

        # System tray
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(self.windowIcon())
        self._tray.setToolTip("工数管理")
        tray_menu = QMenu()
        show_action = QAction("表示", self)
        show_action.triggered.connect(self._restore_from_tray)
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        # Idle reminder
        self._controller = None
        self._idle_notify = True
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(5 * 60 * 1000)  # 5 minutes
        self._idle_timer.timeout.connect(self._check_idle)

        settings_view.settings_changed.connect(self._on_settings_changed)

        # Ctrl+Z undo shortcut
        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self._undo_shortcut.activated.connect(self._on_undo)

        # Ctrl+Y / Ctrl+Shift+Z redo shortcuts (explicit to avoid ambiguity)
        self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self._redo_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._redo_shortcut.activated.connect(self._on_redo)
        self._redo_shortcut2 = QShortcut(QKeySequence("Ctrl+Y"), self)
        self._redo_shortcut2.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._redo_shortcut2.activated.connect(self._on_redo)

    # ウィンドウ幅がこの値を下回ると自動でタイムラインのみモードに切替
    _PANEL_COLLAPSE_THRESHOLD = 550

    def _toggle_panel(self):
        self._apply_panel_mode(not self._timeline_only, save=True, resize_window=True)

    def _apply_panel_mode(self, timeline_only: bool, save: bool = False, resize_window: bool = True):
        self._timeline_only = timeline_only
        if timeline_only:
            if resize_window:
                self._saved_window_size = self.size()
            self._saved_splitter_sizes = self._splitter.sizes()
            self._right_panel.hide()
            self._btn_toggle_panel.setText("▶")
            self.setMinimumWidth(200)
            if resize_window:
                left_width = self._saved_splitter_sizes[0]
                self.resize(left_width, self.height())
        else:
            self._right_panel.show()
            self._btn_toggle_panel.setText("◀")
            self.setMinimumWidth(0)
            if resize_window:
                saved_size = getattr(self, "_saved_window_size", None)
                if saved_size:
                    self.resize(saved_size)
                else:
                    self.resize(1200, self.height())
            sizes = self._saved_splitter_sizes
            if sizes and sum(sizes) > 0:
                total = self._splitter.width() or self.width()
                ratio = total / sum(sizes) if sum(sizes) > 0 else 1.0
                self._splitter.setSizes([int(s * ratio) for s in sizes])
            else:
                w = self.width()
                self._splitter.setSizes([int(w * 0.33), int(w * 0.67)])
        if save:
            from utils.settings import load_settings, save_settings
            s = load_settings()
            s["timeline_only_mode"] = timeline_only
            save_settings(s)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, '_auto_toggling', False):
            return
        w = event.size().width()
        if w < self._PANEL_COLLAPSE_THRESHOLD and not self._timeline_only:
            self._auto_toggling = True
            self._apply_panel_mode(True, save=True, resize_window=False)
            self._auto_toggling = False
        elif w >= self._PANEL_COLLAPSE_THRESHOLD and self._timeline_only:
            self._auto_toggling = True
            self._apply_panel_mode(False, save=True, resize_window=False)
            self._auto_toggling = False

    def set_controller(self, controller):
        """Set controller for idle check. Call after construction."""
        self._controller = controller
        from utils.settings import load_settings
        self._idle_notify = load_settings().get("idle_notify", True)
        if self._idle_notify:
            self._idle_timer.start()

    def _on_undo(self):
        if self._controller is not None:
            self._controller.undo()

    def _on_redo(self):
        if self._controller is not None:
            self._controller.redo()

    def _on_settings_changed(self, settings: dict):
        self._idle_notify = settings.get("idle_notify", True)
        if self._idle_notify:
            self._idle_timer.start()
        else:
            self._idle_timer.stop()

    def _check_idle(self):
        if self._idle_notify and self._controller and self._controller.is_idle():
            self._tray.showMessage(
                "工数管理",
                "タスクが記録されていません。計測を始めましょう！",
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )

    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(200, 400)

    def _on_zoom_changed(self, level: float):
        self._zoom_label.setText(f"{int(level * 100)}%")

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _quit_app(self):
        self._tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _on_timer_started(self, name: str, project_id: str):
        self.setWindowTitle(name)

    def _on_timer_name_changed(self, name: str):
        self.setWindowTitle(name)

    def _on_timer_stopped(self):
        self.setWindowTitle(self._base_title)

