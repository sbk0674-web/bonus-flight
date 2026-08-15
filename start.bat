@echo off
cd /d "%~dp0"

echo 백엔드 서버 시작 중...
start "krean-mileage-backend" cmd /k "cd backend && uvicorn app.main:app --reload"

echo 프론트 서버 시작 중...
start "krean-mileage-frontend" cmd /k "cd frontend && npm run dev"

echo 서버 뜨는 동안 잠깐 대기...
timeout /t 8 /nobreak >nul

start "" "http://localhost:3000"
