"""교수자 기준값, 독립 계산, 오류 입력을 함께 검증한다."""
import sys
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis import (AnalysisError, descriptive_statistics, frequency_table, regression,
                      one_way_anova,two_way_anova,mediation,moderation,format_p)
from data_io import read_data,excel_sheets,export_excel


@pytest.fixture(scope='module')
def df():
    return pd.read_excel(ROOT/'sample.xlsx')


def test_starter_descriptive():
    r=descriptive_statistics(pd.DataFrame({'x':[1,2,3,None]}),['x']).iloc[0]
    assert r['사용 사례 수(n)']==3 and r['결측 수']==1
    assert r['평균']==2 and r['표준편차']==1


def test_reference_descriptive(df):
    r=descriptive_statistics(df,['score']).iloc[0]
    assert r['사용 사례 수(n)']==36
    for key,value in [('평균',76),('표준편차',8.135),('중앙값',76),('최소값',60),('최대값',92)]:
        assert r[key]==pytest.approx(value,abs=.0005)


def test_reference_simple(df):
    r=regression(df,'score',['study_time'])
    assert r['r2']==pytest.approx(.0330,abs=.00005)
    assert r['coefficients']['B'].to_numpy()==pytest.approx([72.4268,1.1089],abs=.00005)
    assert r['coefficients'].iloc[1]['p']==pytest.approx(.288707,abs=.0000005)
    # NumPy least squares로 독립 대조.
    x=np.column_stack([np.ones(len(df)),df.study_time])
    assert np.linalg.lstsq(x,df.score,rcond=None)[0]==pytest.approx(r['coefficients']['B'])


def test_reference_multiple(df):
    r=regression(df,'score',['study_time','pre_score'])
    assert r['r2']==pytest.approx(.9349,abs=.00005)
    assert r['adj_r2']==pytest.approx(.9310,abs=.00005)
    assert r['coefficients']['B'][1:].to_numpy()==pytest.approx([.0729,.8912],abs=.00005)
    assert r['coefficients'].iloc[1]['p']==pytest.approx(.792724,abs=.0000005)
    assert 0<r['coefficients'].iloc[2]['p']<.0000005
    assert (r['vif']['VIF']>=1).all()


def test_reference_oneway(df):
    r=one_way_anova(df,'anova_score','method')
    assert r['table'].iloc[0]['F']==pytest.approx(14.0291,abs=.00005)
    assert r['table'].iloc[0]['p']==pytest.approx(.000039,abs=.0000005)
    assert r['groups']['평균'].to_numpy()==pytest.approx([55.166,58.193,62.407],abs=.0005)
    independent=stats.f_oneway(*(v.anova_score for _,v in df.groupby('method')))
    assert r['table'].iloc[0]['F']==pytest.approx(independent.statistic)
    assert r['eta2']==pytest.approx(317.441763/(317.441763+373.352555))
    assert len(r['posthoc'])==3


def test_reference_twoway(df):
    r=two_way_anova(df,'anova_score','method','grade')
    assert r['table']['F'][:3].to_numpy()==pytest.approx([266.3419,283.2311,8.2607],abs=.00005)
    assert r['interaction_p']==pytest.approx(.000174,abs=.0000005)
    assert r['table']['부분 η²'][:3].between(0,1).all()
    r3=two_way_anova(df,'anova_score','method','grade',ss_type=3)
    # 균형 설계에서는 Type II와 Sum coding의 Type III가 일치한다.
    assert r3['table']['F'][:3].to_numpy()==pytest.approx(r['table']['F'][:3])


def test_reference_mediation_and_seed(df):
    r=mediation(df,'med_x','med_m','med_y',n_boot=2000,seed=42)
    for key,value in [('a',.8027),('b',1.5300),('direct',.1383),('indirect',1.2282)]:
        assert r[key]==pytest.approx(value,abs=.00005)
    assert r['c']==pytest.approx(r['direct']+r['indirect'])
    repeat=mediation(df,'med_x','med_m','med_y',n_boot=2000,seed=42)
    assert np.array_equal(r['bootstrap'],repeat['bootstrap'])
    assert r['valid_boot']==2000 and r['ci'][0]<r['indirect']<r['ci'][1]


def test_reference_moderation_and_centering(df):
    r=moderation(df,'mod_x','mod_w','mod_y')
    raw=moderation(df,'mod_x','mod_w','mod_y',center=False)
    assert r['interaction']==pytest.approx(.6786,abs=.00005)
    assert r['r2']==pytest.approx(.9743,abs=.00005)
    assert 0<r['interaction_p']<.0000005
    assert r['interaction']==pytest.approx(raw['interaction'])
    assert r['slopes']['기울기'].to_numpy()==pytest.approx(raw['slopes']['기울기'])
    assert r['model'].fittedvalues.to_numpy()==pytest.approx(raw['model'].fittedvalues)
    assert r['delta_r2']>0


