# Literaturbasis

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).


Die 15 Quellen der ersten Tabelle ([ADR 0018](../adr/0018-literaturbasis.md)) sind im Exposé zitiert; nur ihre BibTeX-Einträge liegen im privaten PaperLab-Repo unter `expose/latex/main.bib` im Ordner der Bachelorarbeit. Die Webquellen der folgenden Abschnitte sind dort noch nicht enthalten. Zitierstil: APA 7 / biblatex / biber ([ADR 0002](../adr/0002-zitierstil-apa.md)).

| BibTeX-Key | Rolle in der Argumentation | Typ |
|------------|----------------------------|-----|
| `lewis2020rag` | RAG-Grundlagenpaper | NeurIPS |
| `gao2023ragsurvey` | RAG-Survey, Pipeline-Komponenten | Preprint |
| `yu2025ragevalsurvey` | Evaluation auf Komponentenebene | Springer |
| `es2024ragas` | RAGAS, sekundäre automatisierte Evaluation | EACL-Demo |
| `karpukhin2020dpr` | Dense Retrieval | EMNLP |
| `manning2008ir` | IR-Metriken: Precision, Recall, MRR | Buch |
| `reimers2019sbert` | Satz-Embeddings / semantische Ähnlichkeit | EMNLP-IJCNLP |
| `devlin2019bert` | Kontextuelle Repräsentationen (Transformer) | NAACL |
| `hladena2025chunksize` | Einfluss der Chunk-Größe | Springer |
| `jimenoyepes2024chunking` | strukturbasiertes/element-basiertes Chunking | Preprint |
| `finardi2024chronicles` | Retriever/Chunk/Generator als Einheit | Preprint |
| `ji2023hallucination` | Halluzinationen in NLG | ACM CSUR |
| `taiwo2026chunking` | Chunking-Vergleich (Öl & Gas) – domänenfremde Lücke | Preprint |
| `gomezcabello2025chunking` | Chunking-Vergleich (klinisch) – domänenfremde Lücke | Bioengineering |
| `qu2025semanticchunking` | semantisch/struktur ≠ konsistent besser → starke Baseline, „nicht trivial" | NAACL Findings |

> Nicht zitierfähig, aber in „Verwandte Arbeiten" zu erwähnen: der Praktiker-Blogbeitrag (Mai 2026) mit nahezu identischem Setup auf FastAPI/Supabase/Stripe.

## Technische Quellen (Web)

Abgerufen am 13.10.2026; Grundlage von [ADR 0023](../adr/0023-embedding-modell.md) und
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md). Für die Arbeit als APA-7-Webquellen in die BibTeX-Datei
(PaperLab) übernehmen.

| Kurzname | Quelle (APA 7) | Belegt |
|----------|----------------|--------|
| `openai2024embeddingmodels` | OpenAI. (2024, 25. Januar). *New embedding models and API updates*. https://openai.com/index/new-embedding-models-and-api-updates/ | Einführung von `text-embedding-3-small/-large` |
| `openai2026embeddingsguide` | OpenAI. (o. J.). *Vector embeddings* [Leitfaden]. https://developers.openai.com/api/docs/guides/embeddings | MTEB 64,6 % / 62,3 %, max. 8.192 Tokens, `cl100k_base`, Normierung auf Länge 1, Kosinus, Dimensionen |
| `openai2026te3large` | OpenAI. (o. J.). *text-embedding-3-large* [Modellseite]. https://developers.openai.com/api/docs/models/text-embedding-3-large | Preis 0,13 USD je 1 Mio. Tokens, Snapshot nur als Alias |
| `openai2026embeddingsapi` | OpenAI. (o. J.). *Create embeddings* [API-Referenz]. https://developers.openai.com/api/reference/resources/embeddings/methods/create | ≤ 2.048 Eingaben und ≤ 300.000 Tokens je Anfrage, `usage.prompt_tokens` |
| `chroma2026configure` | Chroma. (o. J.). *Configure collections*. https://docs.trychroma.com/docs/collections/configure | HNSW ist approximativ; Standard `l2`, `ef_search` = 100 |

