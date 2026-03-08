from dataclasses import dataclass, field
import uuid


@dataclass
class Routine:
    name: str
    project_id: str | None = None
    start_hour: int = 9
    start_minute: int = 0
    end_hour: int = 9
    end_minute: int = 30
    order: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
