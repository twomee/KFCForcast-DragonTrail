from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


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
        self, historical_sales: list[HistoricalSalePoint]
    ) -> list[HourlyPrediction]:
        quantities_by_hour: dict[int, list[int]] = defaultdict(list)

        for sale in historical_sales:
            quantities_by_hour[sale.sold_at.hour].append(sale.quantity)

        predictions: list[HourlyPrediction] = []
        for hour in range(24):
            quantities = quantities_by_hour.get(hour, [])
            predicted_quantity = round(sum(quantities) / len(quantities)) if quantities else 0
            predictions.append(HourlyPrediction(hour=hour, predicted_quantity=predicted_quantity))

        return predictions

