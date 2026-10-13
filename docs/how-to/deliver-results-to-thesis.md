# Ergebnisse in die Bachelorarbeit übernehmen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Das private Repo PaperLab bindet dieses Repo als Git-Submodul ein
(`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code/`); die Arbeit zitiert den dort festgehaltenen
Commit (Entscheidung im privaten Repo PaperLab: `docs/adr/0007-thesis-code-als-submodul.md`).

1. Tabellen als LaTeX nach `output/tables/*.tex` schreiben, Abbildungen als PDF nach `output/figures/*.pdf`
   (Ordner und Pfad in `src/config.py` entstehen mit der ersten Auswertung).
2. Hier committen und pushen.
3. In PaperLab den Submodul-Zeiger committen: `git -C code push && git add code && git commit -m "chore(thesis): Code auf <hash>"`.
4. In der Arbeit direkt einbinden, ohne Kopie: `\input{code/output/tables/…}`, `\includegraphics{code/output/figures/…}`.
   `./paperlab check` meldet ein veraltetes PDF, wenn dort etwas neuer ist.
