#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medication_adherence.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
복약 이행도(Medication Adherence) 추적 모듈

기능:
  - "약 먹었어" 버튼 / 음성 → 복용 기록 DB 저장
  - 처방별 하루 복용 횟수 대비 실제 복용 횟수 계산
  - COMPLIANCE SENTINEL 수치 실시간 업데이트
  - 미복용 약물 자동 감지 → Guardian Link 알림 트리거

Author: PHARMA-HYBRID Team
"""

import sqlite3
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("medication_adherence")

# ── DB 경로 ──────────────────────────────────────────────────────────────────
ADHERENCE_DB = "medication_adherence.db"

# 복용 확인 음성 키워드 목록
TAKEN_KEYWORDS = [
    "약 먹었어", "약 먹었습니다", "복용했어", "복용했습니다",
    "다 먹었어", "다 먹었습니다", "약 먹었다", "복약 완료",
    "먹었어", "먹었습니다", "드셨어요", "약 드셨어요",
    "took medication", "medication taken",
]


# ═══════════════════════════════════════════════════════════════════════════════
# DB 초기화
# ═══════════════════════════════════════════════════════════════════════════════

def init_adherence_db():
    """복약 이행도 DB 초기화 (최초 1회)."""
    with sqlite3.connect(ADHERENCE_DB) as conn:
        # 복용 기록 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS med_taken (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                medication_name TEXT    NOT NULL,
                taken_at        TEXT    DEFAULT (datetime('now','localtime')),
                dose_label      TEXT    DEFAULT '1회분',
                recorded_by     TEXT    DEFAULT 'patient',
                notes           TEXT    DEFAULT ''
            )
        """)
        # 복약 목표 테이블 (처방 기반 자동 생성)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS med_schedule (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                medication_name TEXT    NOT NULL,
                doses_per_day   INTEGER DEFAULT 1,
                start_date      TEXT,
                end_date        TEXT,
                active          INTEGER DEFAULT 1
            )
        """)
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 처방 → 복약 스케줄 자동 등록
# ═══════════════════════════════════════════════════════════════════════════════

# 복용 횟수 문자열 → 1일 횟수 변환
_FREQ_MAP = {
    "1일1회": 1, "1회/일": 1, "1일 1회": 1, "1일1번": 1,
    "1일2회": 2, "2회/일": 2, "1일 2회": 2, "1일2번": 2,
    "1일3회": 3, "3회/일": 3, "1일 3회": 3, "1일3번": 3,
    "1일4회": 4, "4회/일": 4,
    "2주1회": 0, "3주1회": 0, "4주1회": 0,  # 간헐적 투여 = 0 (이행도 계산 제외)
    "필요시": 0, "prn": 0,
    "식전": 3, "식후": 3, "취침전": 1,
}


def _parse_doses_per_day(frequency_str: str) -> int:
    """처방 빈도 문자열 → 1일 복용 횟수."""
    if not frequency_str:
        return 1
    freq = frequency_str.strip().lower()
    for key, val in _FREQ_MAP.items():
        if key.lower() in freq:
            return val
    return 1  # 파싱 실패 시 기본값 1회


def sync_schedules_from_rx(rx_list: List[Dict]):
    """
    처방 데이터(RAW_RX 기반 dict 리스트)에서 복약 스케줄 자동 생성/갱신.
    이미 존재하면 IGNORE하여 중복 방지.
    """
    init_adherence_db()
    with sqlite3.connect(ADHERENCE_DB) as conn:
        for rx in rx_list:
            pid   = rx.get("patient_id", "")
            med   = rx.get("medication_name", "")
            freq  = rx.get("frequency", "1일1회")
            start = rx.get("start_date", "")
            doses = _parse_doses_per_day(freq)

            if not pid or not med or doses == 0:
                continue  # 간헐적 투여 제외

            # 쉼표로 여러 약품이 묶인 처방 분리
            for med_name in [m.strip() for m in med.split(",")]:
                conn.execute(
                    """INSERT OR IGNORE INTO med_schedule
                       (patient_id, medication_name, doses_per_day, start_date)
                       VALUES (?, ?, ?, ?)""",
                    (pid, med_name, doses, start)
                )
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 복용 기록 저장
# ═══════════════════════════════════════════════════════════════════════════════

def record_medication_taken(
    patient_id: str,
    medication_name: str,
    dose_label: str = "1회분",
    recorded_by: str = "patient",
    notes: str = "",
) -> int:
    """
    복약 완료 기록.

    Parameters
    ----------
    patient_id      : 환자 ID
    medication_name : 약품명
    dose_label      : 복용량 레이블 (예: "1회분", "아침약")
    recorded_by     : "patient" / "nurse" / "voice"
    notes           : 메모

    Returns
    -------
    int: 새로 생성된 레코드 ID
    """
    init_adherence_db()
    with sqlite3.connect(ADHERENCE_DB) as conn:
        cursor = conn.execute(
            """INSERT INTO med_taken
               (patient_id, medication_name, dose_label, recorded_by, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, medication_name, dose_label, recorded_by, notes)
        )
        conn.commit()
        logger.info(f"✅ 복약 기록: {patient_id} - {medication_name} ({dose_label})")
        return cursor.lastrowid


