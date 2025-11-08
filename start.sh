#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Home Server...${NC}"

# App 서버 시작 (백그라운드) - 백엔드 먼저 실행
echo -e "${GREEN}Starting App Server (python3 main.py)...${NC}"
cd /home/pi/workspace/home-server/app
source .venv/bin/activate
python3 main.py > ../logs/app.log 2>&1 &
APP_PID=$!
echo -e "${GREEN}App server started with PID: $APP_PID${NC}"

# 잠시 대기 (백엔드가 준비될 시간)
sleep 3

# Web 서버 시작 (백그라운드)
echo -e "${GREEN}Starting Web Server (npm run dev)...${NC}"
cd /home/pi/workspace/home-server/web
npm run dev > ../logs/web.log 2>&1 &
WEB_PID=$!
echo -e "${GREEN}Web server started with PID: $WEB_PID${NC}"

echo -e "${BLUE}Both servers are running!${NC}"
echo "App PID: $APP_PID"
echo "Web PID: $WEB_PID"
echo ""
echo "To stop the servers, run:"
echo "  kill $WEB_PID $APP_PID"
echo ""
echo "To view logs:"
echo "  tail -f logs/web.log"
echo "  tail -f logs/app.log"
