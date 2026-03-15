from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter

from views.timeline_scene import TimelineScene
from utils.constants import set_zoom_scale

ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
DEFAULT_ZOOM_INDEX = 2  # 0.75x


class TimelineView(QGraphicsView):
    """QGraphicsView wrapper with scroll, antialiasing, and vertical zoom."""

    zoom_changed = Signal(float)

    def __init__(self, scene: TimelineScene, parent=None):
        super().__init__(scene, parent)
        self._scene = scene
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        self._zoom_index = DEFAULT_ZOOM_INDEX

        # Apply default zoom scale
        default_level = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        set_zoom_scale(default_level)
        self._scene.apply_zoom()

        # Scroll so current time is at ~25% from top
        from utils.constants import PIXELS_PER_HOUR
        now = __import__('datetime').datetime.now()
        current_hours = now.hour + now.minute / 60.0
        current_y = current_hours * PIXELS_PER_HOUR
        viewport_h = self.viewport().height() or 600
        center_y = current_y + viewport_h * 0.25
        self.centerOn(0, center_y)

    def zoom_in(self):
        if self._zoom_index < len(ZOOM_LEVELS) - 1:
            self._zoom_index += 1
            self._apply_zoom()

    def zoom_out(self):
        if self._zoom_index > 0:
            self._zoom_index -= 1
            self._apply_zoom()

    def _apply_zoom(self):
        level = ZOOM_LEVELS[self._zoom_index]
        # Remember center position in scene time before zoom
        center_scene_y = self.mapToScene(self.viewport().rect().center()).y()
        from utils.constants import PIXELS_PER_HOUR as old_pph
        # Convert old y to fractional hours
        center_hours = center_scene_y / old_pph

        # Apply new scale
        set_zoom_scale(level)
        self._scene.apply_zoom()

        # Restore center at same time position
        from utils.constants import PIXELS_PER_HOUR as new_pph
        new_center_y = center_hours * new_pph
        self.centerOn(0, new_center_y)

        self.zoom_changed.emit(level)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
