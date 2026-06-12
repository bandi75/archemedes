from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from archimedes.orchestrator.controller import StageController
from archimedes.storage.cosmos_client import CosmosStorageClient
from archimedes.state.state_manager import ArchitectureStateManager

from .routers import artifacts, changes, diffs, evidence, sessions
from .storage import InMemoryArchimedesStorage

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
# Cosmos SDK dumps full HTTP headers at INFO — keep it quiet
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)


class Settings(BaseSettings):
    """Runtime settings for the Archimedes API shell."""

    service_name: str = "archimedes-api"
    api_version: str = "v1"
    cors_origins: list[str] = ["http://localhost:8501"]
    required_env_vars: tuple[str, ...] = ("FOUNDRY_PROJECT_ENDPOINT",)
    validate_required_env: bool = True
    storage_backend: str = "memory"
    cosmos_endpoint: str | None = None
    cosmos_database_name: str = "archimedes"
    cosmos_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ARCHIMEDES_API_",
        extra="ignore",
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _missing_required_env(required_env_vars: Sequence[str]) -> list[str]:
    return [name for name in required_env_vars if not os.getenv(name)]


def _error_response(status_code: int, detail: str, error_code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_code": error_code},
    )


def _build_storage(settings: Settings):
    if settings.storage_backend.strip().lower() != "cosmos":
        return InMemoryArchimedesStorage()

    if not settings.cosmos_endpoint:
        raise RuntimeError("Missing Cosmos endpoint. Set ARCHIMEDES_API_COSMOS_ENDPOINT.")

    try:
        from azure.cosmos import CosmosClient
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("azure-cosmos is required when ARCHIMEDES_API_STORAGE_BACKEND=cosmos.") from exc

    if settings.cosmos_key:
        client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
    else:
        try:
            from azure.identity import DefaultAzureCredential
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("azure-identity is required for Cosmos managed identity authentication.") from exc
        client = CosmosClient(settings.cosmos_endpoint, credential=DefaultAzureCredential())

    database = client.create_database_if_not_exists(id=settings.cosmos_database_name)
    CosmosStorageClient.ensure_containers(database)
    return CosmosStorageClient.from_database(database)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        storage = getattr(app.state, "storage", None) or _build_storage(settings)
        app.state.storage = storage
        app.state.state_manager = ArchitectureStateManager(storage=storage)
        app.state.stage_controller = StageController(
            state_manager=app.state.state_manager,
            storage=storage,
        )
        if settings.validate_required_env:
            missing = _missing_required_env(settings.required_env_vars)
            if missing:
                joined = ", ".join(missing)
                raise RuntimeError(f"Missing required environment variable(s): {joined}")
        yield

    app = FastAPI(
        title="Archimedes API",
        version=settings.api_version,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(artifacts.router, prefix="/api/v1")
    app.include_router(evidence.router, prefix="/api/v1")
    app.include_router(changes.router, prefix="/api/v1")
    app.include_router(diffs.router, prefix="/api/v1")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        error_code = "http_error"
        detail = exc.detail
        if isinstance(exc.detail, dict):
            error_code = str(exc.detail.get("error_code", error_code))
            detail = exc.detail.get("detail", detail)
        return _error_response(exc.status_code, str(detail), error_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(422, str(exc), "validation_error")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        return _error_response(500, str(exc), "internal_error")

    def health_payload() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.api_version,
            "timestamp": _utc_now(),
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return health_payload()

    @app.get("/api/v1/health")
    async def versioned_health() -> dict[str, str]:
        return health_payload()

    @app.get("/api/v1/health/ready")
    async def readiness() -> dict[str, str | list[str]]:
        missing = (
            _missing_required_env(settings.required_env_vars)
            if settings.validate_required_env
            else []
        )
        if missing:
            raise HTTPException(
                status_code=503,
                detail={
                    "detail": f"Missing required environment variable(s): {', '.join(missing)}",
                    "error_code": "service_unavailable",
                },
            )
        return {"status": "ready", "service": settings.service_name, "missing": []}

    return app


app = create_app()
