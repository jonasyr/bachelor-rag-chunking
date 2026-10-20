# Architekturentscheidungen (ADR)

Verbindliche Entscheidungen der Bachelorarbeit, je Datei eine. ADR 0001–0018 sind aus dem Decision Log des früheren
Ground-Truth-Leitfadens übertragen (D1–D18, Stand Juni 2026); ADR 0019–0044 sind seit der Umsetzung hinzugekommen, ab
0019 ist Dn = ADR n. Der Leitfaden lag als `docs/Ground_Truth_Projektleitfaden.md` im Repo, zuletzt auf Commit
`15304d6^` (`git show 15304d6^:docs/Ground_Truth_Projektleitfaden.md`); „Leitfaden §N“ in ADR 0001–0018 meint seine
Abschnitte, die Links führen zur heutigen Seite des Themas.
Hintergrund: [Forschungsdesign](../explanation/research-design.md); offene Entscheidungen: [Plan](../plan.md).
Format: Michael Nygard (Status, Kontext, Entscheidung, Konsequenzen), Nummern und Dateinamen bleiben fest.
Neue oder geänderte Entscheidungen: neue Datei mit der nächsten Nummer, alte auf „ersetzt durch …“ setzen.
Präzisiert oder ergänzt eine neue ADR eine ältere, bekommt die ältere nur einen Hinweis im Status; ihre Entscheidung
bleibt unverändert. Hängt eine Regel an einem abgelösten Korpus, wird sie „gegenstandslos durch …“.

