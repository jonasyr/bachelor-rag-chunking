# 0011. Forschungslücke: entwicklerorientierte Open-Source-Dokumentation

## Status

Angenommen (D11 im Leitfaden; Quelle: Chat, ergänzt die Baseline); „Öl und Gas“ im Kontext ist das Beispiel aus der
Quelle `taiwo2026chunking`; maßgeblich für die Domäne ist der Wortlaut des Exposés, „unternehmensinterne technische
Dokumente“. Zweite Säule eingeengt am 22.10.2026: [Nachtrag](#nachtrag-22102026-zweite-säule-eingeengt)

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
