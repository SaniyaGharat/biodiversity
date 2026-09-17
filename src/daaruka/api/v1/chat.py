"""Chat API v1 endpoints for conversational biodiversity intelligence."""

from fastapi import APIRouter, HTTPException, status
from daaruka.chat.models import ChatRequest, ChatResponse, ChatSession
from daaruka.chat.turn_handler import handle_chat_turn
from daaruka.chat.session_store import session_store

router = APIRouter(tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-turn conversational reasoning and clarification endpoint",
    description="Processes user message, updates multi-turn session state, asks prioritized clarifying questions, or returns grounded recommendations.",
)
async def chat_interaction(request: ChatRequest) -> ChatResponse:
    """Handle conversational turn with memory persistence."""
    try:
        response = handle_chat_turn(message=request.message, session_id=request.session_id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing conversational turn: {str(e)}",
        )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSession,
    summary="Get chat session details",
    description="Retrieve full message history, accumulated site assessment variables, and asked question tracking for a session.",
)
async def get_session(session_id: str) -> ChatSession:
    """Retrieve session by ID."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found.",
        )
    return session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Clear chat session",
    description="Delete session memory and start afresh.",
)
async def clear_session(session_id: str) -> dict:
    """Clear session memory."""
    deleted = session_store.clear(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found.",
        )
    return {"status": "success", "message": f"Session '{session_id}' cleared."}
