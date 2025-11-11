#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/home/pi/workspace/home-server"

echo -e "${BLUE}Stopping Home Server...${NC}"

# PID 파일에서 PID 읽기
if [ -f "$PROJECT_ROOT/logs/app.pid" ]; then
    APP_PID=$(cat "$PROJECT_ROOT/logs/app.pid")
    if ps -p $APP_PID > /dev/null 2>&1; then
        kill $APP_PID
        echo -e "${GREEN}Stopped App server (PID: $APP_PID)${NC}"
    else
        echo -e "${RED}App server (PID: $APP_PID) is not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/app.pid"
fi

if [ -f "$PROJECT_ROOT/logs/web.pid" ]; then
    WEB_PID=$(cat "$PROJECT_ROOT/logs/web.pid")
    if ps -p $WEB_PID > /dev/null 2>&1; then
        kill $WEB_PID
        echo -e "${GREEN}Stopped Web server (PID: $WEB_PID)${NC}"
    else
        echo -e "${RED}Web server (PID: $WEB_PID) is not running${NC}"
    fi
    rm -f "$PROJECT_ROOT/logs/web.pid"
fi

# 프로세스 이름으로도 종료 시도
echo -e "${BLUE}Checking for any remaining processes...${NC}"
pkill -f "python3 main.py" 2>/dev/null && echo -e "${GREEN}Killed python3 main.py processes${NC}"
pkill -f "vite dev" 2>/dev/null && echo -e "${GREEN}Killed vite dev processes${NC}"

echo -e "${GREEN}Home Server stopped!${NC}"
