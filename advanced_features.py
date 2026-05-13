#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 기능 모음
- 복약 알림 & 스케줄
- 개인 약력 저장소
- 약가 비교
- 약물 부작용 추적
- 약물+음식 상호작용
- 유효기간 관리
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
# 1. 복약 알림 & 스케줄
# ═══════════════════════════════════════════════════════════════

class MedicationScheduler:
    """복약 스케줄 관리"""

    def __init__(self, db_path: str = "pharma_mobile.db"):
        self.db_path = db_path
        self._init_schedule_table()

    def _init_schedule_table(self):
        """스케줄 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medication_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            time TEXT NOT NULL,
            frequency TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medication_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            taken_at TIMESTAMP,
            skipped_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def add_schedule(self, patient_id: str, medication_name: str,
                    time: str, frequency: str = "daily") -> Dict:
        """복약 스케줄 추가"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO medication_schedule
            (patient_id, medication_name, time, frequency, start_date, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            ''', (patient_id, medication_name, time, frequency, datetime.now().date()))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'message': f"'{medication_name}' 복약 알림이 {time}에 설정되었습니다",
                'notification_time': time
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_todays_schedule(self, patient_id: str) -> List[Dict]:
        """오늘의 복약 스케줄 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT medication_name, time, frequency FROM medication_schedule
            WHERE patient_id = ? AND status = 'active'
            ORDER BY time
            ''', (patient_id,))

            schedule = []
            for med_name, time, frequency in cursor.fetchall():
                schedule.append({
                    'medication': med_name,
                    'time': time,
                    'frequency': frequency
                })

            conn.close()
            return schedule

        except Exception as e:
            print(f"[ERROR] {e}")
            return []

# ═══════════════════════════════════════════════════════════════
# 2. 개인 약력 저장소
# ═══════════════════════════════════════════════════════════════

