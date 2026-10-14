# Architekturentscheidungen (ADR)

Verbindliche Entscheidungen der Bachelorarbeit, je Datei eine. Übertragen aus dem Decision Log des
früheren Ground-Truth-Leitfadens (D1–D18 = ADR 0001–0018, Stand Juni 2026; in der Git-Historie); ADR 0019–0031 sind seit
der Umsetzung hinzugekommen. Hintergrund: [Forschungsdesign](../explanation/research-design.md); offene Entscheidungen: [Plan](../plan.md).
Format: Michael Nygard (Status, Kontext, Entscheidung, Konsequenzen), Nummern und Dateinamen bleiben fest.
Neue oder geänderte Entscheidungen: neue Datei mit der nächsten Nummer, alte auf „ersetzt durch …“ setzen.
Präzisiert oder ergänzt eine neue ADR eine ältere, bekommt die ältere nur einen Hinweis im Status; ihre Entscheidung
bleibt unverändert.

| ADR | Entscheidung | Status |
|---|---|---|
| [0001](0001-korpus-vuejs.md) | Dokumentkorpus: Vue.js-Dokumentation | Angenommen; konkretisiert durch 0019, 0025 |
| [0002](0002-zitierstil-apa.md) | Zitierstil: biblatex + biber, APA 7, `\parencite` | Angenommen |
| [0003](0003-kein-praxispartner.md) | Kein Praxispartner | Angenommen |
| [0004](0004-zeitraum-und-abgabe.md) | Bearbeitungszeitraum Juli–Dezember 2026, Abgabe 24.12.2026 | Angenommen |
| [0005](0005-drei-chunking-strategien.md) | Drei Chunking-Strategien C1–C3, C4 optional | Angenommen; konkretisiert durch 0021, ergänzt durch 0026; C4-Bedingung präzisiert durch 0028 |
| [0006](0006-nur-chunking-variiert.md) | Nur das Chunking variiert | Angenommen |
| [0007](0007-triangulation.md) | Evaluation als Triangulation: manuell primär, RAGAS sekundär | Angenommen |
| [0008](0008-kosten-als-variable.md) | Kosten/Effizienz als eigene abhängige Variable | Angenommen |
| [0009](0009-hypothesen.md) | Drei geschärfte Hypothesen H1–H3, explorativ | Angenommen |
| [0010](0010-starke-baseline.md) | Fixed-size mit Overlap ist eine starke Baseline | Angenommen |
| [0011](0011-forschungsluecke.md) | Forschungslücke: entwicklerorientierte Open-Source-Dokumentation | Angenommen |
| [0012](0012-retrieval-metriken.md) | Retrieval-Metriken: Recall@k, Precision@k, MRR (+ Hit@k) | Angenommen |
| [0013](0013-antwort-rubrik.md) | Antwort-Rubrik: Skala 0–2, fünf Kriterien, gleich gewichtet | Angenommen |
| [0014](0014-temperatur-und-topk.md) | Temperatur 0 und top-k 5 konstant | Angenommen |
| [0015](0015-tech-stack.md) | Tech-Stack | Angenommen |
| [0016](0016-modell-neutralitaet.md) | Modell-Neutralität | Angenommen; Embedding-Modell und Versionen in 0023 |
| [0017](0017-fragenkatalog.md) | Fragenkatalog: etwa 40 Fragen mit Referenzantworten | Angenommen; präzisiert durch 0027, 0029 und 0030 |
| [0018](0018-literaturbasis.md) | Literaturbasis: 15 verifizierte Quellen | Angenommen |
| [0019](0019-korpus-ausschnitt.md) | Korpus-Ausschnitt: ganzes `src/guide/`, nur Composition API | Teilweise ersetzt (0025); ergänzt durch 0022, Sensitivitätsregel geändert durch 0026 |
| [0020](0020-playground-urls-kuerzen.md) | Kodierte Playground-URLs beim Preprocessing kürzen | Angenommen |
| [0021](0021-c3-grenzen.md) | C3: Untergrenze 50 Tokens, Verschmelzen vor dem Teilen | Angenommen; ergänzt durch 0026 (auch Begründung der Obergrenze) |
| [0022](0022-h1-abschnitte-in-ground-truth.md) | H1-Abschnitte in der Ground Truth nur, wenn die ganze Seite die Antwort ist | Angenommen |
| [0023](0023-embedding-modell.md) | Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen | Angenommen |
| [0024](0024-referenzvektoren-und-exakte-suche.md) | Referenzvektoren speichern und exakt suchen | Angenommen |
| [0025](0025-korpus-guide-api-styleguide.md) | Korpus: Guide, API-Referenz (Composition) und Style Guide auf `40aa88a` | Angenommen |
| [0026](0026-c3-vergleichbarkeit.md) | C3-Vergleichbarkeit: Größenkontrolle K1 und faire Sensitivitätsregel | Angenommen |
| [0027](0027-blinde-annotation.md) | Relevanz-Annotation blind vor jedem Retrieval; nachträgliche Ergänzungen nur als Sensitivität | Angenommen |
| [0028](0028-c4-bedingung.md) | C4 nur, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist | Angenommen |
| [0029](0029-fragetypen-und-konstruktionsklassen.md) | Fragenkatalog: 48 Fragen, Fragetypen und Konstruktionsklassen mit Quoten, Bereichsuntergrenzen | Angenommen; ergänzt durch 0031 |
| [0030](0030-einfrieren-des-fragenkatalogs.md) | Einfrieren des Fragenkatalogs als technische Sperre vor dem Retrieval | Angenommen; erweitert durch 0031 |
| [0031](0031-stichprobenplan-und-ki-durchsicht.md) | Zufälliger Stichprobenplan der Slots und protokollierte KI-Durchsicht des Fragenkatalogs | Angenommen |
