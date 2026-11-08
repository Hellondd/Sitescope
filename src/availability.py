"""Калькулятор доступности, бюджета простоя и учебных показателей надёжности (SLO).

Формулы:
    A    = (T - D) / T * 100 %          T - весь интервал, D - суммарный НЕплановый простой
    Dmax = T * (1 - A_target / 100)     допустимый простой (бюджет ошибки)
Все времена внутри считаются в СЕКУНДАХ (единицы согласованы).

Запуск:  python src/availability.py     (результаты -> results/)
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

TARGETS = (99.0, 99.9, 99.95, 99.99, 99.999)
PERIODS = {            # секунды
    "24 часа": 24 * 3600,
    "7 суток": 7 * 86400,
    "30 суток": 30 * 86400,
    "365 суток": 365 * 86400,
}
INCIDENTS_S = (75, 100, 40)     # по заданию, в одном 30-дневном окне
WINDOW_S = PERIODS["30 суток"]
SLO = 99.99
NEXT_INCIDENT_S = 60


def availability_percent(total_s, downtime_s):
    if total_s <= 0:
        raise ValueError("T должно быть > 0")
    if downtime_s < 0 or downtime_s > total_s:
        raise ValueError("D должно быть в диапазоне [0, T]")
    return (total_s - downtime_s) / total_s * 100


def allowed_downtime_s(total_s, target_percent):
    if total_s <= 0:
        raise ValueError("T должно быть > 0")
    if not 0 <= target_percent <= 100:
        raise ValueError("цель должна быть в диапазоне 0..100 %")
    return total_s * (1 - target_percent / 100)


def budget_table():
    rows = []
    for target in TARGETS:
        for name, seconds in PERIODS.items():
            d = allowed_downtime_s(seconds, target)
            rows.append({"target_percent": target, "period": name,
                         "allowed_downtime_s": round(d, 3), "allowed_downtime_min": round(d / 60, 4)})
    return rows


def incident_report(incidents_s=INCIDENTS_S, window_s=WINDOW_S, slo=SLO, next_incident_s=NEXT_INCIDENT_S):
    d_total = sum(incidents_s)
    budget = allowed_downtime_s(window_s, slo)
    a = availability_percent(window_s, d_total)
    remaining = budget - d_total
    n = len(incidents_s)
    mttr = d_total / n                                  # среднее время восстановления
    uptime = window_s - d_total
    mtbf = uptime / n                                   # среднее время работы между отказами
    return {
        "window_s": window_s,
        "slo_percent": slo,
        "incidents_s": list(incidents_s),
        "downtime_total_s": d_total,
        "availability_percent": a,
        "budget_s": budget,
        "budget_used_percent": d_total / budget * 100,
        "remaining_s": remaining,
        "survives_next_incident": remaining >= next_incident_s,
        "next_incident_s": next_incident_s,
        "overrun_if_next_s": max(0.0, next_incident_s - remaining),
        "mttr_s": mttr,
        "mtbf_s": mtbf,
        "mtbf_availability_percent": mtbf / (mtbf + mttr) * 100,
    }


def plot_budget(rep, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    budget, used, rem = rep["budget_s"], rep["downtime_total_s"], rep["remaining_s"]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.barh(["Бюджет\nпростоя"], [used], color="#d9534f", label=f"Использовано: {used:.0f} с")
    ax.barh(["Бюджет\nпростоя"], [rem], left=[used], color="#5cb85c", label=f"Остаток: {rem:.1f} с")
    nxt = rep["next_incident_s"]
    ax.barh(["Бюджет\nпростоя"], [nxt], left=[budget], color="none", edgecolor="#d9534f",
            hatch="//", label=f"Гипотетический инцидент +{nxt} с (выход за бюджет)")
    ax.axvline(budget, color="black", linestyle="--", label=f"Допустимо (бюджет): {budget:.1f} с")
    ax.set_xlabel("секунды в 30-дневном окне")
    ax.set_title(f"Бюджет простоя для SLO {rep['slo_percent']}% (T = 30 суток)", pad=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.42), ncol=1, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = budget_table()
    with (RESULTS_DIR / "downtime_budget.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("Бюджет простоя (без исключения планового обслуживания):")
    print(f"{'Цель, %':>9}  {'Период':<10}{'Допустимо, с':>15}{'Допустимо, мин':>16}")
    for r in rows:
        print(f"{r['target_percent']:>9}  {r['period']:<10}{r['allowed_downtime_s']:>15.2f}{r['allowed_downtime_min']:>16.4f}")

    rep = incident_report()
    (RESULTS_DIR / "incidents.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_budget(rep, RESULTS_DIR / "downtime_budget.png")

    print("\nИнциденты в 30-дневном окне:", rep["incidents_s"], "с")
    print(f"Суммарный простой D     = {rep['downtime_total_s']} с")
    print(f"Фактическая доступность = {rep['availability_percent']:.6f} %")
    print(f"Бюджет для {rep['slo_percent']}%       = {rep['budget_s']:.1f} с")
    print(f"Израсходовано бюджета   = {rep['budget_used_percent']:.2f} %")
    print(f"Остаток                 = {rep['remaining_s']:.1f} с")
    ok = "ДА" if rep["survives_next_incident"] else "НЕТ"
    print(f"Выдержим ещё {rep['next_incident_s']} с?      = {ok} (превышение {rep['overrun_if_next_s']:.1f} с)")
    print(f"MTTR = {rep['mttr_s']:.2f} с; MTBF = {rep['mtbf_s']:.2f} с ({rep['mtbf_s']/86400:.2f} суток)")
    print(f"MTBF/(MTBF+MTTR) = {rep['mtbf_availability_percent']:.6f} %")
    print("\nСохранено: results/downtime_budget.csv, incidents.json, downtime_budget.png")


if __name__ == "__main__":
    main()
