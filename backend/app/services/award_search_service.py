"""좌석 조회 오케스트레이션 서비스."""
from app.clients.korean_air_client import AntiBotDetectedError, KoreanAirLoginError
from app.models.schemas import CalendarDay


class ScrapeFailedError(Exception):
    """스크랩 실패 시 라우터로 전달되는 도메인 에러."""


class AwardSearchService:
    """KoreanAirClient를 호출해 캘린더를 조회하고 실패를 도메인 에러로 변환한다."""

    def __init__(self, client) -> None:
        """클라이언트를 주입받는다.

        Args:
            client: `fetch_calendar(dep, dest, month)`를 가진 KoreanAirClient.
        """
        self._client = client

    async def search_calendar(self, dep: str, dest: str, month: str) -> list[CalendarDay]:
        """캘린더를 조회한다. 로그인 실패는 1회 재시도, 봇 탐지는 즉시 중단한다.

        Args:
            dep: 출발 공항 코드.
            dest: 목적지 공항 코드.
            month: 조회월 (YYYY-MM).

        Returns:
            좌석이 있는 날짜만 담긴 CalendarDay 리스트.

        Raises:
            ScrapeFailedError: 재시도까지 실패하거나 봇 탐지가 감지된 경우.
        """
        try:
            return await self._client.fetch_calendar(dep, dest, month)
        except AntiBotDetectedError as exc:
            raise ScrapeFailedError("봇 탐지로 조회 중단") from exc
        except KoreanAirLoginError:
            pass

        try:
            return await self._client.fetch_calendar(dep, dest, month)
        except (KoreanAirLoginError, AntiBotDetectedError) as exc:
            raise ScrapeFailedError("재시도 후에도 조회 실패") from exc
