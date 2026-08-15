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
async def test_search_calendar_retries_once_on_login_error():
    """로그인 에러 발생 시 1회 재시도하고, 재시도가 성공하면 결과를 반환한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = [
        KoreanAirLoginError("세션 만료"),
        [CalendarDay(date="2026-09-10", flights=[])],
    ]
    service = AwardSearchService(client=mock_client)

    result = await service.search_calendar("ICN", "NRT", "2026-09")

    assert result == [CalendarDay(date="2026-09-10", flights=[])]
    assert mock_client.fetch_calendar.call_count == 2


@pytest.mark.asyncio
async def test_search_calendar_raises_scrape_failed_after_retry_fails_too():
    """재시도까지 실패하면 ScrapeFailedError로 변환해서 던진다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = [
        KoreanAirLoginError("세션 만료"),
        KoreanAirLoginError("또 실패"),
    ]
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError):
        await service.search_calendar("ICN", "NRT", "2026-09")


@pytest.mark.asyncio
async def test_search_calendar_does_not_retry_on_anti_bot_detection():
    """봇 탐지 에러는 재시도하지 않고 즉시 ScrapeFailedError로 변환한다."""
    mock_client = AsyncMock()
    mock_client.fetch_calendar.side_effect = AntiBotDetectedError("탐지됨")
    service = AwardSearchService(client=mock_client)

    with pytest.raises(ScrapeFailedError):
        await service.search_calendar("ICN", "NRT", "2026-09")

    assert mock_client.fetch_calendar.call_count == 1
