데이터 한눈에 v1.3
AI와 함께 만드는 스마트폰 PC 통계분석 웹앱
제출자: 은수현, 김정훈, 김응범

무엇을 하는 앱인가요?
엑셀/CSV를 읽어 9가지 분석 메뉴와 그래프, 쉬운 해석을 제공하는 교육용 웹앱입니다.
PC에서 프로그램을 켜고 PC 또는 같은 Wi-Fi의 스마트폰 브라우저로 접속할 수 있습니다.
GitHub 소스를 Streamlit Community Cloud에 배포하면 PC를 켜 두지 않고 배포 주소로 접속할 수 있습니다.
배포된 앱 이용자는 Python 설치가 필요하지 않습니다. APK나 iPhone 설치 파일은 아닙니다.
로컬 실행에는 GitHub 계정이나 AI API 키가 필요하지 않습니다. 온라인 배포에는 GitHub·Streamlit 계정이 필요합니다.
앱 실행 중 자료를 생성형 AI 서비스에 전송하지 않습니다.

GitHub 연동 및 온라인 배포
앱 실행 주소: https://4mlyngvxcnuchcxkbzspn8.streamlit.app/
소스 저장소: https://github.com/KEBEOM/kumho_bigdata_8
PC와 스마트폰 브라우저에서 앱 실행 주소를 엽니다. 이용자는 로그인이나 Python 설치가 필요 없습니다.
2026-11-24 배포 완료: 로그인 없는 접속, 기준 데이터 표시, 다중회귀와 엑셀 다운로드 동작 확인.
현재 배포는 Streamlit 기본 Python 설정을 사용했습니다. 정확한 서버 버전은 별도 확인하지 않았습니다.
README.md와 docs/GITHUB_DEPLOY.md를 참고합니다.
GitHub 저장소 최상위에 app.py, requirements.txt, sample.xlsx와 나머지 소스를 함께 올립니다.
Streamlit 배포: Branch=main, Main file path=app.py, Python=3.12 권장, Secrets는 비워 둡니다.
3.12는 배포 서버의 선택값이며 로컬 버전을 제한하는 요구사항이 아닙니다.
ZIP만 GitHub에 올리지 말고 압축을 푼 소스를 올립니다. start.py는 로컬 실행용입니다.
앱 코드를 수정하면 GitHub Actions에서 Python 3.9~3.14 검사를 실행하도록 설정했습니다.
2026-11-26 GitHub Actions에서도 Python 3.9~3.14의 6개 작업이 각각 82개 검사를 통과했습니다.
실제 배포 확인 범위는 docs/배포확인.md, 원격 검사 기록은 docs/v1.3_GitHub검증.json에 있습니다.

내 컴퓨터에 설치해서 실행하는 방법
64비트 CPython 3.9~3.14 중 하나가 설치되어 있으면 됩니다. 특정 3.12 버전을 요구하지 않습니다.
Streamlit이 제외한 Python 3.9.7은 지원하지 않습니다. 3.9의 다른 패치 버전 또는 3.10~3.14를 사용합니다.
Python 3.8 이하, 3.15 이상, PyPy 및 32비트 Python은 이번 지원 범위에 포함하지 않습니다.
최초 설치에는 인터넷이 필요합니다. Python 자체를 자동으로 설치하지는 않습니다.

1. ZIP 전체를 압축 해제합니다. ZIP 안에서 app.py만 실행하지 마세요.
2. app.py, start.py, README.txt가 보이는 stat_app 폴더를 엽니다.
3. Windows는 run_windows.bat를 더블클릭합니다.
   macOS는 run_mac.command를 실행합니다. 열리지 않으면 아래 터미널 방법을 사용합니다.
4. 최초 실행 시 앱 전용 가상환경과 필요한 패키지를 자동으로 준비합니다.
5. 브라우저에서 http://localhost:8501 을 엽니다.
6. 사용하는 동안 터미널을 켜 둡니다. 종료하려면 터미널에서 Ctrl+C를 누릅니다.

macOS / Linux 터미널 실행
터미널을 열고 cd 뒤에 공백을 넣은 다음 stat_app 폴더를 끌어 놓고 Enter를 누릅니다.
그다음 아래 한 줄을 실행합니다.
  bash run_mac_linux.sh
이 실행기는 python3를 우선 확인하고, 지원 범위 밖이면 다른 설치된 python3.14~python3.9를 찾습니다.
Python 버전을 직접 고르고 싶으면 다음처럼 실행합니다.
  python3 start.py
  python3.13 start.py
이름에 3.12를 넣을 필요가 없습니다. 설치되어 있는 지원 버전의 명령을 사용합니다.

Windows 터미널 실행
stat_app 폴더에서 아래 명령을 실행할 수도 있습니다.
  py -3 start.py
