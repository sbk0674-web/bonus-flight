@echo off
cd /d "%~dp0"

echo 웨일 브라우저(CDP 9223)가 안 떠 있으면 먼저 실행하세요:
echo   "C:\Program Files\Naver\Naver Whale\Application\<버전>\whale.exe" --remote-debugging-port=9223 --remote-allow-origins=*
echo (이미 떠 있으면 무시하고 계속됩니다)

echo 백엔드 서버 시작 중...
set KOREANAIR_CDP_ENDPOINT=http://localhost:9223
start "krean-mileage-backend" cmd /k "cd backend && set KOREANAIR_CDP_ENDPOINT=http://localhost:9223 && uvicorn app.main:app --reload --port 8000"

echo 프론트 서버 시작 중...
start "krean-mileage-frontend" cmd /k "cd frontend && npm run dev"

echo 서버 뜨는 동안 잠깐 대기...
timeout /t 8 /nobreak >nul

start "" "http://localhost:3000"
