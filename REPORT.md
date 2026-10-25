# Практическая работа №3 — версионирование данных с DVC и ClearML

## Окружение

| Компонент | Версия |
|---|---|
| Python | 3.12.10 |
| Git | 2.50.1 (Apple Git) |
| DVC | 3.64.0 |
| ClearML | 2.0.2 |
| scikit-learn | 1.7.2 |
| pandas | 2.3.3 |
| ОС | macOS (Apple Silicon) |

Репозиторий: https://github.com/tandrn/mlops-data-zhanyshov

## Git и DVC

| Состояние | Git commit / tag | SHA-256 `iris.csv` | SHA-256 `wine.csv` | SHA-256 `data.dvc` |
|---|---|---|---|---|
| Базовый Iris | `da0d290`, тег `data-v1` | `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f` | — | `af9a6b92231af3d30166d4ec05038ab3fdebc3f28a1de1bea4cea5449e7fde76` |
| `feature/wine` | `93c6370` | `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f` | `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60` | `c42cbceead4c55e97976c576e2bc8dd9ab7037d776a1eff253e8ecde3170ff24` |
| `feature/iris-features` до слияния | `4ee314b` | `3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26` | — | `e6ba0d79a80bff8042f21fd623be1788c9babbd1a70a0fcc9293dbf4be1212c9` |
| Итог после слияния | `c3f065f` | `3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26` | `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60` | `b63003486e5847feba08f387096e7a53191e49eae92790a231dc6c99bbce7692` |

Финальный коммит с отчётом перед его обновлением: `b9bc576` (`main`). Основные изменения данных сохранены отдельно от отчёта.

DVC remote: `storage`, локальная директория `../dvc-storage`, вне Git-репозитория. В Git сохранена конфигурация remote без credentials. Команды `dvc push` завершились успешно; `dvc status -c` показала, что кэш и remote синхронизированы.

В ветке `feature/wine` добавлен `wine.csv` без изменения Iris. В ветке `feature/iris-features` к Iris добавлены `sepal_area` и `petal_area`. Перед повторным слиянием создан `.gitattributes` и настроен merge driver. Слияние ветки `feature/wine` в `feature/iris-features` завершилось коммитом `c3f065f`, после чего итоговое состояние перенесено в `main`. Проверка `check_data.py merged`: **PASS**. В итоге `iris.csv` — 150 × 7, `wine.csv` — 178 × 14, пропусков нет.

### Чистое восстановление

Отдельно выполнены `git clone` в `mlops-data-test`, `poetry install`, `dvc pull` и `python check_data.py merged`. Команда `dvc pull` сообщила: **3 files fetched and 2 files added**. Проверка закончилась **PASS**, хэши Iris и Wine совпали с итоговыми значениями в таблице. Восстановление проверено в отдельном локальном клоне с доступом к общему локальному DVC remote. Доступность remote на другом компьютере этим тестом не проверялась.

## ClearML Dataset

Проект: `MIIT/MLOps/practice_3/zhanyshov`  
Имя датасета: `sklearn-tabular-zhanyshov`

### Версии и связи

```text
1.0.0 — 0e6a69a486b14f059d7eac281ff54d0a
├── 1.1.0 — 375034975eb04f47820f912de0914b5d
└── 2.0.0 — bcb0a0c8756f4dd2af2f4961facb3d23
```

| Version | Dataset ID | Parent ID | Полный список файлов | Added | Modified | Removed |
|---|---|---|---|---|---|---|
| `1.0.0` | `0e6a69a486b14f059d7eac281ff54d0a` | — | `iris.csv` | `iris.csv` | — | — |
| `1.1.0` | `375034975eb04f47820f912de0914b5d` | `0e6a69a486b14f059d7eac281ff54d0a` | `iris.csv`, `wine.csv` | `wine.csv` | — | — |
| `2.0.0` | `bcb0a0c8756f4dd2af2f4961facb3d23` | `0e6a69a486b14f059d7eac281ff54d0a` | `iris.csv` | — | `iris.csv` | — |

### Проверка скачанных файлов

Три версии получены по Dataset ID и скачаны в разные каталоги: `clearml_check/1.0.0`, `clearml_check/1.1.0`, `clearml_check/2.0.0`. Состав файлов подтверждён отдельно для каждого каталога. Также скрипт `clearml_datasets.py verify` проверил размеры, пропуски, столбцы, SHA-256 и родительские связи.

