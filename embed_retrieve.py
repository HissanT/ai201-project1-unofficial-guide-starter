"""Embed chunked documents in ChromaDB and retrieve relevant source passages.

Examples:
    python embed_retrieve.py index
    python embed_retrieve.py query "What do students say about Galesburg?"
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_PATH = Path("chunks.jsonl")
CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "unofficial_guide_chunks"
DEFAULT_TOP_K = 5
EMBED_BATCH_SIZE = 32

REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "source_file",
    "source_title",
    "source_type",
    "url",
    "text",
}


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    text: str
    source_file: str
    source_title: str
    source_type: str
    url: str
    chunk_position: int
    distance: float

    @property
    def relevance_score(self) -> float:
        """Convert cosine distance to a higher-is-better score."""
        return 1.0 - self.distance


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    """Load and validate ingestion-pipeline chunks from a JSONL file."""
    chunks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with chunks_path.open(encoding="utf-8") as chunk_file:
        for line_number, line in enumerate(chunk_file, start=1):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {chunks_path} on line {line_number}"
                ) from exc

            missing = REQUIRED_CHUNK_FIELDS - chunk.keys()
            if missing:
                fields = ", ".join(sorted(missing))
                raise ValueError(
                    f"Chunk on line {line_number} is missing required fields: {fields}"
                )

            chunk_id = str(chunk["chunk_id"]).strip()
            text = str(chunk["text"]).strip()
            if not chunk_id or not text:
                raise ValueError(
                    f"Chunk on line {line_number} must have a non-empty ID and text"
                )
            if chunk_id in seen_ids:
                raise ValueError(f"Duplicate chunk ID on line {line_number}: {chunk_id}")

            seen_ids.add(chunk_id)
            chunks.append(chunk)

    if not chunks:
        raise ValueError(f"No chunks found in {chunks_path}")
    return chunks


def prepare_chroma_records(
    chunks: Sequence[dict[str, Any]],
) -> tuple[list[str], list[str], list[dict[str, str | int]]]:
    """Build Chroma IDs, documents, and attribution metadata."""
    positions: defaultdict[str, int] = defaultdict(int)
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []

    for chunk in chunks:
        source_file = str(chunk["source_file"])
        positions[source_file] += 1

        ids.append(str(chunk["chunk_id"]))
        documents.append(str(chunk["text"]))
        metadatas.append(
            {
                "source_file": source_file,
                "source_title": str(chunk["source_title"]),
                "source_type": str(chunk["source_type"]),
                "url": str(chunk["url"]),
                "chunk_position": positions[source_file],
                "char_count": int(chunk.get("char_count", len(str(chunk["text"])))),
            }
        )

    return ids, documents, metadatas


def load_embedding_model(model_name: str = MODEL_NAME) -> Any:
    """Load the local sentence-transformers embedding model."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def create_chroma_client(chroma_path: Path = CHROMA_PATH) -> Any:
    """Create a persistent local ChromaDB client."""
    import chromadb

    chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(chroma_path))


def _collection_names(client: Any) -> set[str]:
    names: set[str] = set()
    for collection in client.list_collections():
        names.add(collection if isinstance(collection, str) else collection.name)
    return names


def _batches(items: Sequence[Any], batch_size: int) -> Iterable[Sequence[Any]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def build_vector_store(
    chunks_path: Path = CHUNKS_PATH,
    chroma_path: Path = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    model_name: str = MODEL_NAME,
    batch_size: int = EMBED_BATCH_SIZE,
    *,
    model: Any | None = None,
    client: Any | None = None,
) -> int:
    """Embed every chunk and replace the persistent Chroma collection."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    chunks = load_chunks(chunks_path)
    ids, documents, metadatas = prepare_chroma_records(chunks)
    model = model or load_embedding_model(model_name)
    client = client or create_chroma_client(chroma_path)

    if collection_name in _collection_names(client):
        client.delete_collection(collection_name)
    collection = client.create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": model_name,
        },
    )

    for id_batch, document_batch, metadata_batch in zip(
        _batches(ids, batch_size),
        _batches(documents, batch_size),
        _batches(metadatas, batch_size),
    ):
        embeddings = model.encode(
            list(document_batch),
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        collection.add(
            ids=list(id_batch),
            documents=list(document_batch),
            metadatas=list(metadata_batch),
            embeddings=embeddings.tolist(),
        )

    return len(chunks)


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    chroma_path: Path = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    model_name: str = MODEL_NAME,
    *,
    model: Any | None = None,
    client: Any | None = None,
) -> list[RetrievalResult]:
    """Return the top-k chunks for a query with source attribution metadata."""
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    model = model or load_embedding_model(model_name)
    client = client or create_chroma_client(chroma_path)
    collection = client.get_collection(collection_name)
    available_chunks = collection.count()
    if available_chunks == 0:
        return []

    query_embedding = model.encode(
        [query],
        show_progress_bar=False,
        normalize_embeddings=True,
    )[0].tolist()
    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, available_chunks),
        include=["documents", "metadatas", "distances"],
    )

    ids = response["ids"][0]
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]

    return [
        RetrievalResult(
            chunk_id=chunk_id,
            text=document,
            source_file=str(metadata["source_file"]),
            source_title=str(metadata["source_title"]),
            source_type=str(metadata["source_type"]),
            url=str(metadata["url"]),
            chunk_position=int(metadata["chunk_position"]),
            distance=float(distance),
        )
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances
        )
    ]


def print_results(results: Sequence[RetrievalResult]) -> None:
    for rank, result in enumerate(results, start=1):
        print(f"\n--- Result {rank} ---")
        print(
            f"Source: {result.source_title} "
            f"({result.source_file}, chunk {result.chunk_position})"
        )
        print(f"Type: {result.source_type}")
        print(f"URL: {result.url}")
        print(f"Relevance: {result.relevance_score:.3f}")
        print(result.text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed chunks in ChromaDB and run semantic retrieval."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index", help="Embed chunks and rebuild the ChromaDB collection."
    )
    index_parser.add_argument("--chunks", type=Path, default=CHUNKS_PATH)
    index_parser.add_argument("--db", type=Path, default=CHROMA_PATH)
    index_parser.add_argument("--batch-size", type=int, default=EMBED_BATCH_SIZE)

    query_parser = subparsers.add_parser(
        "query", help="Retrieve the most relevant chunks for a question."
    )
    query_parser.add_argument("query")
    query_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    query_parser.add_argument("--db", type=Path, default=CHROMA_PATH)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "index":
        count = build_vector_store(
            chunks_path=args.chunks,
            chroma_path=args.db,
            batch_size=args.batch_size,
        )
        print(
            f"Embedded {count} chunks with {MODEL_NAME} "
            f"into {args.db}/{COLLECTION_NAME}."
        )
        return

    results = retrieve(
        query=args.query,
        top_k=args.top_k,
        chroma_path=args.db,
    )
    print_results(results)


if __name__ == "__main__":
    main()
