# 대한항공 마일리지 좌석 캘린더 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 국내공항+출발월 선택 → 갈 수 있는 노선 → 좌석 있는 날짜만 보여주는 캘린더 → 가는편 선택 → 오는편 캘린더 → 오는편 선택 → 왕복 요약, 순서로 동작하는 개인용 대한항공 마일리지 좌석 조회 웹앱을 만든다.

**Architecture:** Next.js 15 프론트(Zustand로 화면 간 선택 상태 관리) + FastAPI 백엔드(레이어드: Router → AwardSearchService → KoreanAirClient). `KoreanAirClient`가 Playwright로 대한항공에 로그인(세션 쿠키 15분 캐싱)해서 실시간으로 좌석 캘린더를 긁어온다. DB 없음, 정적 노선맵만 로컬 데이터로 보관.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, Zustand, React Hook Form + Zod (프론트) / Python 3.12, FastAPI, Pydantic, Playwright, pytest, ruff (백엔드)

## Global Constraints

- 프론트: 들여쓰기 스페이스 2칸, 세미콜론 사용 안 함, 작은따옴표, camelCase/PascalCase, any 타입 금지
- 백엔드: snake_case, 모든 API 엔드포인트 Pydantic으로 입출력 검증, docstring은 Google 스타일
- 커밋 메시지 한글로 작성, 작은 단위로 커밋
- 좌석이 0인 날짜/편은 `/api/calendar` 응답에서 서버 단에서 제외 (프론트는 필터링 안 함)
- 승객 수 개념 없음 (등급별 잔여석 숫자만 표시)
- 예약/결제 기능 없음, 편도 없음, 왕복 흐름만
- 앱 자체 로그인 없음. 대한항공 로그인 자격증명은 `.env`에서만 읽음, 코드에 하드코딩 금지
- 안티봇/캡차 감지 시 재시도 금지, 즉시 에러 반환

---

## Task 1: 백엔드 스캐폴드 + Pydantic 스키마

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`
- Test: `backend/tests/test_schemas.py`

**Interfaces:**
- Produces: `SeatCounts(economy: int, business: int, first: int)`, `FlightOption(flight_no: str, dep_time: str, arr_time: str, seats: SeatCounts)`, `CalendarDay(date: str, flights: list[FlightOption])`, `RouteOption(dest: str, dest_name: str)`, `CalendarRequest(dep: str, dest: str, month: str)` — 모두 `backend/app/models/schemas.py`에서 export

- [ ] **Step 1: 백엔드 프로젝트 초기화**

```bash
mkdir -p backend/app/models backend/app/routers backend/app/services backend/app/clients backend/app/data backend/tests/fixtures
```

`backend/pyproject.toml`:

```toml
[project]
name = "krean-mileage-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "playwright>=1.48",
    "pydantic>=2.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.3", "httpx>=0.27", "ruff>=0.7"]

[tool.ruff]
line-length = 100
```

- [ ] **Step 2: 실패하는 스키마 테스트 작성**

`backend/tests/test_schemas.py`:

```python
"""Pydantic 스키마 검증 테스트."""
from app.models.schemas import (
    CalendarDay,
    CalendarRequest,
    FlightOption,
    RouteOption,
    SeatCounts,
)


def test_seat_counts_holds_three_cabin_classes():
    """SeatCounts는 이코노미/비즈니스/일등석 잔여석을 각각 갖는다."""
    seats = SeatCounts(economy=3, business=1, first=0)
    assert seats.economy == 3
    assert seats.business == 1
    assert seats.first == 0


def test_flight_option_nests_seat_counts():
    """FlightOption은 편명/시간과 SeatCounts를 함께 가진다."""
    flight = FlightOption(
        flight_no="KE001",
        dep_time="09:00",
        arr_time="12:00",
        seats=SeatCounts(economy=2, business=0, first=0),
    )
    assert flight.flight_no == "KE001"
    assert flight.seats.economy == 2


def test_calendar_day_groups_flights_by_date():
    """CalendarDay는 날짜 하나에 여러 FlightOption을 묶는다."""
    day = CalendarDay(
        date="2026-09-10",
        flights=[
            FlightOption(
                flight_no="KE001",
                dep_time="09:00",
                arr_time="12:00",
                seats=SeatCounts(economy=1, business=0, first=0),
            )
        ],
    )
    assert day.date == "2026-09-10"
    assert len(day.flights) == 1


def test_route_option_has_dest_code_and_name():
    """RouteOption은 목적지 공항코드와 표시용 이름을 가진다."""
    route = RouteOption(dest="NRT", dest_name="도쿄(나리타)")
    assert route.dest == "NRT"
    assert route.dest_name == "도쿄(나리타)"


def test_calendar_request_requires_dep_dest_month():
    """CalendarRequest는 출발지/목적지/월을 필수로 받는다."""
    req = CalendarRequest(dep="ICN", dest="NRT", month="2026-09")
    assert req.dep == "ICN"
    assert req.month == "2026-09"
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.schemas'`

- [ ] **Step 3: 스키마 구현**

`backend/app/models/schemas.py`:

```python
"""API 요청/응답 Pydantic 모델."""
from pydantic import BaseModel


class SeatCounts(BaseModel):
    """등급별 잔여석 수."""

    economy: int
    business: int
    first: int


class FlightOption(BaseModel):
    """하루 중 특정 편의 시간/등급별 잔여석."""

    flight_no: str
    dep_time: str
    arr_time: str
    seats: SeatCounts


class CalendarDay(BaseModel):
    """특정 날짜에 좌석이 있는 편 목록."""

    date: str
    flights: list[FlightOption]


class RouteOption(BaseModel):
    """출발지에서 갈 수 있는 노선(목적지) 하나."""

    dest: str
    dest_name: str


class CalendarRequest(BaseModel):
    """POST /api/calendar 요청 바디."""

    dep: str
    dest: str
    month: str
```

`backend/app/__init__.py`, `backend/app/models/__init__.py`: 빈 파일로 생성.

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_schemas.py -v`
Expected: `5 passed`

- [ ] **Step 5: FastAPI 앱 뼈대 작성**

`backend/app/main.py`:

```python
"""FastAPI 앱 엔트리포인트."""
from fastapi import FastAPI

app = FastAPI(title="krean-mileage-backend")


