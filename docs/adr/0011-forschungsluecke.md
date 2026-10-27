# 0011. Forschungslücke: entwicklerorientierte Open-Source-Dokumentation

## Status

Angenommen (D11 im Leitfaden; Quelle: Chat, ergänzt die Baseline); „Öl und Gas“ im Kontext ist das Beispiel aus der
Quelle `taiwo2026chunking`; maßgeblich für die Domäne ist der Wortlaut des Exposés, „unternehmensinterne technische
Dokumente“. Zweite Säule eingeengt am 22.10.2026: [Nachtrag](#nachtrag-22102026-zweite-säule-eingeengt); Taiwo (2026) kein Beleg der
Lücke: [Nachtrag 26.10.2026](#nachtrag-26102026-taiwo-kein-beleg-der-lücke); Blogbeitrag entfällt, erste Säule neu
bestimmt: [Nachtrag 26.10.2026](#nachtrag-26102026-blogbeitrag-entfällt-erste-säule-neu)

## Kontext

- Kontrollierte Chunking-Vergleiche liegen bisher vor allem in fachfremden Domänen, etwa Öl und Gas (`taiwo2026chunking`) und klinische Entscheidungsunterstützung (`gomezcabello2025chunking`) ([Leitfaden §4.2](../explanation/research-design.md), §18).
- Ein informeller Vorläufer auf FastAPI/Supabase/Stripe existiert als Praktiker-Blogbeitrag (Leitfaden §4.2, §4.5).

## Entscheidung

Wir werden die Forschungslücke als entwicklerorientierte Open-Source-Softwaredokumentation bestimmen.
Wir werden sie durch eine striktere Methodik ergänzen: manuelle Referenzbewertung als Primärverfahren, Fragetyp-Differenzierung und Reproduzierbarkeit über einen Snapshot.

## Konsequenzen

- Neutral: Die Abgrenzung stützt sich auf drei Säulen: anderer Korpus, andere Domäne, striktere Methodik (Leitfaden §4.2).
- Neutral: Der Blogbeitrag ist nicht zitierfähig, wird aber in „Verwandte Arbeiten“ kurz als informeller Vorläufer eingeordnet (Leitfaden §4.5).

## Nachtrag 22.10.2026: Zweite Säule eingeengt

Von Jonas entschieden. Pesl et al. (2026) vergleichen Chunking auf OpenAPI-Spezifikationen und sind die nächste
verwandte Arbeit. Die zweite Säule („andere Domäne“) ist deshalb auf Fließtext-Anleitungen und -Referenzen für
Entwickler (Markdown/MDX) statt strukturierter API-Spezifikationen eingeengt. Begründung und Wortlaut:
[Forschungsdesign](../explanation/research-design.md#forschungslücke-und-abgrenzung-drei-säulen).

## Nachtrag 26.10.2026: Taiwo kein Beleg der Lücke

Von Jonas entschieden. `taiwo2026chunking` erscheint bei AIRCC, einem Verlag auf Beall's List, und trägt die
Forschungslücke nicht ([Literaturbasis](../reference/literature.md#kernquellen)). Die Aussage, kontrollierte
Chunking-Vergleiche lägen vor allem in fachfremden Domänen vor, stützt sich deshalb auf `gomezcabello2025chunking`
(klinisch) und, vorläufig bis zur Volltextprüfung, auf Pesl et al. (2026, OpenAPI); die Domäne „unternehmensinterne
technische Dokumente“ aus dem Exposé wird nicht mehr als belegt angeführt
([Forschungsdesign](../explanation/research-design.md#forschungslücke-und-abgrenzung-drei-säulen)). Die Entscheidung
selbst und ihre drei Säulen bleiben.

## Nachtrag 26.10.2026: Blogbeitrag entfällt, erste Säule neu

Von Jonas entschieden (Kapitelplanung der Arbeit). Die verwandten Arbeiten stehen in der Arbeit als Abschnitt der
theoretischen Fundierung, und für dieses Kapitel schließt das Thesis-Handbuch Blogbeiträge als Quellen aus (TH S. 11).
Der Praktiker-Blogbeitrag (FastAPI/Supabase/Stripe) wird darum nicht mehr erwähnt; die Konsequenz „wird in
‚Verwandte Arbeiten‘ kurz als informeller Vorläufer eingeordnet“ entfällt.

Die erste Säule („anderer Korpus“ als der des Blogbeitrags) verliert damit ihren Bezugspunkt und lautet neu: **ein dem
Antwortmodell weitgehend unbekannter Korpus, per Closed-Book-Prüfung kontrolliert.** Sprachmodelle kennen populäre
öffentliche Inhalte, und Retrieval hilft vor allem bei selten vorkommendem Wissen (`mallen2023whennot`,
`kandpal2023longtail`); Kontamination ist je Datensatz und Modell zu messen (`sainz2023contamination`). Auf einem
bekannten Korpus vermischen sich Retrieval-Effekte mit Modellwissen; die Messung auf Vue.js hat genau das gezeigt
([ADR 0038](0038-korpus-e2e.md)). Wortlaut: [Forschungsdesign](../explanation/research-design.md#forschungslücke-und-abgrenzung-drei-säulen).

Die Entscheidung selbst bleibt: die Lücke als entwicklerorientierte Open-Source-Dokumentation mit drei Säulen. Der
Nachtrag ersetzt nur den Bezugspunkt der ersten Säule, die schon zuvor auf e2e als Korpus zielte, so wie der Nachtrag
vom 22.10.2026 die zweite Säule eingeengt hat. Die Quellen waren nach [ADR 0018](0018-literaturbasis.md) vorläufig,
bis sie am Volltext geprüft waren. Pesl et al. (2026) ist am 26.10.2026 am Volltext geprüft: Die Studie misst nur das
Retrieval (S. 1527). Mallen et al., Kandpal et al. und Sainz et al. sind am 26.10.2026 geprüft und von Jonas am
27.10.2026 freigegeben ([Literaturbasis](../reference/literature.md#ergänzte-quellen-26102026)).
