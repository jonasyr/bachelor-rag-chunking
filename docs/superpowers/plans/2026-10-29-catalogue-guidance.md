# Schreibhilfen im Katalog-Editor – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Der Editor zeigt pro Slot Doppelungen und verwandte Abschnitte mit „Add“, Leitfragen je Klasse, einen
regelbasierten Typvorschlag und sperrt Speichern, bis alles erfüllt ist; auf Handy, Laptop und Desktop gleich klar.

**Architecture:** Reine Funktionen in `src/catalogue.py` (Doppelungen, Typvorschlag) und ein neues Modul
`src/catalogue_overlap.py` (vorab erstellte KI-Liste); `app/catalogue_page.py` setzt sie zusammen. Keine API, kein
Retrieval (ADR 0027, 0040).

**Tech Stack:** Python 3.12, Streamlit (`AppTest`), pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-29-catalogue-guidance-design.md`

## Global Constraints

- Parameter nur in `src/config.py` (AGENTS.md); neue Schlüssel in `docs/reference/configuration.md`.
- Editor ohne Netz und API; Tests ohne Netz.
- UI-Texte Englisch, Doku Deutsch; Conventional Commits ohne KI-Zeilen.
- Keine Hilfe darf Frage, Antwort, Typ oder Relevanz ohne Klick von Jonas setzen.
- Schwelle wörtliche Doppelung: 8 Wörter; höchstens 10 Treffer sichtbar, Rest hinter „Show all“.

## Review Focus

1. Abschnitt mit sehr vielen geteilten Stellen (Anbieter-Tabelle D036/D037): Kasten bleibt lesbar, ein Eintrag pro
   Abschnitt, nicht pro Stelle. → Test in Task 1 (`test_shared_passages_one_row_per_section`).
2. Gespeicherte Frage erneut öffnen: Typ vorausgewählt, Quote zählt sie nicht doppelt. → Test in Task 4.
3. `catalogue_overlap.csv` fehlt oder nennt unbekannte IDs: Editor läuft bzw. meldet die IDs. → Tests in Task 2 und 4.
4. Typvorschlag bei typografischem Apostroph („can’t“) und Großschreibung. → Test in Task 1.
5. Eingefrorener Katalog: Add-Knöpfe und Typvorschlag-Knopf gesperrt. → Test in Task 4.

---

### Task 1: Doppelungen und Typvorschlag in `catalogue.py`

**Files:**
- Modify: `src/config.py` (Katalogblock), `src/catalogue.py`
- Test: `tests/test_catalogue.py`

**Interfaces:**
- Produces: `catalogue.own_text(corpus, section) -> str`;
  `catalogue.shared_passages(corpus, section_id, min_words=CATALOGUE_DUPLICATE_MIN_WORDS) -> list[tuple[dict, str]]`
  (anderer Abschnitt, Ausschnitt der längsten geteilten Wortfolge, höchstens `CATALOGUE_DUPLICATE_EXCERPT_WORDS`
  Wörter, sonst mit „…“; sortiert in sections.jsonl-Reihenfolge; ohne Vorfahren/Nachkommen);
  `catalogue.suggest_type(question) -> tuple[str, str] | None` (Typ, gefundene Wendung).
- Config: `CATALOGUE_DUPLICATE_MIN_WORDS = 8`, `CATALOGUE_DUPLICATE_EXCERPT_WORDS = 24`,
  `QUESTION_TYPE_HINTS: tuple[tuple[str, str], ...]` (Typ, Regex) in der Spec-Reihenfolge comparative, limitation,
  procedural, conceptual, factual (factual nur am Anfang: `^(what|which|where|when|who|does|do|is|are|can)\b`),
  `CATALOGUE_CLASS_GUIDE: dict[str, dict]` mit `rule` (ein Satz) und `prompts` (2–3 inhaltsfreie Leitfragen) je
  Klasse aus `QUESTION_CLASSES`.

- [ ] **Step 1: Failing tests**

```python
def test_own_text_excludes_subsections(corpus): ...  # Elterntext enthält keinen Kindtext
def test_shared_passages_finds_text_shared_with_another_section(corpus_with_duplicate):
    hits = catalogue.shared_passages(corpus, "A#one")
    assert [s["section_id"] for s, _ in hits] == ["B#two"]
    assert "the same eight or more words" in hits[0][1]
def test_shared_passages_ignores_ancestors_and_descendants(...)
def test_shared_passages_one_row_per_section(...)  # zwei geteilte Stellen → ein Eintrag
def test_shared_passages_below_threshold_is_not_a_hit(...)  # 7 gleiche Wörter → []
@pytest.mark.parametrize("q,expected", [
    ("How do I install the plugin?", "procedural"),
    ("What is the difference between X and Y?", "comparative"),
    ("Why does e2e retry?", "conceptual"),
    ("Which models can’t use forced tool choice?", "limitation"),
    ("What does init write?", "factual"),
    ("Install it", None),
])
def test_suggest_type(q, expected): ...
def test_class_guide_covers_every_class():
    assert set(CATALOGUE_CLASS_GUIDE) == set(QUESTION_CLASSES)
