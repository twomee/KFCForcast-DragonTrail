# Task Explanation

This document explains the assignment in product and technical terms.

## Goal

The system predicts hourly product demand for each KFC store.

The core question is:

```text
For a given store and date, how many units of each product should the kitchen expect to sell each hour?
```

This helps the kitchen prepare enough product before demand arrives, especially around lunch and dinner peaks.

## Why The Date And Hour Matter

A forecast is not only "how many products will this store sell tomorrow." The assignment requires a more operational answer:

```text
store + product + date + hour -> predicted quantity
```

Example:

| Store | Product | Forecast date | Hour | Predicted quantity |
| --- | --- | --- | --- | --- |
| Dizengoff Center | Fries | 2026-05-06 | 12 | 41 |
| Dizengoff Center | Fries | 2026-05-06 | 18 | 55 |
| Dizengoff Center | Wings | 2026-05-06 | 18 | 48 |

The `date` tells us which business day we are predicting. The `hour` tells us the time window inside that day.

This matters because restaurant sales are not evenly distributed. Lunch, afternoon, and dinner behave differently. A daily total is less actionable for kitchen preparation than an hourly breakdown.

## Input Data And Output Data

The system works with two kinds of data:

```text
Historical sales
  what already happened
        |
        v
Forecast generator
  average calculation
        |
        v
Forecast rows
  predictions for a future date
        |
        v
Frontend display
```

Historical sales are the input:

| Store | Product | Sold at | Quantity |
| --- | --- | --- | --- |
| Dizengoff Center | Fries | 2026-05-01 12:00 | 40 |
| Dizengoff Center | Fries | 2026-05-02 12:00 | 44 |

Forecasts are the output:

| Store | Product | Forecast date | Hour | Predicted quantity |
| --- | --- | --- | --- | --- |
| Dizengoff Center | Fries | 2026-05-06 | 12 | 42 |

## Prediction Logic

The assignment asks for an average-based prediction. This implementation intentionally does not use machine learning.

For each store, product, and hour, the system looks at historical sales and calculates the average quantity sold during that hour.

Example:

```text
Store: Dizengoff Center
Product: Fries
Hour: 12
Historical quantities: 40, 44, 38, 42

Average:
(40 + 44 + 38 + 42) / 4 = 41
```

The generated forecast is:

```text
Dizengoff Center + Fries + forecast date + 12:00 -> 41
```

The same process runs for every:

- store
- product
- hour from `0` to `23`

If there is no historical data for an hour, the prediction is `0`. That makes the behavior explicit and easy to verify.

## Full Generation Flow

```text
Start forecast generation
        |
        v
Choose target date
  default: tomorrow
        |
        v
Load all stores
        |
        v
Load all products
        |
        v
For each store/product pair
        |
        v
Load historical sales within the lookback window
        |
        v
Group sales by hour
        |
        v
Calculate average quantity for each hour
        |
        v
Build forecast rows
        |
        v
Upsert rows into forecasts table
        |
        v
Return forecast date and row count
```

## Reading Forecasts

The frontend retrieves forecasts by store and date.

```text
User selects store and date
        |
        v
React UI
        |
        v
GET /api/v1/forecasts?store_id=1&date=2026-05-06
        |
        v
FastAPI endpoint
        |
        v
ForecastService
        |
        v
ForecastRepository
        |
        v
forecasts table
        |
        v
Forecast JSON response
```

The frontend does not calculate predictions. This is intentional. The backend owns business logic and persistence; the frontend only displays the result.

## Scheduler And Manual Generation

There are two ways to generate forecasts:

```text
Daily scheduler
        |
        +--------------------+
                             |
Manual API call              |
POST /forecasts/generate     |
        |                    |
        +---------+----------+
                  |
                  v
ForecastService.generate_for_date(...)
                  |
                  v
forecasts table
```

Automatic generation:

- Runs once per day.
- Uses `FORECAST_RUN_HOUR` from settings.
- Generates forecasts for tomorrow by default.

Manual generation:

- Uses `POST /api/v1/forecasts/generate`.
- Allows a reviewer to generate forecasts immediately.
- Useful for demos, tests, and debugging.

## Seed Data Vs Generated Data

Seed data is not the forecast. Seed data is sample historical sales.

The startup seed creates:

- stores
- products
- historical sales for previous days

The generator then uses those historical sales to create forecast rows.

```text
seed database
  -> historical sales exist
  -> generator runs
  -> forecasts table is populated
```

How to verify forecasts are really generated:

1. Start the app.
2. Call `POST /api/v1/forecasts/generate`.
3. Call `GET /api/v1/forecasts?store_id=1&date=<same date>`.
4. Optionally inspect the database table directly.

Example SQL:

```sql
SELECT store_id, product_id, forecast_date, hour, predicted_quantity, generated_at
FROM forecasts
WHERE store_id = 1
ORDER BY forecast_date DESC, hour, product_id
LIMIT 10;
```

## API Examples

### List stores

```http
GET /api/v1/stores
```

Response:

```json
[
  {
    "id": 1,
    "name": "Dizengoff Center"
  },
  {
    "id": 2,
    "name": "Bnei Brak LYFE"
  }
]
```

### Generate forecasts

```http
POST /api/v1/forecasts/generate
Content-Type: application/json
```

Request:

```json
{
  "forecast_date": "2026-05-06"
}
```

Response:

```json
{
  "forecast_date": "2026-05-06",
  "rows_generated": 360
}
```

`rows_generated` equals:

```text
number of stores * number of products * 24 hours
```

### Read forecasts

```http
GET /api/v1/forecasts?store_id=1&date=2026-05-06
```

Response:

```json
[
  {
    "id": 1,
    "store_id": 1,
    "store_name": "Dizengoff Center",
    "product_id": 1,
    "product_name": "Original Chicken",
    "forecast_date": "2026-05-06",
    "hour": 0,
    "predicted_quantity": 0
  },
  {
    "id": 13,
    "store_id": 1,
    "store_name": "Dizengoff Center",
    "product_id": 3,
    "product_name": "Fries",
    "forecast_date": "2026-05-06",
    "hour": 12,
    "predicted_quantity": 41
  }
]
```

## Interview Explanation

A concise way to explain the solution:

```text
The app stores historical hourly sales. A scheduled backend job generates tomorrow's forecast.
For every store and product, it loads recent historical sales, groups them by hour, calculates
the average quantity for each hour, and saves those predictions in the forecasts table.
The frontend selects a store/date and reads the persisted forecast rows from the API.
```

The important design point is that generation and reading are separated:

- Generation creates durable forecast rows.
- Reading returns already-generated forecast rows.
- The UI does not repeat the business calculation.
