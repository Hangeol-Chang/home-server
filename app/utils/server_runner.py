"""
서버 시작 및 실행 관리
"""

import uvicorn
import os
import sys
from fastapi import FastAPI

class ServerRunner:
    """서버 실행 관리 클래스"""
    
    def __init__(self, app: FastAPI, submodule_manager):
        self.app = app
        self.submodule_manager = submodule_manager
    
    def run_development_server(self, host: str = "0.0.0.0", port: int = 5000):
        """개발용 서버 실행"""
        try:
            print("🌐 통합 FastAPI 서버 시작 (포트: {})".format(port))
            print("📋 모든 서브모듈이 통합되어 실행됩니다.")
            print("📖 API 문서: http://{}:{}/docs".format(host, port))
            print("💚 헬스체크: http://{}:{}/health".format(host, port))
            
            uvicorn.run(
                "main:app",
                host=host,
                port=port,
                reload=True,
                log_level="info",
                reload_excludes=["*.pyc", "__pycache__"]
            )
        except KeyboardInterrupt:
            print("\n🛑 서버 종료 요청을 받았습니다.")
        except Exception as e:
            print(f"❌ 서버 실행 오류: {e}")
        finally:
            self.cleanup()
    
    def run_production_server(self, host: str = "0.0.0.0", port: int = 5000):
        """프로덕션용 서버 실행"""
        try:
            print("🚀 프로덕션 FastAPI 서버 시작")
            
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="warning",
                access_log=False
            )
        except Exception as e:
            print(f"❌ 프로덕션 서버 실행 오류: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """서버 종료 시 정리 작업"""
        if self.submodule_manager:
            self.submodule_manager.cleanup_submodules()
        print("✅ 서버 종료 완료")

def get_server_config():
    """환경 변수에서 서버 설정 읽기"""
    return {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", 5000)),
        "debug": os.getenv("DEBUG", "true").lower() == "true"
    }