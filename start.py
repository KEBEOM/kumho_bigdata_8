"""Python 버전별 가상환경을 준비한 뒤 앱을 실행한다. 표준 라이브러리만 필요하다."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
MIN_MINOR = 9
MAX_MINOR = 14


def supported_version(version):
    """Streamlit이 제외한 3.9.7과 지원하지 않는 major/minor를 거른다."""
    major, minor, patch = tuple(version)[:3]
    return major == 3 and MIN_MINOR <= minor <= MAX_MINOR and (major, minor, patch) != (3, 9, 7)


def clean_environment():
    env = os.environ.copy()
    # 외부 Python 경로나 전역 패키지가 프로젝트 가상환경을 오염시키지 않게 한다.
    for key in ('PYTHONPATH', 'PYTHONHOME'):
        env.pop(key, None)
    env['PYTHONNOUSERSITE'] = '1'
    env['PYTHONUTF8'] = '1'
    return env


def run_command(command, **kwargs):
    return subprocess.run(command, cwd=str(ROOT), env=clean_environment(), check=True, **kwargs)


def environment_path():
    return ROOT / ('.venv-py%d%d' % sys.version_info[:2])


def environment_python(folder):
    return folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def check_dependencies(python, include_tests=False):
    # 설치 범위와 imports를 모두 확인한다. 패키지 폴더 유무만으로 성공을 판단하지 않는다.
    requirement_files = [str(ROOT / 'requirements.txt')]
    if include_tests:
        requirement_files.append(str(ROOT / 'requirements-dev.txt'))
    code = '''
import importlib, importlib.metadata as md, pathlib, sys
from packaging.requirements import Requirement
for filename in sys.argv[1:]:
    for line in pathlib.Path(filename).read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith(('#','-r')): continue
        req=Requirement(line)
        if req.marker and not req.marker.evaluate(): continue
        if not req.specifier.contains(md.version(req.name),prereleases=False):
            raise RuntimeError('호환 범위를 벗어난 패키지: '+req.name)
for module in ['streamlit','pandas','numpy','scipy','statsmodels.api','openpyxl','xlrd','plotly','semopy']:
    importlib.import_module(module)
'''
    try:
        run_command([str(python), '-c', code] + requirement_files, capture_output=True, text=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def prepare_environment(include_tests=False):
    folder = environment_path()
    python = environment_python(folder)
    if not python.exists():
        print('앱 전용 가상환경을 준비합니다:', folder.name, flush=True)
        venv.EnvBuilder(with_pip=True).create(str(folder))
    else:
        check = run_command([str(python), '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'], capture_output=True, text=True)
        expected = '%d.%d' % sys.version_info[:2]
        if check.stdout.strip() != expected:
            raise RuntimeError('기존 가상환경의 Python이 다릅니다. %s 폴더의 이름을 바꿔 보관한 뒤 다시 실행하세요.' % folder.name)
    requirements = ROOT / ('requirements-dev.txt' if include_tests else 'requirements.txt')
    digest = hashlib.sha256((ROOT/'requirements.txt').read_bytes() + (requirements.read_bytes() if include_tests else b'')).hexdigest()
    marker = folder / ('.ready-tests.json' if include_tests else '.ready.json')
    try:
        ready = json.loads(marker.read_text(encoding='utf-8')).get('requirements_sha256') == digest
    except (OSError, ValueError):
        ready = False
    if not ready or not check_dependencies(python, include_tests):
        print('필요한 패키지를 설치합니다. 최초 설치에는 인터넷이 필요합니다.', flush=True)
        run_command([str(python), '-m', 'pip', 'install', '--upgrade', 'pip'])
        run_command([str(python), '-m', 'pip', 'install', '--prefer-binary', '-r', str(requirements)])
        if not check_dependencies(python, include_tests):
            raise RuntimeError('패키지 설치 확인에 실패했습니다. 위 오류 메시지를 확인하세요.')
        marker.write_text(json.dumps({'requirements_sha256':digest,'python':sys.version}), encoding='utf-8')
    return python


def main(argv=None):
    parser = argparse.ArgumentParser(description='데이터 한눈에 설치 및 실행')
    parser.add_argument('--lan', action='store_true', help='같은 Wi-Fi의 스마트폰 접속 허용')
    parser.add_argument('--port', type=int, default=8501, help='기본 포트 8501')
    parser.add_argument('--setup-only', action='store_true', help='설치만 하고 종료')
    parser.add_argument('--test', action='store_true', help='개발 패키지 설치 후 자동 검사')
    parser.add_argument('--check', action='store_true', help='현재 Python 지원 여부만 확인 (설치하지 않음)')
    args = parser.parse_args(argv)
    if not supported_version(sys.version_info) or platform.python_implementation() != 'CPython' or sys.maxsize <= 2**32:
        print('이 앱은 64비트 CPython 3.9~3.14를 지원합니다. Python 3.9.7은 제외합니다.')
        print('현재 Python:', platform.python_version(), platform.python_implementation())
        return 1
    if not 1024 <= args.port <= 65535:
        print('포트는 1024~65535 사이의 정수로 지정해 주세요.')
        return 1
    print('사용 Python:', platform.python_version(), flush=True)
    if args.check:
        print('지원 범위에 해당합니다. start.py로 설치 및 실행할 수 있습니다.')
        return 0
    try:
        python = prepare_environment(include_tests=args.test)
        if args.test:
            run_command([str(python), '-m', 'pytest', '-q', 'tests'])
            return 0
        if args.setup_only:
            print('설치 완료. 같은 명령에서 --setup-only를 빼면 앱이 실행됩니다.')
            return 0
        address = '0.0.0.0' if args.lan else '127.0.0.1'
        print('브라우저에서 http://localhost:%d 를 여세요.' % args.port, flush=True)
        if args.lan:
            print('스마트폰은 같은 Wi-Fi에서 http://PC의_IP주소:%d 로 접속하세요.' % args.port, flush=True)
        run_command([str(python), '-m', 'streamlit', 'run', 'app.py',
                     '--server.address', address, '--server.port', str(args.port),
                     '--browser.gatherUsageStats', 'false'])
        return 0
    except KeyboardInterrupt:
        print('\n앱을 종료했습니다.')
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('\n준비 또는 실행에 실패했습니다:', str(exc))
        print('인터넷 연결, 디스크 공간, Python 설치 상태를 확인하세요. 기존 자료는 삭제하지 않았습니다.')
        print('Linux에서 venv/ensurepip 오류이면 해당 Python 버전의 venv 패키지를 설치해야 합니다.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
