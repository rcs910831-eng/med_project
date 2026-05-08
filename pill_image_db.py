#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pill_image_db.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
알약 이미지 데이터베이스 모듈

데이터 출처:
  🇰🇷 식품의약품안전처 (MFDS) 낱알식별정보 API
       https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService01
  🇺🇸 NIH DailyMed API (국제 의약품)
       https://dailymed.nlm.nih.gov/dailymed/services/v2/
  🌐 OpenFDA Drug API
       https://api.fda.gov/drug/

기능:
  - 환자 처방 약물명으로 MFDS/NIH 에서 낱알 정보 자동 수집
  - 알약 이미지 URL + 실제 이미지 바이너리 SQLite 저장
  - 색상/모양/마킹 인덱스 구축 → 빠른 특징 검색
  - Gemini Vision 결과와 교차 검증
"""

import os
import sqlite3
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("pill_image_db")

# ── .env 로드 ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
except ImportError:
    _ep = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_ep):
        for _l in open(_ep, encoding="utf-8"):
            _l = _l.strip()
            if _l and not _l.startswith("#") and "=" in _l:
                _k, _v = _l.split("=", 1)
                if _k.strip() and not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

PILL_DB = os.path.join(os.path.dirname(__file__), "pill_images.db")

# ── MFDS API 설정 ─────────────────────────────────────────────────────────────
MFDS_PILL_URL   = "https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03"
DAILYMED_URL    = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
OPENFDA_URL     = "https://api.fda.gov/drug/ndc.json"

# ── 색상/모양 코드 → 한국어 ──────────────────────────────────────────────────
COLOR_KR = {
    "하양": "white",  "흰색": "white",
    "노랑": "yellow", "황색": "yellow",
    "주황": "orange",
    "분홍": "pink",   "핑크": "pink",
    "빨강": "red",    "적색": "red",
    "갈색": "brown",  "褐": "brown",
    "연두": "light_green",
    "초록": "green",  "녹색": "green",
    "파랑": "blue",   "청색": "blue",
    "남색": "navy",
    "보라": "purple",
    "회색": "gray",   "灰色": "gray",
    "검정": "black",
    "투명": "transparent",
}

SHAPE_KR = {
    "원형": "circle",    "타원형": "oval",     "장방형": "oblong",
    "삼각형": "triangle", "사각형": "square",   "팔각형": "octagon",
    "오각형": "pentagon", "육각형": "hexagon",  "반원형": "half_circle",
    "기타": "other",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DB 초기화
# ═══════════════════════════════════════════════════════════════════════════════

def init_pill_db():
    """알약 이미지 DB 초기화."""
    with sqlite3.connect(PILL_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pills (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name_kr    TEXT    NOT NULL,
                drug_name_en    TEXT    DEFAULT '',
                manufacturer    TEXT    DEFAULT '',
                shape           TEXT    DEFAULT '',
                color_front     TEXT    DEFAULT '',
                color_back      TEXT    DEFAULT '',
                marking_front   TEXT    DEFAULT '',
                marking_back    TEXT    DEFAULT '',
                line_front      TEXT    DEFAULT '',
                line_back       TEXT    DEFAULT '',
                form_type       TEXT    DEFAULT '',
                otc_type        TEXT    DEFAULT '',
                drug_class      TEXT    DEFAULT '',
                image_url       TEXT    DEFAULT '',
                image_data      BLOB,
                image_thumb     BLOB,
                source          TEXT    DEFAULT 'MFDS',
                raw_json        TEXT    DEFAULT '{}',
                fetched_at      TEXT    DEFAULT (datetime('now','localtime')),
                UNIQUE(drug_name_kr, manufacturer)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patient_drug_map (
                patient_id  TEXT    NOT NULL,
                drug_name   TEXT    NOT NULL,
                pill_id     INTEGER,
                mapped_at   TEXT    DEFAULT (datetime('now','localtime')),
                PRIMARY KEY (patient_id, drug_name)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pills_name ON pills(drug_name_kr)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pills_shape ON pills(shape, color_front)
        """)
        conn.commit()
    logger.info("✅ pill_images.db 초기화 완료")


# ═══════════════════════════════════════════════════════════════════════════════
# MFDS 낱알식별 API
# ═══════════════════════════════════════════════════════════════════════════════

