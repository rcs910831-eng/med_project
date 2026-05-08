#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🫡 PHARMA-HYBRID NEWS & DRUG PRICE INTEGRATION SYSTEM v22.0
약가/뉴스 실시간 연결 시스템
"""

import os
import json
import sqlite3
import threading
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, jsonify

# [전략적 경로 리졸버] 환경 무관성 확보
def get_safe_path(base_path, fallback_name):
    try:
        drive = base_path.split(':')[0] + ':'
        if os.path.exists(drive): return base_path
    except: pass
    fallback_path = os.path.join(os.getcwd(), fallback_name)
    os.makedirs(fallback_path, exist_ok=True)
    return fallback_path

PROJECT_ROOT = get_safe_path(r"C:\PharmaProject", "PharmaProject_Local")
DB_DIR = os.path.join(PROJECT_ROOT, "database", "market")
os.makedirs(DB_DIR, exist_ok=True)

# 로깅
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DB_DIR, "pharma_market.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsType(Enum):
    PRICE_REDUCTION = "약가인하"
    POLICY = "정책"
    NEW_DRUG = "신약"
    APPROVAL = "승인"
    RECALL = "회수"
    OTHER = "기타"

class DrugPriceCollector:
    def __init__(self, db_path=os.path.join(DB_DIR, "pharma_prices.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS drug_prices 
                     (drug_id TEXT PRIMARY KEY, drug_name TEXT, manufacturer TEXT, 
                      current_price REAL, price_change REAL, source TEXT, updated_at TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS news 
                     (news_id TEXT PRIMARY KEY, title TEXT, source TEXT, 
                      news_type TEXT, published_at TIMESTAMP, summary TEXT)''')
        conn.commit()
        conn.close()

    def add_sample_data(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 2026년 실거래가 조사 기반 약가인하 샘플
        samples = [
            ('D001', '아리셉트정', '한국노바티스', 1200, -300, '약사공론', datetime.now().isoformat()),
            ('D002', '다이아벡스정', '대웅제약', 92, -5, '식약처', datetime.now().isoformat()),
            ('D003', '노바스크정', '한국화이자', 365, -12, '데일리팜', datetime.now().isoformat())
        ]
        c.executemany("INSERT OR REPLACE INTO drug_prices VALUES (?,?,?,?,?,?,?)", samples)
        
        news_samples = [
            ('N001', '2026년 상반기 약가 재평가 결과 발표', '보건복지부', '정책', datetime.now().isoformat(), '총 2,450품목 상한금액 조정'),
            ('N002', 'SGLT2 억제제 심부전 급여 확대안 통과', '메디게이트', '승인', datetime.now().isoformat(), '자디앙, 포시가 등 1차 약제 권고 강화')
        ]
        c.executemany("INSERT OR REPLACE INTO news VALUES (?,?,?,?,?,?)", news_samples)
        conn.commit()
        conn.close()

    def get_market_intelligence(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        prices = [dict(r) for r in c.execute("SELECT * FROM drug_prices LIMIT 10").fetchall()]
        news = [dict(r) for r in c.execute("SELECT * FROM news ORDER BY published_at DESC LIMIT 10").fetchall()]
        conn.close()
        return {"prices": prices, "news": news}

class PriceNewsIntegration:
    def __init__(self, port=5556):
        self.collector = DrugPriceCollector()
        self.collector.add_sample_data()
        self.app = Flask(__name__)
        @self.app.route('/api/market')
        def market(): return jsonify(self.collector.get_market_intelligence())
        @self.app.route('/')
        def home():
            data = self.collector.get_market_intelligence()
            return f"<html><body style='background:#f0f4f8; font-family:sans-serif; padding:40px;'>" \
                   f"<h1>📊 PHARMA MARKET INTELLIGENCE v22.0</h1>" \
                   f"<h2>💰 Recent Price Changes</h2>" + \
                   "".join([f"<li>{p['drug_name']}: {p['current_price']}원 ({p['price_change']}원)</li>" for p in data['prices']]) + \
                   f"<h2>📰 Clinical News</h2>" + \
                   "".join([f"<li>[{n['news_type']}] {n['title']} ({n['source']})</li>" for n in data['news']]) + \
                   f"</body></html>"

    def run(self): self.app.run(host='0.0.0.0', port=5556)

if __name__ == '__main__':
    PriceNewsIntegration().run()
