"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import time

from playwright.async_api import Browser, Page, async_playwright

from app.models.schemas import CalendarDay, FlightOption, SeatCounts

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"

# 로그인 성공 여부를 판단하는 마커. 대한항공은 네이버 등 소셜 로그인도 지원해서
# 아이디/비번 자동입력 대신 사용자가 브라우저에서 직접 로그인하고, 이 마커가
# 뜨면 로그인 완료로 간주한다. Task 3 스파이크 결과로 확정되면 실제 값으로 교체.
LOGIN_SUCCESS_MARKER = "text=로그아웃"
LOGIN_WAIT_TIMEOUT_MS = 5 * 60 * 1000  # 사용자가 직접 로그인할 시간 (5분)

CALENDAR_API_PATH = "/api/booking/award-calendar"  # Task 3 스파이크 결과로 확정 필요


def parse_calendar_response(raw: dict) -> list[CalendarDay]:
    """대한항공 캘린더 원시 응답을 CalendarDay 리스트로 변환한다.

    좌석이 전부 0인 편은 제외하고, 그 결과 편이 하나도 안 남는 날짜도 제외한다.

    Args:
        raw: 대한항공 API/HTML 파싱 결과 dict (days -> flights 구조).

    Returns:
        좌석이 있는 날짜만 담긴 CalendarDay 리스트.
    """
    result: list[CalendarDay] = []
    for day in raw.get("days", []):
        available_flights = [
            FlightOption(
                flight_no=f["flightNo"],
                dep_time=f["depTime"],
                arr_time=f["arrTime"],
                seats=SeatCounts(
                    economy=f["economySeats"],
                    business=f["businessSeats"],
                    first=f["firstSeats"],
                ),
            )
            for f in day.get("flights", [])
            if f["economySeats"] > 0 or f["businessSeats"] > 0 or f["firstSeats"] > 0
        ]
        if available_flights:
            result.append(CalendarDay(date=day["date"], flights=available_flights))
    return result


class KoreanAirLoginError(Exception):
    """로그인 실패 시 발생 (자격증명 오류, 정책 변경 등)."""


class AntiBotDetectedError(Exception):
    """캡차/봇 탐지 시 발생. 재시도하지 않고 즉시 상위로 전파해야 한다."""


class KoreanAirClient:
    """대한항공 로그인 세션을 유지하며 마일리지 좌석 정보를 조회하는 클라이언트.

    대한항공은 네이버 등 소셜 로그인을 지원하므로 아이디/비번을 저장해
    자동입력하지 않는다. 대신 headed(화면 보이는) 브라우저를 띄우고, 사용자가
    직접 로그인을 완료할 때까지 기다린다.
    """

    def __init__(self) -> None:
        """자격증명 없이 클라이언트를 만든다 (로그인은 매번 사용자가 직접 진행)."""
        self._session_expires_at: float | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def _is_session_valid(self) -> bool:
        """캐싱된 세션이 아직 TTL 안인지 판단한다."""
        if self._session_expires_at is None:
            return False
        return time.time() < self._session_expires_at

    async def ensure_logged_in(self) -> None:
        """세션이 없거나 만료됐으면 브라우저를 띄우고 사용자의 직접 로그인을 기다린다.

        유효한 세션이 있으면 아무것도 하지 않는다.

        Raises:
            KoreanAirLoginError: 로그인 대기 시간(5분) 안에 로그인이 완료되지 않은 경우.
        """
        if self._is_session_valid():
            return

        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=False)
            self._page = await self._browser.new_page()

        assert self._page is not None

        try:
            await self._page.goto(LOGIN_URL)

            if await self._page.locator(LOGIN_SUCCESS_MARKER).count() > 0:
                self._session_expires_at = time.time() + SESSION_TTL_SECONDS
                return

            try:
                await self._page.wait_for_selector(
                    LOGIN_SUCCESS_MARKER, timeout=LOGIN_WAIT_TIMEOUT_MS
                )
            except Exception as exc:
                raise KoreanAirLoginError(
                    "로그인 대기 시간 초과: 뜬 브라우저 창에서 직접 로그인해주세요"
                ) from exc
        except KoreanAirLoginError:
            # 로그인 실패 시 브라우저/페이지를 오염된 상태로 남겨두지 않는다.
            # 다음 ensure_logged_in() 호출(예: 서비스 레이어의 재시도)이
            # 완전히 새로운 브라우저로 시작하도록 내부 상태를 초기화한다.
            await self.close()
            self._page = None
            raise

        self._session_expires_at = time.time() + SESSION_TTL_SECONDS

    async def fetch_calendar(self, dep: str, dest: str, month: str) -> list[CalendarDay]:
        """출발지/목적지/월 기준 좌석 있는 날짜만 캘린더로 반환한다.

        Args:
            dep: 출발 공항 코드.
            dest: 목적지 공항 코드.
            month: 조회월 (YYYY-MM).

        Returns:
            좌석이 있는 날짜만 담긴 CalendarDay 리스트.

        Raises:
            AntiBotDetectedError: 조회 중 봇 탐지 감지 시.
        """
        await self.ensure_logged_in()
        assert self._page is not None

        response = await self._page.request.get(
            CALENDAR_API_PATH,
            params={"dep": dep, "dest": dest, "month": month},
        )
        if response.status == 403:
            raise AntiBotDetectedError("캘린더 조회 중 봇 탐지 감지")

        raw = await response.json()
        return parse_calendar_response(raw)

    async def close(self) -> None:
        """브라우저를 종료한다."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
