"""신규 추론을 수작업 식, 전수 순열, 공개 lavaan 기준값과 대조한다."""
from io import BytesIO
from itertools import permutations
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from semopy.examples import holzinger39

from analysis import AnalysisError
from advanced_analysis import correlation_analysis, latent_variable_analysis, SEM_TEMPLATES
from advanced_ui import matrix_table, latent_diagram
from data.generate_sem_sample import make_sem_sample
from data_io import export_excel


def test_pearson_covariance_t_test_fisher_ci_and_holm():
    rng = np.random.default_rng(91)
    x = rng.normal(size=40)
    d = pd.DataFrame({'a':x, 'b':.6*x+rng.normal(size=40), 'c':rng.normal(size=40)})
    r = correlation_analysis(d,list(d))
    expected = np.corrcoef(d.to_numpy().T)
    np.testing.assert_allclose(r['correlation'],expected,atol=1e-14)
    coefficient = expected[0,1]
    expected_p = 2*stats.t.sf(abs(coefficient)*np.sqrt(38/(1-coefficient**2)),38)
    row = r['pairs'].iloc[0]
    assert row['p'] == pytest.approx(expected_p)
    ci = np.tanh(np.arctanh(coefficient)+np.array([-1,1])*1.95996398454/np.sqrt(37))
    np.testing.assert_allclose(row[['95% CI 하한','95% CI 상한']].astype(float),ci)
    p = r['pairs']['p'].to_numpy(); order = np.argsort(p)
    holm_sorted = np.minimum(1,np.maximum.accumulate(p[order]*np.arange(3,0,-1)))
    np.testing.assert_allclose(r['pairs']['보정 p'].to_numpy()[order],holm_sorted)
    assert np.isnan(np.diag(r['adjusted_pvalues'])).all()


def test_spearman_exact_ties_and_small_sample():
    d = pd.DataFrame({'a':[1,2,3,4,5], 'b':[5,4,3,2,1]})
    r = correlation_analysis(d,list(d),method='Spearman')['pairs'].iloc[0]
    assert r['상관계수'] == pytest.approx(-1)
    assert r['p'] == pytest.approx(2/120)
    assert r['순열 수'] == 120
    d['a'] = [1,1,2,3,3]
    expected = abs(stats.spearmanr(d.a,d.b).statistic)
    all_r = [abs(stats.spearmanr(d.a,v).statistic) for v in permutations(d.b)]
    row = correlation_analysis(d,list(d),method='Spearman')['pairs'].iloc[0]
    assert row['p'] == pytest.approx(np.mean(np.array(all_r)>=expected-1e-12))


def test_spearman_monte_carlo_positive_reproducible_and_large_n_approximation():
    d = pd.DataFrame({'a':range(10), 'b':range(10)})
    first = correlation_analysis(d,list(d),method='Spearman',n_perm=999)['pairs']
    second = correlation_analysis(d,list(d),method='Spearman',n_perm=999)['pairs']
    pd.testing.assert_frame_equal(first,second)
    assert first.iloc[0]['p'] >= 1/1000
    assert 'Monte Carlo' in first.iloc[0]['검정 방식']
    rng = np.random.default_rng(18)
    d = pd.DataFrame(rng.normal(size=(501,2)),columns=['a','b'])
    row = correlation_analysis(d,list(d),method='Spearman')['pairs'].iloc[0]
    assert row['p'] == pytest.approx(stats.spearmanr(d.a,d.b).pvalue)
    assert row['순열 수'] == 0


def test_pairwise_listwise_counts_and_no_three_case_ci():
    d = pd.DataFrame({'a':[1,2,3,4,5,6], 'b':[2,1,4,3,np.nan,8], 'c':[1,3,2,np.inf,4,7]})
    pair = correlation_analysis(d,list(d))
    complete = correlation_analysis(d,list(d),missing='listwise')
    assert pair['complete_n'] == 4
    assert pair['counts'].loc['a','b'] == 5
    assert pair['counts'].loc['b','c'] == 4
    assert (complete['counts']==4).all().all()
    r = correlation_analysis(d.head(3),['a','b'])['pairs'].iloc[0]
    assert np.isnan(r['95% CI 하한'])
    d['constant'] = 1
    r = correlation_analysis(d,['a','b','constant'])
    assert len(r['pairs']) == 3 and r['pairs']['p'].notna().sum() == 1
    assert r['pairs'].iloc[0]['p'] == r['pairs'].iloc[0]['보정 p']
    with pytest.raises(AnalysisError,match='계산 가능한'):
        correlation_analysis(d,['a','constant'])


