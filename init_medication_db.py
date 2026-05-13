#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
"""
PHARMA-MOBILE 약물 정보 데이터베이스 초기화
SQLite에 기본 약물 정보 저장
"""

import sqlite3
import json
from datetime import datetime

# 샘플 약물 정보 데이터
MEDICATIONS_DATA = [
    {
        "name": "노바스크정",
        "generic_name": "Amlodipine",
        "dosage_strength": "5mg",
        "dosage_forms": "정제",
        "daily_dose": "1회 1정",
        "frequency": "1일 1회",
        "duration": "의사 지시에 따름",
        "mfds_price": "1,234",
        "manufacturer": "비노 제약",
        "side_effects": ["두통", "현기증", "발목 부종", "홍조"],
        "contraindications": "심한 저혈압 환자",
        "drug_interactions": ["자몽주스와 함께 복용 시 상호작용"],
        "special_warnings": "고령자 주의, 임산부 주의",
        "indication": "고혈압, 협심증"
    },
    {
        "name": "글루코판정",
        "generic_name": "Metformin",
        "dosage_strength": "500mg",
        "dosage_forms": "정제",
        "daily_dose": "1회 500-1000mg",
        "frequency": "1일 2-3회",
        "duration": "의사 지시에 따름",
        "mfds_price": "856",
        "manufacturer": "종로 제약",
        "side_effects": ["위장 장애", "설사", "복부 팽만감"],
        "contraindications": "신부전 환자",
        "drug_interactions": ["특이사항 없음"],
        "special_warnings": "신기능 검사 필요, 대비제 투여 시 일시 중단",
        "indication": "제2형 당뇨병"
    },
    {
        "name": "타그리소정",
        "generic_name": "Afatinib",
        "dosage_strength": "150mg",
        "dosage_forms": "정제",
        "daily_dose": "1회 1정",
        "frequency": "1일 1회",
        "duration": "의사 지시에 따름",
        "mfds_price": "45,000",
        "manufacturer": "보에링거 인겔하임",
        "side_effects": ["피부 발진", "설사", "오심", "식욕부진"],
        "contraindications": "임산부, 수유부",
        "drug_interactions": ["특정 약물과의 상호작용 확인 필요"],
        "special_warnings": "간기능 검사 필요, 피부 부작용 모니터링",
        "indication": "폐암 (EGFR 돌연변이)"
    },
    {
        "name": "리피토정",
        "generic_name": "Atorvastatin",
        "dosage_strength": "10mg",
        "dosage_forms": "정제",
        "daily_dose": "1회 1정",
        "frequency": "1일 1회",
        "duration": "의사 지시에 따름",
        "mfds_price": "2,100",
        "manufacturer": "한국파이저",
        "side_effects": ["근육통", "두통", "소화불량"],
        "contraindications": "활성 간질환, 임산부",
        "drug_interactions": ["자몽주스와의 상호작용"],
        "special_warnings": "고령자 주의, 근육통 모니터링",
        "indication": "고콜레스테롤혈증"
    },
    {
        "name": "싱귤레어정",
        "generic_name": "Montelukast",
        "dosage_strength": "4mg",
        "dosage_forms": "정제",
        "daily_dose": "1회 1정",
        "frequency": "1일 1회",
        "duration": "의사 지시에 따름",
        "mfds_price": "1,850",
        "manufacturer": "머크 샤프 돔",
        "side_effects": ["두통", "피로", "복부통"],
        "contraindications": "특이사항 없음",
        "drug_interactions": ["특이사항 없음"],
        "special_warnings": "천식 악화 시 즉시 알림",
        "indication": "천식, 알레르기성 비염"
    }
]

def init_medication_db(db_path="pharma_mobile.db"):
    """약물 정보 데이터베이스 초기화"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 약물 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            generic_name TEXT,
            dosage_strength TEXT,
            dosage_forms TEXT,
            daily_dose TEXT,
            frequency TEXT,
            duration TEXT,
            mfds_price TEXT,
            manufacturer TEXT,
            side_effects TEXT,
            contraindications TEXT,
            drug_interactions TEXT,
            special_warnings TEXT,
            indication TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 약물 정보 삽입
        for med in MEDICATIONS_DATA:
            cursor.execute('''
            INSERT OR REPLACE INTO medications
            (name, generic_name, dosage_strength, dosage_forms, daily_dose,
             frequency, duration, mfds_price, manufacturer, side_effects,
             contraindications, drug_interactions, special_warnings, indication)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                med['name'],
                med['generic_name'],
                med['dosage_strength'],
                med['dosage_forms'],
                med['daily_dose'],
                med['frequency'],
                med['duration'],
                med['mfds_price'],
                med['manufacturer'],
                json.dumps(med['side_effects'], ensure_ascii=False),
                med['contraindications'],
                json.dumps(med['drug_interactions'], ensure_ascii=False),
                med['special_warnings'],
                med['indication']
            ))

        conn.commit()
        print(f"✅ 약물 DB 초기화 완료: {db_path}")
        print(f"   저장된 약물: {len(MEDICATIONS_DATA)}개")

        # 확인 조회
        cursor.execute('SELECT COUNT(*) FROM medications')
        count = cursor.fetchone()[0]
        print(f"   DB 확인: {count}개 약물 저장됨")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    init_medication_db()