@app.get("/health")
def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok"}
```

- [ ] **Step 6: 커밋**

```bash
git add backend/
git commit -m "백엔드 스캐폴드 및 Pydantic 스키마 추가"
```

---

## Task 2: 정적 노선맵 + GET /api/routes

**Files:**
- Create: `backend/app/data/route_map.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/routes.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_routes_api.py`

**Interfaces:**
- Consumes: `RouteOption` (Task 1)
- Produces: `get_routes_for(dep: str) -> list[RouteOption]` in `app/data/route_map.py`, `GET /api/routes?dep=&month=` 엔드포인트

- [ ] **Step 1: 정적 노선맵 데이터 작성**

`backend/app/data/route_map.py`:

```python
"""대한항공 국내공항별 취항 국제선 목적지 정적 데이터.

실제 서비스 전에 대한항공 취항지 페이지 기준으로 갱신 필요 (MVP는 주요 노선만).
"""
from app.models.schemas import RouteOption

ROUTE_MAP: dict[str, list[RouteOption]] = {
    "ICN": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
        RouteOption(dest="KIX", dest_name="오사카"),
        RouteOption(dest="LAX", dest_name="로스앤젤레스"),
        RouteOption(dest="JFK", dest_name="뉴욕"),
        RouteOption(dest="CDG", dest_name="파리"),
        RouteOption(dest="LHR", dest_name="런던"),
        RouteOption(dest="SIN", dest_name="싱가포르"),
        RouteOption(dest="BKK", dest_name="방콕"),
    ],
    "GMP": [
        RouteOption(dest="HND", dest_name="도쿄(하네다)"),
        RouteOption(dest="KIX", dest_name="오사카"),
    ],
    "PUS": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
        RouteOption(dest="KIX", dest_name="오사카"),
    ],
    "CJU": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
    ],
}


def get_routes_for(dep: str) -> list[RouteOption]:
    """출발 공항 코드로 갈 수 있는 노선 목록을 반환한다.

    Args:
        dep: 출발 국내공항 IATA 코드 (예: ICN).

    Returns:
        해당 공항에서 취항하는 목적지 목록. 매핑에 없으면 빈 리스트.
    """
    return ROUTE_MAP.get(dep.upper(), [])
```

- [ ] **Step 2: 실패하는 API 테스트 작성**

`backend/tests/test_routes_api.py`:

```python
"""GET /api/routes 계약 테스트."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_routes_returns_destinations_for_known_airport():
    """ICN으로 조회하면 매핑된 목적지 목록을 돌려준다."""
    res = client.get("/api/routes", params={"dep": "ICN", "month": "2026-09"})
    assert res.status_code == 200
    body = res.json()
    assert any(item["dest"] == "NRT" for item in body)


def test_get_routes_returns_empty_list_for_unknown_airport():
    """매핑에 없는 공항 코드는 빈 리스트를 돌려준다."""
    res = client.get("/api/routes", params={"dep": "XXX", "month": "2026-09"})
    assert res.status_code == 200
    assert res.json() == []


def test_get_routes_requires_dep_and_month_params():
    """dep, month 파라미터 없이 호출하면 422."""
    res = client.get("/api/routes")
    assert res.status_code == 422
```

- [ ] **Step 3: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_routes_api.py -v`
Expected: FAIL (`ModuleNotFoundError` 또는 404, 라우터 아직 없음)

- [ ] **Step 4: 라우터 구현 및 등록**

`backend/app/routers/routes.py`:

```python
"""정적 노선 조회 라우터."""
from fastapi import APIRouter, Query

from app.data.route_map import get_routes_for
from app.models.schemas import RouteOption

router = APIRouter()


@router.get("/api/routes", response_model=list[RouteOption])
def list_routes(
    dep: str = Query(..., description="출발 국내공항 IATA 코드"),
    month: str = Query(..., description="출발월 YYYY-MM"),
) -> list[RouteOption]:
    """출발지에서 갈 수 있는 노선 목록을 반환한다 (정적 데이터, 즉시 응답)."""
    return get_routes_for(dep)
```

`backend/app/main.py` 수정:

```python
"""FastAPI 앱 엔트리포인트."""
from fastapi import FastAPI

from app.routers import routes

app = FastAPI(title="krean-mileage-backend")
app.include_router(routes.router)


@app.get("/health")
def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok"}
```

`backend/app/routers/__init__.py`: 빈 파일.

- [ ] **Step 5: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_routes_api.py -v`
Expected: `3 passed`

- [ ] **Step 6: 커밋**

```bash
git add backend/
git commit -m "정적 노선맵 및 GET /api/routes 추가"
```

---

## Task 3: KoreanAirClient 로그인 흐름 스파이크 (실사)

이 태스크는 자동화 코드가 아니라 **사람이 직접 실행하는 조사 스크립트**다. 실제 대한항공 계정으로 로그인해서 마일리지 좌석 조회 흐름의 실제 셀렉터/네트워크 요청을 확인해야, Task 4/5의 실제 스크래퍼 코드가 진짜로 동작한다 (브레인스토밍 단계 실사에서 `kds-switch` 토글이 스크립트 클릭으로 안 먹히는 것까지만 확인했고, 로그인 이후 화면은 미확인 상태).

**Files:**
- Create: `backend/scripts/spike_login.py`
- Create: `backend/.env.example`

**Interfaces:**
- Produces: `backend/tmp/spike_dom_dump.html`, `backend/tmp/spike_network.json` (조사 산출물, 사람이 직접 실행 후 생성됨)

- [ ] **Step 1: 조사 스크립트 작성**

`backend/scripts/spike_login.py`:

```python
"""대한항공 마일리지 로그인+좌석조회 흐름 조사용 스파이크 스크립트.

사람이 직접 headed 모드로 실행해서 로그인 → 마일리지 예매 토글 → 좌석 조회까지
수동으로 진행하며 각 단계 DOM/네트워크를 tmp/ 에 덤프한다. 이 결과를 보고
Task 4, 5의 실제 셀렉터/API 응답 구조를 확정한다.

실행: KOREANAIR_ID=xxx KOREANAIR_PW=xxx python scripts/spike_login.py
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

TMP_DIR = Path(__file__).parent.parent / "tmp"


