import random
from dataclasses import dataclass, field
import uuid

from utils.constants import DEFAULT_BLOCK_COLORS


@dataclass
class Project:
    name: str
    color: str = field(default_factory=lambda: random.choice(DEFAULT_BLOCK_COLORS))
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
