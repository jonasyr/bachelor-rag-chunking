# Literaturbasis

*[Doku-Index](../README.md) · Referenz · Verwandt: [Forschungsdesign](../explanation/research-design.md), [ADR 0018](../adr/0018-literaturbasis.md), [ADR 0002](../adr/0002-zitierstil-apa.md)*

Alle Quellen der Arbeit mit ihrer Rolle, Stand 26.10.2026. Maßgeblich für die bibliografischen Angaben ist die
`main.bib` der Bachelorarbeit im privaten PaperLab-Repo (am 22.10.2026 gegen Crossref, arXiv, ACL Anthology und die
Webseiten geprüft, einzelne Angaben am Volltext: Renze und Guven, Lee et al., Taiwo und Amaluddin Yusoff); diese Seite spiegelt sie für Leser des öffentlichen Repos. Das Exposé-Bib (`expose/latex/main.bib`)
ist eingefroren und enthält noch ältere Angaben (etwa die Autorenreihenfolge von Qu et al.). Zitierstil: APA 7 /
biblatex / biber ([ADR 0002](../adr/0002-zitierstil-apa.md)).

Jede Tabelle hat dieselben Spalten: BibTeX-Key, Quelle (APA 7, gekürzt) und was die Quelle in der Arbeit belegt.

## Kernquellen

Die 15 im Exposé zitierten Quellen ([ADR 0018](../adr/0018-literaturbasis.md)) und eine am 22.10.2026 ergänzte, am 26.10.2026
am Volltext geprüfte Domänenstudie (Pesl et al.).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `lewis2020rag` | Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In *Advances in Neural Information Processing Systems 33* (S. 9459–9474). Curran Associates. | RAG-Grundlagenpaper |
| `gao2023ragsurvey` | Gao, Y., et al. (2023). *Retrieval-augmented generation for large language models: A survey* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2312.10997 | RAG-Survey, Pipeline-Komponenten |
| `yu2025ragevalsurvey` | Yu, H., et al. (2025). Evaluation of retrieval-augmented generation: A survey. In *Big data (BigData 2024)* (CCIS 2301, S. 102–120). Springer. https://doi.org/10.1007/978-981-96-1024-2_8 | Evaluation auf Komponentenebene |
| `es2024ragas` | Es, S., James, J., Espinosa Anke, L., & Schockaert, S. (2024). RAGAs: Automated evaluation of retrieval augmented generation. In *Proceedings of EACL 2024: System Demonstrations* (S. 150–158). https://doi.org/10.18653/v1/2024.eacl-demo.16 | RAGAS, sekundäre automatisierte Evaluation ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) |
| `karpukhin2020dpr` | Karpukhin, V., et al. (2020). Dense passage retrieval for open-domain question answering. In *Proceedings of EMNLP 2020* (S. 6769–6781). https://doi.org/10.18653/v1/2020.emnlp-main.550 | Dense Retrieval |
| `manning2008ir` | Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to information retrieval*. Cambridge University Press. https://doi.org/10.1017/CBO9780511809071 | IR-Metriken: Precision, Recall, MRR |
| `reimers2019sbert` | Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of EMNLP-IJCNLP 2019* (S. 3982–3992). https://doi.org/10.18653/v1/D19-1410 | Satz-Embeddings, semantische Ähnlichkeit |
| `devlin2019bert` | Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of NAACL-HLT 2019* (S. 4171–4186). https://doi.org/10.18653/v1/N19-1423 | Kontextuelle Repräsentationen (Transformer) |
| `hladena2025chunksize` | Hladěna, J., et al. (2025). The effect of chunk size on the RAG performance. In *Software engineering: Emerging trends and practices in system development (CSOC 2025)* (LNNS 1559, S. 317–326). Springer. https://doi.org/10.1007/978-3-032-00712-4_21 | Einfluss der Chunk-Größe |
| `jimenoyepes2024chunking` | Jimeno Yepes, A., et al. (2024). *Financial report chunking for effective retrieval augmented generation* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2402.05131 | strukturbasiertes, element-basiertes Chunking |
| `finardi2024chronicles` | Finardi, P., et al. (2024). *The chronicles of RAG: The retriever, the chunk and the generator* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2401.07883 | Retriever, Chunk und Generator als Einheit |
| `ji2023hallucination` | Ji, Z., et al. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys, 55*(12), Artikel 248. https://doi.org/10.1145/3571730 | Halluzinationen in NLG |
| `taiwo2026chunking` | Taiwo, S., & Amaluddin Yusoff, M. (2026). Evaluating chunking strategies for retrieval-augmented generation in oil and gas enterprise documents. In D. C. Wyld et al. (Hrsg.), *Computer Science & Information Technology (CS & IT)* (S. 69–79). AIRCC Publishing Corporation. https://doi.org/10.5121/csit.2026.160507 | nur Domänenbeispiel (Öl und Gas, nur Retrieval); trägt die Forschungslücke nicht, weil der Verlag AIRCC auf Beall's List steht ([ADR 0011, Nachtrag](../adr/0011-forschungsluecke.md#nachtrag-26102026-taiwo-kein-beleg-der-lücke)) |
| `gomezcabello2025chunking` | Gomez-Cabello, C. A., et al. (2025). Comparative evaluation of advanced chunking for retrieval-augmented generation in large language models for clinical decision support. *Bioengineering, 12*(11), 1194. https://doi.org/10.3390/bioengineering12111194 | Chunking-Vergleich in einer Fachdomäne (klinisch), Forschungslücke ([ADR 0011](../adr/0011-forschungsluecke.md)) |
| `qu2025semanticchunking` | Qu, R., Tu, R., & Bao, F. S. (2025). Is semantic chunking worth the computational cost? In *Findings of the ACL: NAACL 2025* (S. 2155–2177). https://doi.org/10.18653/v1/2025.findings-naacl.114 | semantisch/strukturell nicht konsistent besser: starke Baseline, Thema nicht trivial ([ADR 0010](../adr/0010-starke-baseline.md)) |
| `pesl2026servicediscovery` | Pesl, R. D., Mathew, J. G., Mecella, M., & Aiello, M. (2026). Retrieval-augmented generation for service discovery: Chunking strategies and benchmarking. *IEEE Transactions on Services Computing, 19*(2), 1520–1534. https://doi.org/10.1109/TSC.2026.3665441 | nächste verwandte Arbeit: Chunking-Vergleich auf OpenAPI-Dokumentation (Aufteilung je Endpunkt schlägt ganzes Dokument und JSON-Aufteilung, S. 1530); misst nur das Retrieval (Recall, Precision, S. 1527); Abgrenzung über Dokumentart und Methodik ([Forschungsdesign](../explanation/research-design.md#verwandte-arbeiten)); Volltext am 26.10.2026 geprüft |

