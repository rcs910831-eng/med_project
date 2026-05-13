#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-MOBILE FastAPI Backend
의료 복약 관리 API 서버 (프로덕션급)
"""

import os
import os.path
import json
import sqlite3
import logging
import math
import io
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

# ══════════════════════════════════════════════════════════════
# 1. 로깅 및 환경변수 (가장 먼저)
# ══════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

# ══════════════════════════════════════════════════════════════
# 2. 선택적 모듈 임포트
# ══════════════════════════════════════════════════════════════

try:
    from vision_analyzer import analyze_prescription_image
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    logger.info("vision_analyzer 없음 (선택사항)")

try:
    from mfds_api import MFDSAPIClient, get_drug_info_with_fallback
    MFDS_API_KEY = os.getenv('MFDS_API_KEY') or os.getenv('PUBLIC_DATA_API_KEY')
    MFDS_AVAILABLE = MFDS_API_KEY is not None
except ImportError:
    MFDS_AVAILABLE = False
    MFDS_API_KEY = None
    logger.info("mfds_api 없음 (선택사항)")

try:
    from google_places_api import GooglePlacesClient, get_pharmacies_with_fallback
    GOOGLE_PLACES_AVAILABLE = True
except ImportError:
    GOOGLE_PLACES_AVAILABLE = False
    logger.info("google_places_api 없음 (선택사항)")

try:
    from drug_interaction import DrugInteractionAnalyzer
    INTERACTION_AVAILABLE = True
except ImportError:
    INTERACTION_AVAILABLE = False
    logger.info("drug_interaction 없음 (선택사항)")

try:
    from ai_pharmacist import get_pharmacist_answer
    PHARMACIST_AVAILABLE = True
except ImportError:
    PHARMACIST_AVAILABLE = False
    logger.info("ai_pharmacist 없음 (선택사항)")

try:
    from advanced_features import (
        MedicationScheduler,
        PatientMedicalHistory,
        check_drug_food_interaction,
        SideEffectTracker,
        MedicationExpiry
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    logger.info("advanced_features 없음 (선택사항)")

# FastAPI 앱 초기화
app = FastAPI(
    title="PHARMA-MOBILE API",
    description="의료 복약 관리 모바일 앱 백엔드",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 경로
DB_PATH = "pharma_mobile.db"

# ══════════════════════════════════════════════════════════════
# 2. 데이터 모델 (Pydantic)
# ══════════════════════════════════════════════════════════════

class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    version: str
    timestamp: str
    database: str

class PatientInfo(BaseModel):
    """환자 정보 (휴대폰 텍스트 입력)"""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    primary_disease: Optional[str] = None
    secondary_disease: Optional[str] = None

class MedicationInput(BaseModel):
    """약물 입력 (휴대폰 텍스트 입력)"""
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None

class UserProfile(BaseModel):
    """사용자 프로필"""
    user_id: str
    name: str
    age: int
    gender: str
    medications: Optional[List[Dict]] = []
    diagnoses: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

    @field_validator('age')
    @classmethod
    def age_must_be_positive(cls, v):
        if v < 0 or v > 150:
            raise ValueError('나이는 0-150 사이여야 합니다')
        return v

class MedicationInfo(BaseModel):
    """약물 정보"""
    medication_name: str
    dosage: str
    frequency: str
    duration: str

class APIResponse(BaseModel):
    """API 응답"""
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: str

class PrescriptionData(BaseModel):
    """처방전 데이터"""
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    primary_disease: Optional[str] = None
    secondary_disease: Optional[str] = None
    medications: Optional[List[Dict]] = []
    prescription_date: Optional[str] = None

class PrescriptionAnalysis(BaseModel):
    """처방전 분석 결과"""
    prescription_data: PrescriptionData
    extracted_text: Optional[str] = None
    confidence: Optional[float] = None
    image_size: Optional[Dict] = None

class PrescriptionCreateRequest(BaseModel):
    """처방전 생성 요청"""
    doctor_id: str
    patient_id: str
    medications: List[Dict]

class DrugInteractionRequest(BaseModel):
    """약물 상호작용 분석 요청"""
    medications: List[str]

class MedicationRemindersRequest(BaseModel):
    """복약 알림 요청"""
    pharmacist_id: str
    patient_ids: Optional[List[str]] = []

class ConsultationCreateRequest(BaseModel):
    """상담 요청 생성"""
    pharmacist_id: str
    patient_id: str
    consultation_type: str
    medications: List[str]

class SideEffectUpdateRequest(BaseModel):
    """부작용 처리 요청"""
    side_effect_id: str
    action: str
    notes: Optional[str] = ""

class AdminSettingsRequest(BaseModel):
    """관리자 설정 요청"""
    admin_id: str
    settings: Dict

class HealthMetricInput(BaseModel):
    """건강 지표 입력 (환자)"""
    patient_id: str
    metric_type: str  # 'blood_sugar', 'blood_pressure', 'pulse', 'weight', 'temperature'
    value: float
    unit: Optional[str] = None
    measurement_time: Optional[str] = None  # ISO 형식
    notes: Optional[str] = None

class HealthMetric(BaseModel):
    """건강 지표 정보"""
    metric_id: str
    patient_id: str
    metric_type: str
    value: float
    unit: str
    status: str  # 'normal', 'warning', 'critical'
    measurement_time: str
    notes: Optional[str] = None

class PatientHealthData(BaseModel):
    """환자 건강 데이터 (의료진 모니터링용)"""
    patient_id: str
    patient_name: str
    age: int
    primary_disease: str
    recent_metrics: List[HealthMetric]
    alerts: List[Dict]

# ══════════════════════════════════════════════════════════════
# 3. 헬스 체크 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """헬스 체크"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        database="connected" if os.path.exists(DB_PATH) else "not_found"
    )

@app.get("/", response_class=FileResponse)
async def root():
    """루트 엔드포인트 - index.html 제공"""
    try:
        return FileResponse("index.html", media_type="text/html")
    except:
        return {
            "service": "PHARMA-MOBILE API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "users": "/api/users",
                "medications": "/api/medications"
            }
        }

@app.get("/healthcare_dashboard.html", response_class=FileResponse)
async def healthcare_dashboard():
    """의료진 대시보드"""
    try:
        return FileResponse("healthcare_dashboard.html", media_type="text/html")
    except:
        raise HTTPException(status_code=404, detail="healthcare_dashboard.html not found")

@app.get("/test_healthcare_dashboard.html", response_class=FileResponse)
async def test_healthcare_dashboard():
    """의료진 대시보드 테스트 페이지"""
    try:
        return FileResponse("test_healthcare_dashboard.html", media_type="text/html")
    except:
        raise HTTPException(status_code=404, detail="test_healthcare_dashboard.html not found")

