
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ==========================================
# 1. PRIHODI
# ==========================================

class IncomePayment(Base):
    __tablename__ = "income_payments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    source_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    expected_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    expected_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    actual_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )

    actual_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Expected", nullable=False
    )


# ==========================================
# 2. FINANSIJSKE OBAVEZE
# ==========================================

class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    title: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    due_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    paid_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Pending", nullable=False
    )


# ==========================================
# 3. STANJE RACUNA
# ==========================================

class AccountState(Base):
    __tablename__ = "account_state"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


# ==========================================
# 4. UPOZORENJA AGENTA
# ==========================================

class AgentAlert(Base):
    __tablename__ = "agent_alerts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    shortage_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    shortage_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
