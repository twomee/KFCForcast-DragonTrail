import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.forecast import ForecastGenerateRequest, ForecastGenerateResponse, ForecastRead
from app.services.forecast_service import ForecastService, StoreNotFoundError

router = APIRouter(prefix="/forecasts", tags=["forecasts"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ForecastRead])
async def list_forecasts(
    store_id: int = Query(gt=0),
    forecast_date: date = Query(alias="date"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[ForecastRead]:
    logger.info("api_list_forecasts store_id=%s forecast_date=%s", store_id, forecast_date)
    service = ForecastService(db, settings)
    try:
        forecasts = service.get_forecasts(store_id=store_id, forecast_date=forecast_date)
    except StoreNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        ) from exc

    return [
        ForecastRead(
            id=forecast.id,
            store_id=forecast.store_id,
            store_name=forecast.store.name,
            product_id=forecast.product_id,
            product_name=forecast.product.name,
            forecast_date=forecast.forecast_date,
            hour=forecast.hour,
            predicted_quantity=forecast.predicted_quantity,
        )
        for forecast in forecasts
    ]


@router.post("/generate", response_model=ForecastGenerateResponse)
async def generate_forecasts(
    payload: ForecastGenerateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ForecastGenerateResponse:
    logger.info("api_generate_forecasts forecast_date=%s", payload.forecast_date)
    forecast_date, rows_generated = ForecastService(db, settings).generate_for_date(
        payload.forecast_date
    )
    return ForecastGenerateResponse(forecast_date=forecast_date, rows_generated=rows_generated)
