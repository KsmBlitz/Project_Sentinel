from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.domain.entities import Check, MonitoredURL


def make_url(interval_minutes: int = 5) -> MonitoredURL:
    return MonitoredURL(
        id=uuid4(),
        url="https://example.com",
        name="Example",
        interval_minutes=interval_minutes,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


class TestShouldCheckNow:
    def test_deberia_chequear_si_paso_el_intervalo(self):
        url = make_url(interval_minutes=5)
        last_checked = datetime.now(timezone.utc) - timedelta(minutes=6)

        assert url.should_check_now(last_checked) is True

    def test_no_deberia_chequear_si_no_paso_el_intervalo(self):
        url = make_url(interval_minutes=5)
        last_checked = datetime.now(timezone.utc) - timedelta(minutes=3)

        assert url.should_check_now(last_checked) is False

    def test_deberia_chequear_si_paso_exactamente_el_intervalo(self):
        url = make_url(interval_minutes=5)
        last_checked = datetime.now(timezone.utc) - timedelta(minutes=5)

        assert url.should_check_now(last_checked) is True
