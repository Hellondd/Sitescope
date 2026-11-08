from datetime import date

from generate_catalog import generate_catalog, manual_docs, save_jsonl, load_jsonl

FIELDS = {"id", "title", "description", "category", "tags", "published_at"}


def test_catalog_has_at_least_1000_docs():
    assert len(generate_catalog()) >= 1000


def test_catalog_is_reproducible_with_same_seed():
    assert generate_catalog(seed=42) == generate_catalog(seed=42)


def test_catalog_differs_for_other_seed():
    assert generate_catalog(seed=1) != generate_catalog(seed=2)


def test_document_format():
    for d in generate_catalog():
        assert set(d) == FIELDS
        assert isinstance(d["tags"], list) and d["tags"]
        date.fromisoformat(d["published_at"])      # корректная дата ISO


def test_ids_are_unique():
    ids = [d["id"] for d in generate_catalog()]
    assert len(ids) == len(set(ids))


def test_at_least_20_manual_docs():
    assert len(manual_docs()) >= 20


def test_jsonl_roundtrip(tmp_path):
    docs = generate_catalog(total=50)
    path = tmp_path / "c.jsonl"
    save_jsonl(docs, path)
    assert load_jsonl(path) == docs
