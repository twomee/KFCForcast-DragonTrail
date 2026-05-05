# Architecture Overview

This document explains the architecture used for the KFC Forecast assignment and the reasoning behind the main design decisions.

## Executive Summary

The solution is implemented as a modular monolith:

- React frontend for store/date selection and forecast display.
- FastAPI backend for HTTP APIs, forecast generation, scheduling, and business orchestration.
- PostgreSQL database for stores, products, historical sales, and generated forecasts.

The backend is deployed as one service, but the code is split by responsibility:

```text
HTTP layer
  -> service layer
  -> domain calculation
  -> repositories
  -> database
```

This keeps the project simple to run and review while still showing production-minded boundaries.

## Current System Design

```text
Reviewer / Store Operator
        |
        v
React Frontend
        |
        |  GET  /api/v1/stores
        |  GET  /api/v1/forecasts?store_id=1&date=2026-05-06
        |  POST /api/v1/forecasts/generate
        v
FastAPI Backend
        |
        |  read/write
        v
PostgreSQL
```

Backend modules inside the FastAPI service:

```text
FastAPI app
  |
  +-- Routers
  |     HTTP endpoints and response mapping
  |
  +-- Services
  |     application use cases
  |
  +-- ForecastCalculator
  |     average-based prediction logic
  |
  +-- Repositories
  |     database reads and writes
  |
  +-- Scheduler
  |     daily generation trigger
  |
  +-- SQLAlchemy Models
  |     database table mapping
  |
  +-- Pydantic Schemas
        API request/response contracts
```

## Backend Layering

```text
Router layer
  Parses HTTP input, calls services, returns JSON
        |
        v
Service layer
  Orchestrates use cases such as "generate forecasts"
        |
        +--------------------+
        |                    |
        v                    v
Domain layer          Repository layer
  Pure forecast math    Database access
        |                    |
        +---------+----------+
                  |
                  v
              PostgreSQL
```

Layer responsibilities:

| Layer | Responsibility | Example |
| --- | --- | --- |
| Routers | HTTP contract only | Parse query params, return JSON, map domain errors to HTTP errors |
| Services | Application use cases | Generate forecasts for a date, retrieve forecasts by store/date |
| Domain | Business calculation | Calculate hourly averages from historical sales |
| Repositories | Persistence | Query sales history, upsert forecast rows |
| Models | Database mapping | SQLAlchemy table definitions |
| Schemas | API contract | Pydantic request/response models |
| Scheduler | Time trigger | Run forecast generation once per day |

This separation keeps business logic out of controllers and database logic out of services.

## Generation Flow

Forecast generation can be triggered by the scheduler or manually through the API.

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
ForecastService.generate_for_date(target_date)
                  |
                  v
Load all stores and products
                  |
                  v
For each store/product pair:
  1. Load historical sales within the lookback window
  2. Group sales by hour
  3. Calculate average quantity per hour
  4. Build forecast rows
                  |
                  v
Upsert forecast rows into PostgreSQL
```

The generated forecast row is identified by this business key:

```text
store_id + product_id + forecast_date + hour
```

That key makes generation idempotent. Running the generator again for the same date updates existing rows instead of creating duplicates.

## Read Flow

The frontend does not calculate forecasts. It only reads persisted forecast data.

```text
React UI
  User selects store and date
        |
        v
GET /api/v1/forecasts?store_id=1&date=2026-05-06
        |
        v
Forecast router
        |
        v
ForecastService.get_forecasts(store_id, date)
        |
        v
ForecastRepository.list_by_store_and_date(store_id, date)
        |
        v
PostgreSQL forecasts table
        |
        v
JSON response returned to the UI
```

The query supports retrieval by both store and date:

```http
GET /api/v1/forecasts?store_id=1&date=2026-05-06
```

## Why Modular Monolith Instead Of Microservices

Microservices are valuable when independent services have different ownership, scaling, deployment cadence, or failure boundaries. This assignment does not yet have those constraints.

For this project, a microservice split would add operational complexity without clear product value:

- multiple deployable services
- service-to-service networking
- duplicated configuration and logging
- more failure modes
- harder local setup for reviewers
- harder tests because behavior crosses process boundaries

The modular monolith keeps the runtime simple but the boundaries explicit. That is the important part for this assignment.

## When The Design Should Change

The design can evolve to a separate worker or forecasting service if real production constraints appear.

Signals that would justify extraction:

- forecast generation becomes CPU-heavy or long-running
- the forecasting algorithm is owned by a separate data science team
- generation must scale independently from API traffic
- forecasts need to be generated from events or queues
- multiple systems need to consume forecast-created events
- API instances are scaled horizontally and scheduler duplication becomes unacceptable

## Production-Oriented Design

In production, the scheduler should usually be outside the API process. If four API instances run and each starts its own scheduler, the system can attempt generation four times. Upsert protects data correctness, but the work is duplicated.

A cleaner production design:

```text
Users
  |
  v
Static hosting / CDN
  |
  v
Load balancer
  |
  +--------------------+
  |                    |
  v                    v
FastAPI instance 1     FastAPI instance 2
  |                    |
  +---------+----------+
            |
            v
        PostgreSQL


Cloud Scheduler or Kubernetes CronJob
            |
            v
      Forecast Worker
            |
            v
        PostgreSQL


FastAPI instances and the worker all emit:
  -> logs
  -> metrics
  -> alerts
```

The code boundary remains almost the same. The worker would still call the same use case:

```python
ForecastService.generate_for_date(target_date)
```

The first production extraction is therefore a deployment change, not a rewrite.

## Database Design

```text
stores
  id
  name
  |
  +-- sales.store_id
  |
  +-- forecasts.store_id

