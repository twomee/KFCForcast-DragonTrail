from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import Settings


def default_forecast_date(settings: Settings, now: datetime | None = None) -> date:
    current_time = now or datetime.now(ZoneInfo(settings.forecast_timezone))
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=ZoneInfo(settings.forecast_timezone))
    return current_time.astimezone(ZoneInfo(settings.forecast_timezone)).date() + timedelta(days=1)
