"""개발자가 만든 연속형 가상 SEM 예제. 교수자 제공 자료나 실제 설문이 아니다."""
from pathlib import Path
import numpy as np
import pandas as pd


def make_sem_sample(n=300, seed=20261126):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    m = .65*x + np.sqrt(1-.65**2)*rng.normal(size=n)
    explained = .30**2 + .55**2 + 2*.30*.55*.65
    y = .30*x + .55*m + np.sqrt(1-explained)*rng.normal(size=n)
    data = {}
    for prefix, factor in [('x',x),('m',m),('y',y)]:
        for i, loading in enumerate([.85,.80,.75],1):
            indicator = loading*factor + np.sqrt(1-loading**2)*rng.normal(size=n)
            data[f'{prefix}{i}'] = 50 + 10*indicator
    return pd.DataFrame(data)


if __name__ == '__main__':
    make_sem_sample().to_csv(Path(__file__).with_name('sem_sample.csv'),index=False,float_format='%.8f')
