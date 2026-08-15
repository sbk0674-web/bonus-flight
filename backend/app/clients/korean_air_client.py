"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import asyncio
import os
import time
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

from app.models.schemas import CalendarDay, FlightOption, SeatCounts

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"
GOTO_TIMEOUT_MS = 30 * 1000

# 설정돼 있으면 매번 새 브라우저를 띄우는 대신 이미 떠 있는 브라우저(예: 사용자가
# 평소 쓰는 웨일/크롬을 --remote-debugging-port로 띄운 것)에 CDP로 붙는다.
# 이미 로그인돼 있는 브라우저면 매번 로그인할 필요가 없다.
CDP_ENDPOINT = os.environ.get("KOREANAIR_CDP_ENDPOINT")

# 로그인 성공 여부 판단: 로그인 전 헤더에는 "로그인" 버튼이 정확히 이 텍스트로
# 떠 있다 (실사로 확인됨, 2026-08-15 스크린샷). 로그인하면 이 버튼이 사라지므로
# "로그인" 텍스트가 없어지는 시점을 로그인 완료로 간주한다.
LOGIN_BUTTON_TEXT = "로그인"
LOGIN_WAIT_TIMEOUT_MS = 5 * 60 * 1000  # 사용자가 직접 로그인할 시간 (5분)

DEBUG_DUMP_DIR = Path(__file__).parent.parent.parent / "tmp"


async def _dump_debug_state(page: Page, label: str) -> None:
    """실패 시점의 페이지 상태를 tmp/에 덤프한다 (원인 진단용, 실패해도 무시)."""
    try:
        DEBUG_DUMP_DIR.mkdir(exist_ok=True)
        await page.screenshot(path=str(DEBUG_DUMP_DIR / f"{label}.png"))
        (DEBUG_DUMP_DIR / f"{label}.html").write_text(await page.content(), encoding="utf-8")
        (DEBUG_DUMP_DIR / f"{label}_url.txt").write_text(page.url, encoding="utf-8")
    except Exception:
        pass

CALENDAR_API_PATH = "/api/hmp/bonusSeatView/bonusSeatView"

# 실사로 확인된 실제 응답 구조 (2026-08-15, 로그인된 웨일 브라우저 CDP로 확인):
#   POST body: {"departureAirport": "PUS", "arrivalAirport": "NRT", "departureDate": "20261001"}
#   (departureDate는 조회하려는 달의 1일, YYYYMMDD. 응답은 그 달 전체를 돌려준다)
#   응답: {"flightList": [{"departureDate": "20261001",
#           "flightDetailList": [{"departureTime": "07:55", "flightNumber": "KE5083",
#             "availableSeat": true, "bookingClass": "X", "frontBookingClass": "E"}, ...]}]}
# 대한항공은 등급별 정확한 잔여석 "개수"를 안 주고 availableSeat true/false(있다/없다)만
# 준다. 도착시간(arrTime)도 이 API엔 없다. 그래서 SeatCounts의 값은 실제로는
# "있으면 1, 없으면 0"이고, arr_time은 항상 빈 문자열이다.
FRONT_CLASS_TO_SEAT_FIELD = {"E": "economy", "P": "business", "U": "first"}


