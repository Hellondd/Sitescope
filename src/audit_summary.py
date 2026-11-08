"""Сводка результатов PageSpeed Insights из results/audit_pagespeed.csv:
среднее по двум запускам и разброс (макс - мин) для каждого сочетания «сайт × режим».

Запуск:  python src/audit_summary.py  ->  results/audit_summary.csv
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "results" / "audit_pagespeed.csv"
OUT = ROOT / "results" / "audit_summary.csv"
METRICS = ["performance", "accessibility", "best_practices", "seo", "lcp_s", "cls", "tbt_ms"]


def load_rows(path):
    with Path(path).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["site"], r["mode"])].append(r)
    out = []
    for (site, mode), items in groups.items():
        row = {"site": site, "mode": mode, "runs": len(items)}
        for m in METRICS:
            vals = [float(i[m]) for i in items]
            row[f"{m}_mean"] = round(sum(vals) / len(vals), 3)
            row[f"{m}_spread"] = round(max(vals) - min(vals), 3)
        out.append(row)
    return out


def main():
    summary = summarize(load_rows(SRC))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    for r in summary:
        print(f"{r['site']:<9}{r['mode']:<8} perf={r['performance_mean']:>5} (±{r['performance_spread']/2:g})  "
              f"LCP={r['lcp_s_mean']} с  CLS={r['cls_mean']}  TBT={r['tbt_ms_mean']} мс")
    print(f"Сохранено: {OUT}")


if __name__ == "__main__":
    main()
