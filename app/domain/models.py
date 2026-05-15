from dataclasses import dataclass, field


@dataclass
class HistoricalPoint:
    dt: int    # Unix timestamp (seconds)
    temp: float


@dataclass
class DhwStatus:
    temperature: float | None
    minutes_left: int
    available: bool
    heating_dhw: bool
    dhw_historical: list[HistoricalPoint] = field(default_factory=list)
