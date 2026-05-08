@echo off
CHCP 65001 > nul
title PHARMA-HYBRID DATABASE ENGINE v24.0
echo ============================================================
echo 🫡 PHARMA-HYBRID 암종 데이터베이스 기동 중...
echo ============================================================
echo.
python c:\Users\rcs91\github\med_project\pharma_cancer_db.py
echo.
echo ============================================================
echo ✅ 작업이 완료되었습니다. 아무 키나 누르면 종료합니다.
echo ============================================================
pause > nul
