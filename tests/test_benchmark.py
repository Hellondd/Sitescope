from benchmark import (binary_search, build_dict, build_sorted, dict_search, linear_search,
                       make_dataset, median_us_per_lookup, run_benchmark, verify_same_results)


def test_three_algorithms_return_same_results():
    records, existing, missing = make_dataset(1000)
    assert verify_same_results(records, existing + missing)


def test_found_and_missing_keys():
    records, existing, missing = make_dataset(1000)
    sorted_ids, sorted_records = build_sorted(records)
    index = build_dict(records)
    for k in existing:
        assert linear_search(records, k)["id"] == k
        assert binary_search(sorted_ids, sorted_records, k)["id"] == k
        assert dict_search(index, k)["id"] == k
    for k in missing:
        assert linear_search(records, k) is None
        assert binary_search(sorted_ids, sorted_records, k) is None
        assert dict_search(index, k) is None


def test_dataset_shape():
    records, existing, missing = make_dataset(1000)
    ids = {r["id"] for r in records}
    assert len(ids) == 1000
    assert len(existing) == 100 and set(existing) <= ids
    assert len(missing) == 100 and not (set(missing) & ids)


def test_binary_search_edge_cases():
    assert binary_search([], [], 5) is None
    assert binary_search([7], [{"id": 7}], 7) == {"id": 7}
    assert binary_search([7], [{"id": 7}], 8) is None


def test_median_is_positive_and_uses_median():
    calls = []
    t = median_us_per_lookup(lambda k: calls.append(k), [1, 2, 3], repeats=5)
    assert t >= 0
    assert len(calls) == 15        # 5 повторов x 3 ключа


def test_run_benchmark_small():
    search_rows, prep_rows = run_benchmark(sizes=(1000,), repeats=5)
    assert len(search_rows) == 2 and len(prep_rows) == 1
    for r in search_rows:
        assert r["linear_us"] > 0 and r["binary_us"] > 0 and r["dict_us"] > 0
