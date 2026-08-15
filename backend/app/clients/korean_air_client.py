"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import asyncio
import time
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

from app.models.schemas import CalendarDay, FlightOption, SeatCounts

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"
GOTO_TIMEOUT_MS = 30 * 1000

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
