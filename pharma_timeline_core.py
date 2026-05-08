"""
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

PHARMA-HYBRID v19.2 - 다중 병원 약물 충돌 감시 & 타임라인 통합 코어
(Multi-Hospital Drug Collision & Timeline Integrated Core)

작성: TF팀 (신준호, 임대균, 박지현, 최영민)
최종 수정: 2026년 04월 26일

════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
"""

import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import hashlib
from collections import defaultdict
from pharma_v19_performance import ThreadSafeDatabasePool, performance, monitor

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. 환자 & 다중 병원 매니저 - 처방 이력 저장 및 관리
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

class PatientTimelineManager:
    """
    환자의 다중 병원 처방 이력을 데이터베이스에 저장하고 관리하는 클래스
    """
    
    def __init__(self, db_path=None):
        # [전술적 경로 확보] C: 드라이브가 없으면 로컬 디렉토리 사용
        if db_path is None:
            default_root = r'C:\PharmaProject'
            if not os.path.exists(os.path.dirname(default_root.split(':')[0] + ':')):
                default_root = os.path.join(os.getcwd(), 'PharmaProject_Local')
            db_path = os.path.join(default_root, 'database', 'pharma_timeline.db')
            
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.pool = ThreadSafeDatabasePool(self.db_path, pool_size=5)
        self.init_database()
    
    def init_database(self):
        """SQLite 데이터베이스 초기화 (v19.2 스키마 + 최적화 인덱스)"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. 환자 정보 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    medical_history TEXT,
                    allergies TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. 통합 처방 이력 테이블 (다중 병원 지원)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prescriptions (
                    prescription_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    hospital_name TEXT DEFAULT '본원',
                    hospital_id TEXT,
                    disease TEXT NOT NULL,
                    medication_1 TEXT,
                    medication_2 TEXT,
                    medication_3 TEXT,
                    medication_4 TEXT,
                    prescribed_date TIMESTAMP NOT NULL,
                    duration_days INTEGER,
                    duration_end TIMESTAMP,
                    prescriber TEXT,
                    notes TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            
            # 3. 병원 정보 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hospitals (
                    hospital_id TEXT PRIMARY KEY,
                    hospital_name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    department TEXT
                )
            """)
            
            # 4. 약물 스캔 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scanned_medications (
                    scan_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    medication_name TEXT NOT NULL,
                    scan_date TIMESTAMP NOT NULL,
                    scan_method TEXT,
                    image_path TEXT,
                    ocr_confidence REAL,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            
            # 5. 충돌 경고 로그
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collision_warnings (
                    warning_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    warning_type TEXT,
                    severity TEXT,
                    hospital_1 TEXT,
                    hospital_2 TEXT,
                    medication_1 TEXT,
                    medication_2 TEXT,
                    description TEXT,
                    recommendation TEXT,
                    detected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved INTEGER DEFAULT 0,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            
            # 인덱스 추가 (조회 속도 최적화)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_presc_patient ON prescriptions(patient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_presc_date ON prescriptions(prescribed_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_patient ON scanned_medications(patient_id)")
            
            conn.commit()
        finally:
            self.pool.return_connection(conn)
    
    @performance
    def add_patient(self, patient_id: str, name: str, age: int, gender: str, history: str = "", allergies: str = "") -> str:
        """환자 정보 등록 (성능 측정 포함)"""
        # 만약 patient_id가 None이면 해시로 생성
        if not patient_id:
            patient_id = hashlib.md5(name.encode()).hexdigest()[:8]
            
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO patients 
                (patient_id, name, age, gender, medical_history, allergies, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, name, age, gender, history, allergies, datetime.now()))
            conn.commit()
            return {"status": "success", "patient_id": patient_id}
        except Exception as e: return {"status": "error", "message": str(e)}
        finally:
            self.pool.return_connection(conn)

    @performance
    def add_hospital(self, hospital_id, hospital_name, address="", phone="", department=""):
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO hospitals VALUES (?, ?, ?, ?, ?)", 
                          (hospital_id, hospital_name, address, phone, department))
            conn.commit()
            return {"status": "success", "hospital": hospital_name}
        finally:
            self.pool.return_connection(conn)

    def get_patient(self, patient_id: str):
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "name": row[1], "age": row[2], "gender": row[3],
                    "history": row[4], "allergies": row[5]
                }
            return None
        finally:
            self.pool.return_connection(conn)

    @performance
    def add_prescription(self, patient_id: str, disease: str, 
                       medications: List[str], duration_days: int,
                       hospital_name: str = "본원", hospital_id: str = None,
                       prescriber: str = "", notes: str = "",
                       prescribed_date: str = None):
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # [신규] 과거 날짜 지원 로직
            if prescribed_date:
                try:
                    dt = datetime.strptime(prescribed_date, "%Y-%m-%d")
                except:
                    dt = datetime.now()
            else:
                dt = datetime.now()
                
            prescription_id = self._generate_id(f"{patient_id}_{disease}_{dt.isoformat()}")
            duration_end = dt + timedelta(days=duration_days)
            meds = medications + [None] * (4 - len(medications))
            
            cursor.execute("""
                INSERT INTO prescriptions 
                (prescription_id, patient_id, hospital_name, hospital_id, disease, 
                 medication_1, medication_2, medication_3, medication_4, 
                 prescribed_date, duration_days, duration_end, prescriber, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prescription_id, patient_id, hospital_name, hospital_id, disease, 
                  meds[0], meds[1], meds[2], meds[3], dt, duration_days, 
                  duration_end, prescriber, notes))
            conn.commit()
            return {"status": "success", "prescription_id": prescription_id}
        except Exception as e: return {"status": "error", "message": str(e)}
        finally:
            self.pool.return_connection(conn)
    
    @performance
    def scan_medications_today(self, patient_id: str, medications: List[str], 
                               scan_method: str = "OCR", image_path: str = ""):
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            scan_date = datetime.now()
            for med in medications:
                scan_id = self._generate_id(f"{patient_id}_{med}_{scan_date.isoformat()}")
                cursor.execute("""
                    INSERT INTO scanned_medications 
                    (scan_id, patient_id, medication_name, scan_date, scan_method, image_path, ocr_confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (scan_id, patient_id, med, scan_date, scan_method, image_path, 0.95))
            conn.commit()
            return {"status": "success", "count": len(medications)}
        except Exception as e: return {"status": "error", "message": str(e)}
        finally:
            self.pool.return_connection(conn)

    def get_all_patient_prescriptions(self, patient_id: str):
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prescription_id, hospital_name, hospital_id, disease,
                       medication_1, medication_2, medication_3, medication_4,
                       prescribed_date, duration_end, prescriber
                FROM prescriptions WHERE patient_id = ? ORDER BY prescribed_date DESC
            """, (patient_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append({
                    "id": r[0], "hospital": r[1], "hospital_id": r[2], "disease": r[3],
                    "meds": [m for m in r[4:8] if m], "date": r[8], "end": r[9], "doctor": r[10]
                })
            return result
        finally:
            self.pool.return_connection(conn)
    
    def _generate_id(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. 다중 병원 충돌 감시 엔진 - 심각/주의 수준 상호작용 분석
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

class MultiHospitalCollisionDetector:
    """다중 병원 약물 충돌 및 중복 복용 감시 엔진"""
    
    CRITICAL_INTERACTIONS = {
        ("아이부프로펜", "와파린"): {"severity": "🔴 심각", "score": 95, "desc": "위장관 출혈 위험 극도로 높음", "reco": "아이부프로펜 즉시 중단 및 아세트아미노펜 대체"},
        ("메트포르민", "알코올"): {"severity": "🔴 심각", "score": 90, "desc": "유산산증(락타산중독) 위험 - 치명적", "reco": "알코올 섭취 절대 금지"},
        ("메트포르민", "대조제"): {"severity": "🔴 심각", "score": 85, "desc": "급성 신부전 위험", "reco": "조영제 사용 전후 48시간 메트포르민 중단"}
    }
    
    WARNING_INTERACTIONS = {
        ("칼슘카보네이트", "리시노프릴"): {"severity": "🟡 주의", "score": 65, "desc": "약물 흡수 감소", "reco": "2시간 이상 간격 두고 섭취"},
        ("자몽", "암로디핀"): {"severity": "🟡 주의", "score": 70, "desc": "약물 농도 증가로 저혈압 위험", "reco": "자몽 섭취 제한"},
        ("아목시실린", "메트포르민"): {"severity": "🟡 주의", "score": 50, "desc": "혈당 변동 위험", "reco": "혈당 모니터링 강화"}
    }
    
    def detect_duplicates(self, patient_id, manager):
        prescriptions = manager.get_all_patient_prescriptions(patient_id)
        active_meds = defaultdict(list)
        now = datetime.now().isoformat()
        for rx in prescriptions:
            if rx['end'] and rx['end'] > now:
                for med in rx['meds']:
                    active_meds[med].append({"hospital": rx['hospital'], "doctor": rx['doctor']})
        
        duplicates = {m: h for m, h in active_meds.items() if len(h) > 1}
        return {"count": len(duplicates), "data": duplicates}

    def detect_interactions(self, patient_id, manager, current_scanned=[]):
        prescriptions = manager.get_all_patient_prescriptions(patient_id)
        active_meds = set(current_scanned)
        now = datetime.now().isoformat()
        for rx in prescriptions:
            if rx['end'] and rx['end'] > now:
                active_meds.update(rx['meds'])
        
        critical = []
        warning = []
        meds_list = list(active_meds)
        for i in range(len(meds_list)):
            for j in range(i+1, len(meds_list)):
                med1, med2 = meds_list[i], meds_list[j]
                key = tuple(sorted([med1, med2]))
                if key in self.CRITICAL_INTERACTIONS:
                    it = self.CRITICAL_INTERACTIONS[key]
                    critical.append({"med1": med1, "med2": med2, "severity": it['severity'], "score": it['score'], "desc": it['desc'], "reco": it['reco']})
                elif key in self.WARNING_INTERACTIONS:
                    it = self.WARNING_INTERACTIONS[key]
                    warning.append({"med1": med1, "med2": med2, "severity": it['severity'], "score": it['score'], "desc": it['desc'], "reco": it['reco']})
        
        return {"critical": critical, "warning": warning}

class PHARMAHYBRIDv19_Core:
    def __init__(self):
        self.manager = PatientTimelineManager()
        self.detector = MultiHospitalCollisionDetector()
        
    def analyze_full_risk(self, patient_id, current_meds=[]):
        duplicates = self.detector.detect_duplicates(patient_id, self.manager)
        interactions = self.detector.detect_interactions(patient_id, self.manager, current_meds)
        return {
            "duplicates": duplicates,
            "interactions": interactions
        }
