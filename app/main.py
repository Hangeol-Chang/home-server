from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
import sys
import importlib.util
import asyncio
import subprocess
import signal
from pathlib import Path

# 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

app = FastAPI(
    title="Home Server",
    description="통합 홈 서버 API - 모든 서브모듈 포함",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 실제 배포시 도메인 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서브모듈 프로세스 관리
submodule_processes = []

def load_submodule_router(module_name, module_path):
    """서브모듈의 라우터를 직접 로드"""
    try:
        router_file = os.path.join(module_path, "app", "router.py")
        if os.path.exists(router_file):
            # 모듈 스펙 생성
            spec = importlib.util.spec_from_file_location(f"{module_name}_router", router_file)
            router_module = importlib.util.module_from_spec(spec)
            
            # 모듈의 sys.path에 추가
            module_app_path = os.path.join(module_path, "app")
            sys.path.insert(0, module_app_path)
            
            # 모듈 실행
            spec.loader.exec_module(router_module)
            
            if hasattr(router_module, "router"):
                app.include_router(
                    router_module.router, 
                    prefix=f"/{module_name}",
                    tags=[module_name.replace("-", " ").title()]
                )
                print(f"✅ {module_name} 라우터가 통합되었습니다.")
                return True
            
            sys.path.remove(module_app_path)
            
    except Exception as e:
        print(f"⚠️ {module_name} 라우터 로드 실패: {e}")
    
    return False

def start_submodule_process(module_name, module_path):
    """서브모듈을 별도 프로세스로 실행 (백업 방식)"""
    try:
        main_file = os.path.join(module_path, "app", "main.py")
        if os.path.exists(main_file):
            # 서브모듈 실행
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=os.path.join(module_path, "app"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            submodule_processes.append((module_name, process))
            print(f"🚀 {module_name} 서브모듈 프로세스 시작됨 (PID: {process.pid})")
            return True
    except Exception as e:
        print(f"❌ {module_name} 서브모듈 프로세스 시작 실패: {e}")
    
    return False

def register_modules():
    """모듈들을 통합 등록 - 라우터 통합 우선, 실패시 별도 프로세스"""
    modules_dir = os.path.join(project_root, "modules")
    
    if not os.path.exists(modules_dir):
        print("⚠️ modules 디렉토리가 없습니다.")
        return
    
    print("🔄 서브모듈들을 통합 로드 중...")
    
    for module_name in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module_name)
        
        if os.path.isdir(module_path) and module_name != "auto-trader":
            print(f"📦 {module_name} 모듈 처리 중...")
            
            # 1단계: 라우터 직접 통합 시도
            if load_submodule_router(module_name, module_path):
                continue
            
            # 2단계: 별도 프로세스로 실행 (백업)
            print(f"🔄 {module_name} 별도 프로세스로 실행 시도...")
            start_submodule_process(module_name, module_path)

def cleanup_submodules():
    """서브모듈 프로세스들 정리"""
    print("🛑 서브모듈 프로세스들 종료 중...")
    for module_name, process in submodule_processes:
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"✅ {module_name} 프로세스 종료됨")
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"⚠️ {module_name} 프로세스 강제 종료됨")
        except Exception as e:
            print(f"❌ {module_name} 종료 오류: {e}")

# 시그널 핸들러 등록
def signal_handler(signum, frame):
    cleanup_submodules()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 정적 파일 서빙 (웹 앱)
web_dir = os.path.join(os.path.dirname(current_dir), "web", "dist")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

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
            "integrated_modules": len([name for name in os.listdir(os.path.join(project_root, "modules")) 
                                     if os.path.isdir(os.path.join(project_root, "modules", name)) 
                                     and name != "auto-trader"]) if os.path.exists(os.path.join(project_root, "modules")) else 0
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
        "subprocesses": len(submodule_processes)
    }

# 시작시 모듈 등록
print("🏠 Home Server 통합 시스템 시작 중...")
register_modules()
print(f"✅ 모든 모듈 로딩 완료!")

if __name__ == "__main__":
    try:
        print("🌐 통합 FastAPI 서버 시작 (포트: 5000)")
        print("📋 모든 서브모듈이 통합되어 실행됩니다.")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            log_level="info"
        )
    finally:
        cleanup_submodules()