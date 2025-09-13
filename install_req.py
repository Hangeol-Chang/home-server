#!/usr/bin/env python3
"""
Home Server Requirements Installer

이 스크립트는 메인 서버와 모든 모듈의 requirements.txt를 자동으로 찾아서 설치합니다.
가상환경 사용을 권장하며, 자동으로 가상환경 생성 및 활성화 옵션을 제공합니다.

사용법:
    python3 install_req.py              # 현재 환경에 설치
    python3 install_req.py --venv       # 가상환경 생성 후 설치
    python3 install_req.py --venv-name myenv  # 특정 이름의 가상환경 사용
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import venv

def run_command(command, cwd=None, check=True):
    """명령어 실행 및 결과 출력"""
    print(f"실행 중: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"경고: {result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"오류: 명령어 실행 실패 - {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def create_virtual_environment(venv_path):
    """가상환경 생성"""
    print(f"가상환경 생성 중: {venv_path}")
    
    if venv_path.exists():
        print(f"기존 가상환경이 존재합니다: {venv_path}")
        return True
    
    try:
        venv.create(venv_path, with_pip=True)
        print(f"가상환경이 성공적으로 생성되었습니다: {venv_path}")
        return True
    except Exception as e:
        print(f"가상환경 생성 실패: {e}")
        return False

def get_venv_python_path(venv_path):
    """가상환경의 Python 실행파일 경로 반환"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "python"

def get_venv_pip_path(venv_path):
    """가상환경의 pip 실행파일 경로 반환"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "pip"

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

def install_requirements(pip_command, requirements_files):
    """requirements.txt 파일들을 순서대로 설치"""
    success_count = 0
    
    for module_name, req_file in requirements_files:
        print(f"\n{'='*50}")
        print(f"모듈 '{module_name}' 패키지 설치 중...")
        print(f"파일: {req_file}")
        print(f"{'='*50}")
        
        command = f"{pip_command} install -r {req_file}"
        if run_command(command):
            print(f"✅ '{module_name}' 패키지 설치 완료")
            success_count += 1
        else:
            print(f"❌ '{module_name}' 패키지 설치 실패")
    
    return success_count

def main():
    parser = argparse.ArgumentParser(description='Home Server Requirements Installer')
    parser.add_argument('--venv', action='store_true', 
                       help='가상환경을 생성하고 그 안에 패키지 설치')
    parser.add_argument('--venv-name', default='venv', 
                       help='가상환경 디렉토리 이름 (기본값: venv)')
    parser.add_argument('--upgrade', action='store_true',
                       help='패키지 업그레이드 옵션 추가')
    
    args = parser.parse_args()
    
    # 현재 스크립트가 있는 디렉토리를 기준으로 작업
    script_dir = Path(__file__).parent.absolute()
    print(f"작업 디렉토리: {script_dir}")
    
    # requirements.txt 파일들 찾기
    requirements_files = find_requirements_files(script_dir)
    
    if not requirements_files:
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        return 1
    
    print(f"\n발견된 requirements.txt 파일들:")
    for module_name, req_file in requirements_files:
        print(f"  - {module_name}: {req_file}")
    
    # 가상환경 사용 여부 결정
    if args.venv:
        venv_path = script_dir / args.venv_name
        
        # 가상환경 생성
        if not create_virtual_environment(venv_path):
            return 1
        
        # 가상환경의 pip 사용
        python_path = get_venv_python_path(venv_path)
        pip_command = f"{python_path} -m pip"
        
        # pip 업그레이드
        print("\npip 업그레이드 중...")
        run_command(f"{pip_command} install --upgrade pip")
        
        print(f"\n가상환경 사용: {venv_path}")
        print(f"Python 경로: {python_path}")
        
        # 가상환경 활성화 명령어 안내
        if os.name == 'nt':  # Windows
            activate_cmd = f"{venv_path}\\Scripts\\activate.bat"
        else:  # Unix/Linux/macOS
            activate_cmd = f"source {venv_path}/bin/activate"
        
        print(f"\n나중에 가상환경을 활성화하려면:")
        print(f"  {activate_cmd}")
        
    else:
        # 시스템 Python 사용
        pip_command = "python3 -m pip"
        print(f"\n시스템 Python 사용")
        print("⚠️  가상환경 사용을 권장합니다: python3 install_req.py --venv")
    
    # 업그레이드 옵션 추가
    if args.upgrade:
        pip_command += " --upgrade"
    
    # 패키지 설치
    print(f"\n{'='*60}")
    print("패키지 설치 시작")
    print(f"{'='*60}")
    
    success_count = install_requirements(pip_command, requirements_files)
    
    # 결과 출력
    print(f"\n{'='*60}")
    print("설치 완료 결과")
    print(f"{'='*60}")
    print(f"총 {len(requirements_files)}개 모듈 중 {success_count}개 성공")
    
    if success_count == len(requirements_files):
        print("🎉 모든 패키지가 성공적으로 설치되었습니다!")
        
        if args.venv:
            print(f"\n서버 실행 방법:")
            if os.name == 'nt':  # Windows
                print(f"  {venv_path}\\Scripts\\activate.bat")
            else:  # Unix/Linux/macOS
                print(f"  source {venv_path}/bin/activate")
            print(f"  python3 app.py")
        
        return 0
    else:
        print(f"❌ {len(requirements_files) - success_count}개 모듈에서 설치 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