def parse_calendar_response(raw: dict) -> list[CalendarDay]:
    """대한항공 bonusSeatView 원시 응답을 CalendarDay 리스트로 변환한다.

    같은 편(편명+출발시간)에 등급(E/P/U)별로 한 줄씩 내려오므로 편 단위로 묶고,
    좌석이 하나도 없는 편/날짜는 제외한다.

    Args:
        raw: bonusSeatView API 응답 dict (flightList -> flightDetailList 구조).

    Returns:
        좌석이 있는 날짜만 담긴 CalendarDay 리스트.
    """
    result: list[CalendarDay] = []
    for day in raw.get("flightList", []):
        flights_by_key: dict[tuple[str, str], dict[str, int]] = {}
        for detail in day.get("flightDetailList", []):
            field = FRONT_CLASS_TO_SEAT_FIELD.get(detail.get("frontBookingClass"))
            if field is None or not detail.get("availableSeat"):
                continue
            key = (detail["flightNumber"], detail["departureTime"])
            seats = flights_by_key.setdefault(key, {"economy": 0, "business": 0, "first": 0})
            seats[field] = 1

        if not flights_by_key:
            continue

        flights = [
            FlightOption(
                flight_no=flight_no,
                dep_time=dep_time,
                arr_time="",
                seats=SeatCounts(**seats),
            )
            for (flight_no, dep_time), seats in flights_by_key.items()
        ]
        raw_date = day["departureDate"]
        date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        result.append(CalendarDay(date=date, flights=flights))
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
        # 브라우저/페이지 하나를 여러 요청이 동시에 공유하므로, 겹치는 요청이
        # 서로의 페이지 상태를 오염시키지 않도록 한 번에 하나씩만 처리한다.
        self._lock = asyncio.Lock()

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
            if CDP_ENDPOINT:
                self._browser = await playwright.chromium.connect_over_cdp(CDP_ENDPOINT)
                context = self._browser.contexts[0] if self._browser.contexts else (
                    await self._browser.new_context()
                )
                self._page = await context.new_page()
            else:
                self._browser = await playwright.chromium.launch(headless=False)
                self._page = await self._browser.new_page()

        assert self._page is not None

        try:
            await self._page.goto(LOGIN_URL, timeout=GOTO_TIMEOUT_MS)

            # Angular SPA라 헤더가 늦게 하이드레이션된다. 로그인 버튼 유무를
            # 판단하기 전에 항상 뜨는 요소(마일리지 예매 토글)로 렌더 완료를 기다린다.
            await self._page.wait_for_selector("text=마일리지 예매", timeout=GOTO_TIMEOUT_MS)

            # 쿠키 동의 배너가 로그인 버튼을 가리는 경우가 있어 자동으로 닫는다.
            try:
                await self._page.get_by_text("동의합니다", exact=True).click(timeout=5_000)
            except Exception:
                pass

            login_button = self._page.get_by_text(LOGIN_BUTTON_TEXT, exact=True)
            if await login_button.count() == 0:
                # 이미 로그인 버튼이 안 보임 = 이미 로그인된 상태
                self._session_expires_at = time.time() + SESSION_TTL_SECONDS
                return

            try:
                await login_button.first.wait_for(state="detached", timeout=LOGIN_WAIT_TIMEOUT_MS)
            except Exception as exc:
                await _dump_debug_state(self._page, "login_timeout")
                raise KoreanAirLoginError(
                    "로그인 대기 시간 초과: 뜬 브라우저 창에서 직접 로그인해주세요"
                ) from exc
        except Exception:
            # 어떤 이유로든 로그인이 실패하면 원인 진단을 위해 그 시점 상태를 덤프하고,
            # 브라우저/페이지를 오염된 상태로 남겨두지 않는다. 다음 ensure_logged_in()
            # 호출(예: 서비스 레이어의 재시도)이 완전히 새로운 브라우저로 시작하도록
            # 내부 상태를 초기화한다.
            if self._page is not None:
                await _dump_debug_state(self._page, "ensure_logged_in_failure")
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
        async with self._lock:
            await self.ensure_logged_in()
            assert self._page is not None

            year, mon = month.split("-")
            departure_date = f"{year}{mon}01"  # bonusSeatView는 그 달 1일 기준으로 한 달치를 돌려줌
            response = await self._page.request.post(
                f"https://www.koreanair.com{CALENDAR_API_PATH}",
                data={
                    "departureAirport": dep,
                    "arrivalAirport": dest,
                    "departureDate": departure_date,
                },
            )
            if response.status == 403:
                raise AntiBotDetectedError("캘린더 조회 중 봇 탐지 감지")

            raw = await response.json()
            return parse_calendar_response(raw)

    async def close(self) -> None:
        """브라우저(또는 CDP 모드에서는 우리가 연 탭)를 정리한다.

        CDP로 기존 브라우저(사용자의 웨일 등)에 붙은 경우, browser.close()를
        부르면 사용자의 다른 탭까지 전부 닫힐 위험이 있다. CDP 모드에서는
        우리가 새로 연 탭(self._page)만 닫고 브라우저 연결은 그대로 둔다.
        """
        if CDP_ENDPOINT:
            if self._page is not None:
                await self._page.close()
            self._browser = None
            return

        if self._browser is not None:
            await self._browser.close()
            self._browser = None
