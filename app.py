"""
Home Server Main Application

Flask 기반의 메인 서버로, modules 디렉토리 안의 각 모듈들을 통합 관리합니다.
각 모듈은 sub_app.py를 통해 자체 라우트와 프로세스를 관리합니다.
"""

import os
import sys
import logging
import threading
import importlib
from pathlib import Path
from flask import Flask, jsonify, request
from werkzeug.exceptions import NotFound

# 현재 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'home-server-secret-key'

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 모듈별 서브 앱들을 저장할 딕셔너리
sub_apps = {}
module_processes = {}

def setup_logging():
    """로깅 설정"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 파일 핸들러 추가
    file_handler = logging.FileHandler(log_dir / "home_server.log", encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

def discover_and_load_modules():
    """modules 디렉토리에서 모듈들을 발견하고 로드"""
    modules_dir = Path(current_dir) / "modules"
    
    if not modules_dir.exists():
        logger.warning("modules 디렉토리가 존재하지 않습니다: %s", modules_dir)
        return
    
    for module_path in modules_dir.iterdir():
        if module_path.is_dir() and not module_path.name.startswith('.'):
            module_name = module_path.name
            sub_app_file = module_path / "sub_app.py"
            
            if sub_app_file.exists():
                try:
                    logger.info("모듈 로드 중: %s", module_name)
                    load_module(module_name, module_path)
                except Exception as e:
                    logger.error("모듈 로드 실패 %s: %s", module_name, e)
            else:
                logger.info("sub_app.py가 없어 스킵: %s", module_name)

def load_module(module_name, module_path):
    """개별 모듈을 로드하고 라우트를 등록"""
    try:
        # 모듈의 디렉토리를 Python path에 추가
        sys.path.insert(0, str(module_path))
        
        # sub_app 모듈 import
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            f"{module_name}_sub_app", 
            module_path / "sub_app.py"
        )
        sub_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sub_app_module)
        
        # 서브 앱 인스턴스 가져오기
        if hasattr(sub_app_module, 'sub_app'):
            sub_app_instance = sub_app_module.sub_app
            sub_apps[module_name] = sub_app_instance
            
            # 라우트를 메인 앱에 등록
            register_module_routes(module_name, sub_app_instance)
            
            # 모듈의 백그라운드 프로세스 시작
            if hasattr(sub_app_module, 'start_background_processes'):
                start_module_processes(module_name, sub_app_module.start_background_processes)
            
            logger.info("모듈 '%s' 성공적으로 로드됨", module_name)
        else:
            logger.error("모듈 '%s'에 sub_app 인스턴스가 없습니다", module_name)
            
    except Exception as e:
        logger.error("모듈 '%s' 로드 중 오류: %s", module_name, e)
        raise

def register_module_routes(module_name, sub_app_instance):
    """모듈의 라우트들을 메인 앱에 등록"""
    try:
        # Flask 앱의 URL 맵에서 라우트들을 가져와서 등록
        for rule in sub_app_instance.url_map.iter_rules():
            if rule.endpoint != 'static':  # static 파일 라우트는 제외
                # 모듈 이름을 prefix로 사용
                new_rule = f"/{module_name}{rule.rule}"
                
                # view function 가져오기
                view_func = sub_app_instance.view_functions[rule.endpoint]
                
                # 메인 앱에 라우트 등록
                app.add_url_rule(
                    new_rule,
                    endpoint=f"{module_name}_{rule.endpoint}",
                    view_func=view_func,
                    methods=list(rule.methods)
                )
                
                logger.debug("라우트 등록: %s -> %s", new_rule, rule.endpoint)
                
    except Exception as e:
        logger.error("모듈 '%s' 라우트 등록 중 오류: %s", module_name, e)

def start_module_processes(module_name, start_function):
    """모듈의 백그라운드 프로세스를 시작"""
    try:
        def run_process():
            try:
                logger.info("모듈 '%s' 백그라운드 프로세스 시작", module_name)
                start_function()
            except Exception as e:
                logger.error("모듈 '%s' 프로세스 오류: %s", module_name, e)
        
        process_thread = threading.Thread(target=run_process, daemon=True)
        process_thread.name = f"Process-{module_name}"
        process_thread.start()
        
        module_processes[module_name] = process_thread
        logger.info("모듈 '%s' 프로세스 스레드 시작됨", module_name)
        
    except Exception as e:
        logger.error("모듈 '%s' 프로세스 시작 실패: %s", module_name, e)

# 메인 앱 라우트들
@app.route('/')
def index():
    """홈 페이지"""
    return jsonify({
        "status": "ok",
        "message": "Home Server is running",
        "loaded_modules": list(sub_apps.keys()),
        "active_processes": [name for name, thread in module_processes.items() if thread.is_alive()]
    })

@app.route('/health')
def health():
    """헬스 체크"""
    module_status = {}
    for module_name, thread in module_processes.items():
        module_status[module_name] = {
            "process_alive": thread.is_alive(),
            "routes_loaded": module_name in sub_apps
        }
    
    return jsonify({
        "status": "up",
        "modules": module_status,
        "total_modules": len(sub_apps)
    })

@app.route('/modules')
def list_modules():
    """로드된 모듈 목록"""
    module_info = {}
    
    for module_name, sub_app_instance in sub_apps.items():
        routes = []
        for rule in sub_app_instance.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    "path": f"/{module_name}{rule.rule}",
                    "methods": list(rule.methods),
                    "endpoint": rule.endpoint
                })
        
        module_info[module_name] = {
            "routes": routes,
            "process_status": module_processes.get(module_name, {}).is_alive() if module_name in module_processes else "No process"
        }
    
    return jsonify({
        "status": "ok",
        "modules": module_info
    })

@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        "status": "error", 
        "message": "Endpoint not found",
        "available_modules": list(sub_apps.keys()),
        "help": "Use /modules to see available routes"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error("Internal server error: %s", error)
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

def shutdown_all_processes():
    """모든 모듈 프로세스 종료"""
    logger.info("모든 모듈 프로세스 종료 중...")
    
    for module_name, thread in module_processes.items():
        if thread.is_alive():
            logger.info("모듈 '%s' 프로세스 종료 대기 중...", module_name)
            # 데몬 스레드이므로 메인 프로세스 종료 시 자동으로 종료됨

if __name__ == '__main__':
    try:
        setup_logging()
        logger.info("Home Server 시작 중...")
        
        # 모듈들 로드
        discover_and_load_modules()
        
        logger.info("Home Server 준비 완료. 포트 5000에서 실행 중...")
        
        # Flask 서버 실행
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False  # 모듈 로딩 중복 방지
        )
        
    except KeyboardInterrupt:
        logger.info("서버 종료 신호 받음")
        shutdown_all_processes()
    except Exception as e:
        logger.error("서버 시작 실패: %s", e)
        shutdown_all_processes()
        sys.exit(1)
