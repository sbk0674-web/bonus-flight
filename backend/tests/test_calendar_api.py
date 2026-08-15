"""POST /api/calendar 계약 테스트 (AwardSearchService는 의존성 오버라이드로 목 처리)."""
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import CalendarDay, FlightOption, SeatCounts
from app.routers.calendar import get_award_search_service
from app.services.award_search_service import ScrapeFailedError

client = TestClient(app)


class _FakeServiceOk:
    async def search_calendar(self, dep, dest, month):
        return [
            CalendarDay(
                date="2026-09-10",
                flights=[
                    FlightOption(
                        flight_no="KE001",
                        dep_time="09:00",
                        arr_time="12:00",
                        seats=SeatCounts(economy=2, business=1, first=0),
                    )
                ],
            )
        ]


class _FakeServiceFail:
    async def search_calendar(self, dep, dest, month):
        raise ScrapeFailedError("조회 실패")


def test_post_calendar_returns_days_on_success():
    """정상 조회 시 CalendarDay 리스트를 그대로 반환한다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceOk()
    res = client.post("/api/calendar", json={"dep": "ICN", "dest": "NRT", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert body[0]["date"] == "2026-09-10"
    flight = body[0]["flights"][0]
    assert flight["flight_no"] == "KE001"
    assert flight["dep_time"] == "09:00"
    assert flight["arr_time"] == "12:00"
    assert flight["seats"]["economy"] == 2
    assert flight["seats"]["business"] == 1
    assert flight["seats"]["first"] == 0


def test_post_calendar_returns_502_on_scrape_failure():
    """스크랩 실패 시 502와 에러 메시지를 반환한다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceFail()
    res = client.post("/api/calendar", json={"dep": "ICN", "dest": "NRT", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 502
    assert "조회 실패" in res.json()["detail"]


def test_post_calendar_validates_request_body():
    """필수 필드 없이 호출하면 422."""
    res = client.post("/api/calendar", json={"dep": "ICN"})
    assert res.status_code == 422
