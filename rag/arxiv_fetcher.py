"""
arxiv_fetcher.py — Automatically fetch papers from arxiv by topic and index them.

Usage:
    # Fetch default topics (defined below)
    python rag/arxiv_fetcher.py

    # Fetch specific topics
    python rag/arxiv_fetcher.py --topics "machine learning" "quantum computing" --max 3
"""

import os
import sys
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from rag.retriever import index_documents

ARXIV_API = "http://export.arxiv.org/api/query"
NS = "{http://www.w3.org/2005/Atom}"

# Default topics — edit this list to add/remove topics you want
DEFAULT_TOPICS = [
    "artificial intelligence",
    "machine learning",
    "quantum computing",
    "climate change",
    "financial markets",
    "astrophysics",
    "mathematics",
    "computer vision",
    "natural language processing",
    "economics",
]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "],
)


def fetch_papers(topic: str, max_results: int = 2) -> list[Document]:
    """Fetch paper abstracts from arxiv API for a given topic."""
    params = urllib.parse.urlencode({
        "search_query": f"all:{topic}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"  [error] Could not fetch '{topic}': {e}")
        return []

    root = ET.fromstring(xml_data)
    docs = []

    for entry in root.findall(f"{NS}entry"):
        title     = entry.findtext(f"{NS}title", "").strip().replace("\n", " ")
        summary   = entry.findtext(f"{NS}summary", "").strip().replace("\n", " ")
        authors   = [a.findtext(f"{NS}name", "") for a in entry.findall(f"{NS}author")]
        link      = entry.findtext(f"{NS}id", "").strip()
        published = entry.findtext(f"{NS}published", "")[:10]

        if not title or not summary:
            continue

        content = (
            f"Title: {title}\n"
            f"Authors: {', '.join(authors[:3])}\n"
            f"Published: {published}\n"
            f"Topic: {topic}\n"
            f"Source: {link}\n\n"
            f"Abstract:\n{summary}"
        )

        docs.append(Document(
            page_content=content,
            metadata={
                "source": f"arxiv:{topic}",
                "title": title,
                "link": link,
                "published": published,
            },
        ))

    return docs


def fetch_and_index(topics: list[str], max_per_topic: int = 2):
    """Fetch papers for all topics and index them into FAISS."""
    print(f"\n Fetching papers for {len(topics)} topic(s), "
          f"{max_per_topic} paper(s) each...\n")

    all_docs = []
    for topic in topics:
        print(f"  Fetching: {topic}...")
        papers = fetch_papers(topic, max_results=max_per_topic)
        print(f"  -> {len(papers)} paper(s) fetched")
        all_docs.extend(papers)

    if not all_docs:
        print("\n[error] No papers fetched. Check your internet connection.")
        return

    total_papers = len(all_docs)
    chunks = splitter.split_documents(all_docs)

    print(f"\n Split into {len(chunks)} chunks from {total_papers} paper(s)")
    print("Indexing into FAISS (may take a moment)...\n")

    index_documents(chunks)

    print(f"\n Done! {len(chunks)} chunks indexed.")
    print(f"   Papers fetched : {total_papers}")
    print(f"   Topics covered : {', '.join(topics)}")
    print(f"   Index saved to : data/vector_index/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch arxiv papers by topic and index into FAISS."
    )
    parser.add_argument(
        "--topics", nargs="+",
        default=DEFAULT_TOPICS,
        help='Topics to search e.g. --topics "machine learning" "black holes"'
    )
    parser.add_argument(
        "--max", type=int, default=2,
        help="Max papers per topic (default: 2)"
    )
    args = parser.parse_args()
    fetch_and_index(topics=args.topics, max_per_topic=args.max)