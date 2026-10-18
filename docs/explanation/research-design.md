# Forschungsdesign

> Seitentyp: Hintergrund (explanation). Übersicht: [Dokumentation](../README.md).

Diese Seite erklärt, was die Arbeit untersucht und warum sie so angelegt ist. Sie legt nichts fest.

**Was gilt bei Widersprüchen:** Die [ADRs](../adr/README.md) sind verbindlich; danach gelten die Seiten unter
[Nachschlagen](../README.md#nachschlagen-reference). Das Exposé legt nur Forschungsfrage und Vorgehen fest. Frühere
Grundsatzentscheidungen gegenüber der ursprünglichen Projekt-Baseline (Korpus, Hypothesen, Triangulation, Kosten,
Zeitplan) stehen mit ihrer Begründung in den ADRs. Zeitplan und Projektstand: [Plan](../plan.md).

## Forschungsfrage

Thema der Arbeit: **Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
Retrieval-Augmented-Generation-Systems für technische Projektdokumentation**

Forschungsfrage, wörtlich aus dem Exposé:

> *Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines
> Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis technischer
> Open-Source-Dokumentation?*

Das Exposé ist final und bei der IU angemeldet. Das Original (LaTeX) liegt im privaten Repo PaperLab, nicht in
diesem Repo. Es legt nur die Forschungsfrage und das Vorgehen fest (experimenteller Vergleich, nur die Segmentierung
variiert); alle konkreten Festlegungen stehen in den ADRs.

### Unterfragen (Arbeitsfragen)

Die Unterfragen stammen aus dem Projektleitfaden (Juni 2026, in der Git-Historie), nicht aus dem angemeldeten Exposé.
Sie gliedern die Auswertung, sind aber keine angemeldeten Forschungsfragen.

1. Welche Chunking-Strategien eignen sich für die Aufbereitung technischer Projektdokumentation im Kontext eines
   RAG-Systems?
2. Wie unterscheiden sich die Strategien hinsichtlich der Retrieval-Qualität (Recall@k, Precision@k, MRR; dazu Hit@k,
   [ADR 0012](../adr/0012-retrieval-metriken.md))?
3. Wie wirken sie sich auf die Antwortqualität aus (Korrektheit, Vollständigkeit, Quellenbezug,
   Halluzinationsfreiheit, Verständlichkeit; die fünf Kriterien der Rubrik, [ADR 0013](../adr/0013-antwort-rubrik.md))?
4. Welche Trade-offs ergeben sich zwischen Chunk-Größe, Kontextabdeckung, Redundanz, Retrieval-Präzision, Kosten und
   Antwortqualität?
5. Welche Empfehlungen lassen sich für die Gestaltung von RAG-Systemen auf technischer Dokumentation ableiten?

### Abgrenzung des Umfangs

Nicht Teil der Arbeit: bester LLM- oder Embedding-Vergleich; RAG gegen kein RAG als Hauptfrage; Fine-Tuning; lokale
LLMs; rein automatische Bewertung ohne menschliche Kontrolle; private Firmendaten; multimodale Dokumente (PDFs mit
Diagrammen).

## Wissenschaftlicher Rahmen

### Problem und Ansatz

Technische Dokumentation enthält umfangreiches projektspezifisches Wissen, das über viele Dateien verteilt ist. LLMs
beantworten Fragen, verfügen aber ohne Kontext nicht zuverlässig über projektspezifisches Wissen und neigen zu
unbelegten Aussagen. RAG ruft relevante Dokumentstellen zur Laufzeit ab und stellt sie als Kontext bereit. Die
Qualität hängt maßgeblich von der **Segmentierung (Chunking)** ab: Zu kleine Segmente verlieren Kontext, zu große
tragen irrelevante Information mit, und eine Zerlegung quer zur Dokumentstruktur trennt Zusammengehöriges.

### Forschungslücke und Abgrenzung (drei Säulen)

Entscheidung: [ADR 0011](../adr/0011-forschungsluecke.md).

1. **Anderer Korpus:** e2e ([ADR 0038](../adr/0038-korpus-e2e.md); ursprünglich Vue.js) statt der bereits informell
   untersuchten FastAPI/Supabase/Stripe-Dokumentation.
2. **Andere Domäne:** entwicklerorientierte Dokumentation eines Testframeworks; kontrollierte Chunking-Vergleiche gibt
   es bislang vor allem fachfremd (Unternehmensdokumente, klinische Entscheidungsunterstützung).
3. **Striktere Methodik:** referenzbasierte manuelle Bewertung als Primärverfahren, Fragetyp-Differenzierung,
   Reproduzierbarkeit über einen fixierten Snapshot.

### Hypothesen (verbindlich, explorativ)

Wortlaut aus dem Exposé; Entscheidung, sie explorativ und deskriptiv auszuwerten:
[ADR 0009](../adr/0009-hypothesen.md).

- **H1 (starke Baseline):** Strukturbasiertes Chunking übertrifft größenbasiertes ohne Überlappung hinsichtlich der
  Retrieval-Qualität, nicht aber durchgängig größenbasiertes mit Überlappung, da diese den Informationsverlust an
  Segmentgrenzen weitgehend kompensiert.
- **H2 (Entkopplung Retrieval/Antwort):** Retrieval-Unterschiede übertragen sich nur teilweise auf die
  Antwortqualität, da das Sprachmodell moderate Defizite ausgleichen kann.
- **H3 (Fragetyp-Interaktion):** Die relative Eignung der Strategien variiert nach Fragetyp, wobei strukturbasiertes
  Chunking insbesondere konzeptuelle, abschnittsübergreifende Fragen begünstigt, während größenbasierte Verfahren für
  eng umgrenzte faktische Fragen ausreichen.

Die Hypothesen werden nicht inferenzstatistisch bestätigt, sondern dienen als Leitannahmen für die deskriptive
Auswertung.

### Warum das Thema nicht trivial ist

Die Annahme „strukturiert schlägt naiv offensichtlich“ ist empirisch nicht gesichert: Qu, Bao & Tu (2025) zeigen,
dass semantisch oder strukturell motiviertes Chunking größenbasiertes Chunking nicht konsistent übertrifft und der
Mehraufwand oft nicht gerechtfertigt ist ([ADR 0010](../adr/0010-starke-baseline.md)). Der Erkenntnisgewinn liegt
daher nicht in „wer gewinnt“, sondern in Effektgröße, Kosten, Metrik-Abhängigkeit, der Entkopplung von Retrieval und
Antwort und der Wechselwirkung mit dem Fragetyp.

### Verwandte Arbeiten (Hinweis)

Ein Praktiker-Blogbeitrag (Mai 2026) mit nahezu gleichem Setup ist keine zitierfähige wissenschaftliche Quelle, wird
aber im Kapitel „Verwandte Arbeiten“ kurz als informeller Vorläufer eingeordnet; das unterstreicht die Abgrenzung
(siehe [ADR 0011](../adr/0011-forschungsluecke.md)).

## Korpus: Begründung der Wahl

Korpus ist die Dokumentation des Testframeworks e2e (`tester-army/e2e`, Commit `ef977f4`,
[ADR 0038](../adr/0038-korpus-e2e.md)). Ursprünglich war Vue.js gewählt ([ADR 0001](../adr/0001-korpus-vuejs.md),
[ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)); das Antwortmodell kannte Vue.js aber so gut, dass Retrieval
kaum einen Unterschied machte. e2e ist neu, wird real genutzt, ist mit rund 250.000 Tokens groß genug und dem Modell
weitgehend unbekannt (Messung: [Korpusauswahl](../reference/corpus-selection.md)). Einzelheiten:
[Korpus](../reference/corpus.md).

## Chunking-Strategien

Entscheidungen: [ADR 0005](../adr/0005-drei-chunking-strategien.md) (Auswahl),
[ADR 0021](../adr/0021-c3-grenzen.md) (Grenzen von C3), [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) (Kontrolle
K1), [ADR 0028](../adr/0028-c4-bedingung.md) (Bedingung für C4). Parameterwerte stehen nur in `src/config.py`,
erklärt in [Konfiguration](../reference/configuration.md).

| ID | Strategie | Vorteil | Nachteil |
|----|-----------|---------|----------|
| **C1** | größenbasiert ohne Overlap | einfach, reproduzierbar, Baseline | Kontextbruch an Grenzen |
| **C2** | größenbasiert mit Overlap | bessere Abdeckung, **starke Baseline** | mehr Chunks, mehr Redundanz, höhere Kosten |
| **C3** | strukturbasiert an Markdown-Überschriften, mit Unter- und Obergrenze | erhält semantische Einheiten | uneinheitliche Chunkgrößen (auf Vue relevant: lange Abschnitte) |
| K1 | Kontrolle, keine Strategie: größenbasiert ohne Overlap in der mittleren C3-Größe, nur Retrieval | trennt Struktur- von Größeneffekt | eine zusätzliche Retrieval-Reihe |
| C4 | semantisch (optional) | theoretisch spannend | Mehraufwand, weitere Modellabhängigkeit |

**Warum diese drei.** C1 ist die naive, reproduzierbare Untergrenze. C2 ist die Variante, die in der Praxis oft
genügt; sie als starke Baseline ernst zu nehmen, schützt die Arbeit gegen den Vorwurf der Trivialität (H1). C3 nutzt
die Markdown-Struktur, die technische Dokumentation ohnehin mitbringt, und ist die Strategie, deren Mehrwert in Frage
steht. C4 bringt eine weitere Modellabhängigkeit und kommt nur, wenn der Zeitplan es zulässt.

**Warum die Kontrolle K1.** C3 unterscheidet sich von C1/C2 nicht nur in der Struktur, sondern auch in der Größe:
Seine Chunks sind deutlich kleiner, und bei konstantem top-k erhält das Sprachmodell weniger Kontext. Ohne Kontrolle
wäre ein Unterschied zwischen C3 und C1 nicht zuzuordnen. K1 hat die Größe von C3, aber keine Struktur: Schlägt C3
C1, K1 aber ebenso, liegt der Effekt in der Größe; schlägt C3 auch K1, in der Struktur. Aus demselben Grund wertet die
Sensitivitätsprüfung kleine Chunks nicht konstruktionsbedingt ab. K1 erzeugt keine Antworten, weil es nur die
Retrieval-Frage klären soll; es wird als Kontrollanalyse berichtet, nicht als vierte Strategie. Gemessene
Chunk-Zahlen und -Längen: [Experiment-Protokoll](../reference/experiment-record.md).

## Warum nur das Chunking variiert

Die Forschungsfrage zielt auf einen kausal interpretierbaren Einfluss der Segmentierung. Das trägt nur, wenn sich die
Läufe in nichts anderem unterscheiden: Korpus, Embedding-Modell, Sprachmodell, Temperatur, top-k, Prompt,
Fragenkatalog, Rubrik und Vektorindex bleiben für alle Strategien gleich. Die vollständige Liste steht in
[ADR 0006](../adr/0006-nur-chunking-variiert.md), Temperatur und top-k in
[ADR 0014](../adr/0014-temperatur-und-topk.md).

## Warum die Evaluation so angelegt ist

- **Ground Truth vorab:** Fragen, Referenzantworten und relevante Abschnitte stehen fest, bevor irgendein Ergebnis
  vorliegt ([ADR 0017](../adr/0017-fragenkatalog.md)); sonst könnte die Bewertungsgrundlage unbemerkt den Ergebnissen
  folgen. Deshalb wird die Relevanz auch blind annotiert, also vor jedem Retrieval; nachträgliche Ergänzungen zählen
  nur als Sensitivität ([ADR 0027](../adr/0027-blinde-annotation.md)).
- **Retrieval und Antwort getrennt:** Retrieval-Metriken ([ADR 0012](../adr/0012-retrieval-metriken.md)) und die
  Antwort-Rubrik ([ADR 0013](../adr/0013-antwort-rubrik.md)) werden getrennt erhoben, weil H2 gerade fragt, ob sich
  Unterschiede im Retrieval auf die Antworten übertragen.
- **Triangulation:** Die manuelle, referenzbasierte Bewertung ist primär, weil sie auf der eigenen Ground Truth beruht
  und nicht zirkulär ist; ein automatisiertes Framework (RAGAS) ist sekundär, und die Übereinstimmung beider ist
  selbst ein Befund ([ADR 0007](../adr/0007-triangulation.md)).
- **Kosten:** Strategien unterscheiden sich im Aufwand; Qualität wird deshalb den Kosten gegenübergestellt
  ([ADR 0008](../adr/0008-kosten-als-variable.md)).

Metriken, Formeln und Rubrik im Einzelnen: [Evaluation](../reference/evaluation.md).

## RAG-Pipeline-Architektur

```
Documentation Snapshot (e2e, MDX)
        ↓
Preprocessing (MDX → Markdown)
        ↓
Chunking Strategy  → C1 / C2 / C3   (+ Kontrolle K1)
        ↓
Embedding (OpenAI Embeddings)
        ↓
Vector Store (Chroma, ein Index pro Strategie und für K1)
        ↓
Question → Retriever (Top-k)        ← K1 endet hier (nur Retrieval)
        ↓
Prompt Assembly (Question + Context, identisch für alle Strategien)
        ↓
LLM Answer (Answer + Sources)
        ↓
Evaluation (Retrieval-Metriken + Antwort-Rubrik + Effizienz)
```

Welche Schritte schon umgesetzt sind: [Plan](../plan.md#stand).

## Validität und Grenzen

- **Interne Validität:** Misst die Arbeit wirklich den Chunking-Einfluss? Absicherung über Konstanthaltung aller
  anderen Parameter (gleicher Korpus, gleiche Fragen, Prompts und Modelle, Temperatur 0) und die Kontrolle K1.
- **Externe Validität:** begrenzt; ein Korpus (e2e, [ADR 0038](../adr/0038-korpus-e2e.md)).
  Die Ergebnisse liefern Hinweise, keine universelle Aussage.
- **Konstruktvalidität:** etablierte Metriken, transparente Rubrik, Bewertungsbeispiele; eine Zweitbewertung von
  10–20 % der Antworten wird empfohlen ([ADR 0007](../adr/0007-triangulation.md)).
- **Reliabilität:** Temperatur 0, Rohdaten speichern, Modellversionen dokumentieren, fixierter Snapshot, Prompts
  veröffentlichen. Temperatur 0 verringert die Zufälligkeit, garantiert aber keine identischen Ausgaben; deshalb werden
  die Antworten einmal erzeugt und gespeichert ([ADR 0033](../adr/0033-antwortmodell.md)).
- **Generator:** Das Antwortmodell antwortet direkt, ohne verdecktes Reasoning (Effort `none`, die Voraussetzung für
  Temperatur 0). Die Ergebnisse gelten für einen solchen Generator; ein Reasoning-Modell könnte schwache Kontexte
  teilweise ausgleichen, sodass die Unterschiede zwischen den Strategien kleiner ausfielen
  ([ADR 0033](../adr/0033-antwortmodell.md)).

## Prompt-Gestaltung

- Kein Chain-of-Thought und keine Few-Shot-Beispiele: Der Prompt bleibt minimal und vermeidet Störgrößen durch
  Prompt-Engineering bei der Antwortqualität.
- Das Modell soll ausdrücklich ablehnen, wenn der Kontext nicht reicht; das stützt die Bewertung der
  Halluzinationsfreiheit (Rubrik-Kriterium 4).
- Der System-Prompt bindet das Modell an den gegebenen Kontext, damit Unterschiede in der Antwortqualität auf die
  gefundenen Chunks (und damit auf die Chunking-Strategie) zurückgehen und nicht auf parametrisches Wissen.

Die Vorlagen selbst: [Prompts](../reference/prompts.md).
