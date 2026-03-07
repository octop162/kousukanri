from datetime import datetime
from enum import Enum, auto

from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsItem, QMenu, QInputDialog,
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent,
)
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont, QCursor
from PySide6.QtCore import Qt, QRectF

from models.task import Task
from utils.constants import (
    BLOCK_WIDTH, BLOCK_LEFT, BLOCK_CORNER_RADIUS, RESIZE_HANDLE_PX,
    time_to_y, y_to_time,
)


class _Mode(Enum):
    NONE = auto()
    MOVE = auto()
    RESIZE_TOP = auto()
    RESIZE_BOTTOM = auto()


class TaskBlockItem(QGraphicsRectItem):
    """A draggable, resizable rectangle representing a task on the vertical timeline."""

    def __init__(self, task: Task, reference_date: datetime, scene=None):
        y1 = time_to_y(task.start_time)
        y2 = time_to_y(task.end_time)
        super().__init__(QRectF(0, 0, BLOCK_WIDTH, y2 - y1))

        self.task = task
        self._reference_date = reference_date
        self._scene = scene
        self._mode = _Mode.NONE
        self._press_y: float = 0
        self._press_rect = QRectF()
        self._font = QFont("Segoe UI", 9)

        self.setPos(BLOCK_LEFT, y1)

        self.setAcceptHoverEvents(True)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(10)
        self._update_brush()

    # ── painting ──────────────────────────────────────────────

    def _update_brush(self):
        self.setBrush(QBrush(QColor(self.task.color)))
        self.setPen(QPen(QColor(self.task.color).darker(130), 1))

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(r, BLOCK_CORNER_RADIUS, BLOCK_CORNER_RADIUS)

        # Draw task name
        painter.setPen(QPen(QColor("white")))
        painter.setFont(self._font)
        text_rect = r.adjusted(8, 4, -4, -4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self.task.name)

    # ── hover cursor ──────────────────────────────────────────

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        y = event.pos().y()
        r = self.rect()
        if y < RESIZE_HANDLE_PX or y > r.height() - RESIZE_HANDLE_PX:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def hoverLeaveEvent(self, event):
        self.unsetCursor()

    # ── mouse press / move / release ──────────────────────────

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        y = event.pos().y()
        r = self.rect()
        self._press_y = event.scenePos().y()
        self._press_rect = QRectF(self.pos().x(), self.pos().y(), r.width(), r.height())

        if y < RESIZE_HANDLE_PX:
            self._mode = _Mode.RESIZE_TOP
        elif y > r.height() - RESIZE_HANDLE_PX:
            self._mode = _Mode.RESIZE_BOTTOM
        else:
            self._mode = _Mode.MOVE
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        dy = event.scenePos().y() - self._press_y

        if self._mode == _Mode.RESIZE_TOP:
            new_y = self._press_rect.y() + dy
            new_h = self._press_rect.height() - dy
            if new_h > RESIZE_HANDLE_PX * 2 and new_y >= 0:
                self.setPos(self.pos().x(), new_y)
                self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

        elif self._mode == _Mode.RESIZE_BOTTOM:
            new_h = self._press_rect.height() + dy
            if new_h > RESIZE_HANDLE_PX * 2:
                self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

        elif self._mode == _Mode.MOVE:
            new_y = self._press_rect.y() + dy
            new_y = max(0, new_y)
            self.setPos(self.pos().x(), new_y)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._mode != _Mode.NONE:
            if self._mode == _Mode.MOVE:
                self._sync_move()
            else:
                self._sync_resize()
            self._mode = _Mode.NONE
            self.unsetCursor()
            if self._scene is not None:
                self._scene.task_changed.emit(self.task)

    def _sync_move(self):
        """Move block, keeping duration. Jump to nearest free slot on overlap."""
        scene_y = self.pos().y()
        h = self.rect().height()
        start = y_to_time(scene_y, self._reference_date)
        end = y_to_time(scene_y + h, self._reference_date)

        if self._scene is not None:
            start, end = self._scene.resolve_move(start, end, exclude=self)

        self.task.start_time = start
        self.task.end_time = end
        self._apply_visual()

    def _sync_resize(self):
        """Resize block, adjusting start/end to avoid overlaps."""
        scene_y = self.pos().y()
        h = self.rect().height()
        start = y_to_time(scene_y, self._reference_date)
        end = y_to_time(scene_y + h, self._reference_date)

        if self._scene is not None:
            result = self._scene.resolve_overlap(start, end, exclude=self)
            if result is not None:
                start, end = result

        self.task.start_time = start
        self.task.end_time = end
        self._apply_visual()

    def _apply_visual(self):
        """Update rect position/size to match task times."""
        new_y = time_to_y(self.task.start_time)
        new_h = time_to_y(self.task.end_time) - new_y
        self.setPos(self.pos().x(), new_y)
        self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

    # ── context menu ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        from utils.constants import DEFAULT_BLOCK_COLOR

        menu = QMenu()
        rename_action = menu.addAction("Rename")

        # Project submenu
        project_menu = menu.addMenu("Change Project")
        none_action = project_menu.addAction("(なし)")
        project_actions = {}
        if self._scene is not None:
            for proj in self._scene._projects:
                act = project_menu.addAction(proj.name)
                project_actions[act] = proj

        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.screenPos())

        if action is None:
            return

        if action == rename_action:
            name, ok = QInputDialog.getText(None, "Rename Task", "Task name:", text=self.task.name)
            if ok and name:
                self.task.name = name
                self.update()
                if self._scene is not None:
                    self._scene.task_changed.emit(self.task)

        elif action == none_action:
            self.task.project_id = None
            self.task.color = DEFAULT_BLOCK_COLOR
            self._update_brush()
            self.update()
            if self._scene is not None:
                self._scene.task_changed.emit(self.task)

        elif action in project_actions:
            proj = project_actions[action]
            self.task.project_id = proj.id
            self.task.color = proj.color
            self._update_brush()
            self.update()
            if self._scene is not None:
                self._scene.task_changed.emit(self.task)

        elif action == delete_action:
            if self._scene is not None:
                self._scene.task_deleted.emit(self.task.id)
                self._scene.removeItem(self)
