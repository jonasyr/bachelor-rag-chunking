# 0002. Zitierstil: biblatex + biber, APA 7, `\parencite`

## Status

Angenommen (D2 im Leitfaden; Quelle: Chat, konkretisiert die Baseline)

## Kontext

- Der Leitfaden nennt für diese Entscheidung keinen Grund; sie stammt aus dem Chat (Leitfaden §2: Ground-Truth-Leitfaden, Juni 2026, in der Git-Historie).
- Die 15 Quellen der Literaturbasis sind im Exposé zitiert, ihre BibTeX-Einträge liegen im privaten PaperLab-Repo unter `expose/latex/main.bib` (Leitfaden §18).
- Form- und Stilregeln der Arbeit kommen aus der IU Source of Truth im PaperLab-Repo (Leitfaden §20).

## Entscheidung

Wir werden mit biblatex und biber im APA-7-Stil zitieren und dafür `\parencite` verwenden.

## Konsequenzen

- Neutral: Die Entscheidung betrifft nur den Text der Arbeit, nicht den Code in diesem Repo.
- Neutral: Umsetzung und Prüfung (`./paperlab check`) liegen im privaten PaperLab-Repo (Leitfaden §17, §20).
