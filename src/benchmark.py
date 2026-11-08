"""Честное сравнение трёх способов найти запись по точному числовому id:
  1) линейный поиск по неотсортированному списку  - O(n)
  2) бинарный поиск по заранее отсортированным id - O(log n)
  3) поиск в dict по id                           - O(1) в среднем

Правила честности:
  * одинаковые данные и одинаковые ключи для всех алгоритмов;
  * N = 1 000, 10 000, 100 000; на каждый N 100 существующих и 100 отсутствующих ключей;
  * время через time.perf_counter_ns, не менее 5 повторов, берём МЕДИАНУ;
  * время построения отсортированного списка и dict измеряется ОТДЕЛЬНО;
  * перед замерами проверяется, что все три алгоритма возвращают одинаковый результат.

Elasticsearch сюда НЕ входит: это другая операция (сеть + индекс + анализ + ранжирование).

Запуск:  python src/benchmark.py            (результаты -> results/)
         python src/benchmark.py --repeats 9
"""
import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

import random

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
SIZES = (1_000, 10_000, 100_000)
N_KEYS = 100


# ---------- данные ----------
def make_dataset(n, seed=42, n_keys=N_KEYS):
    """Список записей (в случайном порядке), 100 существующих и 100 отсутствующих ключей."""
    rnd = random.Random(seed + n)
    ids = rnd.sample(range(1, n * 10 + 1), n)          # уникальные id, порядок случайный
    records = [{"id": i, "title": f"item-{i}"} for i in ids]
    existing = rnd.sample(ids, n_keys)
    id_set = set(ids)
    missing = set()
    while len(missing) < n_keys:
        k = rnd.randint(1, n * 10)
        if k not in id_set:
            missing.add(k)
    return records, existing, sorted(missing)


# ---------- алгоритмы ----------
def linear_search(records, key):
    """O(n): просмотр списка подряд."""
    for rec in records:
        if rec["id"] == key:
            return rec
    return None


def build_sorted(records):
    """Подготовка для бинарного поиска: сортировка O(n log n)."""
    sorted_records = sorted(records, key=lambda r: r["id"])
    sorted_ids = [r["id"] for r in sorted_records]
    return sorted_ids, sorted_records


def binary_search(sorted_ids, sorted_records, key):
    """O(log n): классический бинарный поиск по отсортированным id."""
    lo, hi = 0, len(sorted_ids) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_val = sorted_ids[mid]
        if mid_val == key:
            return sorted_records[mid]
        if mid_val < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def build_dict(records):
    """Подготовка для dict-поиска: построение хеш-таблицы O(n)."""
    return {r["id"]: r for r in records}


def dict_search(index, key):
    """O(1) в среднем."""
    return index.get(key)


# ---------- измерения ----------
def verify_same_results(records, keys):
    sorted_ids, sorted_records = build_sorted(records)
    index = build_dict(records)
    for k in keys:
        a = linear_search(records, k)
        b = binary_search(sorted_ids, sorted_records, k)
        c = dict_search(index, k)
        if not (a == b == c):
            raise AssertionError(f"Алгоритмы вернули разные результаты для ключа {k}")
    return True


def median_us_per_lookup(func, keys, repeats):
    """Медиана (по повторам) среднего времени одного поиска, микросекунды."""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        for k in keys:
            func(k)
        t1 = time.perf_counter_ns()
        samples.append((t1 - t0) / len(keys) / 1000)   # нс -> мкс на один поиск
    return statistics.median(samples)


def median_ms(func, repeats):
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        func()
        samples.append((time.perf_counter_ns() - t0) / 1_000_000)
    return statistics.median(samples)


def run_benchmark(sizes=SIZES, repeats=7, seed=42):
    search_rows, prep_rows = [], []
    for n in sizes:
        records, existing, missing = make_dataset(n, seed)
        verify_same_results(records, existing + missing)
        sorted_ids, sorted_records = build_sorted(records)
        index = build_dict(records)

        prep_rows.append({
            "n": n,
            "sort_ms": round(median_ms(lambda: build_sorted(records), repeats), 4),
            "dict_build_ms": round(median_ms(lambda: build_dict(records), repeats), 4),
            "dict_container_bytes": sys.getsizeof(index),
            "sorted_ids_container_bytes": sys.getsizeof(sorted_ids),
        })
        for cond, keys in (("found", existing), ("missing", missing)):
            search_rows.append({
                "n": n,
                "condition": cond,
                "linear_us": round(median_us_per_lookup(lambda k: linear_search(records, k), keys, repeats), 4),
                "binary_us": round(median_us_per_lookup(lambda k: binary_search(sorted_ids, sorted_records, k), keys, repeats), 4),
                "dict_us": round(median_us_per_lookup(lambda k: dict_search(index, k), keys, repeats), 4),
            })
        print(f"N={n:>7}: готово")
    return search_rows, prep_rows


def save_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def plot(search_rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, cond, title in zip(axes, ("found", "missing"), ("Ключ найден", "Ключ не найден")):
        rows = [r for r in search_rows if r["condition"] == cond]
        ns = [r["n"] for r in rows]
        for col, label in (("linear_us", "Линейный O(n)"), ("binary_us", "Бинарный O(log n)"), ("dict_us", "dict O(1)")):
            ax.plot(ns, [r[col] for r in rows], marker="o", label=label)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("N (число записей)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.3)
    axes[0].set_ylabel("Медиана времени одного поиска, мкс")
    axes[0].legend()
    fig.suptitle("Поиск по числовому id: время одного поиска (лог-лог шкала)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def print_table(search_rows, prep_rows):
    print("\nТАБЛИЦА № 3. Медианы, мкс на один поиск")
    print(f"{'N / условие':<22}{'Линейный':>12}{'Бинарный':>12}{'Dict':>12}")
    for r in search_rows:
        name = f"{r['n']:,} / {'найден' if r['condition'] == 'found' else 'не найден'}".replace(",", " ")
        print(f"{name:<22}{r['linear_us']:>12.3f}{r['binary_us']:>12.3f}{r['dict_us']:>12.3f}")
    print("\nПодготовка структур (медиана, мс):")
    for r in prep_rows:
        print(f"  N={r['n']:>7}: сортировка {r['sort_ms']:.3f} мс, построение dict {r['dict_build_ms']:.3f} мс, "
              f"размер dict-контейнера {r['dict_container_bytes']} байт")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repeats", type=int, default=7, help="число повторов (не менее 5)")
    a = p.parse_args()
    if a.repeats < 5:
        p.error("по заданию нужно не менее 5 повторов")
    RESULTS_DIR.mkdir(exist_ok=True)
    search_rows, prep_rows = run_benchmark(repeats=a.repeats)
    save_csv(RESULTS_DIR / "benchmark_search.csv", search_rows)
    save_csv(RESULTS_DIR / "benchmark_prep.csv", prep_rows)
    plot(search_rows, RESULTS_DIR / "benchmark_plot.png")
    print_table(search_rows, prep_rows)
    print("\nСохранено: results/benchmark_search.csv, benchmark_prep.csv, benchmark_plot.png")


if __name__ == "__main__":
    main()
