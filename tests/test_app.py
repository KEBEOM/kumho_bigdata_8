"""실제 Streamlit 스크립트를 실행하는 UI 흐름 검증."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
MODES=['기초통계','상관관계','단순회귀','다중회귀','일원분산분석','이원분산분석','매개효과','조절효과','구조방정식 / CFA']


@pytest.mark.parametrize('mode',MODES)
def test_each_analysis_screen(mode):
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    app.selectbox(key='analysis_mode').select(mode).run()
    app.button[0].click().run()
    assert not app.exception
    assert not app.error
    assert len(app.dataframe)>=1
    assert app.session_state['result']


def test_previous_result_hidden_after_settings_change():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.button[0].click().run()
    assert app.session_state['result']
    app.multiselect(key='sel_desc').set_value(['pre_score']).run()
    assert 'result' not in app.session_state


def test_empty_descriptive_shows_friendly_error():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.multiselect(key='sel_desc').set_value([]).run()
    app.selectbox(key='sel_freq').select('사용 안 함').run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.error)==1


def test_sem_source_switch_cfa_and_result_invalidation():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.radio(key='data_source').set_value('구조방정식 예제로 연습').run()
    assert app.selectbox(key='analysis_mode').value=='구조방정식 / CFA'
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.session_state['result']['n']==300
    app.selectbox(key='sel_sem_template').select('2요인 측정모형 (CFA)').run()
    assert 'result' not in app.session_state
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.session_state['result']['paths'].empty
    app.radio(key='data_source').set_value('기준 데이터로 연습').run()
    assert 'result' not in app.session_state
    app.button[0].click().run()
    assert not app.exception and len(app.error)==1
    assert '최소 50' in app.error[0].value


def test_spearman_screen_and_invalid_empty_selection():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.selectbox(key='analysis_mode').select('상관관계').run()
    app.selectbox(key='sel_corr_method').select('Spearman').run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.session_state['result']['method']=='Spearman'
    app.multiselect(key='sel_corr_columns').set_value([]).run()
    app.button[0].click().run()
    assert not app.exception and len(app.error)==1
