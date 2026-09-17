"""Chat module providing multi-turn memory, field extraction, and conversational reasoning."""

from daaruka.chat.models import (
    ChatMessage,
    ChatSession,
    ChatRequest,
    ChatResponse,
    SessionStateSummary,
)
from daaruka.chat.session_store import session_store, InMemorySessionStore
from daaruka.chat.extractor import extract_site_assessment_from_text
from daaruka.chat.turn_handler import handle_chat_turn, merge_assessment_inputs

__all__ = [
    "ChatMessage",
    "ChatSession",
    "ChatRequest",
    "ChatResponse",
    "SessionStateSummary",
    "session_store",
    "InMemorySessionStore",
    "extract_site_assessment_from_text",
    "handle_chat_turn",
    "merge_assessment_inputs",
]
