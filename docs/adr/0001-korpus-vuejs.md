# 0001. Dokumentkorpus: Vue.js-Dokumentation

## Status

Angenommen (D1 im Leitfaden; Quelle: Chat, ersetzt FastAPI aus der Baseline)

## Kontext

- Die Baseline sah die FastAPI-Dokumentation als Korpus vor ([Leitfaden §3](../Ground_Truth_Projektleitfaden.md#3-was-sich-gegenüber-der-ursprünglichen-baseline-geändert-hat)).
- Ein Praktiker-Blogbeitrag (Mai 2026) hat ein nahezu identisches Setup bereits umgesetzt: FastAPI/Supabase/Stripe, eingefrorenes QA-Set, eine Variable pro Experiment, RAGAS, überschriftenbasiertes Chunking (Leitfaden §3).
- Die Vue.js-Dokumentation ist entwicklerorientiert, liegt im Quellrepository durchgängig als Markdown (VitePress) vor, ist öffentlich und stabil und erlaubt viele Fragetypen (Leitfaden §5.1).

## Entscheidung

Wir werden die offizielle Vue-3-Dokumentation (`vuejs/docs`, Markdown) als Korpus verwenden.
Wir werden alle FastAPI-spezifischen Beispiele durch Vue-Beispiele ersetzen und den Snapshot unter `data/raw/vue_docs_snapshot/` ablegen.

## Konsequenzen

- Gut: Korpus und Domäne grenzen sich klar vom Blogbeitrag ab, die Fragetyp-Vielfalt bleibt erhalten (Leitfaden §3).
- Gut: Markdown lässt sich sauber als Snapshot fixieren und parsen (Leitfaden §5.1).
- Schlecht: Manche Vue-Abschnitte sind lang und erzeugen bei C3 große Chunks (Leitfaden §6).
- Neutral: Der genaue Ausschnitt (Pfade, Commit) ist noch offen, siehe [Leitfaden §19](../Ground_Truth_Projektleitfaden.md#19-offene-entscheidungen--vor-beginn-zu-bestätigen); der Pfad steht als `DATA_RAW` in [`src/config.py`](../../src/config.py).
