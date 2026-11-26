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

## Prompt der LLM-Gegenprobe

Die LLM-Gegenprobe ([ADR 0046, Nachtrag 17.11.2026](../adr/0046-zweitbewertung.md#nachtrag-17112026-ersatzverfahren-ausgelöst))
lässt `config.LLM_RATER_MODEL` je Antwort die Prüffragen der Rubrik beantworten ([Evaluation](evaluation.md#zweitbewertung)).
Sie gehört nicht zum konstanten Prompt des Experiments: Das Modell sieht weder Code noch Strategie. Der System-Prompt
setzt sich aus dem Wortlaut der App zusammen (`config.RUBRIC_CHECK_QUESTIONS`, `RUBRIC_POINT_HELP`,
`RUBRIC_CHECK_HELP`); hier steht er zusammengesetzt (`config.LLM_RATER_SYSTEM_PROMPT`). Die Antwort ist JSON nach
einem strikten Schema (Optionen aus `scoring_rules.CHECKS`, ein Wert je Kernpunkt, zuletzt eine kurze Begründung
`reason`, die nur im Journal bleibt).

```
You score one answer of a RAG system against fixed checks. Answer only from the question, the reference answer, the key points and the excerpts shown.

Answer every check with one of its options:
- declines: Does the answer say the excerpts do not contain the answer, and give none? No when it gives part of the answer and says the rest is not covered (K0: unknown): the missing parts count as missing key points.
- points: one mark per key point, in their order (point 1 is the core point). Covered: the same meaning, also in other words. A qualifier in brackets, such as a version, is not required. Stated only partly: missing.
- core_wrong: Does it state the core point wrongly or contradict it?
- other_error: Is any other statement factually wrong?
- grounded: How many of its statements are backed by the excerpts? A true statement that the excerpts do not back counts as not backed.
- hallucination: Does it contain anything that neither the excerpts nor the reference cover? Counts also when the addition is true (minor if it does not change the answer). An illustrative example name is not a hallucination.
- answers_question: Does it address what was asked?
- direct: Does the core point come in the first two sentences? Yes when the answer's own core point comes in the first two sentences, even if it is wrong (that counts under the facts checks) or a second part of the question is answered later.
- wordy: Is it repetitive, padded or confusing?
- reason: one or two short sentences on the decisive checks.

If declines is yes, the key points and the checks core_wrong, other_error, grounded and hallucination are not asked: mark every key point missing and answer no, no, all, none.
```

Nutzernachricht (`config.LLM_RATER_USER_TEMPLATE`); `{key_points}` sind Zeilen nach `config.LLM_RATER_POINT_TEMPLATE`
(`{n}. {text}`), `{excerpts}` die Auszüge des Items in Rangfolge nach `config.LLM_RATER_EXCERPT_TEMPLATE` (`### Excerpt {n}`, dann
der Text), getrennt durch eine Leerzeile:

```
## Question
{question}

## Reference answer
{reference_answer}

## Key points
{key_points}

## Excerpts
{excerpts}

## Answer
{answer}
```

### Gegenprobe über K0

Mit `--control` ([ADR 0051](../adr/0051-hybride-bewertung.md)) bewertet dasselbe Modell die K0-Antworten, die ohne
Auszüge entstanden sind: ohne `grounded`, mit dem K0-Wortlaut von `declines` und `hallucination`
(`config.RUBRIC_CONTROL_QUESTIONS`), Schema aus `scoring_rules.CONTROL_CHECKS` (`config.LLM_RATER_CONTROL_SYSTEM_PROMPT`):

```
You score one answer of a language model given without any excerpts against fixed checks. Answer only from the question, the reference answer and the key points shown.

Answer every check with one of its options:
- declines: Does the answer say it does not know the answer, and give none? No when it gives part of the answer and says the rest is not covered (K0: unknown): the missing parts count as missing key points.
- points: one mark per key point, in their order (point 1 is the core point). Covered: the same meaning, also in other words. A qualifier in brackets, such as a version, is not required. Stated only partly: missing.
- core_wrong: Does it state the core point wrongly or contradict it?
- other_error: Is any other statement factually wrong?
- hallucination: Does it contain anything the reference does not cover? Counts also when the addition is true (minor if it does not change the answer). An illustrative example name is not a hallucination.
- answers_question: Does it address what was asked?
- direct: Does the core point come in the first two sentences? Yes when the answer's own core point comes in the first two sentences, even if it is wrong (that counts under the facts checks) or a second part of the question is answered later.
- wordy: Is it repetitive, padded or confusing?
- reason: one or two short sentences on the decisive checks.

If declines is yes, the key points and the checks core_wrong, other_error and hallucination are not asked: mark every key point missing and answer no, no, none.
```

Nutzernachricht (`config.LLM_RATER_CONTROL_USER_TEMPLATE`), wie oben, aber ohne Auszüge:

```
## Question
{question}

## Reference answer
{reference_answer}

## Key points
{key_points}

## Answer
{answer}
```

## Parameter

Konstant für alle Strategien, die Closed-Book-Prüfung und K0: `LLM_MODEL`, `LLM_REASONING_EFFORT`, `LLM_SEED`,
`LLM_MAX_TOKENS` ([ADR 0033](../adr/0033-antwortmodell.md)) und `LLM_TEMPERATURE`
([ADR 0014](../adr/0014-temperatur-und-topk.md)). Nur für den RAG-Prompt außerdem `TOP_K` (Zahl der Auszüge, ADR 0014);
der Closed-Book-Prompt enthält keine Auszüge. Werte: [Konfiguration](configuration.md#llm-und-embedding),
`TOP_K` unter [Retrieval](configuration.md#retrieval).
