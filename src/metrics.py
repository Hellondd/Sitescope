"""Метрики качества поиска (без зависимости от Elasticsearch)."""


def precision_at_k(returned_ids, relevant_ids, k=5):
    """Precision@k = (число релевантных среди первых k результатов) / k.

    Делим именно на k (а не на len(returned)), как принято в классическом определении:
    если поиск вернул меньше k документов, недостающие позиции считаются нерелевантными.
    """
    if k <= 0:
        raise ValueError("k должно быть > 0")
    relevant = set(relevant_ids)
    top = list(returned_ids)[:k]
    hits = sum(1 for doc_id in top if doc_id in relevant)
    return hits / k


def mean(values):
    values = list(values)
    if not values:
        raise ValueError("пустой список")
    return sum(values) / len(values)
