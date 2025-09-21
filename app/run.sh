#!/bin/bash
ls# 메인 서버 실행 스크립트 (통합 모드)
echo "🚀 Home Server 통합 시스템 시작 중..."

# 가상환경이 있으면 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 가상환경 활성화됨"
fi

# 의존성 설치
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 의존성 설치 완료"
fi

# 모든 서브모듈의 의존성도 설치
echo "📦 서브모듈 의존성 확인 중..."
for module_dir in ../../modules/*/; do
    if [ -d "$module_dir" ] && [ "$(basename "$module_dir")" != "auto-trader" ]; then
        module_name=$(basename "$module_dir")
        req_file="$module_dir/app/requirements.txt"
        if [ -f "$req_file" ]; then
            echo "📦 $module_name 의존성 설치 중..."
            pip install -r "$req_file"
        fi
    fi
done

# FastAPI 통합 서버 실행
echo "🌐 통합 FastAPI 서버 실행 (포트: 5000)"
echo "📋 모든 서브모듈이 자동으로 로드됩니다."
python main.py