products
  id
  name
  |
  +-- sales.product_id
  |
  +-- forecasts.product_id

sales
  id
  store_id
  product_id
  sold_at
  quantity

forecasts
  id
  store_id
  product_id
  forecast_date
  hour
  predicted_quantity
  generated_at
```

Relationship summary:

| Relationship | Meaning |
| --- | --- |
| `stores -> sales` | One store has many historical sales rows. |
| `products -> sales` | One product has many historical sales rows. |
| `stores -> forecasts` | One store has many generated forecast rows. |
| `products -> forecasts` | One product has many generated forecast rows. |

## Index Strategy

Indexes were added based on the actual query patterns.

### Forecast uniqueness

```python
UniqueConstraint("store_id", "product_id", "forecast_date", "hour")
```

Why:

- A forecast row means one prediction for one store, one product, one date, and one hour.
- Duplicate rows for the same business key would make the UI incorrect.
- The upsert uses this unique key to decide whether to insert or update.

### Forecast read index

```python
Index("ix_forecasts_store_date", "store_id", "forecast_date")
```

Why:

- The read endpoint filters by `store_id` and `forecast_date`.
- This lets PostgreSQL find the relevant forecast slice quickly.
- `product_id` is not first because the current UI does not query by product first.

### Sales history index

```python
Index("ix_sales_store_product_sold_at", "store_id", "product_id", "sold_at")
```

Why:

- The generator repeatedly loads historical sales for a specific store/product/date range.
- Equality filters come first: `store_id`, `product_id`.
- The range filter comes last: `sold_at`.

This column order matches the query shape used by the generator.

## Forecast Calculation And Query Efficiency

The current implementation keeps the average calculation in the application service:

```text
For each store
  For each product
    load historical sales for that store/product/date range
    group the rows by hour in Python
    calculate the average quantity per hour
```

This is acceptable for the home assignment because the data set is intentionally small, the algorithm is easy to read, and the business rule is covered by unit tests. It also keeps the implementation transparent for review: the `ForecastCalculator` contains the average logic, while repositories only handle persistence.

The trade-off is that this approach would not be ideal for high-volume production data. With many stores and products, the generator can become a batch N+1 pattern because it performs one history query per store/product pair.

For production scale, the first optimization would be a grouped SQL query:

```sql
SELECT
  store_id,
  product_id,
  EXTRACT(HOUR FROM sold_at) AS sale_hour,
  ROUND(AVG(quantity)) AS predicted_quantity
FROM sales
WHERE sold_at >= :start_time
  AND sold_at < :end_time
GROUP BY store_id, product_id, EXTRACT(HOUR FROM sold_at);
```

That lets PostgreSQL aggregate the history in one pass instead of moving all raw rows into Python for repeated per-product calculations.

For larger systems, the next step would be pre-aggregation:

```text
raw sales
  -> hourly_sales_summary table
  -> forecast generation reads summary rows
  -> forecasts table
```

Example summary shape:

```text
store_id
product_id
sale_date
hour
total_quantity
```

This reduces the amount of data scanned during forecast generation and makes the job more predictable as raw sales volume grows.

The current design intentionally keeps a clean boundary around `ForecastService.generate_for_date(...)`, so this optimization can be implemented later without changing the API or frontend.

## Forecast Model

The `Forecast` model maps to the `forecasts` table.

| Field | Purpose |
| --- | --- |
| `id` | Technical primary key for ORM identity and API output. |
| `store_id` | Foreign key to the store being predicted. |
| `product_id` | Foreign key to the product being predicted. |
| `forecast_date` | The business date being predicted. |
| `hour` | The hour inside that date, `0` through `23`. |
| `predicted_quantity` | The calculated expected sales quantity. |
| `generated_at` | Timestamp showing when the row was generated. |
| `store` | ORM relationship used to read the store object from a forecast. |
| `product` | ORM relationship used to read the product object from a forecast. |

The business key is not `id`. The business key is:

```text
store_id + product_id + forecast_date + hour
```

`id` exists because relational tables and ORMs work better with a simple primary key, but correctness is enforced by the unique business key.

## Upsert Strategy

The repository uses upsert for forecast persistence.

SQL concept:

```sql
INSERT INTO forecasts (...)
VALUES (...)
ON CONFLICT (store_id, product_id, forecast_date, hour)
DO UPDATE SET
  predicted_quantity = EXCLUDED.predicted_quantity,
  generated_at = EXCLUDED.generated_at;
```

Important detail: upsert starts as an insert. There is no separate standard SQL command named `UPSERT`. In PostgreSQL, the operation is written as:

```text
INSERT ... ON CONFLICT DO UPDATE
```

So the SQLAlchemy code builds an insert statement first, then adds conflict behavior:

```python
insert_statement = insert(Forecast).values(rows)
upsert_statement = insert_statement.on_conflict_do_update(...)
```

`excluded.predicted_quantity` means "the value that was attempted in the insert." If a conflict happens, that incoming value is used to update the existing row.

## Trade-Offs

Strengths:

- Easy for reviewers to run with Docker Compose.
- Clear separation of concerns inside the backend.
- Forecast generation is idempotent.
- Prediction logic is simple and explainable.
- The design can evolve into a worker/service without rewriting the core use case.

Known limitations:

- The in-process scheduler is acceptable for this assignment, but a production multi-instance deployment should use a dedicated worker or external scheduler.
- The prediction algorithm is intentionally simple. A real system may include weekday patterns, holidays, promotions, weather, and recent sales trends.
- The project uses `create_all` for assignment simplicity. Production should use Alembic migrations.
- Authentication and authorization are not included because the assignment focuses on forecasting, not user management.
