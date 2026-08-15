"""AwardSearchService 테스트 (KoreanAirClient는 목 처리)."""
from unittest.mock import AsyncMock

import pytest

from app.clients.korean_air_client import AntiBotDetectedError, KoreanAirLoginError
from app.models.schemas import CalendarDay
from app.services.award_search_service import AwardSearchService, ScrapeFailedError


@pytest.mark.asyncio
async def test_search_calendar_returns_client_result_on_success():
    """클라이언트가 성공적으로 반환하면 그대로 리턴한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.return_value = [CalendarDay(date="2026-09-10", flights=[])]
    service = AwardSearchService(client=mock_client)

    result = await service.search_calendar("ICN", "NRT", "2026-09")

    assert result == [CalendarDay(date="2026-09-10", flights=[])]


@pytest.mark.asyncio
async def test_search_calendar_does_not_retry_on_login_error():
    """로그인 실패(사용자가 headed 브라우저에서 제시간에 로그인 못함)는 재시도하지 않는다.

    재시도하면 5분 대기가 배로 늘어나고 브라우저 창이 하나 더 뜨는 혼란만 생긴다.
    """
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = KoreanAirLoginError("로그인 대기 시간 초과")
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError):
        await service.search_calendar("ICN", "NRT", "2026-09")

    assert mock_client.fetch_calendar.call_count == 1


@pytest.mark.asyncio
async def test_search_calendar_does_not_retry_on_anti_bot_detection():
    """봇 탐지 에러는 재시도하지 않고 즉시 ScrapeFailedError로 변환한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = AntiBotDetectedError("탐지됨")
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError):
        await service.search_calendar("ICN", "NRT", "2026-09")

    assert mock_client.fetch_calendar.call_count == 1


@pytest.mark.asyncio
async def test_search_calendar_raises_login_failed_message():
    """로그인 실패 시 사용자 메시지가 '대한항공 로그인 실패'여야 한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = KoreanAirLoginError("로그인 대기 시간 초과")
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError) as exc_info:
        await service.search_calendar("ICN", "NRT", "2026-09")

    assert exc_info.value.user_message == "대한항공 로그인 실패"


@pytest.mark.asyncio
async def test_search_calendar_converts_unexpected_exception_to_default_message():
    """로그인/봇 탐지 외의 예외도 잡아서 기본 사용자 메시지로 변환한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = ValueError("파싱 실패")
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError) as exc_info:
        await service.search_calendar("ICN", "NRT", "2026-09")

    assert exc_info.value.user_message == "조회 실패, 다시 시도해주세요"
