from types import SimpleNamespace

import pytest

import embedding_client
from config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from embedding_client import embed_texts


class FakeOpenAI:
    """Mimics client.embeddings.create; returns items in reverse order to test re-sorting."""

    def __init__(self, dimensions=EMBEDDING_DIMENSIONS):
        self.requests = []
        self.dimensions = dimensions
        self.embeddings = SimpleNamespace(create=self.create)

    def create(self, model, input, encoding_format):
        self.requests.append((model, list(input), encoding_format))
        data = [
            SimpleNamespace(index=i, embedding=[float(len(text))] * self.dimensions)
            for i, text in enumerate(input)
        ]
        return SimpleNamespace(data=data[::-1], usage=SimpleNamespace(prompt_tokens=3 * len(input)))


def test_batches_keep_order_and_sum_tokens():
    client = FakeOpenAI()
    texts = ["a", "bb", "ccc", "dddd", "eeeee"]
    result = embed_texts(texts, client=client, batch_size=2)
    assert [len(batch) for _, batch, _ in client.requests] == [2, 2, 1]
    assert {model for model, _, _ in client.requests} == {EMBEDDING_MODEL}
    assert result.vectors.shape == (5, EMBEDDING_DIMENSIONS)
    assert result.vectors[:, 0].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert result.input_tokens == 15


def test_wrong_dimension_raises():
    with pytest.raises(ValueError, match="dimensions"):
        embed_texts(["a"], client=FakeOpenAI(dimensions=3))


def test_empty_text_raises():
    with pytest.raises(ValueError, match="empty text"):
        embed_texts(["a", "  "], client=FakeOpenAI())


def test_missing_api_key_points_to_env_file(monkeypatch):
    monkeypatch.setattr(embedding_client, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set; copy .env.example"):
        embed_texts(["a"])
