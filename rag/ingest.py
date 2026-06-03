"""
ingest.py — Load PDFs, text files, and Word docs from data/docs/ nested subfolders into FAISS.

Supports deeply nested folder structure:
    data/docs/
    ├── computing/
    │   ├── python/          <- python-specific docs
    │   ├── javascript/      <- js-specific docs
    │   ├── algorithms/
    │   ├── ai_ml/
    │   └── devops/
    ├── mathematics/
    │   ├── linear_algebra/
    │   ├── calculus/
    │   └── probability/
    ├── finance/
    │   ├── stocks/
    │   └── crypto/
    ├── science/
    ├── health/
    ├── climate/
    └── general/

Each chunk gets tagged with: category, subcategory, filename, and full path.

Usage:
    python rag/ingest.py                          # index everything
    python rag/ingest.py --category computing     # one top-level category
    python rag/ingest.py --sub python             # one subcategory anywhere
"""

import os
import sys
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from rag.retriever import index_documents

DOCS_DIR = Path("data/docs")

SUPPORTED = {
    ".pdf":  PyPDFLoader,
    ".txt":  TextLoader,
    ".docx": Docx2txtLoader,
}

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " "],
)


def load_file(path: Path, category: str, subcategory: str = None) -> list[Document]:
    """Load a single file and tag it with precise metadata."""
    ext = path.suffix.lower()
    loader_cls = SUPPORTED.get(ext)
    if not loader_cls:
        print(f"      [skip] Unsupported type: {path.name}")
        return []
    try:
        loader = loader_cls(str(path))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"]      = path.name
            doc.metadata["category"]    = category
            doc.metadata["subcategory"] = subcategory or category
            doc.metadata["topic"]       = subcategory or category
            doc.metadata["path"]        = str(path)
        print(f"      [load] {path.name} → {len(docs)} page(s)")
        return docs
    except Exception as e:
        print(f"      [error] {path.name}: {e}")
        return []


def walk_folder(folder: Path, category: str, sub_filter: str = None) -> list[Document]:
    """Recursively walk a folder, loading all supported files with metadata."""
    all_docs = []

    # Load files directly in this folder
    direct_files = [f for f in folder.iterdir()
                    if f.is_file() and f.suffix.lower() in SUPPORTED]
    if direct_files:
        subcategory = folder.name if folder.name != category else category
        if sub_filter and sub_filter != subcategory:
            pass
        else:
            for f in sorted(direct_files):
                all_docs.extend(load_file(f, category, subcategory))

    # Recurse into subfolders
    subfolders = [d for d in sorted(folder.iterdir()) if d.is_dir()]
    for subfolder in subfolders:
        subcategory = subfolder.name
        if sub_filter and sub_filter != subcategory:
            continue
        files = [f for f in subfolder.iterdir()
                 if f.is_file() and f.suffix.lower() in SUPPORTED]
        if files:
            print(f"\n    [{category.upper()} > {subcategory}] "
                  f"{len(files)} file(s):")
            for f in sorted(files):
                all_docs.extend(load_file(f, category, subcategory))
        # Recurse deeper if needed
        deeper = [d for d in subfolder.iterdir() if d.is_dir()]
        for deep in deeper:
            deep_files = [f for f in deep.iterdir()
                          if f.is_file() and f.suffix.lower() in SUPPORTED]
            if deep_files:
                print(f"\n    [{category.upper()} > {subcategory} > {deep.name}] "
                      f"{len(deep_files)} file(s):")
                for f in sorted(deep_files):
                    all_docs.extend(load_file(f, category, f"{subcategory}/{deep.name}"))

    return all_docs


def ingest_all(category_filter: str = None, sub_filter: str = None):
    """Index all categories or filter by category/subcategory."""
    if not DOCS_DIR.exists():
        print(f"[error] {DOCS_DIR} not found.")
        return

    top_folders = [d for d in sorted(DOCS_DIR.iterdir()) if d.is_dir()]
    if not top_folders:
        print(f"[warn] No folders found in {DOCS_DIR}")
        return

    if category_filter:
        top_folders = [d for d in top_folders if d.name == category_filter]
        if not top_folders:
            print(f"[error] Category '{category_filter}' not found.")
            return

    print(f"\n📂 Scanning {len(top_folders)} top-level folder(s)...\n")

    all_docs = []
    for folder in top_folders:
        category = folder.name
        print(f"\n  [{category.upper()}]")
        docs = walk_folder(folder, category, sub_filter)
        if not docs:
            print(f"    (no files found)")
        all_docs.extend(docs)

    if not all_docs:
        print("\n[error] No documents loaded.")
        return

    chunks = splitter.split_documents(all_docs)
    print(f"\n✂️  Split into {len(chunks)} chunks from {len(all_docs)} page(s)")
    print("⏳ Indexing into FAISS (downloading embedding model ~90MB on first run)...\n")
    index_documents(chunks)

    # Summary by subcategory
    sub_counts = {}
    for doc in all_docs:
        key = f"{doc.metadata.get('category','?')} > {doc.metadata.get('subcategory','?')}"
        sub_counts[key] = sub_counts.get(key, 0) + 1

    print(f"\n✅ Done! {len(chunks)} chunks indexed from {len(all_docs)} page(s)")
    print(f"\n   Breakdown:")
    for key, count in sorted(sub_counts.items()):
        print(f"   - {key:<35} {count} page(s)")
    print(f"\n   Index saved to: data/vector_index/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Index nested docs from data/docs/ into FAISS."
    )
    parser.add_argument(
        "--category", type=str, default=None,
        help="Top-level category e.g. --category computing"
    )
    parser.add_argument(
        "--sub", type=str, default=None,
        help="Subcategory e.g. --sub python"
    )
    args = parser.parse_args()
    ingest_all(category_filter=args.category, sub_filter=args.sub)