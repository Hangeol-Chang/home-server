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
from flask import Flask, jsonify, request, session, render_template, redirect
from werkzeug.exceptions import NotFound
from jinja2 import ChoiceLoader, FileSystemLoader

# 현재 디렉토리와 프로젝트 루트를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # home-server 루트 디렉토리
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

app = Flask(__name__, 
            static_folder='web/static',
            template_folder='web/templates')
app.config['SECRET_KEY'] = 'home-server-secret-key-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = 24 * 60 * 60  # 24시간

# 개발 모드 설정 - 템플릿 자동 리로딩
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# 템플릿 로더 설정 - 메인 템플릿 폴더를 기본으로 설정
main_template_loader = FileSystemLoader(os.path.join(current_dir, 'web', 'templates'))
app.jinja_loader = ChoiceLoader([main_template_loader])

# Google OAuth 인증 관리자 초기화
from auth.google_auth import GoogleAuthManager, require_auth
auth_manager = GoogleAuthManager(app, current_dir)
app.auth_manager = auth_manager  # 전역 접근을 위해 앱에 등록

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 모듈별 서브 앱들을 저장할 딕셔너리
sub_apps = {}
module_processes = {}

@app.context_processor
def inject_user_info():
    """모든 템플릿에 사용자 정보와 로드된 모듈 정보 주입"""
    # 로드된 모듈들 정보 생성
    loaded_modules = []
    for module_name, module_data in module_processes.items():
        if module_data.get('active', False):
            # 모듈명을 기반으로 한국어 이름과 이모지 매핑
            module_info = {
                'name': module_name,
                'url': f'/{module_name}/',
                'display_name': get_module_display_name(module_name),
                'emoji': get_module_emoji(module_name)
            }
            loaded_modules.append(module_info)
    
    # 사용자 인증 정보
    user_data = {}
    if auth_manager.is_authenticated():
        user_data = {
            'user_email': auth_manager.get_current_user_email(),
            'user_name': session.get('user_name', 'Unknown'),
            'is_authenticated': True
        }
    else:
        user_data = {
            'user_email': None,
            'user_name': None,
            'is_authenticated': False
        }
    
    # 모든 데이터 결합
    user_data['loaded_modules'] = loaded_modules
    return user_data

def get_module_display_name(module_name):
    """모듈명을 한국어 표시명으로 변환"""
    display_names = {
        'auto-trader': 'Auto Trader',
        'asset-manager': '자산관리',
        'schedule-manager': '일정관리',
        'file-manager': '파일관리',
        'note-manager': '노트관리'
    }
    return display_names.get(module_name, module_name.replace('-', ' ').title())

def get_module_emoji(module_name):
    """모듈명에 따른 이모지 반환"""
    emojis = {
        'auto-trader': '🚀',
        'asset-manager': '💰',
        'schedule-manager': '📅',
        'file-manager': '📁',
        'note-manager': '📝'
    }
    return emojis.get(module_name, '📦')

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

def add_template_folder_for_module(module_path):
    """모듈의 템플릿 폴더를 전역 템플릿 로더에 추가"""
    template_folder = module_path / "web" / "templates"
    if template_folder.exists():
        # 새로운 FileSystemLoader 생성
        module_loader = FileSystemLoader(str(template_folder))
        # 기존 로더 리스트에 추가
        current_loaders = list(app.jinja_loader.loaders)
        current_loaders.append(module_loader)
        app.jinja_loader = ChoiceLoader(current_loaders)
        logger.info("템플릿 폴더 추가됨: %s", template_folder)

def discover_and_load_modules():
    """modules 디렉토리에서 모듈들을 발견하고 로드"""
    modules_dir = Path(current_dir).parent / "modules"
    
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
            
            # 모듈의 템플릿 폴더를 전역 템플릿 로더에 추가
            add_template_folder_for_module(module_path)
            
            # 라우트를 메인 앱에 등록
            register_module_routes(module_name, sub_app_instance)
            
            # 모듈을 활성 프로세스로 등록 (Blueprint는 항상 활성 상태)
            if hasattr(sub_app_instance, 'name'):  # Blueprint인 경우
                module_processes[module_name] = {'type': 'blueprint', 'active': True}
            else:
                module_processes[module_name] = {'type': 'flask_app', 'active': True}
            
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
    """모듈의 Blueprint를 메인 앱에 등록 (인증 적용)"""
    try:
        # Blueprint인 경우 직접 등록
        if hasattr(sub_app_instance, 'name'):  # Blueprint 확인
            # Blueprint를 메인 앱에 등록
            app.register_blueprint(sub_app_instance)
            logger.info("Blueprint '%s' 등록 완료", module_name)
            
            # 등록된 Blueprint의 모든 엔드포인트에 인증 적용
            for endpoint in app.view_functions:
                if endpoint.startswith(f'{sub_app_instance.name}.'):
                    original_func = app.view_functions[endpoint]
                    app.view_functions[endpoint] = require_auth(original_func)
                    
        else:
            # 기존 Flask 앱 방식 (하위 호환성)
            # Flask 앱의 URL 맵에서 라우트들을 가져와서 등록
            for rule in sub_app_instance.url_map.iter_rules():
                if rule.endpoint != 'static':  # static 파일 라우트는 제외
                    # 모듈 이름을 prefix로 사용
                    new_rule = f"/{module_name}{rule.rule}"
                    
                    # view function 가져오기
                    original_view_func = sub_app_instance.view_functions[rule.endpoint]
                    
                    # 인증이 필요한 view function으로 래핑
                    authenticated_view_func = require_auth(original_view_func)
                    
                    # 메인 앱에 라우트 등록
                    app.add_url_rule(
                        new_rule,
                        endpoint=f"{module_name}_{rule.endpoint}",
                        view_func=authenticated_view_func,
                        methods=list(rule.methods)
                    )
                    
                    logger.debug("라우트 등록 (인증 적용): %s -> %s", new_rule, rule.endpoint)
                
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
        
        # 기존 모듈 정보 업데이트 (백그라운드 프로세스 추가)
        if module_name in module_processes:
            module_processes[module_name]['background_thread'] = process_thread
        else:
            module_processes[module_name] = {'type': 'background_process', 'active': True, 'background_thread': process_thread}
            
        logger.info("모듈 '%s' 프로세스 스레드 시작됨", module_name)
        
    except Exception as e:
        logger.error("모듈 '%s' 프로세스 시작 실패: %s", module_name, e)

