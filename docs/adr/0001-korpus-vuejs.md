# ADR 0001: Dokumentkorpus: Vue.js-Dokumentation

- **Status:** angenommen (D1, verbindlich)
- **Quelle:** Chat; Verhältnis zur Baseline: ersetzt FastAPI
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §3, §5

## Kontext

Ein Praktiker-Blogbeitrag (Mai 2026) hat ein nahezu identisches Setup auf FastAPI/Supabase/Stripe bereits umgesetzt (eingefrorenes QA-Set, eine Variable pro Experiment, RAGAS, überschriftenbasiertes Chunking).

## Entscheidung

Korpus ist die offizielle Vue-3-Dokumentation (`vuejs/docs`, Markdown). FastAPI-spezifische Beispiele entfallen; der Snapshot liegt unter `data/raw/vue_docs_snapshot/`.

## Folgen

Korpus und Domäne grenzen sich klar ab, die Fragetyp-Vielfalt bleibt erhalten. Der genaue Ausschnitt (Pfade, Commit) ist noch offen, siehe Leitfaden §19.
