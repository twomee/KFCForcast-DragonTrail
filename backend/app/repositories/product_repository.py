from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Product]:
        return list(self.db.scalars(select(Product).order_by(Product.name)))

