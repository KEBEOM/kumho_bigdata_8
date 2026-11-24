"""데이터 한눈에: 스마트폰과 PC에서 사용하는 교육용 통계 웹앱."""
from pathlib import Path
import hashlib
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import streamlit as st
from analysis import (AnalysisError, numeric_series, descriptive_statistics, frequency_table,
    regression, one_way_anova, two_way_anova, mediation, moderation, format_p)
from data_io import read_data, excel_sheets, export_excel
from ui import inject_styles, render_header, section_title, analysis_hint, render_empty_result, render_footer

ROOT = Path(__file__).resolve().parent
MODES = ['기초통계','단순회귀','다중회귀','일원분산분석','이원분산분석','매개효과','조절효과']
st.set_page_config(page_title='데이터 한눈에 | 통계분석',page_icon='📊',layout='wide')
inject_styles()
render_header()
with st.container(key='guide'):
    with st.expander('처음 사용하시나요? 실행 순서와 분석 안내'):
        st.write('① 기준 데이터로 먼저 연습하세요. ② 분석 종류를 고릅니다. ③ 변수와 설정을 확인한 뒤 분석 실행을 누릅니다. ④ 결과표와 해석을 내려받습니다.')
        st.write('기초통계: 분포 요약 · 회귀: 수치형 변수 간 관계 · 분산분석: 집단 평균 비교 · 매개: X–M–Y의 간접적 연관 · 조절: W에 따라 X–Y 관계가 달라지는지 확인')
        st.caption('업로드 자료는 앱이 실행되는 서버에서 계산합니다. 로컬 실행 시 내 PC, 클라우드 접속 시 배포 서버로 전달됩니다. 앱은 자료를 AI 서비스로 보내거나 별도 파일로 자동 저장하지 않습니다. 샘플은 가상 데이터입니다.')

