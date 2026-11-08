"""Иллюстрация «кривой ванны» (bathtub curve): СИНТЕТИЧЕСКАЯ модель, не прогноз для конкретного продукта.

λ(t) - интенсивность отказов (условные единицы) на интервале 36 условных месяцев:
    0-6    ранние отказы: убывает
    6-24   нормальная эксплуатация: примерно постоянна
    24-36  износ: возрастает
Запуск:  python src/bathtub.py     -> results/bathtub_curve.png
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "bathtub_curve.png"

T_EARLY, T_WEAR, T_END = 6, 24, 36
BASE, PEAK, END = 0.004, 0.020, 0.016


def failure_rate(t):
    """Кусочно-заданная непрерывная функция λ(t), t в условных месяцах."""
    if t < 0 or t > T_END:
        raise ValueError("t вне интервала 0..36")
    if t < T_EARLY:                                    # ранние отказы
        return BASE + (PEAK - BASE) * (1 - t / T_EARLY) ** 2
    if t <= T_WEAR:                                    # нормальная работа
        return BASE
    k = (END - BASE) / (T_END - T_WEAR) ** 2           # износ
    return BASE + k * (t - T_WEAR) ** 2


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ts = [i * T_END / 360 for i in range(361)]
    ys = [failure_rate(t) for t in ts]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.5, 1]})
    ax.plot(ts, ys, color="#1f4e79", linewidth=2.5)
    zones = [(0, T_EARLY, "#f8d7da", "Ранние отказы\n(λ убывает)"),
             (T_EARLY, T_WEAR, "#d4edda", "Нормальная эксплуатация\n(λ ≈ const)"),
             (T_WEAR, T_END, "#fff3cd", "Износ\n(λ растёт)")]
    for a, b, color, label in zones:
        ax.axvspan(a, b, color=color, alpha=0.8)
        ax.text((a + b) / 2, PEAK * 0.93, label, ha="center", va="top", fontsize=9)
    ax.set_xlim(0, T_END)
    ax.set_ylim(0, PEAK * 1.08)
    ax.set_xlabel("Возраст системы, условные месяцы")
    ax.set_ylabel("Интенсивность отказов λ(t), усл. ед.")
    ax.set_title("Кривая ванны: интенсивность отказов")
    ax.text(0.5, -0.17, "Синтетическая модель, не прогноз для конкретного продукта",
            transform=ax.transAxes, ha="center", fontsize=10, color="#a00", style="italic")
    ax.grid(True, alpha=0.3)

    ax2.axis("off")
    ax2.set_title("Инженерные действия по фазам")
    actions = [("Ранние отказы", "Приёмочное тестирование,\nприработка, burn-in,\nпроверка конфигурации", "#f8d7da"),
               ("Нормальная работа", "Наблюдение и диагностика:\nмониторинг, алерты,\nанализ логов", "#d4edda"),
               ("Износ", "Профилактика и замена\nизнашивающихся узлов,\nплановое обновление", "#fff3cd")]
    for i, (phase, text, color) in enumerate(actions):
        y = 0.80 - i * 0.32
        ax2.text(0.5, y, f"{phase}\n\n{text}", ha="center", va="center", fontsize=10,
                 bbox=dict(boxstyle="round,pad=0.6", facecolor=color, edgecolor="#555"),
                 transform=ax2.transAxes)
    fig.tight_layout()
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"Сохранено: {OUT}")


if __name__ == "__main__":
    main()
