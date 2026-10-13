# Forschungsdesign

> Seitentyp: Hintergrund (explanation). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

## Rangfolge bei Widersprüchen

Diese Seite erklärt, was die Arbeit untersucht und warum sie so angelegt ist. Verbindliche Entscheidungen stehen
einzeln in den [ADRs](../adr/README.md), Formate und Definitionen unter [Nachschlagen](../README.md), der Zeitplan
und offene Punkte im [Plan](../plan.md).

**Prioritätsregel bei Widersprüchen:**

1. Finales Exposé und spätere Präzisierungen im Chat (höchste Priorität)
2. Konkret bestätigte Entscheidungen aus dem Chatverlauf
3. Ursprüngliche Projekt-Baseline
4. Allgemeine Best Practices

Wo die ursprüngliche Baseline und das Exposé sich unterscheiden, gilt das Exposé. Die wichtigsten Abweichungen sind im Abschnitt „Was sich gegenüber der ursprünglichen Baseline geändert hat“ unten aufgeführt.


## Finale Projektdefinition (verbindlich)

### Titel
**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems für technische Projektdokumentation**

### Hauptforschungsfrage
**Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis technischer Open-Source-Dokumentation?**

### Unterfragen
1. Welche Chunking-Strategien eignen sich für die Aufbereitung technischer Projektdokumentation im Kontext eines RAG-Systems?
2. Wie unterscheiden sich die Strategien hinsichtlich der Retrieval-Qualität (Recall@k, Precision@k, MRR)?
3. Wie wirken sie sich auf die Antwortqualität aus (Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit)?
4. Welche Trade-offs ergeben sich zwischen Chunk-Größe, Kontextabdeckung, Redundanz, Retrieval-Präzision, Kosten und Antwortqualität?
5. Welche Empfehlungen lassen sich für die Gestaltung von RAG-Systemen auf technischer Dokumentation ableiten?

### Ziel in einem Satz
Konzeption, Implementierung und Evaluation einer RAG-Pipeline für technische Open-Source-Dokumentation, bei der ausschließlich die Chunking-Strategie variiert wird, um deren Einfluss auf Retrieval- und Antwortqualität isoliert zu bestimmen und daraus praktische Empfehlungen abzuleiten.

### Dozenten-taugliche Kurzbeschreibung
Die Arbeit vergleicht drei Chunking-Strategien für ein RAG-System auf Basis der Vue.js-Dokumentation. Dazu wird ein Dokumentationssnapshot fixiert, ein Fragenkatalog mit Referenzantworten und relevanten Quellen kuratiert und eine RAG-Pipeline mit konstantem Modell-, Embedding- und Retrieval-Setup implementiert. Bewertet werden Retrieval-Qualität (Recall@k, Precision@k, MRR) und Antwortqualität (referenzbasierte Rubrik), ergänzt um eine automatisierte Sekundärbewertung und eine Effizienzbetrachtung.


## Was sich gegenüber der ursprünglichen Baseline geändert hat

Dieser Abschnitt ist bewusst explizit, damit keine veralteten Baseline-Punkte versehentlich übernommen werden.

### Geändert / ersetzt
- **Korpus FastAPI → Vue.js.** Grund: Abgrenzung. Ein Praktiker-Blogbeitrag (Mai 2026) hat ein nahezu identisches Setup (FastAPI/Supabase/Stripe, eingefrorenes QA-Set, eine Variable pro Experiment, RAGAS, überschriftenbasiertes Chunking) bereits umgesetzt. Vue.js grenzt Korpus und Domäne klar ab und behält die Fragetyp-Vielfalt.
- **Alle FastAPI-spezifischen Beispiele entfallen** (Path Parameters, Dependency Injection, Pydantic) und werden durch Vue-Beispiele ersetzt (Reaktivität, Composition API, Komponenten, Props, Composables; siehe [Fragenkatalog](../reference/question-catalogue.md)).
- **Repository-Pfad** `data/raw/fastapi_docs_snapshot/` → `data/raw/vue_docs_snapshot/`.
- **Hypothesen** der Baseline (alte H1–H3) → durch geschärfte H1–H3 ersetzt (Abschnitt „Hypothesen“ unten), die die nicht-offensichtlichen Dimensionen betonen.
- **RAGAS-Rolle** von „optional/Zusatz" → fester Bestandteil der **Triangulation** mit explizitem Übereinstimmungsabgleich.

