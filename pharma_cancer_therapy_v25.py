#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🫡 PHARMA-HYBRID 신종암 통합 치료 시스템 v25.0
치료방법, 식단, 약물, 운동, 시너지 데이터 통합 엔진
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

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
CLINICAL_DIR = os.path.join(PROJECT_ROOT, "database", "clinical")
os.makedirs(CLINICAL_DIR, exist_ok=True)

class EmergedCancerComprehensiveSystem:
    def __init__(self):
        self.cancers = self._build_cancer_database()
        self.nutrition = self._build_nutrition_database()
        self.synergies = self._build_synergy_data()
        
    def _build_cancer_database(self):
        return {
            "MERKEL_CELL": {
                "name": "머클 세포 암종", "english": "Merkel Cell Carcinoma",
                "survival": {"5_year": 54.0},
                "medications": ["옵디보 (Nivolumab)", "키트루다 (Pembrolizumab)", "바벤티오 (Avelumab)"],
                "exercise": "Phase 1: 수술 후 4주 회복 (걷기/호흡)"
            },
            "LIQUID_BIOPSY_DETECTED": {
                "name": "액상 생검 조기 감지 암", "english": "Liquid Biopsy-Detected Early Cancer",
                "survival": {"5_year": 99.0},
                "characteristics": "2025년형 신종 조기 진단 모델"
            }
        }
        
    def _build_nutrition_database(self):
        return {
            "recommended": ["브로콜리 (설포라판)", "블루베리 (안토시아닌)", "연어 (오메가-3)", "토마토 (라이코펜)"],
            "meal_plan": {
                "breakfast": "베리 요거트 + 견과류",
                "lunch": "연어 샐러드 + 올리브유",
                "dinner": "시금치 나물 + 현미밥"
            }
        }
        
    def _build_synergy_data(self):
        return {
            "beneficial": ["강황 + 검은 후추 (흡수율 200% 증가)", "녹차 + 레몬 (카테킨 5배 증가)"],
            "warnings": ["자몽 <-> 면역항암제 (대사 저해 위험)"]
        }

    def export_json(self):
        filepath = os.path.join(CLINICAL_DIR, "emerging_cancer_therapy_v25.json")
        data = {
            "metadata": {"version": "25.0", "updated": datetime.now().isoformat()},
            "cancers": self.cancers,
            "nutrition": self.nutrition,
            "synergy": self.synergies
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

if __name__ == "__main__":
    # 인코딩 보정
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    
    print("="*60)
    print("PHARMA-HYBRID Emerging Cancer Integrated Therapy System v25.0")
    print("="*60)
    
    system = EmergedCancerComprehensiveSystem()
    path = system.export_json()
    
    print(f"[SUCCESS] Therapy database synchronized to:")
    print(f" -> {path}")
    
    # 샘플 시너지 출력
    print(f"\n[SYNERGY INTELLIGENCE]")
    for syn in system.synergies['beneficial']:
        print(f" - {syn}")
        
    print("\n" + "="*60)
    print("Clinical Intelligence Update Completed.")
