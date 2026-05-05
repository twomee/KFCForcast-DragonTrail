from collections.abc import AsyncGenerator
from datetime import date, datetime, time, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.product import Product
from app.models.sale import Sale
from app.models.store import Store
from app.services.forecast_service import ForecastService, StoreNotFoundError


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def build_app() -> tuple[FastAPI, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    async def override_get_db() -> AsyncGenerator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    def override_settings() -> Settings:
        return Settings(
            database_url="sqlite:///:memory:",
            forecast_lookback_days=14,
            seed_database=False,
        )

    with testing_session() as db:
        store = Store(name="API Store")
        product = Product(name="Wings")
        db.add_all([store, product])
        db.flush()
        target_date = date(2026, 5, 5)
        db.add(
            Sale(
                store_id=store.id,
                product_id=product.id,
                sold_at=datetime.combine(target_date - timedelta(days=1), time(hour=18)),
                quantity=30,
            )
        )
        db.commit()

    test_settings = Settings(
        database_url="sqlite:///:memory:",
        forecast_lookback_days=14,
        seed_database=False,
        enable_scheduler=False,
    )
    app = create_app(test_settings, use_lifespan=False)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_settings
    return app, testing_session


@pytest.mark.anyio
async def test_lists_stores() -> None:
    app, _ = build_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/stores")

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "API Store"}]


def test_generates_and_reads_forecasts_by_store_and_date() -> None:
    _, testing_session = build_app()

    with testing_session() as db:
        service = ForecastService(
            db,
            Settings(
                database_url="sqlite:///:memory:",
                forecast_lookback_days=14,
                seed_database=False,
                enable_scheduler=False,
            ),
        )
        service.generate_for_date(date(2026, 5, 5))
        forecasts = service.get_forecasts(store_id=1, forecast_date=date(2026, 5, 5))

    assert len(forecasts) == 24
    assert forecasts[18].predicted_quantity == 30


def test_unknown_store_raises_domain_error() -> None:
    _, testing_session = build_app()

    with testing_session() as db:
        service = ForecastService(
            db,
            Settings(
                database_url="sqlite:///:memory:",
                forecast_lookback_days=14,
                seed_database=False,
                enable_scheduler=False,
            ),
        )

        with pytest.raises(StoreNotFoundError):
            service.get_forecasts(store_id=999, forecast_date=date(2026, 5, 5))
