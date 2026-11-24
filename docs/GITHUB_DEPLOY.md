# GitHub 저장소와 실행 주소 만들기

팀원: 은수현, 김정훈, 김응범

## 현재 배포 상태 · 2026-11-24

- **[데이터 한눈에 실행](https://4mlyngvxcnuchcxkbzspn8.streamlit.app/)**: 로그인 없이 이용 가능합니다.
- **[GitHub 저장소](https://github.com/KEBEOM/kumho_bigdata_8)**: 공개 저장소, `main` 브랜치의 루트 `app.py`를 배포했습니다.
- 현재 서버는 Streamlit 기본 Python 설정을 사용했습니다. 정확한 버전은 별도 확인하지 않았으며, 아래의 3.12는 새로 배포할 때의 권장값입니다.
- 기준 데이터와 다중회귀 실행을 확인했습니다. 구체적인 결과와 미확인 항목은 [배포 확인 기록](배포확인.md)에 있습니다.

아래는 다른 계정에서 다시 배포하거나 설정을 확인할 때 참고할 절차입니다.

## 1. GitHub에 소스 올리기

1. 이 과제의 저장소는 [KEBEOM/kumho_bigdata_8](https://github.com/KEBEOM/kumho_bigdata_8)입니다. 다른 계정에서 새로 배포하는 경우 별도 저장소를 만듭니다.
2. 소스 ZIP을 해제합니다. `stat_app` 안의 **파일과 하위 폴더**를 저장소 최상위에 올립니다.
3. 저장소 첫 화면에 `app.py`, `analysis.py`, `data_io.py`, `requirements.txt`, `sample.xlsx`, `README.md`가 보이는지 확인합니다.
4. 숨김 폴더인 `.streamlit`, `.github`와 `.gitignore`, `.gitattributes`도 포함합니다. macOS Finder에서는 `Command+Shift+.`으로 숨김 파일을 표시할 수 있습니다.
5. `Commit changes`로 저장합니다. ZIP 파일 자체를 업로드하는 것만으로는 배포되지 않습니다.

가상환경, 캐시, 실제 조사자료, 비밀번호·토큰을 올리지 않습니다. 이 프로젝트의 `.gitignore`는 실행 환경과 비밀 설정을 제외합니다. 웹 업로드에서는 제외 규칙이 자동 적용되지 않으므로 배포용 소스에 포함된 파일만 올립니다.

## 2. Streamlit Community Cloud에 연결

1. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인합니다.
2. GitHub 계정을 연결하고, 사용할 저장소에 대한 필요한 접근 권한을 설정합니다. 배포할 계정은 저장소 관리자 권한이 필요합니다.
3. `Create app` → `Yup, I have an app`을 선택합니다.
4. Repository는 `KEBEOM/kumho_bigdata_8`, Branch는 `main`, Main file path는 **`app.py`**로 지정합니다.
5. `Advanced settings`에서 Python **3.12**를 선택합니다. 이 값은 서버 실행 환경이며 로컬 실행을 3.12로 제한하지 않습니다. 이 앱에 입력할 Secrets는 없습니다.
6. `Deploy` 후 설치 로그를 확인합니다. 오류 없이 앱 화면이 열리면 표시되는 `streamlit.app` 실행 주소를 복사합니다.

저장소 URL은 소스를 보는 주소이고, `streamlit.app` URL은 앱을 사용하는 주소입니다. 배포가 완료된 후에만 실제 실행 주소를 제출 문서에 기록합니다.

## 3. 배포 후 확인

- 기준 데이터의 36사례·14변수가 표시되는지 확인합니다.
- 다중회귀에서 Y=`score`, X=`study_time`, `pre_score`로 실행하여 R²가 약 0.9349인지 확인합니다.
- 결과 엑셀과 해석 TXT를 다운로드합니다.
- 휴대폰 브라우저에서 **배포 주소**로 접속하여 분석과 다운로드를 확인합니다. 같은 Wi-Fi에 있을 필요가 없습니다.
- GitHub **Actions → Python compatibility**에서 6개 Python 검사 결과를 확인합니다.

클라우드의 자원 한도나 휴면 정책에 따라 첫 접속이 늦어질 수 있습니다. 실제 이용 가능 상태는 배포 화면에서 확인합니다.

## 4. 수정 내용 반영

GitHub의 배포 브랜치(`main`)에 수정 사항을 저장하면 Streamlit이 해당 변경을 반영합니다. 패키지가 바뀌면 설치 시간이 추가로 필요할 수 있습니다. Actions의 검사 실패가 Streamlit 자동 배포를 막도록 구성된 것은 아니므로, 중요한 수정은 별도 브랜치와 Pull request에서 검사 후 `main`에 병합합니다.

## 5. 교수님께 제시할 자료

- 기존 제출물 두 ZIP: 마스터·코딩 프롬프트 / 전체 소스
- 실제 생성된 GitHub 저장소 주소
- 앱 실행 주소: https://4mlyngvxcnuchcxkbzspn8.streamlit.app/
- GitHub Actions 결과와 앱 시연 화면

공식 안내: [배포 절차](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [GitHub 연결](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account).

현재 저장소는 공개 상태이며 앱도 로그인 없는 접속을 확인했습니다. 향후 공개 범위를 변경하면 소스와 앱의 접근 가능 여부를 각각 다시 확인합니다.
