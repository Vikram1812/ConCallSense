# app/models.py
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    earnings_calls: Mapped[List["EarningsCall"]] = relationship(
        "EarningsCall", back_populates="company", cascade="all, delete-orphan"
    )


class EarningsCall(Base):
    __tablename__ = "earnings_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    fiscal_year: Mapped[str] = mapped_column(String(10))     # e.g., 'FY26'
    fiscal_quarter: Mapped[str] = mapped_column(String(10))  # e.g., 'Q3'
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capex_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship("Company", back_populates="earnings_calls")
    guidance_items: Mapped[List["GuidanceCommitment"]] = relationship(
        "GuidanceCommitment", back_populates="call", cascade="all, delete-orphan"
    )


class GuidanceCommitment(Base):
    __tablename__ = "guidance_commitments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("earnings_calls.id", ondelete="CASCADE"), index=True)
    metric_type: Mapped[str] = mapped_column(String(50))   # REVENUE, EBITDA_MARGIN, etc.
    target_value: Mapped[float] = mapped_column(Numeric(15, 2))
    target_unit: Mapped[str] = mapped_column(String(20))    # PERCENT, CRORE, etc.
    target_period: Mapped[str] = mapped_column(String(30))  # Q4 FY26, FY27
    verbatim_quote: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING") # PENDING, MET, MISSED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    call: Mapped["EarningsCall"] = relationship("EarningsCall", back_populates="guidance_items")