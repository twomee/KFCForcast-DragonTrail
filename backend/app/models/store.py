from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    sales = relationship("Sale", back_populates="store", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="store", cascade="all, delete-orphan")

