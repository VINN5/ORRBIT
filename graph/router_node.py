from langchain_groq import ChatGroq
from state import AgentState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

ROUTER_PROMPT = """You are a query router for Orrbit — a multi-domain AI assistant.
Classify the user's query into exactly one domain.

Domains:
- finance: stocks, investing, budgeting, crypto, banking, taxes, financial planning
- computing: programming, software, algorithms, AI, machine learning, Docker, databases
- health: symptoms, medicine, nutrition, fitness, wellness, drugs
- legal: contracts, rights, law, legal processes, court, regulations
- mental_health: depression, anxiety, stress, grief, emotions, therapy, relationships, suicide
- business: startups, entrepreneurship, marketing, strategy, leadership, management
- history: world history, civilizations, wars, cultures, historical figures, events
- astronomy: space, planets, stars, black holes, galaxies, missions, cosmology
- sports: football, basketball, athletics, fitness training, sports analytics
- technology: phones, gadgets, laptops, consumer electronics, tech reviews, latest devices
- general: everything else — science, math, education, philosophy, languages

Respond with ONLY the domain name, nothing else.

Query: {query}
"""

VALID_DOMAINS = {
    "finance", "computing", "health", "legal", "mental_health",
    "business", "history", "astronomy", "sports", "technology", "general"
}

DOMAIN_ALIASES = {
    "tech": "technology",
    "gadgets": "technology",
    "phones": "technology",
    "code": "computing",
    "coding": "computing",
    "programming": "computing",
    "cs": "computing",
    "ai": "computing",
    "ml": "computing",
    "medicine": "health",
    "medical": "health",
    "mental": "mental_health",
    "psychology": "mental_health",
    "depression": "mental_health",
    "anxiety": "mental_health",
    "law": "legal",
    "lawyer": "legal",
    "startup": "business",
    "marketing": "business",
    "economics": "finance",
    "crypto": "finance",
    "space": "astronomy",
    "universe": "astronomy",
    "soccer": "sports",
    "football": "sports",
    "culture": "history",
    "science": "general",
    "math": "general",
    "mathematics": "general",
}


def router_node(state: AgentState) -> AgentState:
    """Classifies the user query and sets the domain in state."""
    query = state["messages"][-1].content
    prompt = ROUTER_PROMPT.format(query=query)
    response = llm.invoke(prompt)
    domain = response.content.strip().lower().strip(".,!? \n")

    if domain not in VALID_DOMAINS:
        domain = DOMAIN_ALIASES.get(domain, "general")

    print(f"🔀 Orrbit routing → {domain.upper()}")

    return {**state, "domain": domain, "user_query": query}


def route_to_domain(state: AgentState) -> str:
    return state.get("domain", "general")


def route_to_domain(state: AgentState) -> str:
    """Conditional edge: returns the domain string to select next node."""
    return state.get("domain", "general")
