from pydantic import BaseModel


class HistoricalPointSchema(BaseModel):
    timestamp: str
    temperature: float


class DhwStatusSchema(BaseModel):
    model_config = {"from_attributes": True}

    temperature: float | None
    time_left: int
    available: bool
    heating_dhw: bool
    historical: list[HistoricalPointSchema]
