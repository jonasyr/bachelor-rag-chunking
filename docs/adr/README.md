# Architekturentscheidungen (ADR)

*[Doku-Index](../README.md) · Entscheidungen*

Verbindliche Entscheidungen der Bachelorarbeit, je Datei eine. ADR 0001–0018 sind aus dem Decision Log des früheren
Ground-Truth-Leitfadens übertragen (D1–D18, Stand Juni 2026); ADR 0019–0048 sind seit der Umsetzung hinzugekommen, ab
0019 ist Dn = ADR n. Der Leitfaden lag als `docs/Ground_Truth_Projektleitfaden.md` im Repo, zuletzt auf Commit
`15304d6^` (`git show 15304d6^:docs/Ground_Truth_Projektleitfaden.md`); „Leitfaden §N“ in ADR 0001–0018 meint seine
Abschnitte, die Links führen zur heutigen Seite des Themas.
Hintergrund: [Forschungsdesign](../explanation/research-design.md); offene Entscheidungen: [Plan](../plan.md).

## Regeln

- Format: Michael Nygard (Status, Kontext, Entscheidung, Konsequenzen); Nummern und Dateinamen bleiben fest. Kontext,
  Entscheidung und Konsequenzen einer angenommenen ADR werden nie geändert; ausgenommen sind Linkziele, wenn eine
  verlinkte Seite umzieht.
- Eine neue oder geänderte Entscheidung bekommt eine neue Datei mit der nächsten Nummer. Die ältere ADR bekommt in
  ihrer Statuszeile die Beziehung mit Link; ist sie ganz abgelöst, beginnt die Statuszeile mit „Ersetzt durch …“.
- Nachtrag: ein datierter Abschnitt `## Nachtrag TT.MM.JJJJ: Thema` am Ende (vor `## Literatur`), mit dem
  Entscheider im ersten Satz. Er präzisiert, korrigiert oder hält eine Folgeentscheidung fest, ohne die Entscheidung
  zu ersetzen; ersetzt er sie, ist eine neue ADR nötig. Die Statuszeile verweist auf ihn.
- Die Statuszeile enthält nur Status, Beziehungen und kurze Hinweise mit Link; alles mit eigenem Inhalt steht in einem
  Nachtrag.

## Beziehungen

| Begriff | Bedeutung |
|---|---|
| ersetzt (durch) | Die ganze Entscheidung gilt nicht mehr; die Statuszeile der alten ADR beginnt mit „Ersetzt durch …“. |
| teilweise ersetzt | Einzelne Teile gelten nicht mehr (genannt), der Rest gilt weiter. |
| geändert durch / ändert | Eine Regel der alten Entscheidung gilt in geänderter Form; der Rest bleibt. |
| gegenstandslos durch | Die Regel hängt an etwas Abgelöstem (meist dem Vue-Korpus) und hat keinen Anwendungsfall mehr. |
| ergänzt / erweitert | Fügt etwas hinzu, ohne Bestehendes zu ändern. |
| präzisiert / konkretisiert | Legt fest, was die ältere ADR offen ließ (Wert, Verfahren, Bedingung). |
| umgesetzt durch | Setzt die Entscheidung technisch oder mit konkreten Werten um. |
| Nachtrag | Datierter Abschnitt in derselben ADR (siehe Regeln). |
| Hinweis | Kurze Anmerkung in der Statuszeile: Korrektur eines Belegs im Kontext, geänderter Stand (z. B. Korpus), Verweis. |

## Index

Spalte „Titel“ = Überschrift der Datei; „Status“ = Status und Beziehungen, Kurzform der Statuszeile.

