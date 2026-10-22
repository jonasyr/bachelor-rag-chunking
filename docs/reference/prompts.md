# Prompt-Vorlagen

*[Doku-Index](../README.md) · Referenz · Verwandt: [Konfiguration](configuration.md#llm-und-embedding), [Forschungsdesign](../explanation/research-design.md#prompt-gestaltung), [Evaluation](evaluation.md)*

Stand: 22.10.2026. Umgesetzt in `src/prompt.py`, die Texte stehen in `src/config.py`; zwei Tests
(`tests/test_prompt.py`) vergleichen sie mit den ersten vier Codeblöcken dieser Seite in ihrer Reihenfolge, also keinen
Codeblock davor einfügen.

Die Prompts sind für alle Chunking-Strategien gleich ([ADR 0006](../adr/0006-nur-chunking-variiert.md)); jede Änderung
macht die Läufe der Strategien unvergleichbar. Die Vorlagen sind Englisch, weil Korpus und Fragen Englisch sind.
Warum die Prompts so knapp sind: [Forschungsdesign](../explanation/research-design.md#prompt-gestaltung). Die
Prompts des RAGAS-Richters sind die von RAGAS 0.4.3 und gehören nicht zum konstanten Prompt des Experiments
([Evaluation](evaluation.md#triangulation)).

## System-Prompt

```
You are a helpful assistant that answers questions about the e2e testing framework
based solely on the provided documentation excerpts.
Do not use any knowledge outside the provided context.
If the context does not contain sufficient information to answer the question,
state that explicitly.
```

## Vorlage für die Nutzernachricht

```
Answer the following question based exclusively on the documentation excerpts below.

Question: {question}

Documentation excerpts:
{context}

Answer:
```

`{context}` ist die Verkettung der top-k gefundenen Chunks in Rangfolge, getrennt durch eine Zeile `---`; jeder Chunk
beginnt mit `[Excerpt N]`. Geschweifte Klammern in Frage oder Chunk bleiben unverändert.

## Closed-Book-Prompt (Prüfung und K0)

Ohne Ausschnitte beantwortet das Antwortmodell jede Katalogfrage bei der Closed-Book-Prüfung und in der Kontrolle K0
([ADR 0038](../adr/0038-korpus-e2e.md), [ADR 0040](../adr/0040-closed-book-pruefung.md)). Er entspricht dem
RAG-Prompt ohne Ausschnitte und ohne die Bindung an sie; die Ablehnungsregel bezieht sich auf das eigene Wissen. Warum
ein eigener Prompt: [Forschungsdesign](../explanation/research-design.md#warum-closed-book-prüfung-und-k0).

```
You are a helpful assistant that answers questions about the e2e testing framework.
If you do not know the answer, state that explicitly.
```

```
Answer the following question.

Question: {question}

Answer:
```

## Parameter

Konstant für alle Strategien, die Closed-Book-Prüfung und K0: `LLM_MODEL`, `LLM_REASONING_EFFORT`, `LLM_SEED`,
`LLM_MAX_TOKENS` ([ADR 0033](../adr/0033-antwortmodell.md)) und `LLM_TEMPERATURE`
([ADR 0014](../adr/0014-temperatur-und-topk.md)). Nur für den RAG-Prompt außerdem `TOP_K` (Zahl der Auszüge, ADR 0014);
der Closed-Book-Prompt enthält keine Auszüge. Werte: [Konfiguration](configuration.md#llm-und-embedding),
`TOP_K` unter [Retrieval](configuration.md#retrieval).
