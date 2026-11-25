"""상관분석과 제한된 연속형 잠재변수 CFA/SEM. 화면과 독립적으로 검산한다."""
from __future__ import annotations

from itertools import combinations, permutations
import math
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from analysis import AnalysisError, _columns, _prepare, numeric_series

SEM_TEMPLATES = {
    '2변수 구조모형: X → Y': ('X', 'Y'),
    '3변수 구조모형: X → M → Y, X → Y': ('X', 'M', 'Y'),
    '2요인 측정모형 (CFA)': ('X', 'Y'),
    '3요인 측정모형 (CFA)': ('X', 'M', 'Y'),
}


def _rank_permutation_p(x, y, seed, n_perm):
    """양측 |rho| 검정. n<=7 전수 순열, 그 외 Monte Carlo +1 보정."""
    a = stats.rankdata(x).astype(float)
    b = stats.rankdata(y).astype(float)
    a -= a.mean()
    b -= b.mean()
    a /= np.linalg.norm(a)
    b /= np.linalg.norm(b)
    observed = abs(float(a @ b))
    tolerance = 1e-12
    if len(a) <= 7:
        extreme = sum(abs(float(a @ b[list(order)])) >= observed-tolerance
                      for order in permutations(range(len(a))))
        count = math.factorial(len(a))
        return extreme/count, '정확 순열 (양측 |ρ|)', count
    rng = np.random.default_rng(seed)
    extreme = 0
    # A small batch bounds memory even near the 500-case permutation threshold.
    for start in range(0, n_perm, 256):
        count = min(256, n_perm-start)
        permuted = np.stack([rng.permutation(b) for _ in range(count)])
        extreme += int(np.count_nonzero(np.abs(permuted @ a) >= observed-tolerance))
    return (extreme+1)/(n_perm+1), 'Monte Carlo 순열 (+1, 양측 |ρ|)', n_perm


def correlation_analysis(df, columns, method='Pearson', missing='pairwise', seed=42, n_perm=4999):
    """행렬, 쌍별 사례 수, 양측 p, Holm p, Pearson Fisher CI를 반환한다."""
    _columns(df, columns)
    if not 2 <= len(columns) <= 10:
        raise AnalysisError('상관분석은 서로 다른 수치형 변수 2~10개를 선택해 주세요.')
    if method not in ('Pearson', 'Spearman') or missing not in ('pairwise', 'listwise'):
        raise AnalysisError('상관계수 종류와 결측 처리 방식을 확인해 주세요.')
    if not isinstance(seed, int) or not 0 <= seed <= 2147483647:
        raise AnalysisError('순열검정 시드는 0~2147483647의 정수여야 합니다.')
    if not isinstance(n_perm, int) or not 999 <= n_perm <= 9999:
        raise AnalysisError('순열검정 반복 횟수는 999~9999 사이여야 합니다.')
    data = pd.DataFrame({c: numeric_series(df[c]) for c in columns})
    complete_n = int(data.notna().all(axis=1).sum())
    if missing == 'listwise':
        data = data.dropna()
    matrices = {name: pd.DataFrame(np.nan, index=columns, columns=columns)
                for name in ('correlation', 'pvalues', 'adjusted_pvalues', 'counts')}
    for name in columns:
        s = data[name].dropna()
        matrices['counts'].loc[name, name] = len(s)
        if len(s) >= 3 and s.nunique() > 1:
            matrices['correlation'].loc[name, name] = 1.
    rows, messages = [], []
    for left, right in combinations(columns, 2):
        pair = data[[left, right]].dropna()
        n = len(pair)
        r = p = lo = hi = np.nan
        repeats, test = 0, '계산 불가'
        if n < 3 or pair[left].nunique() < 2 or pair[right].nunique() < 2:
            messages.append(f'{left}–{right}: 유효 사례가 3개 미만이거나 한 변수가 상수여서 계산하지 않았습니다.')
        else:
            x, y = pair[left].to_numpy(), pair[right].to_numpy()
            if method == 'Pearson':
                result = stats.pearsonr(x, y)
                r, p = float(result.statistic), float(result.pvalue)
                test = 'Pearson 양측 검정'
                if n > 3:
                    if abs(r) >= 1-1e-14:
                        lo = hi = float(np.sign(r))
                    else:
                        z = np.arctanh(r)
                        lo, hi = np.tanh(z + np.array([-1, 1])*stats.norm.ppf(.975)/np.sqrt(n-3))
            else:
                result = stats.spearmanr(x, y)
                r = float(result.statistic)
                if n <= 500:
                    p, test, repeats = _rank_permutation_p(x, y, seed, n_perm)
                else:
                    p, test = float(result.pvalue), 'Spearman 양측 근사 (n>500)'
        rows.append({'변수1':left, '변수2':right, '사용 사례 수(n)':n,
                     '제외 사례 수':len(df)-n, '상관계수':r, 'p':p,
                     '95% CI 하한':lo, '95% CI 상한':hi, '검정 방식':test, '순열 수':repeats})
        for name, value in [('correlation',r), ('pvalues',p), ('counts',n)]:
            matrices[name].loc[left,right] = matrices[name].loc[right,left] = value
    pairs = pd.DataFrame(rows)
    valid = pairs['p'].notna()
    if not valid.any():
        raise AnalysisError('계산 가능한 변수 쌍이 없습니다. 사례 수, 결측값과 상수 변수를 확인해 주세요.')
    pairs['보정 p'] = np.nan
    pairs.loc[valid, '보정 p'] = multipletests(pairs.loc[valid,'p'], method='holm')[1]
    for row in pairs.to_dict('records'):
        matrices['adjusted_pvalues'].loc[row['변수1'],row['변수2']] = row['보정 p']
        matrices['adjusted_pvalues'].loc[row['변수2'],row['변수1']] = row['보정 p']
    pairs.insert(6, '보정 p', pairs.pop('보정 p'))
    messages.append('Holm 보정은 계산 가능한 고유 변수 쌍 전체에 적용합니다. 쌍별 검정 전 p와 보정 p를 구분하세요.')
    if missing == 'pairwise':
        messages.append('쌍별 결측 제외에서는 비교마다 사례가 달라집니다. 이 행렬을 SEM의 입력 공분산으로 사용하지 마세요.')
    if method == 'Pearson':
        messages.append('Pearson p와 Fisher 95% 신뢰구간은 독립 관측과 이변량 정규성 가정에 유의하세요. n=3이면 CI를 표시하지 않습니다.')
    else:
        messages.append('Spearman은 평균 순위를 사용합니다. n≤7은 전수 순열, 8~500은 4,999회 순열, n>500은 근사 p입니다. Spearman 신뢰구간은 제공하지 않습니다.'.replace('4,999',f'{n_perm:,}'))
    messages.append('상관계수는 인과관계를 뜻하지 않습니다. 독립 관측을 전제로 하며 반복측정·군집 자료를 보정하지 않습니다.')
    return dict(matrices, pairs=pairs, data=data, total=len(df), complete_n=complete_n,
                method=method, missing=missing, warnings=messages, seed=seed)


