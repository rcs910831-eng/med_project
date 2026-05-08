#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-MOBILE BACKEND API (FastAPI)
모바일 앱을 위한 의료 API 서버
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import sqlite3
from pathlib import Path
import google.generativeai as genai

# ── 1. FastAPI 초기화 ──────────────────────────────────────────
app = FastAPI(
    title="PHARMA-MOBILE API",
    description="의료 복약 관리 모바일 앱 백엔드",
    version="1.0.0"
)

# CORS 설정 (모바일 앱 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API 설정
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # 환경변수로 설정 필요
genai.configure(api_key=GEMINI_API_KEY)

# ── 2. 데이터 모델 ────────────────────────────────────────────
class UserProfile(BaseModel):
    """사용자 프로필"""
    user_id: str
    name: str
    age: int
    gender: str
    medications: List[Dict]
    diagnoses: List[str]
    allergies: List[str] = []

class HealthInput(BaseModel):
    """오늘의 건강 상태 입력"""
    user_id: str
    input_type: str  # "text" or "voice"
    content: str  # 텍스트 또는 음성 변환 텍스트
    timestamp: datetime = None

class MedicationReminder(BaseModel):
    """약물 알림"""
    med_name: str
    dose: str
    time: str  # "morning", "lunch", "dinner", "bedtime"
    reason: str
    synergy: str  # 다른 약과의 상호작용

class ComplexMedication(BaseModel):
    """복약 기록"""
    user_id: str
    medication_name: str
    taken: bool  # True: 먹음, False: 안 먹음
    side_effect: Optional[str] = None
    timestamp: datetime = None

# ── 3. 데이터베이스 ────────────────────────────────────────────
def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    # 사용자 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            profile_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 건강 입력 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            input_type TEXT,
            content TEXT,
            ai_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # 복약 기록 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            medication_name TEXT,
            taken BOOLEAN,
            side_effect TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # 알림 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            medication_name TEXT,
            reminder_time TEXT,
            scheduled_at TIMESTAMP,
            sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()

# 데이터베이스 초기화
init_database()

# ── 4. API 엔드포인트 ──────────────────────────────────────────

@app.post("/api/user/register")
async def register_user(profile: UserProfile):
    """사용자 등록"""
    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (user_id, name, age, gender, profile_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            profile.user_id,
            profile.name,
            profile.age,
            profile.gender,
            json.dumps(profile.dict())
        ))
        conn.commit()
        return {"status": "success", "user_id": profile.user_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

@app.post("/api/health/analyze")
async def analyze_health(health_input: HealthInput):
    """
    건강 상태 입력 분석
    사용자가 텍스트 또는 음성으로 입력한 건강 상태를 분석
    """

    # Gemini AI로 분석
    prompt = f"""
    환자가 오늘 다음과 같은 건강 상태를 보고했습니다:
    "{health_input.content}"

    다음을 분석하고 JSON 형식으로 응답해주세요:

    1. 현재 건강 상태 요약
    2. 약물 복용 순서 (추천)
    3. 식단 추천 (3가지)
    4. 운동 추천 (강도, 시간, 주의사항)
    5. 영양제 추천 (약물과의 시너지)
    6. 주의사항 (부작용 예방)

    응답 형식:
    {{
        "status_summary": "...",
        "medication_order": ["약1", "약2", ...],
        "diet_recommendation": ["음식1", "음식2", "음식3"],
        "exercise": {{
            "type": "...",
            "duration": "...",
            "intensity": "...",
            "caution": "..."
        }},
        "supplements": [
            {{"name": "...", "dosage": "...", "synergy": "..."}}
        ],
        "precautions": ["주의1", "주의2", ...]
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)

        # 응답 파싱
        ai_response = response.text

        # 데이터베이스 저장
        conn = sqlite3.connect("pharma_mobile.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_inputs (user_id, input_type, content, ai_response)
            VALUES (?, ?, ?, ?)
        """, (health_input.user_id, health_input.input_type, health_input.content, ai_response))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "analysis": ai_response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/medication/schedule")
