# krean-mileage

대한항공 마일리지 좌석 왕복 조회 개인용 웹앱.

## 구조

- `backend/`: FastAPI + Playwright 스크래퍼 (레이어드: routers → services → clients)
- `frontend/`: Next.js 15 프론트

## 실행

### 백엔드

```bash
cd backend
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env   # KOREANAIR_ID, KOREANAIR_PW 채워넣기
uvicorn app.main:app --reload
```

> **주의**: 실제 대한항공 로그인/캘린더 조회가 동작하려면 먼저 `backend/scripts/spike_login.py`
> (Task 3 조사 스파이크)를 실제 SKYPASS 계정으로 직접 실행해서 로그인 폼 셀렉터와
> `app/clients/korean_air_client.py`의 `CALENDAR_API_PATH` 등 플레이스홀더 값을 실제 값으로
> 교체해야 합니다. 이 스파이크는 사람이 브라우저를 보며 대화형으로 실행해야 하는 작업이라
> 자동화된 환경에서는 수행할 수 없습니다.

### 프론트

```bash
cd frontend
npm install
npm run dev
```

`http://localhost:3000` 접속.

## 테스트

```bash
cd backend && python -m pytest -v
```
