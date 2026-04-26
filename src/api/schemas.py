from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    url: HttpUrl
    name: str
    interval_minutes: int = 5


class URLResponse(BaseModel):
    id: UUID
    url: str
    name: str
    interval_minutes: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckResponse(BaseModel):
    id: UUID
    url_id: UUID
    checked_at: datetime
    is_up: bool
    status_code: int | None
    response_time_ms: int | None
    error_msg: str | None

    model_config = {"from_attributes": True}


class URLStatusResponse(BaseModel):
    url_id: UUID
    is_up: bool | None
    last_checked_at: datetime | None
    last_response_time_ms: int | None


class HourlyStatsResponse(BaseModel):
    hour: datetime
    total_checks: int
    successful: int
    uptime_pct: float
    avg_response_ms: int | None
    p95_response_ms: int | None

    model_config = {"from_attributes": True}


class IncidentResponse(BaseModel):
    id: UUID
    url_id: UUID
    started_at: datetime
    resolved_at: datetime | None
    duration_min: int | None
    checks_failed: int

    model_config = {"from_attributes": True}
