from datetime import datetime

from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtGui import QColor, QBrush, QPen, QTransform
from PySide6.QtCore import Signal, QRectF

import utils.constants as C
from utils.constants import time_to_y, y_to_time
from models.task import Task
from views.time_ruler_item import TimeRulerItem
from views.task_block_item import TaskBlockItem


class TimelineScene(QGraphicsScene):
    task_created = Signal(Task)
    task_changed = Signal(Task)
    task_deleted = Signal(str)  # task id

    def __init__(self, parent=None, theme_colors: dict | None = None):
        super().__init__(parent)
        self._reference_date = datetime.now()
        self._projects = []
        self._theme_colors = theme_colors or {}
        self._ruler = TimeRulerItem(theme_colors=self._theme_colors)
        self.addItem(self._ruler)

        scene_w = C.BLOCK_LEFT + C.BLOCK_WIDTH + 20
        self.setSceneRect(0, 0, scene_w, C.TIMELINE_HEIGHT)
        bg = self._theme_colors.get("timeline_bg", "#1E1E1E")
        self.setBackgroundBrush(QBrush(QColor(bg)))

        # Drag-to-create state
        self._drag_creating = False
        self._drag_start_y: float = 0
        self._temp_rect: QGraphicsRectItem | None = None

    # ── helpers ───────────────────────────────────────────────

    def _get_blocks(self, exclude: TaskBlockItem | None = None) -> list[TaskBlockItem]:
        return [
            item for item in self.items()
            if isinstance(item, TaskBlockItem) and item is not exclude
        ]

    def resolve_overlap(self, start: datetime, end: datetime,
                        exclude: TaskBlockItem | None = None) -> tuple[datetime, datetime] | None:
        """Adjust start/end to avoid overlapping existing blocks.

        Returns adjusted (start, end) or None if the slot is fully blocked.
        """
        blocks = self._get_blocks(exclude)
        # Sort by start_time
        others = sorted([(b.task.start_time, b.task.end_time) for b in blocks])

        start_blocked = False
        end_blocked = False

        for bs, be in others:
            # Check if start falls inside this block
            if bs < start < be:
                start = be
                start_blocked = True
            # Check if end falls inside this block
            if bs < end < be:
                end = bs
                end_blocked = True

        if start_blocked and end_blocked:
            return None

        # Check if our range fully contains any block (both start & end are outside
        # but a block sits in between) — shrink to nearest boundary
        for bs, be in others:
            if start < bs < end and start < be < end:
                # A block sits entirely inside our range — can't create
                return None
            if start < bs < end:
                end = bs
            elif start < be < end:
                start = be

        if start >= end:
            return None

        return (start, end)

    def resolve_move(self, start: datetime, end: datetime,
                     exclude: TaskBlockItem | None = None) -> tuple[datetime, datetime]:
        """Move a block (keeping duration) to avoid overlaps.

        Tries the requested position first. If it overlaps, snaps to just after
        or just before the colliding block. Falls back to original position.
        """
        duration = end - start
        blocks = self._get_blocks(exclude)
        others = sorted([(b.task.start_time, b.task.end_time) for b in blocks])

        def has_overlap(s, e):
            for bs, be in others:
                if s < be and e > bs:
                    return True
            return False

        # No collision — use as-is
        if not has_overlap(start, end):
            return (start, end)

        # Collect candidate positions: just after or just before each colliding block
        candidates = []
        for bs, be in others:
            if start < be and end > bs:
                # Try after this block
                cand_start = be
                cand_end = be + duration
                candidates.append((cand_start, cand_end, abs((cand_start - start).total_seconds())))
                # Try before this block
                cand_end2 = bs
                cand_start2 = bs - duration
                candidates.append((cand_start2, cand_end2, abs((cand_start2 - start).total_seconds())))

        # Sort by distance from original position (prefer closest)
        candidates.sort(key=lambda c: c[2])

        midnight = start.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        day_start = midnight + timedelta(hours=C.TIMELINE_START_HOUR)
        day_end = midnight + timedelta(hours=C.TIMELINE_END_HOUR)

        for cs, ce, _ in candidates:
            if cs >= day_start and ce <= day_end and not has_overlap(cs, ce):
                return (cs, ce)

        # Nothing worked — return original (keep in place)
        if exclude is not None:
            return (exclude.task.start_time, exclude.task.end_time)
        return (start, end)

    def clear_task_blocks(self):
        """Remove all TaskBlockItems from the scene (keep ruler and other items)."""
        for block in self._get_blocks():
            self.removeItem(block)

    def set_reference_date(self, dt):
        """Update the reference date used for coordinate calculations."""
        self._reference_date = dt

    def add_task_block(self, task: Task) -> TaskBlockItem:
        block = TaskBlockItem(task, self._reference_date, scene=self)
        self.addItem(block)
        return block

    def set_theme_colors(self, colors: dict):
        """Update theme colors at runtime (background + ruler)."""
        self._theme_colors = colors
        bg = colors.get("timeline_bg", "#1E1E1E")
        self.setBackgroundBrush(QBrush(QColor(bg)))
        self._ruler.set_theme_colors(colors)
        self.update()

    def set_projects(self, projects):
        """Update the project list (used by context menus)."""
        self._projects = list(projects)

    def update_task_block(self, task: Task):
        """Update an existing block's visual appearance, position, and size."""
        for block in self._get_blocks():
            if block.task.id == task.id:
                block.task = task
                block.setBrush(QBrush(QColor(task.color)))
                block.setPen(QPen(QColor(task.color).darker(130), 1))
                new_y = time_to_y(task.start_time)
                new_h = time_to_y(task.end_time) - new_y
                block.setPos(C.BLOCK_LEFT, new_y)
                block.setRect(QRectF(0, 0, C.BLOCK_WIDTH, max(new_h, 1)))
                block.update()
                return

    def apply_zoom(self):
        """Reposition all blocks and update scene rect after zoom scale change."""
        scene_w = C.BLOCK_LEFT + C.BLOCK_WIDTH + 20
        self.setSceneRect(0, 0, scene_w, C.TIMELINE_HEIGHT)
        # Reposition all task blocks
        for block in self._get_blocks():
            block._apply_visual()
        # Repaint ruler
        self._ruler.prepareGeometryChange()
        self._ruler.update()

    def _find_gap_at(self, y: float) -> tuple[datetime, datetime] | None:
        """Return the (start, end) of the gap surrounding scene-Y position y."""
        from datetime import timedelta

        clicked_time = y_to_time(y, self._reference_date)
        midnight = self._reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = midnight + timedelta(hours=C.TIMELINE_START_HOUR)
        day_end = midnight + timedelta(hours=C.TIMELINE_END_HOUR)

        blocks = self._get_blocks()
        others = sorted([(b.task.start_time, b.task.end_time) for b in blocks])

        # Check clicked point isn't inside a block
        for bs, be in others:
            if bs <= clicked_time <= be:
                return None

        # Find gap boundaries
        gap_start = day_start
        gap_end = day_end
        for bs, be in others:
            if be <= clicked_time:
                gap_start = max(gap_start, be)
            if bs >= clicked_time:
                gap_end = min(gap_end, bs)
                break

        if gap_start >= gap_end:
            return None
        return (gap_start, gap_end)

    # ── double-click to fill gap ──────────────────────────────

    def mouseDoubleClickEvent(self, event):
        if event.button().value != 1:
            super().mouseDoubleClickEvent(event)
            return

        pos = event.scenePos()
        if pos.x() < C.BLOCK_LEFT:
            super().mouseDoubleClickEvent(event)
            return

        transform = self.views()[0].transform() if self.views() else QTransform()
        item = self.itemAt(pos, transform)
        if item is not None and not isinstance(item, TimeRulerItem):
            super().mouseDoubleClickEvent(event)
            return

        gap = self._find_gap_at(pos.y())
        if gap is not None:
            start, end = gap
            color = C.DEFAULT_BLOCK_COLOR
            task = Task(name="あたらしいタスク", start_time=start, end_time=end, color=color)
            self.add_task_block(task)
            self.task_created.emit(task)

    # ── drag-to-create ───────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button().value != 1:
            super().mousePressEvent(event)
            return

        transform = self.views()[0].transform() if self.views() else QTransform()
        item = self.itemAt(event.scenePos(), transform)
        if item is not None and not isinstance(item, TimeRulerItem):
            super().mousePressEvent(event)
            return

        pos = event.scenePos()
        if pos.x() < C.BLOCK_LEFT:
            super().mousePressEvent(event)
            return

        self._drag_creating = True
        self._drag_start_y = pos.y()

        self._temp_rect = QGraphicsRectItem(QRectF(C.BLOCK_LEFT, pos.y(), C.BLOCK_WIDTH, 0))
        self._temp_rect.setBrush(QBrush(QColor(255, 255, 255, 40)))
        self._temp_rect.setPen(QPen(QColor(255, 255, 255, 100)))
        self._temp_rect.setZValue(100)
        self.addItem(self._temp_rect)

    def mouseMoveEvent(self, event):
        if self._drag_creating and self._temp_rect is not None:
            y1 = min(self._drag_start_y, event.scenePos().y())
            y2 = max(self._drag_start_y, event.scenePos().y())
            self._temp_rect.setRect(QRectF(C.BLOCK_LEFT, y1, C.BLOCK_WIDTH, y2 - y1))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_creating:
            self._drag_creating = False
            if self._temp_rect is not None:
                self.removeItem(self._temp_rect)
                self._temp_rect = None

            y1 = min(self._drag_start_y, event.scenePos().y())
            y2 = max(self._drag_start_y, event.scenePos().y())

            if (y2 - y1) >= C.MIN_BLOCK_DRAG_PX:
                start = y_to_time(y1, self._reference_date)
                end = y_to_time(y2, self._reference_date)
                if start < end:
                    result = self.resolve_overlap(start, end)
                    if result is not None:
                        start, end = result
                        color = C.DEFAULT_BLOCK_COLOR
                        task = Task(
                            name="あたらしいタスク",
                            start_time=start,
                            end_time=end,
                            color=color,
                        )
                        self.add_task_block(task)
                        self.task_created.emit(task)
        else:
            super().mouseReleaseEvent(event)
