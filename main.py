import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from models.database import Database
from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget
from views.date_nav_widget import DateNavWidget
from views.routine_view import RoutineView
from views.main_window import MainWindow
from controllers.task_controller import TaskController


def apply_settings(settings: dict):
    """Apply settings to constants."""
    import utils.constants as C
    C.SNAP_MINUTES = settings["snap_minutes"]
    C.SHIFT_SNAP_MINUTES = settings.get("shift_snap_minutes", 5)
    C.CTRL_SNAP_MINUTES = settings.get("ctrl_snap_minutes", 10)
    C.TIMELINE_START_HOUR = settings.get("timeline_start_hour", 0)
    C.TIMELINE_END_HOUR = settings.get("timeline_end_hour", 24)
    C.TIMELINE_HEIGHT = C.PIXELS_PER_HOUR * (C.TIMELINE_END_HOUR - C.TIMELINE_START_HOUR)


def main():
    app = QApplication(sys.argv)

    # Prevent multiple instances — if already running, activate existing window
    socket = QLocalSocket()
    socket.connectToServer("kousu-kanri-single-instance")
    if socket.waitForConnected(500):
        socket.close()
        sys.exit(0)

    server = QLocalServer()
    QLocalServer.removeServer("kousu-kanri-single-instance")
    server.listen("kousu-kanri-single-instance")

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
    controller = TaskController(scene, database=db)
    controller.set_list_view(list_view)
    controller.set_project_list_view(project_list_view)
    controller.set_timer_widget(timer_widget)
    controller.set_date_nav_widget(date_nav_widget)
    controller.set_routine_view(routine_view)

    window = MainWindow(scene, list_view, project_list_view, settings_view, timer_widget, date_nav_widget, routine_view)
    window.set_controller(controller)
    if "--minimized" in sys.argv:
        window.hide()  # トレイのみ表示、ウィンドウは非表示
    else:
        window.show()

    # Handle connections from other instances (multiple-instance prevention)
    def _on_new_connection():
        conn = server.nextPendingConnection()
        if conn is None:
            return
        conn.waitForReadyRead(500)
        msg = bytes(conn.readAll()).decode("utf-8", errors="ignore")
        conn.close()
        if msg != "reload":
            window.showNormal()
            window.activateWindow()

    server.newConnection.connect(_on_new_connection)

    controller.load_from_db()

    # API server (optional, based on settings)
    api_srv = None
    if settings.get("api_server_enabled", False):
        try:
            from api_server import ApiNotifier, ApiServer
            api_notifier = ApiNotifier()
            api_notifier.data_changed.connect(controller.reload_current_date)
            api_srv = ApiServer(settings.get("api_port", 8321), api_notifier)
            api_srv.start()
        except OSError as e:
            print(f"API server failed to start: {e}", file=sys.stderr)

    app.aboutToQuit.connect(controller.stop_running_timer)
    if api_srv is not None:
        app.aboutToQuit.connect(api_srv.stop)
    app.aboutToQuit.connect(db.close)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
