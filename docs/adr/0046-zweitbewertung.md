# 0046. Zweitbewertung der Antworten

## Status

Angenommen (21.10.2026; konkretisiert die Empfehlung aus [ADR 0007](0007-triangulation.md) und
[Evaluation](../reference/evaluation.md#zweitbewertung)); Person, Stichprobe und Relevanz von Jonas entschieden, das
Übereinstimmungsmaß ist ein Vorschlag von Claude. Ergänzt am 22.10.2026 um den
[Datenschutz der zweiten Person](#nachtrag-22102026-datenschutz-der-zweiten-person) (Jonas). Präzisiert am 22.10.2026:
[Maß für die geordneten Prüffragen](#nachtrag-22102026-maß-für-die-geordneten-prüffragen) (Jonas).

## Kontext

- Jonas bewertet alle 144 Antworten C1–C3 allein, blind ([ADR 0032](0032-blinde-rubrik-bewertung.md)) und regelbasiert
  ([ADR 0035](0035-regelbasierte-bewertung.md), [ADR 0036](0036-regelbasierte-bewertung-verpflichtend.md)), dazu die
  48 K0-Antworten regelbasiert, aber nicht blind ([ADR 0041](0041-kontrolle-k0.md)). Ohne
  zweite Bewertung bleibt offen, wie stark die Werte von der bewertenden Person abhängen.
- Die Werte sind stark ungleich verteilt: im Pilot e2e (48 Antworten) erhält je Kriterium 71–94 % die 2. Bei so hoher
  Prävalenz fällt Cohens Kappa auch bei fast vollständiger Übereinstimmung niedrig aus (Feinstein & Cicchetti, 1990);
  Gwets AC1 und seine gewichtete Form AC2 bleiben dagegen stabil (Gwet, 2008, 2014).
- Die App kann eine Zweitbewertung schon aufnehmen: eine Kopie des Sets ohne Schlüssel und ohne Prüfantworten
  ([Evaluation](../reference/evaluation.md#zweitbewertung)).

## Entscheidung

Wir werden eine zweite Person (Kommilitonin, Kollege) 12 Fragen × C1–C3 (36 der 144 Antworten, 25 %) blind und
unabhängig mit denselben Prüffragen und den eingefrorenen Kernpunkten in der App bewerten lassen. Die 12 Fragen werden
nach dem Einfrieren des Katalogs und vor der eigenen Bewertung mit festem Seed gezogen, geschichtet nach Fragetyp und
Konstruktionsklasse; die Ziehung kennt keine Ergebnisse.
Wir werden die Übereinstimmung je Prüffrage und je Kriterium berichten: einfache Übereinstimmung, Gwets AC1
(Prüffragen) bzw. AC2 mit ordinalen Gewichten (Kriterien 0–2) und zum Vergleich Krippendorffs α (ordinal; Hayes &
Krippendorff, 2007), jeweils mit Bootstrap-Konfidenzintervall über Fragen. Die Werte der Arbeit bleiben Jonas'
Bewertung; Abweichungen werden besprochen und berichtet, aber nicht nachträglich in `scores.csv` übernommen.
Wir werden, falls bis Mitte November keine Person gefunden ist, ersatzweise dieselbe Stichprobe frühestens zwei
Wochen nach der eigenen Bewertung erneut blind bewerten (Intra-Rater) und zusätzlich ein Sprachmodell, das nicht das
Antwortmodell ist, die Prüffragen beantworten lassen; beides wird als Konsistenz- bzw. Triangulationsprüfung
berichtet, nicht als Inter-Rater-Reliabilität (Zheng et al., 2023).
Die Zweitannotation der Relevanz (`relevant_section_ids`) bleibt vorgemerkt und wird nach dem Einfrieren entschieden.

## Konsequenzen

- Positiv: Die Arbeit kann die Abhängigkeit der Werte von der bewertenden Person beziffern, mit einem Maß, das bei
  fast nur 2en nicht irreführt; die Ziehung vor der Bewertung schließt eine Auswahl nach Ergebnissen aus.
- Negativ: Etwa 1,5–2 Stunden Arbeit für die zweite Person; bei 12 Fragen bleiben die Konfidenzintervalle breit.
  Ziehung und Übereinstimmungsrechnung sind noch umzusetzen (Parameter in `src/config.py`).
- Neutral: K0 bekommt keine Zweitbewertung; seine Werte sind ohne Auszüge nicht blind ([ADR 0041](0041-kontrolle-k0.md)).

## Nachtrag 22.10.2026: Datenschutz der zweiten Person

Von Jonas entschieden; ändert die Entscheidung oben nicht.

- Das Repo ist öffentlich. Die zweite Person erscheint darin nur über ihre Rolle („zweite bewertende Person“), in
  Dateien unter einem Pseudonym (z. B. `R2`); ihr Name und ihre Kontaktdaten stehen in keiner Datei, keinem Commit,
  keinem Log und keiner Ausgabe.
- Vor der Bewertung stimmt sie mündlich zu, dass ihre pseudonymen Werte in der Arbeit und im Repo ausgewertet werden;
  Jonas vermerkt die Zustimmung außerhalb des Repos.
- Ihre Werte liegen nur unter `data/evaluation/` (Dateien und Format legt die Umsetzung fest). Auf ihren Wunsch
  werden sie aus dem aktuellen Stand entfernt (die Git-Historie bleibt); die Arbeit berichtet dann das
  Ersatzverfahren.
- In der Danksagung erscheint sie nur mit ihrem Einverständnis.

## Nachtrag 22.10.2026: Maß für die geordneten Prüffragen

Von Jonas entschieden; präzisiert das Maß, ändert Umfang und Verfahren nicht. Die beiden dreistufigen, geordneten
Prüffragen `grounded` (none < some < all) und `hallucination` (substantive < minor < none) bekommen wie die Kriterien
Gwets AC2 mit ordinalen Gewichten statt AC1, so dass ein knappes Verfehlen als knapp zählt und AC2 und α derselben
Zeile dieselbe Ordnung nutzen. Die Ja/Nein-Prüffragen und die Kernpunkte behalten AC1 (AC2 ohne Gewichte ist AC1).
Umsetzung: [Design](../superpowers/specs/2026-10-22-second-rater-design.md).

## Literatur

- Feinstein, A. R., & Cicchetti, D. V. (1990). High agreement but low kappa: I. The problems of two paradoxes.
  *Journal of Clinical Epidemiology, 43*(6), 543–549.
- Gwet, K. L. (2008). Computing inter-rater reliability and its variance in the presence of high agreement.
  *British Journal of Mathematical and Statistical Psychology, 61*(1), 29–48.
- Gwet, K. L. (2014). *Handbook of inter-rater reliability* (4. Aufl.). Advanced Analytics.
- Hayes, A. F., & Krippendorff, K. (2007). Answering the call for a standard reliability measure for coding data.
  *Communication Methods and Measures, 1*(1), 77–89.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.
  *Advances in Neural Information Processing Systems 36* (Datasets and Benchmarks Track).