def main() -> None:
    """headed 브라우저를 열고 수동 조작 후 Enter 누르면 DOM/네트워크를 덤프한다."""
    TMP_DIR.mkdir(exist_ok=True)
    requests_log: list[dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.on(
            "response",
            lambda res: requests_log.append({"url": res.url, "status": str(res.status)})
            if "koreanair" in res.url
            else None,
        )
        page.goto("https://www.koreanair.com/korea/ko.html")

        print("브라우저에서 직접 로그인 → 마일리지 예매 토글 → 좌석 조회까지 진행하세요.")
        print(f"KOREANAIR_ID={os.environ.get('KOREANAIR_ID', '(미설정)')}")
        input("다 끝나면 Enter를 누르세요 (그 시점 DOM/네트워크를 덤프합니다)...")

        (TMP_DIR / "spike_dom_dump.html").write_text(page.content(), encoding="utf-8")
        (TMP_DIR / "spike_network.json").write_text(
            json.dumps(requests_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"덤프 완료: {TMP_DIR}")
        browser.close()


if __name__ == "__main__":
    main()
```

`backend/.env.example`:

```
KOREANAIR_ID=
KOREANAIR_PW=
```

- [ ] **Step 2: playwright 브라우저 설치 및 스크립트 실행 (사람이 직접)**

```bash
cd backend
pip install -e ".[dev]"
playwright install chromium
python scripts/spike_login.py
```

브라우저가 열리면 직접: (1) 로그인, (2) 마일리지 예매 토글 켜기, (3) 편도/출발지/목적지/월 입력 후 좌석 조회까지 진행. 그 상태에서 터미널로 돌아와 Enter.

- [ ] **Step 3: 산출물 확인 및 기록**

`backend/tmp/spike_network.json`을 열어 `koreanair.com`으로 가는 요청 중 좌석/캘린더 관련 API로 보이는 URL을 찾는다 (예: `/api/...award...`, `/api/...calendar...` 패턴). 찾으면 그 요청의 실제 URL 패턴과 응답 바디 구조를 `docs/superpowers/specs/2026-08-15-korean-air-award-calendar-design.md`의 리스크 섹션 아래에 발견한 그대로 추가 기록한다. JSON API가 없고 서버렌더링 HTML만 있다면 `spike_dom_dump.html`에서 좌석 정보가 들어있는 DOM 구조(클래스명/데이터 속성)를 기록한다.

이 기록이 Task 4, 5 구현의 실제 근거가 된다 — 발견한 구조가 이 플랜에서 가정한 것과 다르면 Task 4/5 코드를 발견한 구조에 맞게 수정한다.

- [ ] **Step 4: 커밋**

```bash
git add backend/scripts/spike_login.py backend/.env.example docs/
echo "backend/tmp/" >> .gitignore
git add .gitignore
git commit -m "대한항공 로그인/조회 흐름 조사용 스파이크 스크립트 추가"
```

---

## Task 4: KoreanAirClient 로그인 + 세션 캐싱

**Files:**
- Create: `backend/app/clients/__init__.py`
- Create: `backend/app/clients/korean_air_client.py`
- Test: `backend/tests/test_korean_air_client_session.py`

**Interfaces:**
- Consumes: `KOREANAIR_ID`, `KOREANAIR_PW` 환경변수
- Produces: `class KoreanAirClient` with `async def ensure_logged_in(self) -> None`, `self._session_expires_at: float | None` — Task 5, 6에서 이 클래스에 메서드 추가

Task 3 스파이크 결과에서 실제 로그인 폼 셀렉터가 나오면 아래 코드의 `SELECTOR_ID_INPUT` 등 상수를 그 값으로 교체한다. 여기서는 Task 3 조사 전 합리적 기본값(표준 로그인 폼 패턴: `input[name=userId]`, `input[name=userPw]`, `button[type=submit]`)으로 작성하고, 세션 캐싱/TTL 로직은 셀렉터와 무관하게 그대로 유효하다.

- [ ] **Step 1: 실패하는 세션 캐싱 테스트 작성**

세션 캐싱 로직(TTL 만료 판단)은 Playwright 없이도 순수 로직으로 테스트 가능하게 분리한다.

`backend/tests/test_korean_air_client_session.py`:

```python
"""KoreanAirClient 세션 캐시 TTL 로직 테스트 (Playwright 없이)."""
import time

from app.clients.korean_air_client import KoreanAirClient


def test_session_not_expired_right_after_login():
    """로그인 직후에는 세션이 만료되지 않은 것으로 판단한다."""
    client = KoreanAirClient(user_id="u", password="p")
    client._session_expires_at = time.time() + 900
    assert client._is_session_valid() is True


def test_session_expired_after_ttl():
    """TTL이 지난 세션은 만료로 판단한다."""
    client = KoreanAirClient(user_id="u", password="p")
    client._session_expires_at = time.time() - 1
    assert client._is_session_valid() is False


def test_session_invalid_before_first_login():
    """한 번도 로그인 안 한 상태는 세션이 없는 것으로 판단한다."""
    client = KoreanAirClient(user_id="u", password="p")
    assert client._is_session_valid() is False
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_korean_air_client_session.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: KoreanAirClient 구현**

`backend/app/clients/korean_air_client.py`:

```python
"""대한항공 사이트 로그인 및 좌석 조회를 담당하는 Playwright 클라이언트."""
import time

from playwright.async_api import Browser, Page, async_playwright

SESSION_TTL_SECONDS = 15 * 60
LOGIN_URL = "https://www.koreanair.com/korea/ko.html"

# Task 3 스파이크 결과로 확정되면 실제 값으로 교체
SELECTOR_ID_INPUT = "input[name=userId]"
SELECTOR_PW_INPUT = "input[name=userPw]"
SELECTOR_LOGIN_SUBMIT = "button[type=submit]"


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

        self._session_expires_at = time.time() + SESSION_TTL_SECONDS

    async def close(self) -> None:
        """브라우저를 종료한다."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
```

`backend/app/clients/__init__.py`: 빈 파일.

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_korean_air_client_session.py -v`
Expected: `3 passed`

- [ ] **Step 5: 커밋**

```bash
git add backend/
git commit -m "KoreanAirClient 로그인 및 세션 TTL 캐싱 추가"
```

---

## Task 5: KoreanAirClient 캘린더 조회 + 파서 (fixture 기반)

파서(원시 HTML/JSON → `CalendarDay` 리스트 변환)는 Playwright 없이 순수 함수로 분리해서, 저장된 fixture로 테스트한다. Task 3 스파이크에서 실제 응답 구조를 확인했다면 fixture를 그 구조로 교체한다.

**Files:**
- Create: `backend/tests/fixtures/calendar_response_sample.json`
- Modify: `backend/app/clients/korean_air_client.py`
- Test: `backend/tests/test_korean_air_client_parser.py`

**Interfaces:**
- Consumes: `CalendarDay`, `FlightOption`, `SeatCounts` (Task 1)
- Produces: `parse_calendar_response(raw: dict) -> list[CalendarDay]` (모듈 레벨 함수, `korean_air_client.py`), `async def fetch_calendar(self, dep: str, dest: str, month: str) -> list[CalendarDay]` (KoreanAirClient 메서드)

- [ ] **Step 1: 대한항공 응답 형태를 가정한 fixture 작성**

`backend/tests/fixtures/calendar_response_sample.json`:

```json
{
  "days": [
    {
      "date": "2026-09-10",
      "flights": [
        {"flightNo": "KE001", "depTime": "09:00", "arrTime": "12:00", "economySeats": 3, "businessSeats": 1, "firstSeats": 0},
        {"flightNo": "KE005", "depTime": "18:00", "arrTime": "21:00", "economySeats": 0, "businessSeats": 0, "firstSeats": 0}
      ]
    },
    {
      "date": "2026-09-11",
      "flights": [
        {"flightNo": "KE001", "depTime": "09:00", "arrTime": "12:00", "economySeats": 0, "businessSeats": 0, "firstSeats": 0}
      ]
    }
  ]
}
```

이 fixture는 날짜 09-10엔 좌석 있는 편(KE001)과 없는 편(KE005)이 섞여있고, 09-11은 전부 0인 케이스를 담아서 필터링 로직을 검증한다.

- [ ] **Step 2: 실패하는 파서 테스트 작성**

`backend/tests/test_korean_air_client_parser.py`:

```python
"""KoreanAirClient 원시 응답 파서 테스트 (fixture 기반, 네트워크 없음)."""
import json
from pathlib import Path

from app.clients.korean_air_client import parse_calendar_response

FIXTURE = Path(__file__).parent / "fixtures" / "calendar_response_sample.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_parse_maps_seat_fields_to_seat_counts():
    """원시 응답의 economySeats/businessSeats/firstSeats를 SeatCounts로 매핑한다."""
    days = parse_calendar_response(_load_fixture())
    first_day = days[0]
    ke001 = next(f for f in first_day.flights if f.flight_no == "KE001")
    assert ke001.seats.economy == 3
    assert ke001.seats.business == 1
    assert ke001.seats.first == 0


def test_parse_excludes_flights_with_zero_seats_in_all_classes():
    """세 등급 모두 0석인 편(KE005)은 파싱 결과에서 제외된다."""
    days = parse_calendar_response(_load_fixture())
    first_day = days[0]
    flight_numbers = [f.flight_no for f in first_day.flights]
    assert "KE005" not in flight_numbers


def test_parse_excludes_dates_with_no_available_flights():
    """모든 편이 0석인 날짜(09-11) 자체가 결과에서 빠진다."""
    days = parse_calendar_response(_load_fixture())
    dates = [d.date for d in days]
    assert "2026-09-11" not in dates
    assert "2026-09-10" in dates
```

- [ ] **Step 3: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_korean_air_client_parser.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_calendar_response'`

- [ ] **Step 4: 파서 및 fetch_calendar 구현**

`backend/app/clients/korean_air_client.py`에 추가 (파일 맨 위 import 및 하단에 이어서):

```python
from app.models.schemas import CalendarDay, FlightOption, SeatCounts

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
```

`KoreanAirClient` 클래스 안에 메서드 추가:

```python
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
```

- [ ] **Step 5: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_korean_air_client_parser.py -v`
Expected: `3 passed`

- [ ] **Step 6: 커밋**

```bash
git add backend/
git commit -m "KoreanAirClient 캘린더 파서 및 fetch_calendar 추가"
```

---

## Task 6: AwardSearchService

Service는 Task 5의 필터링이 이미 파서 단에서 끝났으므로, 여기서는 KoreanAirClient 예외를 도메인 에러로 변환하고 1회 재시도(세션 만료 시)하는 오케스트레이션만 담당한다.

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/award_search_service.py`
- Test: `backend/tests/test_award_search_service.py`

**Interfaces:**
- Consumes: `KoreanAirClient.fetch_calendar`, `KoreanAirLoginError`, `AntiBotDetectedError` (Task 4, 5)
- Produces: `class AwardSearchService`, `async def search_calendar(self, dep: str, dest: str, month: str) -> list[CalendarDay]`, `class ScrapeFailedError(Exception)`

- [ ] **Step 1: 실패하는 서비스 테스트 작성 (KoreanAirClient 목 사용)**

`backend/tests/test_award_search_service.py`:

```python
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
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_award_search_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

(사전 준비: `backend/pyproject.toml`의 dev 의존성에 `pytest-asyncio>=0.24` 추가하고 `backend/pytest.ini`에 `[pytest]\nasyncio_mode = auto` 작성)

- [ ] **Step 3: 서비스 구현**

`backend/app/services/award_search_service.py`:

```python
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
```

`backend/app/services/__init__.py`: 빈 파일.

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_award_search_service.py -v`
Expected: `4 passed`

- [ ] **Step 5: 커밋**

```bash
git add backend/
git commit -m "AwardSearchService 재시도/에러 변환 로직 추가"
```

---

## Task 7: POST /api/calendar 엔드포인트

**Files:**
- Create: `backend/app/routers/calendar.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_calendar_api.py`

**Interfaces:**
- Consumes: `CalendarRequest`, `CalendarDay` (Task 1), `AwardSearchService.search_calendar`, `ScrapeFailedError` (Task 6)
- Produces: `POST /api/calendar` 엔드포인트

- [ ] **Step 1: 실패하는 API 테스트 작성 (서비스 의존성 오버라이드)**

`backend/tests/test_calendar_api.py`:

```python
"""POST /api/calendar 계약 테스트 (AwardSearchService는 의존성 오버라이드로 목 처리)."""
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import CalendarDay
from app.routers.calendar import get_award_search_service
from app.services.award_search_service import ScrapeFailedError

client = TestClient(app)


class _FakeServiceOk:
    async def search_calendar(self, dep, dest, month):
        return [CalendarDay(date="2026-09-10", flights=[])]


class _FakeServiceFail:
    async def search_calendar(self, dep, dest, month):
        raise ScrapeFailedError("조회 실패")


def test_post_calendar_returns_days_on_success():
    """정상 조회 시 CalendarDay 리스트를 그대로 반환한다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceOk()
    res = client.post("/api/calendar", json={"dep": "ICN", "dest": "NRT", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json() == [{"date": "2026-09-10", "flights": []}]


def test_post_calendar_returns_502_on_scrape_failure():
    """스크랩 실패 시 502와 에러 메시지를 반환한다."""
    app.dependency_overrides[get_award_search_service] = lambda: _FakeServiceFail()
    res = client.post("/api/calendar", json={"dep": "ICN", "dest": "NRT", "month": "2026-09"})
    app.dependency_overrides.clear()

    assert res.status_code == 502
    assert "조회 실패" in res.json()["detail"]


def test_post_calendar_validates_request_body():
    """필수 필드 없이 호출하면 422."""
    res = client.post("/api/calendar", json={"dep": "ICN"})
    assert res.status_code == 422
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd backend && python -m pytest tests/test_calendar_api.py -v`
Expected: FAIL with `ImportError: cannot import name 'get_award_search_service'`

- [ ] **Step 3: 라우터 구현**

`backend/app/routers/calendar.py`:

```python
"""좌석 캘린더 조회 라우터."""
import os

from fastapi import APIRouter, Depends, HTTPException

from app.clients.korean_air_client import KoreanAirClient
from app.models.schemas import CalendarDay, CalendarRequest
from app.services.award_search_service import AwardSearchService, ScrapeFailedError

router = APIRouter()

_client_singleton: KoreanAirClient | None = None


def get_award_search_service() -> AwardSearchService:
    """AwardSearchService를 만든다. 클라이언트는 프로세스 내에서 재사용한다."""
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = KoreanAirClient(
            user_id=os.environ["KOREANAIR_ID"],
            password=os.environ["KOREANAIR_PW"],
        )
    return AwardSearchService(client=_client_singleton)


@router.post("/api/calendar", response_model=list[CalendarDay])
async def search_calendar(
    body: CalendarRequest,
    service: AwardSearchService = Depends(get_award_search_service),
) -> list[CalendarDay]:
    """출발지/목적지/월 기준 좌석이 있는 날짜만 캘린더로 반환한다 (라이브 스크랩)."""
    try:
        return await service.search_calendar(body.dep, body.dest, body.month)
    except ScrapeFailedError as exc:
        raise HTTPException(status_code=502, detail=f"조회 실패, 다시 시도해주세요: {exc}") from exc
```

`backend/app/main.py`에 라우터 등록 추가:

```python
from app.routers import calendar, routes

app = FastAPI(title="krean-mileage-backend")
app.include_router(routes.router)
app.include_router(calendar.router)
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `cd backend && python -m pytest tests/test_calendar_api.py -v`
Expected: `3 passed`

- [ ] **Step 5: 전체 백엔드 테스트 스위트 실행**

Run: `cd backend && python -m pytest -v`
Expected: 지금까지 작성한 모든 테스트 통과 (18개 전후)

- [ ] **Step 6: 커밋**

```bash
git add backend/
git commit -m "POST /api/calendar 엔드포인트 추가"
```

---

## Task 8: 프론트 스캐폴드 + 타입 + Zustand 스토어

**Files:**
- Create: `frontend/` (Next.js 15 프로젝트, `create-next-app`)
- Create: `frontend/src/types/award.ts`
- Create: `frontend/src/stores/useSearchStore.ts`
- Create: `frontend/src/lib/api.ts`

**Interfaces:**
- Produces: `SeatCounts`, `FlightOption`, `CalendarDay`, `RouteOption` 타입, `useSearchStore` (Zustand), `fetchRoutes`, `fetchCalendar` API 함수 — 이후 모든 화면 태스크가 사용

- [ ] **Step 1: Next.js 프로젝트 생성**

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias
cd frontend
npx shadcn@latest init -d
npx shadcn@latest add button card select calendar
npm install zustand react-hook-form zod @hookform/resolvers
```

`.eslintrc.json`, `.prettierrc`가 세미콜론/작은따옴표 규칙과 다르면 프로젝트 컨벤션(세미콜론 없음, 작은따옴표)에 맞게 조정.

- [ ] **Step 2: 백엔드 응답 타입 정의**

`frontend/src/types/award.ts`:

```typescript
export type SeatCounts = {
  economy: number
  business: number
  first: number
}

export type FlightOption = {
  flightNo: string
  depTime: string
  arrTime: string
  seats: SeatCounts
}

export type CalendarDay = {
  date: string
  flights: FlightOption[]
}

export type RouteOption = {
  dest: string
  destName: string
}

export type LegSelection = {
  dep: string
  dest: string
  month: string
  date: string
  flight: FlightOption
}
```

- [ ] **Step 3: API 클라이언트 작성**

`frontend/src/lib/api.ts`:

```typescript
import type { CalendarDay, RouteOption } from '@/types/award'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export async function fetchRoutes(dep: string, month: string): Promise<RouteOption[]> {
  const res = await fetch(`${API_BASE}/api/routes?dep=${dep}&month=${month}`)
  if (!res.ok) throw new Error('노선 조회 실패')
  const body = await res.json()
  return body.map((r: { dest: string; dest_name: string }) => ({
    dest: r.dest,
    destName: r.dest_name,
  }))
}

export async function fetchCalendar(dep: string, dest: string, month: string): Promise<CalendarDay[]> {
  const res = await fetch(`${API_BASE}/api/calendar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dep, dest, month }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: '조회 실패' }))
    throw new Error(body.detail ?? '조회 실패')
  }
  const body = await res.json()
  return body.map((day: { date: string; flights: Array<{ flight_no: string; dep_time: string; arr_time: string; seats: { economy: number; business: number; first: number } }> }) => ({
    date: day.date,
    flights: day.flights.map((f) => ({
      flightNo: f.flight_no,
      depTime: f.dep_time,
      arrTime: f.arr_time,
      seats: f.seats,
    })),
  }))
}
```

- [ ] **Step 4: Zustand 스토어 작성**

`frontend/src/stores/useSearchStore.ts`:

```typescript
import { create } from 'zustand'
import type { LegSelection } from '@/types/award'

