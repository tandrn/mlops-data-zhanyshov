# Практики 3–4. Версионирование данных и учёт экспериментов

Практика 3 использует DVC и ClearML. Версии данных, контрольные суммы и
результаты проверки описаны в [REPORT.md](REPORT.md). Для восстановления
итоговой версии DVC нужен доступ к хранилищу `storage`. В учебном репозитории
оно настроено как `../dvc-storage`, рядом с клоном.

```sh
poetry env use python3.12
poetry install
poetry run dvc pull
poetry run python check_data.py merged
```

Если копия хранилища находится в другом месте, укажите её путь локально через
`poetry run dvc remote modify --local storage url /path/to/dvc-storage`.
Для проверки версий ClearML после настройки SDK используйте
`poetry run python clearml_datasets.py verify`.

## Практика 4

```sh
poetry env use python3.12
poetry install
poetry run python -m pip check
poetry run clearml-init
poetry run python run_experiments.py \
  --dataset-id 375034975eb04f47820f912de0914b5d \
  --expected-sha256 38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60 \
  --publish
```

ClearML использует локальную конфигурацию SDK. Ключи хранятся вне репозитория.
Скрипт загружает финализированный датасет Wine и проверяет SHA-256. Для
локальной проверки можно передать скачанный в практике 3 файл через
`--cached-wine clearml_check/1.1.0/wine.csv` и опустить `--publish`.
Скрипт применяет ту же проверку SHA-256 для локального файла.

По умолчанию запуски записываются в локальный SQLite. Интерфейс MLflow
доступен по адресу `http://127.0.0.1:5000` после запуска из корня проекта.

```sh
poetry run mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1
```

Для другого сервера задайте `--tracking-uri` или `MLFLOW_TRACKING_URI`.
Выходные файлы сохраняются в `experiment-reports/`. В корне находится
[verification.json](verification.json) с результатом проверенного прогона и идентификаторами опубликованной модели.
Ссылки на ClearML Task и OutputModel приведены в [REPORT.md](REPORT.md).
