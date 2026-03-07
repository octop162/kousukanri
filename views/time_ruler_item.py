from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCore import QRectF, Qt

from utils.constants import (
    PIXELS_PER_HOUR, TIMELINE_START_HOUR, TIMELINE_END_HOUR,
    RULER_WIDTH, RULER_TICK_MAJOR, RULER_TICK_MINOR, TIMELINE_HEIGHT,
    BLOCK_LEFT, BLOCK_WIDTH,
)


class TimeRulerItem(QGraphicsItem):
    """Draws time labels on the left and horizontal grid lines."""

    def __init__(self):
        super().__init__()
        self._font = QFont("Segoe UI", 9)
        self.setZValue(-10)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, BLOCK_LEFT + BLOCK_WIDTH + 20, TIMELINE_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setFont(self._font)
        pen_major = QPen(QColor("#555555"), 1)
        pen_minor = QPen(QColor("#333333"), 1)
        pen_text = QPen(QColor("#CCCCCC"))

        total_minutes = (TIMELINE_END_HOUR - TIMELINE_START_HOUR) * 60
        scene_width = BLOCK_LEFT + BLOCK_WIDTH + 20

        for m in range(0, total_minutes + 1, RULER_TICK_MINOR):
            y = (m / 60.0) * PIXELS_PER_HOUR
            is_major = (m % RULER_TICK_MAJOR == 0)

            if is_major:
                painter.setPen(pen_major)
                painter.drawLine(RULER_WIDTH, int(y), int(scene_width), int(y))
                # Hour label
                hour = TIMELINE_START_HOUR + m // 60
                painter.setPen(pen_text)
                painter.drawText(
                    0, int(y) - 8, RULER_WIDTH - 6, 20,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{hour:02d}:00",
                )
            else:
                painter.setPen(pen_minor)
                painter.drawLine(RULER_WIDTH, int(y), int(scene_width), int(y))
