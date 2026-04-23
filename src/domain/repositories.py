from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Check, HourlyStats, Incident, MonitoredURL


class URLRepository(ABC):
    @abstractmethod
    def get_active_urls(self) -> list[MonitoredURL]: ...

    @abstractmethod
    def get_by_id(self, url_id: UUID) -> MonitoredURL | None: ...

    @abstractmethod
    def save(self, url: MonitoredURL) -> None: ...


class CheckRepository(ABC):
    @abstractmethod
    def save_check(self, check: Check) -> None: ...

    @abstractmethod
    def get_checks(self, url_id: UUID, limit: int = 100) -> list[Check]: ...

    @abstractmethod
    def get_last_check(self, url_id: UUID) -> Check | None: ...


class StatsRepository(ABC):
    @abstractmethod
    def save_hourly_stats(self, stats: HourlyStats) -> None: ...

    @abstractmethod
    def get_stats(self, url_id: UUID, days: int) -> list[HourlyStats]: ...


class IncidentRepository(ABC):
    @abstractmethod
    def save_incident(self, incident: Incident) -> None: ...

    @abstractmethod
    def get_open_incident(self, url_id: UUID) -> Incident | None: ...

    @abstractmethod
    def get_incidents(self, url_id: UUID) -> list[Incident]: ...