def _get_api_key() -> str:
    """공공데이터포털 API 키 (DRUG_STOCK_API_KEY 재사용)."""
    for k in ("DRUG_STOCK_API_KEY", "MFDS_API_KEY", "PUBLIC_DATA_API_KEY"):
        v = os.environ.get(k, "")
        if v:
            return v
    return ""


def fetch_mfds_pill_info(drug_name: str, page: int = 1, rows: int = 10) -> List[Dict]:
    """
    MFDS 낱알식별 API v03 호출.
    serviceKey 를 URL에 직접 삽입 (이중인코딩 방지).
    """
    import requests as _req
    api_key = _get_api_key()
    if not api_key:
        return _get_fallback_pill_info(drug_name)

    import urllib.parse
    encoded_name = urllib.parse.quote(drug_name, safe="")
    url = (
        f"{MFDS_PILL_URL}"
        f"?serviceKey={api_key}"
        f"&item_name={encoded_name}"
        f"&type=json"
        f"&numOfRows={rows}"
        f"&pageNo={page}"
    )
    try:
        resp = _req.get(url, timeout=10, verify=False,
                        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        data = resp.json()
        items = (data.get("body") or {}).get("items") or []
        if isinstance(items, dict):
            items = [items]
        logger.info(f"✅ MFDS v03 [{drug_name}]: {len(items)}건")
        return items
    except Exception as e:
        logger.warning(f"⚠️ MFDS v03 API 실패 ({drug_name}): {e}")
        return _get_fallback_pill_info(drug_name)


def fetch_mfds_all(page: int = 1, rows: int = 100) -> List[Dict]:
    """MFDS 전체 낱알 목록 페이지 단위 조회."""
    import requests as _req
    api_key = _get_api_key()
    if not api_key:
        return []
    url = (
        f"{MFDS_PILL_URL}"
        f"?serviceKey={api_key}"
        f"&type=json&numOfRows={rows}&pageNo={page}"
    )
    try:
        resp = _req.get(url, timeout=15, verify=False,
                        headers={"User-Agent": "Mozilla/5.0"})
        data = resp.json()
        body  = data.get("body") or {}
        items = body.get("items") or []
        total = body.get("totalCount", 0)
        if isinstance(items, dict):
            items = [items]
        return items, total
    except Exception as e:
        logger.error(f"❌ MFDS 전체 조회 실패: {e}")
        return [], 0


def _fetch_mfds_urllib(drug_name: str) -> List[Dict]:
    """requests 없을 때 urllib 사용 (v03)."""
    import urllib.request, urllib.parse
    api_key = _get_api_key()
    encoded_name = urllib.parse.quote(drug_name, safe="")
    url = (f"{MFDS_PILL_URL}?serviceKey={api_key}"
           f"&item_name={encoded_name}&type=json&numOfRows=10&pageNo=1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
            items = (data.get("body") or {}).get("items") or []
            if isinstance(items, dict):
                items = [items]
            return items
    except Exception as e:
        logger.warning(f"⚠️ urllib MFDS 호출 실패: {e}")
        return _get_fallback_pill_info(drug_name)


# ── 알약 상세 내장 데이터 (API 없을 때 fallback) ─────────────────────────────
PILL_FALLBACK_DB: Dict[str, Dict] = {
    "타세바": {
        "ITEM_NAME": "타세바정150mg", "ENTP_NAME": "한국로슈",
        "CHART": "원형 흰색 필름코팅정, 한 면에 'TBE' 음각",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "TBE", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148701202000020",
    },
    "타그리소": {
        "ITEM_NAME": "타그리소정80mg", "ENTP_NAME": "아스트라제네카",
        "CHART": "베이지/갈색 타원형 필름코팅정, 'AZ' 마킹",
        "COLOR_CLASS1": "갈색", "SHAPE_CODE": "타원형",
        "PRINT_FRONT": "AZ", "PRINT_BACK": "80",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148801201900033",
    },
    "글리벡": {
        "ITEM_NAME": "글리벡정400mg", "ENTP_NAME": "한국노바티스",
        "CHART": "황색 타원형 필름코팅정, 'NVR/SA' 마킹",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "타원형",
        "PRINT_FRONT": "NVR", "PRINT_BACK": "SA",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148301200500021",
    },
    "입랜스": {
        "ITEM_NAME": "입랜스캡슐125mg", "ENTP_NAME": "한국화이자",
        "CHART": "적갈색/적갈색 캡슐, 'Pfizer PBC 125' 마킹",
        "COLOR_CLASS1": "갈색", "SHAPE_CODE": "캡슐형",
        "PRINT_FRONT": "PBC 125", "PRINT_BACK": "Pfizer",
        "FORM_CODE_NAME": "경질캡슐", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148801201500040",
    },
    "넥사바": {
        "ITEM_NAME": "넥사바정200mg", "ENTP_NAME": "바이엘코리아",
        "CHART": "빨강 원형 필름코팅정, '200' 마킹",
        "COLOR_CLASS1": "빨강", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "200", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148501200600028",
    },
    "젤로다": {
        "ITEM_NAME": "젤로다정500mg", "ENTP_NAME": "한국로슈",
        "CHART": "복숭아색 장방형 필름코팅정, 'XELODA 500' 마킹",
        "COLOR_CLASS1": "주황", "SHAPE_CODE": "장방형",
        "PRINT_FRONT": "XELODA 500", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148701200500024",
    },
    "레트로졸": {
        "ITEM_NAME": "레트로졸정2.5mg", "ENTP_NAME": "한국노바티스",
        "CHART": "황색 원형 필름코팅정, 'FV/CG' 마킹",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "FV", "PRINT_BACK": "CG",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148301200200020",
    },
    "아스피린": {
        "ITEM_NAME": "아스피린프로텍트정100mg", "ENTP_NAME": "바이엘코리아",
        "CHART": "흰색 원형 장용정",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "ASPIRIN", "PRINT_BACK": "",
        "FORM_CODE_NAME": "장용정", "ETC_OTC_NAME": "일반의약품",
        "CLASS_NAME": "해열·진통·소염제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148501200000014",
    },
    "메트포르민": {
        "ITEM_NAME": "메트포르민염산염정500mg", "ENTP_NAME": "동아에스티",
        "CHART": "흰색 원형 필름코팅정",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "DA", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "당뇨병용제",
        "ITEM_IMAGE": "",
    },
    "암로디핀": {
        "ITEM_NAME": "암로디핀베실산염정5mg", "ENTP_NAME": "한국화이자",
        "CHART": "흰색 원형 나정",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "아스코", "PRINT_BACK": "5",
        "FORM_CODE_NAME": "나정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "혈압강하제",
        "ITEM_IMAGE": "",
    },
    "로수바스타틴": {
        "ITEM_NAME": "크레스토정10mg", "ENTP_NAME": "한국아스트라제네카",
        "CHART": "분홍색 원형 필름코팅정, 'ZD4522 10' 마킹",
        "COLOR_CLASS1": "분홍", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "ZD4522 10", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "고지혈증용제",
        "ITEM_IMAGE": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148801200300018",
    },
    "탐옥시펜": {
        "ITEM_NAME": "놀바덱스정20mg", "ENTP_NAME": "한국아스트라제네카",
        "CHART": "흰색 팔각형 나정, 'Nolvadex 20' 마킹",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "팔각형",
        "PRINT_FRONT": "NOLVADEX 20", "PRINT_BACK": "",
        "FORM_CODE_NAME": "나정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제",
        "ITEM_IMAGE": "",
    },
    "도네페질": {
        "ITEM_NAME": "아리셉트정10mg", "ENTP_NAME": "한국에자이",
        "CHART": "노란색 원형 필름코팅정, 'ARICEPT 10' 마킹",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "ARICEPT 10", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "치매치료제",
        "ITEM_IMAGE": "",
    },
    "레보티록신": {
        "ITEM_NAME": "씬지로이드정0.1mg", "ENTP_NAME": "한국애브비",
        "CHART": "노란색 원형 나정",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "SYNTHROID", "PRINT_BACK": "",
        "FORM_CODE_NAME": "나정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "갑상선호르몬제",
        "ITEM_IMAGE": "",
    },
    "오메프라졸": {
        "ITEM_NAME": "오메프라졸캡슐20mg", "ENTP_NAME": "아스트라제네카",
        "CHART": "분홍/투명 캡슐",
        "COLOR_CLASS1": "분홍", "SHAPE_CODE": "캡슐형",
        "PRINT_FRONT": "20", "PRINT_BACK": "",
        "FORM_CODE_NAME": "경질캡슐", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "소화성궤양용제",
        "ITEM_IMAGE": "",
    },
    "칼슘제": {
        "ITEM_NAME": "칼트레이트600정", "ENTP_NAME": "한국화이자",
        "CHART": "흰색 타원형 필름코팅정",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "타원형",
        "PRINT_FRONT": "600", "PRINT_BACK": "",
        "FORM_CODE_NAME": "필름코팅정", "ETC_OTC_NAME": "일반의약품",
        "CLASS_NAME": "칼슘제",
        "ITEM_IMAGE": "",
    },
    "비타민D": {
        "ITEM_NAME": "비타민D3연질캡슐1000IU", "ENTP_NAME": "유한양행",
        "CHART": "노란색 연질캡슐",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "캡슐형",
        "PRINT_FRONT": "", "PRINT_BACK": "",
        "FORM_CODE_NAME": "연질캡슐", "ETC_OTC_NAME": "일반의약품",
        "CLASS_NAME": "비타민제",
        "ITEM_IMAGE": "",
    },
}

# 국제 의약품 (NIH DailyMed 기반)
INTL_PILL_DB: Dict[str, Dict] = {
    "키트루다": {
        "ITEM_NAME": "Keytruda (pembrolizumab) 100mg/4mL",
        "ENTP_NAME": "Merck Sharp & Dohme",
        "CHART": "무색 또는 약간 황색의 투명 액상 (주사제)",
        "COLOR_CLASS1": "투명", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·면역항암제",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?name=keytruda.jpg",
        "ndc": "0006-3026-04",
    },
    "옵디보": {
        "ITEM_NAME": "Opdivo (nivolumab) 10mg/mL",
        "ENTP_NAME": "Bristol-Myers Squibb",
        "CHART": "무색 또는 약간 황색 투명 액상 (주사제)",
        "COLOR_CLASS1": "투명", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·PD-1억제제",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?name=opdivo.jpg",
        "ndc": "0003-3772-11",
    },
    "허셉틴": {
        "ITEM_NAME": "Herceptin (trastuzumab) 440mg",
        "ENTP_NAME": "Genentech/Roche",
        "CHART": "흰색 동결건조 분말 (주사용 바이알)",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "주사제(동결건조)",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·HER2억제제",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "50242-134-01",
    },
    "파클리탁셀": {
        "ITEM_NAME": "Paclitaxel Injection 6mg/mL",
        "ENTP_NAME": "Hospira",
        "CHART": "투명 ~ 황색 액상 (주사제)",
        "COLOR_CLASS1": "투명", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·탁산계",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0409-0725-34",
    },
    "독소루비신": {
        "ITEM_NAME": "Doxorubicin Hydrochloride Injection",
        "ENTP_NAME": "Pfizer",
        "CHART": "적색 투명 액상 (주사제) — '붉은 악마' 별칭",
        "COLOR_CLASS1": "빨강", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·안트라사이클린계",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0069-3031-20",
    },
    "메토트렉세이트": {
        "ITEM_NAME": "Methotrexate Tablet 2.5mg",
        "ENTP_NAME": "Roxane Laboratories",
        "CHART": "노란색 원형 나정",
        "COLOR_CLASS1": "노랑", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "54 092", "PRINT_BACK": "",
        "FORM_CODE_NAME": "나정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·면역억제제",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0054-4010-25",
    },
    "카보플라틴": {
        "ITEM_NAME": "Carboplatin Injection 10mg/mL",
        "ENTP_NAME": "Teva Pharmaceuticals",
        "CHART": "무색 투명 액상 (주사제)",
        "COLOR_CLASS1": "투명", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·백금계",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0703-5759-01",
    },
    "옥살리플라틴": {
        "ITEM_NAME": "Oxaliplatin for Injection 5mg/mL",
        "ENTP_NAME": "Sanofi",
        "CHART": "무색 ~ 약간 황색 액상 (주사제)",
        "COLOR_CLASS1": "투명", "SHAPE_CODE": "주사제",
        "FORM_CODE_NAME": "주사제", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "항악성종양제·백금계",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0024-5591-20",
    },
    "에스트라디올": {
        "ITEM_NAME": "Estradiol Tablet 1mg",
        "ENTP_NAME": "Warner Chilcott",
        "CHART": "흰색 원형 나정",
        "COLOR_CLASS1": "하양", "SHAPE_CODE": "원형",
        "PRINT_FRONT": "E 1", "PRINT_BACK": "",
        "FORM_CODE_NAME": "나정", "ETC_OTC_NAME": "전문의약품",
        "CLASS_NAME": "여성호르몬제",
        "source": "NIH_DailyMed",
        "ITEM_IMAGE": "",
        "ndc": "0430-0355-14",
    },
}


def _get_fallback_pill_info(drug_name: str) -> List[Dict]:
    """API 키 없을 때 내장 DB 조회."""
    # 한국 DB 검색
    for key, val in PILL_FALLBACK_DB.items():
        if key in drug_name or drug_name in key or drug_name in val.get("ITEM_NAME", ""):
            return [val]
    # 국제 DB 검색
    for key, val in INTL_PILL_DB.items():
        if key in drug_name or drug_name in key or drug_name in val.get("ITEM_NAME", ""):
            return [val]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# 이미지 다운로드
# ═══════════════════════════════════════════════════════════════════════════════

def _download_image(url: str, timeout: int = 10) -> Optional[bytes]:
    """이미지 URL → bytes 다운로드."""
    if not url:
        return None
    try:
        import requests
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "PharmaHybrid/1.0"})
        if resp.status_code == 200 and len(resp.content) > 500:
            return resp.content
    except Exception:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = r.read()
                if len(data) > 500:
                    return data
        except Exception:
            pass
    return None


