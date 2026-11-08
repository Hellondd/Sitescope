import math

from audit_summary import load_rows, summarize, SRC
from bathtub import failure_rate


def test_bathtub_three_phases():
    early = [failure_rate(t) for t in (0, 1, 2, 3, 4, 5, 6)]
    normal = [failure_rate(t) for t in (6, 10, 15, 20, 24)]
    wear = [failure_rate(t) for t in (24, 28, 32, 36)]
    assert all(a > b for a, b in zip(early, early[1:]))       # убывает
    assert max(normal) == min(normal)                         # постоянна
    assert all(a < b for a, b in zip(wear, wear[1:]))         # возрастает


def test_bathtub_continuity_and_range():
    assert math.isclose(failure_rate(6), failure_rate(6.0001), abs_tol=1e-4)
    assert math.isclose(failure_rate(24), failure_rate(24.0001), abs_tol=1e-4)


def test_audit_csv_has_8_runs_two_per_combination():
    rows = load_rows(SRC)
    assert len(rows) == 8
    summary = summarize(rows)
    assert len(summary) == 4
    assert all(s["runs"] == 2 for s in summary)


def test_audit_summary_mean():
    rows = [
        {"site": "A", "mode": "mobile", "performance": "40", "accessibility": "80", "best_practices": "80",
         "seo": "80", "lcp_s": "2", "cls": "0", "tbt_ms": "100"},
        {"site": "A", "mode": "mobile", "performance": "50", "accessibility": "80", "best_practices": "80",
         "seo": "80", "lcp_s": "4", "cls": "0", "tbt_ms": "300"},
    ]
    s = summarize(rows)[0]
    assert s["performance_mean"] == 45 and s["performance_spread"] == 10
    assert s["lcp_s_mean"] == 3 and s["tbt_ms_mean"] == 200
