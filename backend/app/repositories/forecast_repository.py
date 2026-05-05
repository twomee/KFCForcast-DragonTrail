from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, joinedload

from app.models.forecast import Forecast


class ForecastRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, forecasts: list[Forecast]) -> int:
        if not forecasts:
            return 0

        rows = [
            {
                "store_id": forecast.store_id,
                "product_id": forecast.product_id,
                "forecast_date": forecast.forecast_date,
                "hour": forecast.hour,
                "predicted_quantity": forecast.predicted_quantity,
                "generated_at": forecast.generated_at,
            }
            for forecast in forecasts
        ]

        dialect_name = self.db.bind.dialect.name if self.db.bind is not None else ""
        insert_statement = self._insert_statement_for_dialect(dialect_name, rows)
        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=["store_id", "product_id", "forecast_date", "hour"],
            set_={
                "predicted_quantity": insert_statement.excluded.predicted_quantity,
                "generated_at": insert_statement.excluded.generated_at,
            },
        )
        self.db.execute(upsert_statement)
        self.db.commit()
        return len(forecasts)

    def _insert_statement_for_dialect(self, dialect_name: str, rows: list[dict[str, object]]):
        if dialect_name == "postgresql":
            return postgresql_insert(Forecast).values(rows)
        if dialect_name == "sqlite":
            return sqlite_insert(Forecast).values(rows)

        raise RuntimeError(f"unsupported database dialect for forecast upsert: {dialect_name}")

    def list_by_store_and_date(self, *, store_id: int, forecast_date: date) -> list[Forecast]:
        statement = (
            select(Forecast)
            .options(joinedload(Forecast.store), joinedload(Forecast.product))
            .where(Forecast.store_id == store_id, Forecast.forecast_date == forecast_date)
            .order_by(Forecast.hour, Forecast.product_id)
        )
        return list(self.db.scalars(statement))
