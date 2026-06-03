"""
conversation_memory.py — Level 1: Conversation history within a session.

Keeps track of the full conversation so Orrbit can understand
follow-up questions and references like "that", "it", "the previous example".

Each session gets a unique session_id. History is lost when the session ends.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A single message in the conversation."""
    role:      str       # "user" or "assistant"
    content:   str       # message text
    domain:    str = ""  # which domain handled it
    timestamp: str = ""  # when it was sent

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%H:%M:%S")


class ConversationMemory:
    """
    Stores conversation history for a single session.
    Passed to the LLM so it understands context from earlier in the chat.
    """

    def __init__(self, max_history: int = 20):
        self.messages:    list[Message] = []
        self.max_history: int = max_history
        self.session_id:  str = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_user_message(self, content: str):
        """Record a user message."""
        self.messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant_message(self, content: str, domain: str = ""):
        """Record an assistant response."""
        self.messages.append(
            Message(role="assistant", content=content, domain=domain)
        )
        self._trim()

    def get_history_as_text(self) -> str:
        """
        Returns conversation history as formatted text.
        Injected into domain node prompts as context.
        """
        if not self.messages:
            return ""

        lines = ["--- Conversation History ---"]
        for msg in self.messages[-10:]:  # last 10 messages only
            prefix = "User" if msg.role == "user" else "Orrbit"
            lines.append(f"{prefix}: {msg.content}")
        lines.append("--- End of History ---")
        return "\n".join(lines)

    def get_history_as_messages(self) -> list[dict]:
        """
        Returns history in LangChain message format.
        Used directly in LLM calls for best context understanding.
        """
        result = []
        for msg in self.messages[-10:]:
            result.append({
                "role":    msg.role,
                "content": msg.content,
            })
        return result

    def is_followup(self, query: str) -> bool:
        """
        Detects if the query is a follow-up to a previous message.
        Helps decide whether to use history context.
        """
        followup_indicators = [
            "that", "it", "this", "those", "them", "the same",
            "previous", "again", "more", "also", "what about",
            "and", "but", "however", "elaborate", "explain more",
            "give me an example", "can you", "what do you mean",
        ]
        lower = query.lower()
        return (
            len(self.messages) > 0 and
            any(indicator in lower for indicator in followup_indicators)
        )

    def clear(self):
        """Clear the conversation history."""
        self.messages = []

    def _trim(self):
        """Keep only the most recent messages."""
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    @property
    def turn_count(self) -> int:
        """Number of conversation turns so far."""
        return sum(1 for m in self.messages if m.role == "user")


# Session store — maps session_id to ConversationMemory
# In production this would be Redis or a database
_sessions: dict[str, ConversationMemory] = {}


def get_session(session_id: str) -> ConversationMemory:
    """Get or create a conversation memory for a session."""
    if session_id not in _sessions:
        _sessions[session_id] = ConversationMemory()
    return _sessions[session_id]


def clear_session(session_id: str):
    """Clear a session's conversation history."""
    if session_id in _sessions:
        del _sessions[session_id]