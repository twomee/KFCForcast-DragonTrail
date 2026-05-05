from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sale import Sale


class SaleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_history(
        self,
        *,
        store_id: int,
        product_id: int,
        forecast_date: date,
        lookback_days: int,
    ) -> list[Sale]:
        start_date = forecast_date - timedelta(days=lookback_days)
        start = datetime.combine(start_date, time.min)
        end = datetime.combine(forecast_date, time.min)

        statement = (
            select(Sale)
            .where(
                Sale.store_id == store_id,
                Sale.product_id == product_id,
                Sale.sold_at >= start,
                Sale.sold_at < end,
            )
            .order_by(Sale.sold_at)
        )
        return list(self.db.scalars(statement))

