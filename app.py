"""Gradio interface for The Unofficial Guide."""

from __future__ import annotations

from generate_answer import (
    format_retrieved_chunks,
    format_sources,
    generate_grounded_answer,
)


def answer_for_interface(question: str, top_k: int) -> tuple[str, str, str]:
    """Return answer, sources, and exact retrieval details for Gradio."""
    if not question.strip():
        return "Enter a question first.", "", ""

    try:
        result = generate_grounded_answer(question, top_k=int(top_k))
    except Exception as exc:
        return f"Error: {exc}", "", ""

    return (
        result.answer,
        format_sources(result.sources),
        format_retrieved_chunks(result.retrieved_chunks),
    )


def clear_interface() -> tuple[str, str, str, str]:
    return "", "", "", ""


def build_app():
    import gradio as gr

    with gr.Blocks(title="The Unofficial Guide to Knox College") as demo:
        gr.Markdown(
            """
            # The Unofficial Guide to Knox College
            Ask questions grounded in collected student and alumni sources.
            The answer is generated only from the retrieved excerpts shown below.
            """
        )

        question = gr.Textbox(
            label="Question",
            placeholder="What do students say about Knox's CS program?",
            lines=2,
        )
        top_k = gr.Slider(
            minimum=1,
            maximum=10,
            value=5,
            step=1,
            label="Number of chunks to retrieve",
        )

        with gr.Row():
            submit = gr.Button("Ask", variant="primary")
            clear = gr.Button("Clear")

        answer = gr.Markdown()
        sources = gr.Markdown()
        retrieved = gr.Markdown()

        submit.click(
            fn=answer_for_interface,
            inputs=[question, top_k],
            outputs=[answer, sources, retrieved],
        )
        question.submit(
            fn=answer_for_interface,
            inputs=[question, top_k],
            outputs=[answer, sources, retrieved],
        )
        clear.click(
            fn=clear_interface,
            outputs=[question, answer, sources, retrieved],
        )

        gr.Examples(
            examples=[
                [
                    "If an international student has about a $15,000 EFC, "
                    "would Knox be affordable without extra work?"
                ],
                ["What do students and alumni say about living in Galesburg?"],
                ["How do students describe Jaime Spacco's teaching?"],
            ],
            inputs=[question],
        )

    return demo


if __name__ == "__main__":
    build_app().launch()
