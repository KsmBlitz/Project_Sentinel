from datetime import datetime, timezone
from uuid import uuid4

from src.domain.entities import Check, Incident, MonitoredURL
from src.domain.repositories import CheckRepository, IncidentRepository


class MonitorURL:
    def __init__(self, check_repo: CheckRepository, incident_repo: IncidentRepository, http_client):
        self.check_repo = check_repo
        self.incident_repo = incident_repo
        self.http = http_client

    def execute(self, url: MonitoredURL) -> Check:
        result = self.http.get(url.url)

        check = Check(
            id=uuid4(),
            url_id=url.id,
            checked_at=datetime.now(timezone.utc),
            is_up=result["is_up"],
            status_code=result["status_code"],
            response_time_ms=result["response_time_ms"],
            error_msg=result["error_msg"],
        )
        self.check_repo.save_check(check)

        self._handle_incident(url, check)

        return check

    def _handle_incident(self, url: MonitoredURL, check: Check) -> None:
        open_incident = self.incident_repo.get_open_incident(url.id)

        if not check.is_up and open_incident is None:
            incident = Incident(
                id=uuid4(),
                url_id=url.id,
                started_at=check.checked_at,
                resolved_at=None,
                duration_min=None,
                checks_failed=1,
            )
            self.incident_repo.save_incident(incident)

        elif not check.is_up and open_incident is not None:
            open_incident.checks_failed += 1
            self.incident_repo.save_incident(open_incident)

        elif check.is_up and open_incident is not None:
            elapsed = (check.checked_at - open_incident.started_at).seconds // 60
            open_incident.resolved_at = check.checked_at
            open_incident.duration_min = elapsed
            self.incident_repo.save_incident(open_incident)
