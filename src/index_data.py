"""Создаёт индекс sitescope-pages с явным mapping и загружает каталог через bulk API.

Запуск:  python src/index_data.py
Требуется запущенный Elasticsearch (docker compose up -d), см. README.md.
"""
import argparse
import json
from pathlib import Path

from elasticsearch import Elasticsearch, helpers

from generate_catalog import load_jsonl

ROOT = Path(__file__).resolve().parent.parent
INDEX = "sitescope-pages"
MAPPING_FILE = ROOT / "queries" / "index_mapping.json"
CATALOG_FILE = ROOT / "data" / "catalog.jsonl"
INFO_FILE = ROOT / "results" / "index_info.json"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="http://127.0.0.1:9200")
    p.add_argument("--catalog", default=str(CATALOG_FILE))
    a = p.parse_args()

    es = Elasticsearch(a.host)
    info = es.info()
    version = info["version"]["number"]
    print(f"Elasticsearch {version}, cluster: {info['cluster_name']}")

    body = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
        print(f"Старый индекс {INDEX} удалён")
    es.indices.create(index=INDEX, settings=body["settings"], mappings=body["mappings"])
    print(f"Индекс {INDEX} создан с явным mapping")

    docs = load_jsonl(a.catalog)
    actions = ({"_index": INDEX, "_id": d["id"], "_source": d} for d in docs)
    ok, errors = helpers.bulk(es, actions, stats_only=True)
    es.indices.refresh(index=INDEX)
    count = es.count(index=INDEX)["count"]
    print(f"Загружено: {ok}, ошибок: {errors}, документов в индексе: {count}")

    INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
    INFO_FILE.write_text(json.dumps(
        {"elasticsearch_version": version, "index": INDEX, "documents_indexed": count,
         "bulk_ok": ok, "bulk_errors": errors},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сводка сохранена: {INFO_FILE}")


if __name__ == "__main__":
    main()