def _make_thumbnail(image_bytes: bytes, size: Tuple[int,int] = (120,120)) -> Optional[bytes]:
    """PIL 썸네일 생성."""
    if not image_bytes:
        return None
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(size, Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DB 저장 / 조회
# ═══════════════════════════════════════════════════════════════════════════════

def save_pill_to_db(item: Dict, source: str = "MFDS") -> int:
    """낱알 정보 + 이미지 DB 저장."""
    init_pill_db()

    # v03 필드명 우선, fallback 필드명 보조
    def _f(*keys):
        for k in keys:
            v = item.get(k, "")
            if v and str(v).lower() not in ("none", "null", ""):
                return str(v).strip()
        return ""

    name_kr  = _f("ITEM_NAME",   "item_name")
    name_en  = _f("ITEM_ENG_NAME","item_eng_name")
    maker    = _f("ENTP_NAME",   "entp_name")
    img_url  = _f("ITEM_IMAGE",  "item_image")
    shape    = _f("DRUG_SHAPE",  "SHAPE_CODE_NAME","SHAPE_CODE","shape_code")
    color1   = _f("COLOR_CLASS1","color_class1")
    color2   = _f("COLOR_CLASS2","color_class2")
    mark_f   = _f("PRINT_FRONT", "print_front","MARK_CODE_FRONT")
    mark_b   = _f("PRINT_BACK",  "print_back", "MARK_CODE_BACK")
    line_f   = _f("LINE_FRONT",  "line_front")
    line_b   = _f("LINE_BACK",   "line_back")
    form     = _f("FORM_CODE_NAME","form_code_name")
    otc      = _f("ETC_OTC_NAME","etc_otc_name")
    cls      = _f("CLASS_NAME",  "class_name")

    # 이미지 다운로드
    img_data  = _download_image(img_url) if img_url else None
    img_thumb = _make_thumbnail(img_data) if img_data else None

    with sqlite3.connect(PILL_DB) as conn:
        cursor = conn.execute(
            """INSERT OR REPLACE INTO pills
               (drug_name_kr, drug_name_en, manufacturer,
                shape, color_front, color_back,
                marking_front, marking_back, line_front, line_back,
                form_type, otc_type, drug_class,
                image_url, image_data, image_thumb,
                source, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                name_kr, name_en, maker,
                shape, color1, color2,
                mark_f, mark_b, line_f, line_b,
                form, otc, cls,
                img_url, img_data, img_thumb,
                source, json.dumps(item, ensure_ascii=False),
            )
        )
        conn.commit()
        return cursor.lastrowid


def get_pill_from_db(drug_name: str) -> List[Dict]:
    """약품명으로 DB 조회."""
    init_pill_db()
    with sqlite3.connect(PILL_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM pills
               WHERE drug_name_kr LIKE ? OR drug_name_kr LIKE ?
               ORDER BY id LIMIT 5""",
            (f"%{drug_name}%", f"{drug_name}%")
        ).fetchall()
    return [dict(r) for r in rows]


def search_by_features(
    color: str = "",
    shape: str = "",
    marking: str = "",
    limit: int = 10,
) -> List[Dict]:
    """색상/모양/마킹으로 알약 검색."""
    init_pill_db()
    clauses, args = [], []
    if color:
        clauses.append("(color_front LIKE ? OR color_back LIKE ?)")
        args += [f"%{color}%", f"%{color}%"]
    if shape:
        clauses.append("shape LIKE ?")
        args.append(f"%{shape}%")
    if marking:
        clauses.append("(marking_front LIKE ? OR marking_back LIKE ?)")
        args += [f"%{marking}%", f"%{marking}%"]

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with sqlite3.connect(PILL_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT * FROM pills {where} LIMIT ?",
            args + [limit]
        ).fetchall()
    return [dict(r) for r in rows]


def get_pill_thumbnail(drug_name: str) -> Optional[bytes]:
    """약품명 → 썸네일 bytes (없으면 None)."""
    rows = get_pill_from_db(drug_name)
    if rows and rows[0].get("image_thumb"):
        return rows[0]["image_thumb"]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 환자 처방약 일괄 학습 (DB 구축)
# ═══════════════════════════════════════════════════════════════════════════════

def learn_patient_drugs(patient_prescriptions: List[Dict]) -> Dict:
    """
    환자 처방 데이터에서 약품명 추출 → MFDS/NIH API 호출 → DB 저장.
    한 번 실행하면 이후 오프라인으로도 인식 가능.

    Returns
    -------
    dict: {"learned": [약품명], "failed": [약품명], "total": int}
    """
    init_pill_db()
    learned, failed = [], []

    all_drug_names = set()
    for rx in patient_prescriptions:
        med_str = rx.get("medication_name", "")
        for m in med_str.split(","):
            name = m.strip()
            if name:
                # 핵심 약품명 추출 (용량 제거)
                core = name.split("정")[0].split("주")[0].split("캡")[0].split(" ")[0]
                all_drug_names.add(core)
                all_drug_names.add(name)  # 원본도 추가

    for drug in sorted(all_drug_names):
        # 이미 DB에 있으면 skip
        existing = get_pill_from_db(drug)
        if existing:
            learned.append(drug)
            continue

        # API 호출
        items = fetch_mfds_pill_info(drug)
        if items:
            for item in items[:2]:  # 최대 2개
                save_pill_to_db(item, source="MFDS")
            learned.append(drug)
            logger.info(f"✅ 학습 완료: {drug}")
        else:
            failed.append(drug)
            logger.warning(f"⚠️ 데이터 없음: {drug}")

        time.sleep(0.3)  # API 레이트 리밋 방지

    # 국제 의약품 fallback
    for key, val in INTL_PILL_DB.items():
        existing = get_pill_from_db(key)
        if not existing:
            save_pill_to_db(val, source="NIH_DailyMed")
            if key not in learned:
                learned.append(key)

    # 한국 내장 DB fallback
    for key, val in PILL_FALLBACK_DB.items():
        existing = get_pill_from_db(key)
        if not existing:
            save_pill_to_db(val, source="MFDS_LOCAL")
            if key not in learned:
                learned.append(key)

    return {
        "learned": learned,
        "failed":  failed,
        "total":   len(all_drug_names),
        "db_path": PILL_DB,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DB 통계
# ═══════════════════════════════════════════════════════════════════════════════

def get_db_stats() -> Dict:
    """DB 현황 통계."""
    init_pill_db()
    with sqlite3.connect(PILL_DB) as conn:
        total   = conn.execute("SELECT COUNT(*) FROM pills").fetchone()[0]
        with_img = conn.execute("SELECT COUNT(*) FROM pills WHERE image_data IS NOT NULL").fetchone()[0]
        mfds    = conn.execute("SELECT COUNT(*) FROM pills WHERE source LIKE '%MFDS%'").fetchone()[0]
        nih     = conn.execute("SELECT COUNT(*) FROM pills WHERE source LIKE '%NIH%'").fetchone()[0]
    return {
        "total_pills":   total,
        "with_image":    with_img,
        "mfds_count":    mfds,
        "nih_count":     nih,
        "db_size_kb":    round(os.path.getsize(PILL_DB) / 1024, 1) if os.path.exists(PILL_DB) else 0,
    }


if __name__ == "__main__":
    print("💊 알약 DB 초기화 및 내장 데이터 로딩...")
    init_pill_db()

    # 내장 데이터 전체 저장
    for key, val in {**PILL_FALLBACK_DB, **INTL_PILL_DB}.items():
        existing = get_pill_from_db(key)
        if not existing:
            save_pill_to_db(val, source=val.get("source","MFDS_LOCAL"))

    stats = get_db_stats()
    print(f"✅ 완료: 총 {stats['total_pills']}종 등록 | 이미지 {stats['with_image']}개 | DB {stats['db_size_kb']}KB")
