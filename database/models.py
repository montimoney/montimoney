from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    main_message_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )

    operation_type: Mapped[str] = mapped_column(
        String(20)
    )

    amount: Mapped[int] = mapped_column(
        Integer
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_credit_card: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        index=True,
    )

class CreditCard(Base):
    __tablename__ = "credit_cards"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        primary_key=True,
    )

    credit_limit: Mapped[int] = mapped_column(
        Integer,
        default=220000,
    )

    balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


class MandatoryTemplate(Base):
    __tablename__ = "mandatory_templates"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="uq_mandatory_template_user_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    amount: Mapped[int] = mapped_column(
        Integer
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )


class MandatoryExpense(Base):
    __tablename__ = "mandatory_expenses"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "template_id",
            "month",
            "year",
            name="uq_mandatory_month_payment",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )

    template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("mandatory_templates.id", ondelete="CASCADE"),
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    amount: Mapped[int] = mapped_column(
        Integer
    )

    paid_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    month: Mapped[int] = mapped_column(
        Integer
    )

    year: Mapped[int] = mapped_column(
        Integer
    )


class CategoryKeyword(Base):
    __tablename__ = "category_keywords"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )

    keyword: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100)
    )


class SavingGoal(Base):
    __tablename__ = "saving_goals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    target_amount: Mapped[int] = mapped_column(
        Integer
    )

    saved_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    