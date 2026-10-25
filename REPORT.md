# Практическая №3 — Git, DVC, ClearML

> Заполнять фактическими результатами команд. Не выдавать незапущенные действия за выполненные.

## Окружение
- Python: 3.12.10
- DVC: 3.64.0
- ClearML: 2.0.2
- scikit-learn: 1.7.2
- pandas: 2.3.3
- Git repository: mlops-data-zhanyshov

## История DVC
| Состояние | Git commit | SHA-256 iris.csv | SHA-256 wine.csv | SHA-256 data.dvc |
|---|---|---|---|---|
| data-v1 | da0d290 | 6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f | — | af9a6b92231af3d30166d4ec05038ab3fdebc3f28a1de1bea4cea5449e7fde76 |
| feature/wine | 93c6370 | 6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f | 38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60 | c42cbceead4c55e97976c576e2bc8dd9ab7037d776a1eff253e8ecde3170ff24 |
| feature/iris-features | 4ee314b | 3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26 | — | e6ba0d79a80bff8042f21fd623be1788c9babbd1a70a0fcc9293dbf4be1212c9 |
| merged/main | c3f065f | 3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26 | 38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60 | b63003486e5847feba08f387096e7a53191e49eae92790a231dc6c99bbce7692 |

DVC remote: локальная директория вне Git-репозитория, конкретный путь: ../dvc-storage.

Чистое восстановление: git clone mlops-data-zhanyshov mlops-data-test; poetry install; poetry run dvc pull; poetry run python check_data.py merged. Результат PASS, хэши совпали.

## ClearML Dataset lineage

```text
1.0.0 (BASE_ID: 0e6a69a486b14f059d7eac281ff54d0a)
├── 1.1.0 (WINE_ID: 375034975eb04f47820f912de0914b5d)
└── 2.0.0 (IRIS_FEATURES_ID: bcb0a0c8756f4dd2af2f4961facb3d23)
```

| Version | ID | Parent ID | Files | Added | Modified | Removed | SHA-256 / shape / columns |
|---|---|---|---|---|---|---|---|
| 1.0.0 | 0e6a69a486b14f059d7eac281ff54d0a | — | iris.csv | iris.csv | — | — | Iris: 150x5, SHA-256: 6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f |
| 1.1.0 | 375034975eb04f47820f912de0914b5d | 0e6a69a486b14f059d7eac281ff54d0a | iris.csv, wine.csv | wine.csv | — | — | Iris: 150x5; Wine: 178x14, SHA-256 Wine: 38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60 |
| 2.0.0 | bcb0a0c8756f4dd2af2f4961facb3d23 | 0e6a69a486b14f059d7eac281ff54d0a | iris.csv | — | iris.csv | — | Iris: 150x7, SHA-256: 3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26 |

Все три версии повторно скачаны в отдельные директории clearml_check/1.0.0, clearml_check/1.1.0, clearml_check/2.0.0. Проверен состав CSV.

## Сравнение
| Критерий | DVC | ClearML Dataset |
|---|---|---|
| Идентификатор версии | Git commit/tag плюс `data.dvc` с хэшем содержимого; подтверждено выполненными командами | Dataset ID; подтверждено выполненными командами |
| Метаданные | `.dvc` и Git | ClearML server |
| Файлы | DVC cache/remote | Dataset storage |
| Дочерняя версия | Ветка Git + `dvc add` | Dataset.create(parent_datasets=...) |
| Переключение | git switch + dvc checkout | Dataset.get(dataset_id=...) |
| Чистое восстановление | git clone + dvc pull | Dataset.get + get_local_copy |
| Ветвление | Git branches | Parent Dataset IDs |
| Слияние | Git/DVC merge, проверка данных | Явный состав потомков |
| Связь с Git | Прямая | Необязательная |
| UI | Обычно внешний UI Git-хостинга | ClearML web UI |

## Контрольные вопросы

1. **Какой объект однозначно определяет версию данных в DVC?** Значение content hash в `data.dvc` определяет содержимое отслеживаемых данных; Git commit/tag фиксирует, какая версия `data.dvc` выбрана.
2. **Почему Git-коммита недостаточно без DVC remote?** Git хранит метаданные, а не сами большие CSV: без доступного DVC cache/remote их не восстановить в чистом клоне.
3. **Dataset version и Dataset ID?** Версия `1.1.0` — человекочитаемая метка в проекте, а Dataset ID — уникальный идентификатор конкретного объекта на сервере.
4. **Почему finalize() не следующая версия?** `finalize()` завершает текущий Dataset; следующий создают новым вызовом Dataset.create().
5. **Как доказать parent 2.0.0?** Записать parent IDs из сервера: единственный parent `2.0.0` должен быть BASE_ID, не WINE_ID.
6. **Если не выполнить DVC checkout после git switch?** CSV в workspace могут остаться от предыдущего коммита, тогда метаданные Git не соответствуют данным.
7. **Когда удобнее DVC, а когда ClearML?** DVC удобен для Git-веток, merge и воспроизводимости из коммитов; ClearML — для lineage Dataset IDs, UI и скачивания опубликованных версий.
