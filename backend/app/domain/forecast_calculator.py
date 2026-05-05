from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class HistoricalSalePoint:
    sold_at: datetime
    quantity: int


@dataclass(frozen=True)
class HourlyPrediction:
    hour: int
    predicted_quantity: int


class ForecastCalculator:
    def calculate_hourly_average(
        self,
        historical_sales: list[HistoricalSalePoint],
        target_date: date | None = None,
    ) -> list[HourlyPrediction]:
        all_quantities_by_hour: dict[int, list[int]] = defaultdict(list)
        target_weekday_quantities_by_hour: dict[int, list[int]] = defaultdict(list)

        for sale in historical_sales:
            sale_hour = sale.sold_at.hour
            all_quantities_by_hour[sale_hour].append(sale.quantity)
            if target_date is not None and sale.sold_at.weekday() == target_date.weekday():
                target_weekday_quantities_by_hour[sale_hour].append(sale.quantity)

        predictions: list[HourlyPrediction] = []
        for hour in range(24):
            # Prefer same-weekday history, but fall back when that hour has no matching rows.
            quantities_for_hour = target_weekday_quantities_by_hour.get(
                hour
            ) or all_quantities_by_hour.get(
                hour,
                [],
            )
            predictions.append(
                HourlyPrediction(
                    hour=hour,
                    predicted_quantity=self._average_quantity(quantities_for_hour),
                )
            )

        return predictions

    def _average_quantity(self, quantities: list[int]) -> int:
        # Use business-style half-up rounding for forecast units instead of
        # Python's banker rounding.
        return int((sum(quantities) / len(quantities)) + 0.5) if quantities else 0
