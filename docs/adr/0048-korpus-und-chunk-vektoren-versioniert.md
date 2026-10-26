# 0048. Korpus-Snapshot und Chunk-Vektoren versioniert

## Status

Angenommen (26.10.2026; von Jonas entschieden; ändert die Archivierung der Vektordateien in
[ADR 0024](0024-referenzvektoren-und-exakte-suche.md) und die Konsequenz „Chunk-Vektoren bleiben ignoriert“ in
[ADR 0045](0045-retrieval-ergebnisse-versioniert.md))

## Kontext

- Die Arbeit soll für die Begutachtung nachvollziehbar sein: Wer das Repo klont, soll das Retrieval und die Auswertung
  ohne API-Schlüssel wiederholen und mit den versionierten Ergebnissen vergleichen können.
- Versioniert waren bisher die Fragevektoren, die Retrieval-Ergebnisse, die Antworten und die Bewertungen
  ([ADR 0033](0033-antwortmodell.md), [ADR 0045](0045-retrieval-ergebnisse-versioniert.md)). Ignoriert waren der
  Korpus-Snapshot (`data/raw/e2e_docs_snapshot/`, 62 Dateien, 1,1 MB) und die Chunk-Vektoren
  (`data/processed/embeddings_c1|c2|c3|k1.npz`, zusammen 54 MB); ADR 0024 sah vor, die Vektoren für die DOI gesondert zu
  sichern, ohne festzulegen wie.
- Die Chunk-Vektoren lässt kein Lauf bitgleich neu entstehen: neue Vektoren kosten API-Aufrufe und weichen ab
  (Modellstand-Prüfung, [ADR 0024](0024-referenzvektoren-und-exakte-suche.md)). Mit den gespeicherten Vektoren baut
  `embed.py` den Chroma-Index ohne API-Aufruf neu (geprüft am 26.10.2026 auf einer frischen Kopie ohne `.env`: 0 Tokens,
  `api_called=False`), und die exakte Suche liefert dasselbe Top-5.
- Der Snapshot wird von `tester-army/e2e` geholt; verschwindet das Repository oder der Commit, lässt sich der Korpus
  nicht mehr herstellen. Die Seiten stehen unter der Apache License 2.0, die die Weitergabe mit Lizenztext und
  NOTICE-Hinweis erlaubt.
- Aus dem Snapshot entstehen `documents.jsonl`, `sections.jsonl` und `chunks_*.jsonl` bitgleich neu (geprüft am
  26.10.2026 auf einer frischen Kopie: alle sechs Dateien mit identischer SHA-256); jeder spätere Schritt prüft ihre
  Prüfsummen ohnehin.
- Die Vektoren werden einmal erzeugt; die Datei je Strategie liegt unter 17 MB und damit unter den Grenzen von GitHub.

## Entscheidung

Wir werden den Korpus-Snapshot `data/raw/e2e_docs_snapshot/` unverändert und die Chunk-Vektoren
`data/processed/embeddings_c1.npz`, `embeddings_c2.npz`, `embeddings_c3.npz` und `embeddings_k1.npz` versionieren.
Ignoriert bleiben alle Dateien, die daraus bitgleich neu entstehen (`documents.jsonl`, `sections.jsonl`,
`section_index.md`, `chunks_*.jsonl`, `chroma_db/`). Kein pre-commit-Hook darf den Snapshot verändern; die CI baut die
Korpusdateien aus dem Snapshot neu, damit die Integrationstests der Korpusdateien und Vektoren auf jedem Pull Request
laufen.

## Konsequenzen

- Positiv: Retrieval und Auswertung sind auf jedem Klon ohne API-Schlüssel und ohne Netz wiederholbar
  ([Ergebnisse nachvollziehen](../how-to/reproduce-the-results.md)); ein zweiter Rechner braucht nur `git pull`
  ([Auf zwei Rechnern arbeiten](../how-to/work-on-two-machines.md)); das DOI-Archiv enthält alles ohne gesonderte
  Sicherung.
- Positiv: Die CI prüft bei jedem Pull Request, dass Snapshot, Chunks und Vektoren zusammenpassen.
- Negativ: Etwa 55 MB Binärdaten in der Git-Historie; ein erneutes Einbetten käme noch einmal hinzu.
- Neutral: Der Korpus wird weitergegeben; Lizenztext und NOTICE stehen im [README](../../README.md#license).
  `snapshot.py` bleibt der Weg, den Snapshot gegen das Original zu prüfen; es schreibt dieselben Bytes.
