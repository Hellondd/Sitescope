"""Простой CLI-поиск по индексу.

Примеры:
    python src/search.py --query "Docker контейнеры"
    python src/search.py --query тестирование --category testing --limit 3
"""
import argparse

INDEX = "sitescope-pages"


def build_query(text, category=None):
    query = {"bool": {"must": [{"multi_match": {"query": text, "fields": ["title^2", "description"]}}]}}
    if category:
        query["bool"]["filter"] = [{"term": {"category": category}}]
    return query


def main():
    p = argparse.ArgumentParser(description="Поиск по каталогу sitescope-pages")
    p.add_argument("--query", required=True)
    p.add_argument("--category")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--host", default="http://127.0.0.1:9200")
    a = p.parse_args()

    from elasticsearch import Elasticsearch  # импорт здесь: build_query тестируется без клиента
    es = Elasticsearch(a.host)
    resp = es.search(index=INDEX, size=a.limit, query=build_query(a.query, a.category),
                     source=["id", "title", "category"])
    print(f"Найдено: {resp['hits']['total']['value']}")
    for h in resp["hits"]["hits"]:
        s = h["_source"]
        print(f"[{s['id']}] {h['_score']:.3f}  {s['title']}  ({s['category']})")


if __name__ == "__main__":
    main()
