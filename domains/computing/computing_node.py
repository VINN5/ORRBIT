from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage

from state import AgentState
from prompts.computing_prompt import COMPUTING_SYSTEM_PROMPT

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def computing_node(state: AgentState) -> AgentState:
    """Handles computing, programming, and AI/ML domain queries."""
    context = state.get("retrieved_context", "")
    query = state["user_query"]

    messages = [
        {"role": "system", "content": COMPUTING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from documents:\n{context}\n\nQuestion: {query}"
            if context else query,
        },
    ]

    response = llm.invoke(messages)
    answer = response.content

    return {
        **state,
        "final_answer": answer,
        "messages": state["messages"] + [AIMessage(content=answer)],
    }