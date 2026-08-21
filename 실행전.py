"""
이 파일은 프로젝트 실행 전 개발 환경을 자동으로 구축하기 위한 초기화 스크립트입니다.
uv 도구를 활용하여 로컬 가상환경(.venv)을 생성하고, requirements.txt에 명시된
필수 라이브러리 패키지들을 가상환경 내부에 한 번에 설치 및 동기화합니다.
"""

import subprocess
import sys
import os

def run_cmd(cmd):
    """지정한 리스트 형태의 명령어를 실행합니다."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        print(f"[오류] 명령어 실행 중 에러가 발생했습니다: {e}")
        return False

def main():
    print("=============================================================")
    print(" [프로젝트 초기 환경 설정 및 가상환경 구축 시작]")
    print("=============================================================")

    # 1. uv 도구 존재 여부 확인 및 설치 시도
    print("\n>>> 1단계: uv 도구 상태 확인 및 가상환경(.venv) 생성")
    
    if os.path.exists(".venv"):
        print("[Info] 이미 가상환경(.venv)이 존재합니다. 생성을 건너뜁니다.")
    else:
        # uv venv 실행 시도
        success = run_cmd(["uv", "venv"])
        
        if not success:
            print("[Warning] 시스템에서 'uv' 명령어를 찾을 수 없습니다.")
            print("[Info] 시스템 pip를 통해 'uv' 패키지 설치를 시도합니다...")
            
            # pip install uv 실행
            pip_install_uv = run_cmd([sys.executable, "-m", "pip", "install", "uv"])
            if not pip_install_uv:
                print("[Error] uv 설치에 실패했습니다. 파이썬 및 pip 설정을 확인해주세요.")
                sys.exit(1)
                
            print("[Success] uv 설치 완료. 가상환경(.venv) 생성을 재시도합니다.")
            # 다시 uv venv 실행
            if not run_cmd(["uv", "venv"]):
                print("[Error] 가상환경(.venv) 생성에 실패했습니다.")
                sys.exit(1)
        else:
            print("[Success] 가상환경(.venv) 생성 완료.")

    # 2. requirements.txt 패키지 설치
    print("\n>>> 2단계: 필수 패키지 설치 및 동기화")
    if not os.path.exists("requirements.txt"):
        print("[Error] requirements.txt 파일이 존재하지 않습니다.")
        sys.exit(1)
        
    print("[Info] uv를 활용해 가상환경에 패키지를 설치합니다 (uv pip install -r requirements.txt)...")
    install_success = run_cmd(["uv", "pip", "install", "-r", "requirements.txt"])
    
    if install_success:
        print("\n=============================================================")
        print(" [초기화 완료] 프로젝트 가상환경 및 필수 패키지 설치가 완료되었습니다!")
        print(" 실행 방법: uv run python <실행할파일.py>")
        print("=============================================================")
    else:
        print("[Error] 패키지 설치에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()