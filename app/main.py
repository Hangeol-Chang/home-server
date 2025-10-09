#!/usr/bin/env python3
"""
Home Server 메인 엔트리 포인트
통합 FastAPI 서버 실행 및 서브모듈 관리
"""

import os
import sys

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)
sys.path.append(current_dir)

# 로컬 모듈 import
from core.app_config import create_app, setup_static_files, add_main_routes
from modules.submodule_manager import SubmoduleManager
from utils.server_runner import ServerRunner, get_server_config

def initialize_application():
    """애플리케이션 초기화"""
    print("🏠 Home Server 통합 시스템 초기화 중...")
    
    # FastAPI 앱 생성
    app = create_app()
    
    # 정적 파일 설정
    setup_static_files(app, current_dir)
    
    # 메인 라우트 추가
    add_main_routes(app, current_dir, project_root)
    
    # 서브모듈 매니저 초기화
    submodule_manager = SubmoduleManager(app, project_root)
    
    # 모든 서브모듈 등록
    submodule_manager.register_all_modules()
    
    print("✅ 모든 모듈 로딩 완료!")
    
    return app, submodule_manager

def main():
    """메인 실행 함수"""
    # 애플리케이션 초기화
    app, submodule_manager = initialize_application()
    
    # 서버 설정 로드
    config = get_server_config()
    
    # 서버 실행
    server_runner = ServerRunner(app, submodule_manager)
    
    if config["debug"]:
        server_runner.run_development_server(
            host=config["host"], 
            port=config["port"]
        )
    else:
        server_runner.run_production_server(
            host=config["host"], 
            port=config["port"]
        )

# 전역 변수로 app 노출 (uvicorn reload용)
app, submodule_manager = initialize_application()

if __name__ == "__main__":
    main()