with st.container(key='workspace'):
    data_column, analysis_column = st.columns([1.05, 1], gap='medium')
    with data_column:
        with st.container(key='data_panel'):
            section_title('01', '데이터 준비', '기준 데이터로 시작하거나, 내 파일을 불러오세요.')
            source = st.radio('데이터 선택',['기준 데이터로 연습','내 파일 업로드'],horizontal=True)
            try:
                if source == '기준 데이터로 연습':
                    raw = (ROOT/'sample.xlsx').read_bytes()
                    df = read_data(raw,'sample.xlsx')
                    source_name = '교수자 제공 기준 데이터 · 36사례'
                    st.download_button('연습용 엑셀 받기',raw,'sample.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch',icon=':material/download:')
                    sheet_name = 'Sheet1'
                else:
                    uploaded = st.file_uploader('엑셀 또는 CSV 파일',type=['xlsx','xls','csv'],help='10MB 이하 · 첫 행은 중복되지 않는 열 이름 · 최대 10,000행/100열')
                    if uploaded is None:
                        st.info('파일을 선택하거나 위에서 ‘기준 데이터로 연습’을 선택해 주세요.')
                        st.stop()
                    raw = uploaded.getvalue()
                    sheet_name = st.selectbox('엑셀 시트',excel_sheets(raw,uploaded.name)) if not uploaded.name.lower().endswith('.csv') else 0
                    df = read_data(raw,uploaded.name,sheet_name)
                    source_name = uploaded.name
            except AnalysisError as exc:
                st.error(str(exc))
                st.stop()

            fingerprint = hashlib.sha256(raw + str(sheet_name).encode()).hexdigest()
            if st.session_state.get('dataset') != fingerprint:
                st.session_state.dataset = fingerprint
                st.session_state.pop('result',None)
                for key in list(st.session_state):
                    if key.startswith('sel_'):
                        del st.session_state[key]
            numeric = df.select_dtypes(include='number').columns.tolist()
            all_columns = df.columns.tolist()
            factors = [c for c in all_columns if 2 <= df[c].nunique() <= 20]
            missing = int(df.isna().sum().sum())
            cols = st.columns(3)
            for col,label,value in zip(cols,['사례 수','변수 수','빈칸 수'],[len(df),df.shape[1],missing]):
                col.metric(label,value)
            st.caption(f'{source_name} · 빈칸 수는 원자료 기준입니다. 무한대는 분석할 때 결측으로 처리합니다.')
            with st.expander('데이터 미리보기 및 변수 유형',expanded=False):
                st.dataframe(df.head(100),hide_index=True,width='stretch')
                st.caption('최대 100행 미리보기 · 전체 유효 데이터로 계산합니다. 넓은 표는 좌우로 스크롤하세요.')
                st.dataframe(pd.DataFrame({'변수':all_columns,'자료형':[str(df[c].dtype) for c in all_columns],
                                         '결측 수':[int(df[c].isna().sum()) for c in all_columns]}),hide_index=True,width='stretch')
    with analysis_column:
        with st.container(key='analysis_panel'):
            section_title('02', '분석 설정', '궁금한 질문에 맞는 분석과 변수를 선택하세요.')
            mode = st.selectbox('분석 종류',MODES,key='analysis_mode')
            analysis_hint(mode)
            if st.session_state.get('mode') != mode:
                st.session_state.mode = mode
                st.session_state.pop('result',None)
            if not numeric and mode != '기초통계':
                st.warning('숫자형 열이 없습니다. 숫자와 글자가 섞여 있는 열은 원본에서 수정해 주세요.')
                st.stop()


            def pick(label, options, preferred, key):
                if not options:
                    raise AnalysisError(f'{label}에 선택할 변수가 부족합니다. 다른 열을 선택하거나 자료를 추가해 주세요.')
                index = options.index(preferred) if preferred in options else 0
                return st.selectbox(label,options,index=index,key='sel_'+mode+key)


            params = {}
            try:
                if mode == '기초통계':
                    default = ['score'] if 'score' in numeric else numeric[:1]
                    params['columns'] = st.multiselect('수치형 변수',numeric,default=default,key='sel_desc')
                    cat = st.selectbox('빈도표 변수 (선택)', ['사용 안 함'] + all_columns,
                                       index=all_columns.index('method')+1 if 'method' in all_columns else 0,key='sel_freq')
                    params['category'] = None if cat=='사용 안 함' else cat
                    st.caption('표준편차는 표본 표준편차(n−1)입니다. 기초통계는 열마다 유효 사례 수가 다를 수 있습니다.')
                elif mode in ('단순회귀','다중회귀'):
                    params['y'] = pick('결과변수 Y',numeric,'score','y')
                    options = [c for c in numeric if c!=params['y']]
                    if mode == '단순회귀':
                        params['xs'] = [pick('설명변수 X',options,'study_time','x')]
                    else:
                        defaults = [c for c in ['study_time','pre_score'] if c in options] or options[:2]
                        params['xs'] = st.multiselect('설명변수 X (2~10개)',options,default=defaults,key='sel_multi_x')
                    st.caption('수치형 변수만 사용합니다. 범주형 설명변수의 더미 코딩은 이 앱에서 제공하지 않습니다.')
                elif mode in ('일원분산분석','이원분산분석'):
                    params['y'] = pick('결과변수 Y',numeric,'anova_score','y')
                    opts = [c for c in factors if c!=params['y']]
                    if mode == '일원분산분석':
                        params['group'] = pick('집단변수',opts,'method','group')
                        st.caption('집단당 2사례 이상 · Tukey HSD 사후검정 · η² 및 ω² 표시')
                    else:
                        params['factor_a'] = pick('요인 A',opts,'method','a')
                        params['factor_b'] = pick('요인 B',[c for c in opts if c!=params['factor_a']],'grade','b')
                        ss = st.selectbox('제곱합 방식',['Type II (기준표 검산)','Type III (합 대비)'],key='sel_ss')
                        params['ss_type'] = 2 if ss.startswith('Type II ') else 3
                        st.caption('모든 A×B 조합에 2사례 이상 필요합니다. 반복측정 분석은 지원하지 않습니다.')
                else:
                    med = mode=='매개효과'
                    params['x'] = pick('설명변수 X',numeric,'med_x' if med else 'mod_x','x')
                    opts = [c for c in numeric if c != params['x']]
                    mid_key = 'mediator' if med else 'moderator'
                    params[mid_key] = pick('매개변수 M' if med else '조절변수 W',opts,'med_m' if med else 'mod_w','mid')
                    params['y'] = pick('결과변수 Y',[c for c in opts if c!=params[mid_key]],'med_y' if med else 'mod_y','y')
                    if med:
                        params['n_boot'] = st.selectbox('부트스트랩 반복 횟수',[2000,5000,10000],key='sel_boot')
                        params['seed'] = int(st.number_input('난수 시드 (같은 값이면 재현 가능)',min_value=0,max_value=2147483647,value=42,key='sel_seed'))
                        st.caption('동일한 유효 사례로 모든 경로 추정 · percentile 95% 신뢰구간')
                    else:
                        params['center'] = st.checkbox('X와 W를 평균 중심화',value=True,key='sel_center')
                        st.caption('중심화해도 상호작용 계수와 R²는 유지됩니다. 주효과와 절편의 의미는 달라집니다.')
            except AnalysisError as exc:
                st.warning(str(exc))
                st.stop()

            # 설정을 바꾸면 이전 결과를 숨겨, 새 설정의 결과로 오해하지 않게 한다.
            signature = (fingerprint,mode,repr(params))
            if st.session_state.get('signature') != signature:
                st.session_state.pop('result',None)
            st.session_state.signature = signature

            if st.button('분석 실행',type='primary',width='stretch',icon=':material/arrow_forward:'):
                try:
                    with st.spinner('자료를 확인하고 계산하고 있습니다…'):
                        if mode=='기초통계':
                            if not params['columns'] and not params['category']:
                                raise AnalysisError('수치형 변수 또는 빈도표 변수를 선택해 주세요.')
                            result = {'description':descriptive_statistics(df,params['columns']) if params['columns'] else pd.DataFrame(),
                                      'frequency':frequency_table(df,params['category']) if params['category'] else pd.DataFrame()}
                        elif mode in ('단순회귀','다중회귀'):
                            if mode=='다중회귀' and len(params['xs']) < 2:
                                raise AnalysisError('다중회귀의 설명변수는 2개 이상 선택해 주세요. 1개이면 단순회귀 메뉴를 사용하세요.')
                            result = regression(df,**params)
                        else:
                            funcs = {'일원분산분석':one_way_anova,'이원분산분석':two_way_anova,'매개효과':mediation,'조절효과':moderation}
                            result = funcs[mode](df,**params)
                    st.session_state.result = result
                except AnalysisError as exc:
                    st.error(str(exc))
                except Exception:
                    logging.exception('분석 실패')
                    st.error('계산 중 문제가 발생했습니다. 다른 변수로 다시 시도하거나 데이터와 설치 버전을 확인해 주세요.')

