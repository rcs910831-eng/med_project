import os
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path

# ==========================================
# 0. 전략적 백업 설정
# ==========================================
SOURCE_DIR = r"C:\PharmaProject"
BACKUP_BASE_DIR = r"C:\PharmaProject_Backups"
MAX_BACKUP_COUNT = 10  # 보관할 최대 백업 개수 (로테이션)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [BACKUP] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BACKUP_BASE_DIR, "backup_log.txt") if os.path.exists(BACKUP_BASE_DIR) else "backup_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def run_strategic_backup():
    """C:\\PharmaProject 전체를 압축 백업하고 로테이션 관리"""
    
    print("\n" + "="*60)
    print(" PHARMA-HYBRID 전략적 자산 백업 시스템 가동")
    print("="*60 + "\n")

    try:
        # 1. 백업 디렉토리 생성
        if not os.path.exists(BACKUP_BASE_DIR):
            os.makedirs(BACKUP_BASE_DIR)
            logging.info(f"✅ 백업 저장소 생성 완료: {BACKUP_BASE_DIR}")

        # 2. 백업 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"Pharma_Backup_{timestamp}"
        backup_path = os.path.join(BACKUP_BASE_DIR, backup_filename)

        # 3. 압축 실행 (ZIP 포맷)
        logging.info(f"🚀 백업 시작: {SOURCE_DIR} -> {backup_path}.zip")
        start_time = time.time()
        
        # shutil.make_archive는 확장자를 자동으로 붙임
        shutil.make_archive(backup_path, 'zip', SOURCE_DIR)
        
        duration = time.time() - start_time
        file_size = os.path.getsize(f"{backup_path}.zip") / (1024 * 1024) # MB
        
        logging.info(f"✅ 백업 완료! (소요시간: {duration:.2f}초, 용량: {file_size:.2f}MB)")

        # 4. 백업 로테이션 (오래된 백업 삭제)
        manage_rotation()

    except Exception as e:
        logging.error(f"❌ 백업 중 치명적 오류 발생: {e}")

def manage_rotation():
    """설정된 개수 이상의 오래된 백업 파일을 자동 삭제"""
    try:
        backups = [
            os.path.join(BACKUP_BASE_DIR, f) 
            for f in os.listdir(BACKUP_BASE_DIR) 
            if f.startswith("Pharma_Backup_") and f.endswith(".zip")
        ]
        
        # 날짜순 정렬
        backups.sort(key=os.path.getmtime)

        if len(backups) > MAX_BACKUP_COUNT:
            count_to_delete = len(backups) - MAX_BACKUP_COUNT
            for i in range(count_to_delete):
                os.remove(backups[i])
                logging.info(f"🗑️ 오래된 백업 로테이션 삭제: {os.path.basename(backups[i])}")
                
    except Exception as e:
        logging.error(f"❌ 로테이션 관리 중 오류: {e}")

if __name__ == "__main__":
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 오류: 원본 디렉토리({SOURCE_DIR})가 존재하지 않습니다.")
    else:
        run_strategic_backup()
