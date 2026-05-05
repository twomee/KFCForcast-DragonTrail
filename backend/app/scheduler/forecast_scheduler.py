import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import Settings
from app.db.session import SessionLocal
from app.domain.forecast_dates import default_forecast_date
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


def create_forecast_scheduler(settings: Settings) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.forecast_timezone))

    def generate_tomorrow_forecast() -> None:
        forecast_date = default_forecast_date(settings)
        logger.info("scheduled_forecast_generation_started forecast_date=%s", forecast_date)
        try:
            with SessionLocal() as db:
                generated_date, rows_generated = ForecastService(db, settings).generate_for_date(
                    forecast_date
                )
            logger.info(
                "scheduled_forecast_generation_completed forecast_date=%s rows_generated=%s",
                generated_date,
                rows_generated,
            )
        except Exception:
            logger.exception("scheduled_forecast_generation_failed forecast_date=%s", forecast_date)
            raise

    scheduler.add_job(
        generate_tomorrow_forecast,
        trigger="cron",
        hour=settings.forecast_run_hour,
        minute=0,
        id="daily_forecast_generation",
        replace_existing=True,
    )
    logger.info(
        "forecast_scheduler_configured timezone=%s run_hour=%s job_id=%s",
        settings.forecast_timezone,
        settings.forecast_run_hour,
        "daily_forecast_generation",
    )
    return scheduler
