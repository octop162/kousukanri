from dataclasses import replace as dc_replace
from datetime import datetime
from enum import Enum, auto

from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsItem, QMenu,
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent,
)
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont, QCursor
from PySide6.QtCore import Qt, QRectF

from models.task import Task
import utils.constants as C
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
        y1 = time_to_y(task.start_time, reference_date)
        y2 = time_to_y(task.end_time, reference_date)
        super().__init__(QRectF(0, 0, BLOCK_WIDTH, y2 - y1))

        self.task = task
        self._reference_date = reference_date
        self._scene = scene
        self._mode = _Mode.NONE
        self._press_y: float = 0
        self._press_rect = QRectF()
        self._pre_drag_snapshot: Task | None = None
        self._font = QFont("Segoe UI", 9)
        self._project_font = QFont("Segoe UI", 8)

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

        text_color = QColor(self.task.color).darker(250)

        # Draw task name
        painter.setPen(QPen(text_color))
        painter.setFont(self._font)
        text_rect = r.adjusted(8, 4, -4, -4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.task.name)

        # Draw project name below task name (muted)
        project_name = self._get_project_name()
        if project_name:
            fm = painter.fontMetrics()
            name_height = fm.boundingRect(text_rect.toRect(),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                self.task.name).height()
            proj_color = QColor(text_color)
            proj_color.setAlpha(120)
            painter.setPen(QPen(proj_color))
            painter.setFont(self._project_font)
            proj_rect = text_rect.adjusted(0, name_height + 2, 0, 0)
            painter.drawText(proj_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, project_name)

    def _get_project_name(self) -> str:
        if not self.task.project_id or self._scene is None:
            return ""
        for p in self._scene._projects:
            if p.id == self.task.project_id:
                return p.name
        return ""

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

    # ── double-click to edit ──────────────────────────────────

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_edit_dialog()
        else:
            super().mouseDoubleClickEvent(event)

    # ── mouse press / move / release ──────────────────────────

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        y = event.pos().y()
        r = self.rect()
        self._press_y = event.scenePos().y()
        self._press_rect = QRectF(self.pos().x(), self.pos().y(), r.width(), r.height())
        self._pre_drag_snapshot = dc_replace(self.task)

        if y < RESIZE_HANDLE_PX:
            self._mode = _Mode.RESIZE_TOP
        elif y > r.height() - RESIZE_HANDLE_PX:
            self._mode = _Mode.RESIZE_BOTTOM
        else:
            self._mode = _Mode.MOVE
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        dy = event.scenePos().y() - self._press_y
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ShiftModifier:
            snap = C.SHIFT_SNAP_MINUTES
        elif mods & Qt.KeyboardModifier.AltModifier:
            snap = C.ALT_SNAP_MINUTES
        else:
            snap = None

        if self._mode == _Mode.RESIZE_TOP:
            raw_y = self._press_rect.y() + dy
            bottom_y = self._press_rect.y() + self._press_rect.height()
            snapped_y = time_to_y(y_to_time(max(0.0, raw_y), self._reference_date, snap))
            new_h = bottom_y - snapped_y
            if new_h > RESIZE_HANDLE_PX * 2 and snapped_y >= 0:
                self.setPos(self.pos().x(), snapped_y)
                self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

        elif self._mode == _Mode.RESIZE_BOTTOM:
            raw_bottom = self._press_rect.y() + self._press_rect.height() + dy
            snapped_bottom = time_to_y(y_to_time(raw_bottom, self._reference_date, snap))
            new_h = snapped_bottom - self._press_rect.y()
            if new_h > RESIZE_HANDLE_PX * 2:
                self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

        elif self._mode == _Mode.MOVE:
            raw_y = max(0.0, self._press_rect.y() + dy)
            snapped_y = time_to_y(y_to_time(raw_y, self._reference_date, snap))
            self.setPos(self.pos().x(), snapped_y)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._mode != _Mode.NONE:
            mods = event.modifiers()
            if mods & Qt.KeyboardModifier.ShiftModifier:
                snap = C.SHIFT_SNAP_MINUTES
            elif mods & Qt.KeyboardModifier.AltModifier:
                snap = C.ALT_SNAP_MINUTES
            else:
                snap = None
            if self._mode == _Mode.MOVE:
                self._sync_move(snap)
            else:
                self._sync_resize(snap)
            self._mode = _Mode.NONE
            self.unsetCursor()
            if self._scene is not None:
                self._scene.task_changed.emit(self._pre_drag_snapshot, self.task)
            self._pre_drag_snapshot = None

    def _sync_move(self, snap_minutes=None):
        """Move block, keeping duration. Jump to nearest free slot on overlap."""
        scene_y = self.pos().y()
        duration = self.task.end_time - self.task.start_time
        start = y_to_time(scene_y, self._reference_date, snap_minutes)
        end = start + duration

        if self._scene is not None:
            start, end = self._scene.resolve_move(start, end, exclude=self)

        self.task.start_time = start
        self.task.end_time = end
        self._apply_visual()

    def _sync_resize(self, snap_minutes=None):
        """Resize block, adjusting start/end to avoid overlaps."""
        scene_y = self.pos().y()
        h = self.rect().height()

        # Only snap the edge being dragged; keep the other edge unchanged
        if self._mode == _Mode.RESIZE_TOP:
            start = y_to_time(scene_y, self._reference_date, snap_minutes)
            end = self.task.end_time
        else:
            start = self.task.start_time
            end = y_to_time(scene_y + h, self._reference_date, snap_minutes)

        orig_start = self.task.start_time
        orig_end = self.task.end_time

        if self._scene is not None:
            blocks = self._scene._get_blocks(exclude=self)

            # Top resize: start moved earlier → snap to overlapping block boundaries
            if start < orig_start:
                for b in blocks:
                    if b.task.start_time < orig_start and b.task.end_time > start:
                        start = max(start, b.task.end_time)

            # Bottom resize: end moved later → snap to overlapping block boundaries
            if end > orig_end:
                for b in blocks:
                    if b.task.end_time > orig_end and b.task.start_time < end:
                        end = min(end, b.task.start_time)

        # If invalid range after snapping, revert to original
        if start >= end:
            start, end = orig_start, orig_end

        self.task.start_time = start
        self.task.end_time = end
        self._apply_visual()

    def _apply_visual(self):
        """Update rect position/size to match task times."""
        new_y = time_to_y(self.task.start_time, self._reference_date)
        new_h = time_to_y(self.task.end_time, self._reference_date) - new_y
        self.setPos(self.pos().x(), new_y)
        self.setRect(QRectF(0, 0, BLOCK_WIDTH, new_h))

    # ── context menu ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("編集")
        menu.addSeparator()
        delete_action = menu.addAction("削除")

        action = menu.exec(event.screenPos())

        if action is None:
            return

        if action == edit_action:
            self._open_edit_dialog()

        elif action == delete_action:
            if self._scene is not None:
                self._scene.task_deleted.emit(self.task.id)
                self._scene.removeItem(self)

    def _open_edit_dialog(self):
        from utils.constants import DEFAULT_BLOCK_COLOR
        from views.task_edit_dialog import TaskEditDialog

        projects = self._scene._projects if self._scene else []
        history = []
        if self._scene and self._scene._get_task_history:
            history = self._scene._get_task_history()
        pre_edit_snapshot = dc_replace(self.task)
        dlg = TaskEditDialog(
            self.task.name, self.task.project_id,
            self.task.start_time, self.task.end_time,
            projects, task_history=history, allow_delete=True,
        )
        if dlg.exec() != TaskEditDialog.DialogCode.Accepted:
            return
        if dlg.deleted:
            if self._scene is not None:
                self._scene.task_deleted.emit(self.task.id)
                self._scene.removeItem(self)
            return
        result = dlg.get_result()
        if result is None:
            return

        self.task.name = result["name"]
        self.task.start_time = result["start_time"]
        self.task.end_time = result["end_time"]
        self.task.project_id = result["project_id"]

        # Resolve project color
        project = None
        for p in projects:
            if p.id == result["project_id"]:
                project = p
                break
        self.task.color = project.color if project else DEFAULT_BLOCK_COLOR

        self._update_brush()
        self._apply_visual()
        if self._scene is not None:
            self._scene.task_changed.emit(pre_edit_snapshot, self.task)
