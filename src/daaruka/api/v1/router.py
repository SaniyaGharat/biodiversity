"""Central API v1 router consolidating all sub-routers."""

from fastapi import APIRouter
from daaruka.api.v1 import health, knowledge

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(knowledge.router, prefix="/knowledge")

# Sub-routers for upcoming phases:
# api_router.include_router(reasoning.router, prefix="/reasoning", tags=["Reasoning"])  # Phase 2
# api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])                # Phase 3
# api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence"]) # Phase 4
