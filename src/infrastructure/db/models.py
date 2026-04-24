import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MonitoredURLModel(Base):
    __tablename__ = "monitored_urls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class RawCheckModel(Base):
    __tablename__ = "raw_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monitored_urls.id"), nullable=False)
    checked_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    is_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_msg: Mapped[str] = mapped_column(Text, nullable=True)


class HourlyStatsModel(Base):
    __tablename__ = "hourly_stats"

    url_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monitored_urls.id"), primary_key=True)
    hour: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    total_checks: Mapped[int] = mapped_column(Integer, nullable=False)
    successful: Mapped[int] = mapped_column(Integer, nullable=False)
    uptime_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    avg_response_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    p95_response_ms: Mapped[int] = mapped_column(Integer, nullable=True)


class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monitored_urls.id"), nullable=False)
    started_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    resolved_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=True)
    checks_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
