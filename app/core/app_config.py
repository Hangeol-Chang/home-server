"""
FastAPI 애플리케이션 설정 및 초기화
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    
    app = FastAPI(
        title="Home Server",
        description="통합 홈 서버 API - 모든 서브모듈 포함",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용, 실제 배포시 도메인 제한 필요
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 
    
    return app

def setup_static_files(app: FastAPI, current_dir: str):
    """정적 파일 서빙 설정"""
    web_dir = os.path.join(os.path.dirname(current_dir), "web", "dist")
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")
        print(f"✅ 정적 파일 디렉토리 설정: {web_dir}")

def add_main_routes(app: FastAPI, current_dir: str, project_root: str):
    """메인 라우트 추가"""
    
    @app.get("/")
    async def root():
        """루트 엔드포인트 - 웹 앱 서빙"""
        web_dir = os.path.join(os.path.dirname(current_dir), "web", "dist")
        index_file = os.path.join(web_dir, "index.html")
        
        if os.path.exists(index_file):
            return FileResponse(index_file)
        else:
            return {
                "message": "Home Server API - 모든 서브모듈 통합",
                "version": "1.0.0",
                "docs": "/docs",
                "status": "running",
                "integrated_modules": get_module_count(project_root)
            }

    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        modules_status = {}
        modules_dir = os.path.join(project_root, "modules")
        
        if os.path.exists(modules_dir):
            for module_name in os.listdir(modules_dir):
                if os.path.isdir(os.path.join(modules_dir, module_name)) and module_name != "auto-trader":
                    modules_status[module_name] = "integrated"
        
        return {
            "status": "healthy", 
            "service": "home-server-integrated",
            "modules": modules_status,
            "timestamp": "2025-10-09"
        }

def get_module_count(project_root: str) -> int:
    """통합된 모듈 수 계산"""
    modules_dir = os.path.join(project_root, "modules")
    if not os.path.exists(modules_dir):
        return 0
    
    return len([
        name for name in os.listdir(modules_dir) 
        if os.path.isdir(os.path.join(modules_dir, name)) and name != "auto-trader"
    ])