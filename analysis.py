"""교육용 통계 계산. 화면 코드와 분리하여 독립적으로 검산한다."""
from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor


class AnalysisError(ValueError):
    """사용자에게 그대로 보여 줄 수 있는 한국어 입력 오류."""


def _columns(df, columns):
    if not columns:
        raise AnalysisError('변수를 한 개 이상 선택해 주세요.')
    if len(set(columns)) != len(columns):
        raise AnalysisError('서로 다른 변수를 선택해 주세요. 같은 변수를 중복 사용할 수 없습니다.')
    if not df.columns.is_unique:
        raise AnalysisError('열 이름이 중복되어 있습니다. 엑셀에서 서로 다른 이름으로 고쳐 주세요.')
    if any(c not in df.columns for c in columns):
        raise AnalysisError('선택한 열이 데이터에 없습니다. 변수를 다시 선택해 주세요.')


def numeric_series(s):
    """빈칸과 무한대는 결측으로, 숫자가 아닌 문자열은 명시적 오류로 처리."""
    s = s.replace(r'^\s*$', np.nan, regex=True)
    out = pd.to_numeric(s, errors='coerce')
    invalid = s.notna() & out.isna()
    if invalid.any():
        raise AnalysisError(f'「{s.name}」에 숫자가 아닌 값이 {int(invalid.sum())}개 있습니다. 숫자 열을 선택하거나 원본을 수정해 주세요.')
    return out.astype(float).replace([np.inf, -np.inf], np.nan)


def _prepare(df, numeric, factors=()):
    cols = list(numeric) + list(factors)
    _columns(df, cols)
    d = df[cols].copy()
    for c in numeric:
        d[c] = numeric_series(d[c])
    for c in factors:
        d[c] = d[c].replace(r'^\s*$', np.nan, regex=True)
    d = d.dropna().reset_index(drop=True)
    if len(d) < 3:
        raise AnalysisError('결측값을 제외한 사례가 3개 미만입니다. 유효한 자료를 추가해 주세요.')
    for c in numeric:
        if d[c].nunique() < 2:
            raise AnalysisError(f'「{c}」의 값이 모두 같습니다. 값에 변화가 있는 변수를 선택해 주세요.')
    for c in factors:
        d[c] = d[c].astype(str)
        if not 2 <= d[c].nunique() <= 20:
            raise AnalysisError(f'「{c}」는 2~20개 집단이 필요합니다. ID나 연속형 변수를 집단으로 선택하지 않았는지 확인해 주세요.')
    return d, {'n': len(d), 'dropped': len(df) - len(d), 'total': len(df)}


def _fit(y, x):
    design = sm.add_constant(x.astype(float), has_constant='add')
    if len(y) <= design.shape[1] + 1:
        raise AnalysisError('표본이 부족합니다. 추정 계수 수보다 최소 2개 더 많은 유효 사례가 필요합니다.')
    if np.linalg.matrix_rank(design.to_numpy()) < design.shape[1]:
        raise AnalysisError('설명변수 사이에 완전한 중복 관계가 있습니다. 같은 값이거나 서로 정확히 비례하는 변수를 빼 주세요.')
    model = sm.OLS(y.astype(float), design).fit()
    _check_residual(model)
    return model


def _check_residual(model):
    if model.df_resid < 2:
        raise AnalysisError('오차를 추정할 자유도가 부족합니다. 사례 수를 늘려 주세요.')
    scale = max(float(np.sum((model.model.endog - np.mean(model.model.endog)) ** 2)), 1e-100)
    if not np.isfinite(model.ssr) or model.ssr <= scale * 1e-14:
        raise AnalysisError('자료가 모형과 거의 완전히 일치해 오차와 p값을 안정적으로 계산할 수 없습니다. 원자료를 확인해 주세요.')


def coefficient_table(model, labels=None):
    labels = labels or {}
    ci = np.asarray(model.conf_int())
    return pd.DataFrame({
        '항': [labels.get(k, '절편' if k == 'const' else k) for k in model.params.index],
        'B': np.asarray(model.params), 'SE': np.asarray(model.bse),
        't': np.asarray(model.tvalues), 'p': np.asarray(model.pvalues),
        '95% CI 하한': ci[:, 0], '95% CI 상한': ci[:, 1],
    })


