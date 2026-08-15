"""credentials_store 테스트. 실제 파일 대신 monkeypatch로 임시 경로를 쓴다."""
import app.services.credentials_store as credentials_store
from app.services.credentials_store import get_credentials, save_credentials


def test_get_credentials_returns_none_when_nothing_set(tmp_path, monkeypatch):
    """파일도 없고 환경변수도 없으면 None을 반환한다."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")
    monkeypatch.delenv("KOREANAIR_ID", raising=False)
    monkeypatch.delenv("KOREANAIR_PW", raising=False)

    assert get_credentials() is None


def test_save_then_get_credentials_roundtrips(tmp_path, monkeypatch):
    """저장한 자격증명을 그대로 다시 읽을 수 있다."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")

    save_credentials("myid", "mypw")

    assert get_credentials() == ("myid", "mypw")


def test_file_takes_priority_over_env_vars(tmp_path, monkeypatch):
    """파일이 있으면 환경변수보다 파일 값을 우선한다."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")
    monkeypatch.setenv("KOREANAIR_ID", "env_id")
    monkeypatch.setenv("KOREANAIR_PW", "env_pw")
    save_credentials("file_id", "file_pw")

    assert get_credentials() == ("file_id", "file_pw")


def test_falls_back_to_env_vars_when_no_file(tmp_path, monkeypatch):
    """파일이 없으면 환경변수를 사용한다."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")
    monkeypatch.setenv("KOREANAIR_ID", "env_id")
    monkeypatch.setenv("KOREANAIR_PW", "env_pw")

    assert get_credentials() == ("env_id", "env_pw")
