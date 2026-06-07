# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Embedding and Retrieval Usage

Build or rebuild the persistent ChromaDB collection from `chunks.jsonl`:

```bash
python embed_retrieve.py index
```

Retrieve the five most relevant chunks with source attribution:

```bash
python embed_retrieve.py query "What do students say about Galesburg?"
```

Use `--top-k` to tune the result count during evaluation.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

 This project focuses on student-generated knowledge about Knox College, including professor reviews, computer science
  experiences, financial aid concerns, campus employment, Galesburg, and overall student life. This information is
  valuable because official college websites usually describe programs, costs, and campus life in polished marketing
  language, but they do not capture what students and alumni actually experienced. The useful details are scattered
  across Reddit threads, Rate My Professor reviews, and Yelp comments, making them hard to search in one place. The
  Unofficial Guide brings those informal sources together so users can ask plain-language questions and get grounded
  answers with citations.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Thread about honest opinions about Knox | Reddit Thread | https://www.reddit.com/r/KnoxCollege/comments/1atsaen/honest_opinion/ |
| 2 | Rate My Professor about Shengting Cao| RateMyProfessor review | https://www.ratemyprofessors.com/professor/3136006 |
| 3 | Rate My Professor about Jaime Spacco| RateMyProfessor review | https://www.ratemyprofessors.com/professor/1988553 |
| 4 | Rate My Professor about Andrew Leahy| RateMyProfessor review | https://www.ratemyprofessors.com/professor/230966 |
| 5 | Rate My Professor about Ole Forsberg| RateMyProfessor review | https://www.ratemyprofessors.com/professor/2676607 |
| 6 | Rate My Professor about David Bunde| RateMyProfessor review | https://www.ratemyprofessors.com/professor/1090694 |
| 7 | Thread about getting into Knox | Reddit Thread | https://www.reddit.com/r/KnoxCollege/comments/18zyrl8/what_do_u_think/ |
| 8 | Thread about whether I should commit to Knox | Reddit Thread | https://www.reddit.com/r/KnoxCollege/comments/1b4x1mi/please_help/ |
| 9 | Thread about location and college | Reddit Thread | https://www.reddit.com/r/illinois/comments/1qh4cy9/knox_college_in_galesburg/ |
| 10 | Article on how is Knox | Yelp reviews | https://www.yelp.com/biz/knox-college-galesburg |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

`all-MiniLM-L6-v2` from `sentence-transformers`. It runs locally without an
API key and provides a practical balance of semantic retrieval quality, model
size, and latency for short English student reviews and comments.

**Production tradeoff reflection:**

For a production system, I would compare stronger local and hosted models on
retrieval accuracy for informal language, latency, context length, multilingual
coverage, privacy, and operating cost. This corpus is mostly short English
text, so accuracy on slang and college-specific language matters more than a
very large context window.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
