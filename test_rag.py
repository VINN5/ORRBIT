import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.retriever import retrieve

def test_retrieval():
    print("=== RAG Retrieval Test (with Source Files) ===\n")
    
    queries = [
        "What is attention mechanism?",
        "Explain BERT model",
        "What is Docker used for?",
        "Give me a summary of deep learning",
        "Basic Python concepts",
        "How to run a Docker container?",
        "What are Python lists and dictionaries?"
    ]
    
    for query in queries:
        print(f"Query: {query}")
        context = retrieve(query, k=3)
        
        if context.strip():
            print("✅ Retrieved:")
            print("-" * 60)
            print(context[:700] + "..." if len(context) > 700 else context)
            print("-" * 60)
        else:
            print("❌ No context retrieved")
        print("\n")

if __name__ == "__main__":
    test_retrieval()