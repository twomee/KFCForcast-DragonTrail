import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale
from app.models.store import Store

STORE_NAMES = ["Dizengoff Center", "Bnei Brak LYFE", "Rishon LeZion Mall"]
PRODUCT_NAMES = ["Original Chicken", "Hot Wings", "Fries", "Zinger Burger", "Coleslaw"]
HISTORICAL_DAYS_TO_SEED = 21
OPENING_HOUR = 10
CLOSING_HOUR = 22
WEEKEND_DAYS = {4, 5}

BASE_DEMAND = 4
STORE_DEMAND_STEP = 2
WEEKEND_DEMAND_BOOST = 8
LUNCH_HOURS = range(12, 15)
LUNCH_DEMAND_BOOST = 18
DINNER_HOURS = range(18, 22)
DINNER_DEMAND_BOOST = 22
DAILY_VARIATION_CYCLE_DAYS = 4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoDemandProfile:
    """Predictable demand pattern for demo data: lunch, dinner, and weekend peaks."""

    def quantity(
        self,
        *,
        store_index: int,
        product_index: int,
        sale_date: date,
        hour: int,
        days_ago: int,
    ) -> int:
        quantity = BASE_DEMAND
        quantity += store_index * STORE_DEMAND_STEP
        quantity += product_index
        quantity += self._weekend_boost(sale_date)
        quantity += self._lunch_boost(hour)
        quantity += self._dinner_boost(hour)
        quantity += days_ago % DAILY_VARIATION_CYCLE_DAYS
        return quantity

    def _weekend_boost(self, sale_date: date) -> int:
        return WEEKEND_DEMAND_BOOST if sale_date.weekday() in WEEKEND_DAYS else 0

    def _lunch_boost(self, hour: int) -> int:
        return LUNCH_DEMAND_BOOST if hour in LUNCH_HOURS else 0

    def _dinner_boost(self, hour: int) -> int:
        return DINNER_DEMAND_BOOST if hour in DINNER_HOURS else 0


def seed_database(db: Session) -> None:
    if db.scalar(select(Store).limit(1)) is not None:
        logger.info("database_seed_skipped reason=stores_already_exist")
        return

    logger.info("database_seed_started")
    stores = [Store(name=name) for name in STORE_NAMES]
    products = [Product(name=name) for name in PRODUCT_NAMES]
    db.add_all([*stores, *products])
    db.flush()

    sales = _build_demo_sales(
        stores=stores,
        products=products,
        demand_profile=DemoDemandProfile(),
        today=datetime.now().date(),
    )
    db.add_all(sales)
    db.commit()

    logger.info(
        "database_seed_completed stores=%s products=%s sales=%s",
        len(stores),
        len(products),
        len(sales),
    )


def _build_demo_sales(
    *,
    stores: list[Store],
    products: list[Product],
    demand_profile: DemoDemandProfile,
    today: date,
) -> list[Sale]:
    sales: list[Sale] = []

    for days_ago in range(1, HISTORICAL_DAYS_TO_SEED + 1):
        sale_date = today - timedelta(days=days_ago)
        for store_index, store in enumerate(stores):
            for product_index, product in enumerate(products):
                for hour in range(OPENING_HOUR, CLOSING_HOUR + 1):
                    sold_at = datetime.combine(sale_date, time(hour=hour))
                    quantity = demand_profile.quantity(
                        store_index=store_index,
                        product_index=product_index,
                        sale_date=sale_date,
                        hour=hour,
                        days_ago=days_ago,
                    )
                    sales.append(
                        Sale(
                            store_id=store.id,
                            product_id=product.id,
                            sold_at=sold_at,
                            quantity=quantity,
                        )
                    )

    return sales
