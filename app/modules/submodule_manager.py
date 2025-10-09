"""
서브모듈 로딩 및 관리
"""

import os
import sys
import importlib.util
import asyncio
import subprocess
import signal
from typing import List, Tuple
from fastapi import FastAPI

class SubmoduleManager:
    """서브모듈 관리 클래스"""
    
    def __init__(self, app: FastAPI, project_root: str):
        self.app = app
        self.project_root = project_root
        self.submodule_processes: List[Tuple[str, subprocess.Popen]] = []
        self.loaded_modules: List[str] = []
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def load_submodule(self, module_name: str, module_path: str) -> bool:
        """서브모듈의 sub_main.py를 로드하여 라우터와 백그라운드 태스크 등록"""
        try:
            # sub_main.py 파일 확인
            sub_main_file = os.path.join(module_path, "app", "sub_main.py")
            if not os.path.exists(sub_main_file):
                print(f"⚠️ {module_name}/app/sub_main.py 파일이 없습니다.")
                return False
                
            # 모듈 스펙 생성
            spec = importlib.util.spec_from_file_location(f"{module_name}_sub_main", sub_main_file)
            sub_main_module = importlib.util.module_from_spec(spec)
            
            # 모듈의 sys.path에 추가
            module_app_path = os.path.join(module_path, "app")
            if module_app_path not in sys.path:
                sys.path.insert(0, module_app_path)
            
            # 모듈 실행
            spec.loader.exec_module(sub_main_module)
            
            # 라우터 등록
            if hasattr(sub_main_module, "get_router"):
                router = sub_main_module.get_router()
                if router:
                    self.app.include_router(
                        router, 
                        prefix=f"/{module_name}",
                        tags=[module_name.replace("-", " ").title()]
                    )
                    print(f"✅ {module_name} 라우터가 통합되었습니다.")
            
            # 백그라운드 태스크 시작
            if hasattr(sub_main_module, "start_background_tasks"):
                try:
                    asyncio.create_task(sub_main_module.start_background_tasks())
                    print(f"✅ {module_name} 백그라운드 태스크가 시작되었습니다.")
                except Exception as e:
                    print(f"⚠️ {module_name} 백그라운드 태스크 시작 실패: {e}")
            
            self.loaded_modules.append(module_name)
            return True
                
        except Exception as e:
            print(f"❌ {module_name} 서브모듈 로드 실패: {e}")
            return False
    
    def start_submodule_process(self, module_name: str, module_path: str) -> bool:
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
                self.submodule_processes.append((module_name, process))
                print(f"🚀 {module_name} 서브모듈 프로세스 시작됨 (PID: {process.pid})")
                return True
        except Exception as e:
            print(f"❌ {module_name} 서브모듈 프로세스 시작 실패: {e}")
        
        return False
    
    def register_all_modules(self):
        """모든 모듈을 통합 등록 - sub_main.py 우선, 실패시 별도 프로세스"""
        modules_dir = os.path.join(self.project_root, "modules")
        
        if not os.path.exists(modules_dir):
            print("⚠️ modules 디렉토리가 없습니다.")
            return
        
        print("🔄 서브모듈들을 통합 로드 중...")
        
        for module_name in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module_name)
            
            if os.path.isdir(module_path) and module_name != "auto-trader":
                print(f"📦 {module_name} 모듈 처리 중...")
                
                # 1단계: sub_main.py 통합 시도
                if self.load_submodule(module_name, module_path):
                    continue
                
                # 2단계: 별도 프로세스로 실행 (백업)
                print(f"🔄 {module_name} 별도 프로세스로 실행 시도...")
                self.start_submodule_process(module_name, module_path)
    
    def cleanup_submodules(self):
        """서브모듈 프로세스들 정리"""
        print("🛑 서브모듈 프로세스들 종료 중...")
        for module_name, process in self.submodule_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {module_name} 프로세스 종료됨")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️ {module_name} 프로세스 강제 종료됨")
            except Exception as e:
                print(f"❌ {module_name} 종료 오류: {e}")
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.cleanup_submodules()
        sys.exit(0)
    
    def get_status(self) -> dict:
        """서브모듈 상태 반환"""
        return {
            "loaded_modules": self.loaded_modules,
            "running_processes": len(self.submodule_processes),
            "total_modules": len(self.loaded_modules) + len(self.submodule_processes)
        }