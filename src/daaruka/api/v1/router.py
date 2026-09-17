from fastapi import APIRouter
from daaruka.api.v1 import health, knowledge, chat, assess

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(knowledge.router, prefix="/knowledge")
api_router.include_router(chat.router, prefix="/chat")
api_router.include_router(assess.router, prefix="/assess")

