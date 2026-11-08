import math

import pytest

from availability import (PERIODS, allowed_downtime_s, availability_percent,
                          budget_table, incident_report)


def test_budget_30_days_99_99_is_4_32_minutes():
    # контрольное значение из задания
    assert math.isclose(allowed_downtime_s(PERIODS["30 суток"], 99.99) / 60, 4.32, rel_tol=1e-9)


def test_budget_365_days_99_99_is_52_56_minutes():
    # контрольное значение из задания
    assert math.isclose(allowed_downtime_s(PERIODS["365 суток"], 99.99) / 60, 52.56, rel_tol=1e-9)


def test_availability_formula():
    assert availability_percent(1000, 0) == 100
    assert math.isclose(availability_percent(1000, 1), 99.9)


def test_budget_table_size():
    # 5 целей x 4 периода
    assert len(budget_table()) == 20


def test_incident_scenario_numbers():
    rep = incident_report()
    assert rep["downtime_total_s"] == 215
    assert math.isclose(rep["budget_s"], 259.2)
    assert math.isclose(rep["remaining_s"], 44.2)
    assert math.isclose(rep["availability_percent"], 99.99170525, abs_tol=1e-7)
    assert math.isclose(rep["budget_used_percent"], 82.947, abs_tol=1e-3)


def test_next_60s_incident_does_not_fit():
    rep = incident_report()
    assert rep["survives_next_incident"] is False
    assert math.isclose(rep["overrun_if_next_s"], 15.8, abs_tol=1e-9)


def test_mttr_mtbf_consistent_with_availability():
    rep = incident_report()
    assert math.isclose(rep["mttr_s"], 215 / 3)
    # при непрерывном наблюдении MTBF/(MTBF+MTTR) совпадает с временной доступностью
    assert math.isclose(rep["mtbf_availability_percent"], rep["availability_percent"], rel_tol=1e-12)


def test_edge_cases():
    with pytest.raises(ValueError):
        availability_percent(0, 0)
    with pytest.raises(ValueError):
        availability_percent(100, 101)
    with pytest.raises(ValueError):
        allowed_downtime_s(100, 101)
    assert allowed_downtime_s(100, 100) == 0
