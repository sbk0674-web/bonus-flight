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
        """캘린더를 조회한다.

        로그인은 사용자가 headed 브라우저에서 직접 진행하므로 여기서 자동
        재시도하지 않는다 (재시도하면 대기 시간이 배로 늘어나고 브라우저 창이
        하나 더 뜨는 혼란만 생긴다). 실패하면 사용자가 프론트에서 직접
        "조회"를 다시 눌러 새로 시도한다.

        Args:
            dep: 출발 공항 코드.
            dest: 목적지 공항 코드.
            month: 조회월 (YYYY-MM).

        Returns:
            좌석이 있는 날짜만 담긴 CalendarDay 리스트.

        Raises:
            ScrapeFailedError: 조회 실패 시.
        """
        try:
            return await self._client.fetch_calendar(dep, dest, month)
        except AntiBotDetectedError as exc:
            raise ScrapeFailedError(
                "봇 탐지로 조회 중단", user_message="잠시 후 다시 시도해주세요"
            ) from exc
        except KoreanAirLoginError as exc:
            raise ScrapeFailedError(
                "로그인 대기 시간 초과", user_message="대한항공 로그인 실패"
            ) from exc
        except Exception as exc:  # 파싱 실패, 타임아웃 등 그 외 모든 예외의 최종 안전망
            print(f"[AwardSearchService] 알 수 없는 오류: {type(exc).__name__}: {exc}", flush=True)
            raise ScrapeFailedError(f"조회 중 알 수 없는 오류: {exc}") from exc

    async def has_route_in_month(self, dep: str, dest: str, month: str) -> bool:
        """노선 목록 화면에서 그 달에 실제 좌석이 있는 노선만 거를 때 쓴다."""
        return await self._client.has_route_in_month(dep, dest, month)

    async def search_award_price(
        self,
        dep: str,
        dest: str,
        outbound_date: str,
        outbound_flight_no: str,
        inbound_date: str,
        inbound_flight_no: str,
    ) -> dict | None:
        """왕복 최종 선택 시점의 소요 마일리지/운임을 조회한다.

        부가 정보라 실패해도 예외를 던지지 않고 None을 반환한다 (라우터가 204로 처리).
        """
        try:
            return await self._client.fetch_award_price(
                dep, dest, outbound_date, outbound_flight_no, inbound_date, inbound_flight_no
            )
        except Exception as exc:
            print(f"[AwardSearchService] 마일리지 조회 실패: {type(exc).__name__}: {exc}", flush=True)
            return None
