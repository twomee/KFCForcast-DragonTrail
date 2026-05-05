from datetime import date, datetime, time, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.models.forecast import Forecast
from app.models.product import Product
from app.models.sale import Sale
from app.models.store import Store
from app.services.forecast_service import ForecastService


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return testing_session()


def seed_sales(db: Session, forecast_date: date) -> tuple[Store, Product]:
    store = Store(name="Test Store")
    product = Product(name="Fries")
    db.add_all([store, product])
    db.flush()

    db.add_all(
        [
            Sale(
                store_id=store.id,
                product_id=product.id,
                sold_at=datetime.combine(forecast_date - timedelta(days=1), time(hour=12)),
                quantity=40,
            ),
            Sale(
                store_id=store.id,
                product_id=product.id,
                sold_at=datetime.combine(forecast_date - timedelta(days=2), time(hour=12)),
                quantity=44,
            ),
        ]
    )
    db.commit()
    return store, product


def test_generate_for_date_persists_forecasts() -> None:
    db = create_test_session()
    target_date = date(2026, 5, 5)
    store, _ = seed_sales(db, target_date)
    settings = Settings(database_url="sqlite:///:memory:", forecast_lookback_days=14)

    generated_date, rows_generated = ForecastService(db, settings).generate_for_date(target_date)
    forecasts = ForecastService(db, settings).get_forecasts(
        store_id=store.id,
        forecast_date=target_date,
    )

    assert generated_date == target_date
    assert rows_generated == 24
    assert forecasts[12].predicted_quantity == 42


def test_generate_for_date_is_idempotent() -> None:
    db = create_test_session()
    target_date = date(2026, 5, 5)
    store, _ = seed_sales(db, target_date)
    settings = Settings(database_url="sqlite:///:memory:", forecast_lookback_days=14)
    service = ForecastService(db, settings)

    service.generate_for_date(target_date)
    service.generate_for_date(target_date)
    forecasts = service.get_forecasts(store_id=store.id, forecast_date=target_date)

    assert len(forecasts) == 24


def test_generate_for_date_updates_existing_forecast_rows() -> None:
    db = create_test_session()
    target_date = date(2026, 5, 5)
    store, _ = seed_sales(db, target_date)
    settings = Settings(database_url="sqlite:///:memory:", forecast_lookback_days=14)
    service = ForecastService(db, settings)

    service.generate_for_date(target_date)
    first_forecasts = service.get_forecasts(store_id=store.id, forecast_date=target_date)
    original_id = first_forecasts[12].id

    for sale in store.sales:
        if sale.sold_at.hour == 12:
            sale.quantity = 100
    db.commit()

    service.generate_for_date(target_date)
    updated_forecasts = service.get_forecasts(store_id=store.id, forecast_date=target_date)

    assert len(updated_forecasts) == 24
    assert updated_forecasts[12].id == original_id
    assert updated_forecasts[12].predicted_quantity == 100


def test_generate_for_date_creates_real_database_rows() -> None:
    db = create_test_session()
    target_date = date(2026, 5, 5)
    store, _ = seed_sales(db, target_date)
    settings = Settings(database_url="sqlite:///:memory:", forecast_lookback_days=14)

    ForecastService(db, settings).generate_for_date(target_date)

    persisted_forecasts = list(
        db.scalars(
            select(Forecast).where(
                Forecast.store_id == store.id,
                Forecast.forecast_date == target_date,
            )
        )
    )
    assert len(persisted_forecasts) == 24
    assert persisted_forecasts[12].predicted_quantity == 42
