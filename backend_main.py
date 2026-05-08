#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-MOBILE FastAPI Backend
완전한 의료 복약 관리 API 서버 (프로덕션급)
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# ══════════════════════════════════════════════════════════════
# 1. 설정 및 초기화
# ══════════════════════════════════════════════════════════════

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "default-key")
genai.configure(api_key=GEMINI_API_KEY)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="PHARMA-MOBILE API",
    description="의료 복약 관리 모바일 앱 백엔드",
    version="1.0.0"
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

class UserProfile(BaseModel):
    """사용자 프로필"""
    user_id: str
    name: str
    age: int
    gender: str
    medications: List[Dict]
    diagnoses: List[str]
    allergies: List[str] = []

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0 or v > 150:
            raise ValueError('나이는 0-150 사이여야 합니다')
        return v


class HealthInput(BaseModel):
    """건강 상태 입력"""
    user_id: str
    input_type: str  # "text" or "voice"
    content: str
    timestamp: Optional[datetime] = None


class MedicationLog(BaseModel):
    """복약 기록"""
    user_id: str
    medication_name: str
    taken: bool
    side_effect: Optional[str] = None
    timestamp: Optional[datetime] = None


class MedicationReminder(BaseModel):
    """약물 알림"""
    user_id: str
    medication_name: str
    reminder_time: str
    scheduled_at: Optional[datetime] = None


# ══════════════════════════════════════════════════════════════
# 3. 데이터베이스 관리
# ══════════════════════════════════════════════════════════════

class DatabaseManager:
    """SQLite 데이터베이스 관리"""

    @staticmethod
    def init_db():
        """데이터베이스 초기화"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 사용자 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                profile_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 건강 입력 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                input_type TEXT NOT NULL,
                content TEXT NOT NULL,
                ai_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # 복약 기록 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                taken BOOLEAN NOT NULL,
                side_effect TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # 알림 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                scheduled_at TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # 약물 정보 캐시 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medication_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medication_name TEXT UNIQUE,
                info_json TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 인덱스 생성 (쿼리 성능 최적화)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON health_inputs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_med_logs ON medication_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders ON reminders(user_id)")

        conn.commit()
        conn.close()
        logger.info("✅ 데이터베이스 초기화 완료")

    @staticmethod
    def get_connection():
        """데이터베이스 연결"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


# 데이터베이스 초기화
DatabaseManager.init_db()

# ══════════════════════════════════════════════════════════════
# 4. 약물 분석 엔진 (AI)
# ══════════════════════════════════════════════════════════════

