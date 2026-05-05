import logging
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.forecast_calculator import ForecastCalculator, HistoricalSalePoint
from app.domain.forecast_dates import default_forecast_date
from app.models.forecast import Forecast
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.store_repository import StoreRepository

logger = logging.getLogger(__name__)


class StoreNotFoundError(Exception):
    pass


class ForecastService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        calculator: ForecastCalculator | None = None,
    ):
        self.settings = settings
        self.store_repository = StoreRepository(db)
        self.product_repository = ProductRepository(db)
        self.sale_repository = SaleRepository(db)
        self.forecast_repository = ForecastRepository(db)
        self.calculator = calculator or ForecastCalculator()

    def generate_for_date(self, forecast_date: date | None = None) -> tuple[date, int]:
        target_date = forecast_date or default_forecast_date(self.settings)
        logger.info(
            "forecast_generation_started forecast_date=%s lookback_days=%s",
            target_date,
            self.settings.forecast_lookback_days,
        )
        stores = self.store_repository.list_all()
        products = self.product_repository.list_all()
        logger.info(
            "forecast_generation_loaded_dimensions stores=%s products=%s",
            len(stores),
            len(products),
        )
        generated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        forecast_rows: list[Forecast] = []

        for store in stores:
            for product in products:
                history = self.sale_repository.list_history(
                    store_id=store.id,
                    product_id=product.id,
                    forecast_date=target_date,
                    lookback_days=self.settings.forecast_lookback_days,
                )
                historical_points = [
                    HistoricalSalePoint(sold_at=sale.sold_at, quantity=sale.quantity)
                    for sale in history
                ]

                predictions = self.calculator.calculate_hourly_average(
                    historical_points,
                    target_date=target_date,
                )
                forecast_rows.extend(
                    Forecast(
                        store_id=store.id,
                        product_id=product.id,
                        forecast_date=target_date,
                        hour=prediction.hour,
                        predicted_quantity=prediction.predicted_quantity,
                        generated_at=generated_at,
                    )
                    for prediction in predictions
                )

        rows_generated = self.forecast_repository.upsert_many(forecast_rows)
        logger.info(
            "forecast_generation_completed forecast_date=%s rows_generated=%s",
            target_date,
            rows_generated,
        )
        return target_date, rows_generated

    def get_forecasts(self, *, store_id: int, forecast_date: date) -> list[Forecast]:
        logger.info("forecast_read_requested store_id=%s forecast_date=%s", store_id, forecast_date)
        if self.store_repository.get(store_id) is None:
            logger.warning("forecast_read_store_not_found store_id=%s", store_id)
            raise StoreNotFoundError(f"store {store_id} was not found")

        forecasts = self.forecast_repository.list_by_store_and_date(
            store_id=store_id,
            forecast_date=forecast_date,
        )
        logger.info(
            "forecast_read_completed store_id=%s forecast_date=%s rows=%s",
            store_id,
            forecast_date,
            len(forecasts),
        )
        return forecasts