기본 Python이 지원 범위 밖이면 run_windows.bat를 사용하거나 설치된 버전을 직접 지정합니다.
  py -3.11 start.py
py 명령이 없고 python 명령만 있다면 python start.py를 사용합니다.

자동 준비가 하는 일
- 사용 중인 Python 버전별로 .venv-py39, .venv-py310, .venv-py311 등의 전용 환경을 만듭니다.
- requirements.txt의 허용 범위에서 해당 Python에 맞는 패키지 버전을 선택합니다.
- 기존 시스템 Python 패키지나 원래 .venv를 변경하지 않습니다.
- 다시 실행하면 설치 상태를 확인하고, 요구사항이 같고 패키지가 정상이면 재설치하지 않습니다.
- 터미널이나 폴더 경로에 한글·공백이 있어도 인수를 따로 전달하도록 구현했습니다.
- 최초 설치 전부터 오프라인인 경우에는 필요한 패키지를 받을 수 없습니다.

스마트폰으로 보기
온라인: 위 앱 실행 주소를 스마트폰 브라우저에서 엽니다. PC를 켜 두거나 같은 Wi-Fi를 사용할 필요가 없습니다.
아래는 클라우드 대신 내 PC에서 실행한 앱에 연결하는 방법입니다.
1. PC와 스마트폰을 같은 Wi-Fi에 연결합니다.
2. PC에서 앱을 다음처럼 켭니다.
   macOS/Linux: bash run_mac_linux.sh --lan
   Windows 터미널: run_windows.bat --lan
   또는 지원 버전의 Python으로: python3 start.py --lan / py -3 start.py --lan
3. PC의 Wi-Fi IPv4 주소를 확인합니다. Windows는 ipconfig, macOS는 시스템 설정의 Wi-Fi 상세정보를 봅니다.
4. PC 주소가 192.168.0.15이면 스마트폰에서 http://192.168.0.15:8501 을 엽니다.
   이 주소는 예시이므로 실제 PC 주소로 바꿔야 합니다.
5. 스마트폰에서 localhost를 사용하면 PC로 연결되지 않습니다.
6. 같은 Wi-Fi인지, 학교망이 기기 간 통신을 막는지, PC 방화벽이 연결을 허용하는지 확인합니다.
   방화벽 전체를 끄지는 마세요. PC에서 먼저 정상 동작하는지 확인합니다.
7. 넓은 결과표는 표 안을 좌우로 밀어 봅니다. 엑셀 다운로드로 전체 표를 볼 수도 있습니다.
실제 스마트폰 기기와 사용자 Wi-Fi 접속은 제출자가 자신의 환경에서 확인해야 합니다.

원하는 환경을 직접 준비하는 방법
자동 실행기를 사용하면 이 절차를 별도로 진행할 필요가 없습니다.
Windows:
  py -3 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m streamlit run app.py
macOS/Linux:
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python -m streamlit run app.py
패키지 버전을 1개 조합으로 고정하지 않았으므로 Python별로 설치된 버전은 다를 수 있습니다.
검증 시 사용한 정확한 버전을 재현하려면 docs/locks의 해당 Python 파일을 사용합니다.
예: Python 3.11 환경에서 python -m pip install -r docs/locks/requirements-py311.txt
이 잠금 파일에는 테스트 도구도 포함되어 있으며, 기록된 플랫폼과 다른 OS에서는 전이 의존성이 달라질 수 있습니다.

5분 사용 순서
1. ‘기준 데이터로 연습’이 기본 선택되어 있습니다.
2. 분석 종류를 선택하면 기준 자료에 맞는 변수가 자동 선택됩니다.
3. ‘분석 실행’을 누릅니다.
4. 사용/제외 사례 수와 결과표·그래프·해석을 확인합니다.
5. ‘결과표 엑셀’과 ‘해석과 설정 TXT’를 내려받습니다.
6. 파일 또는 설정을 바꾸면 이전 결과는 사라집니다. ‘분석 실행’을 다시 누릅니다.

기준 데이터에서 선택할 변수
기초통계: 수치형 score, 빈도표 method
단순회귀: Y=score, X=study_time
다중회귀: Y=score, X=study_time + pre_score
일원분산분석: Y=anova_score, 집단=method
이원분산분석: Y=anova_score, A=method, B=grade, Type II
매개효과: X=med_x, M=med_m, Y=med_y, 2,000회, seed=42
조절효과: X=mod_x, W=mod_w, Y=mod_y, 평균 중심화 선택
id는 사례 구별용 값이므로 설명변수로 선택하지 않습니다.