async def create_medication_schedule(user_id: str):
    """
    복약 스케줄 생성
    사용자의 약물 목록을 기반으로 최적 복약 시간대 생성
    """

    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    try:
        # 사용자 프로필 조회
        cursor.execute("SELECT profile_json FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        profile = json.loads(result[0])
        medications = profile.get("medications", [])

        # AI로 최적 스케줄 생성
        prompt = f"""
        다음 약물들의 최적 복약 스케줄을 생성해주세요:
        {json.dumps(medications, ensure_ascii=False)}

        다음 규칙을 고려해주세요:
        1. 음식과 함께 먹어야 하는 약은 식사 시간에 배치
        2. 공복에 먹어야 하는 약은 별도 배치
        3. 약물 상호작용 최소화
        4. 복약 순응도 최대화 (너무 많은 알림 피함)

        응답 형식:
        {{
            "morning": [
                {{"name": "약1", "dose": "...", "note": "..."}}
            ],
            "lunch": [...],
            "afternoon": [...],
            "dinner": [...],
            "bedtime": [...]
        }}
        """

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        schedule = json.loads(response.text)

        # 알림 스케줄 저장
        time_slots = {
            "morning": "08:00",
            "lunch": "12:00",
            "afternoon": "15:00",
            "dinner": "19:00",
            "bedtime": "21:00"
        }

        for slot, meds in schedule.items():
            for med in meds:
                cursor.execute("""
                    INSERT INTO reminders (user_id, medication_name, reminder_time, scheduled_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    med.get("name"),
                    slot,
                    datetime.now().replace(hour=int(time_slots[slot].split(":")[0])).isoformat()
                ))

        conn.commit()

        return {
            "status": "success",
            "schedule": schedule,
            "message": "복약 스케줄이 생성되었습니다"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

@app.post("/api/medication/log")
async def log_medication(med_log: ComplexMedication):
    """
    복약 기록 저장 (먹음/안 먹음)
    """

    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO medication_logs (user_id, medication_name, taken, side_effect)
            VALUES (?, ?, ?, ?)
        """, (
            med_log.user_id,
            med_log.medication_name,
            med_log.taken,
            med_log.side_effect
        ))
        conn.commit()

        status_msg = "복약이 기록되었습니다" if med_log.taken else "미복약이 기록되었습니다"

        return {
            "status": "success",
            "message": status_msg,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

@app.get("/api/medication/adherence/{user_id}")
async def get_medication_adherence(user_id: str, days: int = 7):
    """
    복약 순응도 조회 (최근 N일)
    """

    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    try:
        # 최근 N일의 복약 기록 조회
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT medication_name, taken, COUNT(*) as count
            FROM medication_logs
            WHERE user_id = ? AND timestamp > ?
            GROUP BY medication_name, taken
        """, (user_id, start_date))

        results = cursor.fetchall()

        # 순응도 계산
        adherence_stats = {}
        for med_name, taken, count in results:
            if med_name not in adherence_stats:
                adherence_stats[med_name] = {"taken": 0, "not_taken": 0}

            if taken:
                adherence_stats[med_name]["taken"] += count
            else:
                adherence_stats[med_name]["not_taken"] += count

        # 백분율 계산
        adherence_rate = {}
        for med, stats in adherence_stats.items():
            total = stats["taken"] + stats["not_taken"]
            rate = (stats["taken"] / total * 100) if total > 0 else 0
            adherence_rate[med] = {
                "taken": stats["taken"],
                "not_taken": stats["not_taken"],
                "rate": round(rate, 1)
            }

        return {
            "status": "success",
            "period_days": days,
            "adherence": adherence_rate,
            "overall_rate": round(sum(v["rate"] for v in adherence_rate.values()) / len(adherence_rate), 1) if adherence_rate else 0
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

@app.get("/api/reminders/{user_id}")
async def get_upcoming_reminders(user_id: str):
    """
    예정된 알림 조회
    """

    conn = sqlite3.connect("pharma_mobile.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT medication_name, reminder_time, scheduled_at
            FROM reminders
            WHERE user_id = ? AND sent = FALSE
            ORDER BY scheduled_at ASC
        """, (user_id,))

        reminders = []
        for med_name, reminder_time, scheduled_at in cursor.fetchall():
            reminders.append({
                "medication": med_name,
                "time": reminder_time,
                "scheduled_at": scheduled_at
            })

        return {
            "status": "success",
            "reminders": reminders,
            "count": len(reminders)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
