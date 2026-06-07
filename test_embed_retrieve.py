"""Focused tests for embedding record preparation and retrieval."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from embed_retrieve import (
    build_vector_store,
    load_chunks,
    prepare_chroma_records,
    retrieve,
)


class FakeEmbeddingRow:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def tolist(self) -> list[float]:
        return self.values


class FakeEmbeddings:
    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def tolist(self) -> list[list[float]]:
        return self.rows

    def __getitem__(self, index: int) -> FakeEmbeddingRow:
        return FakeEmbeddingRow(self.rows[index])


class FakeModel:
    def encode(self, texts: list[str], **_: Any) -> FakeEmbeddings:
        return FakeEmbeddings([[float(len(text)), 1.0] for text in texts])


class FakeCollection:
    def __init__(self) -> None:
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []

    def add(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        self.ids.extend(ids)
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.embeddings = embeddings

    def count(self) -> int:
        return len(self.ids)

    def query(self, **_: Any) -> dict[str, list[list[Any]]]:
        return {
            "ids": [self.ids[:1]],
            "documents": [self.documents[:1]],
            "metadatas": [self.metadatas[:1]],
            "distances": [[0.2]],
        }


class FakeClient:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def list_collections(self) -> list[str]:
        return list(self.collections)

    def delete_collection(self, name: str) -> None:
        del self.collections[name]

    def create_collection(self, name: str, metadata: dict[str, str]) -> FakeCollection:
        collection = FakeCollection()
        collection.collection_metadata = metadata
        self.collections[name] = collection
        return collection

    def get_collection(self, name: str) -> FakeCollection:
        return self.collections[name]


def write_chunks(path: Path) -> None:
    chunks = [
        {
            "chunk_id": "source-a-001-01",
            "source_file": "source-a.txt",
            "source_title": "Source A",
            "source_type": "Reddit thread",
            "url": "https://example.com/a",
            "text": "First passage",
            "char_count": 13,
        },
        {
            "chunk_id": "source-a-002-01",
            "source_file": "source-a.txt",
            "source_title": "Source A",
            "source_type": "Reddit thread",
            "url": "https://example.com/a",
            "text": "Second passage",
            "char_count": 14,
        },
    ]
    path.write_text(
        "".join(json.dumps(chunk) + "\n" for chunk in chunks),
        encoding="utf-8",
    )


class EmbedRetrieveTests(unittest.TestCase):
    def test_prepare_records_tracks_position_within_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            chunks_path = Path(temp_dir) / "chunks.jsonl"
            write_chunks(chunks_path)
            chunks = load_chunks(chunks_path)

        ids, documents, metadatas = prepare_chroma_records(chunks)

        self.assertEqual(ids, ["source-a-001-01", "source-a-002-01"])
        self.assertEqual(documents, ["First passage", "Second passage"])
        self.assertEqual(
            [metadata["chunk_position"] for metadata in metadatas],
            [1, 2],
        )

    def test_build_and_retrieve_preserve_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            chunks_path = Path(temp_dir) / "chunks.jsonl"
            write_chunks(chunks_path)
            client = FakeClient()
            model = FakeModel()

            count = build_vector_store(
                chunks_path=chunks_path,
                client=client,
                model=model,
                batch_size=10,
            )
            results = retrieve(
                "student experience",
                top_k=5,
                client=client,
                model=model,
            )

        self.assertEqual(count, 2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_file, "source-a.txt")
        self.assertEqual(results[0].chunk_position, 1)
        self.assertAlmostEqual(results[0].relevance_score, 0.8)


if __name__ == "__main__":
    unittest.main()
