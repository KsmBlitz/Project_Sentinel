import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from src.application.monitor_url import MonitorURL
from src.infrastructure.db.repos import PostgreSQLCheckRepository, PostgreSQLIncidentRepository, PostgreSQLURLRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.http_client import HTTPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_checks():
    logger.info("Iniciando ronda de chequeos...")
    session = get_session()

    try:
        url_repo = PostgreSQLURLRepository(session)
        check_repo = PostgreSQLCheckRepository(session)
        incident_repo = PostgreSQLIncidentRepository(session)
        http_client = HTTPClient()

        use_case = MonitorURL(
            check_repo=check_repo,
            incident_repo=incident_repo,
            http_client=http_client,
        )

        urls = url_repo.get_active_urls()
        logger.info(f"Chequeando {len(urls)} URLs...")

        for url in urls:
            try:
                check = use_case.execute(url)
                status = "OK" if check.is_up else "CAÍDA"
                logger.info(f"{url.url} → {status} ({check.response_time_ms}ms)")
            except Exception as e:
                logger.error(f"Error al chequear {url.url}: {e}")

    finally:
        session.close()

    logger.info("Ronda de chequeos finalizada.")


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_checks, "interval", minutes=5, id="checker")
    scheduler.start()

    logger.info("Worker iniciado. Chequeando cada 5 minutos.")
    run_checks()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Worker detenido.")
        scheduler.shutdown()