class MedicationAnalyzer:
    """약물 분석 및 추천 엔진"""

    # 약물별 영양소 고갈 맵 (Drug Mugger)
    DRUG_MUGGER_MAP = {
        "노바스크": {
            "depleted": "비타민 B12, 아연",
            "reason": "혈압약 대사 과정에서 소모",
            "recommendation": "굴, 견과류, B12 보충제"
        },
        "다이아벡스": {
            "depleted": "비타민 B12",
            "reason": "장기 복용 시 흡수 저해",
            "recommendation": "메틸코발라민 500mcg/일"
        },
        "리피토": {
            "depleted": "Coenzyme Q10",
            "reason": "체내 합성 경로 차단",
            "recommendation": "CoQ10 100-200mg/일"
        },
        "라식스": {
            "depleted": "칼륨, 칼슘, 마그네슘",
            "reason": "이뇨 작용으로 배설 증가",
            "recommendation": "전해질 보충 필수"
        }
    }

    # 부작용 주의사항
    SIDE_EFFECTS = {
        "노바스크": ["안면 홍조", "발목 부종", "두통", "어지러움"],
        "당뇨약": ["저혈당", "속쓰림", "발진"],
        "항암제": ["오심", "피로", "탈모"],
        "스테로이드": ["수면 방해", "식욕 증가", "기분 변화"]
    }

    @staticmethod
    def analyze_health_status(user_profile: Dict, health_input: str) -> Dict:
        """
        건강 상태를 AI로 분석하여 맞춤형 조언 생성
        """
        prompt = f"""
당신은 30년 경력의 전문 약사입니다.
다음 환자 정보와 건강 상태를 분석하고 실질적인 조언을 제공하세요:

[환자 정보]
이름: {user_profile.get('name', '환자')}
나이: {user_profile.get('age', '?')}세
진단: {', '.join(user_profile.get('diagnoses', []))}
현재 복용 약물: {', '.join([m.get('name', '') for m in user_profile.get('medications', [])])}

[오늘의 건강 상태]
{health_input}

다음을 JSON 형식으로 응답해주세요:
{{
    "status_summary": "현재 상태 한 줄 요약",
    "medication_order": [
        {{"name": "약물명", "time": "복용 시간", "reason": "먼저 먹는 이유"}}
    ],
    "diet_recommendation": [
        {{"food": "음식명", "benefit": "효과", "avoid": "피해야 할 것"}}
    ],
    "exercise": {{
        "type": "운동 종류",
        "duration": "시간",
        "intensity": "강도",
        "timing": "언제",
        "caution": "주의사항"
    }},
    "supplements": [
        {{"name": "영양제", "dosage": "용량", "timing": "시간", "synergy": "약물 시너지"}}
    ],
    "precautions": ["주의사항1", "주의사항2"],
    "urgency": "normal|warning|critical"
}}
"""

        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)

            # JSON 파싱
            response_text = response.text
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"error": "응답 파싱 실패", "raw": response_text}

            return {"status": "success", "analysis": result}

        except Exception as e:
            logger.error(f"AI 분석 오류: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_drug_warnings(medication_names: List[str]) -> Dict:
        """약물 상호작용 및 경고"""
        warnings = []
        for med in medication_names:
            for key, val in MedicationAnalyzer.DRUG_MUGGER_MAP.items():
                if key in med:
                    warnings.append({
                        "medication": med,
                        "depleted_nutrients": val["depleted"],
                        "recommendation": val["recommendation"]
                    })
        return {"warnings": warnings}


# ══════════════════════════════════════════════════════════════
# 5. API 엔드포인트
# ══════════════════════════════════════════════════════════════

# [1] 헬스 체크
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# [2] 사용자 관리
@app.post("/api/user/register")
async def register_user(profile: UserProfile):
    """사용자 등록"""
    conn = DatabaseManager.get_connection()
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

        logger.info(f"✅ 사용자 등록: {profile.user_id}")
        return {
            "status": "success",
            "user_id": profile.user_id,
            "message": f"{profile.name}님의 프로필이 등록되었습니다"
        }

    except sqlite3.IntegrityError:
        return {"status": "error", "message": "이미 존재하는 사용자 ID입니다"}
    except Exception as e:
        logger.error(f"사용자 등록 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    """사용자 프로필 조회"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        profile = json.loads(result["profile_json"])
        return {
            "status": "success",
            "user": {
                "user_id": result["user_id"],
                "name": result["name"],
                "age": result["age"],
                "gender": result["gender"],
                "profile": profile,
                "created_at": result["created_at"]
            }
        }

    except Exception as e:
        logger.error(f"사용자 조회 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [3] 건강 상태 분석
@app.post("/api/health/analyze")
async def analyze_health(health_input: HealthInput):
    """건강 상태 분석 및 AI 추천"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        # 사용자 프로필 조회
        cursor.execute("SELECT profile_json FROM users WHERE user_id = ?", (health_input.user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        user_profile = json.loads(result["profile_json"])

        # AI 분석
        analysis_result = MedicationAnalyzer.analyze_health_status(
            user_profile,
            health_input.content
        )

        # 약물 경고
        med_names = [m.get("name", "") for m in user_profile.get("medications", [])]
        warnings = MedicationAnalyzer.get_drug_warnings(med_names)

        # 데이터베이스 저장
        timestamp = health_input.timestamp or datetime.now()
        cursor.execute("""
            INSERT INTO health_inputs (user_id, input_type, content, ai_response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            health_input.user_id,
            health_input.input_type,
            health_input.content,
            json.dumps(analysis_result),
            timestamp
        ))
        conn.commit()

        logger.info(f"✅ 건강 분석 완료: {health_input.user_id}")

        return {
            "status": "success",
            "analysis": analysis_result.get("analysis", {}),
            "warnings": warnings,
            "timestamp": timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"건강 분석 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [4] 약물 스케줄 생성
@app.post("/api/medication/schedule")
async def create_medication_schedule(user_id: str):
    """최적 약물 복용 스케줄 생성"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT profile_json FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        profile = json.loads(result["profile_json"])
        medications = profile.get("medications", [])

        # 시간대별 배치
        schedule = {
            "morning": [],
            "lunch": [],
            "afternoon": [],
            "dinner": [],
            "bedtime": []
        }

        time_slots = {
            "morning": "08:00",
            "lunch": "12:00",
            "afternoon": "15:00",
            "dinner": "19:00",
            "bedtime": "21:00"
        }

        # 간단한 규칙: 음식과 함께 먹는 약은 식사 시간에
        for med in medications:
            med_name = med.get("name", "")
            if "식사" in med.get("note", "") or "식후" in med.get("dose", ""):
                # 아침, 점심, 저녁 중 배치
                schedule["morning"].append({
                    "name": med_name,
                    "dose": med.get("dose", ""),
                    "note": med.get("note", "")
                })
            elif "취침" in med.get("note", "") or "저녁" in med.get("note", ""):
                schedule["bedtime"].append({
                    "name": med_name,
                    "dose": med.get("dose", ""),
                    "note": med.get("note", "")
                })
            else:
                schedule["morning"].append({
                    "name": med_name,
                    "dose": med.get("dose", ""),
                    "note": med.get("note", "")
                })

        # 알림 저장
        for slot, slot_time in time_slots.items():
            for med in schedule[slot]:
                scheduled_at = datetime.now().replace(
                    hour=int(slot_time.split(":")[0]),
                    minute=int(slot_time.split(":")[1])
                )
                cursor.execute("""
                    INSERT INTO reminders (user_id, medication_name, reminder_time, scheduled_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, med["name"], slot, scheduled_at.isoformat()))

        conn.commit()

        logger.info(f"✅ 약물 스케줄 생성: {user_id}")

        return {
            "status": "success",
            "schedule": schedule,
            "time_slots": time_slots,
            "message": "복약 스케줄이 생성되었습니다"
        }

    except Exception as e:
        logger.error(f"스케줄 생성 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [5] 복약 기록
@app.post("/api/medication/log")
async def log_medication(med_log: MedicationLog):
    """복약 기록 저장"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        timestamp = med_log.timestamp or datetime.now()

        cursor.execute("""
            INSERT INTO medication_logs (user_id, medication_name, taken, side_effect, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            med_log.user_id,
            med_log.medication_name,
            med_log.taken,
            med_log.side_effect,
            timestamp
        ))
        conn.commit()

        status_msg = "약물 복용이 기록되었습니다" if med_log.taken else "미복약이 기록되었습니다"
        logger.info(f"✅ 복약 기록: {med_log.user_id} - {med_log.medication_name}")

        return {
            "status": "success",
            "message": status_msg,
            "timestamp": timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"복약 기록 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [6] 복약 순응도 조회
@app.get("/api/medication/adherence/{user_id}")
async def get_medication_adherence(user_id: str, days: int = 7):
    """복약 순응도 조회"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
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
        for row in results:
            med_name = row["medication_name"]
            taken = row["taken"]
            count = row["count"]

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
                "rate": round(rate, 1),
                "total": total
            }

        overall_rate = round(
            sum(v["rate"] for v in adherence_rate.values()) / len(adherence_rate), 1
        ) if adherence_rate else 0

        logger.info(f"✅ 순응도 조회: {user_id} - {overall_rate}%")

        return {
            "status": "success",
            "period_days": days,
            "adherence": adherence_rate,
            "overall_rate": overall_rate,
            "summary": f"{overall_rate}% 복약 순응도"
        }

    except Exception as e:
        logger.error(f"순응도 조회 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [7] 예정된 알림 조회
@app.get("/api/reminders/{user_id}")
async def get_upcoming_reminders(user_id: str):
    """예정된 약물 알림 조회"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT medication_name, reminder_time, scheduled_at
            FROM reminders
            WHERE user_id = ? AND sent = FALSE
            ORDER BY scheduled_at ASC
        """, (user_id,))

        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                "medication": row["medication_name"],
                "time": row["reminder_time"],
                "scheduled_at": row["scheduled_at"]
            })

        logger.info(f"✅ 알림 조회: {user_id} - {len(reminders)}개")

        return {
            "status": "success",
            "reminders": reminders,
            "count": len(reminders)
        }

    except Exception as e:
        logger.error(f"알림 조회 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [8] 통계 조회
@app.get("/api/statistics/{user_id}")
async def get_user_statistics(user_id: str):
    """사용자 통계"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        # 총 기록 수
        cursor.execute("SELECT COUNT(*) as count FROM medication_logs WHERE user_id = ?", (user_id,))
        total_logs = cursor.fetchone()["count"]

        # 이번 주 기록
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute(
            "SELECT COUNT(*) as count FROM medication_logs WHERE user_id = ? AND timestamp > ?",
            (user_id, week_ago)
        )
        week_logs = cursor.fetchone()["count"]

        # 건강 입력 수
        cursor.execute("SELECT COUNT(*) as count FROM health_inputs WHERE user_id = ?", (user_id,))
        health_inputs = cursor.fetchone()["count"]

        return {
            "status": "success",
            "statistics": {
                "total_medication_logs": total_logs,
                "week_medication_logs": week_logs,
                "health_inputs": health_inputs,
                "last_updated": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# [7] 음성 처리 (Speech-to-Text)
@app.post("/api/voice/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...), user_id: str = ""):
    """음성 파일을 텍스트로 변환 (Speech-to-Text)"""
    try:
        from voice_handler import get_voice_handler

        voice_handler = get_voice_handler()

        # 오디오 파일 읽기
        audio_content = await audio_file.read()

        if not audio_content:
            raise ValueError("오디오 파일이 비어있습니다")

        # Speech-to-Text 수행
        transcript, confidence = voice_handler.speech_to_text(audio_content)

        logger.info(f"✅ 음성 인식 완료: {user_id} - 신뢰도 {confidence:.2%}")

        return {
            "status": "success",
            "transcript": transcript,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 음성 인식 오류: {str(e)}")
        return {"status": "error", "message": str(e)}


# [8] 음성 생성 (Text-to-Speech)
@app.post("/api/voice/synthesize")
async def synthesize_speech(text: str, user_id: str = ""):
    """텍스트를 음성으로 변환 (Text-to-Speech)"""
    try:
        from voice_handler import get_voice_handler

        voice_handler = get_voice_handler()

        if not text or len(text) == 0:
            raise ValueError("변환할 텍스트가 없습니다")

        if len(text) > 5000:
            raise ValueError("텍스트는 5000자 이하여야 합니다")

        # Text-to-Speech 수행
        audio_content = voice_handler.text_to_speech(text)

        logger.info(f"✅ 음성 생성 완료: {user_id} - {len(audio_content)} bytes")

        # Base64로 인코딩하여 전송 (JSON에서 바이너리 데이터 전달용)
        import base64
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')

        return {
            "status": "success",
            "audio_base64": audio_base64,
            "content_type": "audio/mpeg",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 음성 생성 오류: {str(e)}")
        return {"status": "error", "message": str(e)}


# [9] 건강 상태 음성 분석
@app.post("/api/voice/health-analyze")
async def analyze_health_with_voice(user_id: str, audio_file: UploadFile = File(...)):
    """음성 입력으로 건강 상태 분석 및 음성 응답"""
    try:
        from voice_handler import get_voice_handler

        voice_handler = get_voice_handler()
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        # Step 1: 음성 인식 (Speech-to-Text)
        audio_content = await audio_file.read()
        transcript, confidence = voice_handler.speech_to_text(audio_content)

        if confidence < 0.5:
            return {
                "status": "error",
                "message": "음성을 명확하게 인식하지 못했습니다. 다시 시도해주세요.",
                "confidence": confidence
            }

        # Step 2: 사용자 프로필 조회
        cursor.execute("SELECT profile_json FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result:
            return {"status": "error", "message": "사용자를 찾을 수 없습니다"}

        user_profile = json.loads(result["profile_json"])

        # Step 3: AI 건강 분석
        analysis_result = MedicationAnalyzer.analyze_health_status(
            user_profile,
            transcript
        )

        # Step 4: 약물 경고
        med_names = [m.get("name", "") for m in user_profile.get("medications", [])]
        warnings = MedicationAnalyzer.get_drug_warnings(med_names)

        # Step 5: 데이터베이스 저장
        timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO health_inputs (user_id, input_type, content, ai_response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            "voice",
            transcript,
            json.dumps(analysis_result),
            timestamp
        ))
        conn.commit()

        # Step 6: 음성 응답 생성
        voice_response_text = f"""
{user_profile.get('name', '사용자')}님의 건강 분석 결과입니다.

분석 내용: {analysis_result.get('analysis', {}).get('status_summary', '정상입니다')}

{'주의사항:' if warnings.get('warnings') else '특별한 주의사항이 없습니다.'}
"""
        if warnings.get("warnings"):
            for warning in warnings["warnings"]:
                voice_response_text += f"\n• {warning.get('medication')}: {warning.get('recommendation')}"

        # Text-to-Speech 수행
        audio_response = voice_handler.text_to_speech(voice_response_text)

        # Base64 인코딩
        import base64
        audio_base64 = base64.b64encode(audio_response).decode('utf-8')

        logger.info(f"✅ 음성 건강 분석 완료: {user_id}")

        return {
            "status": "success",
            "transcript": transcript,
            "transcript_confidence": confidence,
            "analysis": analysis_result.get("analysis", {}),
            "warnings": warnings,
            "voice_response_base64": audio_base64,
            "response_text": voice_response_text,
            "timestamp": timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 음성 건강 분석 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
# 6. 실행
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         🏥 PHARMA-MOBILE FastAPI Backend v1.0             ║
    ║                                                            ║
    ║  🚀 서버 시작 중...                                        ║
    ║  📍 http://localhost:8000                                 ║
    ║  📖 API 문서: http://localhost:8000/docs                 ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=8000)
