"""GET /api/routes 계약 테스트 (AwardSearchService는 의존성 오버라이드로 목 처리)."""
from fastapi.testclient import TestClient

from app.main import app
from app.routers.calendar import get_award_search_service

client = TestClient(app)


class _FakeServiceAllHaveSeats:
    async def has_route_in_month(self, dep, dest, month):
        return True


class _FakeServiceNoneHaveSeats:
    async def has_route_in_month(self, dep, dest, month):
        return False


class _FakeServiceOnlyNrt:
    async def has_route_in_month(self, dep, dest, month):
        return dest == "NRT"


def test_get_routes_returns_destinations_with_seats_for_known_airport():
    """ICN으로 조회하면 그 달에 좌석이 있는 목적지만 돌려준다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceAllHaveSeats()
    res = client.get("/api/routes", params={"dep": "ICN", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert any(item["dest"] == "NRT" for item in body)


def test_get_routes_filters_out_destinations_without_seats():
    """그 달에 좌석이 없는 노선은 목록에서 빠진다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceOnlyNrt()
    res = client.get("/api/routes", params={"dep": "ICN", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert all(item["dest"] == "NRT" for item in body)


def test_get_routes_returns_empty_list_when_nothing_has_seats():
    """그 달에 아무 노선도 좌석이 없으면 빈 리스트를 돌려준다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceNoneHaveSeats()
    res = client.get("/api/routes", params={"dep": "ICN", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json() == []


def test_get_routes_returns_empty_list_for_unknown_airport():
    """매핑에 없는 공항 코드는 (조회할 후보 자체가 없어) 빈 리스트를 돌려준다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceAllHaveSeats()
    res = client.get("/api/routes", params={"dep": "XXX", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.json() == []


def test_get_routes_requires_dep_and_month_params():
    """dep, month 파라미터 없이 호출하면 422."""
    res = client.get("/api/routes")
    assert res.status_code == 422
