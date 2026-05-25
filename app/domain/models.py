from dataclasses import dataclass, field


@dataclass
class HistoricalPoint:
    timestamp: str  # ISO 8601 UTC e.g. "2026-05-23T10:15:00Z"
    temperature: float


@dataclass
class DhwStatus:
    temperature: float | None
    time_left: int
    available: bool
    heating_dhw: bool
    historical: list[HistoricalPoint] = field(default_factory=list)
