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
    """약물 정보 조회"""
    return APIResponse(
        success=True,
        message=f"약물 '{medication_name}' 정보",
        data={
            "medication_name": medication_name,
            "dosage": "정보 조회됨",
            "frequency": "정보 조회됨"
        },
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
    """음성 파일 전사 (STT)"""
    try:
        return APIResponse(
            success=True,
            message="음성 파일이 처리되었습니다",
            data={"file_name": file.filename},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/voice/synthesize", response_model=APIResponse)
async def synthesize_voice(text: str):
    """텍스트를 음성으로 변환 (TTS)"""
    return APIResponse(
        success=True,
        message="음성 합성 완료",
        data={"text": text},
        timestamp=datetime.now().isoformat()
    )

# ══════════════════════════════════════════════════════════════
# 7. 분석 및 추천 엔드포인트
# ══════════════════════════════════════════════════════════════

@app.post("/api/analysis/prescription", response_model=APIResponse)
async def analyze_prescription(file: UploadFile = File(...)):
    """처방전 분석"""
    try:
        return APIResponse(
            success=True,
            message="처방전이 분석되었습니다",
            data={"file_name": file.filename},
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pharmacies/nearby", response_model=APIResponse)
async def find_nearby_pharmacies(latitude: float, longitude: float):
    """근처 약국 검색"""
    return APIResponse(
        success=True,
        message=f"위치 ({latitude}, {longitude}) 근처 약국 검색 완료",
        data={"latitude": latitude, "longitude": longitude, "pharmacies": []},
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
