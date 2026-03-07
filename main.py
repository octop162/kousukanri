import sys

from PySide6.QtWidgets import QApplication

from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget
from views.main_window import MainWindow
from controllers.task_controller import TaskController


def main():
    app = QApplication(sys.argv)

    # Dark palette
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1E1E1E"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#CCCCCC"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#252526"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#CCCCCC"))
    app.setPalette(palette)

    scene = TimelineScene()
    list_view = TaskListView()
    project_list_view = ProjectListView()
    settings_view = SettingsView()
    timer_widget = TimerWidget()
    controller = TaskController(scene)
    controller.set_list_view(list_view)
    controller.set_project_list_view(project_list_view)
    controller.set_timer_widget(timer_widget)

    window = MainWindow(scene, list_view, project_list_view, settings_view, timer_widget)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
