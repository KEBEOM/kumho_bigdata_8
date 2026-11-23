"""실행기의 버전 판별과 격리 규칙을 확인한다. 테스트 자체는 설치를 하지 않는다."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import start


@pytest.mark.parametrize('version',[(3,9,25),(3,10,22),(3,11,18),(3,12,14),(3,13,5),(3,14,10)])
def test_supported_versions(version):
    assert start.supported_version(version)


@pytest.mark.parametrize('version',[(2,7,18),(3,8,20),(3,9,7),(3,15,0),(4,0,0)])
def test_unsupported_versions(version):
    assert not start.supported_version(version)


def test_clean_environment(monkeypatch):
    monkeypatch.setenv('PYTHONPATH','/unrelated/packages')
    monkeypatch.setenv('PYTHONHOME','/unrelated/runtime')
    env=start.clean_environment()
    assert 'PYTHONPATH' not in env and 'PYTHONHOME' not in env
    assert env['PYTHONNOUSERSITE']=='1' and env['PYTHONUTF8']=='1'


def test_check_does_not_install(monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('버전 확인은 환경을 만들면 안 됩니다.')
    monkeypatch.setattr(start,'prepare_environment',forbidden)
    assert start.main(['--check'])==0


@pytest.mark.parametrize('port',['80','65536'])
def test_invalid_port_does_not_install(monkeypatch,port):
    def forbidden(*args,**kwargs):
        raise AssertionError('잘못된 포트는 환경을 만들면 안 됩니다.')
    monkeypatch.setattr(start,'prepare_environment',forbidden)
    assert start.main(['--port',port])==1
