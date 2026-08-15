"""좌석 조회 오케스트레이션 서비스."""
from app.clients.korean_air_client import AntiBotDetectedError, KoreanAirLoginError
from app.models.schemas import CalendarDay


class ScrapeFailedError(Exception):
    """스크랩 실패 시 라우터로 전달되는 도메인 에러."""

    def __init__(self, message: str, user_message: str = "조회 실패, 다시 시도해주세요") -> None:
        """예외 메시지와 사용자에게 노출할 메시지를 함께 받는다.

        Args:
            message: 내부 로그/디버깅용 상세 메시지.
            user_message: 라우터가 HTTP 응답에 그대로 사용할 사용자 노출 메시지.
        """
        super().__init__(message)
        self.user_message = user_message


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
            raise ScrapeFailedError(
                "봇 탐지로 조회 중단", user_message="잠시 후 다시 시도해주세요"
            ) from exc
        except KoreanAirLoginError:
            pass
        except Exception as exc:  # 파싱 실패, 타임아웃 등 그 외 모든 예외의 최종 안전망
            raise ScrapeFailedError(f"조회 중 알 수 없는 오류: {exc}") from exc

        try:
            return await self._client.fetch_calendar(dep, dest, month)
        except KoreanAirLoginError as exc:
            raise ScrapeFailedError(
                "재시도 후에도 로그인 실패", user_message="대한항공 로그인 실패"
            ) from exc
        except AntiBotDetectedError as exc:
            raise ScrapeFailedError(
                "재시도 중 봇 탐지로 조회 중단", user_message="잠시 후 다시 시도해주세요"
            ) from exc
        except Exception as exc:  # 파싱 실패, 타임아웃 등 그 외 모든 예외의 최종 안전망
            raise ScrapeFailedError(f"재시도 후에도 조회 중 알 수 없는 오류: {exc}") from exc
