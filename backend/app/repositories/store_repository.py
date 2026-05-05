from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.store import Store


class StoreRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Store]:
        return list(self.db.scalars(select(Store).order_by(Store.name)))

    def get(self, store_id: int) -> Store | None:
        return cast(Store | None, self.db.get(Store, store_id))
