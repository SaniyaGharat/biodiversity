"""Main FastAPI Application Entrypoint for Daaruka Biodiversity Intelligence."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from daaruka.core.config import settings
from daaruka.api.v1.router import api_router
from daaruka.api.v1.health import get_health, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    # Startup tasks (e.g. initialize DB connections, load warm caches)
    yield
    # Shutdown tasks (e.g. close connection pools)


def create_application() -> FastAPI:
    """FastAPI application factory."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Top-level health check endpoint
    application.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Top-level Health Check",
    )(get_health)

    # Include Versioned API Router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "daaruka.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
