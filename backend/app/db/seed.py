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

# Real stores usually sell more on weekends, especially in malls and high-traffic areas.
WEEKEND_DEMAND_BOOST = 8
LUNCH_HOURS = range(12, 15)
LUNCH_DEMAND_BOOST = 18
DINNER_HOURS = range(18, 22)
DINNER_DEMAND_BOOST = 22

# Small repeatable day-to-day changes keep the demo data realistic without random test failures.
DAILY_VARIATION_CYCLE_DAYS = 4
DATE_VARIATION_SPREAD = 5

# The factors below create deterministic pseudo-random variation by date/store/product/hour.
DEMAND_VARIATION_RANGE = 7
DEMAND_VARIATION_CENTER = 3
DATE_VARIATION_FACTOR = 17
STORE_VARIATION_FACTOR = 31
PRODUCT_VARIATION_FACTOR = 13
HOUR_VARIATION_FACTOR = 7

# Products have different lunch/dinner behavior; fries and burgers should not move identically.
PRODUCT_DAYPART_DEMAND_BOOSTS = {
    0: {"lunch": 5, "dinner": 8},
    1: {"lunch": 3, "dinner": 10},
    2: {"lunch": 7, "dinner": 4},
    3: {"lunch": 6, "dinner": 9},
    4: {"lunch": 2, "dinner": 1},
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoDemandProfile:
    """Repeatable demo demand with realistic variation by date, store, product, and hour."""

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
        quantity += self._product_daypart_boost(product_index, hour)
        quantity += days_ago % DAILY_VARIATION_CYCLE_DAYS
        quantity += sale_date.toordinal() % DATE_VARIATION_SPREAD
        quantity += self._deterministic_variation(
            store_index=store_index,
            product_index=product_index,
            sale_date=sale_date,
            hour=hour,
        )
        return max(quantity, 0)

    def _weekend_boost(self, sale_date: date) -> int:
        return WEEKEND_DEMAND_BOOST if sale_date.weekday() in WEEKEND_DAYS else 0

    def _lunch_boost(self, hour: int) -> int:
        return LUNCH_DEMAND_BOOST if hour in LUNCH_HOURS else 0

    def _dinner_boost(self, hour: int) -> int:
        return DINNER_DEMAND_BOOST if hour in DINNER_HOURS else 0

    def _product_daypart_boost(self, product_index: int, hour: int) -> int:
        boosts = PRODUCT_DAYPART_DEMAND_BOOSTS.get(product_index, {})
        if hour in LUNCH_HOURS:
            return boosts.get("lunch", 0)
        if hour in DINNER_HOURS:
            return boosts.get("dinner", 0)
        return 0

    def _deterministic_variation(
        self,
        *,
        store_index: int,
        product_index: int,
        sale_date: date,
        hour: int,
    ) -> int:
        date_component = sale_date.toordinal() * DATE_VARIATION_FACTOR
        store_component = store_index * STORE_VARIATION_FACTOR
        product_component = product_index * PRODUCT_VARIATION_FACTOR
        hour_component = hour * HOUR_VARIATION_FACTOR

        stable_seed = (
            date_component
            + store_component
            + product_component
            + hour_component
        )
        variation_from_zero_to_six = stable_seed % DEMAND_VARIATION_RANGE

        return variation_from_zero_to_six - DEMAND_VARIATION_CENTER


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