def _sem_fit_indices(sample_cov, implied_cov, n, n_parameters):
    """ML discrepancy와 대각 독립모형으로 계산. RMSEA는 semopy의 N−1 규약."""
    p = sample_cov.shape[0]
    df = p*(p+1)//2-n_parameters
    if df <= 0:
        raise AnalysisError('모형 자유도가 0 이하라 적합도를 평가할 수 없습니다.')
    sign_s, log_s = np.linalg.slogdet(sample_cov)
    sign_m, log_m = np.linalg.slogdet(implied_cov)
    if sign_s <= 0 or sign_m <= 0:
        raise AnalysisError('공분산 행렬이 양의 정부호가 아닙니다. 중복 변수와 모형을 확인해 주세요.')
    discrepancy = float(log_m + np.trace(np.linalg.solve(implied_cov,sample_cov)) - log_s - p)
    if discrepancy < -1e-7 or not np.isfinite(discrepancy):
        raise AnalysisError('안정적인 적합도 계산에 실패했습니다. 변수 단위와 모형을 확인해 주세요.')
    chi2 = n*max(0., discrepancy)
    baseline_df = p*(p-1)//2
    baseline_chi2 = n*max(0., float(np.log(np.diag(sample_cov)).sum()-log_s))
    denominator = baseline_chi2-baseline_df
    cfi = 1-(chi2-df)/denominator if denominator > 1e-12 else np.nan
    tli = (baseline_chi2/baseline_df-chi2/df)/(baseline_chi2/baseline_df-1) if denominator > 1e-12 else np.nan
    rmsea = float(np.sqrt(max(chi2/df-1,0)/(n-1)))
    return {'χ²':chi2, 'df':df, 'p':float(stats.chi2.sf(chi2,df)), 'CFI':cfi, 'TLI':tli,
            'RMSEA':rmsea, '기준모형 χ²':baseline_chi2, '기준모형 df':baseline_df,
            '사용 사례 수(n)':n, '자유 모수 수':n_parameters}


