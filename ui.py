"""Presentation helpers. Analysis and data handling live in their original modules."""
import base64
from html import escape
from pathlib import Path

import streamlit as st


METHOD_NOTES = {
    '기초통계': ('데이터의 첫인상', '평균과 분포, 빈도표로 데이터의 전체 모습을 살펴보세요.'),
    '단순회귀': ('두 변수의 관계', '하나의 설명변수가 결과변수와 어떤 관계가 있는지 확인하세요.'),
    '다중회귀': ('함께 설명하는 변수들', '여러 설명변수의 관계를 함께 고려하고, 설명력과 계수를 비교하세요.'),
    '일원분산분석': ('집단 사이의 차이', '한 가지 기준으로 나눈 집단의 평균을 비교하세요.'),
    '이원분산분석': ('두 요인의 영향', '두 집단 요인의 주효과와 상호작용을 함께 살펴보세요.'),
    '매개효과': ('관계가 이어지는 경로', 'X에서 M을 거쳐 Y로 이어지는 간접적 연관을 살펴보세요.'),
    '조절효과': ('조건에 따라 달라지는 관계', 'W의 수준에 따라 X와 Y의 관계가 달라지는지 확인하세요.'),
}


def inject_styles():
    css = (Path(__file__).resolve().parent / 'assets' / 'styles.css').read_text(encoding='utf-8')
    # Style-only st.html does not create a blank visible block above the header.
    st.html('<style>' + css + '</style>')


def render_header():
    chart = (Path(__file__).resolve().parent / 'assets' / 'insight.svg').read_bytes()
    chart_uri = 'data:image/svg+xml;base64,' + base64.b64encode(chart).decode('ascii')
    st.html(f'''
    <div class="brandbar">
      <div class="brand-lockup">
        <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
        <span class="brand-name">DATA LAB<span class="brand-divider">/</span><span class="brand-descriptor">통계 워크스페이스</span></span>
      </div>
      <span class="team-credit">은수현 <span>·</span> 김정훈 <span>·</span> 김응범</span>
    </div>
    <section class="hero" aria-labelledby="app-title">
      <div class="hero-copy">
        <span class="hero-kicker"><span class="status-dot"></span> FROM DATA TO INSIGHT</span>
        <h1 id="app-title">데이터 <span>한눈에.</span></h1>
        <p class="hero-description">복잡한 숫자에서, 명확한 발견으로.<br>데이터를 고르고 분석하면, 이해하기 쉬운 결과가 펼쳐집니다.</p>
        <div class="hero-tags"><span>7가지 통계 분석</span><span>Excel · CSV</span><span>결과 다운로드</span></div>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="art-label">EXPLORE THE PATTERN<span>↗</span></div>
        <img class="insight-art" src="{chart_uri}" alt="" />
        <div class="art-caption"><span>OBSERVE</span><span>ANALYZE</span><span>DISCOVER</span></div>
      </div>
    </section>
    ''')


def section_title(number, title, description):
    st.html(f'''<div class="section-heading"><span class="step-number">{escape(number)}</span>
    <div><h2>{escape(title)}</h2><p>{escape(description)}</p></div></div>''')


def analysis_hint(mode):
    title, text = METHOD_NOTES[mode]
    st.html(f'<div class="method-note"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>')


def render_empty_result():
    st.html('''<section class="empty-result" aria-label="분석 결과 안내">
      <div class="empty-icon" aria-hidden="true"><span></span><span></span><span></span></div>
      <div><h3>다음 발견을 기다리고 있어요.</h3><p>변수 설정을 확인한 뒤 <strong>분석 실행</strong>을 누르면 결과표와 그래프가 여기에 나타납니다.</p></div>
      <span class="empty-step" aria-hidden="true">03 / RESULT</span>
    </section>''')


def render_footer():
    st.html('''<footer class="app-footer"><span><strong>DATA LAB</strong> 데이터 한눈에 · v1.2</span>
    <span>은수현 · 김정훈 · 김응범 <span class="footer-separator">/</span> AI 도움으로 개발한 교육용 앱</span></footer>''')