### Konkretisiert / ergänzt
- **Kosten/Effizienz** wird zur eigenständigen abhängigen Variable.
- **Fixed-size + Overlap** wird ausdrücklich als leistungsfähige Baseline positioniert (belegt durch Qu et al. 2025), wodurch die Arbeit gegen den Vorwurf der Trivialität abgesichert ist.
- **Forschungslücke** wird domänenspezifisch geschärft (fachfremde Vergleiche existieren; Softwaredokumentation ist die Lücke).
- **Zeitplan** auf konkrete Kalenderdaten Juli–Dezember 2026 gelegt.

### Bewusst nicht Teil der Arbeit (Scope-Schutz, unverändert)
Bester LLM-/Embedding-Vergleich; RAG vs. kein RAG als Hauptfrage; Fine-Tuning; lokale LLMs; rein automatische Bewertung ohne menschliche Kontrolle; private Firmendaten; multimodale Dokumente/PDFs mit Diagrammen.


## Wissenschaftlicher Rahmen

### Problem und Ansatz
Technische Dokumentation enthält umfangreiches projektspezifisches Wissen, das über viele Dateien verteilt ist. LLMs beantworten Fragen, verfügen aber ohne Kontext nicht zuverlässig über projektspezifisches Wissen und neigen zu unbelegten Aussagen. RAG ruft relevante Dokumentstellen zur Laufzeit ab und stellt sie als Kontext bereit. Die Qualität hängt maßgeblich von der **Segmentierung (Chunking)** ab.

### Forschungslücke und Abgrenzung (drei Säulen)
1. **Anderer Korpus:** Vue.js statt der bereits informell untersuchten FastAPI/Supabase/Stripe-Doku.
2. **Andere Domäne:** entwicklerorientierte Frontend-Framework-Dokumentation; kontrollierte Chunking-Vergleiche existieren bislang vor allem fachfremd (Unternehmensdokumente, klinische Entscheidungsunterstützung).
3. **Striktere Methodik:** referenzbasierte manuelle Bewertung als Primärverfahren, Fragetyp-Differenzierung, Reproduzierbarkeit über Snapshot.

### Hypothesen (verbindlich, explorativ)
- **H1 — Starke Baseline:** Strukturbasiertes Chunking erzielt gegenüber größenbasiertem Chunking **ohne** Overlap eine höhere Retrieval-Qualität, übertrifft größenbasiertes Chunking **mit** Overlap jedoch **nicht durchgängig**, da der Overlap den Verlust an Segmentgrenzen weitgehend kompensiert.
- **H2 — Entkopplung Retrieval/Antwort:** Unterschiede in der Retrieval-Qualität übertragen sich **nur teilweise** auf die Antwortqualität, da das Sprachmodell moderate Retrieval-Defizite ausgleicht.
- **H3 — Fragetyp-Interaktion:** Die relative Eignung der Strategien **variiert nach Fragetyp**; strukturbasiertes Chunking begünstigt konzeptuelle, abschnittsübergreifende Fragen, während größenbasierte Verfahren für eng umgrenzte faktische Fragen ausreichen.

### Warum das Thema nicht trivial ist
Die Annahme „strukturiert schlägt naiv offensichtlich" ist empirisch nicht gesichert: Qu, Bao & Tu (2025) zeigen, dass semantisch/strukturell motiviertes Chunking größenbasiertes Chunking **nicht konsistent** übertrifft und der Mehraufwand oft nicht gerechtfertigt ist. Der eigentliche Erkenntnisgewinn liegt nicht in „wer gewinnt", sondern in **Effektgröße, Kosten, Metrik-Abhängigkeit, der Retrieval-Antwort-Entkopplung und der Fragetyp-Interaktion**.

### Verwandte Arbeiten (Hinweis)
Der erwähnte Praktiker-Blogbeitrag (Mai 2026) ist **keine zitierfähige wissenschaftliche Quelle**, sollte aber im Kapitel „Verwandte Arbeiten" kurz als informeller Vorläufer eingeordnet werden — das wirkt souveräner, als ihn auszulassen, und unterstreicht die Abgrenzung (peer-review-fähige Methodik, anderer Korpus, deutschsprachige wissenschaftliche Arbeit).


