# Ergebnisse in die Bachelorarbeit übernehmen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Das private Repo PaperLab bindet dieses Repo als Git-Submodul ein
(`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code/`); die Arbeit zitiert den dort festgehaltenen
Commit (Entscheidung im privaten Repo PaperLab: `docs/adr/0007-thesis-code-als-submodul.md`).

1. `uv run python src/analyse.py` schreibt die Tabellen als LaTeX nach `output/tables/*.tex` und die Abbildungen als
   PDF nach `output/figures/*.pdf` ([Experiment durchführen](run-the-experiment.md), Inhalte:
   [Evaluation](../reference/evaluation.md#visualisierungen)). PDFs sind sonst gitignored;
   `output/figures/*.pdf` ist per Ausnahme in `.gitignore` versioniert.
2. Auf einem Branch committen, pushen und einen Pull Request öffnen ([Konventionen](../../AGENTS.md#conventions)).
3. Review durch Codex (`@codex review` auf GitHub, ersatzweise der Agent `.claude/agents/codex-reviewer.md`);
   gemergt wird erst, wenn Jonas zustimmt.
4. Im Ordner der Arbeit in PaperLab (`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/`, dort liegt das
   Submodul als `code/`) den Submodul-Zeiger auf den Merge-Commit auf `main` setzen:
   `git -C code switch main && git -C code pull`, dann `git add code && git commit -m "chore(thesis): Code auf <hash>"`.
5. In der Arbeit direkt einbinden, ohne Kopie: `\input{code/output/tables/…}`, `\includegraphics{code/output/figures/…}`.
   Die Abbildungen haben Endgröße (17 cm): ohne Skalieren einbinden, den Titel mit `\caption` darüber setzen und
   darunter `\source{Eigene Darstellung.}`. `./paperlab check` prüft sie (u. a. Schrift, Ausrichtung, Abstände) und
   meldet ein veraltetes PDF, wenn dort etwas neuer ist.
