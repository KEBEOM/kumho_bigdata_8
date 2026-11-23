"""실제 Streamlit 스크립트를 실행하는 UI 흐름 검증."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
MODES=['기초통계','단순회귀','다중회귀','일원분산분석','이원분산분석','매개효과','조절효과']


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
