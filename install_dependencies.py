#!/usr/bin/env python3
"""
Home Server Dependencies Installer

이 스크립트는 Home Server 프로젝트의 모든 의존성을 설치합니다.
- 가상환경 자동 생성 및 활성화
- 메인 서버 및 모든 모듈의 requirements.txt 자동 탐지 및 설치
- 설치 과정과 결과를 명확하게 표시

사용법:
    python3 install_dependencies.py              # 기본 설치 (venv 사용)
    python3 install_dependencies.py --no-venv    # 시스템 Python 사용 (권장하지 않음)
    python3 install_dependencies.py --upgrade    # 기존 패키지 업그레이드
    python3 install_dependencies.py --clean      # venv 초기화 후 재설치
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
import venv


class Colors:
    """터미널 색상 코드"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color
    
    @classmethod
    def disable(cls):
        """Windows 호환성을 위해 색상 비활성화"""
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.PURPLE = cls.CYAN = cls.WHITE = cls.NC = ''


def print_banner():
    """설치 프로그램 배너 출력"""
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.WHITE}🏠 Home Server Dependencies Installer{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
    print()


def print_step(step_num, title, description=""):
    """설치 단계 출력"""
    print(f"{Colors.BLUE}[{step_num}/5] {title}{Colors.NC}")
    if description:
        print(f"   {description}")
    print()


def print_success(message):
    """성공 메시지 출력"""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def print_warning(message):
    """경고 메시지 출력"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def print_error(message):
    """오류 메시지 출력"""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")


def print_info(message):
    """정보 메시지 출력"""
    print(f"{Colors.PURPLE}ℹ️  {message}{Colors.NC}")


def run_command(command, cwd=None, capture_output=True):
    """명령어 실행 및 결과 반환"""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
            return True, result.stdout, result.stderr
        else:
            # 실시간 출력용
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                check=True
            )
            return True, "", ""
    except subprocess.CalledProcessError as e:
        if capture_output:
            return False, e.stdout or "", e.stderr or ""
        else:
            return False, "", str(e)


def check_python_version():
    """Python 버전 확인"""
    print_step(1, "Python 환경 확인")
    
    python_version = sys.version_info
    print_info(f"Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_error("Python 3.8 이상이 필요합니다.")
        return False
    
    print_success("Python 버전 확인 완료")
    return True


def install_pipreqs_if_needed():
    """pipreqs가 설치되어 있지 않으면 설치"""
    try:
        # pipreqs가 설치되어 있는지 확인
        success, _, _ = run_command("pipreqs --version")
        if success:
            return True
        
        print_info("pipreqs 설치 중...")
        success, stdout, stderr = run_command("pip3 install pipreqs")
        if success:
            print_success("pipreqs 설치 완료")
            return True
        else:
            print_error(f"pipreqs 설치 실패: {stderr}")
            return False
    except Exception as e:
        print_error(f"pipreqs 설치 중 오류: {e}")
        return False


def generate_requirements_for_module(module_path, module_name, force=False):
    """특정 모듈에 대해 requirements.txt 생성"""
    req_file = module_path / "requirements.txt"
    
    # 기존 파일이 있고 force가 False인 경우 건너뛰기
    if req_file.exists() and not force:
        print_info(f"'{module_name}' 모듈에 이미 requirements.txt가 존재합니다 (건너뜀)")
        return True
    
    print_info(f"'{module_name}' 모듈의 requirements.txt 생성 중...")
    
    try:
        # pipreqs 실행
        command = f"pipreqs {module_path} --force"
        success, stdout, stderr = run_command(command)
        
        if success:
            print_success(f"'{module_name}' requirements.txt 생성 완료")
            
            # 생성된 파일에 주석 추가
            if req_file.exists():
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                header = f"# {module_name.title()} Module Dependencies\n# Auto-generated by pipreqs\n\n"
                with open(req_file, 'w', encoding='utf-8') as f:
                    f.write(header + content)
            
            return True
        else:
            print_warning(f"'{module_name}' requirements.txt 생성 실패: {stderr}")
            return False
            
    except Exception as e:
        print_error(f"'{module_name}' requirements.txt 생성 중 오류: {e}")
        return False


def generate_all_requirements(script_dir, force=False):
    """모든 모듈에 대해 requirements.txt 생성"""
    print_step(2, "Requirements.txt 자동 생성")
    
    # pipreqs 설치 확인
    if not install_pipreqs_if_needed():
        return False
    
    success_count = 0
    total_count = 0
    
    # 메인 프로젝트 requirements.txt 생성
    main_req = script_dir / "requirements.txt"
    if not main_req.exists() or force:
        print_info("메인 프로젝트 requirements.txt 생성 중...")
        try:
            command = f"pipreqs {script_dir} --force --ignore=modules,venv,.venv,logs,config"
            success, stdout, stderr = run_command(command)
            
            if success:
                print_success("메인 프로젝트 requirements.txt 생성 완료")
                
                # 헤더 추가
                if main_req.exists():
                    with open(main_req, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    header = "# Home Server Main Dependencies\n# Auto-generated by pipreqs\n\n"
                    with open(main_req, 'w', encoding='utf-8') as f:
                        f.write(header + content)
                
                success_count += 1
            else:
                print_warning(f"메인 프로젝트 requirements.txt 생성 실패: {stderr}")
        except Exception as e:
            print_error(f"메인 프로젝트 requirements.txt 생성 중 오류: {e}")
        
        total_count += 1
    
    # 모듈들의 requirements.txt 생성
    modules_dir = script_dir / "modules"
    if modules_dir.exists():
        for module_path in modules_dir.iterdir():
            if module_path.is_dir() and not module_path.name.startswith('.'):
                module_name = module_path.name
                total_count += 1
                
                if generate_requirements_for_module(module_path, module_name, force):
                    success_count += 1
    
    print(f"\n📊 Requirements.txt 생성 결과:")
    print(f"   - 총 프로젝트/모듈 수: {total_count}")
    print(f"   - 성공: {success_count}")
    print(f"   - 실패: {total_count - success_count}")
    
    if success_count > 0:
        print_success("Requirements.txt 파일들이 생성되었습니다!")
        print_info("생성된 파일들을 확인하고 필요시 수동으로 편집하세요.")
    
    return success_count > 0


def find_requirements_files(base_dir):
    """requirements.txt 파일들을 찾아서 반환"""
    requirements_files = []
    base_path = Path(base_dir)
    
    # 메인 디렉토리의 requirements.txt
    main_req = base_path / "requirements.txt"
    if main_req.exists():
        requirements_files.append(("main", main_req))
    
    # 모듈들의 requirements.txt
    modules_dir = base_path / "modules"
    if modules_dir.exists():
        for module_path in modules_dir.iterdir():
            if module_path.is_dir() and not module_path.name.startswith('.'):
                module_req = module_path / "requirements.txt"
                if module_req.exists():
                    requirements_files.append((module_path.name, module_req))
    
    return requirements_files


def setup_virtual_environment(venv_path, clean=False):
    """가상환경 설정"""
    print_step(2, "가상환경 설정")
    
    if clean and venv_path.exists():
        print_info(f"기존 가상환경 삭제 중: {venv_path}")
        shutil.rmtree(venv_path)
    
    if venv_path.exists():
        print_info(f"기존 가상환경 사용: {venv_path}")
    else:
        print_info(f"가상환경 생성 중: {venv_path}")
        try:
            venv.create(venv_path, with_pip=True)
            print_success("가상환경 생성 완료")
        except Exception as e:
            print_error(f"가상환경 생성 실패: {e}")
            return False
    
    return True


def get_venv_paths(venv_path):
    """가상환경의 Python과 pip 경로 반환"""
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:  # Unix/Linux/macOS
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
        activate_script = venv_path / "bin" / "activate"
    
    return python_path, pip_path, activate_script


def upgrade_pip(pip_path):
    """pip 업그레이드"""
    print_info("pip 업그레이드 중...")
    success, stdout, stderr = run_command(f'"{pip_path}" install --upgrade pip')
    if success:
        print_success("pip 업그레이드 완료")
    else:
        print_warning(f"pip 업그레이드 실패: {stderr}")
    return success


def install_requirements(pip_path, requirements_files, upgrade=False):
    """requirements.txt 파일들을 순서대로 설치"""
    print_step(3, "패키지 설치", f"총 {len(requirements_files)}개 파일")
    
    upgrade_flag = "--upgrade" if upgrade else ""
    success_count = 0
    
    for module_name, req_file in requirements_files:
        print(f"\n{Colors.CYAN}📦 모듈 '{module_name}' 설치 중...{Colors.NC}")
        print(f"   파일: {req_file}")
        
        command = f'"{pip_path}" install {upgrade_flag} -r "{req_file}"'
        success, stdout, stderr = run_command(command, capture_output=False)
        
        if success:
            print_success(f"'{module_name}' 설치 완료")
            success_count += 1
        else:
            print_error(f"'{module_name}' 설치 실패")
            if stderr:
                print(f"   오류: {stderr}")
    
    return success_count


def create_activation_scripts(script_dir, venv_path):
    """가상환경 활성화 스크립트 생성"""
    print_step(4, "활성화 스크립트 생성")
    
    # Unix/Linux/macOS 스크립트
    activate_sh = script_dir / "activate_venv.sh"
    with open(activate_sh, 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
# Home Server 가상환경 활성화 스크립트

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 가상환경이 존재하지 않습니다: $VENV_PATH"
    echo "먼저 python3 install_dependencies.py를 실행하세요."
    exit 1
fi

echo "🔄 Home Server 가상환경 활성화 중..."
source "$VENV_PATH/bin/activate"
echo "✅ 가상환경이 활성화되었습니다."
echo "서버 실행: python3 app.py"
echo "비활성화: deactivate"
""")
    
    # Windows 스크립트
    activate_bat = script_dir / "activate_venv.bat"
    with open(activate_bat, 'w', encoding='utf-8') as f:
        f.write(f"""@echo off
rem Home Server 가상환경 활성화 스크립트

set "SCRIPT_DIR=%~dp0"
set "VENV_PATH=%SCRIPT_DIR%venv"

if not exist "%VENV_PATH%" (
    echo ❌ 가상환경이 존재하지 않습니다: %VENV_PATH%
    echo 먼저 python install_dependencies.py를 실행하세요.
    pause
    exit /b 1
)

echo 🔄 Home Server 가상환경 활성화 중...
call "%VENV_PATH%\\Scripts\\activate.bat"
echo ✅ 가상환경이 활성화되었습니다.
echo 서버 실행: python app.py
echo 비활성화: deactivate
""")
    
    # 실행 권한 부여 (Unix 계열)
    if os.name != 'nt':
        os.chmod(activate_sh, 0o755)
    
    print_success("활성화 스크립트 생성 완료")
    print_info(f"Unix/Linux/macOS: ./activate_venv.sh")
    print_info(f"Windows: activate_venv.bat")


