@echo off
rem Home Server 가상환경 활성화 스크립트

set "SCRIPT_DIR=%~dp0"
set "VENV_PATH=%SCRIPT_DIR%venv"

if not exist "%VENV_PATH%" (
    echo ❌ 가상환경이 존재하지 않습니다: %VENV_PATH%
    echo 먼저 python install_dependencies.py를 실행하세요.
    pause
    exit /b 1
)

echo 🔄 Home Server 가상환경 활성화 중...
call "%VENV_PATH%\Scripts\activate.bat"
echo ✅ 가상환경이 활성화되었습니다.
echo 서버 실행: python app.py
echo 비활성화: deactivate
