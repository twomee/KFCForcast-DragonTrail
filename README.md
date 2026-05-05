# KFC Forecast

Full-stack home assignment for hourly KFC product sales forecasting.

The system predicts how many units of each product a store is expected to sell for a selected forecast date, hour by hour. The backend seeds historical sales data, generates forecasts from that data, persists the results, and exposes them through an API consumed by the React frontend.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, APScheduler
- Frontend: React, TypeScript, Vite, TanStack Query
- Tooling: Docker Compose, pytest, Ruff, Vitest, ESLint, GitHub Actions, pre-commit

## Run With Docker

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:8080
- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

Docker Compose starts:

- `postgres`: PostgreSQL database
- `backend`: FastAPI API and scheduler
- `frontend`: built React app served by nginx

The backend creates tables and seeds demo stores, products, and historical sales on startup.

## Demo Flow

1. Open http://localhost:8080.
2. Select a store and forecast date.
3. Click `Generate`.
4. Forecast rows appear for the selected store/date.

The `Generate` button is a manual demo trigger. The automatic production-style flow is the scheduler.

## Scheduler

The scheduler runs once per day and generates forecasts for tomorrow.

Current Docker Compose settings:

```yaml
FORECAST_RUN_HOUR: 20
FORECAST_TIMEZONE: Asia/Jerusalem
```

This means the backend generates tomorrow's forecasts every day at 20:00 Israel time.

## Seed Data Vs Forecast Data

Seed data is historical input data:

```text
stores
products
historical sales
```

Forecast data is generated output data:

```text
forecasts
```

On startup, the backend seeds historical sales. Forecast rows are created by either:

- the scheduler, once per day
- the manual `Generate` button
- `POST /api/v1/forecasts/generate`

This keeps the database reproducible. Reviewers do not need to import a DB dump.

## Useful API Calls

List stores:

```bash
curl http://localhost:8000/api/v1/stores
```

Generate forecasts:

```bash
curl -X POST http://localhost:8000/api/v1/forecasts/generate \
  -H 'Content-Type: application/json' \
  -d '{"forecast_date":"2026-05-06"}'
```

Read forecasts:

```bash
curl 'http://localhost:8000/api/v1/forecasts?store_id=1&date=2026-05-06'
```

## Postman

Import this collection:

```text
postman/kfc-forecast.postman_collection.json
```

Recommended order:

1. Health
2. List Stores
3. Generate Forecasts
4. Read Forecasts By Store And Date

## Logs

The backend logs startup, seeding, scheduler setup, forecast generation, forecast reads, and unexpected errors.

View logs:

```bash
docker compose logs -f backend
```

Example events:

```text
application_startup
database_seed_completed
forecast_scheduler_started
api_generate_forecasts
forecast_generation_completed
forecast_read_completed
```

## Inspect PostgreSQL

Open `psql` inside Docker:

```bash
docker compose exec postgres psql -U kfc -d kfc_forecast
```

List tables:

```sql
\dt
```

Show forecasts:

```sql
SELECT * FROM forecasts ORDER BY forecast_date, store_id, hour, product_id;
```

More queries are available in [docs/troubleshooting.md](docs/troubleshooting.md).

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
ruff check .
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
npm test
npm run lint
npm run build
```

## Quality Checks

Both backend and frontend enforce at least 80% coverage in their test commands.

Backend:

```bash
cd backend
ruff check .
pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
```

Docker:

```bash
docker compose build
```

## CI And Pre-Commit

GitHub Actions runs on pull requests and pushes to `main`:

- backend lint and tests
- frontend lint, tests, and build
- Docker Compose build

Pre-commit is configured for local checks:

```bash
pre-commit install
pre-commit run --all-files
```

## Project Docs

- [Task explanation](docs/task-explanation.md)
- [Architecture overview](docs/architecture-decision.md)
- [Troubleshooting guide](docs/troubleshooting.md)
