import argparse
from pathlib import Path
import pandas as pd
from sklearn.datasets import load_iris, load_wine

DATA = Path('data')

def frame(loader):
    dataset = loader(as_frame=True)
    df = dataset.frame.copy()
    keys = list(dataset.feature_names) + ['target']
    return df.sort_values(keys, kind='mergesort').reset_index(drop=True)

def save(df, filename):
    DATA.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA / filename, index=False, float_format='%.12g', lineterminator='\n')


def main(mode):
    if mode == 'base':
        iris = frame(load_iris)
        save(iris, 'iris.csv')
        (DATA / 'wine.csv').unlink(missing_ok=True)
    elif mode == 'wine':
        if not (DATA / 'iris.csv').is_file():
            raise SystemExit('First create base Iris: python prepare_data.py base')
        save(frame(load_wine), 'wine.csv')
    elif mode == 'iris_features':
        iris = frame(load_iris)
        iris['sepal_area'] = iris['sepal length (cm)'] * iris['sepal width (cm)']
        iris['petal_area'] = iris['petal length (cm)'] * iris['petal width (cm)']
        save(iris, 'iris.csv')
        (DATA / 'wine.csv').unlink(missing_ok=True)
    print(f'Prepared mode: {mode}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['base', 'wine', 'iris_features'])
    main(parser.parse_args().mode)
