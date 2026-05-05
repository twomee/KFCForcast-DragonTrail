from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ForecastGenerateRequest(BaseModel):
    forecast_date: date | None = None


class ForecastGenerateResponse(BaseModel):
    forecast_date: date
    rows_generated: int


class ForecastRead(BaseModel):
    id: int
    store_id: int
    store_name: str
    product_id: int
    product_name: str
    forecast_date: date
    hour: int = Field(ge=0, le=23)
    predicted_quantity: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)