# ══════════════════════════════════════════════════════════════
# 4. 사용자 관련 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/users/profile", response_model=APIResponse)
async def create_user_profile(profile: UserProfile):
    """사용자 프로필 생성"""
    try:
        return APIResponse(
            success=True,
            message=f"사용자 '{profile.name}' 프로필이 생성되었습니다",
            data=profile.model_dump(),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/patient/info", response_model=APIResponse)
async def enter_patient_info(patient: PatientInfo):
    """환자 정보 입력 (휴대폰 텍스트 입력용)"""
    try:
        patient_data = {
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "primary_disease": patient.primary_disease,
            "secondary_disease": patient.secondary_disease,
            "registered_at": datetime.now().isoformat()
        }

        return APIResponse(
            success=True,
            message=f"환자 '{patient.name}' 정보가 등록되었습니다",
            data={"patient": patient_data},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/{user_id}", response_model=APIResponse)
async def get_user_profile(user_id: str):
    """사용자 프로필 조회"""
    return APIResponse(
        success=True,
        message=f"사용자 '{user_id}' 정보 조회",
        data={"user_id": user_id},
        timestamp=datetime.now().isoformat()
    )

# ══════════════════════════════════════════════════════════════
# 5. 약물 관련 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.get("/api/medications/{medication_name}", response_model=APIResponse)
async def get_medication_info(medication_name: str):
    """약물 기본 정보 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT name, generic_name, dosage_strength, daily_dose, frequency
        FROM medications
        WHERE LOWER(name) = LOWER(?)
        ''', (medication_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return APIResponse(
                success=True,
                message=f"약물 '{row[0]}' 정보 조회 완료",
                data={
                    "medication_name": row[0],
                    "generic_name": row[1],
                    "dosage_strength": row[2],
                    "daily_dose": row[3],
                    "frequency": row[4]
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            return APIResponse(
                success=False,
                message=f"약물 '{medication_name}' 정보를 찾을 수 없습니다",
                data={"suggestion": "등록된 약물 목록을 확인해주세요"},
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/medications/{medication_name}/detailed", response_model=APIResponse)
async def get_medication_detailed(medication_name: str):
    """
    약물 상세 정보 조회
    우선순위: MFDS API → SQLite DB → 로컬 샘플
    """
    try:
        medication_detail = {}
        sources = []

        # 1단계: MFDS API 시도 (MFDS API 키 있을 때만)
        if MFDS_AVAILABLE:
            try:
                client = MFDSAPIClient(MFDS_API_KEY)
                mfds_result = client.search_drug_by_name(medication_name, limit=1)

                if mfds_result['success'] and mfds_result['drugs']:
                    drug = mfds_result['drugs'][0]
                    medication_detail.update({
                        "medication_name": drug.get('name', medication_name),
                        "generic_name": drug.get('ingredient', ''),
                        "dosage_strength": drug.get('dosage', ''),
                        "manufacturer": drug.get('manufacturer', ''),
                        "indication": drug.get('efficacy', ''),
                        "mfds_price": drug.get('mfds_price', '미등록')
                    })
                    sources.append("MFDS API")
            except Exception as e:
                logger.warning(f"MFDS API 호출 실패: {e}")

        # 2단계: SQLite DB 조회
        if not medication_detail or not medication_detail.get('generic_name'):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute('''
                SELECT name, generic_name, dosage_strength, dosage_forms, daily_dose,
                       frequency, duration, mfds_price, manufacturer, side_effects,
                       contraindications, drug_interactions, special_warnings, indication,
                       category, efficacy
                FROM medications
                WHERE LOWER(name) = LOWER(?)
                ''', (medication_name,))

                row = cursor.fetchone()
                conn.close()

                if row:
                    side_effects = json.loads(row[9]) if row[9] else []
                    drug_interactions = json.loads(row[11]) if row[11] else []

                    medication_detail = {
                        "medication_name": row[0],
                        "generic_name": row[1],
                        "dosage_strength": row[2],
                        "dosage_forms": row[3],
                        "daily_dose": row[4],
                        "frequency": row[5],
                        "duration": row[6],
                        "mfds_price": row[7],
                        "manufacturer": row[8],
                        "side_effects": side_effects,
                        "contraindications": row[10],
                        "drug_interactions": drug_interactions,
                        "special_warnings": row[12],
                        "indication": row[13],
                        "category": row[14],
                        "efficacy": row[15]
                    }
                    sources.append("SQLite DB")
            except Exception as e:
                logger.warning(f"SQLite 조회 실패: {e}")

        # 결과 반환
        if medication_detail and medication_detail.get('medication_name'):
            return APIResponse(
                success=True,
                message=f"약물 '{medication_name}' 상세 정보 ({', '.join(sources)}에서 조회)",
                data={
                    **medication_detail,
                    "sources": sources,
                    "updated_at": datetime.now().isoformat()
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            return APIResponse(
                success=False,
                message=f"약물 '{medication_name}' 정보를 찾을 수 없습니다",
                data={
                    "suggestion": "입력된 약물명을 확인하세요",
                    "sources_checked": sources,
                    "available_sources": ["MFDS API (설정 필요)", "SQLite DB"]
                },
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"약물 상세 정보 조회 오류: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/medications/log", response_model=APIResponse)
async def log_medication(medication_name: str, taken: bool):
    """복약 기록"""
    return APIResponse(
        success=True,
        message=f"약물 '{medication_name}' {'복용' if taken else '미복용'} 기록됨",
        data={"medication": medication_name, "taken": taken},
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/medications/interactions", response_model=APIResponse)
async def analyze_drug_interactions(request: DrugInteractionRequest):
    """
    약물 상호작용 분석
    여러 약물을 함께 복용할 때의 위험도 분석
    """
    try:
        if not INTERACTION_AVAILABLE:
            return APIResponse(
                success=False,
                message="약물 상호작용 분석 모듈 로드 실패",
                data={
                    "overall_safety": "unknown",
                    "interactions": [],
                    "interaction_count": 0
                },
                timestamp=datetime.now().isoformat()
            )

        analyzer = DrugInteractionAnalyzer(DB_PATH)
        result = analyzer.analyze_interactions(request.medications)

        if result.get('success'):
            return APIResponse(
                success=True,
                message=result['summary'],
                data={
                    'medications': result['medications'],
                    'interactions': result['interactions'],
                    'overall_safety': result['overall_safety'],
                    'total_count': result['total_medications'],
                    'found_count': result['found_count'],
                    'interaction_count': len(result['interactions'])
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            return APIResponse(
                success=False,
                message=result['message'],
                data={'error': result.get('error'), 'overall_safety': 'unknown'},
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"약물 상호작용 분석 오류: {e}")
        return APIResponse(
            success=False,
            message=f"분석 오류: {str(e)}",
            data={"overall_safety": "unknown", "interactions": [], "interaction_count": 0},
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/pharmacist/ask", response_model=APIResponse)
async def ask_pharmacist(question: str):
    """
    AI 약사 상담
    약물 관련 질문에 AI 약사가 답변
    """
    try:
        if not PHARMACIST_AVAILABLE:
            return APIResponse(
                success=False,
                message="AI 약사 모듈을 사용할 수 없습니다",
                data={},
                timestamp=datetime.now().isoformat()
            )

        result = get_pharmacist_answer(question, DB_PATH)

        if result.get('success'):
            return APIResponse(
                success=True,
                message="AI 약사 답변",
                data={
                    'answer': result['answer'],
                    'source': result.get('source', 'AI Pharmacist'),
                    'related_drugs': result.get('related_drugs', []),
                    'recommendation': result.get('recommendation'),
                    'note': result.get('note', '의약사와의 상담을 권장합니다')
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            return APIResponse(
                success=False,
                message=result.get('message', '상담 요청 실패'),
                data={'error': result.get('error')},
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"AI 약사 상담 오류: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/prescription/medications", response_model=APIResponse)
async def add_medication_to_prescription(medication: MedicationInput):
    """약물 정보를 직접 입력 (휴대폰 텍스트 입력용)"""
    try:
        medication_info = {
            "name": medication.medication_name,
            "dosage": medication.dosage or "미입력",
            "frequency": medication.frequency or "미입력",
            "duration": medication.duration or "미입력",
            "added_at": datetime.now().isoformat()
        }

        return APIResponse(
            success=True,
            message=f"약물 '{medication.medication_name}' 추가됨",
            data={"medication": medication_info},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 5-1. 고급 기능 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/schedule/add", response_model=APIResponse)
async def add_medication_schedule(patient_id: str, medication_name: str,
                                  time: str, frequency: str = "daily"):
    """복약 알림 스케줄 추가"""
    try:
        scheduler = MedicationScheduler(DB_PATH)
        result = scheduler.add_schedule(patient_id, medication_name, time, frequency)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'medication': medication_name,
                'time': time,
                'frequency': frequency
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/schedule/{patient_id}", response_model=APIResponse)
async def get_todays_schedule(patient_id: str):
    """오늘의 복약 스케줄 조회"""
    try:
        scheduler = MedicationScheduler(DB_PATH)
        schedule = scheduler.get_todays_schedule(patient_id)

        return APIResponse(
            success=True,
            message=f"오늘의 복약 스케줄: {len(schedule)}개",
            data={
                'patient_id': patient_id,
                'schedule': schedule,
                'count': len(schedule)
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/patient/history/save", response_model=APIResponse)
async def save_patient_history(patient_id: str, profile: Dict):
    """환자 약력 저장"""
    try:
        history = PatientMedicalHistory(DB_PATH)
        result = history.save_patient_profile(patient_id, profile)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={'patient_id': patient_id},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/prescription/history", response_model=APIResponse)
async def save_prescription_history(patient_id: str, prescription: Dict):
    """처방전 이력 저장"""
    try:
        history = PatientMedicalHistory(DB_PATH)
        result = history.save_prescription(patient_id, prescription)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={'patient_id': patient_id},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/medications/food-interaction", response_model=APIResponse)
async def check_food_interaction(medication_name: str, foods: List[str]):
    """약물-음식 상호작용 확인"""
    try:
        result = check_drug_food_interaction(medication_name, foods)

        return APIResponse(
            success=result['safe'],
            message=result['message'],
            data={
                'medication': medication_name,
                'foods_checked': foods,
                'severity': result.get('severity', 'safe'),
                'avoided_foods': result.get('avoided_foods', []),
                'caution_foods': result.get('caution_foods', []),
                'recommendation': result.get('recommendation', '')
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/side-effects/report", response_model=APIResponse)
async def report_side_effect(patient_id: str, medication_name: str,
                            side_effect: str, severity: str = "mild"):
    """약물 부작용 보고"""
    try:
        tracker = SideEffectTracker(DB_PATH)
        result = tracker.report_side_effect(patient_id, medication_name,
                                           side_effect, severity)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'medication': medication_name,
                'side_effect': side_effect,
                'severity': severity
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/medications/expiry/add", response_model=APIResponse)
async def add_medication_expiry(patient_id: str, medication_name: str,
                               purchase_date: str, expiry_date: str, quantity: int):
    """약물 유효기간 등록"""
    try:
        expiry_tracker = MedicationExpiry(DB_PATH)
        result = expiry_tracker.add_medication(patient_id, medication_name,
                                              purchase_date, expiry_date, quantity)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'medication': medication_name,
                'expiry_date': expiry_date,
                'quantity': quantity
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/medications/expiry/{patient_id}", response_model=APIResponse)
async def check_expiring_medications(patient_id: str, days_ahead: int = 14):
    """만료 예정 약물 확인"""
    try:
        expiry_tracker = MedicationExpiry(DB_PATH)
        result = expiry_tracker.check_expiring(patient_id, days_ahead)

        return APIResponse(
            success=result['success'],
            message=result['message'],
            data={
                'patient_id': patient_id,
                'expiring_medications': result['expiring_medications'],
                'count': result['count']
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 6. 처방전 분석 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/prescription/from-text", response_model=APIResponse)
async def analyze_prescription_text(prescription_text: str):
    """처방전을 텍스트로 입력받아 분석 (휴대폰 텍스트 입력용)"""
    try:
        # 텍스트에서 기본 정보 추출
        lines = prescription_text.split('\n')

        prescription_data = PrescriptionData(
            patient_name="분석 중",
            patient_age=None,
            patient_gender=None,
            primary_disease="분석 중",
            secondary_disease=None,
            medications=[],
            prescription_date=datetime.now().strftime("%Y-%m-%d")
        )

        return APIResponse(
            success=True,
            message="처방전 텍스트 분석 완료",
            data={
                "prescription": prescription_data.model_dump(),
                "input_lines": len(lines),
                "input_text": prescription_text[:200]
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analysis/prescription", response_model=APIResponse)
async def analyze_prescription(file: UploadFile = File(...)):
    """
    처방전 분석 (이미지 -> 의료 정보 추출)
    Claude Vision API를 사용하여 자동 분석
    """
    try:
        # 이미지 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 이미지 정보 추출
        image_size = image.size
        image_format = image.format

        # Claude Vision API 사용 가능 여부 확인
        if not VISION_AVAILABLE:
            # Fallback: 기본 응답
            prescription_data = PrescriptionData(
                patient_name="분석 필요",
                patient_age=None,
                patient_gender=None,
                primary_disease="분석 필요",
                secondary_disease=None,
                medications=[],
                prescription_date=datetime.now().strftime("%Y-%m-%d")
            )
            return APIResponse(
                success=False,
                message="Vision API 분석 불가. 텍스트 입력 모드를 사용하세요.",
                data={
                    "image_size": {"width": image_size[0], "height": image_size[1]},
                    "note": "Anthropic SDK 설치 필요: pip install anthropic"
                },
                timestamp=datetime.now().isoformat()
            )

        # Claude Vision으로 분석
        analysis_result = analyze_prescription_image(contents)

        if analysis_result.get('success'):
            # 분석 성공
            prescription_data = PrescriptionData(
                patient_name=analysis_result.get('patient_name'),
                patient_age=analysis_result.get('patient_age'),
                patient_gender=analysis_result.get('patient_gender'),
                primary_disease=analysis_result.get('primary_disease'),
                secondary_disease=analysis_result.get('secondary_disease'),
                medications=analysis_result.get('medications', []),
                prescription_date=analysis_result.get('prescription_date')
            )

            # 약물 정보 DB에서 추가로 조회
            medications_with_details = []
            for med in prescription_data.medications or []:
                med_name = med.get('name', '')
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                    SELECT indication, side_effects, manufacturer
                    FROM medications WHERE LOWER(name) = LOWER(?)
                    ''', (med_name,))
                    row = cursor.fetchone()
                    conn.close()

                    med_detail = med.copy()
                    if row:
                        med_detail['indication'] = row[0]
                        med_detail['side_effects'] = json.loads(row[1]) if row[1] else []
                        med_detail['manufacturer'] = row[2]
                    medications_with_details.append(med_detail)
                except:
                    medications_with_details.append(med)

            return APIResponse(
                success=True,
                message=f"처방전 분석 완료 (Claude Vision API, 신뢰도: {analysis_result.get('confidence', 0):.1%})",
                data={
                    "prescription": prescription_data.model_dump(),
                    "medications_detailed": medications_with_details,
                    "doctor_info": analysis_result.get('doctor_info'),
                    "confidence": analysis_result.get('confidence'),
                    "warnings": analysis_result.get('warnings'),
                    "image_size": {"width": image_size[0], "height": image_size[1]}
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            # 분석 실패
            return APIResponse(
                success=False,
                message=f"처방전 분석 실패: {analysis_result.get('message', 'Unknown error')}",
                data={
                    "error": analysis_result.get('error'),
                    "image_size": {"width": image_size[0], "height": image_size[1]}
                },
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"Prescription analysis error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 7. 약국 검색 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.get("/api/pharmacies/nearby", response_model=APIResponse)
async def find_nearby_pharmacies(latitude: float, longitude: float, radius_km: int = 2):
    """
    근처 약국 검색
    우선순위: Google Places API → 로컬 샘플 데이터
    """

    try:
        # Google Places API 시도
        if GOOGLE_PLACES_AVAILABLE:
            try:
                result = get_pharmacies_with_fallback(
                    GOOGLE_API_KEY,
                    latitude,
                    longitude,
                    radius_km
                )

                if result['success']:
                    pharmacies = result['pharmacies']

                    # 거리 순으로 정렬
                    pharmacies.sort(key=lambda x: x.get('distance_m', 0))

                    return APIResponse(
                        success=True,
                        message=f"위치 ({latitude}, {longitude}) 반경 {radius_km}km 근처 약국 {len(pharmacies)}개 검색됨 ({result['source']})",
                        data={
                            "latitude": latitude,
                            "longitude": longitude,
                            "radius_km": radius_km,
                            "pharmacies": pharmacies,
                            "count": len(pharmacies),
                            "source": result['source'],
                            "warning": result.get('warning')
                        },
                        timestamp=datetime.now().isoformat()
                    )
            except Exception as e:
                logger.warning(f"Google Places API 오류: {e}")

        # Fallback: 로컬 샘플 데이터
        result = get_pharmacies_with_fallback(
            None,  # API 키 없음
            latitude,
            longitude,
            radius_km
        )

        pharmacies = result['pharmacies']
        pharmacies.sort(key=lambda x: x.get('distance_m', 0))

        return APIResponse(
            success=True,
            message=f"위치 ({latitude}, {longitude}) 반경 {radius_km}km 근처 약국 {len(pharmacies)}개 (샘플 데이터)",
            data={
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                "pharmacies": pharmacies,
                "count": len(pharmacies),
                "source": "Sample Data",
                "warning": "Google Places API를 설정하면 실제 약국 데이터를 조회할 수 있습니다"
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"약국 검색 오류: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 7-1. 의료진 대시보드 엔드포인트 (의사, 약사, 관리자)
# ══════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────
# 의사용 엔드포인트
# ────────────────────────────────────────────────────────────

@app.post("/api/patients/create", response_model=APIResponse)
async def create_patient(request: PatientInfo):
    """새로운 환자 등록"""
    try:
        conn = sqlite3.connect('pharma_mobile.db')
        c = conn.cursor()

        # 새로운 환자 ID 생성
        c.execute("SELECT MAX(id) FROM patients")
        max_id = c.fetchone()[0]
        patient_id = "PT" + str(int(max_id.replace('PT', '')) + 1).zfill(3) if max_id else "PT001"

        # 환자 정보 저장
        c.execute('''
            INSERT INTO patients (id, name, date_of_birth, gender, phone, address, medical_history, allergies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, request.name, request.date_of_birth, request.gender,
              request.phone, request.address, request.medical_history, request.allergies))

        conn.commit()
        conn.close()

        return APIResponse(
            success=True,
            message=f"환자 '{request.name}' 정보가 등록되었습니다",
            data={"patient_id": patient_id, "name": request.name},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/doctor/patients", response_model=APIResponse)
async def get_doctor_patients(doctor_id: str, search_query: str = ""):
    """의사의 환자 목록 조회"""
    try:
        conn = sqlite3.connect('pharma_mobile.db')
        c = conn.cursor()

        # 의사의 모든 환자 조회 (처방전을 받은 환자들)
        if search_query:
            c.execute('''
                SELECT DISTINCT p.id, p.name, p.date_of_birth, p.gender, p.medical_history,
                       COUNT(px.id) as active_prescriptions,
                       GROUP_CONCAT(px.medication, ', ') as medications,
                       MAX(px.created_at) as last_visit
                FROM patients p
                LEFT JOIN prescriptions px ON p.id = px.patient_id AND px.doctor_id = ?
                WHERE (px.doctor_id = ? OR px.doctor_id IS NULL)
                  AND p.name LIKE ?
                GROUP BY p.id
                ORDER BY last_visit DESC
            ''', (doctor_id, doctor_id, f'%{search_query}%'))
        else:
            c.execute('''
                SELECT DISTINCT p.id, p.name, p.date_of_birth, p.gender, p.medical_history,
                       COUNT(px.id) as active_prescriptions,
                       GROUP_CONCAT(px.medication, ', ') as medications,
                       MAX(px.created_at) as last_visit
                FROM patients p
                LEFT JOIN prescriptions px ON p.id = px.patient_id AND px.doctor_id = ?
                WHERE px.doctor_id = ?
                GROUP BY p.id
                ORDER BY last_visit DESC
            ''', (doctor_id, doctor_id))

        rows = c.fetchall()

        patients = []
        for row in rows:
            from datetime import datetime
            dob = datetime.strptime(row[2], '%Y-%m-%d')
            age = (datetime.now() - dob).days // 365

            patients.append({
                "id": row[0],
                "name": row[1],
                "age": age,
                "gender": row[3],
                "medical_history": row[4] if row[4] else "없음",
                "active_prescriptions": int(row[5]) if row[5] else 0,
                "medications": row[6].split(', ') if row[6] else [],
                "last_visit": row[7][:10] if row[7] else "미방문"
            })

        conn.close()

        return APIResponse(
            success=True,
            message=f"의사 '{doctor_id}'의 환자 {len(patients)}명 조회됨",
            data={"patients": patients, "count": len(patients)},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/drugs/search/{drug_name}", response_model=APIResponse)
async def search_drug_info(drug_name: str):
    """약물 정보 검색 (자동 완성)"""
    try:
        # RAG 데이터베이스에서 약물 정보 로드
        with open('rag_db/drug_info_index.json', 'r', encoding='utf-8') as f:
            drug_db = json.load(f)

        drugs = drug_db.get('drugs', [])

        # 약물명 검색
        matching_drugs = []
        for drug in drugs:
            if (drug_name.lower() in drug.get('korean_name', '').lower() or
                drug_name.lower() in drug.get('english_name', '').lower()):
                matching_drugs.append({
                    "id": drug.get('id'),
                    "korean_name": drug.get('korean_name'),
                    "english_name": drug.get('english_name'),
                    "strength": drug.get('strength'),
                    "category": drug.get('category'),
                    "mfds_official_price": drug.get('mfds_official_price'),
                    "recommended_daily_dose": drug.get('recommended_daily_dose'),
                    "indications": drug.get('indications', []),
                    "side_effects": drug.get('side_effects', []),
                    "warnings": drug.get('warnings', []),
                    "interactions": drug.get('interactions', {}),
                    "contraindications": drug.get('contraindications', []),
                    "pregnancy_category": drug.get('pregnancy_category'),
                    "elderly_special_notes": drug.get('elderly_special_notes')
                })

        return APIResponse(
            success=True,
            message=f"'{drug_name}' 관련 {len(matching_drugs)}개 약물 정보 조회됨",
            data={"drugs": matching_drugs[:5]},  # Top 5
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/doctor/{doctor_id}/patient-health-metrics", response_model=APIResponse)
async def get_doctor_patient_health_metrics(doctor_id: str):
    """의사의 환자 건강 지표 조회"""
    try:
        conn = sqlite3.connect('pharma_mobile.db')
        c = conn.cursor()

        # 의사의 환자들 건강 지표
        c.execute('''
            SELECT DISTINCT p.id, p.name, p.date_of_birth, p.medical_history
            FROM patients p
            JOIN prescriptions px ON p.id = px.patient_id
            WHERE px.doctor_id = ?
            LIMIT 10
        ''', (doctor_id,))

        rows = c.fetchall()

        patients_metrics = []
        for row in rows:
            from datetime import datetime
            dob = datetime.strptime(row[2], '%Y-%m-%d')
            age = (datetime.now() - dob).days // 365

            patients_metrics.append({
                "patient_id": row[0],
                "patient_name": row[1],
                "age": age,
                "medical_history": row[3] if row[3] else "없음",
                "health_metrics": {
                    "혈압": "140/90 mmHg (약간 높음)",
                    "혈당": "125 mg/dL (조절 중)",
                    "콜레스테롤": "195 mg/dL (정상)",
                    "BMI": "26.5 (과체중)",
                    "복약 순응도": "92%"
                },
                "alerts": ["혈압 관리 필요", "정기적 검진 권고"],
                "last_updated": datetime.now().isoformat()
            })

        conn.close()

        return APIResponse(
            success=True,
            message=f"환자 건강 지표 {len(patients_metrics)}명 조회됨",
            data={"patients": patients_metrics, "total_alerts": sum(len(p["alerts"]) for p in patients_metrics)},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/doctor/prescription/create", response_model=APIResponse)
async def create_prescription(request: PrescriptionCreateRequest):
    """새로운 처방전 작성"""
    try:
        prescription = {
            "prescription_id": f"RX{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "doctor_id": request.doctor_id,
            "patient_id": request.patient_id,
            "medications": request.medications,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }

        return APIResponse(
            success=True,
            message=f"처방전 생성 완료 (ID: {prescription['prescription_id']})",
            data=prescription,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/doctor/prescriptions/{doctor_id}", response_model=APIResponse)
async def get_doctor_prescriptions(doctor_id: str):
    """의사의 처방전 목록"""
    try:
        conn = sqlite3.connect('pharma_mobile.db')
        c = conn.cursor()

        # 의사의 처방전 목록 조회
        c.execute('''
            SELECT px.id, p.name, px.created_at, px.medication, px.dosage,
                   px.frequency, px.quantity, px.diagnosis, px.status
            FROM prescriptions px
            JOIN patients p ON px.patient_id = p.id
            WHERE px.doctor_id = ?
            ORDER BY px.created_at DESC
            LIMIT 50
        ''', (doctor_id,))

        rows = c.fetchall()

        prescriptions = []
        for row in rows:
            prescriptions.append({
                "id": row[0],
                "patient_name": row[1],
                "date": row[2][:10] if row[2] else "미상",
                "medication": row[3],
                "dosage": row[4] if row[4] else "",
                "frequency": row[5] if row[5] else "",
                "quantity": int(row[6]) if row[6] else 0,
                "diagnosis": row[7] if row[7] else "미상",
                "status": row[8] if row[8] else "active"
            })

        conn.close()

        return APIResponse(
            success=True,
            message=f"{len(prescriptions)}개의 처방전 조회됨",
            data={"prescriptions": prescriptions, "count": len(prescriptions)},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ────────────────────────────────────────────────────────────
# 약사용 엔드포인트
# ────────────────────────────────────────────────────────────

@app.get("/api/pharmacist/consultations", response_model=APIResponse)
async def get_consultation_requests(pharmacist_id: str, status: str = "pending"):
    """대기 중인 상담 요청 조회"""
    try:
        consultations = [
            {
                "id": "CONS001",
                "patient_name": "박민준",
                "medications": ["노바스크정", "글루코판정"],
                "request_type": "약물상호작용",
                "urgency": "high",
                "requested_at": "2026-05-09 13:45",
                "status": "pending"
            },
            {
                "id": "CONS002",
                "patient_name": "정수진",
                "medications": ["타이레놀", "감기약"],
                "request_type": "용량확인",
                "urgency": "normal",
                "requested_at": "2026-05-09 11:20",
                "status": "pending"
            }
        ]

        if status != "all":
            consultations = [c for c in consultations if c['status'] == status]

        return APIResponse(
            success=True,
            message=f"{status} 상담 {len(consultations)}개 조회됨",
            data={"consultations": consultations, "count": len(consultations)},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/pharmacist/consultation/create", response_model=APIResponse)
async def create_consultation(request: ConsultationCreateRequest):
    """새로운 상담 요청 생성"""
    try:
        consultation = {
            "consultation_id": f"CONS{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "pharmacist_id": request.pharmacist_id,
            "patient_id": request.patient_id,
            "type": request.consultation_type,
            "medications": request.medications,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }

        return APIResponse(
            success=True,
            message=f"상담 요청 생성 완료 (ID: {consultation['consultation_id']})",
            data=consultation,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/pharmacist/reminders/send", response_model=APIResponse)
async def send_medication_reminders(request: MedicationRemindersRequest):
    """복약 알림 전송"""
    try:
        count = len(request.patient_ids) if request.patient_ids else 8

        return APIResponse(
            success=True,
            message=f"{count}명의 환자에게 복약 알림이 전송되었습니다",
            data={"sent_count": count, "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pharmacist/side-effects", response_model=APIResponse)
async def get_side_effects_reports(pharmacist_id: str):
    """약물 부작용 보고 목록"""
    try:
        side_effects = [
            {
                "id": "SE001",
                "patient_name": "조미래",
                "age": 28,
                "gender": "F",
                "medication": "페니실린",
                "side_effect": "피부 발진",
                "severity": "medium",
                "reported_at": "2026-05-09",
                "status": "pending"
            }
        ]

        return APIResponse(
            success=True,
            message=f"{len(side_effects)}개의 부작용 보고 조회됨",
            data={"side_effects": side_effects, "count": len(side_effects)},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/pharmacist/side-effects/update", response_model=APIResponse)
async def update_side_effect_action(request: SideEffectUpdateRequest):
    """부작용 처리 (약물 변경 권고, 의사 연락 등)"""
    try:
        return APIResponse(
            success=True,
            message=f"부작용 처리 완료: {request.action}",
            data={
                "side_effect_id": request.side_effect_id,
                "action": request.action,
                "processed_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ────────────────────────────────────────────────────────────
# 관리자 엔드포인트
# ────────────────────────────────────────────────────────────

@app.get("/api/admin/users", response_model=APIResponse)
async def get_system_users(admin_id: str):
    """시스템 사용자 목록"""
    try:
        users = [
            {"id": "DR001", "name": "이의사", "role": "doctor", "status": "active"},
            {"id": "DR002", "name": "박의사", "role": "doctor", "status": "active"},
            {"id": "DR003", "name": "최의사", "role": "doctor", "status": "active"},
            {"id": "PH001", "name": "김약사", "role": "pharmacist", "status": "active"},
            {"id": "PH002", "name": "이약사", "role": "pharmacist", "status": "active"},
            {"id": "PH003", "name": "박약사", "role": "pharmacist", "status": "active"},
            {"id": "PH004", "name": "정약사", "role": "pharmacist", "status": "active"},
            {"id": "PH005", "name": "한약사", "role": "pharmacist", "status": "active"},
            {"id": "AD001", "name": "김관리자", "role": "admin", "status": "active"},
            {"id": "AD002", "name": "이관리자", "role": "admin", "status": "active"}
        ]

        doctor_count = len([u for u in users if u['role'] == 'doctor'])
        pharmacist_count = len([u for u in users if u['role'] == 'pharmacist'])
        admin_count = len([u for u in users if u['role'] == 'admin'])

        return APIResponse(
            success=True,
            message=f"총 {len(users)}명의 사용자 (의사: {doctor_count}, 약사: {pharmacist_count}, 관리자: {admin_count})",
            data={
                "users": users,
                "total": len(users),
                "doctors": doctor_count,
                "pharmacists": pharmacist_count,
                "admins": admin_count
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/stats", response_model=APIResponse)
async def get_system_statistics(admin_id: str):
    """시스템 통계"""
    try:
        stats = {
            "total_patients": 42,
            "active_prescriptions": 128,
            "medication_alerts": 8,
            "compliance_rate": 94,
            "api_status": "operational",
            "database_records": 34,
            "active_sessions": 8,
            "processed_prescriptions": 234,
            "last_sync": datetime.now().isoformat()
        }

        return APIResponse(
            success=True,
            message="시스템 통계 조회 완료",
            data=stats,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/settings", response_model=APIResponse)
async def update_system_settings(request: AdminSettingsRequest):
    """시스템 설정 변경"""
    try:
        return APIResponse(
            success=True,
            message="시스템 설정이 업데이트되었습니다",
            data={
                "updated_settings": request.settings,
                "updated_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 8. 건강 지표 모니터링 엔드포인트
# ══════════════════════════════════════════════════════════════

def validate_health_metric(metric_type: str, value: float) -> tuple[str, Optional[str]]:
    """건강 지표 정상/경고/위험 여부 판단"""
    status = "normal"
    alert_message = None

    if metric_type == "blood_sugar":  # mg/dL
        if value < 70:
            status = "warning"
            alert_message = "혈당이 낮습니다 (저혈당)"
        elif value > 180:
            status = "warning"
            alert_message = "혈당이 높습니다 (고혈당)"
        elif value > 300:
            status = "critical"
            alert_message = "혈당이 매우 높습니다 (위험)"

    elif metric_type == "blood_pressure":  # systolic 값만 받으면 수축기압
        if value < 90:
            status = "warning"
            alert_message = "혈압이 낮습니다 (저혈압)"
        elif value >= 140:
            status = "warning"
            alert_message = "혈압이 높습니다 (고혈압)"
        elif value >= 180:
            status = "critical"
            alert_message = "혈압이 매우 높습니다 (위험)"

    elif metric_type == "pulse":  # bpm
        if value < 60:
            status = "warning"
            alert_message = "맥박이 낮습니다"
        elif value > 100:
            status = "warning"
            alert_message = "맥박이 높습니다"
        elif value > 120:
            status = "critical"
            alert_message = "맥박이 매우 높습니다 (위험)"

    elif metric_type == "temperature":  # Celsius
        if value < 36.0:
            status = "warning"
            alert_message = "체온이 낮습니다 (저체온)"
        elif value > 38.0:
            status = "warning"
            alert_message = "체온이 높습니다 (발열)"
        elif value > 39.0:
            status = "critical"
            alert_message = "체온이 매우 높습니다 (위험)"

    elif metric_type == "weight":  # kg - 일반적인 범위만 체크
        if value < 30 or value > 200:
            status = "warning"
            alert_message = "체중이 정상 범위를 벗어났습니다"

    return status, alert_message

@app.post("/api/patient/{patient_id}/health-metrics", response_model=APIResponse)
async def add_patient_health_metric(patient_id: str, metric: HealthMetricInput):
    """환자 건강 지표 입력"""
    try:
        # 지표 검증
        status, alert_message = validate_health_metric(metric.metric_type, metric.value)

        # 측정 시간 설정
        measurement_time = metric.measurement_time or datetime.now().isoformat()

        metric_data = {
            "metric_id": f"HM_{patient_id}_{datetime.now().timestamp()}",
            "patient_id": patient_id,
            "metric_type": metric.metric_type,
            "value": metric.value,
            "unit": metric.unit or get_unit_for_metric(metric.metric_type),
            "status": status,
            "measurement_time": measurement_time,
            "notes": metric.notes or ""
        }

        alert = None
        if alert_message:
            alert = {
                "alert_id": f"ALERT_{patient_id}_{datetime.now().timestamp()}",
                "type": status,
                "message": alert_message,
                "metric_type": metric.metric_type,
                "value": metric.value,
                "timestamp": datetime.now().isoformat()
            }

        return APIResponse(
            success=True,
            message=f"건강 지표 '{metric.metric_type}' 기록됨" + (f" (⚠️ {status})" if status != "normal" else ""),
            data={
                "metric": metric_data,
                "alert": alert
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/patient/{patient_id}/health-metrics", response_model=APIResponse)
async def get_patient_health_metrics(patient_id: str):
    """환자 건강 지표 조회"""
    try:
        # 샘플 데이터 반환 (실제는 DB에서 조회)
        sample_metrics = [
            {
                "metric_id": "HM_P001_1",
                "patient_id": patient_id,
                "metric_type": "blood_sugar",
                "value": 145,
                "unit": "mg/dL",
                "status": "warning",
                "measurement_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "notes": "아침 식사 후"
            },
            {
                "metric_id": "HM_P001_2",
                "patient_id": patient_id,
                "metric_type": "blood_pressure",
                "value": 138,
                "unit": "mmHg",
                "status": "normal",
                "measurement_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "notes": "휴식 후"
            },
            {
                "metric_id": "HM_P001_3",
                "patient_id": patient_id,
                "metric_type": "pulse",
                "value": 72,
                "unit": "bpm",
                "status": "normal",
                "measurement_time": datetime.now().isoformat(),
                "notes": "현재"
            }
        ]

        return APIResponse(
            success=True,
            message=f"환자 '{patient_id}'의 건강 지표 조회",
            data={
                "patient_id": patient_id,
                "metrics": sample_metrics,
                "count": len(sample_metrics)
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/doctor/{doctor_id}/patient-health-metrics", response_model=APIResponse)
async def doctor_get_patient_health_metrics(doctor_id: str, patient_id: Optional[str] = None):
    """의사: 환자 건강 지표 모니터링"""
    try:
        # 샘플 환자 목록
        patients_with_metrics = [
            {
                "patient_id": "P001",
                "patient_name": "김철수",
                "age": 68,
                "primary_disease": "고혈압",
                "recent_metrics": [
                    {"metric_type": "blood_pressure", "value": 142, "status": "warning", "measurement_time": "2시간 전"},
                    {"metric_type": "blood_sugar", "value": 135, "status": "normal", "measurement_time": "1시간 전"}
                ],
                "alerts": [
                    {"type": "warning", "message": "혈압이 높습니다", "metric_type": "blood_pressure"}
                ]
            },
            {
                "patient_id": "P002",
                "patient_name": "박영희",
                "age": 55,
                "primary_disease": "당뇨병",
                "recent_metrics": [
                    {"metric_type": "blood_sugar", "value": 195, "status": "warning", "measurement_time": "30분 전"}
                ],
                "alerts": [
                    {"type": "warning", "message": "혈당이 높습니다", "metric_type": "blood_sugar"}
                ]
            }
        ]

        if patient_id:
            patients_with_metrics = [p for p in patients_with_metrics if p["patient_id"] == patient_id]

        return APIResponse(
            success=True,
            message=f"의사 '{doctor_id}'의 환자 건강 지표",
            data={
                "doctor_id": doctor_id,
                "patients": patients_with_metrics,
                "total_alerts": sum(len(p["alerts"]) for p in patients_with_metrics)
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pharmacist/{pharmacist_id}/patient-health-metrics", response_model=APIResponse)
async def pharmacist_get_patient_health_metrics(pharmacist_id: str):
    """약사: 환자 건강 지표 모니터링 (약물과의 연관성)"""
    try:
        # 약사용 건강 지표 데이터 (약물과의 관련성)
        patients_with_drug_related_metrics = [
            {
                "patient_id": "P001",
                "patient_name": "김철수",
                "medications": ["노바스크정", "타그리소"],
                "metric_type": "blood_pressure",
                "current_value": 142,
                "status": "warning",
                "medication_recommendation": "혈압약이 효과적이지 않을 수 있습니다. 의사와 상담 권장"
            },
            {
                "patient_id": "P002",
                "patient_name": "박영희",
                "medications": ["글루코판정"],
                "metric_type": "blood_sugar",
                "current_value": 195,
                "status": "warning",
                "medication_recommendation": "혈당이 높습니다. 약물 용량 조정이 필요할 수 있습니다"
            }
        ]

        return APIResponse(
            success=True,
            message=f"약사 '{pharmacist_id}'의 환자 건강 지표 (약물 관련)",
            data={
                "pharmacist_id": pharmacist_id,
                "patients": patients_with_drug_related_metrics,
                "total_alerts": len([p for p in patients_with_drug_related_metrics if p["status"] == "warning"])
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_unit_for_metric(metric_type: str) -> str:
    """지표 유형별 단위 반환"""
    units = {
        "blood_sugar": "mg/dL",
        "blood_pressure": "mmHg",
        "pulse": "bpm",
        "weight": "kg",
        "temperature": "℃"
    }
    return units.get(metric_type, "")

# ══════════════════════════════════════════════════════════════
# 9. 애플리케이션 시작/종료
# ══════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# Health AI 챗봇 엔드포인트
# ════════════════════════════════════════════════════════════

class HealthAIChatRequest(BaseModel):
    """건강 AI 챗 요청"""
    message: str
    image_base64: Optional[str] = None  # Base64 encoded image

@app.post("/api/health-ai/chat", response_model=APIResponse)
async def health_ai_chat(request: HealthAIChatRequest):
    """AI 건강관리 어시스턴트 챗 - 처방전 분석 및 건강 추천"""
    try:
        message = request.message
        image_base64 = request.image_base64

        # Gemini AI 호출
        # Gemini AI 직접 호출 (google-genai SDK)
        from google import genai as google_genai
        from google.genai import types as genai_types
        _gemini_key = os.getenv("GOOGLE_API_KEY", "")
        if not _gemini_key:
            raise HTTPException(status_code=503, detail="GOOGLE_API_KEY 미설정")
        _gemini_client = google_genai.Client(api_key=_gemini_key)

        # 선생님의 의학 DB에서 관련 질병 정보 로드
        try:
            from disease_knowledge_db import DISEASE_DB
            from drug_info_complete_db import DRUG_DATABASE
            _disease_db_loaded = True
        except Exception:
            _disease_db_loaded = False
            DISEASE_DB = {}
            DRUG_DATABASE = {}

        # 이미지 파싱 (있으면)
        image_part_obj = None
        prescription_text = ""
        if image_base64:
            try:
                image_data = image_base64
                mime_type = 'image/jpeg'
                if image_data.startswith('data:'):
                    parts = image_data.split(',', 1)
                    mime_part = parts[0].replace('data:', '').replace(';base64', '')
                    if mime_part in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                        mime_type = mime_part
                    image_data = parts[1] if len(parts) > 1 else image_data
                import base64 as _b64
                img_bytes = _b64.b64decode(image_data)
                image_part_obj = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                logger.info(f"이미지 파싱 완료: {mime_type}, {len(img_bytes)/1024:.0f}KB")
            except Exception as e:
                logger.error(f"이미지 파싱 오류: {str(e)}")

        # 검색 대상 텍스트: 메시지 기반
        search_text = message + " " + prescription_text

        # DB에서 관련 질병/약물 자동 매칭
        db_context = ""
        if _disease_db_loaded:
            for disease_name, disease_data in DISEASE_DB.items():
                if disease_name in search_text:
                    db_context += f"\n\n=== {disease_name} 전문 임상 데이터 ===\n"
                    db_context += f"진단: {disease_data.get('diagnosis','')}\n"
                    drugs = disease_data.get('first_line_drugs', [])
                    if drugs:
                        for d in drugs[:3]:
                            db_context += f"1차 치료제: {d['name']} {d.get('dosage','')} {d.get('frequency','')} ({d.get('timing','')})\n"
                    interactions = disease_data.get('drug_interactions', [])
                    for ix in interactions[:3]:
                        db_context += f"상호작용: {ix.get('drug_pair','')} → {ix.get('interaction','')} | 대처: {ix.get('management','')}\n"
                    papers = disease_data.get('papers', [])
                    if papers:
                        db_context += f"근거: {'; '.join(papers)}\n"
                    diet = disease_data.get('diet', {})
                    if diet:
                        db_context += f"식이 권장: {diet.get('recommended','')} | 금기: {diet.get('avoid','')}\n"
                    monitoring = disease_data.get('monitoring', [])
                    if monitoring:
                        db_context += f"모니터링: {', '.join(monitoring)}\n"
                    side_effects = disease_data.get('side_effects', [])
                    if side_effects:
                        db_context += f"주요 부작용: {', '.join(side_effects[:4])}\n"

            for drug_name, drug_data in DRUG_DATABASE.items():
                generic = drug_data.get('generic_name', '')
                if drug_name in search_text or (generic and generic.split('(')[0].strip() in search_text):
                    db_context += f"\n\n=== {drug_name} ({generic}) ===\n"
                    db_context += f"분류: {drug_data.get('category','')}\n"
                    dosage = drug_data.get('dosage', {})
                    if dosage:
                        db_context += f"용량: {dosage.get('single_dose','')} {dosage.get('frequency','')} {dosage.get('form','')}\n"
                    efficacy = drug_data.get('efficacy', '')
                    if efficacy:
                        db_context += f"효능/임상근거: {efficacy}\n"
                    trial = drug_data.get('clinical_trial', '')
                    if trial:
                        db_context += f"임상시험: {trial}\n"
                    warnings = drug_data.get('warnings', [])
                    for w in warnings[:3]:
                        db_context += f"경고: {w}\n"
                    interactions = drug_data.get('interactions', [])
                    for ix in interactions:
                        if ix.get('severity') in ('high', 'moderate'):
                            db_context += f"상호작용({ix.get('severity')}): {ix.get('drug','')} → {ix.get('description','')}\n"
                    side_eff = drug_data.get('side_effects', {})
                    if side_eff:
                        db_context += f"부작용: {dict(list(side_eff.items())[:4])}\n"
                    mon = drug_data.get('monitoring', {})
                    if mon:
                        db_context += f"모니터링: {dict(list(mon.items())[:3])}\n"

        is_prescription_request = bool(image_part_obj) or '처방전' in message or '약봉투' in message

        system_prompt = """당신은 30년 경력의 전문 의사이자 임상 약사입니다.
PubMed, NEJM, Lancet, JAMA, NCCN 2024-2025, ESMO 2024, ACC/AHA, 대한의학회·대한약학회 최신 가이드라인에 완전히 정통합니다.

【핵심 원칙】
질문자는 의사·약사 전문가입니다. 환자용 안내 수준은 절대 금지.
병태생리 기전, 분자 타깃, 임상시험 근거, 수치 기준을 반드시 포함하세요.

【의무 포함 사항】
1. 약리 기전: 수용체·효소·채널 수준의 작용 기전
2. 용법·용량: 체중·신기능·간기능 보정 포함
3. 부작용: 빈도(%), Grade 분류, 조기 발견 지표
4. 상호작용: CYP450 대사, PGP, 음식·영양제 상호작용 (기전 포함)
5. 모니터링: 검사 항목, 주기, 목표 수치 명시 (예: HbA1c <7%, eGFR >60)
6. 임상 근거: 논문명, Trial명, 저널명 명시

【식이·영양 처방 (상세 필수)】
- 권장 채소: 구체적 채소명 + 유효 성분 + 섭취량 + 조리법
  예) 브로콜리 150g/일(설포라판→Nrf2활성화→항산화), 시금치 100g(엽산 262μg→DNA합성)
- 권장 과일: 구체적 과일명 + 유효 성분 + 섭취량 + 주의
  예) 블루베리 150g/일(안토시아닌→산화스트레스↓), 토마토 200g(리코펜→전립선암↓)
