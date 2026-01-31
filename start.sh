#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/home/pi/code-server/src/home-server"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}Starting Home Server Setup & Execution...${NC}"

# 기존 프로세스 종료
echo -e "${YELLOW}Checking for existing processes...${NC}"
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "vite dev" 2>/dev/null || true
sleep 1

# 1. App 서버 설정 (Python venv & Requirements)
echo -e "${YELLOW}Configuring App Server...${NC}"
cd "$PROJECT_ROOT/app" || exit 1

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment (.venv)...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${BLUE}Installing/Updating Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# App 서버 시작 (백그라운드)
echo -e "${GREEN}Starting App Server (python3 main.py)...${NC}"
nohup python3 main.py > "$PROJECT_ROOT/logs/app.log" 2>&1 &
APP_PID=$!

# 2. Web 서버 설정 (Node modules)
echo -e "${YELLOW}Configuring Web Server...${NC}"
cd "$PROJECT_ROOT/web" || exit 1

if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing npm dependencies (this may take a while)...${NC}"
    npm install
fi

# Web 서버 시작 (백그라운드)
echo -e "${GREEN}Starting Web Server (npm run dev)...${NC}"
nohup npm run dev > "$PROJECT_ROOT/logs/web.log" 2>&1 &
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
