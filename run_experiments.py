"""Compare classifiers on the finalized Wine dataset from practice 3."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from clearml import Dataset, OutputModel, Task
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42


def scores(labels, predictions):
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
    }


def configurations():
    for c in (0.01, 0.1, 1.0):
        params = dict(C=c, solver="lbfgs", max_iter=2000, random_state=SEED)
        yield f"logreg-c{c}", "logistic_regression", params, make_pipeline(
            StandardScaler(), LogisticRegression(**params)
        )
    for n, depth in ((25, 2), (75, 4), (150, None)):
        params = dict(n_estimators=n, max_depth=depth, random_state=SEED, n_jobs=1)
        yield f"forest-n{n}-depth{depth}", "random_forest", params, RandomForestClassifier(
            **params
        )


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def publish(args, directory, name, best, split_metadata):
    disabled_integrations = (
        "detect_repository", "hydra", "scikit", "joblib", "matplotlib",
        "tensorflow", "tensorboard", "tfdefines", "pytorch", "megengine",
        "xgboost", "catboost", "fastai", "lightgbm", "gradio",
    )
    task = Task.init(
        project_name=f"MIIT/MLOps/practice_4/{args.surname}",
        task_name="wine-best-model",
        reuse_last_task_id=False,
        auto_connect_frameworks=dict.fromkeys(disabled_integrations, False),
        auto_connect_arg_parser=False,
        auto_resource_monitoring=False,
        auto_connect_streams=False,
        output_uri=True,
    )
    try:
        task.connect(
            {
                **split_metadata,
                "mlflow_run_id": best.info.run_id,
                **best.data.params,
            },
            name="Best run",
        )
        for key, value in best.data.metrics.items():
            task.get_logger().report_single_value(key, value)
        for filename in ("verification.json", "comparison.csv", "wine-model.joblib"):
            if not task.upload_artifact(
                filename, artifact_object=str(directory / filename), wait_on_upload=True
            ):
                raise RuntimeError(f"ClearML did not upload {filename}")
        output = OutputModel(
            task=task, name=name, framework="Scikit-Learn",
            label_enumeration={str(label): int(label) for label in (0, 1, 2)},
        )
        output.set_metadata("mlflow_run_id", best.info.run_id)
        output.set_metadata("clearml_dataset_id", args.dataset_id)
        uploaded = output.update_weights(
            weights_filename=str(directory / "wine-model.joblib"),
            upload_uri=task.output_uri,
            auto_delete_file=False,
            async_enable=False,
        )
        if not uploaded or not output.id:
            raise RuntimeError("ClearML did not register the uploaded model")
        task.flush(wait_for_uploads=True)
        output.publish()
        if not output.published:
            raise RuntimeError("ClearML did not publish the model")
        return {"clearml_task_id": task.id, "clearml_model_id": output.id}
    finally:
        task.close()


def run(args):
    if args.publish and args.cached_wine:
        raise ValueError("--publish requires obtaining Wine directly from ClearML")
    if args.cached_wine:
        wine_path = args.cached_wine
    else:
        dataset = Dataset.get(dataset_id=args.dataset_id, only_completed=True)
        wine_path = Path(dataset.get_local_copy()) / "wine.csv"
    digest = hashlib.sha256(wine_path.read_bytes()).hexdigest()
    if digest != args.expected_sha256.lower():
        raise ValueError(f"wine.csv SHA-256 mismatch: got {digest}")

    wine = pd.read_csv(wine_path)
    x, y = wine.drop(columns=["target"]), wine["target"]
    staging, test = train_test_split(x.index, test_size=0.2, stratify=y, random_state=SEED)
    train, validation = train_test_split(
        staging, test_size=0.25, stratify=y.loc[staging], random_state=SEED
    )
    metadata = {
        "dataset_id": args.dataset_id,
        "dataset_sha256": digest,
        "dataset_source": "verified_cached_download" if args.cached_wine else "clearml",
    }
    directory = args.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    split_path = directory / "split.json"
    write_json(split_path, {
        "random_state": SEED,
        **{name: sorted(map(int, subset)) for name, subset in (
            ("train", train), ("validation", validation), ("test", test)
        )},
    })

    mlflow.set_tracking_uri(args.tracking_uri)
    experiment = mlflow.set_experiment(f"miit-mlops-practice-4-{args.surname}")
    trained = {}
    logging_requirements = {}
    for name, family, params, model in configurations():
        with mlflow.start_run(run_name=name) as active:
            mlflow.set_tags({**metadata, "model_family": family})
            mlflow.log_params({"model_type": family, **params})
            started = perf_counter()
            model.fit(x.loc[train], y.loc[train])
            elapsed = perf_counter() - started
            logged_metrics = {
                **scores(y.loc[validation], model.predict(x.loc[validation])),
                "training_time": elapsed,
            }
            mlflow.log_metrics(logged_metrics)
            example = x.loc[train[:5]]
            mlflow.sklearn.log_model(
                model, name="model", input_example=example,
                signature=infer_signature(example, model.predict(example)),
            )
            mlflow.log_artifact(str(split_path))
            trained[active.info.run_id] = model
            logging_requirements[active.info.run_id] = (
                {"model_type": family, **params},
                logged_metrics,
                {**metadata, "model_family": family},
            )

    # Select from the runs created by this invocation, even when tracking history exists.
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.f1_weighted DESC", "attributes.run_name ASC"],
    )
    runs = runs[runs["run_id"].isin(trained)].copy()
    if len(runs) != 6 or not (runs["status"] == "FINISHED").all():
        raise RuntimeError("Expected six finished runs")
    client = mlflow.MlflowClient()
    for identifier, (params, run_metrics, tags) in logging_requirements.items():
        data = client.get_run(identifier).data
        if (
            any(data.params.get(key) != str(value) for key, value in params.items())
            or not run_metrics.keys() <= data.metrics.keys()
            or any(data.tags.get(key) != value for key, value in tags.items())
            or mlflow.models.get_model_info(f"runs:/{identifier}/model").signature is None
        ):
            raise RuntimeError(f"Incomplete logging for run {identifier}")
    columns = ["run_id", "tags.model_family", "metrics.f1_weighted", "metrics.training_time"]
    columns.extend(sorted(key for key in runs.columns if key.startswith("params.")))
    runs[columns].to_csv(directory / "comparison.csv", index=False)
    run_id = str(runs.iloc[0]["run_id"])
    uri = f"runs:/{run_id}/model"
    model = trained[run_id]
    loaded = mlflow.sklearn.load_model(uri)
    original_predictions = model.predict(x.loc[test])
    if not np.array_equal(original_predictions, loaded.predict(x.loc[test])):
        raise RuntimeError("Reloaded predictions differ")

    metrics = scores(y.loc[test], original_predictions)
    for key, value in metrics.items():
        client.log_metric(run_id, f"test_{key}", value)
    best = client.get_run(run_id)
    validation = scores(y.loc[validation], model.predict(x.loc[validation]))
    required_metrics = {"training_time", *metrics, *(f"test_{key}" for key in metrics)}
    signature = mlflow.models.get_model_info(uri).signature
    required_params = next(
        set(params) | {"model_type"}
        for name, _, params, _ in configurations()
        if name == best.info.run_name
    )
    if not (
        signature and required_metrics <= best.data.metrics.keys()
        and required_params <= best.data.params.keys()
        and all(best.data.tags.get(key) == value for key, value in metadata.items())
    ):
        raise RuntimeError("Missing model signature, parameters, metrics or dataset tags")
    verification = {
        "experiment_id": experiment.experiment_id,
        "best_run_id": run_id,
        "model_uri": uri,
        **metadata,
        "predictions_match": True,
        "signature_present": True,
        "feature_names": list(x.columns),
        "validation": validation,
        "test": metrics,
    }
    verification_path = directory / "verification.json"
    write_json(verification_path, verification)
    client.log_artifact(run_id, str(verification_path))
    client.log_artifact(run_id, str(directory / "comparison.csv"))
    joblib.dump(loaded, directory / "wine-model.joblib")
    if args.publish:
        verification.update(publish(args, directory, best.info.run_name, best, metadata))
        write_json(verification_path, verification)
    print(f"Experiment {experiment.experiment_id} / run {run_id} / test F1 {metrics['f1_weighted']:.4f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking-uri", default=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--surname", default="zhanyshov")
    parser.add_argument("--output-dir", type=Path, default=Path("experiment-reports"))
    parser.add_argument("--cached-wine", type=Path, help="Previously downloaded practice 3 file")
    parser.add_argument("--publish", action="store_true", help="Publish the winning model to ClearML")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