def latent_variable_analysis(df, factors, template):
    """상관된 2/3요인 CFA 또는 X→Y, X→M→Y+X→Y SEM. 사용자 모형문은 실행하지 않음."""
    if template not in SEM_TEMPLATES or tuple(factors) != SEM_TEMPLATES[template]:
        raise AnalysisError('잠재변수 구성과 모형 유형이 맞지 않습니다.')
    for name, items in factors.items():
        if not 3 <= len(items) <= 6:
            raise AnalysisError(f'잠재변수 {name}에는 서로 다른 관측지표 3~6개가 필요합니다.')
    columns = [c for items in factors.values() for c in items]
    _columns(df, columns)
    data, info = _prepare(df, columns)
    if len(data) < 50:
        raise AnalysisError('CFA/SEM은 이 앱에서 유효 사례가 최소 50개 필요합니다. 왼쪽의 ‘구조방정식 예제로 연습’을 선택하거나 더 큰 자료를 사용하세요. 50은 실행 제한이며 표본 적정성 기준은 아닙니다.')
    values = data.to_numpy(dtype=float)
    sample = np.cov(values, rowvar=False, bias=True)
    scale = np.sqrt(np.diag(sample))
    correlation = sample/np.outer(scale,scale)
    if not np.isfinite(correlation).all() or np.linalg.eigvalsh(correlation).min() <= 1e-8:
        raise AnalysisError('관측지표 사이에 완전하거나 거의 완전한 중복 관계가 있습니다. 합계 점수와 그 문항을 함께 넣지 마세요.')
    if scale.max()/scale.min() > 10000:
        raise AnalysisError('관측지표의 단위 차이가 너무 큽니다. 단위를 정리하거나 표준화한 자료로 다시 실행해 주세요.')
    # Safe synthetic symbols prevent arbitrary column names from entering model syntax.
    observed = {c:f'v{i:02d}' for i,c in enumerate(columns)}
    latent = {name:f'F{i}' for i,name in enumerate(factors)}
    labels = {v:k for k,v in observed.items()}
    labels.update({v:k for k,v in latent.items()})
    lines = [latent[name]+' =~ '+' + '.join(observed[c] for c in items) for name,items in factors.items()]
    is_cfa = '(CFA)' in template
    if is_cfa:
        lines += [latent[a]+' ~~ '+latent[b] for a,b in combinations(factors,2)]
    elif 'M' in factors:
        lines += [latent['M']+' ~ '+latent['X'],latent['Y']+' ~ '+latent['M']+' + '+latent['X']]
    else:
        lines += [latent['Y']+' ~ '+latent['X']]
    description = '\n'.join(lines)
    try:
        from semopy import Model
    except ImportError as exc:
        raise AnalysisError('구조방정식 패키지가 없습니다. requirements.txt로 설치하거나 자동 실행기를 다시 실행해 주세요.') from exc
    try:
        model = Model(description)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            fit = model.fit(data.rename(columns=observed), obj='MLW', solver='SLSQP',
                            options={'maxiter':2000,'ftol':1e-10})
        if not fit.success or not np.isfinite(model.param_vals).all():
            raise AnalysisError('모형이 수렴하지 않았습니다. 지표 선택과 자료의 분포를 확인해 주세요.')
        sigma, (_, latent_inverse) = model.calc_sigma()
        info_matrix = model.calc_fim()
        diagonal = np.sqrt(np.maximum(np.diag(info_matrix),0))
        if np.any(diagonal <= 0):
            raise AnalysisError('모형의 정보를 충분히 구분할 수 없습니다. 잠재변수와 지표를 다시 구성해 주세요.')
        scaled_information = info_matrix/np.outer(diagonal,diagonal)
        if np.linalg.eigvalsh(scaled_information).min() <= 1e-9:
            raise AnalysisError('모형의 식별 또는 수치 안정성 문제가 있습니다. 서로 구별되는 지표를 사용해 주세요.')
        raw_parameters = model.inspect(std_est=True)
        fit_values = _sem_fit_indices(model.mx_cov, sigma, len(data), len(model.param_vals))
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError('CFA/SEM 추정에 실패했습니다. 중복 지표, 자료 단위와 모형 구성을 확인해 주세요.') from exc

    parameter_rows, messages = [], []
    factor_symbols = set(latent.values())
    marker_symbols = {observed[items[0]] for items in factors.values()}
    for row in raw_parameters.to_dict('records'):
        left,right,op = row['lval'],row['rval'],row['op']
        fixed = op == '~' and left in marker_symbols and right in factor_symbols
        se = pd.to_numeric(row['Std. Err'], errors='coerce')
        estimate = float(row['Estimate'])
        standardized = float(row['Est. Std'])
        z = estimate/float(se) if np.isfinite(se) and se > 0 else np.nan
        pvalue = float(2*stats.norm.sf(abs(z))) if np.isfinite(z) else np.nan
        kind = ('요인부하량' if op == '~' and left not in factor_symbols else
                '구조경로' if op == '~' else '분산' if left==right else '공분산')
        parameter_rows.append({'구분':kind,'결과':labels[left],'관계':op,'설명':labels[right],
                               'B':estimate,'표준화 추정치':standardized,'SE(B)':se,'z':z,'p':pvalue,
                               'B 95% CI 하한':estimate-1.959963984540054*se if np.isfinite(se) else np.nan,
                               'B 95% CI 상한':estimate+1.959963984540054*se if np.isfinite(se) else np.nan,
                               '고정 모수':fixed})
    parameters = pd.DataFrame(parameter_rows)
    free = ~parameters['고정 모수']
    if not np.isfinite(parameters.loc[free, ['B','표준화 추정치','SE(B)']].to_numpy(float)).all():
        raise AnalysisError('일부 표준오차 또는 표준화 추정치를 안정적으로 계산할 수 없습니다.')
    latent_cov = latent_inverse @ model.mx_psi @ latent_inverse.T
    if np.linalg.eigvalsh(latent_cov).min() <= 0 or np.linalg.eigvalsh(model.mx_psi).min() < -1e-8:
        raise AnalysisError('잠재변수 공분산 또는 잔차 공분산이 부적절한 해입니다. 지표와 모형을 다시 확인해 주세요.')
    variances = parameters[parameters['구분']=='분산']
    if (variances['B'] <= 1e-8).any():
        messages.append('일부 분산이 0 경계에 있습니다. 부적절한 해(Heywood 문제) 가능성이 있으므로 일반적인 결과처럼 해석하지 마세요.')
    if (parameters.loc[parameters['구분']=='요인부하량','표준화 추정치'].abs() > 1+1e-6).any():
        messages.append('절댓값이 1을 넘는 표준화 요인부하량이 있습니다. 측정모형의 부적절한 해를 점검하세요.')
    r_squared = []
    if not is_cfa:
        for name in factors:
            if name == 'X':
                continue
            idx = model.vars['inner'].index(latent[name])
            r2 = 1-model.mx_psi[idx,idx]/latent_cov[idx,idx]
            r_squared.append({'잠재변수':name,'R²':float(r2)})
    order = model.vars['observed']
    observed_names = [labels[c] for c in order]
    messages.extend([
        '연속형 지표, 독립 관측, 다변량 정규성을 전제로 하는 MLW 추정입니다. 평균·절편 모형, 순서형 전용 추정, 다집단·다층모형은 지원하지 않습니다.',
        '잠재변수마다 첫 번째 지표의 비표준화 부하량을 1로 고정했습니다. 고정 모수에는 SE·p·CI가 없습니다. SE·z·p·CI는 비표준화 B에 대한 값입니다.',
        'CFI·TLI는 원값을 표시하므로 0~1을 벗어날 수 있습니다. RMSEA는 N−1 분모 규약입니다. 적합도 하나만으로 모형이 참이거나 인과적이라고 판단하지 마세요.',
        '최소 50사례는 앱의 실행 제한입니다. 필요한 표본 크기는 모형 복잡도·부하량·자료 분포에 따라 달라집니다. 잠재변수 간접효과의 유의성·부트스트랩 CI는 이 메뉴에서 제공하지 않습니다.',
    ])
    return dict(info, data=data, parameters=parameters,
                loadings=parameters[parameters['구분']=='요인부하량'].reset_index(drop=True),
                paths=parameters[parameters['구분']=='구조경로'].reset_index(drop=True),
                variances=parameters[parameters['구분'].isin(['분산','공분산'])].reset_index(drop=True),
                fit=pd.DataFrame([fit_values]), fit_values=fit_values, r_squared=pd.DataFrame(r_squared),
                observed_covariance=pd.DataFrame(model.mx_cov,index=observed_names,columns=observed_names),
                implied_covariance=pd.DataFrame(sigma,index=observed_names,columns=observed_names),
                residual_covariance=pd.DataFrame(model.mx_cov-sigma,index=observed_names,columns=observed_names),
                mapping=pd.DataFrame([{'내부명':v,'원래 변수':k} for k,v in {**observed,**latent}.items()]),
                syntax=description, template=template, warnings=messages, converged=True)