| ADR | Entscheidung | Status |
|---|---|---|
| [0001](0001-korpus-vuejs.md) | Dokumentkorpus: Vue.js-Dokumentation | Ersetzt durch 0038 (e2e); vorher konkretisiert durch 0019, 0025 |
| [0002](0002-zitierstil-apa.md) | Zitierstil: biblatex + biber, APA 7, `\parencite` | Angenommen |
| [0003](0003-kein-praxispartner.md) | Kein Praxispartner | Angenommen |
| [0004](0004-zeitraum-und-abgabe.md) | Bearbeitungszeitraum Juli–Dezember 2026, Abgabe 24.12.2026 | Angenommen |
| [0005](0005-drei-chunking-strategien.md) | Drei Chunking-Strategien C1–C3, C4 optional | Angenommen; konkretisiert durch 0021, ergänzt durch 0026; C4-Bedingung präzisiert durch 0028 |
| [0006](0006-nur-chunking-variiert.md) | Nur das Chunking variiert | Angenommen |
| [0007](0007-triangulation.md) | Evaluation als Triangulation: manuell primär, RAGAS sekundär | Angenommen |
| [0008](0008-kosten-als-variable.md) | Kosten/Effizienz als eigene abhängige Variable | Angenommen; ergänzt durch 0044 |
| [0009](0009-hypothesen.md) | Drei geschärfte Hypothesen H1–H3, explorativ | Angenommen; ergänzt durch 0044 |
| [0010](0010-starke-baseline.md) | Fixed-size mit Overlap ist eine starke Baseline | Angenommen |
| [0011](0011-forschungsluecke.md) | Forschungslücke: entwicklerorientierte Open-Source-Dokumentation | Angenommen; Domäne im Wortlaut des Exposés (Forschungsdesign) |
| [0012](0012-retrieval-metriken.md) | Retrieval-Metriken: Recall@k, Precision@k, MRR (+ Hit@k) | Angenommen; ergänzt durch 0044 |
| [0013](0013-antwort-rubrik.md) | Antwort-Rubrik: Skala 0–2, fünf Kriterien, gleich gewichtet | Angenommen; ergänzt durch 0032, 0035, 0044 |
| [0014](0014-temperatur-und-topk.md) | Temperatur 0 und top-k 5 konstant | Angenommen; umgesetzt in 0033 |
| [0015](0015-tech-stack.md) | Tech-Stack | Angenommen; konkretisiert durch 0023, 0024 |
| [0016](0016-modell-neutralitaet.md) | Modell-Neutralität | Angenommen; Embedding-Modell und Versionen in 0023, Antwortmodell in 0033 |
| [0017](0017-fragenkatalog.md) | Fragenkatalog: etwa 40 Fragen mit Referenzantworten | Angenommen; präzisiert durch 0027, 0029 und 0030; ergänzt durch 0022, 0040 |
| [0018](0018-literaturbasis.md) | Literaturbasis: 15 verifizierte Quellen | Angenommen |
| [0019](0019-korpus-ausschnitt.md) | Korpus-Ausschnitt: ganzes `src/guide/`, nur Composition API | Teilweise ersetzt (0025, 0038); Anker ersetzt durch 0042; ergänzt durch 0020 (gegenstandslos), 0022, Sensitivitätsregel geändert durch 0026 |
| [0020](0020-playground-urls-kuerzen.md) | Kodierte Playground-URLs beim Preprocessing kürzen | Angenommen; gegenstandslos durch 0038 |
| [0021](0021-c3-grenzen.md) | C3: Untergrenze 50 Tokens, Verschmelzen vor dem Teilen | Angenommen; ergänzt durch 0026 (auch Begründung der Obergrenze) |
| [0022](0022-h1-abschnitte-in-ground-truth.md) | H1-Abschnitte in der Ground Truth nur, wenn die ganze Seite die Antwort ist | Angenommen |
| [0023](0023-embedding-modell.md) | Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen | Angenommen |
| [0024](0024-referenzvektoren-und-exakte-suche.md) | Referenzvektoren speichern und exakt suchen | Angenommen |
| [0025](0025-korpus-guide-api-styleguide.md) | Korpus: Guide, API-Referenz (Composition) und Style Guide auf `40aa88a` | Ersetzt durch 0038 |
| [0026](0026-c3-vergleichbarkeit.md) | C3-Vergleichbarkeit: Größenkontrolle K1 und faire Sensitivitätsregel | Angenommen; Zahlen vom Vue-Korpus, K1-Wert korpusabhängig |
| [0027](0027-blinde-annotation.md) | Relevanz-Annotation blind vor jedem Retrieval; nachträgliche Ergänzungen nur als Sensitivität | Angenommen; technisch umgesetzt durch 0030 |
| [0028](0028-c4-bedingung.md) | C4 nur, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist | Angenommen |
| [0029](0029-fragetypen-und-konstruktionsklassen.md) | Fragenkatalog: 48 Fragen, Fragetypen und Konstruktionsklassen mit Quoten, Bereichsuntergrenzen | Angenommen; ergänzt durch 0031; Bereichsquoten ersetzt und Stoppwörter angepasst durch 0039 |
| [0030](0030-einfrieren-des-fragenkatalogs.md) | Einfrieren des Fragenkatalogs als technische Sperre vor dem Retrieval | Angenommen; erweitert durch 0031, ergänzt durch 0040 |
| [0031](0031-stichprobenplan-und-ki-durchsicht.md) | Zufälliger Stichprobenplan der Slots und protokollierte KI-Durchsicht des Fragenkatalogs | Angenommen; Slotzahlen ersetzt durch 0039; ergänzt durch 0040 |
| [0032](0032-blinde-rubrik-bewertung.md) | Blinde Rubrik-Bewertung der Antworten (Lesepaket, Bogen, Schlüssel) | Angenommen; ergänzt durch 0034, 0035 |
| [0033](0033-antwortmodell.md) | Antwortmodell `gpt-6-luna` (Effort `none`, Temperatur 0), Antworten einmal erzeugen | Angenommen; ergänzt durch 0041 |
| [0034](0034-bewertung-in-der-app.md) | Bewertung als Seite der App, blinde Einträge `scoring_items.jsonl` | Angenommen; ergänzt durch 0035 |
| [0035](0035-regelbasierte-bewertung.md) | Regelbasierte Rubrik-Bewertung mit Kernpunkten | Angenommen; präzisiert durch 0036, 0037, 0043; für K0 ergänzt durch 0041 |
| [0036](0036-regelbasierte-bewertung-verpflichtend.md) | Regelbasierte Bewertung verpflichtend für neue Scaffolds | Angenommen |
| [0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md) | Präzisierte Prüfregeln und vorbefüllte Kernpunkte | Angenommen; präzisiert durch 0043 |
| [0038](0038-korpus-e2e.md) | Korpus: e2e-Dokumentation statt Vue.js; Closed-Book-Prüfung und Kontrolle K0 | Angenommen; ersetzt 0001, 0025; Stichprobenplan 0039; Beurteilung festgelegt durch 0040; K0 umgesetzt durch 0041; MDX-Umwandlung ergänzt durch 0042 |
| [0039](0039-stichprobenplan-e2e.md) | Stichprobenplan und Bereichsquoten auf e2e | Angenommen |
| [0040](0040-closed-book-pruefung.md) | Closed-Book-Prüfung des Fragenkatalogs (Urteil durch Jonas, gemeinsamer Prompt mit K0) | Angenommen; K0 nutzt den Prompt (0041) |
| [0041](0041-kontrolle-k0.md) | Kontrolle K0: Antworten ohne Retrieval, eigener Bewertungssatz nach C1–C3 | Angenommen |
| [0042](0042-mdx-umwandlung.md) | MDX-Umwandlung: eigene Anker, Agent-Prompts und Video-Karten bleiben | Angenommen |
| [0043](0043-praezisierung-direct-und-teilantworten.md) | Präzisierte Prüfregeln: `direct` bei falscher Kernaussage, Teilantworten | Angenommen |
| [0044](0044-statistische-auswertung.md) | Statistische Auswertung und Abbildungen | Angenommen; ergänzt 0008, 0009, 0012, 0013 |
