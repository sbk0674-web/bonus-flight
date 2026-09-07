"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import asyncio
import copy
import datetime
import json
import os
import time
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

from app.models.schemas import CalendarDay, FlightOption, SeatCounts

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"
GOTO_TIMEOUT_MS = 30 * 1000

# CDP 연결이 살아있는지 가볍게 찔러볼 때 쓰는 타임아웃과, 완전히 새로 붙을 때
# 쓰는 타임아웃. 웨일의 디버그 서버 자체가 죽어있으면 이 시간 안에 실패로
# 확정하고 위로 에러를 던진다 (기본 180초까지 무한정 매달리는 걸 막음).
CONNECTION_LIVENESS_TIMEOUT_SECONDS = 5
CDP_CONNECT_TIMEOUT_SECONDS = 15
NETWORK_CALL_TIMEOUT_SECONDS = 30

# bonusSeatView는 대한항공 쪽에서 하루 1회만 갱신되는 데이터라, 우리 쪽에서도 같은
# 주기로 캐싱하면 방문자가 몇 명이든 대한항공에 나가는 실제 요청 수는 늘지 않는다.
CALENDAR_CACHE_TTL_SECONDS = 24 * 60 * 60
# scheduleAvailability는 진짜 실시간이라 짧게만 캐싱한다 (신선도와 트래픽 절감의 절충).
EXACT_SEATS_CACHE_TTL_SECONDS = 20 * 60

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