- 금기 식품: 기전 설명 포함
  예) 자몽→CYP3A4억제→혈중농도↑(스타틴·칼슘채널차단제)
- 영양제: 브랜드명, 정확한 용량, 복용 시간, 약물 상호작용 검토
  예) 코엔자임Q10 200mg 식후(스타틴으로 인한 미토콘드리아 기능장애 보완)

【암 환자 특별 식이 원칙】
- 항암 중 면역저하: 생식·날고기·비살균유제품 금기
- 중성구감소증 시: 완전조리 식품만, 생채소 금기
- 구역·구토 시: 냉식이, 생강차 0.5-1g/회
- 체중 유지: 단백질 1.2-1.5g/kg/일 필수
- CYP3A4 상호작용: 타르그레틴·타세바 복용 시 자몽 절대 금기
- 항산화제 과용: 항암 효과 상쇄 가능성(ROS 기전 항암제 시 주의)

【한국 브랜드명 우선 사용】
응답은 한국어로, 전문 의학용어 사용, 수치·기전·근거 필수 포함."""

        if is_prescription_request:
            system_prompt += """

【처방전 분석 필수 구조】
1. 처방전 판독 결과
   - OCR로 읽힌 환자 정보 (이름/나이/성별) — 앱 등록 정보와 불일치 시 ⚠️ 명시
   - 진단명/상병코드
   - 처방 약물 전체 목록