def display_results(script_dir, requirements_files, success_count, use_venv):
    """설치 결과 및 사용법 출력"""
    print_step(5, "설치 완료")
    
    print(f"📊 설치 결과:")
    print(f"   - 총 모듈 수: {len(requirements_files)}")
    print(f"   - 성공: {success_count}")
    print(f"   - 실패: {len(requirements_files) - success_count}")
    
    if success_count == len(requirements_files):
        print_success("모든 패키지가 성공적으로 설치되었습니다! 🎉")
    else:
        print_warning(f"{len(requirements_files) - success_count}개 모듈에서 설치 실패")
    
    print(f"\n{Colors.WHITE}🚀 서버 실행 방법:{Colors.NC}")
    
    if use_venv:
        if os.name == 'nt':  # Windows
            print(f"   1. activate_venv.bat")
            print(f"   2. python app.py")
        else:  # Unix/Linux/macOS
            print(f"   1. ./activate_venv.sh")
            print(f"   2. python3 app.py")
        
        print(f"\n또는 start_server.sh 스크립트 사용:")
        print(f"   ./start_server.sh")
    else:
        print(f"   python3 app.py")
    
    print(f"\n{Colors.WHITE}📖 추가 정보:{Colors.NC}")
    print(f"   - 서버 주소: http://localhost:5000")
    print(f"   - 로그 파일: logs/home_server.log")
    print(f"   - 설정 파일: config/")


