"""GET /api/routes 계약 테스트."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_routes_returns_destinations_for_known_airport():
    """ICN으로 조회하면 매핑된 목적지 목록을 돌려준다."""
    res = client.get("/api/routes", params={"dep": "ICN", "month": "2026-09"})
    assert res.status_code == 200
    body = res.json()
    assert any(item["dest"] == "NRT" for item in body)


def test_get_routes_returns_empty_list_for_unknown_airport():
    """매핑에 없는 공항 코드는 빈 리스트를 돌려준다."""
    res = client.get("/api/routes", params={"dep": "XXX", "month": "2026-09"})
    assert res.status_code == 200
    assert res.json() == []


def test_get_routes_requires_dep_and_month_params():
    """dep, month 파라미터 없이 호출하면 422."""
    res = client.get("/api/routes")
    assert res.status_code == 422