def test_missing_only_selected_columns(df):
    df=df.copy();df.loc[0,'study_time']=np.nan;df.loc[1,'mod_y']=np.nan
    r=regression(df,'score',['study_time'])
    assert r['n']==35 and r['dropped']==1


def test_infinite_counted_missing():
    r=descriptive_statistics(pd.DataFrame({'x':[1,2,np.inf,-np.inf,None]}),['x']).iloc[0]
    assert r['결측 수']==3 and r['사용 사례 수(n)']==2


def test_frequency_denominators():
    r=frequency_table(pd.DataFrame({'a':['A','A','B',None]}),'a')
    assert r.loc[0,'전체 비율(%)']==50
    assert r.loc[0,'유효 비율(%)']==pytest.approx(200/3)
    assert r['빈도'].sum()==4


@pytest.mark.parametrize('y,xs',[('score',['score']),('score',['study_time','study_time']),('score',[]),('missing',['study_time'])])
def test_wrong_columns(df,y,xs):
    with pytest.raises(AnalysisError):regression(df,y,xs)


def test_nonnumeric_rejected():
    with pytest.raises(AnalysisError,match='숫자가 아닌'):
        descriptive_statistics(pd.DataFrame({'x':['1','bad',None]}),['x'])


def test_sample_too_small(df):
    with pytest.raises(AnalysisError):regression(df.iloc[:3],'score',['study_time'])


def test_constant_predictor(df):
    df=df.copy();df['constant']=1
    with pytest.raises(AnalysisError,match='모두 같습니다'):regression(df,'score',['constant'])


def test_collinearity(df):
    df=df.copy();df['double']=df.study_time*2
    with pytest.raises(AnalysisError,match='중복 관계'):regression(df,'score',['study_time','double'])


def test_perfect_fit():
    with pytest.raises(AnalysisError,match='완전히 일치'):
        regression(pd.DataFrame({'x':range(10),'y':np.arange(10)*2+1}),'y',['x'])


def test_one_group(df):
    with pytest.raises(AnalysisError):one_way_anova(df[df.method=='A'],'anova_score','method')


def test_singleton_group(df):
    df=pd.concat([df[df.method!='A'],df[df.method=='A'].iloc[:1]])
    with pytest.raises(AnalysisError,match='2개 이상'):one_way_anova(df,'anova_score','method')


def test_missing_cell(df):
    df=df[~((df.method=='A')&(df.grade=='중1'))]
    with pytest.raises(AnalysisError,match='모든 A×B'):two_way_anova(df,'anova_score','method','grade')


def test_arbitrary_column_names(df):
    df=df.rename(columns={'score':'점수 (Y)!','study_time':'const','method':'수업 A/B','grade':'학년 + 단계'})
    assert regression(df,'점수 (Y)!',['const'])['r2']==pytest.approx(.0330380273871)
    assert two_way_anova(df,'anova_score','수업 A/B','학년 + 단계')['n']==36


def test_empty_selection():
    with pytest.raises(AnalysisError):descriptive_statistics(pd.DataFrame({'x':[1,2]}),[])


def test_read_xlsx_and_sheet():
    raw=(ROOT/'sample.xlsx').read_bytes()
    assert excel_sheets(raw,'test.xlsx')==['Sheet1']
    df=read_data(raw,'test.xlsx','Sheet1')
    assert df.shape==(36,14) and df.score.mean()==76


@pytest.mark.parametrize('encoding',['utf-8-sig','cp949'])
def test_csv_encodings(encoding):
    df=read_data('점수,집단\n1,가\n2,나\n'.encode(encoding),'test.csv')
    assert df['점수'].mean()==1.5


@pytest.mark.parametrize('raw',[b'',b'a,a\n1,2',b'a,\n1,2',b'a\n',b'fake excel'])
def test_invalid_files(raw):
    with pytest.raises(AnalysisError):read_data(raw,'bad.csv' if raw!=b'fake excel' else 'bad.xlsx')


def test_export_excel_formula_is_literal():
    raw=export_excel({'test':pd.DataFrame({'=header':['=1+1','+value','@literal']})},'=formula\nOK')
    book=load_workbook(BytesIO(raw),data_only=False)
    assert book['1_test']['A1'].data_type=='s'
    assert book['1_test']['A2'].value=='=1+1' and book['1_test']['A2'].data_type=='s'
    assert book['분석안내']['A2'].data_type=='s'


def test_p_format():
    assert format_p(6e-21)=='< .001' and format_p(.288707)=='0.2887'
