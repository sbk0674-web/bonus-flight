"""GET/POST /api/settings 계약 테스트."""
from fastapi.testclient import TestClient

import app.services.credentials_store as credentials_store
from app.main import app

client = TestClient(app)


def test_get_settings_returns_not_configured_when_nothing_set(tmp_path, monkeypatch):
    """설정 안 된 상태면 configured=false."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")
    monkeypatch.delenv("KOREANAIR_ID", raising=False)
    monkeypatch.delenv("KOREANAIR_PW", raising=False)

    res = client.get("/api/settings")

    assert res.status_code == 200
    assert res.json() == {"configured": False, "koreanair_id": None}


def test_post_settings_saves_and_get_reflects_it(tmp_path, monkeypatch):
    """저장 후 조회하면 configured=true, 아이디는 보이고 비밀번호는 응답에 없다."""
    monkeypatch.setattr(credentials_store, "CREDENTIALS_PATH", tmp_path / "credentials.json")

    post_res = client.post(
        "/api/settings", json={"koreanair_id": "myid", "koreanair_pw": "mypw"}
    )
    assert post_res.status_code == 200
    assert "koreanair_pw" not in post_res.json()

    get_res = client.get("/api/settings")
    assert get_res.json() == {"configured": True, "koreanair_id": "myid"}
