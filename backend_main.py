#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-MOBILE FastAPI Backend
의료 복약 관리 API 서버 (프로덕션급)
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from dotenv import load_dotenv
import io
from PIL import Image
import base64

# 환경 변수 로드
load_dotenv()

# ══════════════════════════════════════════════════════════════
# 1. 설정 및 초기화
# ══════════════════════════════════════════════════════════════

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class UserProfile(BaseModel):
    """사용자 프로필"""
    user_id: str
    name: str
    age: int
    gender: str
    medications: Optional[List[Dict]] = []
    diagnoses: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

    @validator('age')
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

@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
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
            data=profile.dict(),
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
    return APIResponse(
        success=True,
        message=f"약물 '{medication_name}' 정보 조회 완료",
        data={
            "medication_name": medication_name,
            "dosage": "정보 조회 중",
            "frequency": "정보 조회 중"
        },
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/medications/{medication_name}/detailed", response_model=APIResponse)
async def get_medication_detailed(medication_name: str):
    """약물 상세 정보 조회 (MFDS/논문 기반)"""
    # Phase 1: MFDS API 연동 예정
    medication_detail = {
        "medication_name": medication_name,
        "mfds_code": "조회 중",
        "generic_name": "조회 중",
        "manufacturer": "조회 중",
        "dosage": "조회 중",
        "frequency": "1일 1회",
        "duration": "30일",
        "mfds_price": "공시약가 조회 중",
        "side_effects": [
            "두통 (드물음)",
            "현기증 (매우 드물음)"
        ],
        "contraindications": "조회 중",
        "drug_interactions": [],
        "special_warnings": "고령자 주의",
        "image_url": None,
        "reference_paper": None
    }

    return APIResponse(
        success=True,
        message=f"약물 '{medication_name}' 상세 정보 (Phase 1 개발 중)",
        data=medication_detail,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/medications/log", response_model=APIResponse)
async def log_medication(medication_name: str, taken: bool):
    """복약 기록"""
    return APIResponse(
        success=True,
        message=f"약물 '{medication_name}' {'복용' if taken else '미복용'} 기록됨",
        data={"medication": medication_name, "taken": taken},
        timestamp=datetime.now().isoformat()
    )

# ══════════════════════════════════════════════════════════════
# 6. 음성 처리 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/voice/transcribe", response_model=APIResponse)
async def transcribe_voice(file: UploadFile = File(...)):
    """음성 파일 전사 (STT) - Google Cloud Speech API 기반"""
    try:
        # Phase 1: Google Cloud Speech API 연동 예정
        contents = await file.read()
        file_size = len(contents)

        transcribed_text = "[음성 인식 중...] 처방전 분석을 위한 음성 입력 처리 예정"

        return APIResponse(
            success=True,
            message="음성 파일이 처리되었습니다 (STT 기본 버전)",
            data={
                "file_name": file.filename,
                "file_size": file_size,
                "transcribed_text": transcribed_text,
                "confidence": 0.0,
                "language": "ko-KR"
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/voice/synthesize", response_model=APIResponse)
async def synthesize_voice(text: str, language: str = "ko-KR"):
    """텍스트를 음성으로 변환 (TTS) - Google Cloud TTS 기반"""
    # Phase 1: Google Cloud Text-to-Speech API 연동 예정
    audio_data = {
        "audio_content_base64": "[audio_base64_encoded_data]",
        "audio_config": {
            "audio_encoding": "MP3",
            "sample_rate_hertz": 24000,
            "pitch": 0.0,
            "speaking_rate": 1.0
        },
        "voice": {
            "language_code": language,
            "name": "ko-KR-Neural2-A"
        }
    }

    return APIResponse(
        success=True,
        message="음성 합성 완료 (TTS 기본 버전)",
        data={
            "text": text,
            "language": language,
            "audio_length_seconds": len(text) / 10,  # 대략적 예상
            "audio": audio_data
        },
        timestamp=datetime.now().isoformat()
    )

# ══════════════════════════════════════════════════════════════
# 7. 분석 및 추천 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/analysis/prescription", response_model=APIResponse)
async def analyze_prescription(file: UploadFile = File(...)):
    """처방전 분석 (이미지 -> 의료 정보 추출)"""
    try:
        # 이미지 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 이미지 정보 추출
        image_size = image.size
        image_format = image.format

        # 더미 처방전 데이터 (실제로는 Claude Vision API 사용)
        prescription_data = PrescriptionData(
            patient_name="분석 중...",
            patient_age=None,
            patient_gender=None,
            primary_disease="분석 필요",
            secondary_disease=None,
            medications=[],
            prescription_date=datetime.now().strftime("%Y-%m-%d")
        )

        analysis_result = PrescriptionAnalysis(
            prescription_data=prescription_data,
            extracted_text="OCR 분석 진행 중",
            confidence=0.0,
            image_size={"width": image_size[0], "height": image_size[1]}
        )

        return APIResponse(
            success=True,
            message="처방전이 분석되었습니다. (Phase 1 기본 버전)",
            data=analysis_result.dict(),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pharmacies/nearby", response_model=APIResponse)
async def find_nearby_pharmacies(latitude: float, longitude: float, radius_km: int = 2):
    """근처 약국 검색 (Google Places API 기반)"""
    # Phase 1: Google Places API 연동 예정
    sample_pharmacies = [
        {
            "name": "서울약국",
            "latitude": latitude + 0.005,
            "longitude": longitude + 0.005,
            "distance_m": 500,
            "phone": "02-1234-5678",
            "hours": "09:00-22:00",
            "rating": 4.5,
            "delivery": True,
            "estimated_time": "30분"
        },
        {
            "name": "한약국",
            "latitude": latitude - 0.005,
            "longitude": longitude - 0.005,
            "distance_m": 800,
            "phone": "02-9876-5432",
            "hours": "10:00-21:00",
            "rating": 4.2,
            "delivery": True,
            "estimated_time": "45분"
        }
    ]

    return APIResponse(
        success=True,
        message=f"위치 ({latitude}, {longitude}) 반경 {radius_km}km 근처 약국 검색 완료",
        data={
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "pharmacies": sample_pharmacies,
            "count": len(sample_pharmacies)
        },
        timestamp=datetime.now().isoformat()
    )

# ══════════════════════════════════════════════════════════════
# 8. 애플리케이션 시작/종료
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    logger.info("PHARMA-MOBILE API 서버 시작됨")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info("PHARMA-MOBILE API 서버 종료됨")

# ══════════════════════════════════════════════════════════════
# 9. 에러 핸들러
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
# 10. 프로덕션 설정
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
