from langgraph.graph import StateGraph, END

from state import AgentState
from graph.router_node import router_node, route_to_domain
from domains.finance.finance_node import finance_node
from domains.general.general_node import general_node
from domains.computing.computing_node import computing_node
from domains.health.health_node import health_node
from domains.legal.legal_node import legal_node
from domains.mental_health.mental_health_node import mental_health_node
from domains.business.business_node import business_node
from domains.history.history_node import history_node
from domains.astronomy.astronomy_node import astronomy_node
from domains.sports.sports_node import sports_node
from domains.technology.technology_node import technology_node
from rag.retriever import rag_node
from tools.search_tool import web_search_node

ALL_DOMAINS = [
    "finance", "computing", "health", "legal", "mental_health",
    "business", "history", "astronomy", "sports", "technology", "general"
]

DOMAIN_NODES = {
    "finance":       finance_node,
    "computing":     computing_node,
    "health":        health_node,
    "legal":         legal_node,
    "mental_health": mental_health_node,
    "business":      business_node,
    "history":       history_node,
    "astronomy":     astronomy_node,
    "sports":        sports_node,
    "technology":    technology_node,
    "general":       general_node,
}


def build_graph():
    """Assembles and compiles the full Orrbit LangGraph agent."""
    graph = StateGraph(AgentState)

    # --- Core nodes ---
    graph.add_node("router",     router_node)
    graph.add_node("rag",        rag_node)
    graph.add_node("web_search", web_search_node)

    # --- Domain nodes ---
    for domain, node_fn in DOMAIN_NODES.items():
        graph.add_node(domain, node_fn)

    # --- Entry point ---
    graph.set_entry_point("router")

    # --- Router → RAG ---
    graph.add_edge("router", "rag")

    # --- RAG → Web Search (fallback if no docs found) ---
    graph.add_edge("rag", "web_search")

    # --- Web Search → domain node ---
    graph.add_conditional_edges(
        "web_search",
        route_to_domain,
        {domain: domain for domain in ALL_DOMAINS},
    )

    # --- All domain nodes → END ---
    for domain in ALL_DOMAINS:
        graph.add_edge(domain, END)

    return graph.compile()


agent = build_graph()
