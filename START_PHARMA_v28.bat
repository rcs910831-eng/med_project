@echo off
CHCP 65001 > nul
title PHARMA-HYBRID v28.0 MASTER LAUNCHER
setlocal enabledelayedexpansion

echo ============================================================
echo 🫡 PHARMA-HYBRID v28.0 통합 시스템 기동 시작
echo ============================================================
echo.

:: [1] 기존 프로세스 정리 (포트 8504)
echo [*] 기존 대시보드 정리 중 (Port 8504)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8504 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
    echo [+] 기존 프로세스(PID: %%a) 종료 완료.
)

:: [2] 환경 변수 및 경로 설정
set PYTHON_EXE=C:\Users\rcs91\miniconda3\python.exe
set SCRIPT_PATH=c:\Users\rcs91\github\med_project\pharma_v17_ultimate.py

:: [3] 시스템 기동
echo.
echo [*] PHARMA-HYBRID 대시보드 기동 중...
echo [*] 접속 주소: http://localhost:8504
echo.

:: 백그라운드 서비스 기동 (Vault, News)
start /b "PharmaVault" "%PYTHON_EXE%" c:\Users\rcs91\github\med_project\pharma_vault_system.py >nul 2>&1
start /b "PharmaNews" "%PYTHON_EXE%" c:\Users\rcs91\github\med_project\pharma_news_price.py >nul 2>&1

:: 메인 스트림릿 실행
"%PYTHON_EXE%" -m streamlit run "%SCRIPT_PATH%" --server.port 8504 --server.address 0.0.0.0

if %errorLevel% neq 0 (
    echo.
    echo [🚨 오류] 시스템 기동에 실패했습니다.
    echo 1. 아나콘다 환경에서 'streamlit'이 설치되어 있는지 확인하세요.
    echo 2. 명령어: pip install streamlit
    pause
)

pause
