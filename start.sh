#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/home/pi/workspace/home-server"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}Starting Home Server...${NC}"

# 기존 프로세스 종료
echo -e "${YELLOW}Checking for existing processes...${NC}"
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "vite dev" 2>/dev/null || true
sleep 1

# App 서버 시작 (백그라운드) - 백엔드 먼저 실행
echo -e "${GREEN}Starting App Server (python3 main.py)...${NC}"
cd "$PROJECT_ROOT/app" || exit 1
source .venv/bin/activate
nohup python3 main.py > "$PROJECT_ROOT/logs/app.log" 2>&1 &
APP_PID=$!
echo -e "${GREEN}App server started with PID: $APP_PID${NC}"

# 잠시 대기 (백엔드가 준비될 시간)
sleep 3

# Web 서버 시작 (백그라운드)
echo -e "${GREEN}Starting Web Server (npm run dev)...${NC}"
cd "$PROJECT_ROOT/web" || exit 1
nohup npm run dev > "$PROJECT_ROOT/logs/web.log" 2>&1 &
WEB_PID=$!
echo -e "${GREEN}Web server started with PID: $WEB_PID${NC}"

# PID 저장
echo "$APP_PID" > "$PROJECT_ROOT/logs/app.pid"
echo "$WEB_PID" > "$PROJECT_ROOT/logs/web.pid"

echo ""
echo -e "${BLUE}Both servers are running!${NC}"
echo "App PID: $APP_PID (logs: $PROJECT_ROOT/logs/app.log)"
echo "Web PID: $WEB_PID (logs: $PROJECT_ROOT/logs/web.log)"
echo ""
echo "To stop the servers, run:"
echo "  ./stop.sh"
echo "  or manually: kill $WEB_PID $APP_PID"
echo ""
echo "To view logs:"
echo "  tail -f $PROJECT_ROOT/logs/web.log"
echo "  tail -f $PROJECT_ROOT/logs/app.log"
echo ""
echo -e "${YELLOW}Waiting 5 seconds to check if processes are running...${NC}"
sleep 5

# 프로세스 상태 확인
if ps -p $APP_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ App server is running${NC}"
else
    echo -e "${YELLOW}✗ App server may have stopped. Check logs/app.log${NC}"
fi

if ps -p $WEB_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Web server is running${NC}"
else
    echo -e "${YELLOW}✗ Web server may have stopped. Check logs/web.log${NC}"
fi