def descriptive_statistics(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    _columns(df, columns)
    rows = []
    for col in columns:
        s = numeric_series(df[col])
        q1, q3 = s.quantile(.25), s.quantile(.75)
        rows.append({'변수': col, '사용 사례 수(n)': int(s.notna().sum()),
                     '결측 수': int(s.isna().sum()), '평균': s.mean(),
                     '표준편차': s.std(ddof=1), '중앙값': s.median(),
                     '최소값': s.min(), '최대값': s.max(), '범위': s.max()-s.min(),
                     'Q1': q1, 'Q3': q3, '사분위범위(IQR)': q3-q1})
    return pd.DataFrame(rows)


def frequency_table(df, column):
    _columns(df, [column])
    s = df[column].replace(r'^\s*$', np.nan, regex=True)
    counts = s.dropna().astype(str).value_counts().rename_axis('범주').reset_index(name='빈도')
    counts['전체 비율(%)'] = 100 * counts['빈도'] / max(len(s), 1)
    counts['유효 비율(%)'] = 100 * counts['빈도'] / max(int(s.notna().sum()), 1)
    if s.isna().any():
        counts.loc[len(counts)] = ['(결측)', int(s.isna().sum()), 100*s.isna().mean(), np.nan]
    return counts


def regression(df, y, xs):
    if not xs:
        raise AnalysisError('설명변수 X를 한 개 이상 선택해 주세요.')
    if len(xs) > 10:
        raise AnalysisError('이 교육용 앱에서는 설명변수를 최대 10개까지 선택할 수 있습니다.')
    d, info = _prepare(df, [y] + list(xs))
    # 내부 이름 사용: 사용자의 열 이름이 const여도 충돌하지 않는다.
    x = d[xs].copy()
    x.columns = [f'x{i}' for i in range(len(xs))]
    model = _fit(d[y], x)
    labels = {f'x{i}': name for i, name in enumerate(xs)}
    design = np.asarray(model.model.exog)
    vif = pd.DataFrame({'변수': xs, 'VIF': [variance_inflation_factor(design, i+1) for i in range(len(xs))]})
    residuals = pd.DataFrame({'관측값': d[y], '예측값': np.asarray(model.fittedvalues), '잔차': np.asarray(model.resid)})
    notes = ['선형성·오차 독립성·등분산성과 오차의 정규성을 확인하세요. 계수는 인과효과를 보장하지 않습니다.']
    if (vif['VIF'] >= 5).any():
        notes.append('VIF가 5 이상인 변수가 있습니다. 설명변수의 중복 정보를 검토하세요.')
    return dict(info, data=d, model=model, coefficients=coefficient_table(model, labels),
                r2=model.rsquared, adj_r2=model.rsquared_adj, vif=vif, residuals=residuals, warnings=notes)


def _group_summary(d, y, groups):
    return d.groupby(list(groups), observed=True, sort=True)[y].agg(n='count', 평균='mean', 표준편차='std').reset_index()


def _levene(groups):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        value = stats.levene(*groups, center='median')
    return {'통계량': float(value.statistic), 'p': float(value.pvalue)}


def one_way_anova(df, y, group):
    d, info = _prepare(df, [y], [group])
    groups = [v[y].to_numpy() for _, v in d.groupby(group, observed=True)]
    if min(map(len, groups)) < 2:
        raise AnalysisError('각 집단에 유효한 사례가 2개 이상 필요합니다.')
    internal = pd.DataFrame({'Y': d[y], 'G': d[group]})
    model = ols('Y ~ C(G)', data=internal).fit()
    _check_residual(model)
    a = anova_lm(model, typ=2)
    ssb, sse = a.iloc[0]['sum_sq'], model.ssr
    eta = float(ssb / (ssb + sse))
    omega = max(0., float((ssb - a.iloc[0]['df'] * model.mse_resid) / (ssb + sse + model.mse_resid)))
    table = a.rename(columns={'sum_sq': '제곱합(SS)', 'df': '자유도(df)', 'PR(>F)': 'p'}).copy()
    table.insert(0, '효과', [group, '오차'])
    table['평균제곱(MS)'] = table['제곱합(SS)'] / table['자유도(df)']
    tukey = pairwise_tukeyhsd(d[y], d[group], alpha=.05)
    pairs = [(a, b) for i, a in enumerate(tukey.groupsunique) for b in tukey.groupsunique[i+1:]]
    posthoc = pd.DataFrame({'집단1': [p[0] for p in pairs], '집단2': [p[1] for p in pairs],
        '평균차(집단2-집단1)': tukey.meandiffs, '보정 p': tukey.pvalues,
        '95% CI 하한': tukey.confint[:,0], '95% CI 상한': tukey.confint[:,1], '유의(.05)': tukey.reject})
    lev = _levene(groups)
    notes = ['독립 집단·오차 정규성·등분산성을 가정합니다. Tukey HSD는 등분산 사후검정입니다.']
    if np.isfinite(lev['p']) and lev['p'] < .05:
        notes.append('Levene 검정에서 등분산 가정 위반 가능성이 나타났습니다. F검정·Tukey 해석에 주의하세요. Welch/Games–Howell은 이 앱의 범위 밖입니다.')
    return dict(info, data=d, model=model, table=table.reset_index(drop=True),
                groups=_group_summary(d,y,[group]), eta2=eta, omega2=omega, posthoc=posthoc, levene=lev, warnings=notes)


def two_way_anova(df, y, factor_a, factor_b, ss_type=2):
    if ss_type not in (2, 3):
        raise AnalysisError('제곱합 방식은 Type II 또는 Type III를 선택해 주세요.')
    d, info = _prepare(df, [y], [factor_a, factor_b])
    cells = pd.crosstab(d[factor_a], d[factor_b])
    if (cells < 2).any().any():
        raise AnalysisError('모든 A×B 조합에 유효 사례가 2개 이상 필요합니다. 빈 조합 또는 1명인 조합을 확인해 주세요.')
    internal = pd.DataFrame({'Y': d[y], 'A': d[factor_a], 'B': d[factor_b]})
    # Sum coding은 Type III의 주효과 검정에도 적합하도록 사용한다.
    model = ols('Y ~ C(A, Sum) * C(B, Sum)', data=internal).fit()
    _check_residual(model)
    a = anova_lm(model, typ=ss_type).drop(index='Intercept', errors='ignore')
    table = a.rename(columns={'sum_sq':'제곱합(SS)', 'df':'자유도(df)', 'PR(>F)':'p'}).copy()
    table.insert(0, '효과', [factor_a, factor_b, f'{factor_a} × {factor_b}', '오차'])
    table['평균제곱(MS)'] = table['제곱합(SS)'] / table['자유도(df)']
    table['부분 η²'] = table['제곱합(SS)'] / (table['제곱합(SS)'] + model.ssr)
    table.loc['Residual', '부분 η²'] = np.nan
    notes = [f'Type {"II" if ss_type==2 else "III"} 제곱합, 합 대비(Sum coding), 상호작용 포함 모형입니다.',
             '독립 관측·오차 정규성·등분산성을 가정합니다. 반복측정 자료에는 적용하지 마세요.']
    interaction_p = float(table.iloc[2]['p'])
    if interaction_p < .05:
        notes.append('상호작용이 유의합니다. 한 요인의 관계가 다른 요인 수준에 따라 달라질 수 있어 주효과만으로 결론 내리지 마세요.')
    if cells.to_numpy().max() != cells.to_numpy().min():
        notes.append('집단별 사례 수가 다릅니다. 상호작용을 포함한 불균형 설계에서는 Type II/III 결과와 주효과 의미가 달라질 수 있습니다.')
    return dict(info, data=d, model=model, table=table.reset_index(drop=True), groups=_group_summary(d,y,[factor_a,factor_b]),
                cell_counts=cells, warnings=notes, interaction_p=interaction_p, ss_type=ss_type)


def mediation(df, x, mediator, y, n_boot=2000, seed=42):
    if not isinstance(n_boot, int) or not 200 <= n_boot <= 10000:
        raise AnalysisError('부트스트랩 횟수는 200~10,000 사이의 정수여야 합니다.')
    d, info = _prepare(df, [x, mediator, y])
    if len(d) < 10:
        raise AnalysisError('매개효과는 유효 사례가 최소 10개 필요합니다. 작은 표본의 결과는 불안정할 수 있습니다.')
    z = d.rename(columns={x:'X', mediator:'M', y:'Y'})
    a_model = _fit(z['M'], z[['X']])
    b_model = _fit(z['Y'], z[['X','M']])
    c_model = _fit(z['Y'], z[['X']])
    a, b = a_model.params['X'], b_model.params['M']
    cp, c = b_model.params['X'], c_model.params['X']
    # 행 단위 쌍 부트스트랩. 고정된 seed로 검산을 재현한다.
    rng = np.random.default_rng(seed)
    arr = z[['X','M','Y']].to_numpy()
    boot = []
    for _ in range(n_boot):
        sample = arr[rng.integers(0, len(arr), len(arr))]
        xa = np.column_stack([np.ones(len(arr)), sample[:,0]])
        xb = np.column_stack([xa, sample[:,1]])
        if np.linalg.matrix_rank(xa) < 2 or np.linalg.matrix_rank(xb) < 3:
            continue
        av = np.linalg.lstsq(xa, sample[:,1], rcond=None)[0][1]
        bv = np.linalg.lstsq(xb, sample[:,2], rcond=None)[0][2]
        boot.append(av*bv)
    if len(boot) < .9 * n_boot:
        raise AnalysisError('재표집 자료에서 추정 실패가 많습니다. 사례 수와 변수의 분포를 확인해 주세요.')
    lo, hi = np.quantile(boot, [.025,.975])
    paths = []
    for label, mod, key in [('a: X → M',a_model,'X'),('b: M → Y | X',b_model,'M'),('c: 총 관계',c_model,'X'),("c′: 직접 관계",b_model,'X')]:
        ci = mod.conf_int().loc[key]
        paths.append({'경로':label,'B':mod.params[key],'SE':mod.bse[key],'t':mod.tvalues[key],
                      'p':mod.pvalues[key],'95% CI 하한':ci.iloc[0],'95% CI 상한':ci.iloc[1]})
    return dict(info, data=d, paths=pd.DataFrame(paths), indirect=float(a*b), ci=(float(lo),float(hi)),
        a=float(a), b=float(b), c=float(c), direct=float(cp), bootstrap=np.array(boot), n_boot=n_boot,
        valid_boot=len(boot), seed=seed, warnings=['간접효과 신뢰구간은 percentile 부트스트랩입니다. BCa 방식이 아닙니다.',
        '관찰 자료의 간접적 연관을 추정합니다. 시간 순서·교란 통제 없이 인과적인 매개를 확정할 수 없습니다.'])


def moderation(df, x, moderator, y, center=True):
    d, info = _prepare(df, [x, moderator, y])
    if len(d) < 10:
        raise AnalysisError('조절효과는 유효 사례가 최소 10개 필요합니다.')
    mx, mw = float(d[x].mean()), float(d[moderator].mean())
    offset_x, offset_w = (mx, mw) if center else (0., 0.)
    design = pd.DataFrame({'X':d[x]-offset_x, 'W':d[moderator]-offset_w})
    design['XW'] = design['X'] * design['W']
    model = _fit(d[y], design)
    sd = float(d[moderator].std(ddof=1))
    slopes, lines = [], []
    grid = np.linspace(d[x].min(), d[x].max(), 60)
    for label, w in [('평균 − 1SD', mw-sd), ('평균',mw), ('평균 + 1SD',mw+sd)]:
        wc = w-offset_w
        contrast = np.array([0.,1.,0.,wc])
        effect = model.t_test(contrast)
        ci = np.asarray(effect.conf_int())[0]
        inside = bool(d[moderator].min() <= w <= d[moderator].max())
        slopes.append({'W 수준':label, 'W 원점수':w, '기울기':float(np.asarray(effect.effect).item()),
                       'SE':float(np.asarray(effect.sd).item()),'t':float(np.asarray(effect.tvalue).item()),
                       'p':float(np.asarray(effect.pvalue).item()), '95% CI 하한':ci[0],'95% CI 상한':ci[1],
                       '관측범위 내':inside})
        pred_x = pd.DataFrame({'const':1.,'X':grid-offset_x,'W':wc,'XW':(grid-offset_x)*wc})
        for xv, pred in zip(grid,model.predict(pred_x)):
            lines.append({'X':xv,'예측 Y':pred,'W 수준':label})
    reduced = _fit(d[y], design[['X','W']])
    notes = ['단순기울기는 W의 평균 및 평균±1 표본 표준편차에서 계산합니다. 다중검정 보정 전 p값입니다.',
             '상호작용은 통계적 관계이며 인과적인 조절을 입증하지 않습니다.']
    if not all(v['관측범위 내'] for v in slopes):
        notes.append('일부 단순기울기의 W 수준이 관측 범위 밖입니다. 해당 결과는 외삽이므로 주의하세요.')
    labels = {'X':f'{x} (중심화)' if center else x, 'W':f'{moderator} (중심화)' if center else moderator,
              'XW':f'{x} × {moderator}'}
    return dict(info,data=d,model=model,coefficients=coefficient_table(model,labels),
                slopes=pd.DataFrame(slopes),lines=pd.DataFrame(lines),r2=model.rsquared,
                adj_r2=model.rsquared_adj,delta_r2=model.rsquared-reduced.rsquared,
                interaction=float(model.params['XW']),interaction_p=float(model.pvalues['XW']),
                centered=center,means=(mx,mw),warnings=notes)


def format_p(p):
    if pd.isna(p):
        return '계산 불가'
    return '< .001' if p < .001 else f'{p:.4f}'
