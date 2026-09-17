"""In-memory session store for multi-turn chat interactions."""

import threading
from typing import Dict, Optional, List
from uuid import uuid4

from daaruka.chat.models import ChatSession


class InMemorySessionStore:
    """Thread-safe in-memory session store keyed by session_id."""

    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: Optional[str] = None) -> ChatSession:
        """Retrieve an existing session or initialize a new one."""
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]

            new_id = session_id if session_id else str(uuid4())
            session = ChatSession(session_id=new_id)
            self._sessions[new_id] = session
            return session

    def get(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve a session by ID without auto-creating."""
        with self._lock:
            return self._sessions.get(session_id)

    def save(self, session: ChatSession) -> None:
        """Save/update an existing session in the store."""
        with self._lock:
            self._sessions[session.session_id] = session

    def clear(self, session_id: str) -> bool:
        """Remove a session from storage."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def list_session_ids(self) -> List[str]:
        """List all active session IDs."""
        with self._lock:
            return list(self._sessions.keys())


# Global default session store instance
session_store = InMemorySessionStore()
