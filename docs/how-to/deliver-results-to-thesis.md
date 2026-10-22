# Ergebnisse in die Bachelorarbeit übernehmen

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Experiment durchführen](run-the-experiment.md), [Evaluation](../reference/evaluation.md#visualisierungen), [Datenformate](../reference/data-formats.md#auswertung-output)*

Das private Repo PaperLab bindet dieses Repo als Git-Submodul ein
(`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code/`); die Arbeit zitiert den dort festgehaltenen
Commit (Entscheidung im privaten Repo PaperLab: `docs/adr/0007-thesis-code-als-submodul.md`).

Voraussetzung: der Hauptlauf ist vollständig ([Experiment durchführen](run-the-experiment.md)); `analyse.py` bricht
sonst ab ([Skripte und Optionen](../reference/tooling.md#skripte-und-optionen)).

1. `uv run python src/analyse.py` schreibt nach `output/`: die Tabellen als LaTeX (`output/tables/*.tex`), die
   Abbildungen als PDF (`output/figures/*.pdf`), `output/analysis.json` und, wenn eine abgeschlossene Zweitbewertung
   vorliegt, `output/second_rater_disagreements.csv` (Formate: [Datenformate](../reference/data-formats.md#auswertung-output),
   Inhalte: [Evaluation](../reference/evaluation.md#visualisierungen)). Alle vier werden versioniert; PDFs sind sonst
   gitignored, `output/figures/*.pdf` ist per Ausnahme in `.gitignore` freigegeben. Ohne PaperLab-Checkout vorher
   `PAPERLAB_FONTS` setzen ([Umgebungsvariablen](../reference/tooling.md#umgebungsvariablen)).
2. `git add output/` auf einem Branch committen, pushen und einen Pull Request öffnen; Review und Merge nach den
   [Konventionen](../../AGENTS.md#conventions).
3. In PaperLab im Ordner der Arbeit (`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/`) den
   Submodul-Zeiger auf den Commit setzen, den der Squash-Merge auf `main` erzeugt hat: `git -C code switch main && git -C code pull`, dann
   `git add code && git commit -m "chore(thesis): Code-Submodul auf <PR-Titel> (#<n>) angehoben"`.
4. Einbinden in die Arbeit regelt PaperLab: Kapitel 4 (`sections/04_ergebnisse.tex`) bindet Tabellen und Abbildungen
   über `\ergebnistabelle`/`\ergebnisabbildung` ein, ergänzende in Anhang B (`sections/99_anhang.tex`); Abbildungen
   in Endgröße ohne Skalieren; danach `./paperlab check`.
