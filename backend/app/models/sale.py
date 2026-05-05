from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_store_product_sold_at", "store_id", "product_id", "sold_at"),
        CheckConstraint("quantity >= 0", name="ck_sales_quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    store = relationship("Store", back_populates="sales")
    product = relationship("Product", back_populates="sales")
