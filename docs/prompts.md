# Prompt Templates

These prompts are held **constant** across all chunking strategies (D6).
Any change here invalidates comparability between strategy runs.

---

## System Prompt

```
You are a helpful assistant that answers questions about Vue.js based solely on
the provided documentation excerpts.
Do not use any knowledge outside the provided context.
If the context does not contain sufficient information to answer the question,
state that explicitly.
```

---

## User Prompt Template

```
Answer the following question based exclusively on the documentation excerpts below.

Question: {question}

Documentation excerpts:
{context}

Answer:
```

Where `{context}` is the concatenation of the top-k retrieved chunks, separated by:
```
---
```
Each chunk is prefixed with `[Excerpt N]`.

---

## Parameters (constant, from `src/config.py`)

| Parameter | Value |
|-----------|-------|
| `LLM_MODEL` | see config.py (pinned at implementation time) |
| `LLM_TEMPERATURE` | 0.0 |
| `LLM_MAX_TOKENS` | 1024 |
| `TOP_K` | 5 |

---

## Design rationale

- No chain-of-thought or few-shot examples: keeps the prompt minimal and reduces
  confounds from prompt engineering effects on answer quality.
- The model is instructed to decline answering if context is insufficient,
  which supports hallucination-freedom scoring (rubric criterion 4).
- The system prompt explicitly bounds the model to the provided context,
  ensuring that differences in answer quality can be attributed to the retrieved
  chunks (and thus to the chunking strategy) rather than to parametric knowledge.
