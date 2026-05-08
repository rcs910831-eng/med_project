@echo off
setlocal
:: ============================================================
:: PHARMA-HYBRID 전략적 백업 자동 등록 도구
:: ============================================================

echo [*] 관리자 권한 확인 중...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [+] 관리자 권한 확보 완료.
) else (
    echo [!] 오류: 이 스크립트는 '관리자 권한'으로 실행해야 합니다.
    echo [!] 마우스 오른쪽 버튼을 눌러 '관리자 권한으로 실행'을 선택해 주세요.
    pause
    exit /b
)

set SCRIPT_PATH=c:\Users\rcs91\github\med_project\pharma_backup_system.py
set PYTHON_EXE=%~dp0\..\..\..\miniconda3\python.exe

:: 실제 파이썬 경로가 다를 수 있으므로 현재 실행 환경에서 확인된 경로를 우선 사용 권장
:: 여기서는 사용자의 환경에 맞춰 고정 경로를 설정합니다.
set PYTHON_EXE=C:\Users\rcs91\miniconda3\python.exe

echo [*] 작업 스케줄러 등록을 시작합니다...
echo [*] 대상: %SCRIPT_PATH%
echo [*] 일정: 매일 새벽 02:00

schtasks /create /tn "PharmaHybrid_DailyBackup" /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\"" /sc daily /st 02:00 /f /rl highest

if %errorLevel% == 0 (
    echo.
    echo [OK] 전략적 백업 등록이 완료되었습니다!
    echo [OK] 이제 매일 새벽 2시에 시스템이 자동으로 백업됩니다.
) else (
    echo.
    echo [FAIL] 등록에 실패했습니다. 경로를 확인해 주세요.
)

pause