type SearchState = {
  dep: string | null
  month: string | null
  outbound: LegSelection | null
  inbound: LegSelection | null
  setDeparture: (dep: string, month: string) => void
  setOutbound: (leg: LegSelection) => void
  setInbound: (leg: LegSelection) => void
  reset: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  dep: null,
  month: null,
  outbound: null,
  inbound: null,
  setDeparture: (dep, month) => set({ dep, month }),
  setOutbound: (leg) => set({ outbound: leg }),
  setInbound: (leg) => set({ inbound: leg }),
  reset: () => set({ dep: null, month: null, outbound: null, inbound: null }),
}))
```

- [ ] **Step 5: 커밋**

```bash
git add frontend/
git commit -m "프론트 스캐폴드, 타입, API 클라이언트, Zustand 스토어 추가"
```

---

## Task 9: 화면1 — 출발지 선택

**Files:**
- Create: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes: `useSearchStore.setDeparture` (Task 8)
- Produces: `/` 라우트, "조회" 클릭 시 `/routes`로 이동

- [ ] **Step 1: 국내공항 목록 상수 및 페이지 작성**

`frontend/src/app/page.tsx`:

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/useSearchStore'

const DOMESTIC_AIRPORTS = [
  { code: 'ICN', name: '인천' },
  { code: 'GMP', name: '김포' },
  { code: 'PUS', name: '부산(김해)' },
  { code: 'CJU', name: '제주' },
]

export default function DeparturePage() {
  const router = useRouter()
  const setDeparture = useSearchStore((s) => s.setDeparture)
  const [dep, setDep] = useState('')
  const [month, setMonth] = useState('')

  const canSearch = dep !== '' && month !== ''

  function handleSearch() {
    setDeparture(dep, month)
    router.push('/routes')
  }

  return (
    <main className="flex flex-col items-center gap-4 p-8">
      <h1 className="text-xl font-bold">출발지 선택</h1>
      <select
        className="border rounded p-2"
        value={dep}
        onChange={(e) => setDep(e.target.value)}
      >
        <option value="">국내공항 선택</option>
        {DOMESTIC_AIRPORTS.map((a) => (
          <option key={a.code} value={a.code}>
            {a.name} ({a.code})
          </option>
        ))}
      </select>
      <input
        type="month"
        className="border rounded p-2"
        value={month}
        onChange={(e) => setMonth(e.target.value)}
      />
      <Button disabled={!canSearch} onClick={handleSearch}>
        조회
      </Button>
    </main>
  )
}
```