if 'result' not in st.session_state:
    render_empty_result()
    render_footer()
    st.stop()
with st.container(key='results_panel'):
    r = st.session_state.result
    tables = {}
    notes = [f'데이터 한눈에 | {mode}',f'데이터: {source_name}',f'설정: {params}']
    section_title('03', '분석 결과', mode + ' · 결과표와 그래프를 함께 살펴보세요.')


    def show_table(title, data):
        st.subheader(title)
        display = data.copy()
        for c in display.columns:
            if c in ('p','보정 p'):
                display[c] = display[c].map(lambda v:'—' if pd.isna(v) else format_p(v))
            elif pd.api.types.is_float_dtype(display[c]):
                display[c] = display[c].round(6)
        st.dataframe(display,hide_index=True,width='stretch')
        tables[title] = data


    def chart(fig):
        fig.update_layout(template='plotly_white',font=dict(family='Inter, Apple SD Gothic Neo, Malgun Gothic, sans-serif',size=12,color='#52647b'),
                          colorway=['#0b8b79','#607aab','#d6a14a','#9178ae'],
                          paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
                          margin=dict(l=10,r=10,t=35,b=10),height=340,
                          legend=dict(orientation='h',y=-.25))
        fig.update_xaxes(gridcolor='#edf1f6',zerolinecolor='#e2e9f1',linecolor='#e2e9f1')
        fig.update_yaxes(gridcolor='#edf1f6',zerolinecolor='#e2e9f1',linecolor='#e2e9f1')
        st.plotly_chart(fig,width='stretch',config={'displaylogo':False})


    def interpretation(text):
        st.info(text)
        notes.append(text)


    if mode!='기초통계':
        st.success(f'전체 {r["total"]}사례 중 {r["n"]}사례 사용 · 선택 변수의 결측/무한대로 {r["dropped"]}사례 제외')
        notes.append(f'전체 {r["total"]}, 사용 {r["n"]}, 제외 {r["dropped"]}; 선택 변수 완전사례 분석')

    if mode=='기초통계':
        if not r['description'].empty:
            show_table('수치형 변수 요약',r['description'])
            for col in params['columns']:
                s = numeric_series(df[col]).dropna()
                if len(s):
                    chart(px.histogram(x=s,labels={'x':col,'y':'빈도'},title=f'{col} 분포',nbins=min(20,max(4,int(np.sqrt(len(s)))))))
            first = r['description'].iloc[0]
            interpretation(f'{first["변수"]}: 유효 {int(first["사용 사례 수(n)"])}사례, 평균 {first["평균"]:.3f}, 표본 표준편차 {first["표준편차"]:.3f}입니다. 변수가 여러 개이면 각 열의 유효 사례 수를 확인하세요.')
        if not r['frequency'].empty:
            show_table('빈도와 비율',r['frequency'])
            chart(px.bar(r['frequency'].head(30),x='범주',y='빈도',title=f'{params["category"]} 빈도 (상위 30개)'))
            notes.append('전체 비율은 결측 포함 전체 행 수, 유효 비율은 결측 제외 행 수가 분모입니다.')
        notes.append('표본 표준편차 ddof=1; 무한대는 결측으로 처리. 사례 1개이면 표준편차는 계산 불가입니다.')
    elif mode in ('단순회귀','다중회귀'):
        a,b = st.columns(2)
        a.metric('R²',f'{r["r2"]:.4f}'); b.metric('수정 R²',f'{r["adj_r2"]:.4f}')
        show_table('회귀계수',r['coefficients'])
        model = r['model']
        equation = f'예측 {params["y"]} = {model.params.iloc[0]:.4f}' + ''.join(f' {coef:+.4f} × {name}' for coef,name in zip(model.params.iloc[1:],params['xs']))
        st.write(equation); notes.append(equation)
        show_table('다중공선성 VIF',r['vif'])
        if mode=='단순회귀':
            x,y = params['xs'][0],params['y']
            fig = px.scatter(r['data'],x=x,y=y,title='관측값과 회귀선')
            order = np.argsort(r['data'][x].to_numpy())
            fig.add_scatter(x=r['data'][x].to_numpy()[order],y=np.asarray(model.fittedvalues)[order],mode='lines',name='회귀선')
            chart(fig)
        fig = px.scatter(r['residuals'],x='예측값',y='잔차',title='잔차와 예측값')
        fig.add_hline(y=0,line_dash='dash'); chart(fig)
        qq = stats.probplot(np.asarray(model.resid),dist='norm')
        fig = go.Figure(go.Scatter(x=qq[0][0],y=qq[0][1],mode='markers',name='잔차'))
        fig.add_scatter(x=qq[0][0],y=qq[1][0]*qq[0][0]+qq[1][1],mode='lines',name='기준선')
        fig.update_layout(title='잔차 Q–Q 그래프',xaxis_title='정규분포 이론 분위수',yaxis_title='잔차 분위수');chart(fig)
        tables['잔차'] = r['residuals']
        tables['모형요약'] = pd.DataFrame({'R²':[r['r2']],'수정 R²':[r['adj_r2']],'F':[model.fvalue],'모형 p':[model.f_pvalue]})
        interpretation(f'이 모형의 R²는 {r["r2"]:.4f}입니다. 표본에서 {params["y"]} 변동의 약 {100*r["r2"]:.1f}%를 설명합니다. 계수의 방향·크기·신뢰구간과 잔차를 함께 확인하세요. 인과관계를 뜻하지 않습니다.')
    elif mode in ('일원분산분석','이원분산분석'):
        show_table('집단별 기초통계',r['groups'])
        show_table('분산분석표',r['table'])
        if mode=='일원분산분석':
            a,b = st.columns(2);a.metric('η²',f'{r["eta2"]:.4f}');b.metric('ω²',f'{r["omega2"]:.4f}')
            show_table('Tukey HSD 사후비교',r['posthoc'])
            tables['효과크기 및 등분산'] = pd.DataFrame({'η²':[r['eta2']],'ω²':[r['omega2']],'Levene 통계량':[r['levene']['통계량']],'p':[r['levene']['p']]})
            st.caption(f'Levene 등분산 검정 p = {format_p(r["levene"]["p"])} · 중앙값 기준')
            chart(px.box(r['data'],x=params['group'],y=params['y'],color=params['group'],points='all',title='집단별 분포'))
            p = r['table'].iloc[0]['p']
            interpretation(f'F = {r["table"].iloc[0]["F"]:.4f}, p = {format_p(p)}. ' +
                           ('적어도 한 집단 평균이 다르다는 통계적 근거가 있습니다. 어느 집단이 다른지는 사후비교를 확인하세요.' if p<.05 else '평균 차이의 통계적 근거가 충분하지 않습니다. 집단들이 같다고 입증된 것은 아닙니다.'))
        else:
            chart(px.line(r['groups'],x=params['factor_a'],y='평균',color=params['factor_b'],markers=True,title='두 요인의 상호작용 (집단 평균)'))
            tables['조합별 사례 수'] = r['cell_counts'].reset_index()
            interpretation(f'상호작용 p = {format_p(r["interaction_p"])}. ' +
                           ('두 요인의 조합에 따라 평균 차이 양상이 달라질 수 있습니다.' if r['interaction_p']<.05 else '상호작용에 대한 통계적 근거가 충분하지 않습니다.'))
    elif mode=='매개효과':
        show_table('경로계수',r['paths'])
        st.metric('간접효과 a × b',f'{r["indirect"]:.4f}')
        lo,hi = r['ci']
        st.write(f'부트스트랩 95% 신뢰구간: [{lo:.4f}, {hi:.4f}]')
        st.caption(f'유효 재표집 {r["valid_boot"]:,}/{r["n_boot"]:,}회 · 시드 {r["seed"]}')
        chart(px.histogram(x=r['bootstrap'],nbins=40,labels={'x':'간접효과 a×b','y':'빈도'},title='부트스트랩 간접효과 분포'))
        tables['간접효과'] = pd.DataFrame({'ab':[r['indirect']],'95% CI 하한':[lo],'95% CI 상한':[hi],
                                          '요청 반복':[r['n_boot']],'유효 반복':[r['valid_boot']],'시드':[r['seed']]})
        interpretation(('신뢰구간이 0을 포함하지 않아 간접적 연관에 대한 통계적 근거가 있습니다.' if lo>0 or hi<0 else '신뢰구간이 0을 포함하여 간접적 연관의 통계적 근거가 충분하지 않습니다.') + ' 이 결과만으로 원인과 결과 또는 완전·부분 매개를 확정하지 않습니다.')
        notes.append(f'ab={r["indirect"]:.6f}, percentile 95% CI=[{lo:.6f}, {hi:.6f}], c={r["c"]:.6f}, c′={r["direct"]:.6f}')
    else:
        a,b = st.columns(2);a.metric('R²',f'{r["r2"]:.4f}');b.metric('상호작용 추가 ΔR²',f'{r["delta_r2"]:.4f}')
        show_table('회귀계수',r['coefficients'])
        show_table('W 수준별 단순기울기',r['slopes'])
        chart(px.line(r['lines'],x='X',y='예측 Y',color='W 수준',title='조절변수 수준별 예측선',labels={'X':params['x'],'예측 Y':f'예측 {params["y"]}'}))
        tables['모형요약'] = pd.DataFrame({'R²':[r['r2']],'수정 R²':[r['adj_r2']],'ΔR²':[r['delta_r2']],
                                          'X 평균':[r['means'][0]],'W 평균':[r['means'][1]],'중심화':[r['centered']]})
        interpretation(f'상호작용 계수 B = {r["interaction"]:.4f}, p = {format_p(r["interaction_p"])}. ' +
                       ('W에 따라 X와 Y 사이의 관계가 달라진다는 통계적 근거가 있습니다.' if r['interaction_p']<.05 else 'W에 따라 관계가 달라진다는 통계적 근거가 충분하지 않습니다.'))

    for warning in r.get('warnings',[]):
        st.warning(warning)
        notes.append(warning)
    st.caption('p값은 0으로 표시하지 않습니다. p < .001은 매우 작은 값이며, 효과가 크거나 인과적이라는 뜻은 아닙니다. 다운로드에는 반올림 전 수치가 담깁니다.')
    notes.append('유의수준 .05; p값만으로 중요도·인과관계를 판정하지 않음. 미지원: 로지스틱 회귀, 반복측정 ANOVA, 다층모형, BCa 부트스트랩.')
    summary = '\n'.join(notes)
    st.subheader('결과 가져가기')
    c1,c2 = st.columns(2)
    c1.download_button('결과표 엑셀',export_excel(tables,summary),file_name=f'{mode}_결과.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
    c2.download_button('해석과 설정 TXT',summary.encode('utf-8-sig'),file_name=f'{mode}_해석.txt',mime='text/plain',width='stretch')

render_footer()
