import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import forecasts, stores
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine
from app.scheduler.forecast_scheduler import create_forecast_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    logger.info("application_startup app_name=%s", settings.app_name)
    logger.info("creating_database_tables")
    Base.metadata.create_all(bind=engine)
    if settings.seed_database:
        with SessionLocal() as db:
            logger.info("database_seed_requested")
            seed_database(db)

    scheduler = None
    if settings.enable_scheduler:
        scheduler = create_forecast_scheduler(settings)
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info(
            "forecast_scheduler_started timezone=%s run_hour=%s",
            settings.forecast_timezone,
            settings.forecast_run_hour,
        )
    else:
        logger.info("forecast_scheduler_disabled")
    try:
        yield
    finally:
        if scheduler is not None:
            logger.info("forecast_scheduler_stopping")
            scheduler.shutdown(wait=False)
        logger.info("application_shutdown")


def create_app(settings_override: Settings | None = None, use_lifespan: bool = True) -> FastAPI:
    settings = settings_override or get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, lifespan=lifespan if use_lifespan else None)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        logger.error(
            "unexpected_error path=%s method=%s request_id=%s",
            request.url.path,
            request.method,
            request_id,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Unexpected server error",
                    "details": [],
                    "request_id": request_id,
                }
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(stores.router, prefix=settings.api_v1_prefix)
    app.include_router(forecasts.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
