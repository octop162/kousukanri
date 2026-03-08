import utils.constants as C

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCore import QRectF, Qt


class TimeRulerItem(QGraphicsItem):
    """Draws time labels on the left and horizontal grid lines."""

    def __init__(self, theme_colors: dict | None = None):
        super().__init__()
        self._font = QFont("Segoe UI", 9)
        self._theme = theme_colors or {}
        self.setZValue(-10)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, C.BLOCK_LEFT + C.BLOCK_WIDTH + 20, C.TIMELINE_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setFont(self._font)
        pen_major = QPen(QColor(self._theme.get("ruler_major", "#555555")), 1)
        pen_minor = QPen(QColor(self._theme.get("ruler_minor", "#333333")), 1)
        pen_text = QPen(QColor(self._theme.get("ruler_text", "#CCCCCC")))

        total_minutes = (C.TIMELINE_END_HOUR - C.TIMELINE_START_HOUR) * 60
        scene_width = C.BLOCK_LEFT + C.BLOCK_WIDTH + 20

        for m in range(0, total_minutes + 1, C.RULER_TICK_MINOR):
            y = (m / 60.0) * C.PIXELS_PER_HOUR
            is_major = (m % C.RULER_TICK_MAJOR == 0)

            if is_major:
                painter.setPen(pen_major)
                painter.drawLine(C.RULER_WIDTH, int(y), int(scene_width), int(y))
                # Hour label
                hour = C.TIMELINE_START_HOUR + m // 60
                painter.setPen(pen_text)
                painter.drawText(
                    0, int(y) - 8, C.RULER_WIDTH - 6, 20,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{hour:02d}:00",
                )
            else:
                painter.setPen(pen_minor)
                painter.drawLine(C.RULER_WIDTH, int(y), int(scene_width), int(y))
