import os
import subprocess
import sys

def register_daily_backup():
    """윈도우 작업 스케줄러에 일일 백업 등록"""
    
    # 1. 경로 설정
    script_path = os.path.abspath(r"c:\Users\rcs91\github\med_project\pharma_backup_system.py")
    python_exe = sys.executable  # 현재 실행 중인 파이썬 경로
    task_name = "PharmaHybrid_DailyBackup"
    
    # 2. 실행 명령 생성 (매일 새벽 2시)
    # /SC DAILY : 매일 실행
    # /TN : 작업 이름
    # /TR : 실행할 프로그램 및 인자
    # /ST : 시작 시간
    # /F : 기존 작업이 있으면 강제로 덮어쓰기
    # /RL HIGHEST : 최고 권한으로 실행
    
    command = [
        "schtasks", "/create", "/tn", task_name,
        "/tr", f'"{python_exe}" "{script_path}"',
        "/sc", "daily", "/st", "02:00", "/f", "/rl", "highest"
    ]

    print(f"[*] 작업 스케줄러 등록 시도: {task_name}")
    
    try:
        # 명령 실행
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"SUCCESS: {result.stdout.strip()}")
        print(f"INFO: 매일 새벽 02:00에 '{script_path}'가 자동 실행됩니다.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e.stderr.strip()}")
        print("💡 관리자 권한으로 실행 중인지 확인해 주세요.")

if __name__ == "__main__":
    register_daily_backup()
