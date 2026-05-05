from datetime import date, datetime

from app.domain.forecast_calculator import ForecastCalculator, HistoricalSalePoint


def test_calculates_hourly_average() -> None:
    calculator = ForecastCalculator()

    predictions = calculator.calculate_hourly_average(
        [
            HistoricalSalePoint(sold_at=datetime(2026, 5, 1, 12), quantity=40),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 2, 12), quantity=44),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 3, 13), quantity=20),
        ]
    )

    assert predictions[12].predicted_quantity == 42
    assert predictions[13].predicted_quantity == 20


def test_half_unit_average_rounds_up() -> None:
    calculator = ForecastCalculator()

    predictions = calculator.calculate_hourly_average(
        [
            HistoricalSalePoint(sold_at=datetime(2026, 5, 1, 12), quantity=10),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 2, 12), quantity=11),
        ]
    )

    assert predictions[12].predicted_quantity == 11


def test_no_history_returns_zero_for_each_hour() -> None:
    predictions = ForecastCalculator().calculate_hourly_average([])

    assert len(predictions) == 24
    assert all(prediction.predicted_quantity == 0 for prediction in predictions)


def test_target_date_prefers_same_weekday_history() -> None:
    calculator = ForecastCalculator()

    predictions = calculator.calculate_hourly_average(
        [
            HistoricalSalePoint(sold_at=datetime(2026, 5, 1, 12), quantity=60),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 2, 12), quantity=10),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 8, 12), quantity=64),
        ],
        target_date=date(2026, 5, 15),
    )

    assert predictions[12].predicted_quantity == 62


def test_target_date_falls_back_when_same_weekday_history_is_missing() -> None:
    calculator = ForecastCalculator()

    predictions = calculator.calculate_hourly_average(
        [
            HistoricalSalePoint(sold_at=datetime(2026, 5, 1, 12), quantity=60),
            HistoricalSalePoint(sold_at=datetime(2026, 5, 2, 12), quantity=10),
        ],
        target_date=date(2026, 5, 3),
    )

    assert predictions[12].predicted_quantity == 35
