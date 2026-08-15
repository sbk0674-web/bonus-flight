@echo off
cd /d "%~dp0"

echo [1/3] 백엔드 파이썬 패키지 설치...
cd backend
pip install -e ".[dev]"
python -m playwright install chromium
cd ..

echo [2/3] 프론트 npm 패키지 설치...
cd frontend
call npm install
cd ..

echo [3/3] 완료. 앞으로는 start.bat 더블클릭으로 실행하세요.
echo 계정(SKYPASS 아이디/비번)은 실행 후 웹앱 안 "계정 설정" 화면에서 입력하면 됩니다.
pause