Ohne Eintrag: der Praktiker-Blogbeitrag (Mai 2026) auf FastAPI/Supabase/Stripe; er erscheint in der Arbeit nicht
([ADR 0011, Nachtrag](../adr/0011-forschungsluecke.md#nachtrag-26102026-blogbeitrag-entfällt-erste-säule-neu)).

## Ergänzte Quellen (26.10.2026)

Bei der Kapitelplanung der Arbeit gezielt für Lücken gesucht und am 26.10.2026 gegen Crossref, PMLR, ACL Anthology und
OpenAlex geprüft (bibliografische Angaben). Am 26. und 27.10.2026 hat Claude die zitierten Aussagen am Volltext
geprüft, Jonas hat das Ergebnis am 27.10.2026 freigegeben; damit sind sie nach
[ADR 0018](../adr/0018-literaturbasis.md) zitierbar. Prüfprotokoll mit Zitat, Seite und Einschränkung je Quelle: PaperLab,
`planning/fulltext-check.md`; die Statistik-Originale sind nur für das Verfahren zitiert und bibliografisch an den
JSTOR-PDFs geprüft. Für die
Webquelle `smith2024chunking` (Chroma-Blog) gilt: nur als technische Begründung in ADRs und der Methodik, nicht in der
theoretischen Fundierung (TH S. 11); dort stehen `chen2024densex`, `wang2024bestpractices` und `liu2024lostmiddle`.

### Chunking und Kontext

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `liu2024lostmiddle` | Liu, N. F., et al. (2024). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics, 12*, 157–173. https://doi.org/10.1162/tacl_a_00638 | Sprachmodelle nutzen Passagen in der Mitte langer Kontexte schlechter |
| `chen2024densex` | Chen, T., et al. (2024). Dense X retrieval: What retrieval granularity should we use? In *Proceedings of EMNLP 2024* (S. 15159–15177). https://doi.org/10.18653/v1/2024.emnlp-main.845 | Granularität der Retrieval-Einheit beeinflusst Retrieval und QA |
| `wang2024bestpractices` | Wang, X., et al. (2024). Searching for best practices in retrieval-augmented generation. In *Proceedings of EMNLP 2024* (S. 17716–17736). https://doi.org/10.18653/v1/2024.emnlp-main.981 | Abwägung der Chunk-Größe; Überlappung (Sliding Window) verbessert das Retrieval in einem kleinen Experiment |

### Modellwissen und Kontamination

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `mallen2023whennot` | Mallen, A., et al. (2023). When not to trust language models: Investigating effectiveness of parametric and non-parametric memories. In *Proceedings of ACL 2023* (S. 9802–9822). https://doi.org/10.18653/v1/2023.acl-long.546 | Retrieval hilft vor allem bei seltenem Wissen: erste Säule, Korpuswechsel, K0 |
| `kandpal2023longtail` | Kandpal, N., et al. (2023). Large language models struggle to learn long-tail knowledge. In *Proceedings of ICML 2023* (PMLR 202, S. 15696–15707). https://proceedings.mlr.press/v202/kandpal23a.html | selten vorkommendes Wissen wird schlecht gelernt |
| `sainz2023contamination` | Sainz, O., et al. (2023). NLP evaluation in trouble: On the need to measure LLM data contamination for each benchmark. In *Findings of the ACL: EMNLP 2023* (S. 10776–10787). https://doi.org/10.18653/v1/2023.findings-emnlp.722 | Kontamination je Datensatz und Modell messen: Closed-Book-Prüfung |

### Antwortbewertung und Fragetypen

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `krishna2021hurdles` | Krishna, K., Roy, A., & Iyyer, M. (2021). Hurdles to progress in long-form question answering. In *Proceedings of NAACL-HLT 2021* (S. 4940–4957). https://doi.org/10.18653/v1/2021.naacl-main.393 | ROUGE taugt für lange Antworten nicht; die Bewertung braucht klare Kriterien (menschliche Bewertung nennen sie ebenfalls unzuverlässig) |
| `rashkin2023attribution` | Rashkin, H., et al. (2023). Measuring attribution in natural language generation models. *Computational Linguistics, 49*(4), 777–840. https://doi.org/10.1162/coli_a_00486 | Attribution als eigenes, menschlich bewertetes Kriterium: Quellenbezug |
| `bolotova2022nonfactoid` | Bolotova, V., et al. (2022). A non-factoid question-answering taxonomy. In *Proceedings of SIGIR 2022* (S. 1196–1207). https://doi.org/10.1145/3477495.3531926 | Fragetypen jenseits faktischer Fragen: H3 |
| `beyer2020questions` | Beyer, S., Macho, C., Di Penta, M., & Pinzger, M. (2020). What kind of questions do developers ask on Stack Overflow? *Empirical Software Engineering, 25*(3), 2258–2301. https://doi.org/10.1007/s10664-019-09758-x | Kategorien von Entwicklerfragen |

### Statistik

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `friedman1937ranks` | Friedman, M. (1937). The use of ranks to avoid the assumption of normality implicit in the analysis of variance. *Journal of the American Statistical Association, 32*(200), 675–701. https://doi.org/10.1080/01621459.1937.10503522 | Friedman-Test ([ADR 0044](../adr/0044-statistische-auswertung.md)) |
| `wilcoxon1945ranking` | Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin, 1*(6), 80–83. https://doi.org/10.2307/3001968 | Wilcoxon-Vorzeichen-Rang-Test |
| `holm1979sequentially` | Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70. https://www.jstor.org/stable/4615733 | Holm-Korrektur |
| `kendall1939rankings` | Kendall, M. G., & Babington Smith, B. (1939). The problem of m rankings. *The Annals of Mathematical Statistics, 10*(3), 275–287. https://doi.org/10.1214/aoms/1177732186 | Kendalls W |
| `fritz2012effectsize` | Fritz, C. O., Morris, P. E., & Richler, J. J. (2012). Effect size estimates: Current use, calculations, and interpretation. *Journal of Experimental Psychology: General, 141*(1), 2–18. https://doi.org/10.1037/a0024338 | Effektstärke r = \|z\| / √N, Schwellen .1 / .3 / .5; N bei verbundenen Stichproben ist eigene Festlegung (Paare ohne Nulldifferenz) |
| `spearman1904proof` | Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology, 15*(1), 72–101. https://doi.org/10.2307/1412159 | Spearmans ρ (H2) |
| `efron1979bootstrap` | Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1–26. https://doi.org/10.1214/aos/1176344552 | Bootstrap-Intervalle ([ADR 0044, Nachtrag](../adr/0044-statistische-auswertung.md#nachtrag-26102026-konfidenzintervalle-der-differenzen), [ADR 0046](../adr/0046-zweitbewertung.md)) |
| `dror2018hitchhiker` | Dror, R., Baumer, G., Shlomov, S., & Reichart, R. (2018). The hitchhiker's guide to testing statistical significance in natural language processing. In *Proceedings of ACL 2018* (S. 1383–1392). https://doi.org/10.18653/v1/P18-1128 | Wahl der Signifikanztests beim Systemvergleich |

Endseiten von Wilcoxon (83) und Spearman (101) sowie das Heft von Holm (2) sind am 27.10.2026 an den JSTOR-PDFs bestätigt.

### Entwicklerdokumentation

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `aghajani2019issues` | Aghajani, E., et al. (2019). Software documentation issues unveiled. In *Proceedings of ICSE 2019* (S. 1199–1210). IEEE. https://doi.org/10.1109/ICSE.2019.00122 | Taxonomie mit 162 Problemtypen von Softwaredokumentation (878 Artefakte analysiert, 824 gelabelt): Relevanz der Domäne |

### Methodik

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `doering2016forschungsmethoden` | Döring, N., & Bortz, J. (2016). *Forschungsmethoden und Evaluation in den Sozial- und Humanwissenschaften* (5. Aufl.). Springer. https://doi.org/10.1007/978-3-642-41089-5 | Kap. 7: experimentelles Design, interne und externe Validität (S. 184, 193); Messwiederholung, bei der dieselben Untersuchungseinheiten alle Bedingungen durchlaufen, erhöht die Teststärke (S. 209) |

## Technische Quellen (Web)

Webseiten ohne Datum stehen in der Bibliografie ohne Abrufdatum (Regel der PaperLab-Klasse); das Abrufdatum hier
dokumentiert nur den geprüften Stand.

### Embedding und Vektorsuche

Abgerufen am 13.10.2026; Grundlage von [ADR 0023](../adr/0023-embedding-modell.md) und
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `openai2024embeddingmodels` | OpenAI. (2024, 25. Januar). *New embedding models and API updates*. https://openai.com/index/new-embedding-models-and-api-updates/ | Einführung von `text-embedding-3-small/-large` |
| `openai2026embeddingsguide` | OpenAI. (o. J.). *Vector embeddings* [Leitfaden]. https://developers.openai.com/api/docs/guides/embeddings | MTEB 64,6 % / 62,3 %, max. 8.192 Tokens, `cl100k_base`, Normierung auf Länge 1, Kosinus, Dimensionen |
| `openai2026te3large` | OpenAI. (o. J.). *text-embedding-3-large* [Modellseite]. https://developers.openai.com/api/docs/models/text-embedding-3-large | Preis 0,13 USD je 1 Mio. Tokens, Snapshot nur als Alias |
| `openai2026embeddingsapi` | OpenAI. (o. J.). *Create embeddings* [API-Referenz]. https://developers.openai.com/api/reference/resources/embeddings/methods/create | ≤ 2.048 Eingaben und ≤ 300.000 Tokens je Anfrage, `usage.prompt_tokens` |
| `chroma2026configure` | Chroma. (o. J.). *Configure collections*. https://docs.trychroma.com/docs/collections/configure | HNSW ist approximativ; Standard `l2`, `ef_search` = 100 |

### Chunk-Größe

Abgerufen am 14.10.2026; Grundlage von [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) und
[ADR 0026](../adr/0026-c3-vergleichbarkeit.md) (dort auch die Begründung der C3-Obergrenze aus
[ADR 0021](../adr/0021-c3-grenzen.md)).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `smith2024chunking` | Smith, B., & Troynikov, A. (2024, 3. Juli). *Evaluating chunking strategies for retrieval*. Chroma. https://www.trychroma.com/research/evaluating-chunking | `text-embedding-3-large`, fünf abgerufene Chunks; kleinere Chunks (800 → 200 Tokens) erhöhen die Precision deutlich bei etwa gleichem Recall (rund 85–89 %) |
| `bhat2025chunksize` | Bhat, S. R., Rudat, M., Spiekermann, J., & Flores-Herr, N. (2025). *Rethinking chunk size for long-document retrieval: A multi-dataset analysis* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2505.21700 | beste Chunk-Größe hängt vom Datensatz und Fragetyp ab (64–128 Tokens für knappe Fakten, 512–1.024 für breiten Kontext) und vom Embedding-Modell |
| `vuejs2026compare` | vuejs/docs. (o. J.). *Comparing b75d188...40aa88a*. GitHub. https://github.com/vuejs/docs/compare/b75d188ab16bf83bd1f364a77dfd2315be8f3fa4...40aa88af0094f7bab4aaf786e55c748a6a251d88 | acht Commits, im Ausschnitt sechs geänderte Guide-Dateien; historisch (Vue-Korpus, ADR 0025 ersetzt durch [ADR 0038](../adr/0038-korpus-e2e.md)) |

### Antwortmodell

Abgerufen am 17.10.2026, Volltexte von Renze und Guven sowie Lee et al. am 22.10.2026 geprüft; Grundlage von
[ADR 0033](../adr/0033-antwortmodell.md) (mit Nachtrag 22.10.2026).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `openai2026gpt6luna` | OpenAI. (o. J.). *GPT-6 Luna* [Modellseite]. https://developers.openai.com/api/docs/models/gpt-6-luna | 0,10/0,50 USD je 1 Mio. Ein-/Ausgabe-Tokens, Wissensstand 18.05.2026, Effort `none` bis `max`, nur Alias |
| `openai2026latestmodel` | OpenAI. (o. J.). *Using GPT-6* [Leitfaden]. https://developers.openai.com/api/docs/guides/latest-model | `temperature` nur bei Effort `none`; `none` nur bei GPT-6 Sol und GPT-6 Luna |
| `openai2026reasoning` | OpenAI. (o. J.). *Reasoning models* [Leitfaden]. https://developers.openai.com/api/docs/guides/reasoning | Effort-Stufen, Parameter bei Reasoning |
| `openai2026deprecations` | OpenAI. (o. J.). *Deprecations*. https://developers.openai.com/api/docs/deprecations | GPT-4.1/4o-Snapshots bis 14.01.2027, GPT-5-Snapshots bis 11.12.2026 |
| `renze2024temperature` | Renze, M., & Guven, E. (2024). The effect of sampling temperature on problem solving in large language models. In *Findings of the ACL: EMNLP 2024* (S. 7346–7356). https://doi.org/10.18653/v1/2024.findings-emnlp.432 | keine signifikante Wirkung der Temperatur 0,0–1,0 auf die Lösungsgüte bei Multiple-Choice-Problemlösen; für offene Fragen mit Kontext nur eine Übertragung, keine Messung. Zwei Autoren (laut PDF; ACL Anthology und Crossref nennen einen) |
| `atil2024nondeterminism` | Atil, B., et al. (2024). *Non-determinism of "deterministic" LLM settings* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2408.04667 | Genauigkeitsschwankungen bis 15 % trotz „deterministischer“ Einstellungen; trägt „Temperatur 0 garantiert keine identischen Ausgaben“ |
| `lee2026noisybench` | Lee, S., Jo, Y., Seo, M., Lee, M., & Seo, M. (2026). *Lost in the noise: How reasoning models fail with contextual distractors* [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2601.07226 | Reasoning-Modelle brechen mit störenden Passagen ebenfalls ein; nicht begutachteter Preprint (arXiv v1); kein Vergleich mit abgeschaltetem Reasoning ([ADR 0033](../adr/0033-antwortmodell.md), Nachtrag) |

### Korpus

Abgerufen am 18.10.2026 (Snapshot); Grundlage von [ADR 0038](../adr/0038-korpus-e2e.md). Commit, Daten und SHA-256 je
Datei: `docs/corpus_snapshot.txt`; Umfang und Lizenz: [Korpus](corpus.md).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `testerarmy2026e2e` | TesterArmy, Inc. (2026). *e2e* (Version ef977f4, Commit ef977f4856da009cac26d78d2e9bb14e5991ee41 vom 17.10.2026) [Computer Software, Apache-2.0]. GitHub. https://github.com/tester-army/e2e/tree/ef977f4856da009cac26d78d2e9bb14e5991ee41/docs | Korpus des Experiments: Dokumentation unter `docs/` auf dem festen Commit (`config.CORPUS_COMMIT`) |

## Methodenquellen der Bewertung

Geprüft am 21.10.2026, DOIs am 22.10.2026 ergänzt; Grundlage von [ADR 0046](../adr/0046-zweitbewertung.md)
(Übereinstimmungsmaße der Zweitbewertung) und [ADR 0047](../adr/0047-ragas-als-triangulation.md) (Richtermodell für
RAGAS). RAGAS selbst steht unter den Kernquellen (`es2024ragas`).

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `feinstein1990kappa` | Feinstein, A. R., & Cicchetti, D. V. (1990). High agreement but low kappa: I. The problems of two paradoxes. *Journal of Clinical Epidemiology, 43*(6), 543–549. https://doi.org/10.1016/0895-4356(90)90158-L | Kappa-Paradox bei hoher Prävalenz: darum kein Cohens Kappa |
| `gwet2008ac1` | Gwet, K. L. (2008). Computing inter-rater reliability and its variance in the presence of high agreement. *British Journal of Mathematical and Statistical Psychology, 61*(1), 29–48. https://doi.org/10.1348/000711006X126600 | AC1, stabil bei hoher Übereinstimmung |
| `gwet2014handbook` | Gwet, K. L. (2014). *Handbook of inter-rater reliability: The definitive guide to measuring the extent of agreement among raters* (4. Aufl.). Advanced Analytics. | AC2 mit Gewichten für ordinale Skalen |
| `hayes2007alpha` | Hayes, A. F., & Krippendorff, K. (2007). Answering the call for a standard reliability measure for coding data. *Communication Methods and Measures, 1*(1), 77–89. https://doi.org/10.1080/19312450709336664 | Krippendorffs α (ordinal) als Vergleichsmaß |
| `zheng2023judge` | Zheng, L., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. In *Advances in Neural Information Processing Systems 36* (S. 46595–46623). Curran Associates. https://doi.org/10.52202/075280-2020 | Selbstbevorzugung des Richtermodells; LLM-Gegenprobe nur als Triangulation |

### Nächste Treffer der Suche zur zweiten Säule

Dokumentierte Suche vom 26.10.2026 (Protokoll im Recherche-Log der Arbeit, PaperLab); bibliografische Angaben gegen
Crossref geprüft, nur Abstracts gelesen. Pham Doan und Luong Ngoc (2025) am 26.10.2026 am Volltext geprüft; Dhakal et
al. (2026) nur als Suchtreffer, Begutachtung der Zeitschrift unklar.

| BibTeX-Key | Quelle (APA 7) | Belegt |
|------------|----------------|--------|
| `phamdoan2025headingaware` | Pham Doan, T., & Luong Ngoc, P. (2025). Optimizing context retrieval for RAG via heading-aware chunking and hierarchical document structure integration. In *2025 IEEE 7th Symposium on Computers & Informatics (ISCI)* (S. 456–461). IEEE. https://doi.org/10.1109/ISCI65687.2025.11167620 | nächster Treffer: überschriftenbasiertes Chunking mit Überlappung auf AWS-Handbüchern (100 Fragen), verglichen nur mit semantischem und elementbasiertem Chunking, keine größenbasierte Baseline; Bewertung allein per LLM-as-a-Judge (binär), keine Statistik |
| `dhakal2026techdocs` | Dhakal, A., Neupane, S. S., Dhakal, A., & Paudel, M. (2026). Optimizing technical documentation for RAG systems: A comparative analysis of semantic chunking vs. structural formatting. *International Journal of Scientific Research in Science, Engineering and Technology, 13*(1), 222–227. https://doi.org/10.32628/ijsrset261313 | semantisch gegen ganzes Dokument, nur Retrieval |
