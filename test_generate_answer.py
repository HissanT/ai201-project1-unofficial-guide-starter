"""Tests for grounded prompting and deterministic source attribution."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from embed_retrieve import RetrievalResult
from generate_answer import (
    INSUFFICIENT_INFORMATION_RESPONSE,
    SYSTEM_PROMPT,
    build_messages,
    cited_sources,
    format_inline_citations,
    format_sources,
    generate_grounded_answer,
)


def retrieval_result(
    chunk_id: str,
    text: str,
    source_file: str = "source-a.txt",
    source_title: str = "Source A",
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=text,
        source_file=source_file,
        source_title=source_title,
        source_type="Reddit thread",
        url=f"https://example.com/{source_file}",
        chunk_position=1,
        distance=0.2,
    )


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = {}

    def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content="The source reports a cost gap. [Source 1]")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeGroqClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class GenerateAnswerTests(unittest.TestCase):
    def test_prompt_requires_context_only_and_labels_sources(self) -> None:
        chunks = [
            retrieval_result("a-1", "First excerpt"),
            retrieval_result("a-2", "Second excerpt"),
            retrieval_result("b-1", "Third excerpt", "source-b.txt", "Source B"),
        ]

        messages, sources = build_messages("What happened?", chunks)

        self.assertIn("Use only", SYSTEM_PROMPT)
        self.assertIn(INSUFFICIENT_INFORMATION_RESPONSE, SYSTEM_PROMPT)
        self.assertIn('label="Source 1"', messages[1]["content"])
        self.assertIn('label="Source 2"', messages[1]["content"])
        self.assertEqual(len(sources), 2)

    def test_generation_uses_zero_temperature_and_cited_source(self) -> None:
        chunks = [
            retrieval_result("a-1", "A student reports a cost gap."),
            retrieval_result("b-1", "Other text.", "source-b.txt", "Source B"),
        ]
        client = FakeGroqClient()

        result = generate_grounded_answer(
            "Is it affordable?",
            top_k=5,
            retriever=lambda question, top_k: chunks,
            groq_client=client,
        )

        self.assertEqual(
            result.answer,
            "The source reports a cost gap. [Source A]",
        )
        self.assertEqual([source.title for source in result.sources], ["Source A"])
        self.assertEqual(client.completions.kwargs["temperature"], 0.0)
        self.assertIn("Source A", format_sources(result.sources))

    def test_no_retrieval_results_skips_llm(self) -> None:
        result = generate_grounded_answer(
            "Unknown question",
            retriever=lambda question, top_k: [],
        )

        self.assertEqual(result.answer, INSUFFICIENT_INFORMATION_RESPONSE)
        self.assertEqual(result.sources, ())

    def test_insufficient_answer_has_no_attributed_sources(self) -> None:
        sources = build_messages(
            "Unknown question",
            [retrieval_result("a-1", "Unrelated excerpt")],
        )[1]

        self.assertEqual(
            cited_sources(INSUFFICIENT_INFORMATION_RESPONSE, sources),
            (),
        )

    def test_inline_citations_use_titles_and_cap_repetition(self) -> None:
        sources = build_messages(
            "Compare them",
            [
                retrieval_result("a-1", "First excerpt"),
                retrieval_result("b-1", "Second excerpt", "source-b.txt", "Source B"),
            ],
        )[1]
        answer = (
            "First claim [Source 1]. Second claim [Source 1]. "
            "Third claim [Source 1]. Comparison [Source 1, Source 2]."
        )

        self.assertEqual(
            format_inline_citations(answer, sources),
            (
                "First claim [Source A]. Second claim [Source A]. "
                "Third claim. Comparison [Source B]."
            ),
        )


if __name__ == "__main__":
    unittest.main()
