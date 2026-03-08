import sys

from PySide6.QtWidgets import QApplication

from views.timeline_scene import TimelineScene
from views.task_list_view import TaskListView
from views.project_list_view import ProjectListView
from views.settings_view import SettingsView
from views.timer_widget import TimerWidget
from views.date_nav_widget import DateNavWidget
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

    scene = TimelineScene(theme_colors=theme_colors)
    list_view = TaskListView()
    project_list_view = ProjectListView()
    settings_view = SettingsView()
    settings_view.settings_changed.connect(apply_settings)
    timer_widget = TimerWidget()
    date_nav_widget = DateNavWidget()
    controller = TaskController(scene)
    controller.set_list_view(list_view)
    controller.set_project_list_view(project_list_view)
    controller.set_timer_widget(timer_widget)
    controller.set_date_nav_widget(date_nav_widget)

    window = MainWindow(scene, list_view, project_list_view, settings_view, timer_widget, date_nav_widget)
    window.show()

    # ── Sample data for testing ──
    from datetime import datetime, timedelta
    from models.project import Project
    from models.task import Task

    now = datetime.now().replace(second=0, microsecond=0)

    proj_dev = Project(name="開発")
    proj_mtg = Project(name="ミーティング")
    proj_doc = Project(name="ドキュメント")

    for proj in [proj_dev, proj_mtg, proj_doc]:
        controller._on_project_created(proj)

    sample_tasks = [
        Task(name="コードレビュー", start_time=now - timedelta(hours=3), end_time=now - timedelta(hours=2),
             color=proj_dev.color, project_id=proj_dev.id),
        Task(name="週次定例", start_time=now - timedelta(hours=2), end_time=now - timedelta(hours=1),
             color=proj_mtg.color, project_id=proj_mtg.id),
        Task(name="API設計書作成", start_time=now - timedelta(hours=1), end_time=now,
             color=proj_doc.color, project_id=proj_doc.id),
    ]
    for task in sample_tasks:
        controller._on_task_created(task)
        scene.add_task_block(task)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
