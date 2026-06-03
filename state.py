from typing import Annotated, Any
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Shared state passed between all nodes in the Orrbit graph."""
    messages:          Annotated[list, add_messages]
    domain:            str           # Detected domain e.g. "computing", "health"
    user_query:        str           # Original user query
    retrieved_context: str           # Context from RAG or web search
    final_answer:      str           # Final response to return to user
    used_web_search:   bool          # True if Tavily was used instead of RAG
    metadata:          dict[str, Any] # Catch-all for domain-specific data