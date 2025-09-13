# Home Server

Flask 기반의 모듈화된 홈 서버 프로젝트입니다. 각 모듈은 독립적으로 개발되며, 메인 서버가 이들을 통합 관리합니다.

## 📁 프로젝트 구조

```
home-server/
├── server/
│   ├── app.py                 # 메인 Flask 서버
│   ├── requirements.txt       # 메인 서버 의존성
│   ├── install_req.py         # 통합 패키지 설치 스크립트
│   ├── start_server.sh        # 서버 시작 스크립트
│   ├── logs/                  # 로그 파일들
│   ├── venv/                  # 가상환경 (설치 후 생성됨)
│   └── modules/               # 서브 모듈들
│       ├── auto-trader/       # 자동 트레이딩 모듈
│       │   ├── sub_app.py     # 서브 앱 진입점
│       │   ├── requirements.txt
│       │   ├── main.py        # 기존 독립 실행 파일
│       │   ├── core/          # 핵심 기능들
│       │   ├── module/        # 비즈니스 로직들
│       │   └── ...
│       └── asset-manager/     # 자산 관리 모듈 (예정)
```

## 🚀 빠른 시작

### 1. Google OAuth 설정 (필수)

Home Server는 Google OAuth 인증을 통해 허용된 Gmail 계정만 접근할 수 있습니다.

#### 1.1 설정 파일 준비
```bash
# 설정 파일 템플릿 복사
cp config/google_oauth.json.example config/google_oauth.json
cp config/allowed_emails.json.example config/allowed_emails.json
```

#### 1.2 Google Cloud Console 설정
자세한 설정 방법은 [`GOOGLE_OAUTH_SETUP.md`](./GOOGLE_OAUTH_SETUP.md)를 참조하세요.

#### 1.3 설정 테스트
```bash
# OAuth 설정 확인
./test_oauth_setup.sh
```

### 2. 환경 설정 및 패키지 설치

```bash
# 모든 모듈의 requirements.txt를 가상환경에 설치
python3 install_req.py --venv

# 또는 기존 환경에 설치 (권장하지 않음)
python3 install_req.py
```

### 3. 서버 실행

#### 방법 1: 시작 스크립트 사용 (권장)
```bash
./start_server.sh
```

#### 방법 2: 수동 실행
```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 실행
python3 app.py
```

### 4. 서버 확인

```bash
# 메인 페이지 확인 (브라우저 접속 권장)
curl http://localhost:5000/

# 인증 후 API 접근 (브라우저에서 로그인 후)
curl -b cookies.txt http://localhost:5000/health
curl -b cookies.txt http://localhost:5000/modules
```

**⚠️ 주의:** 웹 브라우저에서 `http://localhost:5000`에 접속하여 Google 계정으로 로그인해야 합니다.

## 📚 API 엔드포인트

### 인증 관련 엔드포인트

| 경로 | 메소드 | 설명 |
|------|--------|------|
| `/` | GET | 메인 대시보드 (인증 필요) |
| `/auth/login` | GET | Google OAuth 로그인 |
| `/auth/logout` | GET | 로그아웃 |
| `/auth/callback` | GET | OAuth 콜백 (자동 처리) |
| `/auth/status` | GET | 인증 상태 확인 |

### 메인 서버 엔드포인트 (모두 인증 필요)

| 경로 | 메소드 | 설명 |
|------|--------|------|
| `/health` | GET | 헬스 체크 |
| `/modules` | GET | 로드된 모듈과 라우트 목록 |

### Auto-trader 모듈 엔드포인트 (모두 인증 필요)

모든 auto-trader 엔드포인트는 `/auto-trader` 프리픽스가 붙습니다.

| 경로 | 메소드 | 설명 |
|------|--------|------|
| `/auto-trader/health` | GET | 모듈 헬스 체크 |
| `/auto-trader/status` | GET | 트레이더 상태 정보 |
| `/auto-trader/ta-signal` | POST | TradingView 웹훅 수신 |
| `/auto-trader/ta-signal-test` | POST | 테스트용 웹훅 |
| `/auto-trader/test-balance` | GET | 업비트 잔고 조회 테스트 |
| `/auto-trader/markets` | GET | 지원 마켓 목록 |
| `/auto-trader/trading-config` | GET | 매매 설정 조회 |
| `/auto-trader/control/stop` | GET | 트레이더 중지 |

## 🔧 모듈 개발 가이드

### 새로운 모듈 추가하기

1. `modules/` 디렉토리에 새 모듈 폴더 생성
2. `sub_app.py` 파일 생성 (필수)
3. `requirements.txt` 파일 생성 (선택)

### sub_app.py 구조

```python
from flask import Flask

# Flask 서브 앱 생성
sub_app = Flask(__name__)

# 라우트 정의
@sub_app.route('/hello')
def hello():
    return {"message": "Hello from my module!"}

# 백그라운드 프로세스가 필요한 경우
def start_background_processes():
    # 백그라운드 작업 구현
    pass
```

### 요구사항

- `sub_app` 변수로 Flask 앱 인스턴스 제공 (필수)
- `start_background_processes()` 함수 제공 (선택, 백그라운드 작업이 필요한 경우)

## 📝 로그

로그 파일들은 `logs/` 디렉토리에 저장됩니다:

- `home_server.log` - 메인 서버 로그
- `auto_trader.log` - Auto-trader 모듈 로그

## 🛠️ 개발 도구

### install_req.py 옵션

```bash
# 가상환경 생성 및 패키지 설치
python3 install_req.py --venv

# 특정 이름의 가상환경 사용
python3 install_req.py --venv-name myenv

# 패키지 업그레이드
python3 install_req.py --venv --upgrade

# 도움말
python3 install_req.py --help
```

## 🔍 문제 해결

### 자주 발생하는 문제들

1. **모듈 import 오류**
   - 각 모듈의 requirements.txt가 올바른지 확인
   - 가상환경이 활성화되었는지 확인

2. **포트 충돌**
   - 기본 포트 5000이 사용 중인 경우, `app.py`에서 포트 변경

3. **권한 문제**
   - 스크립트들이 실행 권한을 가지고 있는지 확인: `chmod +x *.sh`

### 로그 확인

```bash
# 실시간 로그 모니터링
tail -f logs/home_server.log
tail -f logs/auto_trader.log

# 전체 로그 확인
cat logs/home_server.log
```

## 🤝 기여하기

1. 새로운 모듈을 개발할 때는 `modules/` 디렉토리에 추가
2. 각 모듈은 독립적인 `requirements.txt`를 가져야 함
3. 로그는 모듈별로 분리하여 관리
4. API 엔드포인트는 RESTful 원칙을 따름

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.
