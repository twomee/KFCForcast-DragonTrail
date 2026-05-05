# Troubleshooting Guide

This guide helps verify the app, inspect logs, and investigate PostgreSQL data when running with Docker Compose.

## Quick Health Check

Start the full app:

```bash
docker compose up --build
```

Expected URLs:

```text
Frontend: http://localhost:8080
Backend:  http://localhost:8000
Health:   http://localhost:8000/health
```

Check the backend:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Check Container Status

```bash
docker compose ps
```

Healthy state should look conceptually like:

```text
postgres   running / healthy
backend    running
frontend   running
```

If Postgres is not healthy, inspect its logs first.

## Check Logs

All containers:

```bash
docker compose logs -f
```

Backend only:

```bash
docker compose logs -f backend
```

Postgres only:

```bash
docker compose logs -f postgres
```

Frontend only:

```bash
docker compose logs -f frontend
```

The backend logs important lifecycle and business events, for example:

```text
application_startup
creating_database_tables
database_seed_started
database_seed_completed
forecast_scheduler_started
api_generate_forecasts
forecast_generation_started
forecast_generation_completed
api_list_forecasts
forecast_read_completed
```

For more verbose logs, set:

```bash
LOG_LEVEL=DEBUG
```

In Docker Compose, the backend currently sets:

```yaml
LOG_LEVEL: INFO
```

## Verify The API Flow

List stores:

```bash
curl http://localhost:8000/api/v1/stores
```

Generate forecasts for a date:

```bash
curl -X POST http://localhost:8000/api/v1/forecasts/generate \
  -H 'Content-Type: application/json' \
  -d '{"forecast_date":"2026-05-06"}'
```

Read forecasts:

```bash
curl 'http://localhost:8000/api/v1/forecasts?store_id=1&date=2026-05-06'
```

Expected behavior:

- `POST /forecasts/generate` returns `forecast_date` and `rows_generated`.
- `GET /forecasts` returns forecast rows for the selected store/date.

## Use The Postman Collection

Import this file into Postman:

```text
postman/kfc-forecast.postman_collection.json
```

Collection variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `baseUrl` | `http://localhost:8000` | Backend API base URL |
| `storeId` | `1` | Store used by forecast read calls |
| `forecastDate` | `2026-05-06` | Date used by generation/read calls |

Recommended order:

1. Health
2. List Stores
3. Generate Forecasts
4. Read Forecasts By Store And Date

## Investigate PostgreSQL Inside Docker

Open a `psql` shell inside the Postgres container:

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast
```

List all tables:

```sql
\dt
```

Describe a table:

```sql
\d stores
\d products
\d sales
\d forecasts
```

Show all stores:

```sql
SELECT * FROM stores ORDER BY id;
```

Show all products:

```sql
SELECT * FROM products ORDER BY id;
```

Show all sales:

```sql
SELECT * FROM sales ORDER BY sold_at, store_id, product_id;
```

Show all forecasts:

```sql
SELECT * FROM forecasts ORDER BY forecast_date, store_id, hour, product_id;
```

Show row counts for every main table:

```sql
SELECT 'stores' AS table_name, COUNT(*) FROM stores
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sales', COUNT(*) FROM sales
UNION ALL
SELECT 'forecasts', COUNT(*) FROM forecasts;
```

Show forecasts with store and product names:

```sql
SELECT
  f.id,
  s.name AS store_name,
  p.name AS product_name,
  f.forecast_date,
  f.hour,
  f.predicted_quantity,
  f.generated_at
FROM forecasts f
JOIN stores s ON s.id = f.store_id
JOIN products p ON p.id = f.product_id
ORDER BY f.forecast_date, s.name, f.hour, p.name;
```

Show forecasts for one store/date:

```sql
SELECT
  f.hour,
  p.name AS product_name,
  f.predicted_quantity,
  f.generated_at
FROM forecasts f
JOIN products p ON p.id = f.product_id
WHERE f.store_id = 1
  AND f.forecast_date = DATE '2026-05-06'
ORDER BY f.hour, p.name;
```

Show historical sales used as input:

```sql
SELECT
  s.name AS store_name,
  p.name AS product_name,
  sa.sold_at,
  sa.quantity
FROM sales sa
JOIN stores s ON s.id = sa.store_id
JOIN products p ON p.id = sa.product_id
WHERE sa.store_id = 1
ORDER BY sa.sold_at, p.name;
```

Exit `psql`:

```sql
\q
```

## Run One SQL Command Without Opening psql

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast -c "SELECT COUNT(*) FROM forecasts;"
```

List tables:

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast -c "\dt"
```

Show forecast rows:

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast -c "SELECT * FROM forecasts ORDER BY forecast_date, store_id, hour, product_id LIMIT 20;"
```

## Common Problems

### Backend cannot connect to Postgres

Check:

```bash
docker compose ps
docker compose logs postgres
docker compose logs backend
```

Things to verify:

- Postgres container is healthy.
- `DATABASE_URL` points to `postgres:5432`, not `localhost:5432`, inside Docker.
- The username/password/database match Docker Compose.

Expected Docker Compose database URL:

```text
postgresql+psycopg://kfc:kfc_dev_password@postgres:5432/kfc_forecast
```

### Postgres fails after changing image versions

A local Docker volume can contain data created by a different Postgres major version. For local development only, reset the database volume:

```bash
docker compose down -v
docker compose up --build
```

This deletes the local database volume and recreates seed data.

### Forecast response is empty

Possible reasons:

- Forecasts were not generated for that date yet.
- You are querying a different date than the one you generated.
- You are querying a store ID that does not exist.

Fix:

```bash
curl -X POST http://localhost:8000/api/v1/forecasts/generate \
  -H 'Content-Type: application/json' \
  -d '{"forecast_date":"2026-05-06"}'

curl 'http://localhost:8000/api/v1/forecasts?store_id=1&date=2026-05-06'
```

Then inspect the table:

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast -c "SELECT COUNT(*) FROM forecasts WHERE forecast_date = DATE '2026-05-06';"
```

### Frontend cannot reach backend

Check:

```bash
curl http://localhost:8000/health
docker compose logs frontend
docker compose logs backend
```

The browser should use:

```text
http://localhost:8080
```

The frontend container serves the built React app through nginx. The backend API is exposed on:

```text
http://localhost:8000
```

### Need to reset everything locally

For local development only:

```bash
docker compose down -v
docker compose up --build
```

This removes containers and the Postgres volume, then rebuilds the app from scratch.
