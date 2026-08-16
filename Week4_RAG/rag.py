"""
rag_pipeline.py
"Dead Philosophers, Live Chat" — ask a question, get an answer grounded
entirely in real passages from public-domain philosophy/Sufi texts.

Design choice that matters here: answers are written in THIRD PERSON
("Nietzsche argues that...") and cite the source work, not first-person
"as if I were Nietzsche" impersonation. That keeps every claim traceable
to an actual passage instead of the model inventing quotes a dead person
never said.

Setup:
    pip install -r requirements.txt
    python fetch_data.py                # builds data/*.txt + manifest.json
    export GROQ_API_KEY=your_key_here

Run:
    python rag_pipeline.py "What did Nietzsche think about suffering?"
"""

import os
import sys
import json
import glob
from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

DATA_DIR = "data"
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "dead_philosophers"
EMBED_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 5


@dataclass
class RetrievedChunk:
    text: str
    author: str
    title: str
    distance: float


def load_documents(data_dir: str, manifest_file: str) -> list:
    """Load each book's text paired with its author/title from the manifest."""
    if not os.path.exists(manifest_file):
        sys.exit(f"'{manifest_file}' not found. Run fetch_data.py first.")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    docs = []
    for filename, meta in manifest.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            print(f"[warn] '{path}' listed in manifest but missing on disk — skipping.")
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            docs.append(
                {"text": text, "author": meta["author"], "title": meta["title"]}
            )

    if not docs:
        sys.exit("No usable documents found. Run fetch_data.py again.")
    return docs


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Sliding-window chunker that tries to break on sentence/paragraph boundaries."""
    if overlap >= size:
        raise ValueError("chunk overlap must be smaller than chunk size")

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + size, text_len)
        if end < text_len:
            boundary = text.rfind(". ", start, end)
            if boundary == -1 or boundary < start + size * 0.5:
                boundary = text.rfind("\n", start, end)
            if boundary != -1 and boundary > start:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end - overlap > start else end

    return chunks


def build_index(
    docs: list, embedder: SentenceTransformer, client
) -> "chromadb.Collection":
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    ids, texts, metadatas = [], [], []
    for doc in docs:
        pieces = chunk_text(doc["text"])
        for i, piece in enumerate(pieces):
            ids.append(f"{doc['author']}::{doc['title']}::{i}")
            texts.append(piece)
            metadatas.append({"author": doc["author"], "title": doc["title"]})

    if not texts:
        sys.exit("Chunking produced 0 chunks — check source documents.")

    print(f"Embedding {len(texts)} chunks from {len(docs)} book(s)...")
    embeddings = embedder.encode(texts, show_progress_bar=True).tolist()

    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return collection


def retrieve(
    query: str, collection, embedder: SentenceTransformer, k: int = TOP_K
) -> list:
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    if not results["documents"] or not results["documents"][0]:
        return []

    return [
        RetrievedChunk(
            text=doc, author=meta["author"], title=meta["title"], distance=dist
        )
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        )
    ]


def generate_answer(query: str, retrieved: list) -> str:
    if not retrieved:
        return "None of the indexed texts touch on that — try rephrasing or asking something else."

    context = "\n\n---\n\n".join(
        f"[{c.author} — {c.title}]\n{c.text}" for c in retrieved
    )
    prompt = (
        "You are a research assistant summarizing what specific philosophers/mystics "
        "actually wrote, based ONLY on the passages below. Rules:\n"
        "1. Write in THIRD PERSON ('Nietzsche argues...', not 'I believe...').\n"
        "2. Never invent a quote — only paraphrase, and cite the author + work for every claim.\n"
        "3. If the passages don't address the question, say so explicitly instead of guessing.\n"
        "4. If two thinkers disagree in the passages, point that out.\n\n"
        f"Passages:\n{context}\n\nQuestion: {query}"
    )

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[generation failed: {e}]"


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python rag_pipeline.py "your question here"')
    query = sys.argv[1]

    print("Loading documents...")
    docs = load_documents(DATA_DIR, MANIFEST_FILE)

    print(f"Loading embedding model '{EMBED_MODEL}'...")
    embedder = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = build_index(docs, embedder, client)

    print(f"\nQuery: {query}")
    retrieved = retrieve(query, collection, embedder)

    print("\nRetrieved passages (lower distance = more relevant):")
    for i, c in enumerate(retrieved, 1):
        preview = c.text[:110].replace("\n", " ")
        print(f"  {i}. [{c.author} — {c.title}] dist={c.distance:.3f}  {preview}...")

    answer = generate_answer(query, retrieved)
    print("\nAnswer:\n" + answer)


if __name__ == "__main__":
    main()