Abgerufen am 14.10.2026; Grundlage von [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) und
[ADR 0026](../adr/0026-c3-vergleichbarkeit.md) (dort auch die Begründung der C3-Obergrenze aus
[ADR 0021](../adr/0021-c3-grenzen.md)).

| Kurzname | Quelle (APA 7) | Belegt |
|----------|----------------|--------|
| `smith2024chunking` | Smith, B., & Troynikov, A. (2024, 3. Juli). *Evaluating chunking strategies for retrieval*. Chroma. https://www.trychroma.com/research/evaluating-chunking | `text-embedding-3-large`, fünf abgerufene Chunks; kleinere Chunks (800 → 200 Tokens) erhöhen die Precision deutlich bei etwa gleichem Recall (rund 85–89 %) |
| `bhat2025chunksize` | Bhat, S. R., Rudat, M., Spiekermann, J., & Flores-Herr, N. (2025). *Rethinking chunk size for long-document retrieval: A multi-dataset analysis* (arXiv:2505.21700). https://arxiv.org/abs/2505.21700 | beste Chunk-Größe hängt vom Datensatz und Fragetyp ab (64–128 Tokens für knappe Fakten, 512–1.024 für breiten Kontext) und vom Embedding-Modell |
| `vuejs2026compare` | vuejs/docs. (2026). *Compare b75d188…40aa88a* [GitHub-Vergleich]. https://github.com/vuejs/docs/compare/b75d188ab16bf83bd1f364a77dfd2315be8f3fa4...40aa88af0094f7bab4aaf786e55c748a6a251d88 | acht Commits, im Ausschnitt sechs geänderte Guide-Dateien |

Abgerufen am 17.10.2026; Grundlage von [ADR 0033](../adr/0033-antwortmodell.md).

| Kurzname | Quelle (APA 7) | Belegt |
|----------|----------------|--------|
| `openai2026gpt6luna` | OpenAI. (o. J.). *GPT-6 Luna* [Modellseite]. https://developers.openai.com/api/docs/models/gpt-6-luna | 0,10/0,50 USD je 1 Mio. Ein-/Ausgabe-Tokens, Wissensstand 18.05.2026, Effort `none` bis `max`, nur Alias |
| `openai2026latestmodel` | OpenAI. (o. J.). *Using GPT-6* [Leitfaden]. https://developers.openai.com/api/docs/guides/latest-model | `temperature` nur bei Effort `none`; `none` nur bei GPT-6 Sol und GPT-6 Luna |
| `openai2026reasoning` | OpenAI. (o. J.). *Reasoning models* [Leitfaden]. https://developers.openai.com/api/docs/guides/reasoning | Effort-Stufen, Parameter bei Reasoning |
| `openai2026deprecations` | OpenAI. (o. J.). *Deprecations*. https://developers.openai.com/api/docs/deprecations | GPT-4.1/4o-Snapshots bis 14.01.2027, GPT-5-Snapshots bis 11.12.2026 |
| `renze2024temperature` | Renze, M., & Guven, E. (2024). The effect of sampling temperature on problem solving in large language models. In *Findings of the Association for Computational Linguistics: EMNLP 2024*. https://arxiv.org/abs/2402.05201 | keine signifikante Wirkung der Temperatur 0,0–1,0 auf die Lösungsgüte |
| `atil2024nondeterminism` | Atil, B., et al. (2024). *Non-determinism of "deterministic" LLM settings* (arXiv:2408.04667). https://arxiv.org/abs/2408.04667 | Genauigkeitsschwankungen bis 15 % trotz „deterministischer“ Einstellungen |
| `lee2026noisybench` | Lee, S., et al. (2026). *Lost in the noise: How test-time reasoning fails with contextual distractors* (arXiv:2601.07226). https://arxiv.org/abs/2601.07226 | Reasoning-Modelle brechen mit störenden Passagen ebenfalls ein; nur Abstract geprüft, vor dem Zitieren Volltext lesen |
