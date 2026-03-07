from datetime import datetime, timedelta

# Timeline layout (vertical: Y axis = time)
PIXELS_PER_HOUR = 200
TIMELINE_START_HOUR = 0
TIMELINE_END_HOUR = 24
TIMELINE_HEIGHT = PIXELS_PER_HOUR * (TIMELINE_END_HOUR - TIMELINE_START_HOUR)

# Task block
BLOCK_WIDTH = 260
BLOCK_CORNER_RADIUS = 6
RESIZE_HANDLE_PX = 8
MIN_BLOCK_DRAG_PX = 10  # minimum drag distance to create a block

# Snap
SNAP_MINUTES = 5

# Ruler
RULER_WIDTH = 50  # left-side ruler column width
RULER_TICK_MAJOR = 60   # minutes between major ticks (1h)
RULER_TICK_MINOR = 15   # minutes between minor ticks

# Block area starts after the ruler
BLOCK_LEFT = RULER_WIDTH + 8

# Colors
DEFAULT_BLOCK_COLOR = "#4A90D9"  # プロジェクトなしタスクのデフォルト色
DEFAULT_BLOCK_COLORS = [
    "#4A90D9", "#E74C3C", "#2ECC71", "#F39C12",
    "#9B59B6", "#1ABC9C", "#E67E22", "#3498DB",
]


def time_to_y(t: datetime) -> float:
    """Convert a datetime to a Y pixel coordinate."""
    midnight = t.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed = (t - midnight).total_seconds() / 3600.0
    return (elapsed - TIMELINE_START_HOUR) * PIXELS_PER_HOUR


def y_to_time(y: float, reference_date: datetime | None = None) -> datetime:
    """Convert a Y pixel coordinate to a datetime, snapped to SNAP_MINUTES."""
    hours = y / PIXELS_PER_HOUR + TIMELINE_START_HOUR
    total_minutes = hours * 60
    # Snap
    snapped = round(total_minutes / SNAP_MINUTES) * SNAP_MINUTES
    snapped = max(0, min(snapped, 24 * 60))

    if reference_date is None:
        reference_date = datetime.now()
    base = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(minutes=snapped)
