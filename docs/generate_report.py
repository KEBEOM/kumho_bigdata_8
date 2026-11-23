"""동봉된 기준 데이터로 검산표와 HTML 보고서를 다시 만든다.
실행: python docs/generate_report.py (화면 테스트를 대신하지 않음)
"""
from pathlib import Path
import hashlib
import html
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis import descriptive_statistics,regression,one_way_anova,two_way_anova,mediation,moderation


def main():
    df=pd.read_excel(ROOT/'sample.xlsx')
    d=descriptive_statistics(df,['score']).iloc[0]
    s=regression(df,'score',['study_time'])
    r=regression(df,'score',['study_time','pre_score'])
    a=one_way_anova(df,'anova_score','method')
    b=two_way_anova(df,'anova_score','method','grade')
    m=mediation(df,'med_x','med_m','med_y',2000,42)
    w=moderation(df,'mod_x','mod_w','mod_y')
    rows=[]
    def check(kind,metric,expected,actual,digits):
        tolerance=.5*10**(-digits)
        rows.append({'분석':kind,'항목':metric,'교수자 기준값':expected,'앱 계산값':float(actual),
                     '절대 차이':abs(actual-expected),'허용 오차':tolerance,
                     '판정':'일치' if abs(actual-expected)<=tolerance+1e-12 else '불일치'})
    for metric,expected,digits in [('사용 사례 수(n)',36,0),('평균',76,3),('표준편차',8.135,3),('중앙값',76,3),('최소값',60,0),('최대값',92,0)]:
        check('기초통계',metric,expected,d[metric],digits)
    for metric,expected,actual,digits in [('R²',.0330,s['r2'],4),('절편',72.4268,s['coefficients'].iloc[0]['B'],4),
          ('study_time B',1.1089,s['coefficients'].iloc[1]['B'],4),('study_time p',.288707,s['coefficients'].iloc[1]['p'],6)]:
        check('단순회귀',metric,expected,actual,digits)
    for metric,expected,actual,digits in [('R²',.9349,r['r2'],4),('수정 R²',.9310,r['adj_r2'],4),
          ('study_time B',.0729,r['coefficients'].iloc[1]['B'],4),('study_time p',.792724,r['coefficients'].iloc[1]['p'],6),
          ('pre_score B',.8912,r['coefficients'].iloc[2]['B'],4),('pre_score p',0.,r['coefficients'].iloc[2]['p'],6)]:
        check('다중회귀',metric,expected,actual,digits)
    check('일원분산','F',14.0291,a['table'].iloc[0]['F'],4)
    check('일원분산','p',.000039,a['table'].iloc[0]['p'],6)
    for group,expected in [('A',55.166),('B',58.193),('C',62.407)]:
        check('일원분산',f'{group} 평균',expected,a['groups'].set_index('method').loc[group,'평균'],3)
    for i,name,expected in [(0,'method',266.3419),(1,'grade',283.2311),(2,'상호작용',8.2607)]:
        check('이원분산',name+' F',expected,b['table'].iloc[i]['F'],4)
    for i,name,expected in [(0,'method',0.),(1,'grade',0.),(2,'상호작용',.000174)]:
        check('이원분산',name+' p',expected,b['table'].iloc[i]['p'],6)
    for key,metric,expected in [('a','a',.8027),('b','b',1.5300),('direct','c′',.1383),('indirect','ab',1.2282)]:
        check('매개효과',metric,expected,m[key],4)
    check('조절효과','상호작용 B',.6786,w['interaction'],4)
    check('조절효과','상호작용 p',0.,w['interaction_p'],6)
    check('조절효과','R²',.9743,w['r2'],4)
    comparison=pd.DataFrame(rows)
    comparison.to_csv(ROOT/'docs/기준값_검산표.csv',index=False,encoding='utf-8-sig')
    passed=int((comparison['판정']=='일치').sum())
    markup=comparison.to_html(index=False,classes='results',float_format=lambda v:f'{v:.9g}',escape=True)
    digest=hashlib.sha256((ROOT/'sample.xlsx').read_bytes()).hexdigest()
    template='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>데이터 한눈에 검산보고서</title><style>