```

Fixture `corpus_with_duplicate`: kleiner `Corpus` aus zwei Dokumenten in `tests/test_catalogue.py`, wie die
bestehenden Corpus-Fixtures in `conftest.py` gebaut.

- [ ] **Step 2:** `uv run pytest tests/test_catalogue.py -q` → FAIL (Namen fehlen).
- [ ] **Step 3:** Implementieren. `own_text` übernimmt die Kind-Ausschluss-Logik aus `find` (dort dann
  wiederverwenden). Doppelungen: Wort-n-Gramm-Index (`WORD_RE` über `own_text.lower()`) über alle Abschnitte,
  einmal je `Corpus` gebaut und am Objekt gemerkt; längste Folge durch Ausdehnen zusammenhängender Treffer.
  `suggest_type`: `’`→`'`, Kleinschreibung, erste passende Regel.
- [ ] **Step 4:** `uv run pytest tests/test_catalogue.py -q` → PASS.
- [ ] **Step 5:** Commit `feat(catalogue): Doppelungen und Typvorschlag für den Editor`.

### Task 2: `catalogue_overlap.csv` lesen und beim Freeze hashen

**Files:**
- Create: `src/catalogue_overlap.py`; Modify: `src/config.py`, `src/catalogue.py` (`freeze_catalogue`, CLI-Aufruf),
  `src/catalogue_store.py` (Pfad-Global)
- Test: `tests/test_catalogue_overlap.py`, `tests/test_freeze.py`

**Interfaces:**
- Config: `CATALOGUE_OVERLAP_FILE = DATA_EVAL / "catalogue_overlap.csv"`.
- Produces: `catalogue_overlap.OVERLAP_HEADER = ["section_id", "related_section_id", "note"]`;
  `read_overlap(path) -> dict[str, list[tuple[str, str]]]` (fehlende Datei → `{}`; doppelte Paare, Selbstbezug oder
  leere `note` → `ValueError`); `overlap_section_ids(rows) -> set[str]`.
  `store.CATALOGUE_OVERLAP_FILE` als Modul-Global wie die anderen Pfade.
  `freeze_catalogue(..., overlap_file: Path | None = None)` nimmt die Datei in `recorded` auf, wenn sie existiert.

- [ ] **Step 1: Failing tests** `test_missing_file_is_empty`, `test_rows_grouped_by_section`,
  `test_self_reference_is_an_error`, `test_duplicate_pair_is_an_error`, `test_empty_note_is_an_error`;
  in `test_freeze.py`: `test_overlap_file_is_recorded_when_present` (Name der Datei im Record wie bei
  `catalogue_review.csv`).
- [ ] **Step 2:** Tests laufen → FAIL.
- [ ] **Step 3:** Implementieren mit `atomic_csv.read_csv`.
- [ ] **Step 4:** `uv run pytest tests/test_catalogue_overlap.py tests/test_freeze.py -q` → PASS.
- [ ] **Step 5:** Commit `feat(catalogue): Überschneidungsliste lesen und beim Freeze festhalten`.

### Task 3: Leere `catalogue_overlap.csv` und Doku/ADR

**Files:**
- Create: `data/evaluation/catalogue_overlap.csv` (nur Kopfzeile), `docs/adr/0049-schreibhilfen-im-editor.md`
- Modify: `docs/adr/README.md`, `docs/adr/0031-stichprobenplan-und-ki-durchsicht.md` (Status: ergänzt durch 0049),
  `docs/reference/data-formats.md` (Abschnitt `catalogue_overlap.csv`, Freeze-Record, Dateitabelle),
  `docs/reference/configuration.md` (neue Schlüssel), `docs/how-to/build-the-question-catalogue.md` (Ablauf mit Kasten,
  Leitfragen, Typvorschlag), `docs/reference/question-catalogue.md` (KI-Hilfen)

ADR 0049 (Format wie 0046/0047): Kontext (Jonas ohne Korpuskenntnis, übersehene Abschnitte größte Gefahr), Entscheidung
(fünf Hilfen der Spec; Tailscale-Zugang nur im Tailnet, Bindung an `localhost` bleibt; Vorbereitungsblatt Block 1),
Konsequenzen (Offenlegung zählt die Liste; Liste hängt am Abschnitt, nicht an der Frage; kein Ranking, ADR 0027).

- [ ] **Step 1:** Dateien schreiben.
- [ ] **Step 2:** `uvx pre-commit run --all-files` → PASS.
- [ ] **Step 3:** Commit `docs(adr): 0049 Schreibhilfen im Katalog-Editor`.

### Task 4: Editor-Seite

**Files:**
- Modify: `app/catalogue_page.py`, `app/ui_theme.py`
- Test: `tests/test_catalogue_editor.py`

**Interfaces:**
- Consumes: Task 1 und 2.
- Produces (in `catalogue_page.py`): `type_quota_left(questions, qtype, qid) -> int`;
  `save_blocker(question, answer, qtype, items, questions, qid) -> str | None` (erster Grund oder `None`);
  `also_covered(corpus, seed, overlap) -> list[dict]` mit Schlüsseln `section`, `kind` (`"same text"`/`"related"`),
  `detail` (Ausschnitt bzw. `note`); wörtliche zuerst, dann verwandte, je Abschnitt einmal.

Aufbau: Zeile 1 Titel + Slotwahl; Zeile 2 voller Breite: Expander „How to write a {class} question“ (offen) mit
`rule` und `prompts`; Zeile 3 zwei Spalten: links Abschnitt, darunter Kasten „Also covered elsewhere“ (Keys
`add_dup_<section_id>`, Expander mit Abschnittstext, Badge „added“/„inside an added section“, „Show all“ ab 11);
rechts Frage, Typ (`index=None`, Platzhalter „Choose a type“; gespeicherte Frage: gespeicherter Typ), Vorschlag
„Looks like {type} (“{phrase}”)“ mit Knopf `use_type`, offene Plätze je Typ als Zeile, Antwort, Notizen, relevante
Abschnitte, Prüfungen, Speichern (gesperrt mit Grund), Überspringen; Zeile 4 links Suche wie bisher.
`unknown_sections` berücksichtigt `overlap_section_ids`. Unter 640 px: alles einspaltig in dieser Reihenfolge,
Abschnitt höchstens 60vh, Touch-Ziele ≥ 44 px.

- [ ] **Step 1: Failing tests**

```python
def test_type_starts_empty_and_save_is_blocked(app): ...  # Button save disabled, Grund "Choose a type"
def test_suggested_type_is_set_only_on_click(app): ...    # nach Frage "How do I …": selectbox None; Klick use_type → procedural
def test_add_from_also_covered(app_with_overlap): ...     # Klick add_dup_<id> → Abschnitt in Liste, gespeichert in ground_truth
def test_full_type_quota_blocks_save(app, monkeypatch): ...  # QUESTION_TYPES factual=0 → Grund nennt Quote
def test_saved_question_keeps_its_type_and_quota(app): ...
def test_unknown_overlap_section_is_reported(app): ...
def test_frozen_disables_add_and_use_type(app): ...
```

- [ ] **Step 2:** `uv run pytest tests/test_catalogue_editor.py -q` → FAIL.
- [ ] **Step 3:** Implementieren; bestehende Tests anpassen, die den Typ vorausgesetzt haben.
- [ ] **Step 4:** `uv run pytest -q` → PASS; `uvx pre-commit run --all-files` → PASS.
- [ ] **Step 5:** Commit `feat(app): Schreibhilfen im Katalog-Editor`.

### Task 5: UI-Prüfung

- [ ] **Step 1:** Editor läuft (`localhost:8501`); `playwright-cli` bei 320, 768, 1280 px: Slot S02 öffnen, Frage
  tippen, Typvorschlag übernehmen, Abschnitt aus dem Kasten hinzufügen, Konsole lesen. Screenshots ins Scratchpad.
  Speichern nicht auslösen (echte Daten).
- [ ] **Step 2:** Skill `impeccable` `audit`, dann `polish`; Funde in `ui_theme.py`/`catalogue_page.py` beheben,
  Schritt 1 wiederholen.
- [ ] **Step 3:** Commit `style(app): Feinschliff Katalog-Editor`.

### Task 6: Überschneidungsliste füllen (Inhalt, Claude)

- [ ] **Step 1:** Für jeden Abschnitt aus `catalogue_plan.csv` (Status open/used/reserve) den Korpus mit
  `catalogue.py find`/`show` nach Abschnitten mit gleichem Inhalt absuchen (nicht über Chunks), Zeilen mit
  einsatziger `note` (was beide gemeinsam haben, keine Frageidee); wörtliche Doppelungen (Task 1) dürfen fehlen.
- [ ] **Step 2:** Stichprobe gegenlesen (10 Abschnitte, ob `note` inhaltsneutral ist), Editor lädt ohne Fehler.
- [ ] **Step 3:** Commit `chore(catalogue): Überschneidungsliste für Plan- und Reserveabschnitte`.

### Task 7: PR

- [ ] Branch pushen, PR mit Zusammenfassung, `codex-reviewer`-Review, Befunde beheben; Merge erst nach Jonas' OK.
  Katalogdaten (Q001, Vorbereitungsblatt) **nicht** in diesen PR; sie kommen mit Block 1.
