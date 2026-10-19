# Catalogue quotas and sampling plan on e2e Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The catalogue tools use the 15 e2e areas (slots, reserve, minimums, stopwords), and the e2e sampling plan is drawn once while the Vue plan is archived.

**Architecture:** Only configuration values change; `catalogue_plan.py` and `catalogue.py` already read the dicts generically. The editor drops its Vue label map. The plan file is moved with `git mv` and the existing `catalogue.py plan` command draws the new one. ADR 0039 records the decision.

**Tech Stack:** Python 3.12, uv, pytest, Streamlit 1.58 (editor), ruff via pre-commit.

**Spec:** `docs/superpowers/specs/2026-10-18-e2e-catalogue-quotas-design.md`

## Global Constraints

- All parameters only in `src/config.py`; area keys exactly `CORPUS_AREAS`, in that order.
- Slots = reserve = minimum per area: Get started 2, Platforms 2, Features 2, Models and agents 2, Run in CI 2, Hosted browsers and devices 2, Extend 1, Deep dive 3, Migrate 4, Test API 7, Project 12, Web 2, Mobile 2, Engine contract 4, Examples 1 (sum 48).
- `CATALOGUE_SEED` stays `20261014`; `"e2e"` replaces `"v"` and `"vue"` in `CATALOGUE_STOPWORDS`.
- The Vue plan is moved unchanged to `data/evaluation/archive_vue/catalogue_plan.csv`; the e2e plan is written once by `catalogue.py plan`, never edited by hand.
- Tests never call the OpenAI API. Conventional Commits, German subjects, no AI attribution. Never commit `.env`.
- Claude writes no question, reference answer, relevance judgement or key point.
- Docs in German (repo convention), code and comments in English.

## Review Focus

- Area names with spaces ("Hosted browsers and devices", "Models and agents") in the plan CSV and the hash: must round-trip through `read_plan` unchanged — covered by the integration test `test_committed_plan_matches_a_fresh_draw` (Task 2).
- An area whose candidate pool is smaller than slots + reserve (Examples has 3, Web and Mobile 9): `draw_area` must not silently draw fewer — covered by `test_every_area_has_enough_candidates` (Task 2).
- Editor sidebar and slot header with e2e area names: no `KeyError` from a leftover Vue label map — covered by the browser check in Task 1.
- A future edit that adds an area to one dict but not the others — covered by `test_area_quotas_follow_the_corpus_areas` (Task 1).
- The paraphrase rule on questions naming the product ("e2e") — covered by `test_product_name_is_not_a_shared_word` (Task 1).

---

### Task 1: e2e area quotas, stopwords and editor labels

**Files:**
- Modify: `src/config.py:181-200` (AREA_MIN_QUESTIONS, CATALOGUE_AREA_SLOTS, CATALOGUE_RESERVE and comments), `src/config.py:222-230` (CATALOGUE_STOPWORDS)
- Modify: `app/catalogue_page.py:31,74,166` (AREA_NAMES)
- Test: `tests/test_catalogue_plan.py:27-29`, `tests/test_catalogue.py:120-121,354-355`

**Interfaces:**
- Consumes: `config.CORPUS_AREAS` (tuple of the 15 area names), `config.QUESTION_CLASSES`.
- Produces: `CATALOGUE_AREA_SLOTS`, `CATALOGUE_RESERVE`, `AREA_MIN_QUESTIONS` as `dict[str, int]` keyed by the area names in `CORPUS_AREAS` order (Task 2 draws with them).

- [ ] **Step 1: Write the failing tests**

In `tests/test_catalogue_plan.py` replace `test_config_slots_match_the_catalogue` and extend the config import:

```python
from config import (
    AREA_MIN_QUESTIONS,
    CATALOGUE_AREA_SLOTS,
    CATALOGUE_RESERVE,
    CORPUS_AREAS,
    QUESTION_CLASSES,
)
```

