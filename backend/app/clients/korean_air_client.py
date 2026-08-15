"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import time

from playwright.async_api import Browser, Page, async_playwright

from app.models.schemas import CalendarDay, FlightOption, SeatCounts

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"

# Task 3 스파이크 결과로 확정되면 실제 값으로 교체
SELECTOR_ID_INPUT = "input[name=userId]"
SELECTOR_PW_INPUT = "input[name=userPw]"
SELECTOR_LOGIN_SUBMIT = "button[type=submit]"

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
    """대한항공 로그인 세션을 유지하며 마일리지 좌석 정보를 조회하는 클라이언트."""

    def __init__(self, user_id: str, password: str) -> None:
        """자격증명을 받아 클라이언트를 만든다.

        Args:
            user_id: 대한항공 SKYPASS 아이디.
            password: 대한항공 SKYPASS 비밀번호.
        """
        self._user_id = user_id
        self._password = password
        self._session_expires_at: float | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def _is_session_valid(self) -> bool:
        """캐싱된 세션이 아직 TTL 안인지 판단한다."""
        if self._session_expires_at is None:
            return False
        return time.time() < self._session_expires_at

    async def ensure_logged_in(self) -> None:
        """세션이 없거나 만료됐으면 로그인하고, 유효하면 아무것도 하지 않는다.

        Raises:
            KoreanAirLoginError: 로그인 실패.
            AntiBotDetectedError: 로그인 과정에서 캡차/봇 탐지가 감지된 경우.
        """
        if self._is_session_valid():
            return

        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=True)
            self._page = await self._browser.new_page()

        assert self._page is not None

        try:
            await self._page.goto(LOGIN_URL)

            if await self._page.locator("text=자동입력 방지").count() > 0:
                raise AntiBotDetectedError("로그인 페이지에서 봇 탐지 감지")

            await self._page.fill(SELECTOR_ID_INPUT, self._user_id)
            await self._page.fill(SELECTOR_PW_INPUT, self._password)
            await self._page.click(SELECTOR_LOGIN_SUBMIT)

            try:
                await self._page.wait_for_selector("text=로그아웃", timeout=10_000)
            except Exception as exc:
                raise KoreanAirLoginError("로그인 실패: 자격증명 또는 페이지 구조 확인 필요") from exc
        except (AntiBotDetectedError, KoreanAirLoginError):
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
