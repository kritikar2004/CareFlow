from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    hospital_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    dataset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="uploaded",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="TRUE",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )

    file_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )

    training_period_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    training_period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    feature_schema_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    validation_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    test_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    training_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    training_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="completed",
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    dataset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )

    training_run_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("training_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    forecast_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    horizon: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    performance_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class ResourceRecord(Base):
    __tablename__ = "resource_records"

    __table_args__ = (
        CheckConstraint(
            "quantity_available >= 0",
            name="ck_resource_quantity_available_non_negative",
        ),
        CheckConstraint(
            "quantity_used >= 0",
            name="ck_resource_quantity_used_non_negative",
        ),
        CheckConstraint(
            "reference_capacity > 0",
            name="ck_resource_reference_capacity_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    resource_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quantity_available: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    quantity_used: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    reference_capacity: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )