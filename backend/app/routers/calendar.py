"""좌석 캘린더 조회 라우터."""
from fastapi import APIRouter, Depends, HTTPException

from app.clients.korean_air_client import KoreanAirClient
from app.models.schemas import CalendarDay, CalendarRequest
from app.services.award_search_service import AwardSearchService, ScrapeFailedError

router = APIRouter()

_client_singleton: KoreanAirClient | None = None


def get_award_search_service() -> AwardSearchService:
    """AwardSearchService를 만든다. 클라이언트는 프로세스 내에서 재사용한다.

    첫 조회 시 headed 브라우저가 뜨고, 사용자가 직접 대한항공에 로그인해야 한다.
    """
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = KoreanAirClient()
    return AwardSearchService(client=_client_singleton)


@router.post("/api/calendar", response_model=list[CalendarDay])
async def search_calendar(
    body: CalendarRequest,
    service: AwardSearchService = Depends(get_award_search_service),
) -> list[CalendarDay]:
    """출발지/목적지/월 기준 좌석이 있는 날짜만 캘린더로 반환한다 (라이브 스크랩)."""
    try:
        return await service.search_calendar(body.dep, body.dest, body.month)
    except ScrapeFailedError as exc:
        raise HTTPException(status_code=502, detail=exc.user_message) from exc
