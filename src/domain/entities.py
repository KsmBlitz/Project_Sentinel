from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class MonitoredURL:
    id: UUID
    url: str
    name: str
    interval_minutes: int
    is_active: bool
    created_at: datetime

    def should_check_now(self, last_checked: datetime) -> bool:
        elapsed_minutes = (datetime.now(timezone.utc) - last_checked).seconds / 60
        return elapsed_minutes >= self.interval_minutes


@dataclass
class Check:
    id: UUID
    url_id: UUID
    checked_at: datetime
    is_up: bool
    status_code: int | None
    response_time_ms: int | None
    error_msg: str | None


@dataclass
class HourlyStats:
    url_id: UUID
    hour: datetime
    total_checks: int
    successful: int
    uptime_pct: float
    avg_response_ms: int | None
    p95_response_ms: int | None


@dataclass
class Incident:
    id: UUID
    url_id: UUID
    started_at: datetime
    resolved_at: datetime | None
    duration_min: int | None
    checks_failed: int
