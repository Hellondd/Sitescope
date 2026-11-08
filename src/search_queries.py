"""Выполняет поисковые сценарии (Query DSL из queries/scenarios/*.json),
считает Precision@5 по queries/precision_queries.json и сохраняет результаты в results/.

Запуск:  python src/search_queries.py
"""
import argparse
import csv
import json
from pathlib import Path

from elasticsearch import Elasticsearch

from metrics import mean, precision_at_k

ROOT = Path(__file__).resolve().parent.parent
INDEX = "sitescope-pages"
SCENARIOS_DIR = ROOT / "queries" / "scenarios"
PRECISION_FILE = ROOT / "queries" / "precision_queries.json"
RESULTS_DIR = ROOT / "results"


def short(text, n=60):
    return text if len(text) <= n else text[: n - 1] + "…"


def run_scenarios(es):
    out = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        sc = json.loads(path.read_text(encoding="utf-8"))
        body = dict(sc["body"])
        if "_source" in body:  # в клиенте 8.x параметр называется source
            body["source"] = body.pop("_source")
        resp = es.search(index=INDEX, **body)
        total = resp["hits"]["total"]["value"]
        hits = [
            {"id": h["_source"].get("id", h["_id"]), "title": h["_source"].get("title"),
             "score": h["_score"], "source": h["_source"]}
            for h in resp["hits"]["hits"]
        ]
        print(f"\n=== {sc['name']}  ({path.name}) ===")
        print(f"Ожидание: {sc['expect']}")
        print(f"Найдено всего: {total}, took={resp['took']} мс")
        for rank, h in enumerate(hits, 1):
            score = "—" if h["score"] is None else f"{h['score']:.3f}"
            print(f"  {rank}. [{h['id']}] score={score}  {short(h['title'] or '')}")
        out.append({"file": path.name, "name": sc["name"], "expect": sc["expect"],
                    "total_hits": total, "took_ms": resp["took"], "top": hits})
    return out


def run_precision(es):
    cfg = json.loads(PRECISION_FILE.read_text(encoding="utf-8"))
    k = cfg["k"]
    rows = []
    print(f"\n=== Precision@{k} ===")
    for q in cfg["queries"]:
        resp = es.search(
            index=INDEX, size=k, source=["id", "title"],
            query={"multi_match": {"query": q["text"], "fields": cfg["fields"]}},
        )
        ids = [h["_source"]["id"] for h in resp["hits"]["hits"]]
        scores = [round(h["_score"], 3) for h in resp["hits"]["hits"]]
        p = precision_at_k(ids, q["relevant"], k)
        hits = [i for i in ids if i in set(q["relevant"])]
        print(f"{q['id']} «{q['text']}»: P@{k} = {p:.2f}  (релевантных в топ-{k}: {len(hits)})")
        print(f"     выдача: {ids}")
        rows.append({"query_id": q["id"], "query": q["text"], "returned": " ".join(ids),
                     "scores": " ".join(map(str, scores)),
                     "relevant_in_top": len(hits), f"precision_at_{k}": round(p, 3)})
    avg = mean(r[f"precision_at_{k}"] for r in rows)
    print(f"Среднее Precision@{k} по {len(rows)} запросам: {avg:.3f}")
    return rows, avg, k


def analyze_demo(es):
    """Показывает, что text-поля анализируются, а keyword-поля хранятся как есть."""
    demo = {
        "title (text, russian)": es.indices.analyze(index=INDEX, field="title",
                                                    text="Контейнеры Docker для начинающих"),
        "category (keyword)": es.indices.analyze(index=INDEX, field="category", text="Devops Tools"),
    }
    result = {name: [t["token"] for t in r["tokens"]] for name, r in demo.items()}
    print("\n=== Анализ текста ===")
    for name, tokens in result.items():
        print(f"  {name}: {tokens}")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="http://127.0.0.1:9200")
    a = p.parse_args()
    es = Elasticsearch(a.host)
    RESULTS_DIR.mkdir(exist_ok=True)

    scenarios = run_scenarios(es)
    rows, avg, k = run_precision(es)
    analysis = analyze_demo(es)

    (RESULTS_DIR / "search_results.json").write_text(
        json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "analyze_demo.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    with (RESULTS_DIR / "precision.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
        w.writerow({"query_id": "MEAN", f"precision_at_{k}": round(avg, 3)})
    print("\nСохранено в results/: search_results.json, precision.csv, analyze_demo.json")


if __name__ == "__main__":
    main()
