# krean-mileage

대한항공 마일리지 좌석 왕복 조회 개인용 웹앱.

## 구조

- `backend/`: FastAPI + Playwright 스크래퍼 (레이어드: routers → services → clients)
- `frontend/`: Next.js 15 프론트

## 실행 (원클릭)

**최초 1회만**: `setup.bat` 더블클릭 (파이썬/npm 패키지, Playwright 브라우저 설치)

**이후 매번**: `start.bat` 더블클릭 — 백엔드/프론트 서버가 뜨고 브라우저가 자동으로 열립니다.

대한항공은 네이버 등 소셜 로그인도 지원하므로 이 앱은 아이디/비밀번호를 저장하거나
자동입력하지 않습니다. 웹앱에서 "조회"를 누르면 브라우저 창이 하나 뜨고, 그 창에서
**매번 직접** 대한항공에 로그인하면 됩니다(5분 안에 로그인하면 이후 15분간 세션 재사용).

> **주의**: 실제 캘린더 조회가 동작하려면 먼저 `backend/scripts/spike_login.py`
> (Task 3 조사 스파이크)를 직접 실행해서 로그인 성공 마커와
> `app/clients/korean_air_client.py`의 `CALENDAR_API_PATH` 등 플레이스홀더 값을 실제 값으로
> 교체해야 합니다. 이 스파이크는 사람이 브라우저를 보며 대화형으로 실행해야 하는 작업이라
> 자동화된 환경에서는 수행할 수 없습니다. (배치파일로는 실행 안 됨 — 터미널에서 직접
> `python scripts/spike_login.py`로 실행)

## 수동 실행 (원클릭 대신)

### 백엔드

```bash
cd backend
pip install -e ".[dev]"
playwright install chromium
uvicorn app.main:app --reload
```

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
