from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities import Check, Incident, MonitoredURL
from src.domain.repositories import CheckRepository, IncidentRepository, URLRepository
from src.infrastructure.db.models import IncidentModel, MonitoredURLModel, RawCheckModel


class PostgreSQLURLRepository(URLRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_active_urls(self) -> list[MonitoredURL]:
        rows = self.session.query(MonitoredURLModel).filter_by(is_active=True).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, url_id: UUID) -> MonitoredURL | None:
        row = self.session.query(MonitoredURLModel).filter_by(id=url_id).first()
        return self._to_domain(row) if row else None

    def save(self, url: MonitoredURL) -> None:
        row = MonitoredURLModel(
            id=url.id,
            url=url.url,
            name=url.name,
            interval_minutes=url.interval_minutes,
            is_active=url.is_active,
            created_at=url.created_at,
        )
        self.session.merge(row)
        self.session.commit()

    def _to_domain(self, row: MonitoredURLModel) -> MonitoredURL:
        return MonitoredURL(
            id=row.id,
            url=row.url,
            name=row.name,
            interval_minutes=row.interval_minutes,
            is_active=row.is_active,
            created_at=row.created_at,
        )


class PostgreSQLCheckRepository(CheckRepository):
    def __init__(self, session: Session):
        self.session = session

    def save_check(self, check: Check) -> None:
        row = RawCheckModel(
            id=check.id,
            url_id=check.url_id,
            checked_at=check.checked_at,
            is_up=check.is_up,
            status_code=check.status_code,
            response_time_ms=check.response_time_ms,
            error_msg=check.error_msg,
        )
        self.session.add(row)
        self.session.commit()

    def get_checks(self, url_id: UUID, limit: int = 100) -> list[Check]:
        rows = (
            self.session.query(RawCheckModel)
            .filter_by(url_id=url_id)
            .order_by(RawCheckModel.checked_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def get_last_check(self, url_id: UUID) -> Check | None:
        row = (
            self.session.query(RawCheckModel)
            .filter_by(url_id=url_id)
            .order_by(RawCheckModel.checked_at.desc())
            .first()
        )
        return self._to_domain(row) if row else None

    def _to_domain(self, row: RawCheckModel) -> Check:
        return Check(
            id=row.id,
            url_id=row.url_id,
            checked_at=row.checked_at,
            is_up=row.is_up,
            status_code=row.status_code,
            response_time_ms=row.response_time_ms,
            error_msg=row.error_msg,
        )


class PostgreSQLIncidentRepository(IncidentRepository):
    def __init__(self, session: Session):
        self.session = session

    def save_incident(self, incident: Incident) -> None:
        row = IncidentModel(
            id=incident.id,
            url_id=incident.url_id,
            started_at=incident.started_at,
            resolved_at=incident.resolved_at,
            duration_min=incident.duration_min,
            checks_failed=incident.checks_failed,
        )
        self.session.merge(row)
        self.session.commit()

    def get_open_incident(self, url_id: UUID) -> Incident | None:
        row = (
            self.session.query(IncidentModel)
            .filter_by(url_id=url_id, resolved_at=None)
            .first()
        )
        return self._to_domain(row) if row else None

    def get_incidents(self, url_id: UUID) -> list[Incident]:
        rows = (
            self.session.query(IncidentModel)
            .filter_by(url_id=url_id)
            .order_by(IncidentModel.started_at.desc())
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def _to_domain(self, row: IncidentModel) -> Incident:
        return Incident(
            id=row.id,
            url_id=row.url_id,
            started_at=row.started_at,
            resolved_at=row.resolved_at,
            duration_min=row.duration_min,
            checks_failed=row.checks_failed,
        )