def main():
    """메인 실행 함수"""
    # Windows에서 색상 지원 확인
    if os.name == 'nt':
        try:
            # Windows 10+에서 ANSI 색상 지원 활성화
            import subprocess
            subprocess.run("", shell=True)
        except:
            Colors.disable()
    
    parser = argparse.ArgumentParser(
        description='Home Server Dependencies Installer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python3 install_dependencies.py                      # 기본 설치 (venv 사용)
  python3 install_dependencies.py --no-venv            # 시스템 Python 사용
  python3 install_dependencies.py --upgrade            # 패키지 업그레이드
  python3 install_dependencies.py --clean              # venv 초기화 후 재설치
  python3 install_dependencies.py --generate-requirements  # requirements.txt 자동 생성
  python3 install_dependencies.py --generate-requirements --force-generate  # 강제 재생성
        """
    )
    
    parser.add_argument('--no-venv', action='store_true',
                       help='가상환경을 사용하지 않고 시스템 Python에 설치 (권장하지 않음)')
    parser.add_argument('--upgrade', action='store_true',
                       help='기존 패키지를 최신 버전으로 업그레이드')
    parser.add_argument('--clean', action='store_true',
                       help='기존 가상환경을 삭제하고 새로 생성')
    parser.add_argument('--generate-requirements', action='store_true',
                       help='pipreqs를 사용하여 requirements.txt 파일들을 자동 생성')
    parser.add_argument('--force-generate', action='store_true',
                       help='기존 requirements.txt 파일을 덮어쓰고 새로 생성')
    
    args = parser.parse_args()
    
    # 배너 출력
    print_banner()
    
    # Python 버전 확인
    if not check_python_version():
        return 1
    
    # 작업 디렉토리 설정
    script_dir = Path(__file__).parent.absolute()
    print_info(f"작업 디렉토리: {script_dir}")
    
    # Requirements.txt 자동 생성 옵션 처리
    if args.generate_requirements:
        if generate_all_requirements(script_dir, args.force_generate):
            print_info("Requirements.txt 생성이 완료되었습니다.")
            print_info("이제 'python3 install_dependencies.py'를 실행하여 패키지를 설치하세요.")
        return 0
    
    # requirements.txt 파일들 찾기
    requirements_files = find_requirements_files(script_dir)
    
    if not requirements_files:
        print_error("requirements.txt 파일을 찾을 수 없습니다.")
        return 1
    
    print_info(f"발견된 requirements.txt 파일들:")
    for module_name, req_file in requirements_files:
        print(f"   - {module_name}: {req_file.relative_to(script_dir)}")
    print()
    
    # 가상환경 사용 여부 결정
    use_venv = not args.no_venv
    
    if use_venv:
        venv_path = script_dir / ".venv"
        
        # 가상환경 설정
        if not setup_virtual_environment(venv_path, args.clean):
            return 1
        
        # 가상환경 경로들 가져오기
        python_path, pip_path, activate_script = get_venv_paths(venv_path)
        print_info(f"Python 경로: {python_path}")
        print_info(f"pip 경로: {pip_path}")
        
        # pip 업그레이드
        upgrade_pip(pip_path)
        
    else:
        # 시스템 Python 사용
        print_warning("시스템 Python을 사용합니다. 가상환경 사용을 권장합니다.")
        pip_path = "pip3"
        
        # pip이 있는지 확인
        success, _, _ = run_command("pip3 --version")
        if not success:
            pip_path = "pip"
            success, _, _ = run_command("pip --version")
            if not success:
                print_error("pip을 찾을 수 없습니다.")
                return 1
    
    # 패키지 설치
    success_count = install_requirements(pip_path, requirements_files, args.upgrade)
    
    # 가상환경 활성화 스크립트 생성
    if use_venv:
        create_activation_scripts(script_dir, venv_path)
    
    # 결과 출력
    display_results(script_dir, requirements_files, success_count, use_venv)
    
    return 0 if success_count == len(requirements_files) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}설치가 사용자에 의해 중단되었습니다.{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}예상치 못한 오류가 발생했습니다: {e}{Colors.NC}")
        sys.exit(1)