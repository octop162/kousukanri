from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QWidget, QVBoxLayout
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
        self.resize(900, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        timeline_view = TimelineView(scene, self)
        splitter.addWidget(timeline_view)

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
        splitter.setSizes([500, 400])

        self.setCentralWidget(splitter)
