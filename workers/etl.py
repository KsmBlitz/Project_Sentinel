import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from src.application.run_etl import RunETL
from src.infrastructure.db.session import get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_etl():
    session = get_session()
    try:
        use_case = RunETL(session)
        processed = use_case.execute()
        logger.info(f"ETL procesó {processed} registros.")
    except Exception as e:
        logger.error(f"Error en el ETL: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_etl, "interval", hours=1, id="etl")
    scheduler.start()

    logger.info("Worker ETL iniciado. Corriendo cada 1 hora.")
    run_etl()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Worker ETL detenido.")
        scheduler.shutdown()
