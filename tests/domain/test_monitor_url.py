from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.entities import Check, Incident, MonitoredURL
from src.domain.repositories import CheckRepository, IncidentRepository
from src.application.monitor_url import MonitorURL


# --- Fakes ---

class FakeCheckRepository(CheckRepository):
    def __init__(self):
        self.checks: list[Check] = []

    def save_check(self, check: Check) -> None:
        self.checks.append(check)

    def get_checks(self, url_id: UUID, limit: int = 100) -> list[Check]:
        return [c for c in self.checks if c.url_id == url_id]

    def get_last_check(self, url_id: UUID) -> Check | None:
        checks = self.get_checks(url_id)
        return checks[-1] if checks else None


class FakeIncidentRepository(IncidentRepository):
    def __init__(self):
        self.incidents: list[Incident] = []

    def save_incident(self, incident: Incident) -> None:
        existing = next((i for i in self.incidents if i.id == incident.id), None)
        if existing:
            self.incidents.remove(existing)
        self.incidents.append(incident)

    def get_open_incident(self, url_id: UUID) -> Incident | None:
        return next(
            (i for i in self.incidents if i.url_id == url_id and i.resolved_at is None),
            None,
        )

    def get_incidents(self, url_id: UUID) -> list[Incident]:
        return [i for i in self.incidents if i.url_id == url_id]


class FakeHTTPClient:
    def __init__(self, is_up: bool = True):
        self.is_up = is_up

    def get(self, url: str, timeout: int = 10) -> dict:
        return {
            "is_up": self.is_up,
            "status_code": 200 if self.is_up else 500,
            "response_time_ms": 100,
            "error_msg": None,
        }


# --- Helpers ---

def make_url() -> MonitoredURL:
    return MonitoredURL(
        id=uuid4(),
        url="https://example.com",
        name="Example",
        interval_minutes=5,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


# --- Tests ---

class TestMonitorURL:
    def test_guarda_check_cuando_url_esta_activa(self):
        check_repo = FakeCheckRepository()
        incident_repo = FakeIncidentRepository()
        use_case = MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=True))
        url = make_url()

        use_case.execute(url)

        assert len(check_repo.checks) == 1
        assert check_repo.checks[0].is_up is True

    def test_guarda_check_cuando_url_esta_caida(self):
        check_repo = FakeCheckRepository()
        incident_repo = FakeIncidentRepository()
        use_case = MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=False))
        url = make_url()

        use_case.execute(url)

        assert len(check_repo.checks) == 1
        assert check_repo.checks[0].is_up is False

    def test_crea_incidente_cuando_url_cae(self):
        check_repo = FakeCheckRepository()
        incident_repo = FakeIncidentRepository()
        use_case = MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=False))
        url = make_url()

        use_case.execute(url)

        assert len(incident_repo.incidents) == 1
        assert incident_repo.incidents[0].resolved_at is None

    def test_no_crea_incidente_duplicado(self):
        check_repo = FakeCheckRepository()
        incident_repo = FakeIncidentRepository()
        use_case = MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=False))
        url = make_url()

        use_case.execute(url)
        use_case.execute(url)

        assert len(incident_repo.incidents) == 1
        assert incident_repo.incidents[0].checks_failed == 2

    def test_cierra_incidente_cuando_url_se_recupera(self):
        check_repo = FakeCheckRepository()
        incident_repo = FakeIncidentRepository()
        url = make_url()

        MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=False)).execute(url)
        MonitorURL(check_repo, incident_repo, FakeHTTPClient(is_up=True)).execute(url)

        assert incident_repo.incidents[0].resolved_at is not None