- [ ] **Step 2: 로컬에서 수동 확인**

Run: `cd frontend && npm run dev`
브라우저에서 `http://localhost:3000` 열고 공항+월 선택 후 [조회] 클릭 시 `/routes`로 이동하는지 확인. `/routes`는 아직 없으니 404가 정상 (다음 태스크에서 만듦).

- [ ] **Step 3: 커밋**

```bash
git add frontend/
git commit -m "출발지 선택 화면 추가"
```

---

## Task 10: 화면2 — 노선 목록

**Files:**
- Create: `frontend/src/app/routes/page.tsx`

**Interfaces:**
- Consumes: `useSearchStore` (dep, month), `fetchRoutes` (Task 8)
- Produces: `/routes` 라우트, 노선 클릭 시 `/calendar?leg=outbound`로 이동하며 store에 `dest` 임시 저장 필요 — store에 `pendingDest` 필드 추가

- [ ] **Step 1: 스토어에 pendingDest 필드 추가**

`frontend/src/stores/useSearchStore.ts` 수정 (`SearchState` 타입과 초기값에 추가):

```typescript
type SearchState = {
  dep: string | null
  month: string | null
  pendingDest: string | null
  outbound: LegSelection | null
  inbound: LegSelection | null
  setDeparture: (dep: string, month: string) => void
  setPendingDest: (dest: string) => void
  setOutbound: (leg: LegSelection) => void
  setInbound: (leg: LegSelection) => void
  reset: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  dep: null,
  month: null,
  pendingDest: null,
  outbound: null,
  inbound: null,
  setDeparture: (dep, month) => set({ dep, month }),
  setPendingDest: (dest) => set({ pendingDest: dest }),
  setOutbound: (leg) => set({ outbound: leg }),
  setInbound: (leg) => set({ inbound: leg }),
  reset: () => set({ dep: null, month: null, pendingDest: null, outbound: null, inbound: null }),
}))
```