def record_all_meds_taken(
    patient_id: str,
    prescriptions: List[Dict],
    recorded_by: str = "patient",
    notes: str = "",
) -> List[int]:
    """
    "오늘 약 다 먹었어요" → 현재 처방 전체 복약 완료 기록.

    Returns
    -------
    List[int]: 생성된 레코드 ID 목록
    """
    ids = []
    for rx in prescriptions:
        if rx.get("patient_id") != patient_id:
            continue
        med_str = rx.get("medication_name", "")
        freq = rx.get("frequency", "")
        doses = _parse_doses_per_day(freq)
        if doses == 0:
            continue  # 간헐적 투여는 자동 기록 제외

        for med_name in [m.strip() for m in med_str.split(",")]:
            if med_name:
                record_id = record_medication_taken(
                    patient_id, med_name,
                    dose_label="일괄 복용 확인",
                    recorded_by=recorded_by,
                    notes=notes,
                )
                ids.append(record_id)
    return ids


# ═══════════════════════════════════════════════════════════════════════════════
# 복약 이행도 계산
# ═══════════════════════════════════════════════════════════════════════════════

def get_compliance_rate(
    patient_id: str,
    days: int = 7,
) -> Dict:
    """
    최근 N일 복약 이행도 계산.

    Returns
    -------
    dict:
        compliance_rate : float (0~100)
        taken_count     : int
        expected_count  : int
        missed_drugs    : List[str]
        today_taken     : bool
        grade           : str ("우수"/"양호"/"주의"/"위험")
    """
    init_adherence_db()
    today = date.today()
    since = (today - timedelta(days=days)).isoformat()

    with sqlite3.connect(ADHERENCE_DB) as conn:
        # 기간 내 실제 복용 횟수
        taken_rows = conn.execute(
            """SELECT medication_name, COUNT(*) as cnt
               FROM med_taken
               WHERE patient_id = ? AND taken_at >= ?
               GROUP BY medication_name""",
            (patient_id, since)
        ).fetchall()
        taken_map = {r[0]: r[1] for r in taken_rows}

        # 기대 복용 횟수 (스케줄 기반)
        schedules = conn.execute(
            """SELECT medication_name, doses_per_day
               FROM med_schedule
               WHERE patient_id = ? AND active = 1""",
            (patient_id,)
        ).fetchall()

        # 오늘 복용 여부
        today_taken_rows = conn.execute(
            """SELECT COUNT(*) FROM med_taken
               WHERE patient_id = ? AND date(taken_at) = ?""",
            (patient_id, today.isoformat())
        ).fetchone()
        today_taken = today_taken_rows[0] > 0

    if not schedules:
        # 스케줄 없음 → 처방 기반 유추
        return {
            "compliance_rate": 0.0,
            "taken_count": sum(taken_map.values()),
            "expected_count": 0,
            "missed_drugs": [],
            "today_taken": today_taken,
            "grade": "데이터 없음",
        }

    total_expected = 0
    total_taken = 0
    missed_drugs = []

    for med_name, doses_per_day in schedules:
        expected = doses_per_day * days
        taken = taken_map.get(med_name, 0)
        total_expected += expected
        total_taken += taken
        if taken < expected * 0.8:  # 80% 미만이면 누락으로 간주
            missed_drugs.append(med_name)

    if total_expected == 0:
        rate = 0.0
    else:
        rate = min(100.0, (total_taken / total_expected) * 100)

    if rate >= 90:
        grade = "우수"
    elif rate >= 75:
        grade = "양호"
    elif rate >= 50:
        grade = "주의 필요"
    else:
        grade = "위험"

    return {
        "compliance_rate": round(rate, 1),
        "taken_count": total_taken,
        "expected_count": total_expected,
        "missed_drugs": missed_drugs,
        "today_taken": today_taken,
        "grade": grade,
    }