내 파일 준비
.xlsx, .xls, .csv / 최대 10MB / 최대 10,000행·100열
첫 행: 공백이나 중복이 없는 열 이름
둘째 행부터: 한 줄에 한 사례, 한 열에 한 변수
숫자 칸에 ‘없음’, ‘-’, 단위 같은 글자를 섞지 말고 결측은 빈칸으로 둡니다.
CSV는 UTF-8 또는 CP949를 지원합니다. 표준 쉼표 구분 파일을 사용하세요.
엑셀은 업로드 후 시트를 선택합니다. 병합 셀·여러 줄 제목·중간 합계는 먼저 정리합니다.
문자가 섞인 열은 수치형 목록에 나타나지 않을 수 있습니다. 데이터 미리보기에서 유형을 확인합니다.

계산 규칙
- 기초통계는 변수별 결측을 제외합니다. 표준편차는 표본 기준(ddof=1)입니다.
- 숫자형 ±무한대는 결측으로 취급합니다. 모형은 선택 변수의 완전사례만 사용합니다.
- 수치형 변수가 모두 같은 값, 중복 변수, 완전 공선성, 사실상 0인 잔차는 오류로 안내합니다.
- 일반 회귀는 사례 수가 추정 계수 수+1보다 커야 합니다. 이는 최소 계산 조건이지 충분한 표본 권고가 아닙니다.
- 매개·조절은 최소 10사례를 요구합니다. 작은 표본은 해석이 불안정합니다.
- ANOVA는 2~20집단을 허용하고 집단/조합마다 2사례 이상을 요구합니다.
- 일원 ANOVA의 η²=SS효과/SS전체, ω²=(SS효과−df효과×MS오차)/(SS전체+MS오차)입니다.
  음수 ω²는 표시상 0으로 제한합니다.
- 이원 ANOVA는 Sum coding, 상호작용 포함 모형이며 기본 Type II입니다. Type III도 선택 가능합니다.
  부분 η²=SS효과/(SS효과+SS오차)입니다.
- 매개는 행 단위 percentile 부트스트랩 95% CI입니다. BCa 방식이 아닙니다.
- 조절은 W 평균·평균±1 표본 SD에서 단순기울기를 계산하며 다중검정 보정 전 p값입니다.
- 유의수준 .05, 신뢰수준 95%입니다. p < .001을 0이라고 해석하지 않습니다.
- 화면은 반올림되지만 결과 엑셀에는 원시 정밀도를 보존합니다.

검산하기
자동 실행기를 쓰는 경우:
  macOS/Linux: bash run_mac_linux.sh --test
  Windows: run_windows.bat --test
  또는 지원 버전의 Python으로: python3 start.py --test
자동으로 pytest를 포함한 개발 패키지를 설치하고 테스트합니다.
이미 별도 가상환경을 준비한 경우:
  python -m pip install -r requirements-dev.txt
  python -m pytest -q tests
Python별 검증 결과는 docs/호환성보고서.md, v1.3의 실제 설치 버전은 docs/v1.3_호환성검증.json에 기록했습니다.
통계 기준값은 docs/검산보고서.html과 docs/기준값_검산표.csv에서 확인합니다.
교수자 기준표 원문은 data/교수자_기준결과_원문.md입니다.
기준값은 반올림 정밀도 안에서 비교합니다. p=0.000000 표기는 정확한 0을 뜻하지 않습니다.

파일 구성
app.py                   화면·변수 선택·그래프·결과 다운로드
ui.py                    화면 헤더·안내·푸터
assets/                  반응형 CSS와 장식용 SVG (앱과 함께 복사 필요)
analysis.py              기초통계·회귀·ANOVA·매개·조절 계산
data_io.py               파일 읽기·헤더 검사·결과 엑셀 생성
sample.xlsx              교수자 36사례 가상 기준 데이터
requirements.txt         Python별 설치가 가능한 패키지 범위
requirements-dev.txt     자동 검사 도구
start.py                 Python 확인·전용 환경 준비·설치·앱 실행
README.txt               설치·사용·검산 안내
run_windows.bat          Windows 설치 및 실행
run_mac_linux.sh         macOS/Linux 설치 및 실행
run_mac.command          macOS 더블클릭용 실행 파일
.streamlit/config.toml   색상·업로드 한도·사용통계 설정
tests/                   계산과 UI 자동 검사
data/                    원본 starter 샘플 및 교수자 기준표
docs/                    검산표·개발 기록·기능 설명·발표 메모

