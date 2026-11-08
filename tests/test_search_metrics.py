import pytest

from metrics import mean, precision_at_k
from search import build_query


def test_precision_all_relevant():
    assert precision_at_k(["a", "b", "c", "d", "e"], {"a", "b", "c", "d", "e"}, 5) == 1.0


def test_precision_none_relevant():
    assert precision_at_k(["x", "y"], {"a"}, 5) == 0.0


def test_precision_partial_and_short_result():
    # вернули только 3 документа, 2 релевантных: делим на k=5, а не на 3
    assert precision_at_k(["a", "x", "b"], {"a", "b"}, 5) == 0.4


def test_precision_uses_only_top_k():
    assert precision_at_k(["x", "x2", "x3", "x4", "x5", "a"], {"a"}, 5) == 0.0


def test_precision_invalid_k():
    with pytest.raises(ValueError):
        precision_at_k(["a"], {"a"}, 0)


def test_mean():
    assert mean([0.2, 0.4, 0.6]) == pytest.approx(0.4)
    with pytest.raises(ValueError):
        mean([])


def test_build_query_with_and_without_category():
    assert "filter" not in build_query("docker")["bool"]
    q = build_query("docker", "devops")
    assert q["bool"]["filter"] == [{"term": {"category": "devops"}}]
