#!/usr/bin/env python3
"""
SHIELD PHARMA-HYBRID v21.0 - FINAL PRODUCTION LAUNCHER
AntiGravity 통합 실행 및 시스템 무결성 검증 스크립트
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# 윈도우 터미널 인코딩 대응 (UTF-8 강제)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ANSI 색상 코드
class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    banner = f"""
{Color.CYAN}{Color.BOLD}
    ======================================================================
    🛡️  SHIELD PHARMA-HYBRID v21.0 : PRODUCTION STANDALONE
    ======================================================================
    [SYSTEM] : Strategic Clinical Decision Support System
    [STATUS] : 3-Column Modernized Layout Active
    [TIME]   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ======================================================================
{Color.END}"""
    print(banner)

def check_system():
    print(f"{Color.YELLOW}[1/3] 시스템 무결성 검사 중...{Color.END}")
    essential_files = [
        "전부_코드화_데이터통합시스템.py",
        "gemini_ai_engine.py",
        "drug_info_complete_db.py",
        "disease_knowledge_db.py",
        "real_patient_data.json"
    ]
    
    missing = []
    for f in essential_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print(f"{Color.RED}❌ 오류: 필수 파일이 누락되었습니다: {', '.join(missing)}{Color.END}")
        return False
    
    print(f"{Color.GREEN}✅ 파일 무결성 확인 완료 (100%){Color.END}")
    return True

def check_environment():
    print(f"{Color.YELLOW}[2/3] 실행 환경 구성 확인 중...{Color.END}")
    try:
        import streamlit
        import google.generativeai
        print(f"{Color.GREEN}✅ 핵심 라이브러리 로드 성공 (Streamlit, Gemini SDK){Color.END}")
    except ImportError as e:
        print(f"{Color.RED}❌ 오류: 라이브러리 누락 - {e}{Color.END}")
        return False
    return True

def launch_dashboard():
    print(f"{Color.YELLOW}[3/3] PHARMA-HYBRID 대시보드 기동 중...{Color.END}")
    print(f"{Color.CYAN}----------------------------------------------------------------------")
    print(f"🚀 브라우저에서 대시보드가 열립니다. (포트: 8503 권장)")
    print(f"----------------------------------------------------------------------{Color.END}")
    
    cmd = ["streamlit", "run", "전부_코드화_데이터통합시스템.py", "--server.port", "8503"]
    
    try:
        # 윈도우 환경에서 새 프로세스로 실행
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  사용자에 의해 시스템이 종료되었습니다.{Color.END}")
    except Exception as e:
        print(f"\n{Color.RED}❌ 실행 중 오류 발생: {e}{Color.END}")

def main():
    print_banner()
    if check_system() and check_environment():
        time.sleep(1)
        launch_dashboard()
    else:
        print(f"{Color.RED}🚨 시스템 가동 실패. 로그를 확인하세요.{Color.END}")

if __name__ == "__main__":
    main()