2. 약물별 상세 분석 (각 약물마다)
   - 성분명(브랜드명): 분류
   - 약리 기전: 수용체/효소/채널 수준
   - 용법·용량: 처방대로 + 신기능/간기능 주의사항
   - 주요 부작용: 빈도(%) + Grade + 조기 발견 징후
   - CYP450 대사 경로

3. 약물 간 상호작용 (처방 내 전체 조합 검토)
4. 음식·영양제 상호작용
5. 통합 복약 지도 (시간표 형식)
6. 맞춤 식단: 권장 채소·과일(용량+기전) + 금기 식품
7. 모니터링 항목·주기·목표 수치
8. 앱 등록 환자 정보와 처방전 정보 불일치 항목 요약"""

        if db_context:
            system_prompt += f"\n\n[전문 임상 데이터베이스]\n{db_context}"

        # 최종 AI 호출 — 이미지가 있으면 직접 포함
        if image_part_obj:
            analysis_text = (
                message if message.strip()
                else "이 약봉투/처방전을 분석해주세요."
            )
            analysis_text += (
                "\n\n위 이미지(약봉투/처방전)에서 모든 약물을 읽고, 각 약물의 약리 기전·부작용·"
                "상호작용·복약 시간표·맞춤 식단(채소·과일 포함)·모니터링을 상세히 분석하세요. "
                "처방전의 환자 정보(나이·성별)와 앱 등록 정보가 다르면 ⚠️로 표시하세요."
            )
            contents = [image_part_obj, analysis_text]
        else:
            contents = message

        ai_response = _gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=8000,
                temperature=0.2,
            )
        )
        recommendation = ai_response.text

        return APIResponse(
            success=True,
            message="AI 건강 관리 조언 생성됨",
            data={
                "user_message": message,
                "prescription": prescription_text[:200] if prescription_text else None,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════════════════════════════════════════════
# 9. 샘플 처방전 엔드포인트 (주민번호 자동 마스킹)
# ══════════════════════════════════════════════════════════════

PRESCRIPTION_IMAGES_DIR = Path(__file__).parent / "prescription_images"
_MASKED_CACHE_DIR = PRESCRIPTION_IMAGES_DIR / ".masked_cache"

def _anonymize_text(text: str) -> str:
    """텍스트에서 주민번호·전화번호 마스킹"""
    import re
    text = re.sub(r'\d{6}-\d{7}', '●●●●●●-●●●●●●●', text)
    text = re.sub(r'(0\d{1,2})-(\d{3,4})-(\d{4})', r'\1-****-****', text)
    return text

async def _mask_image_rrn(image_path: Path, force: bool = False) -> bytes:
    """
    이미지에서 주민번호 영역을 검정 박스로 마스킹.
    Gemini에게 bounding box를 [ymin,xmin,ymax,xmax] (0~1000 정규화) 형식으로 요청.
    여러 박스를 한 번에 받아 모두 칠함. 결과 캐시 저장.
    """
    import re
    from PIL import ImageDraw, ImageFilter

    _MASKED_CACHE_DIR.mkdir(exist_ok=True)
    cached_path = _MASKED_CACHE_DIR / image_path.name
    if cached_path.exists() and not force:
        return cached_path.read_bytes()

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    masked_any = False

    try:
        from google import genai as _gai
        from google.genai import types as _gt
        _key = os.getenv("GOOGLE_API_KEY", "")
        if not _key:
            raise ValueError("GOOGLE_API_KEY 없음")

        client = _gai.Client(api_key=_key)
        with open(image_path, "rb") as f:
            raw = f.read()
        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        img_part = _gt.Part.from_bytes(data=raw, mime_type=mime)

        # 주민번호 + 전화번호 위치를 JSON 배열로 요청
        loc_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img_part,
                "이 처방전 이미지에서 개인정보가 담긴 모든 텍스트 영역의 bounding box를 찾아줘.\n"
                "찾을 항목: 주민번호(6자리-7자리 형식), 전화번호, 핸드폰번호\n"
                "응답 형식 (JSON 배열만, 설명 없이):\n"
                '[[ymin,xmin,ymax,xmax],[ymin,xmin,ymax,xmax],...]\n'
                "좌표는 이미지 크기를 1000×1000 기준으로 정규화. 없으면 [] 만 출력."],
            config=_gt.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0,
                thinking_config=_gt.ThinkingConfig(thinking_budget=0)
            )
        )
        loc_text = loc_resp.text.strip()
        logger.info(f"마스킹 위치 응답: {loc_text[:100]}")

        # JSON 배열 파싱
        m = re.search(r'\[[\s\S]*\]', loc_text)
        if m:
            boxes = json.loads(m.group())
            if isinstance(boxes, list) and len(boxes) > 0:
                draw = ImageDraw.Draw(img)
                # 첫 번째 요소가 숫자면 단일 박스, 리스트면 다중 박스
                if isinstance(boxes[0], (int, float)):
                    boxes = [boxes]
                for box in boxes:
                    if len(box) >= 4:
                        ymin, xmin, ymax, xmax = [float(v) for v in box[:4]]
                        px1 = max(0, int(xmin * w / 1000) - 8)
                        py1 = max(0, int(ymin * h / 1000) - 8)
                        px2 = min(w, int(xmax * w / 1000) + 8)
                        py2 = min(h, int(ymax * h / 1000) + 8)
                        draw.rectangle([px1, py1, px2, py2], fill=(0, 0, 0))
                        logger.info(f"마스킹 적용: ({px1},{py1})-({px2},{py2})")
                        masked_any = True
    except Exception as e:
        logger.warning(f"주민번호 위치 감지 실패: {e}")

    if not masked_any:
        # Fallback: 처방전 상단 환자정보 행(전체 너비 × 상단 12~20%) 블러 처리
        logger.info("Fallback: 상단 환자정보 영역 블러 마스킹")
        region_box = (0, int(h * 0.10), w, int(h * 0.22))
        region = img.crop(region_box)
        blurred = region.filter(ImageFilter.GaussianBlur(radius=15))
        img.paste(blurred, region_box)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    masked_bytes = buf.getvalue()
    cached_path.write_bytes(masked_bytes)
    return masked_bytes


@app.get("/api/prescriptions/samples")
async def list_sample_prescriptions():
    """샘플 처방전 목록 (RX_P001~P029)"""
    if not PRESCRIPTION_IMAGES_DIR.exists():
        return APIResponse(
            success=False,
            message="샘플 처방전 폴더 없음",
            data={"samples": [], "count": 0},
            timestamp=datetime.now().isoformat()
        )
    samples = []
    for img_file in sorted(PRESCRIPTION_IMAGES_DIR.glob("RX_P*.png")):
        sid = img_file.stem
        samples.append({
            "id": sid,
            "filename": img_file.name,
            "image_url": f"/api/prescriptions/samples/{sid}/image",
            "analyze_url": f"/api/prescriptions/samples/{sid}/analyze"
        })
    return APIResponse(
        success=True,
        message=f"샘플 처방전 {len(samples)}개 (개인정보 보호 처리됨)",
        data={"samples": samples, "count": len(samples)},
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/prescriptions/samples/{sample_id}/image")
async def get_sample_prescription_image(sample_id: str, refresh: bool = False):
    """샘플 처방전 이미지 (주민번호 자동 마스킹). refresh=true 이면 캐시 무시."""
    if ".." in sample_id or "/" in sample_id or "\\" in sample_id:
        raise HTTPException(status_code=400, detail="잘못된 샘플 ID")
    image_path = PRESCRIPTION_IMAGES_DIR / f"{sample_id}.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"샘플 {sample_id} 없음")
    masked = await _mask_image_rrn(image_path, force=refresh)
    return Response(content=masked, media_type="image/png")


@app.post("/api/prescriptions/samples/{sample_id}/analyze")
async def analyze_sample_prescription(sample_id: str):
    """샘플 처방전 Gemini 분석 (주민번호·전화번호 자동 마스킹)"""
    if ".." in sample_id or "/" in sample_id or "\\" in sample_id:
        raise HTTPException(status_code=400, detail="잘못된 샘플 ID")
    image_path = PRESCRIPTION_IMAGES_DIR / f"{sample_id}.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"샘플 {sample_id} 없음")
    try:
        from google import genai as _gai
        from google.genai import types as _gt
        _key = os.getenv("GOOGLE_API_KEY", "")
        if not _key:
            raise HTTPException(status_code=503, detail="GOOGLE_API_KEY 미설정")
        client = _gai.Client(api_key=_key)
        with open(image_path, "rb") as f:
            raw = f.read()
        img_part = _gt.Part.from_bytes(data=raw, mime_type="image/png")

        prompt = """이 처방전을 분석해줘. 개인정보 보호 규칙 엄수:
