#!/bin/bash
# Home Server 가상환경 활성화 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 가상환경이 존재하지 않습니다: $VENV_PATH"
    echo "먼저 python3 install_dependencies.py를 실행하세요."
    exit 1
fi

echo "🔄 Home Server 가상환경 활성화 중..."
source "$VENV_PATH/bin/activate"
echo "✅ 가상환경이 활성화되었습니다."
echo "서버 실행: python3 app.py"
echo "비활성화: deactivate"
