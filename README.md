# krean-mileage

대한항공 마일리지 좌석 왕복 조회 개인용 웹앱.

## 구조

- `backend/`: FastAPI + Playwright 스크래퍼 (레이어드: routers → services → clients)
- `frontend/`: Next.js 15 프론트

## 실행 (원클릭)

**최초 1회만**: `setup.bat` 더블클릭 (파이썬/npm 패키지, Playwright 브라우저 설치)

**이후 매번**: `start.bat` 더블클릭 — 백엔드/프론트 서버가 뜨고 브라우저가 자동으로 열립니다.

대한항공은 네이버 등 소셜 로그인도 지원하므로 이 앱은 아이디/비밀번호를 저장하거나
자동입력하지 않습니다. 대신 두 가지 방식으로 로그인 세션을 씁니다:

**방식 A (추천): 웨일 브라우저에 CDP로 접속**

평소 쓰는 네이버 웨일에 이미 로그인돼 있으면, 매번 새로 로그인할 필요 없이 그 세션을
그대로 재사용합니다. 웨일을 아래 플래그로 띄운 상태에서 `start.bat`을 실행하면 됩니다.

```bash
"C:\Program Files\Naver\Naver Whale\Application\<버전>\whale.exe" --remote-debugging-port=9223 --remote-allow-origins=*
```

(`--remote-allow-origins=*` 없으면 최신 크로미움 보안 정책 때문에 CDP 연결 자체가 안 됩니다.)
백엔드 실행 시 `KOREANAIR_CDP_ENDPOINT=http://localhost:9223` 환경변수를 설정하면 이 방식이 켜집니다
(`start.bat`에 이미 반영돼 있음).

**방식 B: 매번 새 브라우저로 직접 로그인**

`KOREANAIR_CDP_ENDPOINT`를 설정하지 않으면, "조회"를 누를 때마다 headed 브라우저 창이 새로
뜨고 그 창에서 직접 로그인해야 합니다 (5분 안에 로그인하면 이후 15분간 세션 재사용).

실제 캘린더 API(`/api/hmp/bonusSeatView/bonusSeatView`)와 로그인 성공 판단 로직은 실사로
검증 완료된 상태입니다 (`app/clients/korean_air_client.py`).

## 데이터 정확도에 대한 중요한 한계

이 앱이 쓰는 `bonusSeatView` API는 대한항공이 공식적으로 **"실시간 현황이 아니며 하루
1회 업데이트"**된다고 명시한 데이터입니다 (대한항공 "보너스 좌석 조회" 페이지 안내문).
실사로 실제 예약 API(`awardAvailability`, 로그인 UI를 직접 거쳐야만 호출 가능해서
이 앱에는 통합하지 않음)와 대조해본 결과, `bonusSeatView`가 "가능"이라고 표시한
등급이 실제로는 매진인 경우가 확인됐습니다 (예: 2026-10-03 KE2129 비즈니스석).

**따라서 이 앱은 "이 정도면 있을 만하다"는 참고용이지, 예약 가능을 보장하지 않습니다.**
예약 전 반드시 대한항공 사이트에서 직접 재확인하세요. (프론트 각 화면에 경고 문구로
표시되어 있습니다.)

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
