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


from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

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

    # Mount static assets if directory exists
    if STATIC_DIR.exists():
        application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Serve Single-Page Conversational UI on Root
    @application.get("/", include_in_schema=False)
    async def serve_index() -> FileResponse:
        """Serve the self-contained static frontend."""
        if INDEX_HTML.exists():
            return FileResponse(INDEX_HTML, media_type="text/html")
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

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
