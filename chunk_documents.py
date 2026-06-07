"""Chunk cleaned documents using the strategy from planning.md.

Strategy:
- Use natural review/comment boundaries first.
- Target about 400 characters per chunk.
- Keep short complete reviews/comments whole.
- Use 0 overlap for normal chunks.
- Use 50-100 characters of overlap only when splitting long chunks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


CLEAN_DIR = Path("cleaned_documents")
OUTPUT_PATH = Path("chunks.jsonl")
TARGET_CHARS = 400
MAX_NATURAL_CHARS = 650
LONG_CHUNK_OVERLAP = 75


@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    source_title: str
    source_type: str
    url: str
    text: str
    char_count: int


def parse_metadata(text: str) -> dict[str, str]:
    metadata = {
        "source_title": "",
        "source_type": "",
        "url": "",
    }

    for line in text.splitlines():
        if line.startswith("Source title:"):
            metadata["source_title"] = line.split(":", 1)[1].strip()
        elif line.startswith("Source type:"):
            metadata["source_type"] = line.split(":", 1)[1].strip()
        elif line.startswith("URL:"):
            metadata["url"] = line.split(":", 1)[1].strip()

    return metadata


def section_between(text: str, start: str, end: str | None = None) -> str:
    start_match = re.search(rf"^{re.escape(start)}\s*$", text, flags=re.MULTILINE)
    if not start_match:
        return ""

    start_index = start_match.end()
    if end is None:
        return text[start_index:].strip()

    end_match = re.search(rf"^{re.escape(end)}\s*$", text[start_index:], flags=re.MULTILINE)
    if not end_match:
        return text[start_index:].strip()

    return text[start_index : start_index + end_match.start()].strip()


def split_marker_blocks(section: str, marker: str) -> list[str]:
    """Split text into blocks that start after a repeated marker line."""
    blocks: list[str] = []
    current: list[str] = []

    for line in section.splitlines():
        if line.strip() == marker:
            if current:
                block = "\n".join(current).strip()
                if block:
                    blocks.append(block)
            current = []
        else:
            current.append(line)

    if current:
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)

    return blocks


def split_course_blocks(section: str) -> list[str]:
    """Split RateMyProfessor review text into one block per course review."""
    blocks: list[str] = []
    current: list[str] = []

    for line in section.splitlines():
        if line.startswith("Course:") and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)

    return blocks


def natural_units(text: str) -> list[str]:
    """Return natural units: post descriptions, comments, reviews, or course reviews."""
    units: list[str] = []

    post_description = section_between(text, "Post description:", "Thread text:")
    if post_description:
        units.append("Post description:\n" + post_description)

    thread_text = section_between(text, "Thread text:")
    if thread_text:
        for block in split_marker_blocks(thread_text, "Comment:"):
            units.append("Comment:\n" + block)

    review_text = section_between(text, "Review text:")
    if review_text:
        if "Course:" in review_text:
            units.extend(split_course_blocks(review_text))
        else:
            for block in split_marker_blocks(review_text, "Review:"):
                units.append("Review:\n" + block)

    # Fallback for any document that does not match expected section markers.
    if not units:
        body = re.sub(
            r"^(Source title|Source type|URL):.*$",
            "",
            text,
            flags=re.MULTILINE,
        ).strip()
        units.extend(paragraphs(body))

    return [unit.strip() for unit in units if unit.strip()]


def paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]


def overlap_prefix(previous_text: str) -> str:
    if not previous_text:
        return ""
    prefix = previous_text[-LONG_CHUNK_OVERLAP:].strip()
    first_space = prefix.find(" ")
    if first_space > 0:
        prefix = prefix[first_space + 1 :]
    return prefix


def split_long_unit(unit: str) -> list[str]:
    """Split a long natural unit by paragraphs/sentences with small overlap."""
    if len(unit) <= MAX_NATURAL_CHARS:
        return [unit]

    pieces = paragraphs(unit)
    if len(pieces) == 1:
        pieces = sentences(unit)

    chunks: list[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current}\n\n{piece}".strip() if current else piece
        if len(candidate) <= TARGET_CHARS or not current:
            current = candidate
            continue

        chunks.append(current)
        prefix = overlap_prefix(current)
        current = f"{prefix} {piece}".strip() if prefix else piece

    if current:
        chunks.append(current)

    final_chunks: list[str] = []
    for chunk in chunks:
        if len(chunk) <= MAX_NATURAL_CHARS:
            final_chunks.append(chunk)
        else:
            final_chunks.extend(split_sentence_window(chunk))
    return final_chunks


def split_sentence_window(text: str) -> list[str]:
    chunks: list[str] = []
    current = ""

    for sentence in sentences(text):
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= TARGET_CHARS or not current:
            current = candidate
            continue

        chunks.append(current)
        prefix = overlap_prefix(current)
        current = f"{prefix} {sentence}".strip() if prefix else sentence

    if current:
        chunks.append(current)
    return chunks


def chunk_document(path: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    metadata = parse_metadata(text)
    chunks: list[Chunk] = []

    for unit_index, unit in enumerate(natural_units(text), start=1):
        for split_index, chunk_text in enumerate(split_long_unit(unit), start=1):
            chunk_id = f"{path.stem}-{unit_index:03d}-{split_index:02d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source_file=path.name,
                    source_title=metadata["source_title"],
                    source_type=metadata["source_type"],
                    url=metadata["url"],
                    text=chunk_text,
                    char_count=len(chunk_text),
                )
            )

    return chunks


def load_all_chunks(clean_dir: Path = CLEAN_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(clean_dir.glob("*.txt")):
        chunks.extend(chunk_document(path))
    return chunks


def write_chunks(chunks: list[Chunk], output_path: Path = OUTPUT_PATH) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def print_sample_chunks(chunks: list[Chunk], sample_count: int = 5) -> None:
    print(f"Total chunks: {len(chunks)}")
    print(f"Wrote chunks to: {OUTPUT_PATH}")

    for chunk in chunks[:sample_count]:
        print("\n--- Chunk ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Source: {chunk.source_title}")
        print(f"Type: {chunk.source_type}")
        print(f"Chars: {chunk.char_count}")
        print(chunk.text)


def main() -> None:
    chunks = load_all_chunks()
    write_chunks(chunks)
    print_sample_chunks(chunks, sample_count=5)


if __name__ == "__main__":
    main()
