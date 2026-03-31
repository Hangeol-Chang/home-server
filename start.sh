#!/bin/bash
set -euo pipefail

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}Starting Home Server Setup & Execution...${NC}"

if [ ! -d "$PROJECT_ROOT/app" ] || [ ! -d "$PROJECT_ROOT/web" ]; then
    echo -e "${RED}Error: app 또는 web 디렉토리를 찾을 수 없습니다: $PROJECT_ROOT${NC}"
    exit 1
fi

# 기존 프로세스 종료
echo -e "${YELLOW}Checking for existing processes...${NC}"
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "\.venv/bin/python main.py" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "vite dev" 2>/dev/null || true
sleep 1

# 1. App 서버 설정 (Python venv & Requirements)
echo -e "${YELLOW}Configuring App Server...${NC}"
cd "$PROJECT_ROOT/app" || exit 1

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment (.venv)...${NC}"
    python3 -m venv .venv
fi

if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    echo -e "${YELLOW}pip이 .venv에 없어 복구를 시도합니다 (ensurepip)...${NC}"
    .venv/bin/python -m ensurepip --upgrade || true
fi

if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    echo -e "${YELLOW}pip 복구 실패. .venv를 재생성합니다...${NC}"
    rm -rf .venv
    python3 -m venv .venv
fi

echo -e "${BLUE}Installing/Updating Python dependencies...${NC}"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo -e "${BLUE}Verifying Python runtime dependencies...${NC}"
.venv/bin/python -c "import fastapi, uvicorn" >/dev/null

# App 서버 시작 (백그라운드)
echo -e "${GREEN}Starting App Server (.venv/bin/python main.py)...${NC}"
nohup .venv/bin/python main.py > "$PROJECT_ROOT/logs/app.log" 2>&1 &
APP_PID=$!

# 2. Web 서버 설정 (Node modules)
echo -e "${YELLOW}Configuring Web Server...${NC}"
cd "$PROJECT_ROOT/web" || exit 1

# 터미널 외부(systemd 등)에서 실행될 때를 대비해 PATH 확장
export PATH="$PATH:/usr/local/bin:/usr/bin:/bin:/snap/bin:$HOME/.local/bin"

# NVM이 설치된 경우 NVM 환경 로드
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
elif [ -s "$HOME/.n-install/bin/n" ]; then
    export PATH="$PATH:$HOME/.n-install/bin"
fi

# npm 경로 확인
NPM_CMD=""
if command -v npm >/dev/null 2>&1; then
    NPM_CMD="$(command -v npm)"
elif [ -n "${NVM_BIN:-}" ] && [ -x "$NVM_BIN/npm" ]; then
    NPM_CMD="$NVM_BIN/npm"
fi

if [ -z "$NPM_CMD" ]; then
    echo -e "${RED}Error: npm을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}Node.js/npm을 설치한 뒤 다시 실행하세요. (예: nvm 설치 후 node LTS 설치)${NC}"
    exit 1
fi

NODE_VER_RAW="$(node -v 2>/dev/null || true)"
NODE_MAJOR="${NODE_VER_RAW#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
if [ -z "$NODE_MAJOR" ] || [ "$NODE_MAJOR" -lt 18 ]; then
    echo -e "${RED}Error: Node.js 버전이 너무 낮습니다. 현재: ${NODE_VER_RAW:-unknown}${NC}"
    echo -e "${YELLOW}web 프로젝트는 Node.js >= 18 이 필요합니다.${NC}"
    echo -e "${YELLOW}권장: nvm 설치 후 'nvm install --lts && nvm use --lts'${NC}"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing npm dependencies (this may take a while)...${NC}"
    "$NPM_CMD" install
fi

# Web 서버 시작 (백그라운드)
echo -e "${GREEN}Starting Web Server ($NPM_CMD run dev -- --host 0.0.0.0 --port 5173)...${NC}"
nohup "$NPM_CMD" run dev -- --host 0.0.0.0 --port 5173 > "$PROJECT_ROOT/logs/web.log" 2>&1 &
WEB_PID=$!

# PID 저장
echo "$APP_PID" > "$PROJECT_ROOT/logs/app.pid"
echo "$WEB_PID" > "$PROJECT_ROOT/logs/web.pid"

# 결과 출력
echo -e "\n${BLUE}Both servers are running!${NC}"
echo "App PID: $APP_PID (logs: $PROJECT_ROOT/logs/app.log)"
echo "Web PID: $WEB_PID (logs: $PROJECT_ROOT/logs/web.log)"
echo -e "\n${YELLOW}Waiting 5 seconds to check status...${NC}"
sleep 5

if ps -p $APP_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ App server is running${NC}"
else
    echo -e "${YELLOW}✗ App server failed. Check logs/app.log${NC}"
fi

if ps -p $WEB_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Web server is running${NC}"
else
    echo -e "${YELLOW}✗ Web server failed. Check logs/web.log${NC}"
fi
