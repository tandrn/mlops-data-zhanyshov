import argparse
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, load_wine


def check_file(path, loader, with_features=False):
    if not path.is_file():
        raise ValueError(f'Missing expected file: {path}')
    df = pd.read_csv(path)
    expected = loader(as_frame=True).frame
    cols = list(expected.columns)
    if with_features:
        cols += ['sepal_area', 'petal_area']
    if any(str(c).startswith('Unnamed:') for c in df.columns):
        raise ValueError(f'Unnamed index column in {path}')
    if list(df.columns) != cols:
        raise ValueError(f'Wrong columns in {path}: {list(df.columns)}')
    if len(df) != len(expected):
        raise ValueError(f'Wrong row count in {path}')
    expected = expected.sort_values(list(expected.columns), kind='mergesort').reset_index(drop=True)
    if not np.allclose(df[list(expected.columns)].to_numpy(), expected.to_numpy(), rtol=0, atol=1e-9):
        raise ValueError(f'Original data changed in {path}')
    if with_features:
        for name, a, b in [('sepal_area', 'sepal length (cm)', 'sepal width (cm)'),
                           ('petal_area', 'petal length (cm)', 'petal width (cm)')]:
            if not np.allclose(df[name], df[a] * df[b], rtol=0, atol=1e-9):
                raise ValueError(f'Invalid {name} in {path}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f'{path} | SHA-256: {digest} | shape: {df.shape} | nulls: {int(df.isna().sum().sum())} | columns: {list(df.columns)}')


def main(mode):
    directory = Path('data')
    iris = directory / 'iris.csv'
    wine = directory / 'wine.csv'
    check_file(iris, load_iris, with_features=mode in ('iris_features', 'merged'))
    if mode in ('wine', 'merged'):
        check_file(wine, load_wine)
    elif wine.exists():
        raise ValueError('Unexpected data/wine.csv')
    files = {p.name for p in directory.glob('*.csv')}
    required = {'iris.csv', 'wine.csv'} if mode in ('wine', 'merged') else {'iris.csv'}
    if files != required:
        raise ValueError(f'Unexpected CSV set: {files}')
    print('PASS')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['base', 'wine', 'iris_features', 'merged'])
    main(parser.parse_args().mode)
