#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🫡 PHARMA-HYBRID 종합 약물 데이터베이스 v24.0
작성일: 2026-04-26
버전: v24.0 (최종)
"""

import json
import csv
import os
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

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
MASTER_DATA_DIR = os.path.join(PROJECT_ROOT, "database", "master_data")
os.makedirs(MASTER_DATA_DIR, exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════════
# 【PART 1】종합 약물 데이터베이스 (v24.0 Master Data)
# ═════════════════════════════════════════════════════════════════════════════

COMPREHENSIVE_MEDICATION_DATABASE = {
    "metadata": {
        "name": "PHARMA-HYBRID Comprehensive Medication Database v24.0",
        "version": "24.0",
        "created_date": "2026-04-26",
        "data_sources": [
            "FDA (미국 식약청)", "MHRA (영국 의약청)", "NCBI (의학도서관)", 
            "clinicaltrials.gov", "Nature Communications", "JAMA Oncology",
            "대한약학회", "한국병원약사회"
        ]
    },
    "diseases": {
        "common_cold": {
            "name": "감기",
            "medications": [
                {
                    "name": "아세트아미노펜", "en": "Acetaminophen", "func": "해열진통", 
                    "dose": "500-1000mg q4-6h", "source": "FDA/NCBI"
                },
                {
                    "name": "슈도에페드린", "en": "Pseudoephedrine", "func": "비충혈제거", 
                    "dose": "60mg q4-6h", "source": "MHRA"
                }
            ]
        },
        "hypertension": {
            "name": "고혈압",
            "medications": [
                {
                    "name": "리시노프릴", "en": "Lisinopril", "func": "ACE Inhibitor", 
                    "dose": "10-40mg qd", "source": "FDA"
                },
                {
                    "name": "암로디핀", "en": "Amlodipine", "func": "CCB", 
                    "dose": "5-10mg qd", "source": "FDA"
                }
            ]
        },
        "lung_cancer": {
            "name": "폐암 (NSCLC)",
            "medications": [
                {
                    "name": "오시머티닙", "en": "Osimertinib", "brand": "Tagrisso",
                    "type": "3rd Gen EGFR-TKI", "dose": "80mg qd",
                    "trial": "FLAURA/LAURA (PFS 39.1m)", "source": "ASCO 2024 / FDA"
                },
                {
                    "name": "펨브롤리주맙", "en": "Pembrolizumab", "brand": "Keytruda",
                    "type": "PD-1 Inhibitor", "dose": "200mg q3w",
                    "source": "FDA / NCBI"
                }
            ]
        },
        "gastric_cancer": {
            "name": "위암",
            "medications": [
                {
                    "name": "트라스투주맙", "en": "Trastuzumab", "brand": "Herceptin",
                    "indication": "HER2+", "dose": "6-8mg/kg q3w", "source": "ToGA Trial / FDA"
                },
                {
                    "name": "엔허투", "en": "Trastuzumab deruxtecan", "type": "ADC",
                    "dose": "5.4mg/kg q3w", "source": "NCBI / FDA"
                }
            ]
        },
        "icu_critical": {
            "name": "중증/응급",
            "medications": [
                {
                    "name": "에피네프린", "en": "Epinephrine", "func": "심정지/아나필락시스", 
                    "dose": "0.5-1mg IV", "source": "FDA Emergency"
                }
            ]
        }
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# 【PART 2】데이터베이스 관리 엔진
# ═════════════════════════════════════════════════════════════════════════════

class PHARMAComprehensiveDB:
    def __init__(self):
        self.data = COMPREHENSIVE_MEDICATION_DATABASE
        self.json_path = os.path.join(MASTER_DATA_DIR, "comprehensive_medication_db_v24.json")
        self.csv_path = os.path.join(MASTER_DATA_DIR, "comprehensive_medication_db_v24.csv")
    
    def save_all(self):
        # 1. JSON 저장
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # 2. CSV 저장
        with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['질병', '약물명', '영문명', '기능/타입', '용량', '출처'])
            for cat, details in self.data['diseases'].items():
                d_name = details['name']
                for med in details['medications']:
                    writer.writerow([
                        d_name, med.get('name'), med.get('en'), 
                        med.get('func') or med.get('type'), med.get('dose'), med.get('source')
                    ])
        
        print(f"[SUCCESS] Data Saved Successfully:")
        print(f"   - JSON: {self.json_path}")
        print(f"   - CSV: {self.csv_path}")

    def search(self, query):
        results = []
        for cat, details in self.data['diseases'].items():
            for med in details['medications']:
                if query.lower() in med['name'].lower() or query.lower() in med['en'].lower():
                    results.append({"disease": details['name'], "med": med})
        return results

if __name__ == "__main__":
    db = PHARMAComprehensiveDB()
    db.save_all()
    
    # 샘플 검색 테스트
    search_res = db.search("오시머티닙")
    if search_res:
        print(f"\n[SEARCH RESULT] (Osimertinib): {search_res[0]['med']['trial']}")