def get_today_taken_meds(patient_id: str) -> List[str]:
    """오늘 복용 완료한 약품 목록."""
    init_adherence_db()
    with sqlite3.connect(ADHERENCE_DB) as conn:
        rows = conn.execute(
            """SELECT DISTINCT medication_name FROM med_taken
               WHERE patient_id = ? AND date(taken_at) = ?""",
            (patient_id, date.today().isoformat())
        ).fetchall()
    return [r[0] for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# 음성 키워드 감지
# ═══════════════════════════════════════════════════════════════════════════════

def detect_taken_from_voice(text: str) -> bool:
    """
    음성 인식 텍스트에서 '약 먹었어' 패턴 감지.

    Returns
    -------
    bool: True = 복약 완료 의사 표현 감지됨
    """
    text_lower = text.lower().strip()
    return any(kw.lower() in text_lower for kw in TAKEN_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 헬퍼
# ═══════════════════════════════════════════════════════════════════════════════

def render_compliance_sentinel_html(
    patient_id: str,
    patient_name: str,
    days: int = 7,
) -> str:
    """
    COMPLIANCE SENTINEL 게이지 HTML 렌더링.
    st.markdown(unsafe_allow_html=True) 에 직접 삽입.
    """
    try:
        data = get_compliance_rate(patient_id, days)
    except Exception:
        data = {"compliance_rate": 0, "grade": "오류", "today_taken": False}

    rate = data["compliance_rate"]
    grade = data["grade"]
    today = data["today_taken"]

    # 색상 결정
    if rate >= 90:
        color = "#00ff88"
        glow  = "0 0 12px rgba(0,255,136,0.5)"
    elif rate >= 75:
        color = "#00e8ff"
        glow  = "0 0 12px rgba(0,232,255,0.4)"
    elif rate >= 50:
        color = "#ffaa00"
        glow  = "0 0 12px rgba(255,170,0,0.4)"
    else:
        color = "#ff4b4b"
        glow  = "0 0 16px rgba(255,75,75,0.6)"

    today_badge = (
        '<span style="background:#00ff88;color:#000;border-radius:4px;'
        'padding:1px 7px;font-size:0.6rem;font-weight:700;margin-left:6px;">오늘 복용 ✓</span>'
        if today else
        '<span style="background:#ff4b4b;color:#fff;border-radius:4px;'
        'padding:1px 7px;font-size:0.6rem;font-weight:700;margin-left:6px;">오늘 미복용</span>'
    )

    bar_width = int(rate)

    return (
        f'<div style="border:1.5px solid rgba(0,242,255,0.28);background:rgba(0,10,30,0.7);'
        f'border-radius:8px;padding:10px 12px;margin-top:6px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="color:rgba(0,200,255,0.6);font-size:0.68rem;font-weight:700;'
        f'font-family:\'Noto Sans KR\',sans-serif;">💊 COMPLIANCE SENTINEL</span>'
        f'{today_badge}'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;gap:6px;margin-bottom:6px;">'
        f'<span style="font-family:\'Orbitron\',sans-serif;color:{color};font-size:2.2rem;'
        f'font-weight:700;text-shadow:{glow};">{rate:.0f}%</span>'
        f'<span style="color:rgba(255,255,255,0.4);font-size:0.7rem;">{grade}</span>'
        f'</div>'
        f'<div style="background:rgba(0,0,0,0.4);border-radius:4px;height:6px;margin-bottom:4px;">'
        f'<div style="background:{color};border-radius:4px;height:6px;'
        f'width:{bar_width}%;transition:width 0.5s ease;"></div>'
        f'</div>'
        f'<div style="color:rgba(0,200,255,0.35);font-size:0.58rem;'
        f'font-family:\'Noto Sans KR\',sans-serif;">최근 {days}일 기준 · {patient_name}</div>'
        f'</div>'
    )


def render_taken_button_area_html(today_meds: List[str]) -> str:
    """오늘 복용한 약품 목록 표시 카드 HTML."""
    if not today_meds:
        return (
            '<div style="color:rgba(255,170,0,0.7);font-size:0.72rem;'
            'font-family:\'Noto Sans KR\',sans-serif;margin-top:4px;">'
            '⚠️ 오늘 복용 기록 없음</div>'
        )
    meds_str = " · ".join(today_meds[:5])
    return (
        f'<div style="color:rgba(0,255,136,0.7);font-size:0.68rem;'
        f'font-family:\'Noto Sans KR\',sans-serif;margin-top:4px;">'
        f'✅ 오늘 복용 완료: {meds_str}</div>'
    )