- [ ] **Step 2: 노선 목록 페이지 작성**

`frontend/src/app/routes/page.tsx`:

```typescript
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { fetchRoutes } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { RouteOption } from '@/types/award'

export default function RoutesPage() {
  const router = useRouter()
  const { dep, month, setPendingDest } = useSearchStore()
  const [routeList, setRouteList] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dep || !month) {
      router.replace('/')
      return
    }
    fetchRoutes(dep, month)
      .then(setRouteList)
      .finally(() => setLoading(false))
  }, [dep, month, router])

  function handleSelect(dest: string) {
    setPendingDest(dest)
    router.push('/calendar?leg=outbound')
  }

  if (loading) return <p className="p-8">노선 불러오는 중...</p>

  return (
    <main className="flex flex-col gap-2 p-8">
      <h1 className="text-xl font-bold">갈 수 있는 노선</h1>
      {routeList.length === 0 && <p>취항 노선이 없습니다.</p>}
      <ul className="flex flex-col gap-2">
        {routeList.map((r) => (
          <li key={r.dest}>
            <button
              className="border rounded p-2 w-full text-left"
              onClick={() => handleSelect(r.dest)}
            >
              {r.destName} ({r.dest})
            </button>
          </li>
        ))}
      </ul>
    </main>
  )
}
```

- [ ] **Step 3: 수동 확인**

