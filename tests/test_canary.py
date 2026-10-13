import pytest
from conftest import FakeEmbedder

from canary import check_vintage
from embed import save_vectors


@pytest.fixture
def stored(tmp_path):
    texts = [f"chunk text {i}" for i in range(7)]
    vectors = FakeEmbedder()(texts).vectors
    path = tmp_path / "embeddings_c1.npz"
    save_vectors(path, [f"C1_D001_{i:04d}" for i in range(7)], texts, vectors)
    return path


def test_no_stored_vectors_means_nothing_to_compare(tmp_path):
    fake = FakeEmbedder()
    assert check_vintage(fake, [tmp_path / "missing.npz"]) == (None, 0)
    assert fake.calls == []


def test_same_model_passes_with_the_measured_cosine(stored):
    fake = FakeEmbedder()
    cosine, tokens = check_vintage(fake, [stored])
    assert fake.calls == [["chunk text 0", "chunk text 3", "chunk text 6"]]  # first, middle, last
    assert cosine == pytest.approx(1.0)
    assert tokens == 21


def test_a_changed_model_behind_the_same_name_aborts(stored):
    with pytest.raises(RuntimeError, match="delete all embedding files deliberately"):
        check_vintage(FakeEmbedder(salt="model-update"), [stored])


def test_probe_positions_come_from_the_config(stored, monkeypatch):
    import canary

    monkeypatch.setattr(canary, "CANARY_PROBE_POSITIONS", (0.0, 1.0))
    fake = FakeEmbedder()
    canary.check_vintage(fake, [stored])
    assert fake.calls == [["chunk text 0", "chunk text 6"]]
