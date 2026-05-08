#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🫡 PHARMA-HYBRID VAULT SYSTEM v21.0
금고 자동 백업 & AntiGravity 화면 통합
"""

import os
import sys
import shutil
import zipfile
import hashlib
import datetime
import logging
import threading
import time
import json
import schedule
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, jsonify

# [전략적 경로 리졸버] 환경에 구애받지 않는 무결성 경로 확보
def get_safe_path(base_path, fallback_name):
    """지정된 경로가 없으면 현재 실행 디렉토리에 생성하여 반환"""
    if os.path.exists(os.path.dirname(base_path.split(':')[0] + ':')):
        return base_path
    fallback_path = os.path.join(os.getcwd(), fallback_name)
    os.makedirs(fallback_path, exist_ok=True)
    return fallback_path

SOURCE_PATH = get_safe_path(r"C:\PharmaProject", "PharmaProject_Local")
BACKUP_BASE = get_safe_path(r"C:\PharmaBackup", "PharmaBackup_Local")
VAULT_LOG_DIR = os.path.join(BACKUP_BASE, "vault_logs")

# 백업 설정
BACKUP_INTERVAL_HOURS = 1
CLEANUP_DAYS = 30
ZIP_COMPRESSION = zipfile.ZIP_DEFLATED

# 로깅 설정
os.makedirs(VAULT_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{VAULT_LOG_DIR}/pharma_vault.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VaultStatus(Enum):
    IDLE = "대기 중"
    BACKING_UP = "백업 중..."
    COMPLETED = "완료"
    ERROR = "오류"
    RUNNING = "가동 중"

@dataclass
class BackupInfo:
    timestamp: str
    source_path: str
    backup_path: str
    file_count: int
    total_size: int
    compressed_size: int
    compression_ratio: float
    status: str
    duration: float
    hash_value: str = ""

class PHARMAVaultSystem:
    def __init__(self, source_path: str = SOURCE_PATH, backup_base: str = BACKUP_BASE):
        self.source_path = source_path
        self.backup_base = backup_base
        self.status = VaultStatus.IDLE
        self.last_backup = "기록 없음"
        self.next_backup = "계산 중..."
        self.backup_history = []
        os.makedirs(backup_base, exist_ok=True)
        logger.info("🫡 PHARMA VAULT SYSTEM v21.0 초기화 완료")
    
    def get_status_info(self) -> Dict:
        return {
            'status': self.status.value,
            'last_backup': self.last_backup,
            'next_backup': self.next_backup,
            'backup_count': len(self.backup_history),
            'vault_active': True,
            'message': '🔐 금고 가동 중' if self.status == VaultStatus.RUNNING else self.status.value
        }
    
    def backup_now(self) -> bool:
        try:
            self.status = VaultStatus.BACKING_UP
            start_time = time.time()
            if not os.path.exists(self.source_path): os.makedirs(self.source_path, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"PHARMA_VAULT_{timestamp}.zip"
            backup_path = os.path.join(self.backup_base, backup_filename)
            
            file_count, total_size, comp_size = self._create_zip(self.source_path, backup_path)
            duration = time.time() - start_time
            
            info = BackupInfo(
                timestamp=datetime.datetime.now().isoformat(),
                source_path=self.source_path,
                backup_path=backup_path,
                file_count=file_count,
                total_size=total_size,
                compressed_size=comp_size,
                compression_ratio=(1 - comp_size / total_size * 100) if total_size > 0 else 0,
                status='success',
                duration=duration,
                hash_value=self._hash(backup_path)
            )
            self.backup_history.append(info)
            self.last_backup = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.next_backup = (datetime.datetime.now() + datetime.timedelta(hours=BACKUP_INTERVAL_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
            self.status = VaultStatus.RUNNING
            return True
        except Exception as e:
            logger.error(f"❌ 백업 실패: {e}")
            self.status = VaultStatus.ERROR
            return False

    def _create_zip(self, src, dst):
        cnt, sz = 0, 0
        with zipfile.ZipFile(dst, 'w', ZIP_COMPRESSION) as zf:
            for root, _, files in os.walk(src):
                for f in files:
                    fp = os.path.join(root, f)
                    zf.write(fp, os.path.relpath(fp, src))
                    cnt += 1
                    sz += os.path.getsize(fp)
        return cnt, sz, os.path.getsize(dst)

    def _hash(self, path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192): h.update(chunk)
        return h.hexdigest()[:16]

class AntiGravityIntegration:
    def __init__(self, vault, port=5555):
        self.vault = vault
        self.app = Flask(__name__)
        @self.app.route('/api/vault/status')
        def status(): return jsonify(self.vault.get_status_info())
        @self.app.route('/')
        def home():
            s = self.vault.get_status_info()
            return f"<html><body style='background:#050505;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;flex-direction:column;'>" \
                   f"<h1>🫡 PHARMA VAULT SYSTEM</h1>" \
                   f"<div style='font-size:3em;border:2px solid #00ff00;padding:20px;border-radius:10px;box-shadow:0 0 20px #00ff00;'>{s['message']}</div>" \
                   f"<p>마지막 백업: {s['last_backup']}</p>" \
                   f"<p>다음 백업: {s['next_backup']}</p>" \
                   f"</body></html>"

    def run(self): self.app.run(host='0.0.0.0', port=5555)

if __name__ == '__main__':
    vault = PHARMAVaultSystem()
    scheduler_thread = threading.Thread(target=lambda: (schedule.every(1).hours.do(vault.backup_now), 
                                                        vault.backup_now(), # 초기 백업
                                                        [schedule.run_pending() or time.sleep(60) for _ in iter(int, 1)]), daemon=True)
    scheduler_thread.start()
    AntiGravityIntegration(vault).run()
