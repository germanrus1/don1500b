from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SensorStatus(Enum):
    OK = "ok"
    WARN_LOW = "warn_low"
    WARN_HIGH = "warn_high"
    CRITICAL = "critical"


@dataclass
class SensorReading:
    name: str
    display_name: str
    value: float
    unit: str
    status: SensorStatus
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def has_error(self) -> bool:
        return self.status != SensorStatus.OK