# 정확한 좌석수용 API. bonusSeatView와 달리 실제 예약 검색 잡(job)이라 "이 날짜,
# 이 등급"만 딱 집어서 물어봐야 한다 (한 달 전체를 한 번에 안 줌). 그래서
# bonusSeatView로 먼저 "좌석 있을 법한 날짜/등급"만 걸러낸 뒤, 그 조합에만 이
# API를 호출해 정확한 좌석수와 실제 운항사(코드셰어 포함)를 덧붙인다.
# 실사로 확인된 응답 구조 (2026-08-16):
#   POST body: {"award": true, "sta": false, "segmentList": [{"departureDate": "20260901",
#     "departureAirport": "PUS", "arrivalAirport": "DAD"}],
#     "travelers": [{"travellerType": "ADT", "lastName": ..., "firstName": ...}],
#     "cabinType": "ECONOMY"}
#   응답: {"boundFlightList": [{"flightInfoList": [{"segmentList": [{"carrierCode": "KE",
#     "flightNumber": "5771", "operationCarrierCode": "LJ", "operationCarrierName": "Jin Air",
#     "codeShare": true, "departureDateTime": "20260829211500",
#     "cabinClassList": [{"cabinClass": "R", "cabinSeatCount": 7, ...}], ...}]}]}]}
SCHEDULE_AVAILABILITY_API_PATH = "/api/ap/long-running/booking/avail/scheduleAvailability"
LOGIN_USER_INFO_API_PATH = "/api/li/auth/loginUserInfo"
CABIN_FIELD_TO_API_TYPE = {"economy": "ECONOMY", "business": "PRESTIGE", "first": "FIRST"}


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
        # scheduleAvailability 호출에 필요한 여행자 이름. 세션 중 메모리에만
        # 캐싱하고 디스크/로그에는 절대 쓰지 않는다 (실명 PII).
        self._traveler_last_name: str | None = None
        self._traveler_first_name: str | None = None
        # (dep, dest, month) -> (캐싱 시각, bonusSeatView 파싱 결과)
        self._calendar_cache: dict[tuple[str, str, str], tuple[float, list[CalendarDay]]] = {}
        # (dep, dest, date_yyyymmdd, cabin_type) -> (캐싱 시각, scheduleAvailability 결과)
        self._exact_seats_cache: dict[tuple[str, str, str, str], tuple[float, list[dict]]] = {}

    def _is_session_valid(self) -> bool:
        """캐싱된 세션이 아직 TTL 안인지 판단한다."""
        if self._session_expires_at is None:
            return False
        return time.time() < self._session_expires_at

    async def _reconnect_if_connection_dead(self) -> None:
        """CDP 연결이 좀비 상태(응답 없음)가 됐으면 감지해서 상태를 리셋한다.

        웨일 브라우저를 재시작하지 않는 한 이번 페이지 객체는 계속 죽어있으므로,
        여기서 상태를 비워두면 바로 아래 ensure_logged_in의 재연결 분기가 새
        connect_over_cdp를 시도한다. 가벼운 evaluate 하나로 살아있는지만 본다.
        """
        if self._page is None:
            return
        try:
            await asyncio.wait_for(self._page.evaluate("1"), timeout=CONNECTION_LIVENESS_TIMEOUT_SECONDS)
        except Exception:
            print("[KoreanAirClient] CDP 연결 죽음 감지, 재연결 준비", flush=True)
            self._browser = None
            self._page = None
            self._session_expires_at = None

    async def ensure_logged_in(self) -> None:
        """세션이 없거나 만료됐으면 브라우저를 띄우고 사용자의 직접 로그인을 기다린다.

        유효한 세션이 있으면 아무것도 하지 않는다. 단, 세션은 유효해 보여도
        실제 CDP 연결이 죽어있을 수 있어 먼저 살아있는지 확인한다.

        Raises:
            KoreanAirLoginError: 로그인 대기 시간(5분) 안에 로그인이 완료되지 않은 경우.
        """
        await self._reconnect_if_connection_dead()

        if self._is_session_valid():
            return

        if self._browser is None:
            playwright = await async_playwright().start()
            if CDP_ENDPOINT:
                try:
                    self._browser = await asyncio.wait_for(
                        playwright.chromium.connect_over_cdp(CDP_ENDPOINT),
                        timeout=CDP_CONNECT_TIMEOUT_SECONDS,
                    )
                except asyncio.TimeoutError as exc:
                    raise KoreanAirLoginError(
                        "웨일 브라우저 디버그 연결에 실패했습니다 — 브라우저를 재시작해야 할 수 있습니다"
                    ) from exc
                context = self._browser.contexts[0] if self._browser.contexts else (
                    await self._browser.new_context()
                )
                # 재연결마다 새 탭을 만들면 그때마다 브라우저 창 포커스를 뺏어가서
                # 사용자 작업을 방해한다 — 기존에 열려있던 대한항공 탭이 있으면
                # 그걸 재사용하고, 없을 때만 새로 연다.
                existing = next(
                    (pg for pg in context.pages if "koreanair.com" in pg.url), None
                )
                self._page = existing if existing is not None else await context.new_page()
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
        days = await self._fetch_bonus_seatview_cached(dep, dest, month)

        async with self._lock:
            await self.ensure_logged_in()
            await self._enrich_with_exact_seats(dep, dest, days)
        return days

    async def _fetch_bonus_seatview_cached(self, dep: str, dest: str, month: str) -> list[CalendarDay]:
        """bonusSeatView 원시 결과(등급별 있다/없다만)를 캐싱해서 반환한다.

        fetch_calendar(정확한 좌석수까지 채움)와 has_route_in_month(존재 여부만
        필요) 둘 다 여기서 같은 캐시를 공유한다.
        """
        cache_key = (dep, dest, month)
        cached = self._calendar_cache.get(cache_key)
        if cached is not None and time.time() - cached[0] < CALENDAR_CACHE_TTL_SECONDS:
            return copy.deepcopy(cached[1])

        async with self._lock:
            await self.ensure_logged_in()
            assert self._page is not None

            year, mon = month.split("-")
            departure_date = f"{year}{mon}01"  # bonusSeatView는 그 달 1일 기준으로 한 달치를 돌려줌
            response = await asyncio.wait_for(
                self._page.request.post(
                    f"https://www.koreanair.com{CALENDAR_API_PATH}",
                    data={
                        "departureAirport": dep,
                        "arrivalAirport": dest,
                        "departureDate": departure_date,
                    },
                ),
                timeout=NETWORK_CALL_TIMEOUT_SECONDS,
            )
            if response.status == 403:
                raise AntiBotDetectedError("캘린더 조회 중 봇 탐지 감지")

            raw = await response.json()
            days = parse_calendar_response(raw)
            self._calendar_cache[cache_key] = (time.time(), copy.deepcopy(days))
            return days

    async def has_route_in_month(self, dep: str, dest: str, month: str) -> bool:
        """해당 노선에 그 달에 좌석이 있는 날짜가 하나라도 있는지만 가볍게 확인한다.

        정확한 좌석수(scheduleAvailability) 조회는 건너뛰어서 노선 목록 화면처럼
        여러 목적지를 한 번에 훑을 때도 빠르다. bonusSeatView 캐시를 그대로 쓴다.
        """
        try:
            days = await self._fetch_bonus_seatview_cached(dep, dest, month)
        except Exception:
            return True  # 조회 실패 시 걸러내지 않고 목록에 남긴다 (안전한 쪽으로)
        return len(days) > 0

    async def _traveler_name(self) -> tuple[str, str]:
        """scheduleAvailability에 넣을 여행자 이름을 조회해 메모리에 캐싱한다.

        Returns:
            (성, 이름) 튜플. 세션 동안 재사용하고 파일에는 절대 쓰지 않는다.
        """
        if self._traveler_last_name is None:
            assert self._page is not None
            response = await self._page.request.get(
                f"https://www.koreanair.com{LOGIN_USER_INFO_API_PATH}"
            )
            info = await response.json()
            self._traveler_last_name = info.get("englishLastName") or ""
            self._traveler_first_name = info.get("englishFirstName") or ""
        return self._traveler_last_name, self._traveler_first_name

    async def _fetch_exact_seats(
        self, dep: str, dest: str, date_yyyymmdd: str, cabin_type: str
    ) -> list[dict]:
        """특정 날짜/등급의 정확한 좌석수와 실제 운항사를 scheduleAvailability로 조회한다.

        직항편만 남기고(경유편은 이 앱 스코프 밖), 편명/출발시각을
        bonusSeatView 쪽과 맞출 수 있는 키로 반환한다.

        Args:
            dep: 출발 공항 코드.
            dest: 목적지 공항 코드.
            date_yyyymmdd: 조회 날짜 (YYYYMMDD).
            cabin_type: "ECONOMY" | "PRESTIGE" | "FIRST".

        Returns:
            {"flight_no", "dep_time", "seat_count", "operator_code",
             "operator_name", "code_share"} 딕셔너리 리스트.
        """
        assert self._page is not None
        last_name, first_name = await self._traveler_name()
        payload = {
            "award": True,
            "currency": "",
            "sta": False,
            "segmentList": [
                {"departureDate": date_yyyymmdd, "departureAirport": dep, "arrivalAirport": dest}
            ],
            "travelers": [
                {"travellerType": "ADT", "lastName": last_name, "firstName": first_name, "discountCode": ""}
            ],
            "cabinType": cabin_type,
        }
        response = await asyncio.wait_for(
            self._page.request.post(
                f"https://www.koreanair.com{SCHEDULE_AVAILABILITY_API_PATH}",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            ),
            timeout=NETWORK_CALL_TIMEOUT_SECONDS,
        )
        body = await response.json()

        results: list[dict] = []
        for bound in body.get("boundFlightList", []):
            for flight in bound.get("flightInfoList", []):
                segments = flight.get("segmentList", [])
                if len(segments) != 1:
                    continue  # 경유편 제외, 직항만
                seg = segments[0]
                cabin_list = seg.get("cabinClassList", [])
                if not cabin_list:
                    continue
                seat_count = max((c.get("cabinSeatCount", 0) for c in cabin_list), default=0)
                dep_dt = seg.get("departureDateTime", "")
                results.append(
                    {
                        "flight_no": f"{seg.get('carrierCode', '')}{seg.get('flightNumber', '')}",
                        "dep_time": f"{dep_dt[8:10]}:{dep_dt[10:12]}" if len(dep_dt) >= 12 else "",
                        "seat_count": seat_count,
                        "operator_code": seg.get("operationCarrierCode"),
                        "operator_name": seg.get("operationCarrierName"),
                        "code_share": bool(seg.get("codeShare", False)),
                    }
                )
        return results

    async def _enrich_with_exact_seats(
        self, dep: str, dest: str, days: list[CalendarDay]
    ) -> None:
        """bonusSeatView가 true로 표시한 (날짜, 등급) 조합만 scheduleAvailability로
        정밀 조회해 정확한 좌석수/운항사를 덧씌운다 (in-place).

        scheduleAvailability 호출 하나가 실패해도(네트워크 오류 등) 그 등급만
        불리언 그대로 남기고 나머지 조회는 계속 진행한다 — 정밀조회는 부가
        기능이지 캘린더 자체를 막을 이유가 아니다.
        """
        # (날짜, 등급) 조합별로 조회할 작업 목록을 먼저 만들고 동시에 몇 개씩 돌린다.
        # 순차로 하면 한 달치가 30번 * 몇 초라 몇 분씩 걸려서, 동시 호출 수를
        # 세마포어로 제한(과도한 트래픽으로 봇 탐지되는 걸 피하기 위함)해 병렬 처리한다.
        jobs: list[tuple[CalendarDay, str, str]] = [
            (day, field, day.date.replace("-", ""))
            for day in days
            for field in ("economy", "business", "first")
            if any(getattr(flight.seats, field) > 0 for flight in day.flights)
        ]

        semaphore = asyncio.Semaphore(6)

        async def _run_one(day: CalendarDay, field: str, date_yyyymmdd: str) -> tuple[CalendarDay, str, list[dict]]:
            cabin_type = CABIN_FIELD_TO_API_TYPE[field]
            cache_key = (dep, dest, date_yyyymmdd, cabin_type)
            cached = self._exact_seats_cache.get(cache_key)
            if cached is not None and time.time() - cached[0] < EXACT_SEATS_CACHE_TTL_SECONDS:
                return day, field, cached[1]

            async with semaphore:
                try:
                    exact = await self._fetch_exact_seats(dep, dest, date_yyyymmdd, cabin_type)
                except Exception:
                    exact = None
            if exact is not None:
                self._exact_seats_cache[cache_key] = (time.time(), exact)
            return day, field, exact

        job_results = await asyncio.gather(*(_run_one(*job) for job in jobs))

        for day, field, exact in job_results:
            if exact is None:
                continue  # 호출 실패, 그 등급은 불리언 값 그대로 남긴다
            by_key = {(r["flight_no"], r["dep_time"]): r for r in exact}
            for flight in day.flights:
                match = by_key.get((flight.flight_no, flight.dep_time))
                if match is None:
                    # 정밀조회에서 안 잡히면 실제로는 매진일 가능성이 높다
                    # (bonusSeatView는 하루 1회 업데이트라 부정확할 수 있음).
                    setattr(flight.seats, field, 0)
                    continue
                setattr(flight.seats, field, match["seat_count"])
                if match["operator_code"]:
                    flight.operator_code = match["operator_code"]
                    flight.operator_name = match["operator_name"]
                    flight.code_share = match["code_share"]

    async def fetch_award_price(
        self,
        dep: str,
        dest: str,
        outbound_date: str,
        outbound_flight_no: str,
        inbound_date: str,
        inbound_flight_no: str,
    ) -> dict | None:
        """왕복 최종 선택 시점에 딱 1번, 실제 UI를 그대로 흉내내 소요 마일리지/운임을 가져온다.

        이 값을 주는 awardAvailability API는 scheduleAvailability와 달리 API를 직접
        호출하면 막힌다 (Angular 내부 인증 토큰 필요, 실사로 확인됨) — 그래서 실제
        검색 폼을 채우고 검색 버튼을 눌러야만 나온다. 노선당 한 번이면 충분하므로
        (달력 조회처럼 날짜마다 반복 호출하지 않음) 몇 초~몇십 초 걸려도 감수한다.

        두 날짜가 캘린더 창에 동시에 보이는 두 달(현재~다음 달) 범위를 벗어나면
        (예: 왕복 간격이 두 달 이상) 지금 구현으로는 못 찾아서 None을 반환한다 —
        마일리지 표시는 부가 정보라 이 경우 화면에서 조용히 생략된다.

        Args:
            dep: 출발 공항 코드.
            dest: 목적지 공항 코드.
            outbound_date: 가는 날 (YYYY-MM-DD).
            outbound_flight_no: 가는 편명 (예: KE5771).
            inbound_date: 오는 날 (YYYY-MM-DD).
            inbound_flight_no: 오는 편명.

        Returns:
            {"outbound": {"mileage": int, "fare_krw": int},
             "inbound": {"mileage": int, "fare_krw": int}} 또는 못 찾으면 None.
        """
        async with self._lock:
            await self.ensure_logged_in()
            assert self._page is not None
            page = self._page

            out_d = datetime.date.fromisoformat(outbound_date)
            in_d = datetime.date.fromisoformat(inbound_date)

            try:
                # 아래 좌표들은 전부 1280x1000 기준으로 실사 검증된 값이라, 실제 창
                # 크기(예: 웨일 창이 1920 너비)와 무관하게 고정해야 한다.
                await page.set_viewport_size({"width": 1280, "height": 1000})
                await page.goto(
                    "https://www.koreanair.com/booking/search?bookingType=S&tripType=RT",
                    wait_until="load",
                    timeout=GOTO_TIMEOUT_MS,
                )
                await page.wait_for_timeout(2000)

                # 스카이팀 여정 토글이 켜져 있으면 끈다 (일반 KE 예매로)
                await page.evaluate(
                    """
                    () => {
                      const els = [...document.querySelectorAll('*')];
                      const label = els.find(e => e.children.length === 0 && e.textContent.trim() === '스카이팀 여정');
                      if (!label) return;
                      const row = label.closest('div');
                      const input = row ? row.querySelector('input[type=checkbox]') : null;
                      if (input && input.checked) label.click();
                    }
                    """
                )
                await page.wait_for_timeout(500)

                await self._fill_award_search_city(page, (120, 480), (200, 729), dep)
                await self._fill_award_search_city(page, (301, 478), (340, 729), dest)
                print("[KoreanAirClient] award-price: 출발/도착 입력 완료", flush=True)

                today = datetime.date.today()
                months_ahead = (out_d.year * 12 + out_d.month) - (today.year * 12 + today.month)
                if in_d.year * 12 + in_d.month > out_d.year * 12 + out_d.month + 1:
                    return None  # 두 달 창을 벗어남 — 부가 기능이라 조용히 포기

                await page.mouse.click(456, 480)  # 출발일 필드 (실사 검증된 고정 위치)
                await page.wait_for_timeout(1000)
                for _ in range(max(0, months_ahead)):
                    await page.mouse.click(1195, 703)  # 달력 '다음달' 화살표
                    await page.wait_for_timeout(500)

                # months_ahead번 '다음달'을 눌렀으므로, 이제 화면엔 [출발월, 출발월+1]이 보인다.
                await self._click_calendar_day(page, out_d, month_slot=0)
                await page.wait_for_timeout(400)
                in_slot = 0 if (in_d.year, in_d.month) == (out_d.year, out_d.month) else 1
                await self._click_calendar_day(page, in_d, month_slot=in_slot)
                await page.wait_for_timeout(500)
                print("[KoreanAirClient] award-price: 날짜 선택 완료", flush=True)

                response_holder: dict = {}

                async def _on_response(resp):
                    if "awardAvailability" in resp.url and "body" not in response_holder:
                        try:
                            response_holder["body"] = await resp.json()
                        except Exception:
                            pass

                page.on("response", _on_response)
                await page.mouse.click(632, 658)  # 항공편 검색 버튼 (실사 검증된 고정 위치)
                print("[KoreanAirClient] award-price: 검색 버튼 클릭", flush=True)
                for _ in range(20):
                    await page.wait_for_timeout(1000)
                    if "body" in response_holder:
                        break
                page.remove_listener("response", _on_response)
                print(f"[KoreanAirClient] award-price: 응답 수신={'body' in response_holder}", flush=True)

                body = response_holder.get("body")
                if not body or "upsellBoundAvailList" not in body:
                    await _dump_debug_state(page, "award_price_no_response")
                    return None

                out_price = self._extract_award_price(body, 0, outbound_flight_no)
                in_price = self._extract_award_price(body, 1, inbound_flight_no)
                print(f"[KoreanAirClient] award-price: out={out_price} in={in_price}", flush=True)
                if out_price is None or in_price is None:
                    with open(str(DEBUG_DUMP_DIR / "award_price_body.json"), "w", encoding="utf-8") as f:
                        json.dump(body, f, ensure_ascii=False)
                    return None
                return {"outbound": out_price, "inbound": in_price}
            except Exception as exc:
                print(f"[KoreanAirClient] award-price 예외: {type(exc).__name__}: {exc}", flush=True)
                await _dump_debug_state(page, "award_price_failure")
                return None
            finally:
                try:
                    await page.goto(LOGIN_URL, timeout=GOTO_TIMEOUT_MS)
                except Exception:
                    pass

    @staticmethod
    async def _fill_award_search_city(
        page: Page, box_pos: tuple[int, int], option_pos: tuple[int, int], code: str
    ) -> None:
        """출발지/도착지 박스를 열고 공항 코드를 입력해 첫 자동완성 결과를 클릭한다.

        박스 자체는 이미 채워진 값(예: 이전 검색의 SEL)에 따라 표시 텍스트가
        달라져서 텍스트로 못 찾고, 자동완성 결과 행도 코드+한글명이 여러 span에
        걸쳐 있어 정확히 텍스트로 매칭이 안 된다 (실사로 확인됨) — 실사로 검증된
        고정 좌표를 그대로 쓴다.
        """
        await page.mouse.click(*box_pos)
        await page.wait_for_timeout(800)
        await page.keyboard.type(code, delay=120)
        await page.wait_for_timeout(1200)
        await page.mouse.click(*option_pos)
        await page.wait_for_timeout(500)

    @staticmethod
    async def _click_calendar_day(page: Page, target: datetime.date, month_slot: int) -> None:
        """달력에서 특정 날짜를 클릭한다 (달력에 보이는 두 달 중 month_slot번째 달 기준).

        실사로 검증된 그리드 좌표(2026-08/09 기준)를 요일 계산으로 일반화한 것.
        """
        col_x = (
            [366, 426, 486, 546, 606, 665, 724]
            if month_slot == 0
            else [824, 884, 944, 1004, 1064, 1124, 1182]
        )
        row_y_base = 798
        row_height = 47

        first_of_month = target.replace(day=1)
        first_col = (first_of_month.weekday() + 1) % 7  # 월요일=0 -> 일요일 기준 0으로 변환
        cell_index = first_col + (target.day - 1)
        row = cell_index // 7
        col = cell_index % 7

        await page.mouse.click(col_x[col], row_y_base + row * row_height)

    @staticmethod
    def _extract_award_price(body: dict, bound_id: int, flight_no: str) -> dict | None:
        """awardAvailability 응답에서 특정 편명의 소요 마일리지/운임을 뽑는다."""
        bounds = body.get("upsellBoundAvailList", [])
        bound = next((b for b in bounds if b.get("boundId") == str(bound_id)), None)
        if bound is None:
            return None
        for flight in bound.get("availFlightList", []):
            segments = flight.get("flightInfoList", [])
            combined_no = "".join(
                f"{seg.get('carrierCode', '')}{seg.get('flightNumber', '')}" for seg in segments[:1]
            )
            if combined_no != flight_no:
                continue
            fare_families = flight.get("commercialFareFamilyList", [])
            if not fare_families:
                continue
            first = fare_families[0]
            try:
                mileage = int(float(first.get("totalMileage", 0)))
                fare_krw = int(float(first.get("totalFare", 0)))
            except (TypeError, ValueError):
                return None
            return {"mileage": mileage, "fare_krw": fare_krw}
        return None

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