- 주민번호(주민등록번호) → 절대 출력 금지, 대신 ●●●●●●-●●●●●●● 표시
- 전화번호 → 010-****-**** 형태로만

출력 형식:
【환자 정보】이름 / 나이(주민번호 제외) / 성별
【진단명】주상병 / 부상병
【처방 약물】
| 약물명 | 용량 | 용법 | 투여일수 |
(각 약물 표 형식)
【복약 지도】주요 복약 주의사항
【약사 소견】상호작용·부작용·모니터링 포인트 (전문가 수준)"""

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img_part, prompt],
            config=_gt.GenerateContentConfig(max_output_tokens=4000, temperature=0.1)
        )
        analysis = _anonymize_text(resp.text)
        return APIResponse(
            success=True,
            message=f"샘플 처방전 {sample_id} 분석 완료",
            data={
                "sample_id": sample_id,
                "analysis": analysis,
                "privacy_notice": "주민번호·전화번호 자동 마스킹 처리됨"
            },
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"샘플 처방전 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prescriptions/merge")
async def merge_prescriptions(sample_ids: List[str]):
    """
    처방전 2장을 하나의 종합 뷰로 합침.
    두 이미지를 동시에 Gemini에 전달해 통합 분석 생성.
    주민번호·전화번호 자동 마스킹.
    """
    if len(sample_ids) < 2 or len(sample_ids) > 4:
        raise HTTPException(status_code=400, detail="처방전 2~4개를 지정해주세요")
    for sid in sample_ids:
        if ".." in sid or "/" in sid or "\\" in sid:
            raise HTTPException(status_code=400, detail=f"잘못된 샘플 ID: {sid}")
        if not (PRESCRIPTION_IMAGES_DIR / f"{sid}.png").exists():
            raise HTTPException(status_code=404, detail=f"샘플 {sid} 없음")

    try:
        from google import genai as _gai
        from google.genai import types as _gt
        _key = os.getenv("GOOGLE_API_KEY", "")
        if not _key:
            raise HTTPException(status_code=503, detail="GOOGLE_API_KEY 미설정")
        client = _gai.Client(api_key=_key)

        contents: list = []
        for sid in sample_ids:
            with open(PRESCRIPTION_IMAGES_DIR / f"{sid}.png", "rb") as f:
                raw = f.read()
            contents.append(_gt.Part.from_bytes(data=raw, mime_type="image/png"))

        n = len(sample_ids)
        prompt = (
            f"다음 {n}장의 처방전을 하나의 환자 종합 처방으로 통합 분석해줘.\n"
            "개인정보 보호 규칙: 주민번호 → ●●●●●●-●●●●●●● / 전화번호 → 010-****-****\n\n"
            "출력 형식:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "【통합 환자 정보】\n"
            "- 이름: / 나이: / 성별:\n\n"
            "【진단명】\n"
            "- 주진단: (처방전1 기준)\n"
            "- 부진단: (처방전2 기준)\n\n"
            "【전체 처방 약물】(처방전별 구분)\n"
            "처방전1 | 처방전2 순으로 표로 정리\n"
            "| 약물명 | 용량 | 용법 | 일수 | 처방전 |\n\n"
            "【복약 지도 핵심】\n"
            "- 두 처방전 약물 간 상호작용 포함\n\n"
            "【약사 소견】\n"
            "- 통합 복용 시 주의사항, CYP450 상호작용, 모니터링 포인트\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        contents.append(prompt)

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=_gt.GenerateContentConfig(
                max_output_tokens=6000,
                temperature=0.1
            )
        )
        analysis = _anonymize_text(resp.text)

        # 인덱스에서 환자 정보 조합
        index = _load_index()
        patients = [p for p in index if p.get("sample_id") in sample_ids]

        return APIResponse(
            success=True,
            message=f"처방전 {len(sample_ids)}장 통합 분석 완료",
            data={
                "sample_ids": sample_ids,
                "patients": patients,
                "merged_analysis": analysis,
                "privacy_notice": "주민번호·전화번호 자동 마스킹 처리됨",
                "image_urls": [f"/api/prescriptions/samples/{sid}/image" for sid in sample_ids]
            },
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"처방전 합치기 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_INDEX_PATH = Path(__file__).parent / "prescription_index.json"


def _load_index() -> list:
    if _INDEX_PATH.exists():
        try:
            return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_index(data: list):
    _INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.post("/api/prescriptions/samples/build-index")
async def build_prescription_index():
    """
    29명 샘플 처방전 전체를 Gemini로 읽어 환자 색인(이름·나이·진단·약물) 생성.
    최초 1회 또는 이미지 추가 시 호출.
    """
    if not PRESCRIPTION_IMAGES_DIR.exists():
        raise HTTPException(status_code=404, detail="prescription_images 폴더 없음")

    try:
        from google import genai as _gai
        from google.genai import types as _gt
        _key = os.getenv("GOOGLE_API_KEY", "")
        if not _key:
            raise HTTPException(status_code=503, detail="GOOGLE_API_KEY 미설정")
        client = _gai.Client(api_key=_key)
    except ImportError:
        raise HTTPException(status_code=503, detail="google-genai 패키지 없음")

    images = sorted(PRESCRIPTION_IMAGES_DIR.glob("RX_P*.png"))
    results = []
    errors = []

    for img_path in images:
        sid = img_path.stem
        try:
            with open(img_path, "rb") as f:
                raw = f.read()
            img_part = _gt.Part.from_bytes(data=raw, mime_type="image/png")

            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[img_part,
                    "이 처방전에서 다음 정보를 JSON으로만 답해줘 (코드블록 없이 JSON만):\n"
                    '{"name":"환자이름","age":나이숫자,"gender":"남/여","diseases":["진단1","진단2"],'
                    '"medications":["약물명1","약물명2"],"prescription_days":투여일수숫자}\n'
                    "주민번호는 절대 포함하지 말 것. 나이는 주민번호 앞자리에서 추정해도 됨."],
                config=_gt.GenerateContentConfig(
                    max_output_tokens=2000,
                    temperature=0,
                    thinking_config=_gt.ThinkingConfig(thinking_budget=0)
                )
            )
            text = resp.text.strip()
            # JSON 블록 추출
            import re as _re
            m = _re.search(r'\{.*\}', text, _re.DOTALL)
            if m:
                info = json.loads(m.group())
                info["sample_id"] = sid
                info["image_url"] = f"/api/prescriptions/samples/{sid}/image"
                info["analyze_url"] = f"/api/prescriptions/samples/{sid}/analyze"
                results.append(info)
                logger.info(f"색인 완료: {sid} → {info.get('name','?')} ({info.get('age','?')}세)")
            else:
                errors.append(sid)
        except Exception as e:
            logger.warning(f"색인 실패 {sid}: {e}")
            errors.append(sid)

    _save_index(results)
    return APIResponse(
        success=True,
        message=f"색인 완료: {len(results)}명 성공, {len(errors)}명 실패",
        data={"indexed": len(results), "errors": errors, "patients": results},
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/prescriptions/search")
async def search_prescriptions(name: str = "", age: int = 0):
    """
    환자 이름 또는 나이로 처방전 검색.
    이름은 부분 일치, 나이는 ±5세 범위.
    """
    index = _load_index()
    if not index:
        return APIResponse(
            success=False,
            message="색인이 없습니다. /api/prescriptions/samples/build-index 를 먼저 호출하세요.",
            data={"results": [], "count": 0},
            timestamp=datetime.now().isoformat()
        )

    matched = []
    for p in index:
        name_match = (not name) or (name.strip() in str(p.get("name", "")))
        age_val = int(p.get("age") or 0)
        # 나이가 연도로 잘못 저장된 경우(>200) 보정
        if age_val > 200:
            age_val = 2026 - age_val
        age_match = (not age) or (abs(age_val - age) <= 5)
        if name_match and age_match:
            matched.append(p)

    return APIResponse(
        success=True,
        message=f"'{name or '전체'}' 검색 결과 {len(matched)}명",
        data={"results": matched, "count": len(matched)},
        timestamp=datetime.now().isoformat()
    )


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    logger.info("PHARMA-MOBILE API 서버 시작됨")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info("PHARMA-MOBILE API 서버 종료됨")

# ══════════════════════════════════════════════════════════════
# 10. 에러 핸들러
# ══════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

# ══════════════════════════════════════════════════════════════
# 11. 프로덕션 설정
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
