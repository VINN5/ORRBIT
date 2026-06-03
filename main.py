from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graph.builder import agent


def run(query: str) -> str:
    """Run the multi-domain agent on a single query."""
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "domain": "",
        "user_query": "",
        "retrieved_context": "",
        "final_answer": "",
        "metadata": {},
    }

    result = agent.invoke(initial_state)
    return result["final_answer"]


def main():
    print("🤖 Multi-Domain AI Agent (type 'exit' to quit)\n")
    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        try:
            answer = run(query)
            print(f"\nAgent: {answer}\n")
        except Exception as e:
            print(f"[Error] {e}\n")


if __name__ == "__main__":
    main()