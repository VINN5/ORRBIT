import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from state import AgentState

VECTOR_INDEX_PATH = "data/vector_index"
TOP_K = 4

_vectorstore = None
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _load_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    embeddings = _get_embeddings()

    if os.path.exists(VECTOR_INDEX_PATH):
        _vectorstore = FAISS.load_local(
            VECTOR_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        print(f"[RAG] Loaded vector index from {VECTOR_INDEX_PATH}")
    else:
        print("[RAG] No index found — skipping RAG for now.")
        _vectorstore = None

    return _vectorstore


def retrieve(query: str, k: int = TOP_K) -> str:
    """Retrieves top-k relevant chunks for a query."""
    store = _load_vectorstore()
    if store is None:
        return ""
    docs = store.similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in docs)


def rag_node(state: AgentState) -> AgentState:
    """LangGraph node: retrieves context and adds it to state."""
    query = state.get("user_query", "")
    context = retrieve(query) if query else ""
    return {**state, "retrieved_context": context}


def _clean_chunks(docs: list[Document]) -> list[Document]:
    """Filter out bad chunks that would cause embedding errors."""
    cleaned = []
    skipped = 0

    for doc in docs:
        content = doc.page_content

        # Must be a string
        if not isinstance(content, str):
            try:
                content = str(content)
            except Exception:
                skipped += 1
                continue

        # Strip whitespace
        content = content.strip()

        # Must have enough content
        if len(content) < 20:
            skipped += 1
            continue

        # Must be mostly printable
        printable = sum(c.isprintable() for c in content)
        if len(content) > 0 and printable / len(content) < 0.7:
            skipped += 1
            continue

        # Replace null bytes which break tokenizers
        content = content.replace("\x00", " ").replace("\ufffd", " ")

        doc.page_content = content
        cleaned.append(doc)

    if skipped > 0:
        print(f"[RAG] Skipped {skipped} invalid chunks")
    print(f"[RAG] {len(cleaned)} valid chunks ready for indexing")
    return cleaned


def index_documents(docs: list[Document]):
    """Indexes new documents into the FAISS store and persists to disk."""
    global _vectorstore
    embeddings = _get_embeddings()
    os.makedirs(VECTOR_INDEX_PATH, exist_ok=True)

    # Clean chunks
    docs = _clean_chunks(docs)
    if not docs:
        print("[RAG] No valid chunks to index.")
        return

    # Index in batches of 200 to be safe
    batch_size = 200
    batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]
    print(f"[RAG] Indexing {len(docs)} chunks in {len(batches)} batch(es)...")

    for i, batch in enumerate(batches):
        print(f"[RAG] Batch {i + 1}/{len(batches)} ({len(batch)} chunks)...")
        try:
            if _vectorstore is None:
                _vectorstore = FAISS.from_documents(batch, embeddings)
            else:
                _vectorstore.add_documents(batch)
        except Exception as e:
            print(f"[RAG] Batch {i + 1} failed: {e} — skipping")
            continue

    if _vectorstore:
        _vectorstore.save_local(VECTOR_INDEX_PATH)
        print(f"[RAG] Indexed {len(docs)} documents → {VECTOR_INDEX_PATH}")