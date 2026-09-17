"""Data models for chat interactions, session memory, and conversational state."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4
from pydantic import BaseModel, Field

from daaruka.reasoning.models import SiteAssessmentInput, Recommendation


class ChatMessage(BaseModel):
    """A single message within a conversation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """Encapsulates multi-turn conversational session memory and accumulated site data."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    accumulated_assessment: SiteAssessmentInput = Field(default_factory=SiteAssessmentInput)
    messages: List[ChatMessage] = Field(default_factory=list)
    asked_categories: List[str] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, role: Literal["user", "assistant", "system"], content: str, metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """Append a message to the conversation history."""
        msg = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg

    def record_question(self, category: str, question: str) -> None:
        """Track an asked clarifying question to avoid repetition."""
        if category not in self.asked_categories:
            self.asked_categories.append(category)
        if question not in self.asked_questions:
            self.asked_questions.append(question)
        self.updated_at = datetime.utcnow()


class ChatRequest(BaseModel):
    """Incoming payload for chat endpoint."""

    message: str = Field(..., description="User's natural language message or query.")
    session_id: Optional[str] = Field(default=None, description="Existing session ID if continuing a conversation.")


class SessionStateSummary(BaseModel):
    """Summary of current session state and accumulated variables."""

    session_id: str
    accumulated_fields: Dict[str, Any]
    data_completeness_score: float
    missing_categories: List[str]
    present_categories: List[str]
    total_messages: int


class ChatResponse(BaseModel):
    """Outgoing response from chat endpoint."""

    session_id: str
    response_text: str
    session_state_summary: SessionStateSummary
    is_asking_clarification: bool
    recommendations: Optional[List[Recommendation]] = None
    extracted_in_this_turn: Optional[Dict[str, Any]] = None
