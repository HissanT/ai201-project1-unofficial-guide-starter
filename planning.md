# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

 This project focuses on student-generated knowledge about Knox College, including professor reviews, computer science
  experiences, financial aid concerns, campus employment, Galesburg, and overall student life. This information is
  valuable because official college websites usually describe programs, costs, and campus life in polished marketing
  language, but they do not capture what students and alumni actually experienced. The useful details are scattered
  across Reddit threads, Rate My Professor reviews, and Yelp comments, making them hard to search in one place. The
  Unofficial Guide brings those informal sources together so users can ask plain-language questions and get grounded
  answers with citations.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** One review or comment paragraph per chunk, targeting about 400 characters. Longer comments will be
  split by paragraph if they exceed that range.

**Overlap:** Around 50 characters for shorter reviews or comments. Around 100 characters of overlap only when splitting
  longer comments.

**Reasoning:** My corpus is mostly short student reviews, Reddit comments, and Yelp review paragraphs, where each
  chunk usually contains one focused opinion or experience. 400 character should keep the retrievel precise for most questions. I will still split on natural boundaries so the chunking strategy preserves meaning instead of cutting every fixed number of characters. One important note is to not make every chunk exactly 300-500 characters. Use that as a target/limit. If a professor review is 220 characters but complete, keep it whole. If a Reddit bullet is 650 characters but still one coherent idea, either keep it or split at a sentence boundary.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2

**Top-k:** top-3

**Production tradeoff reflection:**  If cost was not a constraint, I would compare embedding models based on accuracy, context length. Accuracy would matter most because my documents are informal student opinions with slang, short reviews, and college-specific details, so the model needs to match questions to meaning rather than exact keywords. Context length would matter for longer Reddit or Yelp comments, but most of my chunks are short, so it would be less important than retrieval quality.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | If an international student has about a $15,000 EFC, would Knox be affordable without extra work? | Not fully. Several people put costs at around $17,000 to $21,000.|
| 2 | Is Knox’s CS program described more as a strong technical/pre-professional program or as part of a broader liberal arts experience?| More as part of a broader liberal arts experience. Some CS alumni report good outcomes, internships, and software jobs, but others say the CS department is only fine or lacks innovation. The stronger theme is that Knox teaches critical thinking, learning how to learn, and interdisciplinary exposure.|
| 3 |  What kind of paid work do you think is realistic for a first-year international student at Knox? |  normal on-campus jobs are more realistic than major-related internships after the first year. One estimate mentions around 10-15 hours per week at Illinois minimum wage, while summer or research work may be possible but not guaranteed.|
| 4 | Do student/alumni sources describe Galesburg as a major advantage, major drawback, or mixed factor for Knox| Mixed, but often a drawback depending on the student. Some describe Galesburg as boring, small, or rough, while others say it has useful stores, restaurants, Amtrak access, and areal small-town community. Most sources frame campus as the center of student life rather than Galesburg itself|
| 5 | Which professor appears more consistently helpful for CS students: Jaime Spacco or David Bunde, and what is the difference in how students describe them? | Both are described as helpful, but in different ways. Spacco is described as engaging, caring, inspirational, and sometimes disorganized, with easier or less structured classes. Bunde is described as helpful, practical, knowledgeable, and strong for labs/projects, though sometimes busy|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Less information available so a lot of concerns could be left unanswered or the answers may not be related.

2. Chunk seperation could lead to unrelated information leaking through.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

documents/*.txt
     |
     v
[Document Ingestion]
Python file reader + basic text cleanup
     |
     v
[Chunking]
Custom review/comment chunk_text()
     |
     v
[Embedding + Vector Store]
sentence-transformers: all-MiniLM-L6-v2
ChromaDB collection
     |
     v
[Retrieval]
ChromaDB similarity search, top-3 chunks
     |
     v
[Generation]
Groq LLM API, grounded answer with source citations

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