# 메인 앱 라우트들
@app.route('/')
def index():
    """홈 페이지 - 인증 필요"""
    if not auth_manager.is_authenticated():
        return render_template('login.html')
    
    user_email = auth_manager.get_current_user_email()
    user_name = session.get('user_name', 'Unknown')
    
    return render_template('index.html', 
                          user_name=user_name,
                          user_email=user_email,
                          modules=list(sub_apps.keys()),
                          active_processes=[name for name, info in module_processes.items() 
                                          if isinstance(info, dict) and info.get('active', False)])

@app.route('/health')
@require_auth
def health():
    """헬스 체크 - 인증 필요"""
    module_status = {}
    for module_name, module_data in module_processes.items():
        # 백그라운드 스레드가 있는 경우에만 is_alive() 확인
        process_alive = False
        if isinstance(module_data, dict) and 'background_thread' in module_data:
            process_alive = module_data['background_thread'].is_alive()
        elif isinstance(module_data, dict):
            process_alive = module_data.get('active', False)
        
        module_status[module_name] = {
            "process_alive": process_alive,
            "routes_loaded": module_name in sub_apps
        }
    
    return jsonify({
        "status": "up",
        "modules": module_status,
        "total_modules": len(sub_apps),
        "authenticated_user": auth_manager.get_current_user_email()
    })

@app.route('/modules')
@require_auth
def list_modules():
    """로드된 모듈 목록 - 인증 필요"""
    module_info = {}
    
    for module_name, sub_app_instance in sub_apps.items():
        routes = []
        
        # Blueprint인 경우와 Flask 앱인 경우를 구분
        if hasattr(sub_app_instance, 'name'):  # Blueprint인 경우
            # 메인 앱에서 해당 Blueprint의 라우트들을 찾기
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith(f'{sub_app_instance.name}.'):
                    routes.append({
                        "path": rule.rule,
                        "methods": list(rule.methods),
                        "endpoint": rule.endpoint
                    })
        else:  # Flask 앱인 경우 (하위 호환성)
            for rule in sub_app_instance.url_map.iter_rules():
                if rule.endpoint != 'static':
                    routes.append({
                        "path": f"/{module_name}{rule.rule}",
                        "methods": list(rule.methods),
                        "endpoint": rule.endpoint
                    })
        
        module_info[module_name] = {
            "routes": routes,
            "process_status": _get_module_process_status(module_name)
        }
    
    return jsonify({
        "status": "ok",
        "modules": module_info,
        "authenticated_user": auth_manager.get_current_user_email()
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
    
    for module_name, module_data in module_processes.items():
        if isinstance(module_data, dict) and 'background_thread' in module_data:
            thread = module_data['background_thread']
            if thread.is_alive():
                logger.info("모듈 '%s' 프로세스 종료 대기 중...", module_name)
                # 데몬 스레드이므로 메인 프로세스 종료 시 자동으로 종료됨

def _get_module_process_status(module_name):
    """모듈의 프로세스 상태를 반환하는 헬퍼 함수"""
    if module_name not in module_processes:
        return "No process"
    
    module_data = module_processes[module_name]
    if isinstance(module_data, dict):
        if 'background_thread' in module_data:
            return "Running" if module_data['background_thread'].is_alive() else "Stopped"
        else:
            return "Active (Blueprint)" if module_data.get('active', False) else "Inactive"
    
    return "Unknown status"

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
            debug=True,  # 개발 모드 활성화 - 템플릿 자동 리로드
            use_reloader=False  # 모듈 로딩 중복 방지
        )
        
    except KeyboardInterrupt:
        logger.info("서버 종료 신호 받음")
        shutdown_all_processes()
    except Exception as e:
        logger.error("서버 시작 실패: %s", e)
        shutdown_all_processes()
        sys.exit(1)
