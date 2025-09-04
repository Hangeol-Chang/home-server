"""
Google OAuth Authentication Module

Flask 기반 홈 서버를 위한 Google OAuth 인증 기능을 제공합니다.
허용된 Gmail 주소로만 접근을 제한합니다.
"""

import os
import json
import logging
from functools import wraps
from flask import session, request, redirect, url_for, jsonify, render_template_string
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# 개발 환경에서 HTTP 허용 (프로덕션에서는 제거해야 함)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

logger = logging.getLogger(__name__)

class GoogleAuthManager:
    def __init__(self, app, config_dir):
        self.app = app
        self.config_dir = config_dir
        self.client_secrets_file = os.path.join(config_dir, 'config', 'google_oauth.json')
        self.allowed_emails_file = os.path.join(config_dir, 'config', 'allowed_emails.json')

        # OAuth 스코프 설정 (Google 공식 권장 스코프)
        self.scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            'openid'
        ]

        # 환경 변수 또는 설정에서 redirect URI 가져오기
        self.base_url = os.environ.get('HOME_SERVER_BASE_URL', 'http://localhost:5000')
        self.redirect_uri = f"{self.base_url}/auth/callback"
        
        self.setup_routes()
    
    def load_allowed_emails(self):
        """허용된 이메일 목록 로드"""
        try:
            with open(self.allowed_emails_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('allowed_emails', [])
        except FileNotFoundError:
            logger.error(f"Allowed emails file not found: {self.allowed_emails_file}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in allowed emails file: {self.allowed_emails_file}")
            return []
    
    def load_oauth_config(self):
        """Google OAuth 설정 로드"""
        try:
            with open(self.client_secrets_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # OAuth v2 엔드포인트로 변경
                if 'web' in config:
                    config['web']['auth_uri'] = 'https://accounts.google.com/o/oauth2/v2/auth'
                
                return config
        except FileNotFoundError:
            logger.error(f"OAuth config file not found: {self.client_secrets_file}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in OAuth config file: {self.client_secrets_file}")
            return None
    
    def is_authenticated(self):
        """현재 사용자의 인증 상태 확인"""
        return 'user_email' in session and session.get('authenticated', False)
    
    def is_email_allowed(self, email):
        """이메일이 허용된 목록에 있는지 확인"""
        allowed_emails = self.load_allowed_emails()
        return email in allowed_emails
    
    def get_current_user_email(self):
        """현재 로그인한 사용자의 이메일 반환"""
        return session.get('user_email')
    
    def setup_routes(self):
        """OAuth 관련 라우트 설정"""
        
        @self.app.route('/auth/login')
        def login():
            """Google OAuth 로그인 시작"""
            oauth_config = self.load_oauth_config()
            if not oauth_config:
                return jsonify({'error': 'OAuth configuration not found'}), 500
            
            try:
                # Google OAuth 공식 예제 방식으로 Flow 생성
                flow = Flow.from_client_config(
                    oauth_config,
                    scopes=[
                        "https://www.googleapis.com/auth/userinfo.email",
                        "https://www.googleapis.com/auth/userinfo.profile",
                        'openid'
                    ],
                )
                
                # Required, redirect URI 설정 (정확히 일치해야 함)
                flow.redirect_uri = self.redirect_uri
                
                logger.info(f"OAuth redirect_uri: {self.redirect_uri}")
                logger.info(f"Configured redirect_uris: {oauth_config.get('web', {}).get('redirect_uris', [])}")
                
                # Generate URL for request to Google's OAuth 2.0 server
                authorization_url, state = flow.authorization_url(
                    # Recommended, enable offline access so that you can refresh an access token without
                    # re-prompting the user for permission. Recommended for web server apps.
                    access_type='offline',
                    # Optional, enable incremental authorization. Recommended as a best practice.
                    include_granted_scopes='true',
                    # Optional, set prompt to 'consent' will prompt the user for consent
                    prompt='consent'
                )
                
                session['state'] = state
                
                print('uri : ', authorization_url)
                return redirect(authorization_url)
            
            except Exception as e:
                logger.error(f"OAuth login error: {e}")
                return jsonify({'error': f'OAuth login failed: {str(e)}'}), 500
        
        @self.app.route('/auth/callback')
        def auth_callback():
            """Google OAuth 콜백 처리"""
            oauth_config = self.load_oauth_config()
            if not oauth_config:
                return jsonify({'error': 'OAuth configuration not found'}), 500
            
            try:
                # Google OAuth 공식 예제 방식으로 Flow 생성
                flow = Flow.from_client_config(
                    oauth_config,
                    scopes=[
                        "https://www.googleapis.com/auth/userinfo.email",
                        "https://www.googleapis.com/auth/userinfo.profile",
                        'openid'
                    ],
                    state=session['state']
                )
                flow.redirect_uri = self.redirect_uri
                
                logger.info(f"OAuth callback redirect_uri: {self.redirect_uri}")
                
                # Authorization code를 Access token으로 교환
                flow.fetch_token(authorization_response=request.url)
                
                credentials = flow.credentials
                
                # ID 토큰에서 사용자 정보 추출 (가장 안전한 방법)
                id_token = credentials.id_token
                if id_token:
                    # ID 토큰 디코딩
                    import jwt
                    try:
                        # ID 토큰은 이미 Google에서 검증되었으므로 verify=False 사용
                        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
                        user_email = decoded_token.get('email')
                        user_name = decoded_token.get('name') or decoded_token.get('given_name', '') + ' ' + decoded_token.get('family_name', '')
                        user_name = user_name.strip()
                        
                        logger.info(f"ID token decoded successfully: {user_email}")
                        
                    except Exception as token_error:
                        logger.warning(f"ID token decode failed, using API fallback: {token_error}")
                        # API 폴백
                        service = build('oauth2', 'v2', credentials=credentials)
                        user_info = service.userinfo().get().execute()
                        user_email = user_info.get('email')
                        user_name = user_info.get('name')
                        
                else:
                    logger.warning("No ID token available, using API")
                    # API 폴백
                    service = build('oauth2', 'v2', credentials=credentials)
                    user_info = service.userinfo().get().execute()
                    user_email = user_info.get('email')
                    user_name = user_info.get('name')
                
                # 허용된 이메일인지 확인
                if not self.is_email_allowed(user_email):
                    logger.warning(f"Unauthorized email attempted login: {user_email}")
                    return render_template_string("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Access Denied</title>
                        <meta charset="utf-8">
                    </head>
                    <body>
                        <h1>접근 거부</h1>
                        <p>이 서버에 접근할 권한이 없습니다.</p>
                        <p>이메일: {{ email }}</p>
                        <a href="/">홈으로 돌아가기</a>
                    </body>
                    </html>
                    """, email=user_email), 403
                
                # 세션에 사용자 정보 저장
                session['user_email'] = user_email
                session['user_name'] = user_name
                session['authenticated'] = True
                
                logger.info(f"User authenticated successfully: {user_email}")
                return redirect('/')
            
            except Exception as e:
                logger.error(f"OAuth callback error: {e}")
                return jsonify({'error': 'Authentication failed'}), 500
        
        @self.app.route('/auth/logout')
        def logout():
            """로그아웃"""
            user_email = session.get('user_email', 'Unknown')
            session.clear()
            logger.info(f"User logged out: {user_email}")
            return redirect('/')
        
        @self.app.route('/auth/status')
        def auth_status():
            """현재 인증 상태 반환"""
            return jsonify({
                'authenticated': self.is_authenticated(),
                'user_email': self.get_current_user_email(),
                'user_name': session.get('user_name')
            })

def require_auth(f):
    """인증이 필요한 라우트에 사용할 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # OAuth 관리자 인스턴스 가져오기
        from flask import current_app
        auth_manager = getattr(current_app, 'auth_manager', None)
        
        if not auth_manager or not auth_manager.is_authenticated():
            if request.is_json:
                return jsonify({'error': 'Authentication required', 'redirect': '/auth/login'}), 401
            else:
                return redirect('/auth/login')
        
        return f(*args, **kwargs)
    return decorated_function

def get_login_page_template():
    """로그인 페이지 HTML 템플릿"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Home Server - Login</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 400px;
                margin: 100px auto;
                padding: 20px;
                text-align: center;
                background-color: #f5f5f5;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .login-btn {
                background-color: #4285f4;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
            .login-btn:hover {
                background-color: #3367d6;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            p {
                color: #666;
                margin-bottom: 30px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>🏠 Home Server</h1>
            <p>Google 계정으로 로그인해주세요</p>
            <a href="/auth/login" class="login-btn">
                🔐 Google로 로그인
            </a>
        </div>
    </body>
    </html>
    """
