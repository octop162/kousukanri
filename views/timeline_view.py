from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

from views.timeline_scene import TimelineScene


class TimelineView(QGraphicsView):
    """QGraphicsView wrapper with scroll and antialiasing."""

    def __init__(self, scene: TimelineScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # Scroll to ~8:00 on startup
        from utils.constants import PIXELS_PER_HOUR
        self.centerOn(0, 8 * PIXELS_PER_HOUR)