```python
def test_config_slots_match_the_catalogue():
    assert sum(CATALOGUE_AREA_SLOTS.values()) == sum(QUESTION_CLASSES.values())
    assert set(CATALOGUE_RESERVE) == set(CATALOGUE_AREA_SLOTS)


def test_area_quotas_follow_the_corpus_areas():
    # ADR 0039: slots by token share, at least 1; reserve and minimum equal the slots
    for quotas in (CATALOGUE_AREA_SLOTS, CATALOGUE_RESERVE, AREA_MIN_QUESTIONS):
        assert list(quotas) == list(CORPUS_AREAS)
    assert CATALOGUE_RESERVE == CATALOGUE_AREA_SLOTS
    assert AREA_MIN_QUESTIONS == CATALOGUE_AREA_SLOTS
    assert min(CATALOGUE_AREA_SLOTS.values()) >= 1
    assert CATALOGUE_AREA_SLOTS["Project"] == 12 and CATALOGUE_AREA_SLOTS["Test API"] == 7
```

In `tests/test_catalogue.py` replace the two Vue-specific tests:

```python
def test_content_words_drop_stopwords_and_punctuation():
    assert content_words("How do I use expect() in e2e?") == {"use", "expect"}
```

```python
def test_product_name_is_not_a_shared_word():
    assert shared_words("How does e2e retry a step?", ["e2e test lifecycle"]) == []
```