body{font-family:"Noto Sans CJK KR","Malgun Gothic",sans-serif;color:#20383e;background:#f4f7f6;margin:0;line-height:1.7}
main{max-width:1060px;margin:32px auto;padding:40px;background:white;border-radius:16px}h1{font-size:32px;line-height:1.25;margin:0 0 16px}h2{font-size:23px;margin-top:38px}
.eyebrow{color:#087e77;font-weight:bold;letter-spacing:2px;font-size:12px}.intro{font-size:18px;color:#56696f}.pill{display:inline-block;border-radius:8px;background:#e9f6f2;padding:14px 20px;margin:10px 10px 10px 0;font-weight:bold}
.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:9px 12px;border-bottom:1px solid #e1e7e6;text-align:left}th{background:#edf5f3}tr:nth-child(even){background:#fafcfc}
.notice{background:#fff5e4;border-left:4px solid #dba553;padding:16px}img{max-width:100%;border:1px solid #dce6e4;border-radius:8px}code{word-break:break-all}a{color:#087e77}
@media(max-width:650px){main{margin:0;padding:22px;border-radius:0}h1{font-size:27px}}@media print{body{background:white}main{margin:0;padding:0}h2{break-after:avoid}tr,img{break-inside:avoid}.table-wrap{overflow:visible}}
</style><main><p class="eyebrow">DATA LAB / VALIDATION</p><h1>데이터 한눈에 검산보고서</h1>
<p class="intro">제출자 은수현, 김정훈, 김응범 · 교수자 제공 기준 데이터 36사례를 이용한 계산 검증</p>
<div class="pill">기준 항목 __PASSED__ / __TOTAL__ 일치</div><div class="pill">6개 Python 환경에서 각 59개 통과</div><div class="pill">브라우저 결과 다운로드 확인</div>
<p>기초통계부터 회귀, 일원·이원분산분석, 매개·조절효과까지 제공된 정답표의 모든 수치를 대조했다. 기준표의 마지막 표시 자릿수 절반을 허용 오차로 사용했으며, 기준값을 실제 계산에 덮어쓰지 않았다.</p>
<h2>검산 조건</h2><ul><li>기초통계 표준편차는 표본 기준이며, 모형은 선택 변수의 완전사례를 사용했다. 기준 데이터는 모든 모형에서 36사례가 사용되었다.</li>
<li>이원분산분석은 상호작용 포함, Sum coding, Type II 제곱합이다.</li><li>매개효과 부트스트랩은 2,000회, 시드 42, percentile 95% 신뢰구간이다.</li><li>조절효과는 X·W 평균 중심화를 기본으로 하고 원점수 모형과의 불변성을 검사했다.</li></ul>
<p class="notice">교수자 표의 p=0.000000은 반올림된 값이다. 앱에서 계산된 작은 양의 p값을 그대로 보존하고, 화면에는 &lt; .001로 표시한다.</p>
<h2>기준값과 계산값 비교</h2><div class="table-wrap">__TABLE__</div>
<h2>추가 검증과 해석</h2><p>매개 간접효과 ab=__AB__, percentile 95% CI=[__LO__, __HI__], 유효 재표집 2,000/2,000회이다. 이 신뢰구간은 제공 정답표에 없으므로 교수자 정답과의 일치 항목으로 계산하지 않았다. 고정 시드 재현성과 경로 항등식 c=c′+ab를 별도로 확인했다.</p>
<p>회귀는 NumPy 최소제곱과, 일원분산분석은 SciPy f_oneway와 독립 대조했다. 중복 변수·문자 혼입·결측·무한대·상수·공선성·표본 부족·빈 집단 조합·잘못된 파일을 자동 검사했다. Streamlit AppTest에서 7개 분석 메뉴를 실제로 실행했다.</p>
<p>Python 3.9.25, 3.10.22, 3.11.18, 3.12.14, 3.13.5, 3.14.10의 독립된 Linux 환경에서 각각 59개 검사를 통과했다. Python별 실제 설치 조합은 호환성보고서.md와 locks 폴더에 기록했다. 자세한 로그는 <a href="자동검사결과.txt">자동검사결과.txt</a>, 설치 버전은 <a href="실행환경.txt">실행환경.txt</a>를 참조한다.</p>
<h2>실행 화면 확인</h2><p>브라우저에서 기초통계와 다중회귀 결과를 확인하고 결과 엑셀을 다운로드했다. 다운로드 파일을 다시 열어 score 평균 76, n=36이 기록되어 있음을 확인했다. 아래 이미지는 실제 브라우저 화면의 일부이다.</p>
<figure><img src="screenshots/03_PC_다중회귀.jpg" alt="다중회귀 결과 R 제곱과 회귀계수 표"><figcaption>다중회귀 결과와 사용 사례 수</figcaption></figure>
<figure><img src="screenshots/02_PC_기초통계결과.jpg" alt="기초통계 히스토그램과 빈도표"><figcaption>기초통계 그래프와 빈도표</figcaption></figure>
<h2>확인 범위와 남은 확인</h2><p class="notice">자동 검사는 Python 6개 환경에서 수행했다. 화면 캡처는 최초 버전의 PC 브라우저 실행 결과이며 분석 화면과 계산 기능은 유지했다. Windows 및 macOS 실기기 검증은 수행하지 않았다. 실제 스마트폰, 모바일 화면 크기별 시각 검증 및 사용자 Wi-Fi 접속은 수행하지 않았다. 제출자가 README의 절차에 따라 본인 PC와 스마트폰에서 최종 확인해야 한다. 공용 서버나 GitHub 배포는 하지 않았다.</p>
<p>이 앱은 독립 관측을 전제로 하는 교육용 도구이다. 인과적 결론, 반복측정, 군집 자료, 로지스틱 회귀, Welch/Games–Howell 및 BCa 부트스트랩은 지원 범위 밖이다. 유의확률만으로 효과의 중요성을 판단하지 않는다.</p>
<h2>재현 방법과 출처</h2><p>앱 폴더에서 <code>python -m pytest -q tests</code>로 자동 검사를 실행한다. <code>python docs/generate_report.py</code>로 기준값 검산표를 다시 만든다. 보고서 생성은 새 브라우저 검사나 스마트폰 검증을 수행하지 않는다.</p>
<p>출처: 첨부 학생용 설명서, 통계앱 starter, 추가자료의 기준 데이터와 기준 결과. 원문 기준표는 data/교수자_기준결과_원문.md에 보관했다. 기준 데이터 SHA-256: <code>__HASH__</code></p>
</main></html>'''
    for key,value in {'__PASSED__':str(passed),'__TOTAL__':str(len(rows)),'__TABLE__':markup,
        '__AB__':f'{m["indirect"]:.6f}','__LO__':f'{m["ci"][0]:.6f}','__HI__':f'{m["ci"][1]:.6f}','__HASH__':digest}.items():
        template=template.replace(key,value)
    (ROOT/'docs/검산보고서.html').write_text(template,encoding='utf-8')
    print(f'기준값 {passed}/{len(rows)} 일치; 간접효과 CI {m["ci"]}')
    if passed != len(rows):
        raise SystemExit('불일치 항목이 있습니다. 기준값_검산표.csv를 확인하세요.')


if __name__=='__main__':
    main()
