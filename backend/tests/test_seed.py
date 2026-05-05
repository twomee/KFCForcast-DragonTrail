from datetime import date

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.seed import (
    CLOSING_HOUR,
    HISTORICAL_DAYS_TO_SEED,
    OPENING_HOUR,
    PRODUCT_NAMES,
    STORE_NAMES,
    DemoDemandProfile,
    seed_database,
)
from app.models.product import Product
from app.models.sale import Sale
from app.models.store import Store


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return testing_session()


def test_seed_database_creates_demo_dimensions_and_sales() -> None:
    db = create_test_session()

    seed_database(db)

    sales_per_product_per_day = CLOSING_HOUR - OPENING_HOUR + 1
    expected_sales = (
        len(STORE_NAMES)
        * len(PRODUCT_NAMES)
        * HISTORICAL_DAYS_TO_SEED
        * sales_per_product_per_day
    )
    assert db.scalar(select(func.count()).select_from(Store)) == len(STORE_NAMES)
    assert db.scalar(select(func.count()).select_from(Product)) == len(PRODUCT_NAMES)
    assert db.scalar(select(func.count()).select_from(Sale)) == expected_sales


def test_seed_database_is_idempotent() -> None:
    db = create_test_session()

    seed_database(db)
    seed_database(db)

    assert db.scalar(select(func.count()).select_from(Store)) == len(STORE_NAMES)
    assert db.scalar(select(func.count()).select_from(Product)) == len(PRODUCT_NAMES)


def test_demo_demand_profile_has_lunch_dinner_and_weekend_peaks() -> None:
    profile = DemoDemandProfile()
    friday = date(2026, 5, 1)
    sunday = date(2026, 5, 3)

    normal_hour = profile.quantity(
        store_index=0,
        product_index=0,
        sale_date=sunday,
        hour=10,
        days_ago=4,
    )
    lunch_hour = profile.quantity(
        store_index=0,
        product_index=0,
        sale_date=sunday,
        hour=12,
        days_ago=4,
    )
    dinner_hour = profile.quantity(
        store_index=0,
        product_index=0,
        sale_date=sunday,
        hour=18,
        days_ago=4,
    )
    weekend_hour = profile.quantity(
        store_index=0,
        product_index=0,
        sale_date=friday,
        hour=10,
        days_ago=4,
    )

    assert lunch_hour > normal_hour
    assert dinner_hour > lunch_hour
    assert weekend_hour > normal_hour
