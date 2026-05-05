from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "product_id",
            "forecast_date",
            "hour",
            name="uq_forecast_store_product_date_hour",
        ),
        Index("ix_forecasts_store_date", "store_id", "forecast_date"),
        CheckConstraint("hour >= 0 AND hour <= 23", name="ck_forecasts_hour_range"),
        CheckConstraint(
            "predicted_quantity >= 0",
            name="ck_forecasts_predicted_quantity_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    store = relationship("Store", back_populates="forecasts")
    product = relationship("Product", back_populates="forecasts")
