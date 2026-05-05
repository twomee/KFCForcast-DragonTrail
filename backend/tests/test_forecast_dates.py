from datetime import datetime, timezone

from app.core.config import Settings
from app.domain.forecast_dates import default_forecast_date


def test_default_forecast_date_uses_business_timezone() -> None:
    settings = Settings(forecast_timezone="Asia/Jerusalem")

    forecast_date = default_forecast_date(
        settings,
        datetime(2026, 5, 5, 21, 30, tzinfo=timezone.utc),
    )

    assert forecast_date.isoformat() == "2026-05-07"