한계와 개선점
이 앱은 교육용입니다. 관찰자료의 상관·회귀·매개·조절 결과만으로 인과관계를 단정하지 않습니다.
독립 관측을 전제로 하며 반복측정·시계열·학교/학급 군집 구조를 보정하지 않습니다.
회귀에는 수치형 설명변수만 사용합니다. 로지스틱 회귀·범주형 더미 코딩·혼합모형은 미지원입니다.
등분산 ANOVA와 Tukey HSD를 사용합니다. Welch ANOVA·Games–Howell·반복측정 ANOVA는 미지원입니다.
결측 대체는 하지 않습니다. 완전사례 분석은 자료에 따라 편향을 만들 수 있습니다.
매개모형은 단일 X–M–Y, 조절모형은 단일 연속형 X–W–Y로 제한합니다.
앱 자체의 로그인·권한 관리 기능은 없습니다. 공개 시연에는 제공된 가상 자료를 사용합니다.
업로드 파일은 로컬 실행이면 내 PC, 클라우드 접속이면 배포 서버에서 처리됩니다.
향후 개선: 강건 표준오차, Welch/Games–Howell, 범주형 회귀, 결측 처리 선택, 실기기 접근성 검증.

자주 생기는 문제
ModuleNotFoundError: start.py를 다시 실행해 전용 환경의 설치 상태를 확인합니다. 수동 실행이면 해당 Python으로 requirements.txt를 설치합니다.
화면이 안 열림: 터미널이 실행 중인지, http://localhost:8501 주소가 맞는지 확인합니다.
Address already in use: 이미 켜진 앱을 쓰거나 start.py --port 8502로 실행하고 주소도 :8502로 바꿉니다.
Permission denied: 개인 폴더에 압축을 풀어 실행합니다.
변수 선택 오류: Y·X·M/W·A/B는 서로 다른 열이어야 합니다.
집단 오류: 각 집단 및 모든 A×B 조합의 유효 사례 수를 확인합니다.
검산 실패: 기준 데이터·선택 변수·Type II 설정을 확인하고, 해당 Python의 docs/locks 파일로 검증된 패키지 조합을 재현합니다.
Linux의 ensurepip/venv 없음: 운영체제에서 해당 Python의 venv 지원 패키지를 먼저 설치합니다.
설치 실패 후 재시도: 같은 실행 파일을 다시 실행합니다. 인터넷 연결과 오류 메시지를 확인합니다.

제출 방법
1. ‘은수현_김정훈_김응범_마스터와 코딩.zip’: 마스터 프롬프트와 코딩 프롬프트 두 문서
2. ‘은수현_김정훈_김응범_소스.zip’: 이 앱의 전체 소스와 샘플·검산·문서
팀원은 은수현, 김정훈, 김응범으로 파일명과 문서, 앱 표기에 반영했습니다.
과제 공지의 ‘소스,zip’은 압축 확장자로 동작하도록 ‘소스.zip’으로 작성했습니다.

참고
첨부 학생용 설명서, starter, 추가자료의 기준 데이터·기준 결과·주차별 프롬프트를 바탕으로 개발했습니다.
공식 API 문서:
https://www.statsmodels.org/stable/generated/statsmodels.stats.anova.anova_lm.html
https://www.statsmodels.org/stable/generated/statsmodels.stats.multicomp.pairwise_tukeyhsd.html
https://docs.streamlit.io/develop/api-reference/data/st.dataframe


v1.3 상관관계 및 구조방정식 확장 (2026-11-26)
- 상관관계: 기준 데이터 → 상관관계 → Pearson 또는 Spearman → 분석 실행.
  쌍별/공통 완전사례, 쌍별 n·양측 p·Holm 보정 p, 상관행렬을 확인합니다.
  Pearson 95% CI를 제공하며 Spearman 소표본은 순열검정을 사용합니다.
- 구조방정식: 구조방정식 예제로 연습 → 분석 실행.
  300사례·9지표 가상 자료이며 교수자 36사례 기준 자료와 다릅니다. 실제 학생 자료가 아닙니다.
  기본은 X→M→Y와 X→Y의 잠재변수 모형입니다. X/Y 2변수 모형과 2·3요인 CFA도 선택할 수 있습니다.
  각 요인에 지표 3~6개를 배정하고 첫 지표의 비표준화 부하량을 1로 고정합니다.
  연속형·독립 관측·다변량 정규성을 전제로 MLW로 계산합니다.
  적합도, 표준화·비표준화 부하량과 경로, B의 SE·p·95% CI, R²와 경로도를 표시합니다.
  CFI/TLI는 원값이라 1보다 클 수 있습니다. RMSEA는 N−1 규약입니다.
  최소 50사례는 실행 제한이며 표본 적정성을 보장하지 않습니다.
  순서형 전용 추정, 다집단·다층, 교차부하, 잔차 상관, 평균구조, 잠재 간접효과 검정은 미지원입니다.
  기존 매개효과 메뉴는 관측변수 회귀 기반이며 잠재변수 SEM과 구분합니다.
- 모형 선택·지표·설정 변경 후에는 다시 분석 실행을 누릅니다. 표와 안내를 XLSX/TXT로 받습니다.
- 자세한 계산식·한계: docs/상관분석_구조방정식_안내.md
- 검증 기록: docs/v1.3_검증보고서.md, docs/v1.3_호환성검증.json
