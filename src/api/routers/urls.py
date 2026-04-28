from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas import (
    CheckResponse,
    HourlyStatsResponse,
    IncidentResponse,
    URLCreate,
    URLResponse,
    URLStatusResponse,
)
from src.domain.entities import MonitoredURL
from src.infrastructure.db.models import HourlyStatsModel, IncidentModel, MonitoredURLModel, RawCheckModel
from src.infrastructure.db.session import get_session
from src.infrastructure.db.repos import (
    PostgreSQLCheckRepository,
    PostgreSQLIncidentRepository,
    PostgreSQLURLRepository,
)
from src.infrastructure.http_client import HTTPClient
from src.application.monitor_url import MonitorURL

router = APIRouter(prefix="/urls", tags=["URLs"])


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("", response_model=list[URLResponse])
def list_urls(db: Session = Depends(get_db)):
    return db.query(MonitoredURLModel).filter_by(is_active=True).all()


@router.post("", response_model=URLResponse, status_code=201)
def create_url(payload: URLCreate, db: Session = Depends(get_db)):
    existing = db.query(MonitoredURLModel).filter_by(url=str(payload.url)).first()
    if existing:
        raise HTTPException(status_code=409, detail="La URL ya está registrada")

    url = MonitoredURLModel(
        id=uuid4(),
        url=str(payload.url),
        name=payload.name,
        interval_minutes=payload.interval_minutes,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


@router.get("/{url_id}/status", response_model=URLStatusResponse)
def get_status(url_id: UUID, db: Session = Depends(get_db)):
    url = db.query(MonitoredURLModel).filter_by(id=url_id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    last_check = (
        db.query(RawCheckModel)
        .filter_by(url_id=url_id)
        .order_by(RawCheckModel.checked_at.desc())
        .first()
    )

    if not last_check:
        return URLStatusResponse(
            url_id=url_id, is_up=None, last_checked_at=None, last_response_time_ms=None
        )

    return URLStatusResponse(
        url_id=url_id,
        is_up=last_check.is_up,
        last_checked_at=last_check.checked_at,
        last_response_time_ms=last_check.response_time_ms,
    )


@router.get("/{url_id}/stats", response_model=list[HourlyStatsResponse])
def get_stats(url_id: UUID, days: int = 7, db: Session = Depends(get_db)):
    url = db.query(MonitoredURLModel).filter_by(id=url_id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    from sqlalchemy import text
    rows = (
        db.query(HourlyStatsModel)
        .filter(
            HourlyStatsModel.url_id == url_id,
        )
        .order_by(HourlyStatsModel.hour.desc())
        .limit(days * 24)
        .all()
    )
    return rows


@router.get("/{url_id}/incidents", response_model=list[IncidentResponse])
def get_incidents(url_id: UUID, db: Session = Depends(get_db)):
    url = db.query(MonitoredURLModel).filter_by(id=url_id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    return (
        db.query(IncidentModel)
        .filter_by(url_id=url_id)
        .order_by(IncidentModel.started_at.desc())
        .all()
    )


@router.post("/{url_id}/check", response_model=URLStatusResponse)
def check_now(url_id: UUID, db: Session = Depends(get_db)):
    url_model = db.query(MonitoredURLModel).filter_by(id=url_id).first()
    if not url_model:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    url = MonitoredURL(
        id=url_model.id,
        url=url_model.url,
        name=url_model.name,
        interval_minutes=url_model.interval_minutes,
        is_active=url_model.is_active,
        created_at=url_model.created_at,
    )

    use_case = MonitorURL(
        check_repo=PostgreSQLCheckRepository(db),
        incident_repo=PostgreSQLIncidentRepository(db),
        http_client=HTTPClient(),
    )
    check = use_case.execute(url)

    return URLStatusResponse(
        url_id=url_id,
        is_up=check.is_up,
        last_checked_at=check.checked_at,
        last_response_time_ms=check.response_time_ms,
    )
