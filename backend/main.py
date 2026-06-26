"""
FastAPI application entry point.

Defines the application factory (create_app) following clean architecture:
- Configuration loading
- Middleware registration
- Router mounting
- Exception handlers
- Lifecycle events (startup/shutdown)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# ⭐ CRITICAL: Force-import all models so SQLAlchemy registers them
import backend.models  # noqa: F401
from backend.api.v1.router import api_router
from backend.core.config import settings
from backend.core.logging_config import setup_logging


# =====================================================
# Lifespan: runs at startup and shutdown
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.

    Use this for:
    - Initializing connections (DB, Redis, ML models)
    - Cleanup on shutdown
    """
    # ----- Startup -----
    setup_logging()
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})")
    logger.info(f"📚 API docs available at http://{settings.API_HOST}:{settings.API_PORT}/docs")

    yield  # Application runs here

    # ----- Shutdown -----
    logger.info(f"👋 Shutting down {settings.APP_NAME}")


# =====================================================
# Application factory
# =====================================================
def create_app() -> FastAPI:
    """
    Build and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "🛠️ **Enterprise ITSM Assistant** — AI-powered helpdesk system "
            "with ML-based ticket routing, priority prediction, and SLA breach detection."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    # -----------------------------------------------
    # Middleware: CORS
    # -----------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------
    # Routers
    # -----------------------------------------------
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # -----------------------------------------------
    # Global exception handler
    # -----------------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions — never leak stack traces to clients."""
        logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    # -----------------------------------------------
    # Root endpoint
    # -----------------------------------------------
    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


# =====================================================
# Module-level app instance (used by uvicorn)
# =====================================================
app = create_app()
