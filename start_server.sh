#!/bin/bash

# Home Server 시작 스크립트
# 가상환경을 활성화하고 Flask 서버를 시작합니다.

set -e  # 오류 발생 시 스크립트 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo -e "${BLUE}🏠 Home Server 시작 스크립트${NC}"
echo "작업 디렉토리: $SCRIPT_DIR"

# 가상환경 확인
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ 가상환경이 존재하지 않습니다.${NC}"
    echo -e "${YELLOW}다음 명령어로 환경을 설정하세요:${NC}"
    echo "  python3 install_req.py --venv"
    exit 1
fi

echo -e "${GREEN}✅ 가상환경 발견: $VENV_DIR${NC}"

# 가상환경 활성화
echo -e "${BLUE}🔄 가상환경 활성화 중...${NC}"
source "$VENV_DIR/bin/activate"

# Python 경로 확인
PYTHON_PATH=$(which python3)
echo -e "${GREEN}✅ Python 경로: $PYTHON_PATH${NC}"

# Flask 앱 실행
echo -e "${BLUE}🚀 Flask 서버 시작 중...${NC}"
echo -e "${YELLOW}서버 종료: Ctrl+C${NC}"
echo -e "${YELLOW}서버 주소: http://localhost:5000${NC}"
echo ""

# 서버 실행
python3 app.py
