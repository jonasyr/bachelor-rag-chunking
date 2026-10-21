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
variiert); alle konkreten Festlegungen stehen in den ADRs. Als Datengrundlage nennt das Exposé die Vue.js-Dokumentation
als Beispiel; den Wechsel zu e2e begründet [ADR 0038](../adr/0038-korpus-e2e.md), der Betreuer wurde darüber
informiert.

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
Diagrammen). Die Kontrolle K0 vergleicht zwar Antworten mit und ohne Retrieval, aber nur als Kontrolle, die H2 deutbar
macht, nicht als eigene Forschungsfrage ([Warum Closed-Book-Prüfung und K0](#warum-closed-book-prüfung-und-k0)).

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
   es bislang vor allem für spezialisierte Fachdomänen (unternehmensinterne technische Dokumente, klinische
   Entscheidungsunterstützung).
3. **Striktere Methodik:** referenzbasierte manuelle Bewertung als Primärverfahren, Fragetyp-Differenzierung,
   Reproduzierbarkeit über einen fixierten Snapshot, eine Closed-Book-Prüfung des Fragenkatalogs und die Kontrollen K1
   und K0.

### Hypothesen (aus dem Exposé, explorativ)

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

Korpus ist die Dokumentation des Testframeworks e2e (`tester-army/e2e`, [ADR 0038](../adr/0038-korpus-e2e.md)).
Ursprünglich war Vue.js gewählt ([ADR 0001](../adr/0001-korpus-vuejs.md),
[ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)); das Antwortmodell kannte Vue.js aber so gut, dass Retrieval
kaum einen Unterschied machte. e2e ist neu, wird real genutzt, ist groß genug und dem Modell weitgehend unbekannt
(Messung: [Korpusauswahl](../reference/corpus-selection.md)). Erst unter dieser Bedingung können sich die Strategien
in der Antwortqualität unterscheiden: Kennt das Modell die Antwort ohnehin, gleicht es jedes Retrieval aus, und H2 und
H3 ließen sich nicht von Modellwissen trennen. Commit, Umfang und Bereiche: [Korpus](../reference/corpus.md).

## Chunking-Strategien

Entscheidungen: [ADR 0005](../adr/0005-drei-chunking-strategien.md) (Auswahl),
[ADR 0021](../adr/0021-c3-grenzen.md) (Grenzen von C3), [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) (Kontrolle
K1), [ADR 0028](../adr/0028-c4-bedingung.md) (Bedingung für C4), [ADR 0041](../adr/0041-kontrolle-k0.md) (Kontrolle
K0). Parameterwerte stehen nur in `src/config.py`, erklärt in [Konfiguration](../reference/configuration.md).

| ID | Strategie | Vorteil | Nachteil |
|----|-----------|---------|----------|
| **C1** | größenbasiert ohne Overlap | einfach, reproduzierbar, Baseline | Kontextbruch an Grenzen |
| **C2** | größenbasiert mit Overlap | bessere Abdeckung, **starke Baseline** | mehr Chunks, mehr Redundanz, höhere Kosten |
| **C3** | strukturbasiert an Markdown-Überschriften, mit Unter- und Obergrenze | erhält semantische Einheiten | uneinheitliche Chunkgrößen (auf e2e relevant: sehr lange Referenzseiten neben vielen kurzen Abschnitten) |
| K1 | Kontrolle, keine Strategie: größenbasiert ohne Overlap in der mittleren C3-Größe, nur Retrieval | trennt Struktur- von Größeneffekt | eine zusätzliche Retrieval-Reihe |
| K0 | Kontrolle, keine Strategie: dieselben Fragen ohne Retrieval, nur Antworten | zeigt den Beitrag des Retrievals überhaupt | nicht blind bewertbar, kein Quellenbezug |
| C4 | semantisch (optional) | theoretisch spannend | Mehraufwand, weitere Modellabhängigkeit |

**Warum diese drei.** C1 ist die naive, reproduzierbare Untergrenze. C2 ist die Variante, die in der Praxis oft
genügt; sie als starke Baseline ernst zu nehmen, schützt die Arbeit gegen den Vorwurf der Trivialität (H1). C3 nutzt
die Markdown-Struktur, die technische Dokumentation ohnehin mitbringt, und ist die Strategie, deren Mehrwert in Frage
steht. C4 bringt eine weitere Modellabhängigkeit und kommt nur, wenn der Zeitplan es zulässt.

**Warum die Kontrolle K1.** C3 unterscheidet sich von C1/C2 nicht nur in der Struktur, sondern auch in der Größe:
Seine Chunks sind im Mittel kleiner, und bei konstantem top-k erhält das Sprachmodell weniger Kontext. Ohne Kontrolle
wäre ein Unterschied zwischen C3 und C1 nicht zuzuordnen. K1 hat die Größe von C3, aber keine Struktur: Schlägt C3
C1, K1 aber ebenso, liegt der Effekt in der Größe; schlägt C3 auch K1, in der Struktur. Aus demselben Grund wertet die
Sensitivitätsprüfung kleine Chunks nicht konstruktionsbedingt ab. K1 erzeugt keine Antworten, weil es nur die
Retrieval-Frage klären soll; es wird als Kontrollanalyse berichtet, nicht als vierte Strategie. Gemessene
Chunk-Zahlen und -Längen: [Experiment-Protokoll](../reference/experiment-record.md#chunking-e2e).

## Warum nur das Chunking variiert

Die Forschungsfrage zielt auf einen kausal interpretierbaren Einfluss der Segmentierung. Das trägt nur, wenn sich die
Läufe in nichts anderem unterscheiden: Korpus, Embedding-Modell, Sprachmodell, Temperatur, top-k, Prompt,
Fragenkatalog, Rubrik und Vektorindex bleiben für alle Strategien gleich. Die vollständige Liste steht in
[ADR 0006](../adr/0006-nur-chunking-variiert.md), Temperatur und top-k in
[ADR 0014](../adr/0014-temperatur-und-topk.md).

## Warum Closed-Book-Prüfung und K0

**Warum der Korpuswechsel sie nötig macht.** Auf Vue.js beantwortete das Antwortmodell die meisten Fragen auch ohne
Dokumentation richtig; die Antwortqualität maß so vor allem Modellwissen, nicht Retrieval
([ADR 0038](../adr/0038-korpus-e2e.md), Messung: [Korpusauswahl](../reference/corpus-selection.md#closed-book-fragen)).
Dass das Modell e2e kaum kennt, beruht auf wenigen Diagnosefragen. Ob das auch für den eigenen Katalog gilt, muss jede
Katalogfrage selbst zeigen; und wie viel das Retrieval am Ende beiträgt, muss die Auswertung messen, nicht annehmen.

**Was die Prüfung für den Katalog sichert.** Jede Frage wird vor dem Einfrieren ohne Kontext beantwortet; trifft die
Antwort den Kernpunkt der Referenzantwort, gilt die Frage als retrieval-unabhängig und wird markiert. Mindestens zwei
Drittel der Fragen müssen retrieval-abhängig sein (`config.CLOSED_BOOK_MIN_DEPENDENT_SHARE`), sonst wird nicht
eingefroren. So misst der Katalog nachweislich überwiegend Retrieval. Bekannte Fragen bleiben markiert im Katalog,
statt ersetzt zu werden: Ein Filter auf alles Unbekannte würde den Katalog auf abseitige Details verschieben, und die
Markierung erlaubt, die Ergebnisse getrennt zu berichten. Jonas beurteilt die Antworten selbst; ein LLM-Richter mit
κ-Prüfung wäre bei so seltenen Treffern instabil ([ADR 0040](../adr/0040-closed-book-pruefung.md)). Ablauf und Regeln:
[Fragenkatalog](../reference/question-catalogue.md#regeln-für-annotation-und-aufbau).

**Warum ein eigener Closed-Book-Prompt.** Der RAG-Prompt bindet das Modell an die Ausschnitte. Ohne Ausschnitte
lehnt es damit fast immer ab und zeigt nicht, was es weiß; die Prüfung wäre wertlos. Der Closed-Book-Prompt ist
derselbe Prompt ohne Ausschnitte und ohne diese Bindung. Prüfung und K0 nutzen ihn beide und messen so dieselbe
Bedingung ([Prompts](../reference/prompts.md#closed-book-prompt-prüfung-und-k0)).

**Warum K0 H2 deutbar macht.** H2 nimmt an, dass das Modell moderate Retrieval-Defizite ausgleicht. Ähnliche
Antwortqualität bei unterschiedlichem Retrieval kann aber auch heißen, dass das Modell die Antwort ohne jeden Kontext
kennt. K0 beantwortet dieselben Fragen ohne Retrieval, im selben Lauf und vom selben Modellstand wie C1–C3; die
Differenz zu C1–C3 zeigt, wie viel das Retrieval überhaupt beiträgt, getrennt für retrieval-abhängige und bekannte
Fragen ([ADR 0041](../adr/0041-kontrolle-k0.md)). K0 ist eine Kontrolle, keine Chunking-Strategie und keine eigene
Forschungsfrage.

**Warum K0 nach C1–C3 und nicht blind bewertet wird.** K0 sah keine Passagen. Im blinden Bewertungspaket wäre eine
K0-Antwort deshalb sofort erkennbar, und der Quellenbezug ergäbe stets 0. K0 wird darum als eigener Satz erst nach
C1–C3 bewertet und ohne Quellenbezug verglichen; die Reihenfolge verhindert, dass das Wissen um die K0-Antworten die
Bewertung der Strategien färbt. Regeln: [Evaluation](../reference/evaluation.md#kontrolle-k0).

## Warum die Evaluation so angelegt ist

- **Ground Truth vorab:** Fragen, Referenzantworten und relevante Abschnitte stehen fest, bevor ein Retrieval- oder
  Strategie-Ergebnis vorliegt ([ADR 0017](../adr/0017-fragenkatalog.md)); sonst könnte die Bewertungsgrundlage
  unbemerkt den Ergebnissen folgen. Deshalb wird die Relevanz auch blind annotiert, also vor jedem Retrieval;
  nachträgliche Ergänzungen zählen nur als Sensitivität ([ADR 0027](../adr/0027-blinde-annotation.md)). Das Einfrieren
  ist im Code erzwungen: Das Retrieval läuft nur auf dem Katalog, dessen Prüfsummen der Freeze-Datensatz festhält
  ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)). Closed-Book-Antworten dürfen vor dem Einfrieren zum
  Umformulieren führen, weil sie nichts über Retrieval, Chunks oder Strategien verraten
  ([ADR 0040](../adr/0040-closed-book-pruefung.md)).
- **Fragenkatalog als Stichprobe:** Fragetyp und Konstruktionsklasse (ein Abschnitt, mehrere Abschnitte, Detail,
  Paraphrase) werden getrennt festgelegt, weil H3 nach beidem fragt und einfache Fragen allein einen Deckeneffekt
  zeigen; die Klassen sind ohne Retrieval maschinell prüfbar
  ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)).
  Die Ausgangsabschnitte werden reproduzierbar zufällig nach Textlänge gezogen und nach dem Tokenanteil der Bereiche
  verteilt, damit nicht die Vorlieben der verfassenden Person die Themen bestimmen und jeder Bereich vorkommt
  ([ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md)).
  Eine KI-Durchsicht schlägt nur vor; Fragen, Referenzantworten und Relevanzurteile schreibt allein Jonas, und jeder
  Vorschlag ist für die KI-Offenlegung protokolliert (ADR 0031).
- **Retrieval und Antwort getrennt:** Retrieval-Metriken ([ADR 0012](../adr/0012-retrieval-metriken.md)) und die
  Antwort-Rubrik ([ADR 0013](../adr/0013-antwort-rubrik.md)) werden getrennt erhoben, weil H2 gerade fragt, ob sich
  Unterschiede im Retrieval auf die Antworten übertragen.
- **Embedding und exakte Suche:** Ein starkes Embedding-Modell für alle Strategien verhindert, dass ein schwaches
  Modell Unterschiede zwischen ihnen verdeckt; es nutzt dieselbe Tokenisierung wie Chunking und Relevanz
  ([ADR 0023](../adr/0023-embedding-modell.md)). Weil das Modell keinen datierten Stand hat, werden die Vektoren einmal
  erzeugt und gespeichert, und jedes Top-k wird gegen eine exakte Rangfolge geprüft. Unterschiede im Retrieval gehen
  so auf die Chunks zurück, nicht auf eine Näherungssuche oder einen veränderten Modellstand
  ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).
- **Blind und regelbasiert bewertet:** Dieselbe Person, die die Hypothesen aufgestellt hat, bewertet die Antworten.
  Sie sieht deshalb nur neutrale Codes statt der Strategie, damit kein Erwartungseffekt entsteht
  ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md), in der App: [ADR 0034](../adr/0034-bewertung-in-der-app.md)).
  Eine Rubrik mit Adjektiven („teilweise korrekt“) lässt dieselbe Antwort an zwei Tagen verschieden einstufen; die
  Werte folgen deshalb nach festen Regeln aus Prüffragen und vorab eingefrorenen Kernpunkten
  ([ADR 0035](../adr/0035-regelbasierte-bewertung.md),
  [ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)).
  Der Pilot zeigte Abzüge aus Regelfällen statt aus schwachen Antworten; die Prüfregeln sind darum präzisiert, und die
  Kernpunkte werden aus der Referenzantwort vorbefüllt und von Jonas bestätigt
  ([ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)).
- **Triangulation:** Die manuelle, referenzbasierte Bewertung ist primär, weil sie auf der eigenen Ground Truth beruht
  und nicht zirkulär ist. RAGAS kommt als feste zweite Sicht erst nach der regelbasierten
  Bewertung, mit einem anderen Richtermodell als dem Antwortmodell; die Übereinstimmung beider ist selbst ein Befund,
  und RAGAS ist nie alleinige Grundlage ([ADR 0007](../adr/0007-triangulation.md),
  [ADR 0047](../adr/0047-ragas-als-triangulation.md)).
- **Kosten:** Strategien unterscheiden sich im Aufwand; Qualität wird deshalb den Kosten gegenübergestellt
  ([ADR 0008](../adr/0008-kosten-als-variable.md)).

Metriken, Formeln und Rubrik im Einzelnen: [Evaluation](../reference/evaluation.md).

## RAG-Pipeline-Architektur

Konzeptionelle Übersicht; die Reihenfolge der Schritte und ihre Befehle stehen im README und in
[Werkzeuge](../reference/tooling.md).

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
Question → Retriever (Top-k)        ← K1 endet hier (nur Retrieval und Retrieval-Metriken)
        ↓
Prompt Assembly (Question + Context, identisch für alle Strategien)
        ↓
LLM Answer (Antwort; Quellen = die top-k Chunk-IDs des Prompts)
        ↓
Evaluation (Retrieval-Metriken + Antwort-Rubrik + Effizienz)

Kontrolle K0 (im selben Lauf, ohne Retrieval):
Question → Closed-Book-Prompt → LLM Answer → Evaluation (Rubrik ohne Quellenbezug, nach C1–C3)
```

Welche Schritte schon umgesetzt sind: [Plan](../plan.md#stand).

## Validität und Grenzen

- **Interne Validität:** Misst die Arbeit wirklich den Chunking-Einfluss? Absicherung über Konstanthaltung aller
  anderen Parameter (gleicher Korpus, gleiche Fragen, Prompts und Modelle, Temperatur 0) und die Kontrollen K1 (Größe
  gegen Struktur) und K0 (Beitrag des Retrievals); die Closed-Book-Prüfung sichert, dass mindestens zwei Drittel der
  Fragen retrieval-abhängig sind ([Warum Closed-Book-Prüfung und K0](#warum-closed-book-prüfung-und-k0)).
- **Externe Validität:** begrenzt; ein Korpus (e2e, [ADR 0038](../adr/0038-korpus-e2e.md)): ein junges Projekt
  (angelegt 22.07.2026) mit einem dem Modell vertrauten Fachgebiet und nach Einschätzung teils KI-geschriebener
  Dokumentation ([Korpusauswahl](../reference/corpus-selection.md)). Die Ergebnisse liefern Hinweise, keine universelle
  Aussage.
- **Korpuswechsel:** Das angemeldete Exposé nennt Vue.js als Datengrundlage. Der Wechsel zu e2e ist mit Messung
  begründet, und der Betreuer wurde informiert ([ADR 0038](../adr/0038-korpus-e2e.md)); die Arbeit nennt die
  Abweichung.
- **Konstruktvalidität:** etablierte Metriken, transparente Rubrik mit regelbasierten Prüffragen und vorab
  eingefrorenen Kernpunkten, blind bewertet ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md),
  [ADR 0035](../adr/0035-regelbasierte-bewertung.md), [0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md),
  [0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md));
  eine zweite Person bewertet 36 Antworten blind ([ADR 0046](../adr/0046-zweitbewertung.md), [Evaluation](../reference/evaluation.md#zweitbewertung)).
- **Kontrollen:** Das Closed-Book-Urteil fällt Jonas über Antworten auf seine eigenen Fragen, nicht blind
  ([ADR 0040](../adr/0040-closed-book-pruefung.md)); K0 wird nicht blind bewertet, und der Quellenbezug fehlt im
  Vergleich ([ADR 0041](../adr/0041-kontrolle-k0.md)). Die Diagnose für die Korpuswahl stammt von Agenten und beruht
  auf 20 Fragen je Korpus, mit entsprechend breiten Intervallen ([ADR 0038](../adr/0038-korpus-e2e.md)).
- **Reliabilität:** Temperatur 0, Rohdaten speichern, Modellversionen dokumentieren, fixierter Snapshot, Prompts
  veröffentlichen. Temperatur 0 verringert die Zufälligkeit, garantiert aber keine identischen Ausgaben; deshalb werden
  die Antworten einmal erzeugt und gespeichert ([ADR 0033](../adr/0033-antwortmodell.md)).
- **Generator:** Das Antwortmodell antwortet direkt, ohne verdecktes Reasoning (`config.LLM_REASONING_EFFORT` =
  `none`, die Voraussetzung für Temperatur 0). Die Ergebnisse gelten für einen solchen Generator; ein Reasoning-Modell
  könnte schwache Kontexte teilweise ausgleichen, sodass die Unterschiede zwischen den Strategien kleiner ausfielen
  ([ADR 0033](../adr/0033-antwortmodell.md)).

## Prompt-Gestaltung

- Kein Chain-of-Thought und keine Few-Shot-Beispiele: Der Prompt bleibt minimal und vermeidet Störgrößen durch
  Prompt-Engineering bei der Antwortqualität.
- Das Modell soll ausdrücklich ablehnen, wenn der Kontext nicht reicht; das stützt die Bewertung der
  Halluzinationsfreiheit (Rubrik-Kriterium 4).
- Der System-Prompt bindet das Modell an den gegebenen Kontext, damit Unterschiede in der Antwortqualität auf die
  gefundenen Chunks (und damit auf die Chunking-Strategie) zurückgehen und nicht auf parametrisches Wissen.
- Closed-Book-Prüfung und K0 nutzen einen eigenen Prompt ohne Ausschnitte und ohne diese Bindung, weil der RAG-Prompt
  ohne Kontext nur ablehnen ließe ([Warum Closed-Book-Prüfung und K0](#warum-closed-book-prüfung-und-k0)).

Die Vorlagen selbst: [Prompts](../reference/prompts.md).
