from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database import Base


class Affiliate(Base):
    __tablename__ = "affiliates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    offers: Mapped[list["Offer"]] = relationship("Offer", back_populates="affiliate")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="affiliate")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    affiliate_id: Mapped[int] = mapped_column(ForeignKey("affiliates.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    affiliate: Mapped["Affiliate"] = relationship("Affiliate", back_populates="offers")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="offer")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    affiliate_id: Mapped[int] = mapped_column(ForeignKey("affiliates.id"), nullable=False, index=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    affiliate: Mapped["Affiliate"] = relationship("Affiliate", back_populates="leads")
    offer: Mapped["Offer"] = relationship("Offer", back_populates="leads")
