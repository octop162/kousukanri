from dataclasses import dataclass, field
from datetime import datetime
import uuid

from utils.constants import DEFAULT_BLOCK_COLOR


@dataclass
class Task:
    name: str
    start_time: datetime
    end_time: datetime
    color: str = DEFAULT_BLOCK_COLOR
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_id: str | None = None
