import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
from clearml import Dataset

from prepare_data import main as prepare
from check_data import main as validate

PROJECT = 'MIIT/MLOps/practice_3/zhanyshov'
NAME = 'sklearn-tabular-zhanyshov'
IDS_PATH = Path('clearml_ids.json')
DOWNLOADS = Path('clearml_downloads')

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def create(version, parent=None, mode='base', only_file=None):
    prepare(mode)
    validate(mode)
    options = dict(dataset_project=PROJECT, dataset_name=NAME, dataset_version=version)
    if parent:
        options['parent_datasets'] = [parent]
    ds = Dataset.create(**options)
    ds.add_files(path=str(Path('data') / only_file) if only_file else 'data', dataset_path='.')
    if version == '1.0.0':
        ds.add_tags(['base'])
    ds.upload()
    ds.finalize()
    print(f'{version}: {ds.id}')
    return ds.id

def verify(ids):
    expected = {'BASE_ID': ('1.0.0', {'iris.csv'}),
                'WINE_ID': ('1.1.0', {'iris.csv', 'wine.csv'}),
                'IRIS_FEATURES_ID': ('2.0.0', {'iris.csv'})}
    DOWNLOADS.mkdir(exist_ok=True)
    for key, (version, files) in expected.items():
        ds = Dataset.get(dataset_id=ids[key])
        destination = DOWNLOADS / version.replace('.', '_')
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir()
        ds.get_mutable_local_copy(target_folder=str(destination), overwrite=True)
        actual = {p.name for p in destination.rglob('*.csv')}
        if actual != files:
            raise RuntimeError(f'{key}: expected {files}, found {actual}')
        print(f'{key} = {ds.id} | version = {version} | files = {sorted(actual)}')
        for path in sorted(destination.rglob('*.csv')):
            df = pd.read_csv(path)
            print(f'  {path.name} | sha256={sha256(path)} | shape={df.shape} | nulls={df.isna().sum().sum()} | columns={list(df.columns)}')
        print(f'  parent IDs (verify in ClearML UI): {ds.get_dependency_graph()}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['create', 'verify'])
    args = parser.parse_args()
    if args.action == 'create':
        if IDS_PATH.exists():
            raise SystemExit(f'{IDS_PATH} already exists; refusing to create duplicates')
        base = create('1.0.0', mode='base')
        wine = create('1.1.0', parent=base, mode='wine', only_file='wine.csv')
        features = create('2.0.0', parent=base, mode='iris_features', only_file='iris.csv')
        ids = {'BASE_ID': base, 'WINE_ID': wine, 'IRIS_FEATURES_ID': features}
        IDS_PATH.write_text(json.dumps(ids, indent=2) + '\n')
        print('Dataset IDs saved to clearml_ids.json')
    else:
        if not IDS_PATH.exists():
            raise SystemExit('Missing clearml_ids.json; first run create')
        verify(json.loads(IDS_PATH.read_text()))

if __name__ == '__main__':
    main()
