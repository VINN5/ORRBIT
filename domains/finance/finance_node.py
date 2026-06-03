from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage

from state import AgentState
from domains.finance.finance_tools import get_finance_tools
from prompts.finance_prompt import FINANCE_SYSTEM_PROMPT

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(get_finance_tools())


def finance_node(state: AgentState) -> AgentState:
    """Handles finance-domain queries, optionally calling finance tools."""
    context = state.get("retrieved_context", "")
    query = state["user_query"]

    messages = [
        {"role": "system", "content": FINANCE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}" if context else query,
        },
    ]

    response = llm_with_tools.invoke(messages)
    answer = response.content if isinstance(response.content, str) else str(response.content)

    return {
        **state,
        "final_answer": answer,
        "messages": state["messages"] + [AIMessage(content=answer)],
    }
