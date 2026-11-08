# SiteScope — учебный проект (пересдача «Технология разработки ПО»)

Автор: Кулягин Владимир Викторович, группа 9/4-РПО-23/2.

Проект состоит из пяти частей: (I) аудит двух сайтов, (II) поиск и релевантность в Elasticsearch,
(III) бенчмарк алгоритмов поиска по id, (IV) доступность 99,99 % и бюджет простоя, (V) «кривая ванны».

## Требования

| Что | Версия / объём |
|---|---|
| Python | 3.11+ (проверено на 3.12) |
| Docker (Desktop или Engine) + Compose v2 | любая актуальная версия |
| Elasticsearch | 8.15.0 (официальный образ, см. `docker-compose.yml`) |
| RAM | ~2 ГБ свободной памяти под Docker (в `ES_JAVA_OPTS` heap = 512 МБ) |
| Зависимости Python | `requirements.txt` (elasticsearch, matplotlib, pytest) |

## Установка

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1      Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
```

## Структура

```
src/        Python-скрипты (generate_catalog, index_data, search_queries, search, benchmark,
            availability, bathtub, audit_summary, metrics)
data/       catalog.jsonl — синтетический каталог (1000 документов, seed = 42)
queries/    index_mapping.json и Query DSL: scenarios/*.json, precision_queries.json
results/    CSV/JSON/PNG с результатами
tests/      pytest-тесты
docker-compose.yml   локальный одновузловой Elasticsearch
```

## Порядок получения результатов

```bash
# Часть I. Аудит: данные PageSpeed (8 прогонов) лежат в results/audit_pagespeed.csv
python src/audit_summary.py

# Часть II. Elasticsearch
python src/generate_catalog.py             # пересоздать data/catalog.jsonl (воспроизводимо)
docker compose up -d                       # запустить Elasticsearch, подождать ~30-60 с
curl http://127.0.0.1:9200                 # проверка: версия и cluster_name
python src/index_data.py                   # индекс sitescope-pages, mapping, bulk-загрузка
python src/search_queries.py               # 7 сценариев Query DSL + Precision@5 + демо анализа текста
python src/search.py --query "Docker контейнеры" --category devops --limit 3   # необязательный CLI

# Часть III. Бенчмарк (результаты зависят от компьютера — запускайте у себя)
python src/benchmark.py                    # 7 повторов, медиана

# Часть IV и V
python src/availability.py
python src/bathtub.py

# Тесты
pytest -q
```

Остановить Elasticsearch: `docker compose down` (данные хранятся в томе `esdata`; `docker compose down -v` удалит и том).

## Безопасность и ограничения

* **Elasticsearch запущен БЕЗ аутентификации** (`xpack.security.enabled=false`) — это допустимо только для
  локальной учебной работы. Порт привязан к `127.0.0.1:9200`, из сети сервис недоступен. Не открывайте его в интернет.
* Каталог **синтетический**: 28 документов (`man-01…man-28`) подготовлены вручную как эталон для Precision@5,
  остальные генерируются случайно (seed = 42). Реальных пользовательских данных в проекте нет.
* Оценка релевантности (Precision@5) выполнена по небольшой выборке из 5 запросов — это учебная оценка, а не
  статистически значимое исследование. Эталон составлен вручную до запуска поиска.
* Бенчмарк (часть III) измеряет **только** поиск по числовому id в памяти Python. Elasticsearch туда не входит:
  его время включает сеть, HTTP, индекс, анализ текста и ранжирование — это другая операция.
* Результаты PageSpeed Insights — лабораторные (Lighthouse), зависят от сети, нагрузки и времени проверки.
  Поле INP не измерялось и не приводится. Два прогона на каждое сочетание «сайт × режим» показывают разброс.
* Модель «кривой ванны» — синтетическая иллюстрация, не прогноз для конкретного продукта.
* Расчёты доступности — это временная доступность без исключения планового обслуживания; доля успешных запросов
  при частичной деградации может отличаться.
