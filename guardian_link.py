#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guardian_link.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
보호자 긴급 알림 (Guardian Link) 모듈  v2.1
  - 이상반응·위험 감지 시 등록된 보호자에게 자동 알림 발송
  - 지원 채널: 카카오톡(KakaoTalk), SMS(Twilio), 이메일(SMTP)
  - API 미설정 시 자동으로 로컬 큐에 저장 (앱 내 알림으로 대체)

[카카오톡 발송 구조]
  KAKAO_ACCESS_TOKEN (secrets/env) = 앱 관리자(약사/보호자 대표) 계정의 OAuth 액세스 토큰
  → 나에게 보내기 API (v2/api/talk/memo/default/send) 로 즉시 알림 발송
  → 보호자별 개인 token이 DB에 저장된 경우 해당 토큰 우선 사용
  ※ REST API 키(c819ab4a...)는 OAuth 인증 후 액세스 토큰 발급에 사용됨
     (앱 설정 → Kakao Developers → 제품 → 카카오 로그인 → REST API 키)

필요 패키지:
  pip install twilio  (SMS 사용 시)
  pip install requests (카카오 HTTP 통신)

환경변수 / Streamlit secrets:
  KAKAO_ACCESS_TOKEN   : 카카오 OAuth 액세스 토큰 (나에게 보내기)
  KAKAO_REST_API_KEY   : 카카오 REST API 키 (액세스 토큰 갱신용)
  KAKAO_REFRESH_TOKEN  : 카카오 OAuth 리프레시 토큰 (자동 갱신)
  TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER
  SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS

