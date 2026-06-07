"""Load and clean the manually collected source documents.

This script is intentionally limited to ingestion + cleaning. It does not chunk,
embed, retrieve, or call an LLM.
"""

from __future__ import annotations

import html
import re
from pathlib import Path


RAW_DIR = Path("documents")
CLEAN_DIR = Path("cleaned_documents")

BOILERPLATE_LINES = {
    "upvote",
    "downvote",
    "reply",
    "award",
    "share",
    "thumbs up",
    "thumbs down",
    "helpful",
    "first to review",
}

BOILERPLATE_PATTERNS = [
    re.compile(r"^\d+\s*(upvotes?|downvotes?|comments?|photos?)$", re.I),
    re.compile(r"^u/[A-Za-z0-9_-]+\s+avatar$", re.I),
    re.compile(r"^\[deleted\]$", re.I),
    re.compile(r"^comment deleted by user$", re.I),
    re.compile(r"^edited\s+\d+\w*\s+ago$", re.I),
    re.compile(r"^\d+\w*\s+ago$", re.I),
    re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}$"),
    re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}$"),
]


def load_documents(raw_dir: Path = RAW_DIR) -> list[tuple[Path, str]]:
    """Return all non-empty .txt documents from the raw documents folder."""
    docs: list[tuple[Path, str]] = []
    for path in sorted(raw_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        if text.strip():
            docs.append((path, text))
    return docs


def is_boilerplate_line(line: str) -> bool:
    normalized = line.strip().lower()
    if not normalized:
        return False
    if normalized in BOILERPLATE_LINES:
        return True
    return any(pattern.match(line.strip()) for pattern in BOILERPLATE_PATTERNS)


def clean_text(raw_text: str) -> str:
    """Remove webpage/comment UI clutter while preserving source wording."""
    text = html.unescape(raw_text)
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2022", "")
    text = text.replace("\ufeff", "")

    # Remove any accidental HTML tags from copied pages.
    text = re.sub(r"<[^>]+>", " ", text)

    cleaned_lines: list[str] = []
    previous_blank = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        line = re.sub(r"\s+", " ", line)

        if is_boilerplate_line(line):
            continue

        if not line:
            if cleaned_lines and not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    cleaned = "\n".join(cleaned_lines).strip()

    # Collapse excessive blank space but keep paragraph breaks.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned + "\n"


def write_cleaned_documents(
    docs: list[tuple[Path, str]],
    clean_dir: Path = CLEAN_DIR,
) -> list[Path]:
    clean_dir.mkdir(exist_ok=True)
    output_paths: list[Path] = []

    for source_path, raw_text in docs:
        cleaned_text = clean_text(raw_text)
        output_path = clean_dir / source_path.name
        output_path.write_text(cleaned_text, encoding="utf-8")
        output_paths.append(output_path)

    return output_paths


def main() -> None:
    docs = load_documents()
    output_paths = write_cleaned_documents(docs)

    print(f"Loaded {len(docs)} raw documents from {RAW_DIR}/")
    print(f"Wrote {len(output_paths)} cleaned documents to {CLEAN_DIR}/")

    if output_paths:
        sample_path = output_paths[0]
        print("\n--- Sample cleaned document ---")
        print(f"File: {sample_path}")
        print(sample_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