**1.0.0:**
- `iris.csv`: 150 × 5; SHA-256: `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f`.
- Столбцы: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.
- Пропусков: 0.

**1.1.0:**
- `iris.csv`: 150 × 5; SHA-256: `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f`.
- Столбцы Iris: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.
- `wine.csv`: 178 × 14; SHA-256: `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60`.
- Столбцы Wine: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.
- Пропусков: 0.

**2.0.0:**
- `iris.csv`: 150 × 7; SHA-256: `3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26`.
- Столбцы: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.
- Пропусков: 0.

Иерархия родителей подтверждена при `verify`: у обеих дочерних версий единственный parent — `1.0.0`. Версия `1.1.0` не является родителем `2.0.0`.

## Сравнение DVC и ClearML

| Критерий | DVC | ClearML Dataset |
|---|---|---|
| Идентификатор версии | `data.dvc` содержит хэш отслеживаемых данных, а Git фиксирует версию метаданных; для базы есть тег `data-v1` | Версии `1.0.0`, `1.1.0`, `2.0.0` получили разные Dataset ID |
| Метаданные | `data.dvc` и `.dvc/config` находятся в Git | Метаданные и parent ID получены через ClearML SDK |
| Файлы | Объекты отправлены в локальный `../dvc-storage` через `dvc push` | Файлы трёх версий загружены в хранилище ClearML |
| Дочерняя версия | Создавалась через Git-ветку, `dvc add data` и коммит | Для `1.1.0` и `2.0.0` указан `parent_datasets` с BASE_ID |
| Переключение | Использовались `git switch` и `dvc checkout` | Получены версии через `Dataset.get(dataset_id=...)` |
| Чистое восстановление | В `mlops-data-test` команда `dvc pull` восстановила два CSV, проверка `PASS` | Все три Dataset отдельно скачаны и проверены по ID |
| Ветвление | `feature/wine` и `feature/iris-features` независимо изменяли базовые данные | От `1.0.0` отдельно созданы `1.1.0` и `2.0.0` |
| Слияние | Коммит `c3f065f` объединил Wine и Iris с двумя новыми признаками; `PASS` | В этом сценарии создавались отдельные дочерние Dataset без слияния lineage |
| Связь с Git | Git-коммиты `93c6370`, `4ee314b` и `c3f065f` связаны с версиями данных через `data.dvc` | Dataset ID и связи версий доступны независимо от Git-коммита |
| UI | История веток и коммитов доступна на GitHub; работа с DVC выполнялась через CLI | В ClearML UI доступны версии, состав файлов и lineage |

## Контрольные вопросы

**1. Какой объект однозначно определяет версию данных в DVC?**

Хэш содержимого в `data.dvc`. По нему DVC понимает, какие именно данные нужны. А Git-коммит показывает, какой хэш использовался в конкретный момент.

**2. Почему одного Git-коммита недостаточно без DVC remote?**

Потому что Git хранит `data.dvc`, а не сами CSV. Если нужных файлов нет ни в кэше, ни в доступном remote, восстановить их не получится.

**3. Чем Dataset version отличается от Dataset ID в ClearML?**

Version — это обычный номер вроде `1.1.0`, чтобы было понятно, какая версия перед нами. Dataset ID — уникальный идентификатор, по которому ClearML находит конкретный датасет.

**4. Почему `finalize()` нельзя считать созданием следующей версии?**

Потому что `finalize()` только завершает текущую версию. Чтобы появилась следующая, надо создать новый Dataset через `Dataset.create()`.

**5. Как доказать, что ClearML version `2.0.0` создана от базы, а не от `1.1.0`?**

Посмотреть parent ID. У `2.0.0` указан ID базы `0e6a69a486b14f059d7eac281ff54d0a`. ID версии `1.1.0` среди родителей нет.

**6. Что произойдёт, если после `git switch` не выполнить DVC checkout?**

Git переключит метаданные, но CSV могут остаться от предыдущей ветки. Тогда файлы в папке не будут соответствовать выбранному коммиту.

**7. В каком сценарии этой работы удобнее DVC, а в каком ClearML Dataset?**

DVC удобнее для работы через Git: сделал ветку, изменил данные, сохранил коммит и потом объединил изменения. ClearML удобнее, когда надо посмотреть версии датасета, кто от кого наследуется, и скачать нужную версию по ID.
