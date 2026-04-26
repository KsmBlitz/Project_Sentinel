import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.db.models import HourlyStatsModel

logger = logging.getLogger(__name__)


ETL_QUERY = text("""
    SELECT
        url_id,
        date_trunc('hour', checked_at) AS hour,
        COUNT(*)                                                        AS total_checks,
        COUNT(*) FILTER (WHERE is_up)                                   AS successful,
        ROUND(100.0 * COUNT(*) FILTER (WHERE is_up) / COUNT(*), 2)     AS uptime_pct,
        AVG(response_time_ms) FILTER (WHERE is_up)                     AS avg_response_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (
            ORDER BY response_time_ms
        ) FILTER (WHERE is_up AND response_time_ms IS NOT NULL)         AS p95_response_ms
    FROM raw_checks
    WHERE checked_at >= now() - interval '2 hours'
    GROUP BY url_id, date_trunc('hour', checked_at)
""")


class RunETL:
    def __init__(self, session: Session):
        self.session = session

    def execute(self) -> int:
        logger.info("Iniciando ETL...")
        rows = self.session.execute(ETL_QUERY).fetchall()

        if not rows:
            logger.info("Sin datos nuevos para procesar.")
            return 0

        for row in rows:
            stats = HourlyStatsModel(
                url_id=row.url_id,
                hour=row.hour,
                total_checks=row.total_checks,
                successful=row.successful,
                uptime_pct=float(row.uptime_pct),
                avg_response_ms=int(row.avg_response_ms) if row.avg_response_ms else None,
                p95_response_ms=int(row.p95_response_ms) if row.p95_response_ms else None,
            )
            self.session.merge(stats)

        self.session.commit()
        logger.info(f"ETL finalizado: {len(rows)} registros procesados.")
        return len(rows)
