from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
from state import AgentState
from prompts.business_prompt import BUSINESS_SYSTEM_PROMPT

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

def business_node(state: AgentState) -> AgentState:
    context = state.get("retrieved_context", "")
    query = state["user_query"]
    messages = [
        {"role": "system", "content": BUSINESS_SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}" if context else query},
    ]
    response = llm.invoke(messages)
    answer = response.content
    return {**state, "final_answer": answer, "messages": state["messages"] + [AIMessage(content=answer)]}