## Korpus: Begründung der Wahl
Vue.js bietet entwicklerorientierte, didaktisch hochwertige Dokumentation mit konzeptueller und prozeduraler Tiefe, liegt im Quellrepository durchgängig als **Markdown** vor (VitePress) und ist öffentlich und stabil. Damit ist sie sauber snapshot- und parsebar und erlaubt viele Fragetypen.

## Chunking-Strategien

| ID | Strategie | Parameter | Vorteil | Nachteil |
|----|-----------|-----------|---------|----------|
| **C1** | Fixed-size ohne Overlap | 500 Tokens, Overlap 0 | einfach, reproduzierbar, Baseline | Kontextbruch an Grenzen |
| **C2** | Fixed-size mit Overlap | 500 Tokens, Overlap 100 | bessere Abdeckung, **starke Baseline** | mehr Chunks, mehr Redundanz, höhere Kosten |
| **C3** | Strukturbasiert | Abschnitt unter H1–H3, 50–800 Tokens (kurze verschmelzen, lange an Absätzen teilen; [ADR 0021](../adr/0021-c3-grenzen.md)) | erhält semantische Einheiten | uneinheitliche Chunkgrößen (auf Vue relevant: lange Abschnitte) |
| C4 | Semantisch (optional) | Trennung nach semantischer Ähnlichkeit | theoretisch spannend | Mehraufwand, weitere Modellabhängigkeit, nur falls Zeit |

**Konstant halten (nur Chunking variiert):** Korpus/Snapshot, Sprache (Englisch), Embedding-Modell, LLM, Temperatur (0), top-k (5), Prompt, Fragenset, Bewertungsrubrik, Vector Store, Retrieval-Art (Dense), Antwortformat.

> C3 auf Vue: 77 von 560 Überschriften-Segmenten sind kürzer als 50 Tokens, 8 länger als 800; Regeln und Begründung in [ADR 0021](../adr/0021-c3-grenzen.md).


## RAG-Pipeline-Architektur

```
Documentation Snapshot (Vue.js)
        ↓
Preprocessing (Markdown Cleaning)
        ↓
Chunking Strategy  → C1 / C2 / C3
        ↓
Embedding (OpenAI Embeddings)
        ↓
Vector Store (Chroma, ein Index pro Strategie)
        ↓
Question → Retriever (Top-k = 5)
        ↓
Prompt Assembly (Question + Context, identisch für alle Strategien)
        ↓
LLM Answer (Answer + Sources)
        ↓
Evaluation (Retrieval-Metriken + Antwort-Rubrik + Effizienz)
```


## Validität und Grenzen

- **Interne Validität:** Misst die Arbeit wirklich den Chunking-Einfluss? Absicherung über Konstanthaltung aller anderen Parameter, gleicher Korpus/Fragen/Prompts/Modelle, temperature 0.
- **Externe Validität:** begrenzt — ein Korpus (Vue.js), Ergebnisse liefern Hinweise, keine universelle Aussage.
- **Konstruktvalidität:** etablierte Metriken, transparente Rubrik, Bewertungsbeispiele zeigen, optional Zweitbewertung.
- **Reliabilität:** temperature 0, Rohdaten speichern, Modellversion dokumentieren, Snapshot verwenden, Prompts veröffentlichen.

## Prompt-Gestaltung

- Kein Chain-of-Thought und keine Few-Shot-Beispiele: Der Prompt bleibt minimal und vermeidet Störgrößen durch
  Prompt-Engineering bei der Antwortqualität.
- Das Modell soll ausdrücklich ablehnen, wenn der Kontext nicht reicht; das stützt die Bewertung der
  Halluzinationsfreiheit (Rubrik-Kriterium 4).
- Der System-Prompt bindet das Modell an den gegebenen Kontext, damit Unterschiede in der Antwortqualität auf die
  gefundenen Chunks (und damit auf die Chunking-Strategie) zurückgehen und nicht auf parametrisches Wissen.

Die Vorlagen selbst: [Prompts](../reference/prompts.md).
