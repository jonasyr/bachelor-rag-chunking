# Prompt-Vorlagen

> Seitentyp: Nachschlagen (reference). Stand: 17.10.2026; umgesetzt in `src/prompt.py`, die Texte stehen in `src/config.py` (ein Test vergleicht sie mit dieser Seite). Übersicht: [Dokumentation](../README.md).

Die Prompts sind für alle Chunking-Strategien gleich ([ADR 0006](../adr/0006-nur-chunking-variiert.md)); jede Änderung
macht die Läufe der Strategien unvergleichbar. Die Vorlagen sind Englisch, weil Korpus und Fragen Englisch sind.
Warum die Prompts so knapp sind: [Forschungsdesign](../explanation/research-design.md#prompt-gestaltung).

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
([ADR 0038](../adr/0038-korpus-e2e.md), [ADR 0040](../adr/0040-closed-book-pruefung.md)). Der RAG-Prompt ohne
Kontext ließe das Modell nur ablehnen; dieser Prompt ist derselbe ohne Ausschnitte und ohne die Bindung an sie.

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

Konstant für alle Strategien, die Closed-Book-Prüfung und K0: `LLM_MODEL`, `LLM_REASONING_EFFORT`, `LLM_SEED` ([ADR 0033](../adr/0033-antwortmodell.md)),
`LLM_TEMPERATURE` und `TOP_K` ([ADR 0014](../adr/0014-temperatur-und-topk.md)), `LLM_MAX_TOKENS`. Werte:
[Konfiguration](configuration.md#llm-und-embedding).