def test_matrix_export_keeps_labels_and_numeric_precision():
    d = pd.DataFrame({'행 변수':[1,2,3,4], '=danger':[2,4,1,3]})
    r = correlation_analysis(d,list(d))
    exported = matrix_table(r['correlation'])
    assert exported.columns[0] == '_행 변수'
    raw = export_excel({'상관':exported},'test')
    read = pd.read_excel(BytesIO(raw),sheet_name='1_상관')
    assert read.iloc[:,0].tolist() == list(d)
    np.testing.assert_allclose(read.iloc[:,1:].to_numpy(float),r['correlation'])


def factors_for(template):
    return {name:[name.lower()+str(i) for i in (1,2,3)] for name in SEM_TEMPLATES[template]}


@pytest.mark.parametrize('template',list(SEM_TEMPLATES))
def test_all_latent_templates_and_fixed_marker_uncertainty(template):
    r = latent_variable_analysis(make_sem_sample(),factors_for(template),template)
    assert r['converged'] and r['n']==300
    assert r['fit_values']['df'] == (24 if '3' in template else 8)
    markers = r['parameters'][r['parameters']['고정 모수']]
    assert len(markers) == len(SEM_TEMPLATES[template])
    assert (markers['B']==1).all()
    assert markers[['p','SE(B)','B 95% CI 하한']].isna().all().all()
    np.testing.assert_allclose(r['observed_covariance']-r['implied_covariance'],r['residual_covariance'])
    assert len(latent_diagram(r).layout.annotations) >= 2
    if '(CFA)' in template:
        assert r['paths'].empty
    else:
        assert r['r_squared']['R²'].between(0,1).all()


def test_cfa_against_published_lavaan_holzinger_swineford_results():
    # https://lavaan.ugent.be/tutorial/cfa.html : published rounded MLE benchmarks.
    data = holzinger39.get_data()
    factors = {'X':['x1','x2','x3'],'M':['x4','x5','x6'],'Y':['x7','x8','x9']}
    r = latent_variable_analysis(data,factors,'3요인 측정모형 (CFA)')
    expected = {'χ²':85.306,'df':24,'CFI':.931,'TLI':.896,'RMSEA':.092}
    for key,value in expected.items():
        assert r['fit_values'][key] == pytest.approx(value,abs=.0005)
    expected_loadings = {'x2':.554,'x3':.729,'x5':1.113,'x6':.926,'x8':1.180,'x9':1.082}
    observed = r['loadings'].set_index('결과')['B']
    for name,value in expected_loadings.items():
        assert observed[name] == pytest.approx(value,abs=.001)


def test_sem_recovers_known_structural_paths_and_missing_counts():
    data = make_sem_sample(n=6000,seed=2718)
    template = '3변수 구조모형: X → M → Y, X → Y'
    data['unused'] = np.nan
    data.loc[0,'x1'] = np.inf
    data.loc[1,'m1'] = np.nan
    r = latent_variable_analysis(data,factors_for(template),template)
    assert r['n']==5998 and r['dropped']==2
    paths = r['paths'].set_index(['결과','설명'])['표준화 추정치']
    for key,value in {('M','X'):.65,('Y','M'):.55,('Y','X'):.30}.items():
        assert paths[key] == pytest.approx(value,abs=.045)
    assert (r['paths']['p'] < .001).all()


@pytest.mark.parametrize('problem',['small','duplicate','singular','constant','text','two_items','scale'])
def test_sem_rejects_unusable_inputs(problem):
    data = make_sem_sample()
    template = '3변수 구조모형: X → M → Y, X → Y'
    factors = factors_for(template)
    if problem=='small': data = data.head(49)
    elif problem=='duplicate': factors['Y'][0] = 'x1'
    elif problem=='singular': data['x2'] = data['x1']*2
    elif problem=='constant': data['x1'] = 1
    elif problem=='text': data['x1'] = data['x1'].astype(str); data.loc[0,'x1'] = 'bad'
    elif problem=='two_items': factors['X'] = ['x1','x2']
    elif problem=='scale': data['x1'] *= 1e6
    with pytest.raises(AnalysisError):
        latent_variable_analysis(data,factors,template)


def test_arbitrary_indicator_names_remain_data_not_model_syntax():
    data = make_sem_sample()
    template = '2변수 구조모형: X → Y'
    factors = factors_for(template)
    dangerous_name = 'name =~ X + Y; <script> test'
    data = data.rename(columns={'x1':dangerous_name})
    factors['X'][0] = dangerous_name
    r = latent_variable_analysis(data,factors,template)
    assert dangerous_name not in r['syntax']
    assert dangerous_name in r['mapping']['원래 변수'].tolist()