class PatientMedicalHistory:
    """환자 약력 관리"""

    def __init__(self, db_path: str = "pharma_mobile.db"):
        self.db_path = db_path
        self._init_history_table()

    def _init_history_table(self):
        """약력 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT,
            age INTEGER,
            gender TEXT,
            allergies TEXT,
            chronic_diseases TEXT,
            past_medications TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescription_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            prescription_date DATE,
            doctor_name TEXT,
            hospital TEXT,
            diagnosis TEXT,
            medications TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def save_patient_profile(self, patient_id: str, profile: Dict) -> Dict:
        """환자 프로필 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT OR REPLACE INTO patient_history
            (patient_id, name, age, gender, allergies, chronic_diseases)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                profile.get('name'),
                profile.get('age'),
                profile.get('gender'),
                json.dumps(profile.get('allergies', []), ensure_ascii=False),
                json.dumps(profile.get('chronic_diseases', []), ensure_ascii=False)
            ))

            conn.commit()
            conn.close()

            return {'success': True, 'message': '환자 정보가 저장되었습니다'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def save_prescription(self, patient_id: str, prescription: Dict) -> Dict:
        """처방전 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO prescription_history
            (patient_id, prescription_date, doctor_name, hospital, diagnosis, medications)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                prescription.get('date', datetime.now().date()),
                prescription.get('doctor'),
                prescription.get('hospital'),
                prescription.get('diagnosis'),
                json.dumps(prescription.get('medications', []), ensure_ascii=False)
            ))

            conn.commit()
            conn.close()

            return {'success': True, 'message': '처방전이 저장되었습니다'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ═══════════════════════════════════════════════════════════════
# 3. 약물+음식 상호작용
# ═══════════════════════════════════════════════════════════════

DRUG_FOOD_INTERACTIONS = {
    '노바스크정': {
        'avoid': ['자몽', '자몽주스', '포멜로'],
        'caution': ['카페인'],
        'safe_with': ['우유', '물']
    },
    '글루코판정': {
        'avoid': ['술', '알코올 음료'],
        'caution': ['고지방 음식'],
        'safe_with': ['일반 식사']
    },
    '리피토정': {
        'avoid': ['자몽', '자몽주스'],
        'caution': ['적포도주'],
        'safe_with': ['저지방 음식']
    }
}

def check_drug_food_interaction(medication_name: str, food_items: List[str]) -> Dict:
    """약물-음식 상호작용 확인"""

    if medication_name not in DRUG_FOOD_INTERACTIONS:
        return {
            'safe': True,
            'message': f"'{medication_name}'의 음식 상호작용 정보가 없습니다",
            'recommendation': '의약사와 상담하세요'
        }

    interactions = DRUG_FOOD_INTERACTIONS[medication_name]
    avoided = []
    caution = []

    for food in food_items:
        if food in interactions['avoid']:
            avoided.append(food)
        elif food in interactions['caution']:
            caution.append(food)

    if avoided:
        return {
            'safe': False,
            'severity': 'danger',
            'avoided_foods': avoided,
            'message': f"⚠️ '{medication_name}'과 {', '.join(avoided)}는 함께 섭취하면 안 됩니다",
            'recommendation': '대체 음식을 선택하세요'
        }
    elif caution:
        return {
            'safe': True,
            'severity': 'caution',
            'caution_foods': caution,
            'message': f"주의: '{medication_name}'과 {', '.join(caution)}를 함께 섭취할 때는 주의하세요",
            'recommendation': '가능하면 피하거나 의약사와 상담하세요'
        }
    else:
        return {
            'safe': True,
            'message': f"'{medication_name}'은 입력된 음식과 상호작용이 없습니다",
            'safe_foods': interactions['safe_with']
        }

# ═══════════════════════════════════════════════════════════════
# 4. 약물 부작용 추적
# ═══════════════════════════════════════════════════════════════

class SideEffectTracker:
    """약물 부작용 추적"""

    COMMON_SIDE_EFFECTS = {
        '두통': 'headache',
        '구역질': 'nausea',
        '설사': 'diarrhea',
        '피로': 'fatigue',
        '어지러움': 'dizziness',
        '발진': 'rash',
        '복부통': 'abdominal_pain',
        '불면증': 'insomnia'
    }

    def __init__(self, db_path: str = "pharma_mobile.db"):
        self.db_path = db_path
        self._init_tracking_table()

    def _init_tracking_table(self):
        """추적 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS side_effect_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            side_effect TEXT,
            severity TEXT,
            started_at TIMESTAMP,
            resolved_at TIMESTAMP,
            notes TEXT,
            reported_to_doctor BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def report_side_effect(self, patient_id: str, medication_name: str,
                          side_effect: str, severity: str = "mild") -> Dict:
        """부작용 보고"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO side_effect_log
            (patient_id, medication_name, side_effect, severity, started_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (patient_id, medication_name, side_effect, severity, datetime.now()))

            conn.commit()
            conn.close()

            return {
                'success': True,
                'message': f"부작용 '{side_effect}'이 기록되었습니다",
                'recommendation': '약사나 의사에게 알려주세요'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ═══════════════════════════════════════════════════════════════
# 5. 유효기간 관리
# ═══════════════════════════════════════════════════════════════

class MedicationExpiry:
    """약물 유효기간 관리"""

    def __init__(self, db_path: str = "pharma_mobile.db"):
        self.db_path = db_path
        self._init_expiry_table()

    def _init_expiry_table(self):
        """유효기간 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medication_expiry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            purchase_date DATE,
            expiry_date DATE,
            quantity INTEGER,
            location TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def add_medication(self, patient_id: str, medication_name: str,
                      purchase_date: str, expiry_date: str, quantity: int) -> Dict:
        """약물 등록"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO medication_expiry
            (patient_id, medication_name, purchase_date, expiry_date, quantity)
            VALUES (?, ?, ?, ?, ?)
            ''', (patient_id, medication_name, purchase_date, expiry_date, quantity))

            conn.commit()
            conn.close()

            return {'success': True, 'message': f"'{medication_name}' 등록 완료"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_expiring(self, patient_id: str, days_ahead: int = 14) -> Dict:
        """곧 만료될 약물 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() + timedelta(days=days_ahead)).date()

            cursor.execute('''
            SELECT medication_name, expiry_date FROM medication_expiry
            WHERE patient_id = ? AND expiry_date <= ? AND status = 'active'
            ORDER BY expiry_date
            ''', (patient_id, cutoff_date))

            expiring = []
            for med_name, expiry_date in cursor.fetchall():
                days_left = (datetime.strptime(expiry_date, '%Y-%m-%d').date() - datetime.now().date()).days
                expiring.append({
                    'medication': med_name,
                    'expiry_date': expiry_date,
                    'days_left': days_left,
                    'status': '❌ 만료됨' if days_left < 0 else f'⏰ {days_left}일 남음'
                })

            conn.close()

            return {
                'success': True,
                'expiring_medications': expiring,
                'count': len(expiring),
                'message': f"{len(expiring)}개의 약물이 곧 만료됩니다" if expiring else "곧 만료될 약물이 없습니다"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    print("[INFO] Advanced Features Module")
