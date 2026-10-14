# Prompt-Vorlagen

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026; die Vorlagen werden mit `generate.py` umgesetzt. Übersicht: [Dokumentation](../README.md).

Die Prompts sind für alle Chunking-Strategien gleich ([ADR 0006](../adr/0006-nur-chunking-variiert.md)); jede Änderung
macht die Läufe der Strategien unvergleichbar. Die Vorlagen sind Englisch, weil Korpus und Fragen Englisch sind.
Warum die Prompts so knapp sind: [Forschungsdesign](../explanation/research-design.md#prompt-gestaltung).

## System-Prompt

```
You are a helpful assistant that answers questions about Vue.js based solely on
the provided documentation excerpts.
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

`{context}` ist die Verkettung der top-k gefundenen Chunks, getrennt durch eine Zeile `---`; jeder Chunk beginnt mit
`[Excerpt N]`.

## Parameter

Konstant für alle Strategien: `LLM_MODEL` (noch Platzhalter, [ADR 0016](../adr/0016-modell-neutralitaet.md)),
`LLM_TEMPERATURE` und `TOP_K` ([ADR 0014](../adr/0014-temperatur-und-topk.md)), `LLM_MAX_TOKENS`. Werte:
[Konfiguration](configuration.md#llm-und-embedding).