Run: `cd frontend && npm run dev`
`/`에서 출발지+월 선택 → `/routes`에서 백엔드(`cd backend && uvicorn app.main:app --reload` 실행 중이어야 함) 응답으로 노선 리스트가 뜨는지 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/
git commit -m "노선 목록 화면 추가"
```

---

## Task 11: 캘린더 화면 (가는편/오는편 공용)

**Files:**
- Create: `frontend/src/components/CalendarView.tsx`
- Create: `frontend/src/app/calendar/page.tsx`

**Interfaces:**
- Consumes: `useSearchStore`, `fetchCalendar` (Task 8), `LegSelection` 타입
- Produces: `/calendar?leg=outbound|inbound` 라우트. outbound 선택 완료 시 `/routes?leg=inbound`로 (도착지→출발지 리버스), inbound 선택 완료 시 `/summary`로 이동

- [ ] **Step 1: 재사용 가능한 CalendarView 컴포넌트 작성**

`frontend/src/components/CalendarView.tsx`:

```typescript
'use client'

import type { CalendarDay, FlightOption } from '@/types/award'

type Props = {
  days: CalendarDay[]
  onSelectFlight: (date: string, flight: FlightOption) => void
}

export function CalendarView({ days, onSelectFlight }: Props) {
  if (days.length === 0) {
    return <p>이 달에는 좌석이 있는 날짜가 없습니다.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {days.map((day) => (
        <div key={day.date} className="border rounded p-3">
          <p className="font-semibold">{day.date}</p>
          <ul className="flex flex-col gap-1 mt-2">
            {day.flights.map((flight) => (
              <li key={flight.flightNo}>
                <button
                  className="border rounded p-2 w-full text-left text-sm"
                  onClick={() => onSelectFlight(day.date, flight)}
                >
                  {flight.flightNo} {flight.depTime}→{flight.arrTime} | 이코노미 {flight.seats.economy} · 비즈니스 {flight.seats.business} · 일등석 {flight.seats.first}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: 캘린더 페이지 작성 (가는편/오는편 분기)**

`frontend/src/app/calendar/page.tsx`:

```typescript
'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CalendarView } from '@/components/CalendarView'
import { fetchCalendar } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { CalendarDay, FlightOption } from '@/types/award'

function CalendarPageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const leg = params.get('leg') === 'inbound' ? 'inbound' : 'outbound'
  const store = useSearchStore()
  const [days, setDays] = useState<CalendarDay[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const dep = leg === 'outbound' ? store.dep : store.outbound?.dest ?? null
  const dest = leg === 'outbound' ? store.pendingDest : store.dep
  const month = leg === 'outbound' ? store.month : store.pendingDest ? store.month : null

  useEffect(() => {
    if (!dep || !dest || !month) {
      router.replace('/')
      return
    }
    setLoading(true)
    setError(null)
    fetchCalendar(dep, dest, month)
      .then(setDays)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [dep, dest, month, router])

  function handleSelectFlight(date: string, flight: FlightOption) {
    if (!dep || !dest || !month) return
    const legSelection = { dep, dest, month, date, flight }
    if (leg === 'outbound') {
      store.setOutbound(legSelection)
      store.setPendingDest(dep) // 리턴 노선 화면에서 도착지가 원래 출발지로 고정되도록
      router.push('/routes?leg=inbound')
    } else {
      store.setInbound(legSelection)
      router.push('/summary')
    }
  }

  if (loading) return <p className="p-8">좌석 조회 중... (수 초~수십 초 걸릴 수 있습니다)</p>
  if (error) return <p className="p-8 text-red-600">{error}</p>

  return (
    <main className="flex flex-col gap-4 p-8">
      <h1 className="text-xl font-bold">{leg === 'outbound' ? '가는편' : '오는편'} 선택</h1>
      <CalendarView days={days} onSelectFlight={handleSelectFlight} />
    </main>
  )
}

export default function CalendarPage() {
  return (
    <Suspense fallback={<p className="p-8">불러오는 중...</p>}>
      <CalendarPageInner />
    </Suspense>
  )
}
```

- [ ] **Step 3: 수동 확인**

가는편 캘린더에서 편 선택 시 `/routes?leg=inbound`로 이동하는지, 오는편 캘린더에서 편 선택 시 `/summary`로 이동하는지 확인 (백엔드가 목 데이터라도 응답해야 함 — 로컬에서 `/api/calendar`를 임시로 하드코딩된 응답으로 띄워 확인 가능).

- [ ] **Step 4: 커밋**

```bash
git add frontend/
git commit -m "캘린더 화면(가는편/오는편 공용) 추가"
```

---

## Task 12: 화면2(노선 목록) 리턴 흐름 대응

Task 10에서 만든 `/routes`는 가는편 기준으로만 만들어졌다. 오는편(`leg=inbound`)일 때는 노선 목록 대신 바로 "출발지로 고정된 목적지"로 캘린더를 조회해야 하므로, `/routes` 화면이 `leg` 쿼리를 인식해서 분기하게 만든다.

**Files:**
- Modify: `frontend/src/app/routes/page.tsx`

**Interfaces:**
- Consumes: `useSearchParams` leg 값, `useSearchStore.pendingDest` (Task 11에서 outbound 완료 시 이미 dep으로 세팅해둠)

- [ ] **Step 1: leg=inbound일 때 노선 목록을 건너뛰고 바로 캘린더로 이동하도록 수정**

`frontend/src/app/routes/page.tsx` 전체를 다음으로 교체:

```typescript
'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { fetchRoutes } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { RouteOption } from '@/types/award'

function RoutesPageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const leg = params.get('leg') === 'inbound' ? 'inbound' : 'outbound'
  const { dep, month, outbound, setPendingDest } = useSearchStore()
  const [routeList, setRouteList] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (leg === 'inbound') {
      // 오는편은 노선 선택 없이 출발지로 고정, 바로 캘린더로 이동
      router.replace('/calendar?leg=inbound')
      return
    }
    if (!dep || !month) {
      router.replace('/')
      return
    }
    fetchRoutes(dep, month)
      .then(setRouteList)
      .finally(() => setLoading(false))
  }, [dep, month, leg, outbound, router])

  function handleSelect(dest: string) {
    setPendingDest(dest)
    router.push('/calendar?leg=outbound')
  }

  if (leg === 'inbound' || loading) return <p className="p-8">불러오는 중...</p>

  return (
    <main className="flex flex-col gap-2 p-8">
      <h1 className="text-xl font-bold">갈 수 있는 노선</h1>
      {routeList.length === 0 && <p>취항 노선이 없습니다.</p>}
      <ul className="flex flex-col gap-2">
        {routeList.map((r) => (
          <li key={r.dest}>
            <button
              className="border rounded p-2 w-full text-left"
              onClick={() => handleSelect(r.dest)}
            >
              {r.destName} ({r.dest})
            </button>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default function RoutesPage() {
  return (
    <Suspense fallback={<p className="p-8">불러오는 중...</p>}>
      <RoutesPageInner />
    </Suspense>
  )
}
```

- [ ] **Step 2: 수동 확인**

가는편 선택 완료 → `/routes?leg=inbound` 진입 시 노선 목록 없이 바로 `/calendar?leg=inbound`로 리다이렉트되는지 확인.

- [ ] **Step 3: 커밋**

```bash
git add frontend/
git commit -m "오는편 흐름에서 노선 목록 건너뛰고 바로 캘린더로 이동하도록 수정"
```

---

## Task 13: 화면6 — 왕복 요약

**Files:**
- Create: `frontend/src/app/summary/page.tsx`

**Interfaces:**
- Consumes: `useSearchStore` (outbound, inbound, reset) (Task 8)
- Produces: `/summary` 라우트

- [ ] **Step 1: 요약 페이지 작성**

`frontend/src/app/summary/page.tsx`:

```typescript
'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/useSearchStore'
import type { LegSelection } from '@/types/award'

function LegSummary({ title, leg }: { title: string; leg: LegSelection }) {
  return (
    <div className="border rounded p-4">
      <p className="font-semibold">{title}</p>
      <p>{leg.dep} → {leg.dest}</p>
      <p>{leg.date} {leg.flight.flightNo} {leg.flight.depTime}→{leg.flight.arrTime}</p>
      <p>
        이코노미 {leg.flight.seats.economy} · 비즈니스 {leg.flight.seats.business} · 일등석 {leg.flight.seats.first}
      </p>
    </div>
  )
}

export default function SummaryPage() {
  const router = useRouter()
  const { outbound, inbound, reset } = useSearchStore()

  useEffect(() => {
    if (!outbound || !inbound) {
      router.replace('/')
    }
  }, [outbound, inbound, router])

  if (!outbound || !inbound) return null

  function handleRestart() {
    reset()
    router.push('/')
  }

  return (
    <main className="flex flex-col gap-4 p-8">
      <h1 className="text-xl font-bold">왕복 조회 결과</h1>
      <LegSummary title="가는편" leg={outbound} />
      <LegSummary title="오는편" leg={inbound} />
      <Button onClick={handleRestart}>다시 조회</Button>
    </main>
  )
}
```

- [ ] **Step 2: 수동 확인**

전체 흐름(출발지 선택 → 노선 → 가는편 캘린더 → 오는편 캘린더 → 요약)을 처음부터 끝까지 클릭해서 상태가 올바르게 넘어가는지 확인.

- [ ] **Step 3: 커밋**

```bash
git add frontend/
git commit -m "왕복 요약 화면 추가"
```

---

## Task 14: 통합 수동 QA + README

**Files:**
- Create: `README.md`
- Create: `backend/.env` (사람이 직접, git에 커밋하지 않음)

**Interfaces:**
- 없음 (문서 + 수동 검증 태스크)

- [ ] **Step 1: 루트 README 작성**

`README.md`:

```markdown
# krean-mileage

대한항공 마일리지 좌석 왕복 조회 개인용 웹앱.

## 구조

- `backend/`: FastAPI + Playwright 스크래퍼 (레이어드: routers → services → clients)
- `frontend/`: Next.js 15 프론트

## 실행

### 백엔드

\`\`\`bash
cd backend
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env   # KOREANAIR_ID, KOREANAIR_PW 채워넣기
uvicorn app.main:app --reload
\`\`\`

### 프론트

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

`http://localhost:3000` 접속.

## 테스트

\`\`\`bash
cd backend && python -m pytest -v
\`\`\`
```

`.gitignore`에 `backend/.env` 추가 확인 (없으면 추가).

- [ ] **Step 2: 백엔드/프론트 동시 실행 후 전체 흐름 수동 QA**

```bash
# 터미널 1
cd backend && cp .env.example .env  # 실제 계정 정보 입력
uvicorn app.main:app --reload

# 터미널 2
cd frontend && npm run dev
```

브라우저로 `http://localhost:3000`에서: 출발공항+월 선택 → 노선 목록 확인 → 목적지 선택 → 가는편 캘린더에서 좌석 있는 날짜만 나오는지 확인 → 편 선택 → 오는편 캘린더 확인 → 편 선택 → 요약 화면에서 두 편 정보 다 맞는지 확인.

로그인 실패, 조회 실패 시나리오도 확인: `.env`의 비밀번호를 일부러 틀리게 넣고 조회했을 때 화면에 "대한항공 로그인 실패" 메시지가 뜨는지 확인.

- [ ] **Step 3: 커밋**

```bash
git add README.md .gitignore
git commit -m "README 및 실행 가이드 추가"
```

---

## Self-Review 결과

- **스펙 커버리지**: 화면 흐름 6단계(Task 9~13), API 계약 2개 엔드포인트(Task 2, 7), 좌석 0 필터링(Task 5), 로그인+세션캐싱(Task 4), 에러 처리 4종(Task 6, 7), 정적 노선맵(Task 2), 승객수 없음(Task 13 요약에 반영 안 함 — 의도적), 리스크(비로그인 여부/anti-bot/shadow DOM)를 Task 3 스파이크로 커버. 모두 대응됨
- **플레이스홀더 스캔**: `CALENDAR_API_PATH`, 로그인 셀렉터 상수는 Task 3 스파이크 결과로 교체하라고 명시했고 합리적 기본값을 채워뒀음 (완전 미정 TBD 아님)
- **타입 일관성**: `CalendarDay`/`FlightOption`/`SeatCounts`가 백엔드(Pydantic, snake_case 필드는 API 응답 JSON 기준)와 프론트(TypeScript, camelCase)에서 각각 정의되고 `frontend/src/lib/api.ts`의 매핑 함수가 그 경계를 명시적으로 처리함. `useSearchStore`의 `setOutbound`/`setInbound`/`setPendingDest`/`setDeparture` 시그니처가 Task 9~13 전체에서 동일하게 사용됨