(`test_single_letter_directive_prefix_is_not_a_shared_word` is deleted: `v-` directives do not exist in the e2e corpus.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_plan.py::test_area_quotas_follow_the_corpus_areas tests/test_catalogue.py::test_content_words_drop_stopwords_and_punctuation tests/test_catalogue.py::test_product_name_is_not_a_shared_word -q`
Expected: 3 failed (keys are `api`/`style-guide`/`guide`; `e2e` is not a stopword).

- [ ] **Step 3: Change the configuration**

In `src/config.py` replace the comment and value of `AREA_MIN_QUESTIONS`:

```python
# Minimum number of questions with a relevant section in an area; a question counts for every area
# it touches (D29). Equal to the area's slots (ADR 0039).
AREA_MIN_QUESTIONS = {
    "Get started": 2, "Platforms": 2, "Features": 2, "Models and agents": 2, "Run in CI": 2,
    "Hosted browsers and devices": 2, "Extend": 1, "Deep dive": 3, "Migrate": 4, "Test API": 7,
    "Project": 12, "Web": 2, "Mobile": 2, "Engine contract": 4, "Examples": 1,
}  # fmt: skip
```

and the slots/reserve block (drop the line `# Vue areas until step 4 sets the e2e slots (plan.md)`):

```python
# Slots per area (ADR 0039): share of the corpus tokens, every area at least 1, the rest by largest
# remainder; written as literals so a corpus change cannot shift them. Sums to the catalogue size.
CATALOGUE_AREA_SLOTS = {
    "Get started": 2, "Platforms": 2, "Features": 2, "Models and agents": 2, "Run in CI": 2,
    "Hosted browsers and devices": 2, "Extend": 1, "Deep dive": 3, "Migrate": 4, "Test API": 7,
    "Project": 12, "Web": 2, "Mobile": 2, "Engine contract": 4, "Examples": 1,
}  # fmt: skip
CATALOGUE_RESERVE = dict(CATALOGUE_AREA_SLOTS)  # replacement sections per area (ADR 0039)
```

In `CATALOGUE_STOPWORDS`, change the line

```python
    "to", "under", "v", "vue", "was", "we", "were", "what", "when", "where", "which", "who", "whom",
```

so that `"e2e"` sits in alphabetical order after `"done"` and `"v"`, `"vue"` are gone:

```python
    "can", "could", "did", "do", "does", "done", "e2e", "for", "from", "had", "has", "have", "he",
```

```python
    "to", "under", "was", "we", "were", "what", "when", "where", "which", "who", "whom",
```

- [ ] **Step 4: Remove the Vue label map from the editor**

In `app/catalogue_page.py` delete line 31 (`AREA_NAMES = {...}`) and replace both uses by the area name itself:

```python
            f"{a} {sum(1 for v in used.values() if v == a)} of at least {n}"
```

```python
        f"<span>{row['area']}, {row['class']}</span></h2>"
```

Run: `grep -n "AREA_NAMES\|style-guide\|\"guide\"" app/*.py src/*.py`
Expected: no output.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `set -o pipefail; uv run pytest -q 2>&1 | tail -3`
Expected: all passed (the corpus integration tests run, the snapshot exists locally).

- [ ] **Step 6: Browser check of the editor**

The editor reads `catalogue_plan.csv`; until Task 2 it is the Vue plan, whose areas are no longer in the config. Do the browser check after Task 2, Step 4 (listed there). Here only check that the module imports:

Run: `uv run python -c "import sys; sys.path[:0]=['src','app']; import catalogue_page"`
Expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
git add src/config.py app/catalogue_page.py tests/test_catalogue_plan.py tests/test_catalogue.py
git commit -m "feat(catalogue): Bereichsquoten und Stoppwörter für e2e"
```

---

### Task 2: Archive the Vue plan, draw the e2e plan

**Files:**
- Move: `data/evaluation/catalogue_plan.csv` → `data/evaluation/archive_vue/catalogue_plan.csv`
- Create (by the tool): `data/evaluation/catalogue_plan.csv`
- Test: `tests/test_corpus_integration.py` (two tests appended)
- Modify: `docs/reference/experiment-record.md` (new section after "Embedding (e2e)")

**Interfaces:**
- Consumes: the Task 1 dicts; `catalogue_plan.candidates(corpus) -> dict[str, list[dict]]`, `draw_plan(corpus) -> list[dict]`, `read_plan(path=CATALOGUE_PLAN_FILE) -> list[dict]`, `plan_integrity(rows, fresh) -> list[str]`; `catalogue.load_corpus()` (defaults to the processed files).
- Produces: the versioned e2e plan (48 slot rows + 48 reserve rows).

- [ ] **Step 1: Write the failing integration tests**

Append to `tests/test_corpus_integration.py` (add `CATALOGUE_AREA_SLOTS`, `CATALOGUE_PLAN_FILE`, `CATALOGUE_RESERVE` to the config import and `from catalogue_plan import candidates, draw_plan, plan_integrity, read_plan`):

```python
@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_every_area_has_enough_candidates():
    pools = candidates(load_corpus())
    for area in CORPUS_AREAS:
        assert len(pools[area]) >= CATALOGUE_AREA_SLOTS[area] + CATALOGUE_RESERVE[area], area


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_committed_plan_matches_a_fresh_draw():
    corpus = load_corpus()
    fresh = draw_plan(corpus)
    assert draw_plan(corpus) == fresh  # deterministic
    rows = read_plan(CATALOGUE_PLAN_FILE)
    assert [r["area"] for r in rows if r["slot_id"]] == [
        a for a in CORPUS_AREAS for _ in range(CATALOGUE_AREA_SLOTS[a])
    ]
    assert plan_integrity(rows, fresh) == []
```

- [ ] **Step 2: Run them to verify the plan test fails**

Run: `uv run pytest tests/test_corpus_integration.py -k "enough_candidates or fresh_draw" -q`
Expected: `test_every_area_has_enough_candidates` passes, `test_committed_plan_matches_a_fresh_draw` fails (the committed plan is the Vue draw: areas `api`, …).

- [ ] **Step 3: Archive the Vue plan**

```bash
mkdir -p data/evaluation/archive_vue
git mv data/evaluation/catalogue_plan.csv data/evaluation/archive_vue/catalogue_plan.csv
sha256sum data/evaluation/archive_vue/catalogue_plan.csv
git show HEAD:data/evaluation/catalogue_plan.csv | sha256sum
```

Expected: both checksums equal (moved unchanged).

- [ ] **Step 4: Draw the e2e plan and check it in the editor**

Run: `uv run python src/catalogue.py plan`
Expected: `96 plan rows -> …/data/evaluation/catalogue_plan.csv`.

Run: `head -3 data/evaluation/catalogue_plan.csv; grep -c ',S' data/evaluation/catalogue_plan.csv; sha256sum data/evaluation/catalogue_plan.csv`
Expected: header `area,draw,section_id,slot_id,class,status,skip_reason,question_id`, first row area `Get started` with slot `S01`; 48 slot rows; note the checksum for the record.

Browser check: restart the editor (stop the running background Streamlit task first, then `uv run streamlit run app/catalogue_editor.py --server.address localhost --server.port 8501 --server.headless true` in the background) and with `playwright-cli` open `http://localhost:8501` at 1280 and 320 px wide: the slot header shows `Get started, <class>`, the sidebar lists all 15 areas as `<name> 0 of at least <n>`, the console has no errors. Save screenshots to the scratchpad.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `set -o pipefail; uv run pytest -q 2>&1 | tail -3`
Expected: all passed.

- [ ] **Step 6: Record the draw**

Add after the section "## Embedding (e2e)" (before "## Snapshot (Vue.js, bis 18.10.2026)") of `docs/reference/experiment-record.md`, with the real checksum from Step 4:

```markdown
## Stichprobenplan (e2e)

| Feld | Wert |
|---|---|
| Gezogen | 18.10.2026, `uv run python src/catalogue.py plan`, Seed `20261014` ([ADR 0039](../adr/0039-stichprobenplan-e2e.md)) |
| Datei | `data/evaluation/catalogue_plan.csv`, 48 Slots und 48 Reserveabschnitte, SHA-256 `<checksum from Step 4>` |
| Slots je Bereich | nach Tokenanteil, mindestens 1: [Korpus](corpus.md#bereiche) |
| Vue-Plan | unverändert archiviert unter `data/evaluation/archive_vue/catalogue_plan.csv` (gezogen 14.10.2026, nie benutzt) |
```

- [ ] **Step 7: Commit**

```bash
git add data/evaluation tests/test_corpus_integration.py docs/reference/experiment-record.md
git commit -m "chore(data): Stichprobenplan auf e2e gezogen, Vue-Plan archiviert"
```

---

### Task 3: ADR 0039 and documentation

**Files:**
- Create: `docs/adr/0039-stichprobenplan-e2e.md`
- Modify: `docs/adr/README.md`, `docs/adr/0029-fragetypen-und-konstruktionsklassen.md` (Status line), `docs/adr/0031-stichprobenplan-und-ki-durchsicht.md` (Status line), `docs/reference/corpus.md`, `docs/reference/configuration.md:113,126-127,134`, `docs/how-to/build-the-question-catalogue.md:24-25`, `docs/plan.md:28-33`, `.serena/memories/pipeline.md:30`

**Interfaces:**
- Consumes: the values of Task 1 and the plan of Task 2.
- Produces: documentation only.

- [ ] **Step 1: Write ADR 0039**

`docs/adr/0039-stichprobenplan-e2e.md`:

```markdown
# 0039. Stichprobenplan und Bereichsquoten auf e2e

## Status

Angenommen (18.10.2026; ersetzt die Slotzahlen von [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md) und die
Bereichsuntergrenzen von [ADR 0029](0029-fragetypen-und-konstruktionsklassen.md); folgt aus
[ADR 0038](0038-korpus-e2e.md))

## Kontext

- Mit dem Korpuswechsel (ADR 0038) gibt es 15 Bereiche statt drei: die Gruppen der Navigation `docs.json`
  ([Korpus](../reference/corpus.md#bereiche)). Die Vue-Quoten (12 API, 3 Style Guide, 33 Guide) folgten den
  Tokenanteilen; der größte Bereich (Guide, 71 %) hatte keine Untergrenze und war Puffer.
- Auf e2e hat kein Bereich eine solche Mehrheit: Project 24,4 %, Test API 14,8 %, alle übrigen unter 9 %; Examples
  (eine Seite, 547 Tokens) 0,2 %.
- Der Vue-Plan (`catalogue_plan.csv`, gezogen 14.10.2026) war versioniert, aber nie benutzt: Es gab noch keine Frage.
- ADR 0031 legt den Seed als nie getunt fest; ein neuer Seed erlaubte, eine Ziehung auszuwählen.

## Entscheidung

Wir werden die 48 Slots nach dem Tokenanteil der Bereiche nach dem Preprocessing verteilen, jeder Bereich mindestens
einen Slot, die übrigen 33 nach größtem Rest über die Anteile oberhalb eines Slots: Get started 2, Platforms 2,
Features 2, Models and agents 2, Run in CI 2, Hosted browsers and devices 2, Extend 1, Deep dive 3, Migrate 4,
Test API 7, Project 12, Web 2, Mobile 2, Engine contract 4, Examples 1.
Wir werden je Bereich so viele Reserveabschnitte ziehen wie Slots und in jedem Bereich mindestens so viele Fragen mit
einem relevanten Abschnitt verlangen wie Slots (eine Frage zählt für jeden berührten Bereich, ADR 0029).
Wir werden den Seed `20261014`, die Ziehung, die Sprunggründe und die KI-Durchsicht aus ADR 0031 unverändert
übernehmen; in den Stoppwörtern ersetzt `e2e` die Vue-Einträge `v` und `vue`.
Wir werden den Vue-Plan unverändert nach `data/evaluation/archive_vue/` verschieben und den e2e-Plan einmal unter dem
bisherigen Pfad ziehen ([Experiment-Protokoll](../reference/experiment-record.md#stichprobenplan-e2e)).

## Konsequenzen

- Positiv: Jeder Bereich kommt im Katalog vor, die Verteilung folgt derselben Regel wie bei Vue und ist in einem Satz
  begründbar; die Zahlen stehen als Literale in `src/config.py` und verschieben sich nicht mit dem Korpus.
- Negativ: Examples bekommt einen Slot für eine kleine Seite; eine Frage, die ihren Bereich verlässt, muss umgeschrieben
  oder anders annotiert werden, weil kein Bereich als Puffer dient.
- Neutral: Die Vorgabe „nie überschreiben“ bleibt erhalten: Der Vue-Plan ist archiviert, nicht ersetzt.
```

- [ ] **Step 2: Link and update the other ADRs**

In `docs/adr/README.md` add after the 0038 row:

```markdown
| [0039](0039-stichprobenplan-e2e.md) | Stichprobenplan und Bereichsquoten auf e2e | Angenommen |
```

and change "ADR 0019–0038" in line 4 to "ADR 0019–0039". In the 0029 and 0031 rows append to the status cell `; Bereichsquoten ersetzt durch 0039` (0029) and `; Slotzahlen ersetzt durch 0039` (0031). In the Status sections of `0029-…md` and `0031-…md` append the same sentence with a link `[ADR 0039](0039-stichprobenplan-e2e.md)`.

- [ ] **Step 3: Update reference and how-to docs**

- `docs/reference/corpus.md`: add a column `Slots` to the areas table with the values above (Examples 1 …), and replace the line "Quoten je Bereich für den Fragenkatalog folgen in Schritt 4 ([Plan](../plan.md#stand))." with "Slots, Reserve und Mindestzahl je Bereich sind gleich (nach Tokenanteil, mindestens 1; [ADR 0039](../adr/0039-stichprobenplan-e2e.md))."
- `docs/reference/configuration.md`: rows `AREA_MIN_QUESTIONS`, `CATALOGUE_AREA_SLOTS`, `CATALOGUE_RESERVE`: value "15 Bereiche, siehe [Korpus](corpus.md#bereiche) (Summe 48)", meaning without "noch Vue-Bereiche", ADR column adds `[ADR 0039](../adr/0039-stichprobenplan-e2e.md)`; row `CATALOGUE_STOPWORDS`: "Tupel englischer Funktions- und Fragewörter plus `e2e` (Produktname)".
- `docs/how-to/build-the-question-catalogue.md` lines 24–25: "(12 API, 3 Style Guide, 33 Guide)" → "(je Bereich nach Tokenanteil, [Korpus](../reference/corpus.md#bereiche))".
- `docs/plan.md`: in the Stand paragraph replace "(4) Katalogwerkzeuge: Quoten je Bereich, Stichprobenplan, Stoppwörter, Closed-Book-Prüfung im Editor, K0" by "(4) Katalogwerkzeuge: (4a) Quoten je Bereich, Stichprobenplan, Stoppwörter (erledigt 18.10.2026, [ADR 0039](adr/0039-stichprobenplan-e2e.md)), (4b) Closed-Book-Prüfung im Editor, (4c) K0" and delete the sentence "Bis Schritt 4 tragen die Katalog-Quoten in `src/config.py` noch Vue-Bereiche."
- `.serena/memories/pipeline.md` line 30: "Catalogue quotas: 15 e2e areas, slots = reserve = minimum by token share (ADR 0039); plan drawn 18.10.2026, Vue plan in `data/evaluation/archive_vue/`."

Run: `grep -rn "Vue-Bereiche\|style-guide\|12 API" docs/reference docs/how-to docs/plan.md .serena/memories AGENTS.md`
Expected: no output.

- [ ] **Step 4: Lint and test**

Run: `set -o pipefail; uvx pre-commit run --all-files && uv run pytest -q 2>&1 | tail -3`
Expected: all hooks pass, all tests pass.

- [ ] **Step 5: Commit**

```bash
git add docs .serena/memories/pipeline.md
git commit -m "docs(adr): ADR 0039 Stichprobenplan und Bereichsquoten auf e2e"
```
