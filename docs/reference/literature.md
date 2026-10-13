# Literaturbasis

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).


Alle Quellen sind im Exposé zitiert; die BibTeX-Einträge liegen im privaten PaperLab-Repo unter `expose/latex/main.bib` im Ordner der Bachelorarbeit. APA 7 / biblatex / biber.

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
