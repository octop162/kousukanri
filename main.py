import sys

from PySide6.QtWidgets import QApplication

from models.database import Database
from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget
from views.date_nav_widget import DateNavWidget
from views.routine_view import RoutineView
from views.export_view import ExportView
from views.main_window import MainWindow
from controllers.task_controller import TaskController


def apply_settings(settings: dict):
    """Apply settings to constants."""
    import utils.constants as C
    C.SNAP_MINUTES = settings["snap_minutes"]
    C.TIMELINE_START_HOUR = settings.get("timeline_start_hour", 0)
    C.TIMELINE_END_HOUR = settings.get("timeline_end_hour", 24)
    C.TIMELINE_HEIGHT = C.PIXELS_PER_HOUR * (C.TIMELINE_END_HOUR - C.TIMELINE_START_HOUR)


def main():
    app = QApplication(sys.argv)

    # Load settings and apply theme
    from utils.settings import load_settings
    from utils.theme import apply_theme, get_theme_colors
    settings = load_settings()
    apply_settings(settings)
    theme_name = settings.get("theme", "dark")
    apply_theme(app, theme_name)
    theme_colors = get_theme_colors(theme_name)

    # Database
    db = Database()

    scene = TimelineScene(theme_colors=theme_colors)
    list_view = TaskListView()
    project_list_view = ProjectListView()
    settings_view = SettingsView()
    settings_view.settings_changed.connect(apply_settings)
    timer_widget = TimerWidget(theme_colors=theme_colors)
    date_nav_widget = DateNavWidget()
    routine_view = RoutineView()
    export_view = ExportView()
    controller = TaskController(scene, database=db)
    controller.set_list_view(list_view)
    controller.set_project_list_view(project_list_view)
    controller.set_timer_widget(timer_widget)
    controller.set_date_nav_widget(date_nav_widget)
    controller.set_routine_view(routine_view)
    controller.set_export_view(export_view)

    window = MainWindow(scene, list_view, project_list_view, settings_view, timer_widget, date_nav_widget, routine_view, export_view)
    window.show()

    controller.load_from_db()

    app.aboutToQuit.connect(db.close)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
