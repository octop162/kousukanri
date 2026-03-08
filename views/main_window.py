from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QWidget,
                                QVBoxLayout, QHBoxLayout, QPushButton, QLabel)
from PySide6.QtCore import Qt

from views.timeline_view import TimelineView
from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget


class MainWindow(QMainWindow):
    def __init__(self, scene: TimelineScene, list_view: TaskListView,
                 project_list_view: ProjectListView,
                 settings_view: SettingsView,
                 timer_widget: TimerWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Time Tracker PoC")
        self.resize(1200, 800)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: timeline + zoom bar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        timeline_view = TimelineView(scene, self)
        left_layout.addWidget(timeline_view)

        # Zoom bar
        zoom_bar = QHBoxLayout()
        zoom_bar.setContentsMargins(4, 2, 4, 2)
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

        btn_out.clicked.connect(timeline_view.zoom_out)
        btn_in.clicked.connect(timeline_view.zoom_in)
        timeline_view.zoom_changed.connect(self._on_zoom_changed)

        splitter.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(timer_widget)

        tab_widget = QTabWidget()
        tab_widget.addTab(list_view, "タスク")
        tab_widget.addTab(project_list_view, "プロジェクト")
        tab_widget.addTab(settings_view, "設定")
        right_layout.addWidget(tab_widget)

        splitter.addWidget(right_panel)
        splitter.setSizes([500, 700])

        self.setCentralWidget(splitter)

    def _on_zoom_changed(self, level: float):
        self._zoom_label.setText(f"{int(level * 100)}%")
