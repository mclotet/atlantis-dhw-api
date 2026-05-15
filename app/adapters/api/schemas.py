from pydantic import BaseModel


class HistoricalPointSchema(BaseModel):
    dt: int
    temp: float


class DhwStatusSchema(BaseModel):
    model_config = {"from_attributes": True}

    temperature: float | None
    minutes_left: int
    available: bool
    heating_dhw: bool
    dhw_historical: list[HistoricalPointSchema]
