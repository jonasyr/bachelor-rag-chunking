import csv
import json

import pytest
from conftest import FakeEmbedder

import freeze
import tokens
import vector_index
from chunking import chunk
from config import CHROMA_COLLECTIONS, CONTROL_STRATEGIES, STRATEGY_IDS
from embed import embed_and_store, load_jsonl
from preprocess import clean_markdown, section_spans
from relevance import is_relevant
from retrieve import HEADER, retrieve
from run_log import sha256_of

HEADER_LINE = ",".join(HEADER) + "\n"
PAGE = (
    "# {title} {{#{a}}}\n\n## First part {{#first}}\n\n{body}\n\n"
    "## Second part {{#second}}\n\n{body2}\n"
)


@pytest.fixture
def setup(tmp_path, fake_embedder):
    docs, sections = [], []
    for i in range(1, 7):
        doc_id = f"D{i:03d}"
        body = f"Topic {i} explains reactive state with ref and computed values. " * 12
        body2 = f"Topic {i} also covers watchers, props and emits in components. " * 12
        result = clean_markdown(
            PAGE.format(title=f"Page {i}", a=f"page-{i}", body=body, body2=body2)
        )
        docs.append(
            {
                "doc_id": doc_id,
                "path": f"guide/p{i}.md",
                "title": f"Page {i}",
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(section_spans(doc_id, result))
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")

    client = vector_index.open_client(tmp_path / "chroma")
    chunk_files, vector_files = {}, {}
    for key in STRATEGY_IDS:  # retrieval always needs every configured strategy
        chunk_files[key] = tmp_path / f"chunks_{key.lower()}.jsonl"
        vector_files[key] = tmp_path / f"embeddings_{key.lower()}.npz"
        chunk(key, docs_file, sections_file, chunk_files[key])
        embed_and_store(
            key,
            embedder=fake_embedder,
            client=client,
            chunk_file=chunk_files[key],
            vector_file=vector_files[key],
            runs_file=tmp_path / "runs.jsonl",
            siblings=[],
        )

    target = load_jsonl(chunk_files["C3"], "")[3]  # questions reuse a chunk text: exact match
    questions = tmp_path / "questions.csv"
    with questions.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["question_id", "question", "type", "difficulty", "notes"])
        writer.writerow(["Q002", target["text"], "factual", "easy", ""])
        writer.writerow(["Q001", "How do watchers work?", "conceptual", "medium", ""])
    truth = tmp_path / "ground_truth.csv"
    truth.write_text(
        "question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n"
        'Q001,"Watchers run side effects.","D002;D003","D002#second; D003#second"\n'
        f'Q002,"Same text.",{target["doc_id"]},{target["doc_id"]}#first\n',
        encoding="utf-8",
    )
    paths = {
        "client": client,
        "questions_file": questions,
        "ground_truth_file": truth,
        "sections_file": sections_file,
        "chunk_files": chunk_files,
        "vector_files": vector_files,
        "query_file": tmp_path / "query_embeddings.npz",
        "out_file": tmp_path / "retrieved_results.csv",
        "runs_file": tmp_path / "runs.jsonl",
    }
    return paths, target, sections, fake_embedder


def read_out(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_writes_exact_format_and_relevance(setup):
    paths, target, sections, fake = setup
    assert retrieve(embedder=fake, **paths) == 2 * len(STRATEGY_IDS) * 5
    rows = read_out(paths["out_file"])
    assert rows[0] == HEADER
    body = rows[1:]
    assert [(r[0], r[1], r[2]) for r in body][:6] == [
        ("Q001", "C1", "1"),
        ("Q001", "C1", "2"),
        ("Q001", "C1", "3"),
        ("Q001", "C1", "4"),
        ("Q001", "C1", "5"),
        ("Q001", "C2", "1"),
    ]
    top_c3_q2 = next(r for r in body if r[0] == "Q002" and r[1] == "C3" and r[2] == "1")
    assert top_c3_q2[3] == target["chunk_id"] and top_c3_q2[4] == "1.000000"
    chunks = {
        c["chunk_id"]: c for k in STRATEGY_IDS for c in load_jsonl(paths["chunk_files"][k], "")
    }
    by_id = {s["section_id"]: s for s in sections}
    gold = {
        "Q001": [by_id["D002#second"], by_id["D003#second"]],
        "Q002": [by_id[f"{target['doc_id']}#first"]],
    }
    for qid, _, _, chunk_id, _, flag in body:
        assert flag == str(int(is_relevant(chunks[chunk_id], gold[qid], 1)))


def test_rerun_is_byte_identical_without_api_call(setup):
    paths, _, _, fake = setup
    calls_before = len(fake.calls)
    retrieve(embedder=fake, **paths)
    first = paths["out_file"].read_bytes()
    assert len(fake.calls) == calls_before + 2  # model-vintage check, then the questions
    retrieve(embedder=fake, **paths)
    assert paths["out_file"].read_bytes() == first
    assert len(fake.calls) == calls_before + 2  # rerun: no API call at all


def test_run_log_records_ground_truth_checksums(setup):
    paths, _, _, fake = setup
    retrieve(embedder=fake, **paths)
    last = json.loads(paths["runs_file"].read_text(encoding="utf-8").splitlines()[-1])
    assert last["step"] == "retrieve"
    assert last["inputs_sha256"]["ground_truth.csv"] == sha256_of(paths["ground_truth_file"])
    assert last["inputs_sha256"]["questions.csv"] == sha256_of(paths["questions_file"])


def test_refuses_empty_ground_truth(setup):
    paths, _, _, fake = setup
    paths["ground_truth_file"].write_text(
        "question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="must be complete before retrieval"):
        retrieve(embedder=fake, **paths)


def test_refuses_unknown_section_ids(setup):
    paths, _, _, fake = setup
    text = (
        paths["ground_truth_file"].read_text(encoding="utf-8").replace("D003#second", "D003#nope")
    )
    paths["ground_truth_file"].write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="unknown section IDs"):
        retrieve(embedder=fake, **paths)


def test_refuses_a_question_without_ground_truth(setup):
    paths, _, _, fake = setup
    lines = paths["ground_truth_file"].read_text(encoding="utf-8").splitlines()
    paths["ground_truth_file"].write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Q002 has no row"):
        retrieve(embedder=fake, **paths)


def test_changed_question_text_is_not_silently_reused(setup):
    paths, _, _, fake = setup
    retrieve(embedder=fake, **paths)
    text = (
        paths["questions_file"].read_text(encoding="utf-8").replace("watchers work", "watchers run")
    )
    paths["questions_file"].write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="delete it deliberately"):
        retrieve(embedder=fake, **paths)


def test_questions_are_not_embedded_with_a_changed_model(setup):
    paths, _, _, _ = setup
    with pytest.raises(RuntimeError, match="delete all embedding files deliberately"):
        retrieve(embedder=FakeEmbedder(salt="model-update"), **paths)
    assert not paths["query_file"].exists()


def test_the_run_log_covers_every_retrieval_input(setup):
    paths, _, _, fake = setup
    retrieve(embedder=fake, **paths)
    last = json.loads(paths["runs_file"].read_text(encoding="utf-8").splitlines()[-1])
    assert set(last["inputs_sha256"]) == {
        "questions.csv",
        "ground_truth.csv",
        "sections.jsonl",
        "query_embeddings.npz",
        "chunks_c1.jsonl",
        "chunks_c2.jsonl",
        "chunks_c3.jsonl",
        "embeddings_c1.npz",
        "embeddings_c2.npz",
        "embeddings_c3.npz",
    }


def test_questions_without_the_documented_columns_are_refused(setup):
    paths, _, _, fake = setup
    lines = paths["questions_file"].read_text(encoding="utf-8").split("\n", 1)
    paths["questions_file"].write_text(
        "question_id,question,type,difficulty\n" + lines[1].replace(",easy,\n", ",easy\n"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="columns"):
        retrieve(embedder=fake, **paths)


def test_ground_truth_with_extra_columns_is_refused(setup):
    paths, _, _, fake = setup
    text = paths["ground_truth_file"].read_text(encoding="utf-8")
    paths["ground_truth_file"].write_text(
        text.replace("relevant_section_ids", "relevant_section_ids,x", 1), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="columns"):
        retrieve(embedder=fake, **paths)


def test_duplicate_question_ids_are_refused(setup):
    paths, _, _, fake = setup
    text = paths["ground_truth_file"].read_text(encoding="utf-8")
    paths["ground_truth_file"].write_text(text + text.splitlines()[1] + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate question_id"):
        retrieve(embedder=fake, **paths)


def test_an_existing_result_file_is_replaced_completely(setup):
    paths, _, _, fake = setup
    paths["out_file"].write_text(HEADER_LINE + "Q999,C9,1,stale,0.1,1\n", encoding="utf-8")
    retrieve(embedder=fake, **paths)
    rows = read_out(paths["out_file"])
    assert {r[1] for r in rows[1:]} == set(STRATEGY_IDS) and all(r[0] != "Q999" for r in rows[1:])


def test_vintage_check_tokens_are_logged_apart_from_the_questions(setup):
    paths, _, _, fake = setup
    retrieve(embedder=fake, **paths)
    last = json.loads(paths["runs_file"].read_text(encoding="utf-8").splitlines()[-1])
    assert last["input_tokens"] == 2 * 7  # two questions
    assert last["canary_input_tokens"] == 3 * len(STRATEGY_IDS) * 7  # first/middle/last per file
    assert last["strategy"] == ",".join(STRATEGY_IDS)


def test_a_question_row_with_a_missing_field_is_refused(setup):
    paths, _, _, fake = setup
    text = paths["questions_file"].read_text(encoding="utf-8")
    paths["questions_file"].write_text(
        text.replace(",conceptual,medium,\n", ",conceptual,medium\n"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="row 3 has 4 fields, expected 5"):
        retrieve(embedder=fake, **paths)


def test_a_ground_truth_row_with_an_extra_field_is_refused(setup):
    paths, _, _, fake = setup
    lines = paths["ground_truth_file"].read_text(encoding="utf-8").splitlines()
    lines[1] += ",surplus"
    paths["ground_truth_file"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row 2 has 5 fields, expected 4"):
        retrieve(embedder=fake, **paths)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('"Watchers run side effects."', '""', "Q001: empty expected_answer"),
        ('"D002;D003"', '""', "Q001: empty relevant_doc_ids"),
        ('"D002;D003"', '"D002;D003;D009"', r"Q001: relevant_doc_ids \['D009'\] not in the corpus"),
        ('"D002;D003"', '"D002"', "Q001: relevant_doc_ids must be exactly the documents"),
    ],
)
def test_incomplete_or_inconsistent_ground_truth_is_refused(setup, old, new, message):
    paths, _, _, fake = setup
    text = paths["ground_truth_file"].read_text(encoding="utf-8")
    paths["ground_truth_file"].write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        retrieve(embedder=fake, **paths)


def test_empty_required_question_fields_are_refused(setup):
    paths, _, _, fake = setup
    text = paths["questions_file"].read_text(encoding="utf-8")
    paths["questions_file"].write_text(text.replace(",conceptual,", ",,", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Q001: empty type"):
        retrieve(embedder=fake, **paths)


def test_ground_truth_rows_without_a_question_are_refused(setup):
    paths, _, _, fake = setup
    with paths["ground_truth_file"].open("a", encoding="utf-8") as f:
        f.write('Q777,"Orphan.",D002,D002#first\n')
    with pytest.raises(ValueError, match=r"ground truth for unknown questions \['Q777'\]"):
        retrieve(embedder=fake, **paths)


@pytest.mark.parametrize("drop", ["chunk_files", "vector_files"])
def test_a_mapping_without_every_strategy_is_refused(setup, drop):
    paths, _, _, fake = setup
    paths[drop] = {k: v for k, v in paths[drop].items() if k != "C2"}
    with pytest.raises(ValueError, match=r"must cover exactly the strategies \['C1', 'C2', 'C3'\]"):
        retrieve(embedder=fake, **paths)


def test_a_missing_vector_file_stops_before_any_api_call(setup):
    paths, _, _, fake = setup
    paths["vector_files"]["C2"].unlink()
    calls_before = len(fake.calls)
    with pytest.raises(FileNotFoundError, match="run src/embed.py first"):
        retrieve(embedder=fake, **paths)
    assert len(fake.calls) == calls_before and not paths["query_file"].exists()


def control_paths(paths, tmp_path):
    return {
        **paths,
        "chunk_files": {"K1": paths["chunk_files"]["C1"]},
        "vector_files": {"K1": paths["vector_files"]["C1"]},
        "out_file": tmp_path / "retrieved_results_control.csv",
    }


def test_control_retrieval_writes_only_the_control(setup, tmp_path):
    paths, *_ = setup
    n = retrieve(
        embedder=FakeEmbedder(),
        strategies=CONTROL_STRATEGIES,
        collections={"K1": CHROMA_COLLECTIONS["C1"]},
        **control_paths(paths, tmp_path),
    )
    rows = read_out(tmp_path / "retrieved_results_control.csv")
    assert rows[0] == HEADER and n == 2 * 5 == len(rows) - 1
    assert {r[1] for r in rows[1:]} == {"K1"}
    assert json.loads(paths["runs_file"].read_text().splitlines()[-1])["strategy"] == "K1"


def test_a_partial_strategy_set_is_refused(setup):
    paths, *_ = setup
    with pytest.raises(ValueError, match="experiment set or the control set"):
        retrieve(embedder=FakeEmbedder(), strategies={"C1": STRATEGY_IDS["C1"]}, **paths)


def test_control_files_in_the_experiment_are_refused(setup):
    paths, *_ = setup
    mixed = {**paths, "chunk_files": {**paths["chunk_files"], "K1": paths["chunk_files"]["C1"]}}
    with pytest.raises(ValueError, match="must cover exactly the strategies"):
        retrieve(embedder=FakeEmbedder(), **mixed)


@pytest.fixture
def as_main_catalogue(setup, monkeypatch):
    paths = setup[0]
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", paths["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", paths["ground_truth_file"])
    return setup


def test_main_catalogue_needs_a_freeze_before_any_api_call(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    calls = len(fake.calls)  # the setup embeds the chunks with the same fake
    with pytest.raises(RuntimeError, match="not frozen"):
        retrieve(embedder=fake, freeze_file=tmp_path / "freeze.json", **paths)
    assert len(fake.calls) == calls and not paths["out_file"].exists()


def test_main_catalogue_runs_when_frozen(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    record = tmp_path / "freeze.json"
    freeze.write_freeze(
        paths["questions_file"], paths["ground_truth_file"], paths["sections_file"], record
    )
    assert retrieve(embedder=fake, freeze_file=record, **paths) > 0


def test_main_catalogue_changed_after_freeze_is_refused(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    record = tmp_path / "freeze.json"
    freeze.write_freeze(
        paths["questions_file"], paths["ground_truth_file"], paths["sections_file"], record
    )
    q = paths["questions_file"]
    q.write_text(q.read_text(encoding="utf-8").replace("How do watchers", "How do Watchers"))
    calls = len(fake.calls)
    with pytest.raises(RuntimeError, match="questions.csv changed since the freeze"):
        retrieve(embedder=fake, freeze_file=record, **paths)
    assert len(fake.calls) == calls