| ADR | Titel | Status |
|---|---|---|
| [0001](0001-korpus-vuejs.md) | Dokumentkorpus: Vue.js-Dokumentation | Ersetzt durch 0038 (e2e); vorher konkretisiert durch 0019, 0025 |
| [0002](0002-zitierstil-apa.md) | Zitierstil: biblatex + biber, APA 7, `\parencite` | Angenommen |
| [0003](0003-kein-praxispartner.md) | Kein Praxispartner | Angenommen; Hinweis: Korpus seit 0038 e2e |
| [0004](0004-zeitraum-und-abgabe.md) | Bearbeitungszeitraum Juli–Dezember 2026, Abgabe 24.12.2026 | Angenommen |
| [0005](0005-drei-chunking-strategien.md) | Drei Chunking-Strategien C1–C3, C4 optional | Angenommen; konkretisiert durch 0021; ergänzt durch 0026; C4-Bedingung präzisiert durch 0028; Hinweis: Korpus seit 0038 e2e |
| [0006](0006-nur-chunking-variiert.md) | Nur das Chunking variiert | Angenommen; Hinweis: Kontrollen K1 (0026) und K0 (0038, 0041) sind keine Strategien |
| [0007](0007-triangulation.md) | Evaluation als Triangulation: manuell primär, RAGAS sekundär | Angenommen; konkretisiert durch 0046; RAGAS konkretisiert und Metriken geändert durch 0047 |
| [0008](0008-kosten-als-variable.md) | Kosten/Effizienz als eigene abhängige Variable | Angenommen; ergänzt durch 0044 |
| [0009](0009-hypothesen.md) | Drei geschärfte Hypothesen H1–H3, explorativ | Angenommen; Auswertungsart geändert durch 0044; Nachtrag 22.10.2026 |
| [0010](0010-starke-baseline.md) | Fixed-size mit Overlap ist eine starke Baseline | Angenommen; Hinweis: Autorenreihenfolge Qu, Tu & Bao |
| [0011](0011-forschungsluecke.md) | Forschungslücke: entwicklerorientierte Open-Source-Dokumentation | Angenommen; Hinweis: Domäne im Wortlaut des Exposés, zweite Säule nach Pesl et al. (2026) eingeengt; Nachtrag 26.10.2026 (Taiwo kein Beleg); Nachtrag 26.10.2026 (Blogbeitrag entfällt, erste Säule neu) |
| [0012](0012-retrieval-metriken.md) | Retrieval-Metriken: Recall@k, Precision@k, MRR (+ Hit@k) | Angenommen; ergänzt durch 0044 |
| [0013](0013-antwort-rubrik.md) | Antwort-Rubrik: Skala 0–2, fünf Kriterien, gleich gewichtet | Angenommen; ergänzt durch 0032, 0044; Stufen operationalisiert durch 0035; Hinweis: Normierung 0–100 nicht umgesetzt |
| [0014](0014-temperatur-und-topk.md) | Temperatur 0 und top-k 5 konstant | Angenommen; umgesetzt in 0033 |
| [0015](0015-tech-stack.md) | Tech-Stack | Angenommen; konkretisiert durch 0023, 0024; „optional RAGAS“ geändert durch 0047; ergänzt durch 0044 (SciPy) |
| [0016](0016-modell-neutralitaet.md) | Modell-Neutralität | Angenommen; konkretisiert durch 0023 (Embedding-Modell) und 0033 (Antwortmodell) |
| [0017](0017-fragenkatalog.md) | Fragenkatalog: etwa 40 Fragen mit Referenzantworten | Angenommen; präzisiert durch 0027, 0029; technisch umgesetzt durch 0030; ergänzt durch 0022, 0040 |
| [0018](0018-literaturbasis.md) | Literaturbasis: 15 verifizierte Quellen | Angenommen; Hinweis: Literaturbasis seitdem erweitert |
| [0019](0019-korpus-ausschnitt.md) | Korpus-Ausschnitt: ganzes `src/guide/`, nur Composition API | Teilweise ersetzt durch 0025, 0038 (Ausschnitt, Commit) und 0042 (Anker); ergänzt durch 0020 (gegenstandslos), 0022; Sensitivitätsregel geändert durch 0026 |
| [0020](0020-playground-urls-kuerzen.md) | Kodierte Playground-URLs beim Preprocessing kürzen | Gegenstandslos durch 0038 |
| [0021](0021-c3-grenzen.md) | C3: Untergrenze 50 Tokens, Verschmelzen vor dem Teilen | Angenommen; ergänzt durch 0026 (auch Begründung der Obergrenze) |
| [0022](0022-h1-abschnitte-in-ground-truth.md) | H1-Abschnitte in der Ground Truth nur, wenn die ganze Seite die Antwort ist | Angenommen; Hinweis: H1-Anker seit 0042 aus dem Seitenpfad |
| [0023](0023-embedding-modell.md) | Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen | Angenommen |
| [0024](0024-referenzvektoren-und-exakte-suche.md) | Referenzvektoren speichern und exakt suchen | Angenommen; Versionierung geändert durch 0045; Archivierung geändert durch 0048 |
| [0025](0025-korpus-guide-api-styleguide.md) | Korpus: Guide, API-Referenz (Composition) und Style Guide auf `40aa88a` | Ersetzt durch 0038 |
| [0026](0026-c3-vergleichbarkeit.md) | C3-Vergleichbarkeit: Größenkontrolle K1 und faire Sensitivitätsregel | Angenommen; ändert die Sensitivitätsregel von 0019; Hinweis: Zahlen vom Vue-Korpus, K1-Wert korpusabhängig |
| [0027](0027-blinde-annotation.md) | Relevanz-Annotation blind vor jedem Retrieval; nachträgliche Ergänzungen nur als Sensitivität | Angenommen; technisch umgesetzt durch 0030 |
| [0028](0028-c4-bedingung.md) | C4 nur, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist | Angenommen; Nachtrag 22.10.2026 (C4 nur deskriptiv) |
| [0029](0029-fragetypen-und-konstruktionsklassen.md) | Fragetypen, Konstruktionsklassen und Quoten des Fragenkatalogs | Angenommen; ergänzt durch 0031; Bereichsuntergrenzen ersetzt und Stoppwörter angepasst durch 0039; Hinweis: Quelle des Verhältnisses 2:2:2:1:1 |
| [0030](0030-einfrieren-des-fragenkatalogs.md) | Einfrieren des Fragenkatalogs als technische Sperre | Angenommen; erweitert durch 0031; ergänzt durch 0040 |
| [0031](0031-stichprobenplan-und-ki-durchsicht.md) | Zufälliger Stichprobenplan und protokollierte KI-Durchsicht des Fragenkatalogs | Angenommen; Slotzahlen ersetzt durch 0039; ergänzt durch 0040 |
| [0032](0032-blinde-rubrik-bewertung.md) | Blinde Rubrik-Bewertung der Antworten | Angenommen; ergänzt durch 0034, 0035; Hinweis: Mischen mit Seed (Nachtrag in 0046) |
| [0033](0033-antwortmodell.md) | Antwortmodell und einmalige Generierung | Angenommen; ergänzt durch 0041; Nachtrag 22.10.2026 (Belege) |
| [0034](0034-bewertung-in-der-app.md) | Bewertung in der App | Angenommen; ergänzt durch 0035 |
| [0035](0035-regelbasierte-bewertung.md) | Regelbasierte Rubrik-Bewertung mit Kernpunkten | Angenommen; präzisiert durch 0036, 0037, 0043 (zwei Regelanpassungen); für K0 ergänzt durch 0041; Intra-Rater-Folgeschritt ersetzt durch 0046 |
| [0036](0036-regelbasierte-bewertung-verpflichtend.md) | Regelbasierte Bewertung verpflichtend für neue Scaffolds | Angenommen |
| [0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md) | Präzisierte Prüfregeln und vorbefüllte Kernpunkte | Angenommen; präzisiert durch 0043 |
| [0038](0038-korpus-e2e.md) | Korpus: e2e-Dokumentation statt Vue.js; Closed-Book-Prüfung und Kontrolle K0 | Angenommen; ersetzt 0001, 0025; Stichprobenplan 0039; Beurteilung festgelegt durch 0040; K0 umgesetzt durch 0041; Bereinigungsregel geändert durch 0042 |
| [0039](0039-stichprobenplan-e2e.md) | Stichprobenplan und Bereichsquoten auf e2e | Angenommen |
| [0040](0040-closed-book-pruefung.md) | Closed-Book-Prüfung des Fragenkatalogs | Angenommen; ergänzt 0017, 0030, 0031; Prompt auch für K0 (0041) |
| [0041](0041-kontrolle-k0.md) | Kontrolle K0: Erzeugung und Bewertung | Angenommen |
| [0042](0042-mdx-umwandlung.md) | MDX-Umwandlung: eigene Anker, Agent-Prompts und Video-Karten bleiben | Angenommen; ersetzt die Ankerregel von 0019; ändert die Bereinigungsregel von 0038 |
| [0043](0043-praezisierung-direct-und-teilantworten.md) | Präzisierte Prüfregeln: `direct` bei falscher Kernaussage, Teilantworten | Angenommen; präzisiert 0035, 0037 |
| [0044](0044-statistische-auswertung.md) | Statistische Auswertung und Abbildungen | Angenommen; ergänzt 0008, 0012, 0013, 0015 (SciPy); ändert die Auswertungsart von 0009; Nachtrag 22.10.2026 (konfirmatorische Tests, Tabellennotiz korrigiert in PR #42); Nachtrag 26.10.2026 (Holm-Familie) |
| [0045](0045-retrieval-ergebnisse-versioniert.md) | Retrieval-Ergebnisse des Hauptlaufs versioniert | Angenommen; ändert die Versionierung von 0024; Chunk-Vektoren geändert durch 0048 |
| [0046](0046-zweitbewertung.md) | Zweitbewertung der Antworten | Angenommen; konkretisiert 0007; ersetzt den Intra-Rater-Folgeschritt von 0035; umgesetzt (PR #40); Nachträge 22.10.2026 (Datenschutz, Maß, Zufallszahlen) |
| [0047](0047-ragas-als-triangulation.md) | RAGAS als feste Triangulation | Angenommen; konkretisiert 0007 und ändert dessen Metriken; ändert 0015; umgesetzt (PR #37); Nachträge 21.10.2026 (Strictness), 26.10.2026 (fehlende Werte) |
| [0048](0048-korpus-und-chunk-vektoren-versioniert.md) | Korpus-Snapshot und Chunk-Vektoren versioniert | Angenommen; ändert die Archivierung von 0024 und die Versionierung von 0045 |
