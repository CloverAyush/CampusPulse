import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.config import settings
from app.database import Base, engine
from app.errors import DomainError, RateLimitedError
from app.logging_config import configure_logging, request_id_var
from app.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.schema_check import (
    format_missing_columns_error,
    format_missing_tables_error,
    missing_columns_by_table,
    missing_required_tables,
)

configure_logging()
logger = logging.getLogger(__name__)

# Imported for its side effect: defining every model class registers it on
# Base.metadata, which the schema-drift check in lifespan() below needs to see
# every table. Every model already gets imported transitively by app.api.v1, but
# that's an accident of which routes happen to reference which models -- this
# makes the dependency explicit instead of relying on it.
importlib.import_module("app.models")

REQUIRED_TABLES = {"users", "issues", "reports", "routing_rules", "issue_types", "locations"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Schema comes from Alembic, not from the app. Starting against an un-migrated
    database -- or, just as often, a leftover SQLite file from before a column was
    added -- fails loudly here with the exact missing table or column, instead of
    surfacing as an OperationalError from deep inside whichever request hits it
    first."""
    missing_tables = missing_required_tables(engine, REQUIRED_TABLES)
    if missing_tables:
        message = format_missing_tables_error(missing_tables)
        logger.critical(message)
        raise RuntimeError(message)

    missing_columns = missing_columns_by_table(engine, Base.metadata)
    if missing_columns:
        message = format_missing_columns_error(missing_columns)
        logger.critical(message)
        raise RuntimeError(message)

    logger.info(
        "API starting",
        extra={"environment": settings.ENVIRONMENT, "docs_enabled": settings.docs_enabled},
    )
    yield
    logger.info("API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Report, route, resolve and verify non-personal campus issues.",
    version="1.0.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
app.add_middleware(RequestContextMiddleware)


def _error_body(code: str, message: str, details=None) -> dict:
    body = {"error": {"code": code, "message": message, "request_id": request_id_var.get()}}
    if details:
        body["error"]["details"] = details
    return body


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError):
    headers = {}
    if isinstance(exc, RateLimitedError):
        headers["Retry-After"] = str(exc.retry_after)
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.error_code, exc.message),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(part) for part in error["loc"][1:]) or "body", "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", "Some of the details you entered are not valid.", details),
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body("http_error", str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Never let an internal detail reach the browser; the request id is the handle
    support uses to find the full trace in the logs."""
    logger.exception("Unhandled error", extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "internal_error",
            "Something went wrong on our side. Quote the request id if you report this.",
        ),
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["ops"])
def health_check():
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unreachable"})

    return {"status": "ready", "database": "reachable"}