Author: PHARMA-HYBRID Team
"""

import os
import json
import sqlite3
import logging
import smtplib
from datetime import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── .env 자동 로드 ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)
except ImportError:
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env_path):
        for _line in open(_env_path, encoding="utf-8"):
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if _k.strip() and not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

logger = logging.getLogger("guardian_link")

# ── 알림 DB 경로 ──────────────────────────────────────────────────────────────
GUARDIAN_DB = "guardian_link.db"

# ── 카카오 API 엔드포인트 ──────────────────────────────────────────────────────
KAKAO_SEND_ME_URL    = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TOKEN_URL      = "https://kauth.kakao.com/oauth/token"
KAKAO_TOKEN_INFO_URL = "https://kapi.kakao.com/v1/user/access_token_info"


# ═══════════════════════════════════════════════════════════════════════════════
# DB 초기화 — 보호자 등록 테이블 + 알림 이력 테이블
# ═══════════════════════════════════════════════════════════════════════════════

def init_guardian_db():
    """보호자 DB 초기화 (최초 1회)"""
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guardians (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                guardian_name   TEXT    NOT NULL,
                relation        TEXT    DEFAULT '보호자',
                phone           TEXT,
                email           TEXT,
                kakao_id        TEXT,
                kakao_token     TEXT    DEFAULT '',
                notify_sms      INTEGER DEFAULT 1,
                notify_email    INTEGER DEFAULT 1,
                notify_kakao    INTEGER DEFAULT 1,
                created_at      TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  TEXT    NOT NULL,
                guardian_id INTEGER,
                alert_type  TEXT    NOT NULL,
                severity    TEXT    DEFAULT 'INFO',
                message     TEXT    NOT NULL,
                channel     TEXT    DEFAULT 'app',
                sent_at     TEXT    DEFAULT (datetime('now','localtime')),
                success     INTEGER DEFAULT 1
            )
        """)
        # kakao_token 컬럼 마이그레이션 (기존 DB 호환)
        try:
            conn.execute("ALTER TABLE guardians ADD COLUMN kakao_token TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 이미 존재
        # notify_kakao 기본값 1로 마이그레이션
        try:
            conn.execute("ALTER TABLE guardians ADD COLUMN notify_kakao INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 보호자 등록 / 조회 / 수정
# ═══════════════════════════════════════════════════════════════════════════════

def add_guardian(
    patient_id: str,
    guardian_name: str,
    relation: str = "보호자",
    phone: str = "",
    email: str = "",
    kakao_id: str = "",
    kakao_token: str = "",
) -> int:
    """보호자 등록. 환자 1명당 최대 3명 권장."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        cursor = conn.execute(
            """INSERT INTO guardians
               (patient_id, guardian_name, relation, phone, email, kakao_id,
                kakao_token, notify_sms, notify_email, notify_kakao)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1)""",
            (patient_id, guardian_name, relation, phone, email, kakao_id, kakao_token)
        )
        conn.commit()
        logger.info(f"✅ 보호자 등록: {guardian_name} ({relation}) for {patient_id}")
        return cursor.lastrowid


def get_guardians(patient_id: str) -> List[Dict]:
    """환자의 보호자 목록 반환."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM guardians WHERE patient_id = ? ORDER BY id",
            (patient_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def remove_guardian(guardian_id: int):
    """보호자 삭제."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.execute("DELETE FROM guardians WHERE id = ?", (guardian_id,))
        conn.commit()


def update_guardian_kakao_token(guardian_id: int, access_token: str):
    """보호자 개인 카카오 액세스 토큰 업데이트."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.execute(
            "UPDATE guardians SET kakao_token = ? WHERE id = ?",
            (access_token, guardian_id)
        )
        conn.commit()
    logger.info(f"✅ 보호자 {guardian_id} 카카오 토큰 업데이트 완료")


# ═══════════════════════════════════════════════════════════════════════════════
# 시크릿 로더
# ═══════════════════════════════════════════════════════════════════════════════

def _load_secret(key: str) -> str:
    """
    시크릿 탐색 순서:
    1) 환경변수 (os.environ)
    2) Streamlit secrets (st.secrets)
    3) .env 파일 (dotenv)
    """
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        v = st.secrets.get(key, "")
        if v:
            return v
    except Exception:
        pass
    try:
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        v = env.get(key, "")
        if v:
            return v
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# 카카오 토큰 관리
# ═══════════════════════════════════════════════════════════════════════════════

def _verify_kakao_token(token: str) -> bool:
    """카카오 액세스 토큰 유효성 검사."""
    if not token:
        return False
    try:
        import urllib.request
        req = urllib.request.Request(
            KAKAO_TOKEN_INFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return "id" in data
    except Exception:
        return False


def _refresh_kakao_token() -> str:
    """
    리프레시 토큰으로 새 액세스 토큰 발급.
    KAKAO_REST_API_KEY + KAKAO_REFRESH_TOKEN 필요.
    """
    rest_key     = _load_secret("KAKAO_REST_API_KEY")
    refresh_token = _load_secret("KAKAO_REFRESH_TOKEN")
    if not rest_key or not refresh_token:
        return ""
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            "grant_type":    "refresh_token",
            "client_id":     rest_key,
            "refresh_token": refresh_token,
        }).encode("utf-8")
        req = urllib.request.Request(
            KAKAO_TOKEN_URL, data=data, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            new_token = result.get("access_token", "")
            if new_token:
                logger.info("✅ 카카오 액세스 토큰 자동 갱신 완료")
                # 환경변수 업데이트 (현재 프로세스 내)
                os.environ["KAKAO_ACCESS_TOKEN"] = new_token
            return new_token
    except Exception as e:
        logger.warning(f"⚠️ 카카오 토큰 갱신 실패: {e}")
        return ""


def _get_valid_kakao_token(guardian: Optional[Dict] = None) -> str:
    """
    유효한 카카오 액세스 토큰 반환.
    우선순위: 보호자 개인 토큰 → 시스템 토큰(secrets) → 자동 갱신 시도
    """
    # 1) 보호자 개인 토큰
    if guardian:
        g_token = guardian.get("kakao_token", "")
        if g_token and _verify_kakao_token(g_token):
            return g_token

    # 2) 시스템 공용 토큰 (secrets / env)
    sys_token = _load_secret("KAKAO_ACCESS_TOKEN")
    if sys_token:
        if _verify_kakao_token(sys_token):
            return sys_token
        # 만료됐으면 갱신 시도
        new_token = _refresh_kakao_token()
        if new_token:
            return new_token

    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# 채널별 발송 함수
# ═══════════════════════════════════════════════════════════════════════════════

def _build_kakao_message(text: str) -> dict:
    """카카오 텍스트 메시지 오브젝트 생성 (나에게 보내기 형식)."""
    # 메시지 길이 제한 (200자)
    display_text = text[:197] + "..." if len(text) > 200 else text
    return {
        "object_type": "text",
        "text": display_text,
        "link": {
            "web_url":        "",
            "mobile_web_url": "",
        },
        "button_title": "상세보기",
    }


def _send_kakao(guardian: Optional[Dict], message: str) -> bool:
    """
    카카오톡 '나에게 보내기' API로 알림 발송.

    Parameters
    ----------
    guardian : 보호자 dict (kakao_token 필드 참조). None이면 시스템 토큰만 사용.
    message  : 발송할 메시지 본문

    Returns
    -------
    bool: 발송 성공 여부
    """
    import urllib.request, urllib.parse

    token = _get_valid_kakao_token(guardian)
    if not token:
        logger.warning("⚠️ 유효한 카카오 액세스 토큰 없음 — 카카오 발송 생략")
        logger.warning("   → secrets.toml 에 KAKAO_ACCESS_TOKEN 설정 또는 토큰 갱신 필요")
        return False

    try:
        payload = _build_kakao_message(message)
        data = urllib.parse.urlencode({
            "template_object": json.dumps(payload, ensure_ascii=False)
        }).encode("utf-8")

        req = urllib.request.Request(
            KAKAO_SEND_ME_URL,
            data=data,
            headers={
                "Authorization":  f"Bearer {token}",
                "Content-Type":   "application/x-www-form-urlencoded;charset=utf-8",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            body   = resp.read().decode("utf-8")
            result = json.loads(body)
            code   = result.get("result_code", -1)

            if code == 0:
                g_name = guardian.get("guardian_name", "시스템") if guardian else "시스템"
                logger.info(f"✅ 카카오톡 발송 완료 → {g_name}")
                return True

            logger.warning(f"⚠️ 카카오톡 API 응답 이상: result_code={code}, body={body[:200]}")
            return False

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error(f"❌ 카카오톡 HTTP 오류 {e.code}: {body[:300]}")
        # 401 Unauthorized = 토큰 만료 → 자동 갱신 재시도
        if e.code == 401:
            logger.info("🔄 카카오 토큰 만료 감지 — 자동 갱신 후 재시도")
            new_token = _refresh_kakao_token()
            if new_token:
                return _send_kakao(guardian, message)  # 1회 재시도
        return False
    except Exception as e:
        logger.error(f"❌ 카카오톡 발송 예외: {e}")
        return False


def _send_sms(to_number: str, message: str) -> bool:
    """Twilio SMS 발송."""
    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning("⚠️ twilio 패키지 미설치. pip install twilio")
        return False

    sid   = _load_secret("TWILIO_ACCOUNT_SID")
    token = _load_secret("TWILIO_AUTH_TOKEN")
    from_ = _load_secret("TWILIO_FROM_NUMBER")

    if not all([sid, token, from_, to_number]):
        logger.warning("⚠️ Twilio 설정 불완전 — SMS 발송 생략")
        return False

    try:
        client = Client(sid, token)
        client.messages.create(body=message, from_=from_, to=to_number)
        logger.info(f"✅ SMS 발송 완료 → {to_number}")
        return True
    except Exception as e:
        logger.error(f"❌ SMS 발송 실패: {e}")
        return False


def _send_email(to_email: str, subject: str, body: str) -> bool:
    """SMTP 이메일 발송."""
    host = _load_secret("SMTP_HOST")
    port = int(_load_secret("SMTP_PORT") or 587)
    user = _load_secret("SMTP_USER")
    pwd  = _load_secret("SMTP_PASS")

    if not all([host, user, pwd, to_email]):
        logger.warning("⚠️ SMTP 설정 불완전 — 이메일 발송 생략")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = user
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, pwd)
            server.sendmail(user, [to_email], msg.as_string())

        logger.info(f"✅ 이메일 발송 완료 → {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ 이메일 발송 실패: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 긴급 알림 메인 함수
# ═══════════════════════════════════════════════════════════════════════════════

SEVERITY_LEVELS = {
    "INFO":     "ℹ️",
    "WARNING":  "⚠️",
    "CRITICAL": "🚨",
}


def send_guardian_alert(
    patient_id: str,
    patient_name: str,
    alert_type: str,
    message: str,
    severity: str = "WARNING",
    extra_data: Optional[Dict] = None,
) -> Dict:
    """
    보호자에게 긴급 알림 발송.

    Parameters
    ----------
    patient_id   : 환자 ID
    patient_name : 환자 이름
    alert_type   : 알림 유형 ("부작용감지" / "복약미실시" / "응급상황" / "수동 알림")
    message      : 상세 메시지
    severity     : "INFO" / "WARNING" / "CRITICAL"
    extra_data   : 추가 데이터 dict

    Returns
    -------
    dict: {"sent": 발송 수, "guardians": [...], "log_ids": [...], "full_message": str}
    """
    init_guardian_db()
    guardians = get_guardians(patient_id)

    icon      = SEVERITY_LEVELS.get(severity, "⚠️")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 메시지 포맷 (모바일 카카오톡 가독성 최적화) ─────────────────────────
    full_message = (
        f"{icon} PHARMA-HYBRID 보호자 알림\n"
        f"{'─' * 20}\n"
        f"환자: {patient_name} ({patient_id})\n"
        f"유형: {alert_type}\n"
        f"시각: {timestamp}\n"
        f"{'─' * 20}\n"
        f"{message}"
    )
    if extra_data:
        full_message += f"\n\n[추가 정보]\n{json.dumps(extra_data, ensure_ascii=False, indent=2)}"

    subject = f"[{severity}] {patient_name}님 {alert_type} 알림"

    result = {
        "sent":         0,
        "guardians":    [],
        "log_ids":      [],
        "full_message": full_message,
        "errors":       [],
    }

    if not guardians:
        # 보호자 미등록 → 시스템 토큰으로 나에게 보내기 시도
        kakao_ok = _send_kakao(None, full_message)
        channel  = "카카오톡(시스템)" if kakao_ok else "app(대기)"
        if kakao_ok:
            result["sent"] += 1
        log_id = _log_alert(patient_id, None, alert_type, severity, message, channel)
        result["log_ids"].append(log_id)
        logger.info(f"ℹ️ {patient_id} 보호자 미등록 — 시스템 카카오 계정으로 발송 시도")
        return result

    # ── [긴급] 전송 엔진 가동 ──────────────────────────────────────────
    for g in guardians:
        sent_channels = []
        g_id = g.get("id")
        g_name = g.get("guardian_name", "보호자")
        
        # ── SMS 발송 (Twilio/국가코드 보정) ────────────────────────────────
        if g.get("notify_sms", 1) and g.get("phone"):
            phone = g["phone"].strip()
            # 국내 번호(+82) 자동 보정
            if phone.startswith("010"):
                phone = "+82" + phone[1:]
            
            ok = _send_sms(phone, full_message)
            if ok:
                sent_channels.append("SMS")
                result["sent"] += 1
            else:
                err_msg = f"SMS 전송 실패: {g_name} ({phone})"
                result["errors"].append(err_msg)
                logger.error(f"❌ {err_msg}")

        # ── 앱 내 로그 및 큐 ──────────────────────────────────────────────
        channel_str = ",".join(sent_channels) if sent_channels else "ERROR/RETRY"
        log_id = _log_alert(patient_id, g_id, alert_type, severity, message, channel_str)
        result["log_ids"].append(log_id)
        result["guardians"].append({
            "name":     g_name,
            "relation": g.get("relation", "보호자"),
            "channels": sent_channels or ["전송 실패 (환경 설정 확인 요망)"],
        })

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 알림 이력 로그
# ═══════════════════════════════════════════════════════════════════════════════

def _log_alert(
    patient_id: str,
    guardian_id: Optional[int],
    alert_type: str,
    severity: str,
    message: str,
    channel: str,
) -> int:
    """알림 이력 DB 저장. 발송 실패해도 항상 기록."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        cursor = conn.execute(
            """INSERT INTO alert_log
               (patient_id, guardian_id, alert_type, severity, message, channel)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (patient_id, guardian_id, alert_type, severity, message, channel)
        )
        conn.commit()
        return cursor.lastrowid


def get_alert_history(patient_id: str, limit: int = 20) -> List[Dict]:
    """최근 알림 이력 조회."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT a.*, g.guardian_name, g.relation
               FROM alert_log a
               LEFT JOIN guardians g ON a.guardian_id = g.id
               WHERE a.patient_id = ?
               ORDER BY a.sent_at DESC
               LIMIT ?""",
            (patient_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def get_pending_alerts(limit: int = 50) -> List[Dict]:
    """채널='app(대기)' 인 미발송 알림 (앱 내 표시용)."""
    init_guardian_db()
    with sqlite3.connect(GUARDIAN_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM alert_log
               WHERE channel LIKE '%app%'
               ORDER BY sent_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# 자동 이상반응 감지 트리거  ← 키워드 대폭 확장
# ═══════════════════════════════════════════════════════════════════════════════

DANGER_KEYWORDS = {
    "CRITICAL": [
        # 생명 위협
        "호흡곤란", "숨막혀", "숨이 안 쉬어져", "숨을 못 쉬겠어",
        "의식", "쓰러짐", "쓰러졌어", "쓰러졌습니다", "쓰러질 것 같아",
        "응급", "응급실", "119", "심정지", "심장이 멈춰",
        "실신", "기절", "기절할 것 같아",
        "심각한 출혈", "피를 많이 흘려", "피가 멈추지 않아",
        "아나필락시스", "알레르기 쇼크", "온몸이 부어",
        "경련", "발작", "간질",
        "의식 없어", "말을 못 해", "반응이 없어",
    ],
    "WARNING": [
        # 통증 (핵심 — "아파요" 류 전부 포함)
        "아파요", "아파", "아파서", "너무 아파", "많이 아파",
        "아프다", "아픔", "아픈데", "아픈 것 같아",
        "통증", "심한 통증", "극심한 통증", "통증이 심해",
        "쑤셔요", "쑤셔", "쑤시고", "결려요", "결려",
        "욱신욱신", "찌르는 것 같아", "칼로 찌르는",
        "배가 아파", "배 아파", "복통", "복부 통증",
        "가슴이 아파", "가슴 통증", "흉통",
        "머리가 아파", "두통", "머리가 깨질 것 같아",
        # 소화기
        "구토", "토했어", "계속 토해", "구역질", "메스꺼워",
        "설사", "심한 설사", "혈변",
        # 발열
        "발열", "열이 나", "열이 많이 나", "고열", "오한",
        # 기타 이상반응
        "혈뇨", "소변에 피", "황달", "피부 발진", "두드러기",
        "부종", "다리가 부어", "얼굴이 부어",
        "백혈구 감소", "절대 금기",
        "힘들어", "너무 힘들어", "몸이 너무 안 좋아",
        "어지러워", "어지럼증", "빙빙 돌아",
        "손발이 저려", "저림", "마비",
        "숨이 차", "숨차",
    ],
}

# 통증 빠른 감지용 단순 키워드 (analyze_voice 에서 우선 체크)
PAIN_QUICK_KEYWORDS = ["아파", "통증", "힘들어", "아프다", "쑤셔"]


def auto_detect_and_alert(
    patient_id: str,
    patient_name: str,
    text: str,
    disease: str = "",
) -> Optional[Dict]:
    """
    입력 텍스트(음성·메모)에서 위험 키워드 자동 감지 후 보호자 알림.

    Returns
    -------
    dict or None: 알림 발송 결과 (감지 없으면 None)
    """
    found_level    = None
    found_keywords = []

    for level in ("CRITICAL", "WARNING"):
        for kw in DANGER_KEYWORDS[level]:
            if kw in text:
                found_keywords.append(kw)
                if not found_level:
                    found_level = level

    if not found_level:
        return None

    logger.info(f"🚨 위험 키워드 감지: {found_keywords} (레벨: {found_level})")

    message = (
        f"환자 {patient_name}님에게 이상 증상이 감지되었습니다.\n\n"
        f"감지 키워드: {', '.join(found_keywords)}\n"
        f"관련 질환:   {disease or '미상'}\n\n"
        f"즉시 환자 상태를 확인하고, 필요 시 의료진에게 연락하세요."
    )

    return send_guardian_alert(
        patient_id=patient_id,
        patient_name=patient_name,
        alert_type="이상반응감지",
        message=message,
        severity=found_level,
        extra_data={"detected_keywords": found_keywords, "disease": disease},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 카카오 토큰 상태 확인 (UI 헬퍼)
# ═══════════════════════════════════════════════════════════════════════════════

def get_kakao_status() -> Dict:
    """
    현재 카카오 토큰 상태 반환.
    Returns: {"token_set": bool, "token_valid": bool, "mode": str}
    """
    token = _load_secret("KAKAO_ACCESS_TOKEN")
    if not token:
        return {"token_set": False, "token_valid": False, "mode": "⚪ 미설정"}

    valid = _verify_kakao_token(token)
    if valid:
        return {"token_set": True, "token_valid": True,  "mode": "🟢 정상"}
    else:
        return {"token_set": True, "token_valid": False, "mode": "🔴 만료 (갱신 필요)"}


# ═══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 헬퍼
# ═══════════════════════════════════════════════════════════════════════════════

def render_guardian_panel_html(patient_id: str) -> str:
    """보호자 등록 현황 + 최근 알림 이력을 HTML로 렌더링."""
    try:
        init_guardian_db()
        guardians = get_guardians(patient_id)
        pending   = get_pending_alerts(5)
    except Exception:
        return ""

    # 보호자 카드
    g_cards = ""
    if guardians:
        for g in guardians:
            phone_icon = "📱" if g.get("phone") else ""
            email_icon = "📧" if g.get("email") else ""
            kakao_icon = "💬" if g.get("kakao_token") else ""
            g_cards += (
                f'<div style="display:flex;align-items:center;gap:8px;'
                f'background:rgba(0,20,50,0.5);border-radius:5px;padding:5px 8px;margin-bottom:4px;">'
                f'<span style="color:#00ff88;font-size:0.75rem;">👤</span>'
                f'<span style="color:#c8eeff;font-size:0.72rem;font-family:\'Noto Sans KR\',sans-serif;">'
                f'{g["guardian_name"]} ({g["relation"]})</span>'
                f'<span style="color:rgba(0,200,255,0.5);font-size:0.65rem;">'
                f'{phone_icon}{email_icon}{kakao_icon}</span>'
                f'</div>'
            )
    else:
        g_cards = '<div style="color:rgba(255,200,0,0.6);font-size:0.72rem;">보호자 미등록</div>'

    # 미발송 알림 배지
    badge = (
        f'<span style="background:#ff4b4b;color:#fff;border-radius:999px;'
        f'padding:1px 6px;font-size:0.65rem;margin-left:4px;">{len(pending)}</span>'
        if pending else ""
    )

    # 카카오 상태
    kakao_st  = get_kakao_status()
    kakao_clr = "#00ff88" if kakao_st["token_valid"] else "#ffaa00"
    kakao_lbl = kakao_st["mode"]

    return (
        f'<div style="margin-top:8px;border:1px solid rgba(0,255,136,0.2);'
        f'border-radius:6px;padding:8px 10px;">'
        f'<div style="color:rgba(0,255,136,0.7);font-size:0.7rem;font-weight:700;'
        f'font-family:\'Noto Sans KR\',sans-serif;margin-bottom:6px;">'
        f'🛡️ GUARDIAN LINK{badge}</div>'
        f'{g_cards}'
        f'<div style="margin-top:5px;font-size:0.6rem;font-family:\'Noto Sans KR\',sans-serif;">'
        f'<span style="color:{kakao_clr};">💬 카카오: {kakao_lbl}</span>'
        f'</div>'
        f'</div>'
    )
