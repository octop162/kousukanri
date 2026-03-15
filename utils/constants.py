from datetime import datetime, timedelta

# Timeline layout (vertical: Y axis = time)
BASE_PIXELS_PER_HOUR = 200
PIXELS_PER_HOUR = 200  # mutable — updated by set_zoom_scale()
TIMELINE_START_HOUR = 0
TIMELINE_END_HOUR = 24
TIMELINE_HEIGHT = PIXELS_PER_HOUR * (TIMELINE_END_HOUR - TIMELINE_START_HOUR)

# Task block
BLOCK_WIDTH = 260
BLOCK_CORNER_RADIUS = 6
RESIZE_HANDLE_PX = 8
MIN_BLOCK_DRAG_PX = 10  # minimum drag distance to create a block

# Snap
SNAP_MINUTES = 1
SHIFT_SNAP_MINUTES = 5   # snap interval when Shift is held (overridden by settings)
ALT_SNAP_MINUTES = 10    # snap interval when Alt is held (overridden by settings)

# Ruler
RULER_WIDTH = 50  # left-side ruler column width
RULER_TICK_MAJOR = 60    # minutes between major ticks (1h)
RULER_TICK_MINOR = 15    # minutes between minor ticks (mutable)
RULER_TICK_SUB_MINOR = 5 # minutes between sub-minor ticks (mutable)

# Block area starts after the ruler
BLOCK_LEFT = RULER_WIDTH + 8

# Colors
DEFAULT_BLOCK_COLOR = "#64B5F6"  # プロジェクトなしタスクのデフォルト色
DEFAULT_BLOCK_COLORS = [
    "#64B5F6", "#E57373", "#81C784", "#FFD54F",
    "#BA68C8", "#4DB6AC", "#FFB74D", "#7986CB",
]


def set_zoom_scale(scale: float):
    """Update PIXELS_PER_HOUR, TIMELINE_HEIGHT, RULER_TICK_MINOR based on zoom scale."""
    global PIXELS_PER_HOUR, TIMELINE_HEIGHT, RULER_TICK_MINOR, RULER_TICK_SUB_MINOR
    PIXELS_PER_HOUR = BASE_PIXELS_PER_HOUR * scale
    TIMELINE_HEIGHT = PIXELS_PER_HOUR * (TIMELINE_END_HOUR - TIMELINE_START_HOUR)
    # If minor tick spacing would be < 35px, double the interval
    minor_px = (15 / 60.0) * PIXELS_PER_HOUR
    RULER_TICK_MINOR = 30 if minor_px < 35 else 15
    # Hide sub-minor ticks if they'd be too dense (< 10px apart)
    sub_minor_px = (5 / 60.0) * PIXELS_PER_HOUR
    RULER_TICK_SUB_MINOR = 0 if sub_minor_px < 10 else 5


def time_to_y(t: datetime) -> float:
    """Convert a datetime to a Y pixel coordinate."""
    midnight = t.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed = (t - midnight).total_seconds() / 3600.0
    return (elapsed - TIMELINE_START_HOUR) * PIXELS_PER_HOUR


def y_to_time(y: float, reference_date: datetime | None = None, snap_minutes: int | None = None) -> datetime:
    """Convert a Y pixel coordinate to a datetime, snapped to snap_minutes (default: SNAP_MINUTES)."""
    hours = y / PIXELS_PER_HOUR + TIMELINE_START_HOUR
    total_minutes = hours * 60
    # Snap
    snap = snap_minutes if snap_minutes is not None else SNAP_MINUTES
    snapped = round(total_minutes / snap) * snap
    snapped = max(0, min(snapped, 24 * 60))

    if reference_date is None:
        reference_date = datetime.now()
    base = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(minutes=snapped)
