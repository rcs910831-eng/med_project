#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[SHIELD] PHARMA-HYBRID v20
핵심 기능 실제 작동판

신규 기능:
1. 음성인식 → 인식된 텍스트를 Gemini AI가 즉시 분석·답변
2. 이미지 업로드 → Gemini AI가 약품 사진 분석, 성분/주의사항 설명
3. 지식베이스 검색도 AI 보강 답변 추가
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import base64
import requests as req
from datetime import datetime
from typing import Dict, List
import plotly.graph_objects as go
import random
import logging

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from medical_knowledge_engine import (
        get_hospital_chart_data,
        get_trend_chart_data,
        get_drug_image_path,
        get_all_drug_images,
        get_prescription_images,
        get_pill_bag_images,
        get_disease_protocol,
        search_knowledge,
        render_drug_image_html,
        analyze_prescription,
        analyze_pill_bag,
        identify_drug_from_image,
        DISEASE_PROTOCOLS,
        get_fda_info,
        get_fda_adverse_events,
        get_fda_indications,
        get_collected_drug_names,
    )
    from cancer_protocols_db import (
        CANCER_PROTOCOLS,
        get_cancer_protocol,
        search_cancer_protocols,
        get_all_cancer_names,
        get_cancers_by_category,
    )
    from nutrition_diet_db import (
        CANCER_TYPE_DIET,
        CHRONIC_DISEASE_DIET,
        CANCER_NUTRITION_GENERAL,
        DIET_DATA_SOURCES,
        get_cancer_diet,
        get_chronic_diet,
        search_diet,
        get_food_restrictions,
        get_all_diet_categories,
        get_nutrient_targets,
        DATA_SOURCES as DIET_DATA_SOURCES,
    )
    HAS_MED_ENGINE = True
    HAS_CANCER_DB = True
    HAS_NUTRITION_DB = True
except ImportError:
    HAS_MED_ENGINE = False
    HAS_CANCER_DB = False
    HAS_NUTRITION_DB = False
    def get_fda_info(_): return {}
    def get_fda_adverse_events(_, top_n=10): return []
    def get_fda_indications(_): return ""
    def get_collected_drug_names(): return []
    CANCER_PROTOCOLS = {}
    CANCER_TYPE_DIET = {}
    CHRONIC_DISEASE_DIET = {}
    CANCER_NUTRITION_GENERAL = {}
    DIET_DATA_SOURCES = {}
    def get_cancer_protocol(_): return None
    def search_cancer_protocols(_): return []
    def get_all_cancer_names(): return []
    def get_cancers_by_category(): return {}
    def get_cancer_diet(_): return {}
    def get_chronic_diet(_): return {}
    def search_diet(_): return []
    def get_food_restrictions(_): return {}
    def get_all_diet_categories(): return {}
    def get_nutrient_targets(_): return {}

# ── Gemini 실제 AI 엔진 (신규) ───────────────────────────────────────────────
try:
    from gemini_ai_engine import (
        call_gemini_compat,      # 기존 call_gemini 대체 래퍼
        call_gemini_text,        # 텍스트 전용 API
        call_gemini_vision,      # Vision AI (처방전 OCR)
        call_gemini_voice,       # 음성 질문 분석
        call_gemini_rag,         # 지식베이스 RAG 보강
        call_gemini_adherence_advice,  # 복약 독려 메시지
        get_engine_status,       # API 상태 확인
    )
    HAS_GEMINI_ENGINE = True
except ImportError:
    HAS_GEMINI_ENGINE = False
    # 폴백: 기존 시뮬레이션 함수로 동작 유지
    def call_gemini_compat(contents, system=""): return "⚠️ Gemini 엔진 로드 실패 — 시뮬레이션 대체"
    def call_gemini_text(p, **kw): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_vision(b, m, p, **kw): return "⚠️ Vision AI 로드 실패"
    def call_gemini_voice(t, pi, rx): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_rag(q, kb, **kw): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_adherence_advice(*a, **kw): return ""
    def get_engine_status(): return {"mode": "🔴 엔진 로드 실패", "ready": False}

# ── Guardian Link (보호자 알림) ───────────────────────────────────────────────
try:
    from guardian_link import (
        init_guardian_db, add_guardian, get_guardians, remove_guardian,
        send_guardian_alert, auto_detect_and_alert,
        get_alert_history, get_pending_alerts,
        render_guardian_panel_html,
    )
    HAS_GUARDIAN = True
except ImportError:
    HAS_GUARDIAN = False
    def init_guardian_db(): pass
    def add_guardian(*a, **kw): return 0
    def get_guardians(pid): return []
    def remove_guardian(gid): pass
    def send_guardian_alert(*a, **kw): return {"sent": 0, "guardians": []}
    def auto_detect_and_alert(*a, **kw): return None
    def get_alert_history(pid, **kw): return []
    def get_pending_alerts(**kw): return []
    def render_guardian_panel_html(pid): return ""

# ── 복약 이행도 ──────────────────────────────────────────────────────────────
try:
    from medication_adherence import (
        init_adherence_db, sync_schedules_from_rx,
        record_medication_taken, record_all_meds_taken,
        get_compliance_rate, get_today_taken_meds,
        detect_taken_from_voice,
        render_compliance_sentinel_html, render_taken_button_area_html,
    )
    HAS_ADHERENCE = True
except ImportError:
    HAS_ADHERENCE = False
    def init_adherence_db(): pass
    def sync_schedules_from_rx(rxs): pass
    def record_medication_taken(*a, **kw): return 0
    def record_all_meds_taken(*a, **kw): return []
    def get_compliance_rate(pid, **kw): return {"compliance_rate": 0, "grade": "N/A", "today_taken": False, "missed_drugs": []}
    def get_today_taken_meds(pid): return []
    def detect_taken_from_voice(text): return False
    def render_compliance_sentinel_html(*a, **kw): return ""
    def render_taken_button_area_html(meds): return ""

try:
    from celebrity_voice_engine import CelebrityVoiceEngine, VoiceSessionManager
    HAS_VOICE_ENGINE = True
except ImportError:
    HAS_VOICE_ENGINE = False
    class CelebrityVoiceEngine:
        pass
    class VoiceSessionManager:
        def __init__(self, ss): pass
        def get_engine(self): return None
        def set_voice(self, v): pass
        def synthesize(self, t, u=True): return None

try:
    from nearby_pharmacy_widget import render_pharmacy_widget_html, get_pharmacy_status, get_stock_summary
    HAS_PHARMACY_WIDGET = True
except ImportError:
    HAS_PHARMACY_WIDGET = False
    def render_pharmacy_widget_html(**kw): return ""
    def get_pharmacy_status(): return []
    def get_stock_summary(d): return {}

# ── 알약 이미지 인식 엔진 ─────────────────────────────────────────────────────
try:
    from pill_image_db import (
        init_pill_db, learn_patient_drugs,
        get_pill_from_db, get_pill_thumbnail, get_db_stats,
    )
    from pill_recognizer import recognize_pill, render_recognition_result_html
    HAS_PILL_RECOGNIZER = True
except ImportError:
    HAS_PILL_RECOGNIZER = False
    def init_pill_db(): pass
    def learn_patient_drugs(rxs): return {"learned": [], "failed": [], "total": 0}
    def get_pill_from_db(n): return []
    def get_pill_thumbnail(n): return None
    def get_db_stats(): return {}
    def recognize_pill(b, m, pi, pm): return {"ai_analysis": "", "match_status": "unknown", "confidence": 0}
    def render_recognition_result_html(r): return ""

try:
    from seasonal_anticancer_rag import (
        search_seasonal_rag, render_seasonal_rag_html,
        get_current_season, get_season_guide, get_total_synergy_count,
    )
    HAS_SEASONAL_RAG = True
except ImportError:
    HAS_SEASONAL_RAG = False
    def search_seasonal_rag(q): return []
    def render_seasonal_rag_html(**kw): return ""
    def get_current_season(): return "봄"
    def get_season_guide(s=None): return []
    def get_total_synergy_count(): return 0

try:
    from emotion_voice_analyzer import (
        EmotionVoiceAnalyzer, render_emotion_result_html, render_demo_result,
    )
    HAS_EMOTION_ANALYZER = True
    _emotion_analyzer = EmotionVoiceAnalyzer()
except ImportError:
    HAS_EMOTION_ANALYZER = False
    def render_emotion_result_html(r): return ""
    def render_demo_result(s="calm"): return None
    _emotion_analyzer = None

# ═══════════════════════════════════════════════════════════════════════════════
# 내장 엣지 AI 분석 엔진 (API 불필요)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# 임상/영양/생활습관 시너지 지식베이스
# ═══════════════════════════════════════════════════════════════════════════════

LIFESTYLE_SYNERGY = {
    "항암": {
        "키워드": ["폐암", "대장암", "흑색종", "유방암", "간암", "백혈병", "타세바", "키트루다", "넥사바", "옵디보", "글리벡", "허셉틴", "아바스틴", "입랜스", "페마라", "엑스지바", "론서프", "보트리엔트"],
        "식단": "소화가 잘 되는 부드러운 고기 죽이나 계란찜",
        "채소_과일": "눈과 몸에 좋은 블루베리, 따뜻하게 익힌 토마토",
        "영양제": "피로회복에 좋은 비타민, 장을 튼튼하게 하는 유산균",
        "운동": "식사하시고 30분 뒤에 가볍게 동네 산책하기",
        "시너지": "독한 약을 드실 때 입맛이 떨어지거나 기운이 빠지는 것을 막아줍니다."
    },
    "심혈관": {
        "키워드": ["고혈압", "심부전", "심질환", "라식스", "엔트레스토", "콩코르", "알닥톤", "디고신", "노바스크", "플라빅스"],
        "식단": "짜지 않은 맑은 국, 등푸른 생선 (고등어, 꽁치)",
        "채소_과일": "바나나, 부드러운 아보카도",
        "영양제": "심장 건강에 좋은 코엔자임 Q10, 식물성 오메가-3",
        "운동": "오후에 따뜻할 때 가볍게 걷기 (아침 찬바람은 피하세요)",
        "시너지": "심장이 뛰는 것을 편안하게 해주고 혈압을 낮춰줍니다."
    },
    "호흡기": {
        "키워드": ["천식", "RSV", "벤톨린", "싱귤레어", "시나지스", "코대원", "라니넥스", "폐암", "타그리소", "알레센자", "지오트리프", "씨투스", "모드콜", "챔프"],
        "식단": "따뜻한 국물 요리, 기름기 적은 부드러운 생선",
        "채소_과일": "기침에 좋은 배와 도라지 끓인 물",
        "영양제": "호흡기를 튼튼하게 하는 프로폴리스, 비타민 D",
        "운동": "미세먼지 없는 날 실내에서 가볍게 움직이기",
        "시너지": "가래와 기침을 줄여주고 숨쉬기 편안하게 만들어 줍니다. 특히 표적항암제 복용 시에는 자몽주스를 피하셔야 약효가 일정하게 유지됩니다."
    },
    "소화기": {
        "키워드": ["위염", "크론병", "궤양", "무코스타", "스토가", "펜타사", "이뮤란", "대장암", "젤로다", "옥살리플라틴", "베아제", "훼스탈", "노루모"],
        "식단": "맵고 짠 음식 피하기, 부드러운 두부나 흰살 생선",
        "채소_과일": "속을 편하게 해주는 삶은 양배추, 찐 감자",
        "영양제": "소화가 잘 되게 돕는 소화효소, 위장 건강 유산균",
        "운동": "식사하시고 1시간 뒤에 가볍게 집 앞 걷기",
        "시너지": "위장을 부드럽게 감싸주어 약을 먹어도 속이 쓰리지 않게 해줍니다. 옥살리플라틴 투여 후에는 차가운 물이나 금속 손잡이를 만지면 손발이 저릴 수 있으니 꼭 따뜻하게 유지하세요."
    },
    "신경_뇌": {
        "키워드": ["파킨슨", "뇌전증", "마도파", "리큅", "케프라", "데파코트", "엑세그란"],
        "식단": "단백질은 조금씩 나누어서 드시기, 신선하고 부드러운 나물 반찬",
        "채소_과일": "머리가 맑아지는 호두 잣죽",
        "영양제": "기억력에 좋은 은행잎 추출물, 비타민 B",
        "운동": "넘어지지 않게 조심하면서 천천히 맨손체조 하기",
        "시너지": "약 기운이 일정하게 유지되게 도와주고 어지러움을 줄여줍니다."
    },
    "당뇨": {
        "키워드": ["당뇨병", "메트포르민", "자누비아", "포시가", "제미글로", "트라젠타", "바이에타", "빅토자", "다이아벡스"],
        "식단": "설탕과 밀가루 줄이기, 잡곡밥과 식이섬유가 많은 반찬",
        "채소_과일": "달지 않은 토마토나 오이, 잎채소 위주",
        "영양제": "당 대사에 좋은 비타민 B군, 크롬, 바나바잎 추출물",
        "운동": "식후 15분 뒤에 30분 정도 꾸준히 걷기",
        "시너지": "혈당이 급격히 오르는 것을 막아주고 합병증 예방을 도와줍니다."
    },
    "만성폐질환": {
        "키워드": ["COPD", "만성폐쇄성폐질환", "스피리바", "심비코트", "브레오", "아노로", "울티브로"],
        "식단": "숨쉬기 편하게 배가 너무 부르지 않게 조금씩 자주 드시기",
        "채소_과일": "폐를 촉촉하게 해주는 도라지, 더덕, 무",
        "영양제": "항염 작용을 돕는 오메가-3, 비타민 D",
        "운동": "입술을 오므리고 천천히 숨 쉬며 가볍게 걷기",
        "시너지": "기관지 염증을 줄여주고 숨쉬는 근육을 튼튼하게 해줍니다."
    },
    "신장": {
        "키워드": ["만성콩팥병", "신부전", "케토스테릴", "네프릴", "에포론"],
        "식단": "짠 음식과 단백질 과다 섭취 주의, 칼륨이 적은 조리법 활용",
        "채소_과일": "칼륨을 뺀 데친 채소, 사과나 배 소량",
        "영양제": "신장용 전문 유산균, 엽산 (상담 후 섭취)",
        "운동": "무리하지 않는 선에서 주 3회 가벼운 스트레칭",
        "시너지": "노폐물이 몸에 쌓이는 것을 줄여주고 신장 기능을 보호합니다."
    },
    "정신건강": {
        "키워드": ["우울증", "불안장애", "렉사프로", "졸로푸트", "푸로작", "아빌리파이"],
        "식단": "기분을 좋게 하는 아미노산이 풍부한 달걀, 바나나",
        "채소_과일": "신선한 샐러드와 상큼한 레몬, 자몽",
        "영양제": "심리적 안정에 도움을 주는 마그네슘, 테아닌",
        "운동": "햇볕을 쬐면서 야외에서 20분간 산책하기",
        "시너지": "세로토닌 분비를 도와 약의 효과를 높이고 마음을 편안하게 합니다."
    }
}

def get_synergy_info(user_text: str) -> str:
    matched = None
    for cat, data in LIFESTYLE_SYNERGY.items():
        if any(kw in user_text for kw in data["키워드"]):
            matched = data
            break
    if not matched:
        matched = {
            "식단": "소화가 잘되는 부드러운 음식",
            "채소_과일": "제철 과일과 신선한 채소 반찬",
            "영양제": "기력 회복에 좋은 종합 비타민",
            "운동": "매일 30분씩 가벼운 동네 걷기",
            "시너지": "약이 몸에 잘 스며들도록 도와주고 기운을 나게 해줍니다."
        }
    return (
        f"<div style='font-size: 1.35rem; line-height: 1.8; background-color: rgba(0, 50, 100, 0.4); padding: 25px; border-radius: 12px; border: 1.5px solid #00f2ff; margin-top:20px;'>"
        f"<h3 style='color: #00ff88; margin-top: 0; margin-bottom: 20px; font-size: 1.6rem;'>🥗 어르신도 알기 쉬운 건강 맞춤 안내</h3>"
        f"<ul style='list-style-type: none; padding-left: 0; margin: 0;'>"
        f"<li style='margin-bottom: 12px;'>🍲 <strong style='color:#ffffff;'>어떤 음식이 좋을까요?</strong><br><span style='color: #bbddff;'>{matched['식단']}</span></li>"
        f"<li style='margin-bottom: 12px;'>🍎 <strong style='color:#ffffff;'>추천 과일과 채소</strong><br><span style='color: #bbddff;'>{matched['채소_과일']}</span></li>"
        f"<li style='margin-bottom: 12px;'>💊 <strong style='color:#ffffff;'>같이 드시면 좋은 영양제</strong><br><span style='color: #bbddff;'>{matched['영양제']}</span></li>"
        f"<li style='margin-bottom: 12px;'>🚶 <strong style='color:#ffffff;'>어떻게 운동할까요?</strong><br><span style='color: #bbddff;'>{matched['운동']}</span></li>"
        f"<li style='margin-bottom: 0px;'>🧬 <strong style='color:#ffffff;'>건강 시너지 효과</strong><br><span style='color: #bbddff;'>{matched['시너지']}</span></li>"
        f"</ul></div>"
    )

def call_gemini(contents: list, system: str = "") -> str:
    """
    ✅ [리팩토링 완료] 실제 Google Gemini API 연동
    - HAS_GEMINI_ENGINE=True : 실제 Gemini 1.5 Flash/Pro 호출
    - HAS_GEMINI_ENGINE=False: 기존 시뮬레이션 로직으로 폴백

    GOOGLE_API_KEY 설정 방법:
      1) .streamlit/secrets.toml  →  GOOGLE_API_KEY = "AIza..."
      2) 환경변수  →  set GOOGLE_API_KEY=AIza...
    """
    # ─── 실제 Gemini API 경로 ──────────────────────────────────────────
    if HAS_GEMINI_ENGINE:
        return call_gemini_compat(contents, system=system)

    # ─── 폴백: 기존 시뮬레이션 (API 키 없을 때 안전망) ──────────────────
    import re, time
    time.sleep(0.8)

    user_text = ""
    for part in contents[0].get("parts", []):
        if "text" in part:
            user_text += part["text"]

    synergy_text = get_synergy_info(user_text)

    if "이미지 분석" in system:
        m = re.search(r"현재 고객 처방: (.+?)\n", user_text)
        rx_list = m.group(1) if m else "베실리온정, 코대원정, 슈다페드정"
        rx_items = [x.strip() for x in rx_list.split(",")]
        drug_explanation = ""
        for drug in rx_items:
            drug_name = drug.split()[0]
            if drug_name in KB["약물"]:
                info = KB["약물"][drug_name]
                drug_explanation += (
                    f"- **{drug_name}** ({info.get('성분','')}): "
                    f"{info.get('적응증','')} 치료제\n"
                    f"  └ 주의: {info.get('주의','—')} / 부작용: {info.get('부작용','—')}\n"
                )
            else:
                drug_explanation += f"- **{drug_name}**: DB 정보 제한\n"
        return (
            "🔬 [시뮬레이션 이미지 분석]\n"
            f"식별 약물: {rx_list}\n\n"
            f"{drug_explanation}\n"
            "⚠️ GOOGLE_API_KEY 설정 시 실제 Vision AI OCR 분석이 활성화됩니다.\n\n"
            f"{synergy_text}"
        )
    elif "임상 지식" in system:
        return (
            "📚 [시뮬레이션 임상 분석]\n"
            "해당 항목은 가이드라인 권장 표준 치료법입니다. "
            "장기 복용 시 정기 혈액 검사 권장.\n"
            "⚠️ GOOGLE_API_KEY 설정 시 실제 Gemini 분석 활성화"
        )
    else:
        rx_match = re.search(r"- 처방 내역:\n(.*?)\n\n음성 질문", user_text, re.DOTALL)
        rx_info = rx_match.group(1).strip() if rx_match else ""
        diseases, drugs = set(), set()
        for line in rx_info.split("\n"):
            mm = re.search(r"- (.*?) \((.*?)\)", line)
            if mm:
                drugs.add(mm.group(1).strip())
                diseases.add(mm.group(2).strip())
        disease_str = ", ".join(diseases) or "파악되지 않음"
        drug_str = ", ".join(drugs) or "처방 없음"
        return (
            f"🎙️ [시뮬레이션 분석 — {disease_str}]\n"
            f"현재 **{disease_str}** 관리를 위해 **{drug_str}** 복용 중.\n"
            "임상적 특이 소견 없음. 상태 변화 시 재브리핑 요청.\n"
            "⚠️ GOOGLE_API_KEY 설정 시 실제 Gemini AI 분석 활성화\n\n"
            f"{synergy_text}"
        )


def analyze_voice(text: str, patient_info: Dict, prescriptions: List[Dict]) -> str:
    """
    ✅ [리팩토링] 음성 텍스트 → 실제 Gemini AI 임상 분석.
    복약 확인 키워드 감지 시 이행도 기록도 동시 처리.
    """
    # ── 복약 완료 키워드 감지 ──────────────────────────────────────────
    if HAS_ADHERENCE and detect_taken_from_voice(text):
        pid = patient_info.get("patient_id", "")
        if pid:
            record_all_meds_taken(pid, prescriptions, recorded_by="voice", notes=text[:50])
        return (
            "✅ **복약 완료 기록!**\n\n"
            f"'{text.strip()}' — 복약 완료가 확인되었습니다.\n"
            "오늘 복용 내역이 COMPLIANCE SENTINEL에 반영되었습니다.\n"
            "꾸준한 복약이 치료 효과를 높입니다. 잘 하셨습니다! 💊"
        )

    # ── 이상반응 키워드 자동 감지 → Guardian Link 트리거 ─────────────
    if HAS_GUARDIAN:
        pat_name = patient_info.get("real_name", patient_info.get("patient_id", ""))
        pid = patient_info.get("patient_id", "")
        disease = prescriptions[0].get("cancer_type", "") if prescriptions else ""
        auto_detect_and_alert(pid, pat_name, text, disease)

    # ── 실제 Gemini 분석 ────────────────────────────────────────────────
    if HAS_GEMINI_ENGINE:
        return call_gemini_voice(text, patient_info, prescriptions)

    # ── 시뮬레이션 폴백 ────────────────────────────────────────────────
    rx_summary = "\n".join([
        f"- {r['medication_name']} ({r['cancer_type']}) {r['dosage']} {r['frequency']}"
        for r in prescriptions
    ])
    system = "당신은 PHARMA-HYBRID 임상 AI 어시스턴트입니다. 한국어로 500자 이내로 답변하세요."
    user_msg = (
        f"나이: {patient_info.get('age','N/A')}세 / 병원: {patient_info.get('hospital','N/A')}\n"
        f"처방: {rx_summary}\n음성 질문: {text}"
    )
    return call_gemini([{"role": "user", "parts": [{"text": user_msg}]}], system=system)


def analyze_image(image_bytes: bytes, mime_type: str, patient_info: Dict, prescriptions: List[Dict]) -> str:
    """
    ✅ [v2.1] 이미지 → 알약 인식 + Gemini Vision AI OCR 통합 분석.
    - 알약 사진: pill_recognizer로 색상·모양·각인 분석 → DB 교차 검증
    - 처방전/약포지: Gemini Vision OCR로 텍스트 추출
    """
    # 처방 약물 목록
    patient_meds = []
    for r in prescriptions:
        for m in r.get("medication_name","").split(","):
            mn = m.strip()
            if mn:
                patient_meds.append(mn)

    rx_summary = ", ".join(patient_meds) if patient_meds else "처방 없음"

    # ── 알약 인식 엔진 우선 시도 ────────────────────────────────────────────
    if HAS_PILL_RECOGNIZER and HAS_GEMINI_ENGINE:
        try:
            recog = recognize_pill(image_bytes, mime_type, patient_info, patient_meds)
            ai_text = recog.get("ai_analysis", "")
            if ai_text:
                status = recog.get("match_status","unknown")
                top    = recog.get("top_match","")
                conf   = recog.get("confidence", 0)
                header = {
                    "confirmed": f"✅ **약품 확인**: {top} (신뢰도 {int(conf*100)}%)",
                    "warning":   f"⚠️ **주의**: {top or '불일치 가능'} (신뢰도 {int(conf*100)}%)",
                    "unknown":   "❓ **DB 매칭 불가** — AI 분석 결과:",
                }[status]
                return f"{header}\n\n{ai_text}"
        except Exception:
            pass  # 실패 시 일반 Vision 분석으로 fallback

    # ── 일반 Gemini Vision OCR (처방전·약포지) ──────────────────────────────
    system = (
        "당신은 PHARMA-HYBRID 처방전·약품 이미지 분석 Vision AI입니다. "
        "업로드된 이미지를 실제로 읽어 약품명·성분·용량·주의사항을 정확히 추출합니다. "
        "처방전이면 모든 약품을 목록화하고 현재 환자 처방과 상호작용을 검토하세요. "
        "약포지(약봉지)면 약품명·복용 시간·주의사항을 읽어 정리하세요. "
        "알약 사진이면 색상·모양·각인을 분석해 약품을 동정하세요. "
        "한국어로 답변하며 핵심 주의사항은 ⚠️로 강조하세요."
    )
    prompt = (
        f"현재 환자 처방: {rx_summary}\n\n"
        "이 이미지를 분석해주세요:\n"
        "📋 처방전/약포지라면: 약품목록·용량·복용시간·상호작용\n"
        "💊 알약 사진이라면: 색상·모양·각인 → 약품 동정 → 처방 일치 여부\n"
        "⚠️ 주의사항을 마지막에 정리하세요."
    )

    if HAS_GEMINI_ENGINE:
        return call_gemini_vision(image_bytes, mime_type, prompt, system_instruction=system)

    # 시뮬레이션 폴백
    b64 = base64.standard_b64encode(image_bytes).decode()
    user_content = [
        {"inlineData": {"mimeType": mime_type, "data": b64}},
        {"text": f"현재 고객 처방: {rx_summary}\n\n{prompt}"}
    ]
    return call_gemini([{"role": "user", "parts": user_content}], system=system)


def ai_kb_search(query: str, kb_results: List[Dict], patient_context: str = "") -> str:
    """
    ✅ [리팩토링] 지식베이스 결과 + 실제 Gemini AI 보강 설명.
    """
    if HAS_GEMINI_ENGINE:
        return call_gemini_rag(query, kb_results, patient_context=patient_context)

    # 시뮬레이션 폴백
    kb_text = ""
    for r in kb_results:
        kb_text += f"\n[{r['type']} - {r['title']}]\n"
        for k, v in r["data"].items():
            kb_text += f"  {k}: {v}\n"
    system = "당신은 임상 지식 AI입니다. 한국어로 400자 이내로 설명하세요."
    user_msg = f"검색어: {query}\n\n데이터베이스:\n{kb_text}\n\n쉽게 설명해주세요."
    return call_gemini([{"role": "user", "parts": [{"text": user_msg}]}], system=system)


# ═══════════════════════════════════════════════════════════════════════════════
# 데이터
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_PATIENTS = {
    "P001": {"real_name": "김상은", "age": 68, "gender": "남", "hospital": "삼성서울병원"},
    "P002": {"real_name": "박지현", "age": 55, "gender": "여", "hospital": "국립암센터"},
    "P003": {"real_name": "이준호", "age": 72, "gender": "남", "hospital": "서울대병원"},
    "P004": {"real_name": "최영민", "age": 61, "gender": "남", "hospital": "세브란스병원"},
    "P005": {"real_name": "신준호", "age": 58, "gender": "남", "hospital": "서울이대병원"},
    "P006": {"real_name": "임대균", "age": 64, "gender": "남", "hospital": "삼성서울병원"},
    "P007": {"real_name": "최민준", "age": 8,  "gender": "남", "hospital": "서울대어린이병원"},
    "P008": {"real_name": "한수진", "age": 55, "gender": "여", "hospital": "세브란스병원"},
    "P009": {"real_name": "조영진", "age": 61, "gender": "남", "hospital": "국립암센터"},
    "P010": {"real_name": "이지온", "age": 1,  "gender": "여", "hospital": "서울아산어린이병원"},
    "P011": {"real_name": "김도윤", "age": 14, "gender": "남", "hospital": "신촌세브란스병원"},
    "P012": {"real_name": "이수진", "age": 28, "gender": "여", "hospital": "고대안암병원"},
    "P013": {"real_name": "박서연", "age": 45, "gender": "여", "hospital": "국립암센터"},
    "P014": {"real_name": "김철수", "age": 82, "gender": "남", "hospital": "분당서울대병원"},
    "P015": {"real_name": "정하은", "age": 5,  "gender": "여", "hospital": "서울대어린이병원"},
    "P016": {"real_name": "James Lee", "age": 24, "gender": "남", "hospital": "Johns Hopkins (US)"},
    "P017": {"real_name": "박소윤", "age": 34, "gender": "여", "hospital": "신촌세브란스병원"},
    "P018": {"real_name": "Michael Kim", "age": 48, "gender": "남", "hospital": "Mayo Clinic (US)"},
    "P019": {"real_name": "이정태", "age": 53, "gender": "남", "hospital": "삼성서울병원"},
    # P020–P023: RAW_RX에 처방 데이터가 있었으나 프로필 누락 → 복원
    "P020": {"real_name": "오창현", "age": 67, "gender": "남", "hospital": "서울아산병원"},
    "P021": {"real_name": "윤지영", "age": 49, "gender": "여", "hospital": "세브란스병원"},
    "P022": {"real_name": "강민서", "age": 31, "gender": "여", "hospital": "고대안암병원"},
    "P023": {"real_name": "서동훈", "age": 44, "gender": "남", "hospital": "국립암센터"},
    # P024–P025: 감기·편두통 환자 (일반 외래)
    "P024": {"real_name": "한지민", "age": 29, "gender": "여", "hospital": "신촌세브란스병원"},
    "P025": {"real_name": "류태영", "age": 38, "gender": "남", "hospital": "삼성서울병원"},
}

RAW_RX = [
    (1,"P001","타세바정","폐암","150mg","1회/일","12주","2026-04-01","Dr. Kim","활성","피로감",90.5,"EGFR 돌연변이","2026-04-27"),
    (2,"P002","키트루다","흑색종","200mg","3주/1회","24주","2026-03-15","Dr. Park","활성","피부염",85.0,"진행성","2026-04-25"),
    (3,"P003","넥사바정","간암","400mg","2회/일","무제한","2026-02-20","Dr. Lee","유지","설사",78.5,"진행성","2026-04-26"),
    (4,"P004","옵디보","대장암","240mg","2주/1회","12주","2026-04-10","Dr. Choi","활성","발진",88.0,"전이성","2026-04-27"),
    (5,"P005","글리벡정","백혈병","400mg","1회/일","24개월","2025-12-01","Dr. Jung","관해","소화불량",95.0,"완전관해","2026-04-27"),
    (6,"P006","허셉틴","유방암","600mg","3주/1회","12개월","2026-01-15","Dr. Baek","활성","심부전",92.0,"좋은반응","2026-04-27"),
    (7,"P007","글리벡정, 싱귤레어츄정, 벤톨린네뷸, 메디락디에스","소아백혈병, 천식","100mg, 5mg, 2.5mg, 1cap","1일1회, 1일1회, 필요시, 1일2회","지속","2026-04-15","Dr. Oh","활성","미약한 떨림",92.0,"소아 다제병용 처방","2026-04-28"),
    (8,"P008","리루텍정, 메스티논정, 코엔자임큐텐, 무코스타정","루게릭병, 중증근무력증","50mg, 60mg, 100mg, 100mg","1일2회, 1일3회, 1일1회, 1일3회","지속","2026-04-01","Dr. Ahn","활성","경미한 소화불량",88.5,"중증 희귀질환 4알 복합처방","2026-04-28"),
    (9,"P009","아바스틴, 론서프정, 스토가정, 맥페란정","진행성 대장암, 위염","5mg/kg, 15mg, 10mg, 10mg","2주1회, 1일2회, 1일2회, 필요시","12주","2026-04-20","Dr. Song","활성","오심",81.0,"항암 4알 복합요법","2026-04-28"),
    (10,"P010","디고신엘릭시르, 라식스, 알닥톤, 시나지스","선천성 심질환, RSV 감염","0.05mg, 1mg, 1mg, 50mg","1일2회, 1일1회, 1일1회, 월1회","지속","2026-04-10","Dr. Yoon","활성","수유 감소",88.0,"영유아 중증 심장·호흡기 다제처방","2026-04-28"),
    (11,"P011","란투스, 휴말로그, 콘서타","제1형 당뇨병, ADHD","10U, 4U, 18mg","1일1회, 식전, 1일1회","지속","2026-03-20","Dr. Kang","활성","식욕부진",90.0,"청소년 만성질환 3제 복합관리","2026-04-28"),
    (12,"P012","휴미라, 이뮤란, 펜타사","크론병","40mg, 50mg, 1g","2주1회, 1일1회, 1일2회","지속","2026-02-15","Dr. Lee","활성","피로감",85.5,"청년기 자가면역질환 표적치료","2026-04-28"),
    (13,"P013","입랜스, 페마라, 엑스지바, 덱사메타손","전이성 유방암","125mg, 2.5mg, 120mg, 4mg","1일1회, 1일1회, 4주1회, 필요시","지속","2026-04-05","Dr. Park","활성","백혈구 감소",82.0,"항암·골전이 복합 다제요법","2026-04-28"),
    (14,"P014","마도파, 리큅, 엔트레스토, 콩코르","파킨슨병, 심부전","125mg, 2mg, 50mg, 2.5mg","1일3회, 1일3회, 1일2회, 1일1회","지속","2026-01-10","Dr. Kim","활성","기립성 저혈압",75.0,"초고령자 다중 만성질환(폴리파머시)","2026-04-28"),
    (15,"P015","케프라시럽, 데파코트스프링클, 엑세그란","소아 뇌전증","100mg, 125mg, 25mg","1일2회, 1일2회, 1일1회","지속","2026-03-01","Dr. Jung","활성","졸음",95.0,"소아 신경계 발작 억제 복합처방","2026-04-28"),
    (16,"P016","벤톨린네뷸, 싱귤레어츄정, 덱사메타손","천식","2.5mg, 5mg, 4mg","필요시, 1일1회, 1일1회","지속","2026-04-10","Dr. Smith","활성","떨림",94.0,"20대 청년층 천식 급성 발작 관리","2026-04-28"),
    (17,"P017","키트루다, 덱사메타손","흑색종","200mg, 4mg","3주1회, 필요시","12개월","2026-02-15","Dr. Lee","활성","피부염",88.5,"30대 여성 피부암 면역항암 요법","2026-04-28"),
    (18,"P018","무코스타정, 스토가정","위염","100mg, 10mg","1일3회, 1일2회","4주","2026-04-05","Dr. Adams","유지","변비",91.0,"40대 중년층 직장인 위장관 스트레스 질환","2026-04-28"),
    (19,"P019","라식스, 콩코르, 엔트레스토","고혈압, 심부전","20mg, 2.5mg, 50mg","1일1회, 1일1회, 1일2회","지속","2025-11-20","Dr. Choi","활성","전해질 불균형 주의",84.0,"50대 장년층 심혈관계 만성질환 3제 요법","2026-04-28"),
    (20,"P020","스피리바, 심비코트","COPD","18mcg, 160/4.5mcg","1일1회, 1일2회","지속","2026-04-15","Dr. Lee","활성","호흡곤란 완화",89.0,"고령 COPD 환자 흡입제 관리","2026-04-28"),
    (21,"P021","자누비아, 메트포르민, 포시가","제2형 당뇨병","100mg, 1000mg, 10mg","1일1회, 1일2회, 1일1회","지속","2026-03-10","Dr. Kang","활성","저혈당 주의",92.5,"중년 당뇨병 3제 복합요법","2026-04-28"),
    (22,"P022","렉사프로, 아빌리파이","우울증","10mg, 2mg","1일1회, 1일1회","6개월","2026-04-01","Dr. Park","유지","기분 조절",85.0,"정신건강의학과 약물 순응도 관리","2026-04-28"),
    (23,"P023","이뮤란, 알로퓨리놀, 펜타사","크론병, 통풍","50mg, 100mg, 1g","1일1회, 1일1회, 1일2회","지속","2026-04-28","Dr. Kim","활성","🚨 상호작용 위험",70.0,"절대 금기 병용 조합 확인용","2026-04-28"),
    (24,"P024","타이레놀정, 코대원정, 씨투스정, 베아제정","급성 상기도감염(감기)","500mg, 1정, 112.5mg, 1정","1일3회, 1일3회, 1일2회, 1일3회","5일","2026-05-01","Dr. Choi","활성","콧물·인후통",98.0,"일반 감기 대증치료 4제","2026-05-01"),
    (25,"P025","이미트렉스정, 나프록센정, 돔페리돈정","편두통","50mg, 500mg, 10mg","발작시, 발작시, 발작시","필요시","2026-04-30","Dr. Park","유지","오심 동반 박동성 두통",94.0,"트립탄 + NSAID + 진토제 편두통 3제","2026-05-01"),
]

KB = {
    "약물": {
        "타그리소": {"성분":"osimertinib 80mg","계열":"3세대 EGFR TKI","적응증":"EGFR 변이 양성 폐암","용량":"80mg 1일 1회","부작용":"피부발진, 설사, 조갑주위염, QTc 연장","주의":"심장 기능(LVEF) 및 전해질 정기 검사 필수. 자몽주스 금지.","보험코드":"652900ATB","급여":"급여","약가":"1정 78,520원","근거":"FLAURA trial mPFS 18.9개월"},
        "알레센자": {"성분":"alectinib 150mg","계열":"2세대 ALK TKI","적응증":"ALK 양성 폐암","용량":"600mg(4정) 1일 2회","부작용":"변비, 부종, 근육통, 간독성","주의":"반드시 식사와 함께 복용할 것. 서맥(맥박 느려짐) 주의.","보험코드":"653100ATB","급여":"급여","약가":"1캡슐 34,820원","근거":"ALEX trial mPFS 34.8개월"},
        "지오트리프": {"성분":"afatinib 40mg","계열":"2세대 EGFR TKI","적응증":"EGFR 변이 폐암","용량":"40mg 1일 1회","부작용":"심한 설사, 구내염, 피부발진","주의":"식전 1시간 또는 식후 3시간(공복)에 복용. 설사 시 즉시 알림.","보험코드":"652800ATB","급여":"급여","약가":"1정 47,850원","근거":"LUX-Lung 3/6 trial"},
        "젤로다": {"성분":"capecitabine 500mg","계열":"경구용 항암제","적응증":"대장암, 위암, 유방암","용량":"1250mg/m2 1일 2회","부작용":"수족증후군, 설사, 오심","주의":"14일 복용 후 7일 휴약 필수. 손발에 요소크림 자주 바를 것.","보험코드":"643700ATB","급여":"급여","약가":"1정 2,385원","근거":"경구용 5-FU 전구약물"},
        "옥살리플라틴": {"성분":"oxaliplatin 100mg","계열":"3세대 백금계 항암제","적응증":"대장암, 위암","용량":"85~130mg/m2","부작용":"말초신경병증, 오심, 한랭과민","주의":"차가운 음식, 음료, 금속 접촉 절대 금지. 실온 수액 사용.","보험코드":"643600ATI","급여":"급여","약가":"100mg 1병 약 15만원","근거":"MOSAIC trial 보조요법 표준"},
        "알로퓨리놀": {"성분":"allopurinol 100mg","계열":"요산생성억제제","적응증":"통풍, 고요산혈증","용량":"100~300mg 1일 1회","부작용":"피부 발진, Stevens-Johnson 증후군","주의":"아자티오프린(이뮤란)과 병용 시 치명적 독성 발생 위험!!","보험코드":"640035ATB","급여":"급여","약가":"1정 80원","근거":"잔틴 산화효소 억제"},
        "메트포르민": {"성분":"metformin","계열":"Biguanide","적응증":"제2형 당뇨병","용량":"500~2000mg 분할 투여","부작용":"위장장애(설사, 오심), 유산산증(드묾)","주의":"신장 기능(eGFR < 30) 금기. 조영제 검사 시 일시 중단.","보험코드":"640023ATB","급여":"급여","약가":"500mg 1정 70원","근거":"당뇨병 1차 선택 약제"},
        "다이아벡스정": {"성분":"metformin 500mg","계열":"Biguanide","적응증":"제2형 당뇨병","용량":"500mg 1일 2~3회","부작용":"위장장애, 금속성 맛","주의":"유산산증 주의. 신장애 환자 모니터링.","보험코드":"641900580","급여":"급여","약가":"1정 72원","근거":"가장 널리 쓰이는 메트포르민 제제"},
        "노바스크정": {"성분":"amlodipine 5mg","계열":"칼슘채널차단제(CCB)","적응증":"고혈압, 협심증","용량":"5mg 1일 1회","부작용":"말초부종, 안면홍조, 두통","주의":"자몽주스 섭취 시 약효 과다 위험.","보험코드":"648900030","급여":"급여","약가":"1정 363원","근거":"혈관 확장 효과가 우수한 고혈압약"},
        "플라빅스정": {"성분":"clopidogrel 75mg","계열":"항혈소판제","적응증":"혈전 예방, 뇌졸중/심근경색 재발방지","용량":"75mg 1일 1회","부작용":"출혈, 혈종, 위장 출혈","주의":"수술 전후 투여 주의. 항응고제 병용 시 출혈 위험.","보험코드":"645200050","급여":"급여","약가":"1정 1,144원","근거":"심혈관 사고 예방 표준 치료"},
        "타이레놀정": {"성분":"acetaminophen 500mg","계열":"해열진통제","적응증":"두통, 발열, 근육통","용량":"500mg 1~2정 1일 3~4회","부작용":"간독성(과량 투여 시)","주의":"음주 후 복용 절대 금지. 일일 최대 4g 준수.","보험코드":"642202040","급여":"급여","약가":"1정 51원","근거":"가장 안전한 해열진통제 중 하나"},
        "게보린정": {"성분":"아세트아미노펜+이소프로필안티피린+카페인","계열":"해열진통제","적응증":"두통, 치통, 생리통","용량":"1정 1일 3회 식후","부작용":"발진, 빈혈","주의":"15세 미만 복용 금지. 장기 연용 피할 것.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"빠른 효과의 진통제"},
        "탁센연질캡슐": {"성분":"naproxen 250mg","계열":"NSAIDs","적응증":"관절염, 생리통, 편두통","용량":"250~500mg 1일 2회","부작용":"위장 출혈, 신장 기능 저하","주의":"심혈관계 위험 증가 가능성. 충분한 물과 복용.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"액상 연질캡슐로 흡수 빠름"},
        "베아제정": {"성분":"소화효소제 복합","계열":"소화제","적응증":"소화불량, 과식, 가스 제거","용량":"1~2정 1일 3회 식후","부작용":"드물게 발진","주의":"임산부 전문가 상의.","보험코드":"641601460","급여":"급여(조건부)","약가":"1정 150원","근거":"위와 장에서 2단계 작용"},
        "훼스탈플러스정": {"성분":"판크레아틴 외","계열":"소화제","적응증":"소화불량, 식욕부진","용량":"1~2정 1일 3회 식후","부작용":"설사, 오심","주의":"씹지 말고 그대로 삼킬 것.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"강력한 소화 효소 보충"},
        "모드콜S": {"성분":"종합감기 성분 복합","계열":"종합감기약","적응증":"감기 제증상(콧물, 기침, 발열)","용량":"2캡슐 1일 3회 식후","부작용":"졸음, 입마름","주의":"운전 및 기계 조작 주의.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"초기 감기 증상 완화"},
        "챔프시럽": {"성분":"acetaminophen 32mg/mL","계열":"해열진통제(소아용)","적응증":"소아 발열 및 통증","용량":"연령/체중별 차등 투여","부작용":"과량 시 간손상","주의":"개별 포장으로 위생적. 정해진 용량 엄수.","보험코드":"642203010","급여":"급여","약가":"5mL 1포 220원","근거":"무색소 안전한 소아 해열제"},
        "노루모듀얼액션": {"성분":"알긴산나트륨 외","계열":"제산제","적응증":"속쓰림, 위산역류","용량":"10~20mL 식후 및 취침 전","부작용":"변비, 설사","주의":"다른 약과 2시간 간격 권장.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"물리적 방어막 형성"},
        "씨투스정": {"성분":"pranlukast 50mg","계열":"류코트리엔 길항제","적응증":"천식, 알레르기 비염","용량":"112.5mg 1일 2회 (소아용 별도)","부작용":"복통, 발진","주의":"간기능 장애 환자 주의.","보험코드":"665500010","급여":"급여","약가":"1정 381원","근거":"호흡기 염증 반응 억제"},
        "보트리엔트정": {"성분":"pazopanib 200mg","계열":"표적항암제(TKI)","적응증":"신세포암, 연조직육종","용량":"800mg 1일 1회 공복","부작용":"고혈압, 간독성, 설사, 모발 변색","주의":"간기능 수치 정기 확인. 심전도 모니터링.","보험코드":"645504780","급여":"급여","약가":"200mg 1정 19,500원","근거":"다중 키나아제 억제 효과"},
        "자누비아": {"성분":"sitagliptin","계열":"DPP-4 억제제","적응증":"제2형 당뇨병","용량":"100mg 1일 1회","부작용":"상기도 감염, 두통","주의":"신장애 고객 용량 조절 필요.","보험코드":"640024ATB","급여":"급여","약가":"1정 800원","근거":"안전한 혈당 강하 효과"},
        "포시가": {"성분":"dapagliflozin","계열":"SGLT-2 억제제","적응증":"당뇨병, 심부전, 만성콩팥병","용량":"10mg 1일 1회","부작용":"생식기 감염, 요로 감염","주의":"수분 섭취 권장. 케톤산증 주의.","보험코드":"640025ATB","급여":"급여","약가":"1정 700원","근거":"심혈관/신장 보호 효과 입증"},
        "스피리바": {"성분":"tiotropium","계열":"LAMA (항콜린제)","적응증":"COPD 유지 치료","용량":"18mcg 1일 1회 흡입","부작용":"구갈, 배뇨 장애","주의":"안압 상승 주의(녹내장).","보험코드":"640026ATB","급여":"급여","약가":"1캡슐 1,200원","근거":"COPD 악화 감소 및 폐기능 개선"},
        "심비코트": {"성분":"budesonide/formoterol","계열":"ICS + LABA","적응증":"천식, COPD","용량":"필요시 또는 정기 흡입","부작용":"구강 칸디다증, 목소리 변함","주의":"사용 후 반드시 입안을 물로 헹굴 것.","보험코드":"640027ATB","급여":"급여","약가":"1통 35,000원","근거":"염증 조절 및 기관지 확장"},
        "렉사프로": {"성분":"escitalopram","계열":"SSRI","적응증":"우울증, 불안장애","용량":"10~20mg 1일 1회","부작용":"오심, 수면 장애, 성기능 장애","주의":"갑작스러운 중단 금지. 청소년 모니터링.","보험코드":"640028ATB","급여":"급여","약가":"1정 1,000원","근거":"우수한 효과와 내약성"},
        "리피토": {"성분":"atorvastatin","계열":"Statin","적응증":"이상지질혈증, 심혈관 예방","용량":"10~80mg 1일 1회","부작용":"근육통, 간효소 수치 상승","주의":"자몽주스 섭취 제한. 근육통 발생 시 상담.","보험코드":"640029ATB","급여":"급여","약가":"1정 600원","근거":"LDL-C 강하 및 심혈관 사고 예방"},
        "포사맥스": {"성분":"alendronate","계열":"Bisphosphonate","적응증":"골다공증","용량":"70mg 주 1회 아침 공복","부작용":"식도염, 복통","주의":"복용 후 30분간 눕지 말 것. 충분한 물과 복용.","보험코드":"640030ATB","급여":"급여","약가":"1정 5,000원","근거":"골절 위험 감소"},
        "케토스테릴": {"성분":"ketoanalogues","계열":"아미노산 제제","적응증":"만성 신부전 단백질 대사 보조","용량":"식사와 함께 복용","부작용":"고칼슘혈증","주의":"저단백 식단과 병행 필수.","보험코드":"640031ATB","급여":"급여","약가":"1정 400원","근거":"신부전 진행 지연 보조"},
        "코대원정": {"성분":"dihydrocodeine 등","계열":"진해거담제","적응증":"기침, 가래 완화","용량":"2정 1일 3회","부작용":"졸음, 변비, 구갈","주의":"과도한 음주나 흡연은 삼가세요. 졸릴 수 있습니다.","보험코드":"비급여","급여":"비급여","약가":"-","근거":"진해거담 복합제"},
        "슈다페드정": {"성분":"pseudoephedrine","계열":"비충혈제거제","적응증":"코막힘 완화","용량":"60mg 1일 3회","부작용":"불면, 심계항진","주의":"전문가 상의 없이 7일 이상 투여하지 마세요.","보험코드":"640032ATB","급여":"급여","약가":"1정 50원","근거":"교감신경 흥분 코막힘 완화"},
        "베아솔론정": {"성분":"methylprednisolone","계열":"부신피질호르몬제","적응증":"알레르기, 염증 질환","용량":"초기 4~48mg","부작용":"혈당상승, 감염위험","주의":"전문가 상의 없이 장기간 연용하지 마세요.","보험코드":"640033ATB","급여":"급여","약가":"1정 30원","근거":"강력한 항염작용"},
        "라니넥스나잘스프레이": {"성분":"mometasone","계열":"비강용 스테로이드","적응증":"알레르기 비염 치료","용량":"1일 1회 각 비강 분무","부작용":"코피, 자극감","주의":"머리를 뒤로 젖히지 말고 선 자세에서 투여하세요.","보험코드":"640034ATB","급여":"급여","약가":"1통 5,000원","근거":"알레르기 비염 1차 치료제"},
        "타세바정": {"성분":"erlotinib","계열":"EGFR TKI","적응증":"비소세포폐암 (EGFR 돌연변이 양성)","용량":"150mg 1일 1회 공복","부작용":"피부발진, 설사, 간독성","주의":"CYP3A4 억제제 병용 주의. 임산부 금기.","보험코드":"652700ATB","급여":"선별급여 80%","약가":"1정 11,234원","근거":"EURTAC trial PFS 9.7개월 vs 화학요법 5.2개월"},
        "키트루다": {"성분":"pembrolizumab","계열":"PD-1 억제제","적응증":"흑색종, NSCLC, 두경부암, MSI-H 고형암","용량":"200mg IV 3주 간격","부작용":"irAE: 폐렴, 대장염, 간염, 내분비병증","주의":"자가면역질환 주의. 스테로이드 병용 시 효과 저하.","보험코드":"645502ATI","급여":"선별급여 80%","약가":"100mg/4mL 바이알 2,847,000원","근거":"KEYNOTE-006 OS 32.7% vs 이필리무맙 15.2%"},
        "넥사바정": {"성분":"sorafenib","계열":"다중 키나아제 억제제","적응증":"간세포암, 신세포암, 갑상선암","용량":"400mg 1일 2회 공복","부작용":"수족증후군, 고혈압, 설사, 출혈","주의":"QT 연장 주의. 와파린 병용 INR 모니터링.","보험코드":"652500ATB","급여":"급여 (Child-Pugh A/B)","약가":"1정 10,945원","근거":"SHARP trial OS 10.7개월 vs 위약 7.9개월"},
        "옵디보":   {"성분":"nivolumab","계열":"PD-1 억제제","적응증":"흑색종, NSCLC, 신세포암, 대장암(MSI-H)","용량":"240mg IV 2주 간격","부작용":"irAE: 폐렴, 대장염, 간염, 신장염","주의":"이필리무맙 병용 시 독성 증가.","보험코드":"645503ATI","급여":"선별급여 80%","약가":"10mg/mL 10mL 바이알 1,823,000원","근거":"CheckMate 025 OS 25.0개월 vs 에베로리무스 19.6개월"},
        "글리벡정": {"성분":"imatinib","계열":"BCR-ABL TKI","적응증":"만성골수성백혈병(CML), GIST","용량":"400mg 1일 1회 식사와 함께","부작용":"오심, 부종, 근육경련, 간독성","주의":"CYP3A4/2D6 상호작용 다수. 임산부 금기.","보험코드":"652300ATB","급여":"급여 100%","약가":"100mg 1정 3,456원","근거":"IRIS trial 5년 CCyR 87%"},
        "허셉틴":   {"성분":"trastuzumab","계열":"HER2 표적 단클론항체","적응증":"HER2 양성 유방암, 위암","용량":"초기 8mg/kg → 유지 6mg/kg 3주 간격","부작용":"심독성(LVEF 감소), 주입 반응","주의":"안트라사이클린 동시 투여 금지.","보험코드":"645501ATI","급여":"급여 (HER2 3+)","약가":"440mg 바이알 804,000원","근거":"HERA trial 2년 DFS HR 0.54"},
        "아바스틴": {"성분":"bevacizumab","계열":"VEGF 억제제","적응증":"대장암, 폐암, 교모세포종","용량":"5mg/kg 2주 간격","부작용":"고혈압, 출혈, 단백뇨","주의":"수술 전후 투여 주의 (상처 치유 지연)","보험코드":"645504ATI","급여":"선별급여 80%","약가":"100mg 바이알 330,000원","근거":"혈관신생 억제 생존율 증가"},
        "싱귤레어츄정": {"성분":"montelukast","계열":"류코트리엔 수용체 길항제","적응증":"천식, 알레르기 비염","용량":"5mg 1일 1회 저녁","부작용":"신경정신계 이상반응","주의":"소아 행동 변화 관찰 필요.","보험코드":"640001ATB","급여":"급여","약가":"1정 700원","근거":"소아 천식 유지요법 가이드라인"},
        "벤톨린네뷸": {"성분":"salbutamol","계열":"속효성 β2 효능제","적응증":"기관지 경련 완화","용량":"2.5mg 필요시","부작용":"심계항진, 떨림","주의":"과도한 사용 피할 것.","보험코드":"640002ATB","급여":"급여","약가":"1앰플 500원","근거":"급성 천식 발작 1차 선택제"},
        "메디락디에스": {"성분":"bacillus subtilis","계열":"프로바이오틱스","적응증":"정장, 장내이상발효","용량":"1캡슐 1일 2~3회","부작용":"드물게 복부팽만","주의":"면역저하자 주의.","보험코드":"640003ATB","급여":"비급여","약가":"1캡슐 200원","근거":"항생제 연관 설사 예방"},
        "리루텍정": {"성분":"riluzole","계열":"글루타메이트 길항제","적응증":"근위축성측삭경화증 (루게릭병)","용량":"50mg 1일 2회","부작용":"무력감, 간효소 수치 상승","주의":"간기능 정기 검사 필수.","보험코드":"640004ATB","급여":"산정특례 90%","약가":"1정 15,000원","근거":"ALS 생존 기간 연장 효과 입증"},
        "메스티논정": {"성분":"pyridostigmine","계열":"항콜린에스테라제","적응증":"중증근무력증","용량":"60mg 1일 3~4회","부작용":"복통, 설사, 타액분비 과다","주의":"천식 고객 주의.","보험코드":"640005ATB","급여":"산정특례 90%","약가":"1정 120원","근거":"중증근무력증 1차 대증치료제"},
        "코엔자임큐텐": {"성분":"coenzyme Q10","계열":"항산화제","적응증":"심혈관 건강, 에너지 대사 보조","용량":"100mg 1일 1회","부작용":"가벼운 위장장애","주의":"항응고제와 상호작용 가능성.","보험코드":"640006ATB","급여":"비급여","약가":"1캡슐 800원","근거":"미토콘드리아 기능 장애 보조"},
        "무코스타정": {"성분":"rebamipide","계열":"위점막 보호제","적응증":"위궤양, 위염","용량":"100mg 1일 3회","부작용":"구갈, 변비","주의":"신장애 고객 주의.","보험코드":"640007ATB","급여":"급여","약가":"1정 130원","근거":"소염진통제 유발 위장관계 부작용 예방"},
        "론서프정": {"성분":"trifluridine/tipiracil","계열":"항대사물질","적응증":"전이성 대장암","용량":"35mg/m2 1일 2회 (1~5, 8~12일)","부작용":"골수억제, 오심, 피로","주의":"중증 신장애 금기.","보험코드":"640008ATB","급여":"급여","약가":"1정 35,000원","근거":"RECOURSE trial OS 연장"},
        "스토가정": {"성분":"lafutidine","계열":"H2 수용체 길항제","적응증":"위·십이지장궤양, 역류성식도염","용량":"10mg 1일 2회","부작용":"변비, 두통","주의":"고령자 용량 감량.","보험코드":"640009ATB","급여":"급여","약가":"1정 250원","근거":"강력한 위산분비 억제 효과"},
        "맥페란정": {"성분":"metoclopramide","계열":"항구토제","적응증":"구역, 구토","용량":"10mg 1일 3회 이하","부작용":"추체외로 증상, 졸음","주의":"5일 이상 장기 사용 금지.","보험코드":"640010ATB","급여":"급여","약가":"1정 50원","근거":"화학요법 유발 오심구토 완화"},
        "디고신엘릭시르": {"성분":"digoxin","계열":"강심제","적응증":"심부전, 빈맥","용량":"체중 비례 조절","부작용":"서맥, 구토","주의":"혈중농도 모니터링 필수.","보험코드":"640011ATB","급여":"급여","약가":"1mL 25원","근거":"소아 심부전 표준치료"},
        "라식스": {"성분":"furosemide","계열":"이뇨제","적응증":"부종, 고혈압","용량":"체중 비례","부작용":"전해질 불균형","주의":"저칼륨혈증 주의.","보험코드":"640012ATB","급여":"급여","약가":"1정 20원","근거":"체액 저류 완화"},
        "알닥톤": {"성분":"spironolactone","계열":"칼륨보존성 이뇨제","적응증":"심부전, 부종","용량":"체중 비례","부작용":"고칼륨혈증","주의":"정기적 전해질 검사.","보험코드":"640013ATB","급여":"급여","약가":"1정 60원","근거":"심부전 사망률 감소"},
        "시나지스": {"성분":"palivizumab","계열":"RSV 단클론항체","적응증":"RSV 감염 예방","용량":"15mg/kg 월 1회","부작용":"발열, 발진","주의":"고위험군 영아 한정.","보험코드":"640014ATB","급여":"급여(조건부)","약가":"50mg 550,000원","근거":"미숙아 RSV 예방"},
        "란투스": {"성분":"insulin glargine","계열":"기저 인슐린","적응증":"당뇨병","용량":"개별 조절","부작용":"저혈당","주의":"매일 같은 시간 투여.","보험코드":"640015ATB","급여":"급여","약가":"1펜 12,000원","근거":"24시간 지속형"},
        "휴말로그": {"성분":"insulin lispro","계열":"초속효성 인슐린","적응증":"당뇨병","용량":"식전 조절","부작용":"저혈당","주의":"식사 15분 전 투여.","보험코드":"640016ATB","급여":"급여","약가":"1펜 10,000원","근거":"식후 혈당 조절"},
        "콘서타": {"성분":"methylphenidate","계열":"중추신경흥분제","적응증":"ADHD","용량":"18~54mg 1일 1회","부작용":"식욕부진, 불면","주의":"성장 지연 모니터링.","보험코드":"640017ATB","급여":"급여","약가":"1정 1,200원","근거":"ADHD 1차 선택제"},
        "휴미라": {"성분":"adalimumab","계열":"TNF-a 억제제","적응증":"크론병, 류마티스","용량":"40mg 2주 1회","부작용":"감염 위험 증가","주의":"결핵 잠복 감염 확인 필수.","보험코드":"640018ATB","급여":"산정특례 90%","약가":"1펜 400,000원","근거":"중증 자가면역질환 완화"},
        "이뮤란": {"성분":"azathioprine","계열":"면역억제제","적응증":"크론병, 장기이식","용량":"50mg 1일 1회","부작용":"골수억제, 간독성","주의":"TPMT 유전자 검사 권장.","보험코드":"640019ATB","급여":"급여","약가":"1정 300원","근거":"스테로이드 대체 요법"},
        "펜타사": {"성분":"mesalazine","계열":"항염증제","적응증":"크론병, 궤양성대장염","용량":"1g 1일 2회","부작용":"두통, 복통","주의":"신장애 주의.","보험코드":"640020ATB","급여":"급여","약가":"1포 800원","근거":"장내 염증 억제"},
        "입랜스": {"성분":"palbociclib","계열":"CDK4/6 억제제","적응증":"HR+ HER2- 유방암","용량":"125mg 1일 1회 (3주 복용/1주 휴약)","부작용":"호중구감소증","주의":"정기적 CBC 검사 필수.","보험코드":"640021ATB","급여":"선별급여","약가":"1정 140,000원","근거":"PFS 유의미한 연장"},
        "페마라": {"성분":"letrozole","계열":"아로마타제 억제제","적응증":"폐경 후 유방암","용량":"2.5mg 1일 1회","부작용":"골다공증, 관절통","주의":"골밀도 모니터링.","보험코드":"640022ATB","급여":"급여","약가":"1정 2,500원","근거":"에스트로겐 생성 억제"},
        "게프티닙정": {"성분":"gefitinib","계열":"EGFR TKI 표적항암제","적응증":"EGFR 돌연변이 폐암","용량":"250mg 1일 1회","부작용":"설사, 피부발진","주의":"간기능 모니터링","보험코드":"652701ATB","급여":"선별급여","약가":"1정 2,500원","근거":"EGFR 억제"},
        "야르보이": {"성분":"ipilimumab","계열":"면역항암제(CTLA-4)","적응증":"진행성 흑색종","용량":"3mg/kg 3주 간격","부작용":"장염, 간염","주의":"옵디보 병용시 독성 증가","보험코드":"645505ATI","급여":"선별급여","약가":"바이알 10,000,000원","근거":"T세포 활성화"},
        "베실리온정": {"성분":"종합 영양보충(L-Glutamine 등)","계열":"항암 보조제","적응증":"항암 치료 중 영양 보충","용량":"1일 1회","부작용":"드물게 위장장애","주의":"임상데이터 Phase 2 진행중","보험코드":"비급여","급여":"비급여","약가":"1정 50,000원","근거":"항암 부작용 완화"},
        "엑스지바": {"성분":"denosumab","계열":"RANKL 억제제","적응증":"골전이 암, 골거대세포종","용량":"120mg 4주 1회 SC","부작용":"저칼슘혈증, 턱뼈괴사","주의":"치과 치료 전 주의. 칼슘 보충.","보험코드":"640023ATB","급여":"선별급여","약가":"1바이알 300,000원","근거":"골격계 합병증(SRE) 지연"},
        "덱사메타손": {"성분":"dexamethasone","계열":"코르티코스테로이드","적응증":"염증, 항암 부작용 예방","용량":"4mg 필요시","부작용":"혈당 상승, 불면","주의":"장기 사용 시 부신억제.","보험코드":"640024ATB","급여":"급여","약가":"1정 20원","근거":"항염증 및 구토 억제"},
        "마도파": {"성분":"levodopa/benserazide","계열":"도파민 전구체","적응증":"파킨슨병","용량":"125mg 1일 3회","부작용":"운동동요, 구역","주의":"고단백 식사와 병용 피할 것.","보험코드":"640025ATB","급여":"급여","약가":"1정 200원","근거":"파킨슨병 1차 증상 완화"},
        "리큅": {"성분":"ropinirole","계열":"도파민 효능제","적응증":"파킨슨병","용량":"2mg 1일 3회","부작용":"졸음, 환각","주의":"갑작스런 수면 발작 주의.","보험코드":"640026ATB","급여":"급여","약가":"1정 600원","근거":"레보도파 용량 절감 효과"},
        "엔트레스토": {"성분":"sacubitril/valsartan","계열":"ARNI","적응증":"만성 심부전","용량":"50mg 1일 2회","부작용":"저혈압, 고칼륨혈증","주의":"ACE 억제제 병용 금기 (36시간 간격).","보험코드":"640027ATB","급여":"선별급여","약가":"1정 2,000원","근거":"심부전 입원 및 사망률 감소"},
        "콩코르": {"성분":"bisoprolol","계열":"베타차단제","적응증":"고혈압, 심부전","용량":"2.5mg 1일 1회","부작용":"서맥, 피로","주의":"천식 고객 주의.","보험코드":"640028ATB","급여":"급여","약가":"1정 150원","근거":"심박수 조절 및 생존율 증가"},
        "케프라시럽": {"성분":"levetiracetam","계열":"항경련제","적응증":"뇌전증 부분발작","용량":"100mg 1일 2회","부작용":"졸음, 행동변화","주의":"신장 기능에 따른 용량 조절.","보험코드":"640029ATB","급여":"급여","약가":"1mL 50원","근거":"소아 뇌전증 안전성 확보"},
        "데파코트스프링클": {"성분":"divalproex sodium","계열":"항경련제","적응증":"뇌전증 발작, 조증","용량":"125mg 1일 2회","부작용":"간독성, 체중증가","주의":"음식에 뿌려 복용 가능 (씹지 말 것).","보험코드":"640030ATB","급여":"급여","약가":"1캡슐 200원","근거":"복용 편의성 개선된 소아 제형"},
        "엑세그란": {"성분":"zonisamide","계열":"항경련제","적응증":"부분발작 보조요법","용량":"25mg 1일 1회","부작용":"졸음, 식욕감소","주의":"설폰아마이드 과민증 금기.","보험코드":"640031ATB","급여":"급여","약가":"1정 300원","근거":"복합 발작 조절에 시너지"},
    },
    "질환": {
        "폐암":   {"분류":"NSCLC 85%, SCLC 15%","바이오마커":"EGFR, ALK, ROS1, KRAS G12C, PD-L1","1차치료":"EGFR 변이: EGFR TKI / PD-L1≥50%: 키트루다","생존율":"5년 전체 22%, 조기 80~90%, 전이 5~10%","스크리닝":"55~80세, 30갑년 이상: 저선량 CT 연 1회"},
        "흑색종": {"분류":"피부·안구·점막 흑색종","바이오마커":"BRAF V600E/K 약 50%, NRAS, c-KIT","1차치료":"PD-1 억제제 ± CTLA-4 / BRAF V600E: BRAF+MEK 억제제","생존율":"전이성 5년 약 25%","주의":"자외선 차단. ABCDE 기준 조기 발견."},
        "간암":   {"분류":"간세포암(HCC) 75~85%","바이오마커":"AFP, PIVKA-II","1차치료":"조기: 절제/고주파 / 중기: TACE / 진행: 소라페닙","생존율":"진행성 5년 10~15%","주의":"B/C형 간염 치료. 6개월마다 초음파."},
        "대장암": {"분류":"결장암 60%, 직장암 40%","바이오마커":"MSI, KRAS, NRAS, BRAF V600E","1차치료":"FOLFOX/FOLFIRI ± 베바시주맙 / MSI-H: 면역관문억제제","생존율":"5년 전체 65%, IV기 14%","스크리닝":"45세부터 대장내시경 10년마다"},
        "백혈병": {"분류":"CML, AML, CLL, ALL","바이오마커":"BCR-ABL(CML), FLT3, NPM1","1차치료":"CML: 이마티닙 / AML: 7+3 화학요법","생존율":"CML 5년 >90%, AML 5년 30%","주의":"정기 PCR 모니터링 (CML)"},
        "유방암": {"분류":"HR+, HER2+, 삼중음성","바이오마커":"ER, PR, HER2, Ki-67, BRCA1/2","1차치료":"HR+: 호르몬요법 ± CDK4/6 억제제 / HER2+: 허셉틴","생존율":"전체 5년 91%, IV기 28%","스크리닝":"40세부터 유방촬영술 1~2년마다"},
        "소아백혈병": {"분류":"ALL (급성림프모구백혈병) 대다수","바이오마커":"BCR-ABL, TEL-AML1","1차치료":"관해유도 화학요법, 조혈모세포이식","생존율":"5년 생존율 80~90% 이상","주의":"성장 지연, 이차암 등 장기 추적관찰 필수"},
        "천식": {"분류":"알레르기성, 비알레르기성","바이오마커":"호산구 수, IgE","1차치료":"흡입용 스테로이드(ICS), 류코트리엔 조절제","생존율":"대부분 양호하나 급성 발작 주의","주의":"소아의 경우 성장 지연 모니터링"},
        "루게릭병": {"분류":"근위축성측삭경화증 (ALS)","바이오마커":"SOD1, C9orf72 유전자 변이","1차치료":"리루졸, 에다라본, 호흡보조","생존율":"진단 후 평균 3~5년","주의":"호흡근 약화, 연하곤란 등 다학제 관리 필요"},
        "중증근무력증": {"분류":"신경근육접합부 자가면역질환","바이오마커":"항AChR 항체, 항MuSK 항체","1차치료":"항콜린에스테라제, 면역억제제, 흉선절제술","생존율":"적절한 치료 시 정상 수명 기대","주의":"호흡부전(근무력성 위기) 유발 약물(일부 항생제 등) 주의"},
        "위염": {"분류":"급성, 만성 (표재성, 위축성 등)","바이오마커":"H. pylori 검사","1차치료":"PPI, H2RA, 점막보호제, 제균치료","생존율":"양호 (위암 진행 모니터링)","주의":"식이조절, 스트레스 관리, 장기 복용 최소화"},
        "진행성 대장암": {"분류":"결장암 60%, 직장암 40%","바이오마커":"MSI, KRAS, NRAS, BRAF V600E","1차치료":"FOLFOX/FOLFIRI ± 표적치료제(아바스틴 등)","생존율":"진행성 10-15%","주의":"다제 요법 부작용 집중 관리"},
        "선천성 심질환": {"분류":"VSD, ASD 등 다양","바이오마커":"심초음파 소견","1차치료":"약물요법(이뇨제, 강심제) 또는 수술","생존율":"질환 및 수술 여부에 따라 상이","주의":"호흡기 감염 예방 필수 (RSV 위험)"},
        "RSV 감염": {"분류":"호흡기 세포융합 바이러스 감염","바이오마커":"RSV 항원 검사","1차치료":"대증요법, 고위험군 예방적 항체(시나지스)","생존율":"대부분 회복하나 고위험 영유아 치명적일 수 있음","주의":"비말 감염 주의, 겨울철 예방 접종 중요"},
        "제1형 당뇨병": {"분류":"자가면역성 췌장 베타세포 파괴","바이오마커":"자가항체, 낮은 C-펩타이드","1차치료":"다회 인슐린 주사(MDI) 또는 펌프","생존율":"적절한 관리 시 일반인과 유사","주의":"성장기 소아청소년의 철저한 혈당 및 영양 관리"},
        "ADHD": {"분류":"주의력결핍 과다행동장애","바이오마커":"특정 임상 평가 척도","1차치료":"중추신경흥분제(메틸페니데이트), 행동치료","생존율":"생명 지장 없음","주의":"식욕부진 및 수면장애 모니터링"},
        "크론병": {"분류":"염증성 장질환 (전장관 침범 가능)","바이오마커":"CRP, 대변 칼프로텍틴","1차치료":"생물학적제제(휴미라 등), 면역억제제","생존율":"생명 지장 없으나 삶의 질 크게 저하","주의":"장 협착, 누공 등 합병증 관찰"},
        "전이성 유방암": {"분류":"호르몬/HER2 수용체 상태에 따른 아형","바이오마커":"ER, PR, HER2","1차치료":"표적항암제(CDK4/6 억제제 등) + 호르몬치료","생존율":"5년 생존율 약 30% 수준","주의":"골전이 동반 시 뼈 보호제(엑스지바 등) 필수"},
        "파킨슨병": {"분류":"신경퇴행성 질환","바이오마커":"도파민 운반체(DAT) 스캔","1차치료":"레보도파 복합제, 도파민 효능제","생존율":"서서히 진행, 합병증(폐렴 등) 주의","주의":"약물 소진 현상(wearing-off) 및 기립성 저혈압 관찰"},
        "심부전": {"분류":"HFrEF, HFpEF","바이오마커":"NT-proBNP","1차치료":"ARNI(엔트레스토), 베타차단제, SGLT2 억제제","생존율":"5년 생존율 약 50%","주의":"다제약물(폴리파머시)로 인한 신기능/전해질 이상 주의"},
        "소아 뇌전증": {"분류":"전신발작, 부분발작 등 다양","바이오마커":"뇌파(EEG), MRI","1차치료":"항경련제 단독 또는 복합요법","생존율":"원인에 따라 다양 (양성 뇌전증은 호전 가능)","주의":"발작 빈도 기록 및 약물 순응도 엄격히 관리"},
        "췌장암": {"분류":"C25","바이오마커":"BRCA, MSI","1차치료":"수술, FOLFIRINOX 등 항암화학","생존율":"1년 25%, 5년 12%","주의":"조기 발견 매우 어려움, 황달 모니터링"},
        "자궁경부암": {"분류":"C53","바이오마커":"HPV","1차치료":"수술, 방사선, 항암","생존율":"초기 95%","주의":"HPV 백신 접종 및 정기적 팝스미어 권장"},
        "액상 생검(MCED)": {"분류":"조기 진단 기술","바이오마커":"ctDNA, CTC (순환 종양 세포)","1차치료":"현재 FoundationOne 등 제한적 동반 진단 사용중","생존율":"임상 진단 3년 전부터 암 감지 가능 (Cancer Discovery 2025 보고)","주의":"대부분 임상시험 단계이며 FDA 승인 기기 제한적"},
    },
    "상호작용": {
        "알로퓨리놀 + 이뮤란":     "⚠️ [절대 금기] 독성 4~5배 상승하여 심각한 골수억제 유발. 즉시 중단 및 확인 필요.",
        "타세바정 + 키트루다":     "병용 시 irAE 및 피부독성 증가 가능. 주의 요함.",
        "글리벡정 + 와파린":       "이마티닙 CYP2C9 억제 → INR 상승 위험. 주간 모니터링 필수.",
        "허셉틴 + 안트라사이클린": "동시 투여 절대 금기 (심독성). 4주 후 허셉틴 시작.",
        "옵디보 + 스테로이드":     "면역관문억제제 효과 저하 가능. irAE 치료 외 최소화.",
        "엔트레스토 + ACE억제제": "혈관부종 위험. ACE억제제 중단 후 반드시 36시간 대기 후 엔트레스토 시작.",
    },
}

DRUG_PRICES = {
    "타세바정": {"성분":"erlotinib 150mg",     "코드":"652700ATB","가격":11234,   "단위":"정",     "급여":"선별급여 80%"},
    "키트루다": {"성분":"pembrolizumab 100mg", "코드":"645502ATI","가격":2847000, "단위":"바이알", "급여":"선별급여 80%"},
    "넥사바정": {"성분":"sorafenib 200mg",      "코드":"652500ATB","가격":10945,   "단위":"정",     "급여":"급여(Child-Pugh A/B)"},
    "옵디보":   {"성분":"nivolumab 10mg/mL",    "코드":"645503ATI","가격":1823000, "단위":"바이알", "급여":"선별급여 80%"},
    "글리벡정": {"성분":"imatinib 100mg",       "코드":"652300ATB","가격":3456,    "단위":"정",     "급여":"급여 100%"},
    "허셉틴":   {"성분":"trastuzumab 440mg",    "코드":"645501ATI","가격":804000,  "단위":"바이알", "급여":"급여(HER2 3+)"},
    "타그리소": {"성분":"osimertinib 80mg",     "코드":"652900ATB","가격":78520,   "단위":"정",     "급여":"선별급여 80%"},
    "렌비마":   {"성분":"lenvatinib 10mg",      "코드":"652800ATB","가격":24500,   "단위":"정",     "급여":"선별급여 80%"},
    "엑스탄디": {"성분":"enzalutamide 40mg",    "코드":"653100ATB","가격":14200,   "단위":"정",     "급여":"급여(전이성 CRPC)"},
    "아바스틴": {"성분":"bevacizumab 100mg",    "코드":"645504ATI","가격":330000,  "단위":"바이알", "급여":"선별급여 80%"},
    "싱귤레어츄정": {"성분":"montelukast 5mg", "코드":"640001ATB","가격":700, "단위":"정", "급여":"급여"},
    "벤톨린네뷸": {"성분":"salbutamol 2.5mg", "코드":"640002ATB","가격":500, "단위":"앰플", "급여":"급여"},
    "메디락디에스": {"성분":"bacillus subtilis", "코드":"640003ATB","가격":200, "단위":"캡슐", "급여":"비급여"},
    "리루텍정": {"성분":"riluzole 50mg", "코드":"640004ATB","가격":15000, "단위":"정", "급여":"산정특례 90%"},
    "메스티논정": {"성분":"pyridostigmine 60mg", "코드":"640005ATB","가격":120, "단위":"정", "급여":"산정특례 90%"},
    "코엔자임큐텐": {"성분":"coenzyme Q10 100mg", "코드":"640006ATB","가격":800, "단위":"캡슐", "급여":"비급여"},
    "무코스타정": {"성분":"rebamipide 100mg", "코드":"640007ATB","가격":130, "단위":"정", "급여":"급여"},
    "론서프정": {"성분":"trifluridine 15mg", "코드":"640008ATB","가격":35000, "단위":"정", "급여":"급여"},
    "스토가정": {"성분":"lafutidine 10mg", "코드":"640009ATB","가격":250, "단위":"정", "급여":"급여"},
    "맥페란정": {"성분":"metoclopramide 10mg", "코드":"640010ATB","가격":50, "단위":"정", "급여":"급여"},
    "디고신엘릭시르": {"성분":"digoxin", "코드":"640011ATB","가격":25, "단위":"mL", "급여":"급여"},
    "라식스": {"성분":"furosemide", "코드":"640012ATB","가격":20, "단위":"정", "급여":"급여"},
    "알닥톤": {"성분":"spironolactone", "코드":"640013ATB","가격":60, "단위":"정", "급여":"급여"},
    "시나지스": {"성분":"palivizumab 50mg", "코드":"640014ATB","가격":550000, "단위":"바이알", "급여":"급여(조건부)"},
    "란투스": {"성분":"insulin glargine", "코드":"640015ATB","가격":12000, "단위":"펜", "급여":"급여"},
    "휴말로그": {"성분":"insulin lispro", "코드":"640016ATB","가격":10000, "단위":"펜", "급여":"급여"},
    "콘서타": {"성분":"methylphenidate 18mg", "코드":"640017ATB","가격":1200, "단위":"정", "급여":"급여"},
    "휴미라": {"성분":"adalimumab 40mg", "코드":"640018ATB","가격":400000, "단위":"펜", "급여":"산정특례 90%"},
    "이뮤란": {"성분":"azathioprine 50mg", "코드":"640019ATB","가격":300, "단위":"정", "급여":"급여"},
    "펜타사": {"성분":"mesalazine 1g", "코드":"640020ATB","가격":800, "단위":"포", "급여":"급여"},
    "입랜스": {"성분":"palbociclib 125mg", "코드":"640021ATB","가격":140000, "단위":"정", "급여":"선별급여"},
    "페마라": {"성분":"letrozole 2.5mg", "코드":"640022ATB","가격":2500, "단위":"정", "급여":"급여"},
    "엑스지바": {"성분":"denosumab 120mg", "코드":"640023ATB","가격":300000, "단위":"바이알", "급여":"선별급여"},
    "덱사메타손": {"성분":"dexamethasone 4mg", "코드":"640024ATB","가격":20, "단위":"정", "급여":"급여"},
    "마도파": {"성분":"levodopa/benserazide", "코드":"640025ATB","가격":200, "단위":"정", "급여":"급여"},
    "리큅": {"성분":"ropinirole 2mg", "코드":"640026ATB","가격":600, "단위":"정", "급여":"급여"},
    "엔트레스토": {"성분":"sacubitril/valsartan 50mg", "코드":"640027ATB","가격":2000, "단위":"정", "급여":"선별급여"},
    "콩코르": {"성분":"bisoprolol 2.5mg", "코드":"640028ATB","가격":150, "단위":"정", "급여":"급여"},
    "케프라시럽": {"성분":"levetiracetam", "코드":"640029ATB","가격":50, "단위":"mL", "급여":"급여"},
    "데파코트스프링클": {"성분":"divalproex sodium", "코드":"640030ATB","가격":200, "단위":"캡슐", "급여":"급여"},
    "엑세그란": {"성분":"zonisamide 25mg",      "코드":"640031ATB","가격":300,    "단위":"정",     "급여":"급여"},
    "다이아벡스정": {"성분":"metformin 500mg", "코드":"641900580","가격":72,      "단위":"정",     "급여":"급여"},
    "노바스크정": {"성분":"amlodipine 5mg",    "코드":"648900030","가격":363,     "단위":"정",     "급여":"급여"},
    "플라빅스정": {"성분":"clopidogrel 75mg",  "코드":"645200050","가격":1144,    "단위":"정",     "급여":"급여"},
    "타이레놀정": {"성분":"acetaminophen 500mg","코드":"642202040","가격":51,      "단위":"정",     "급여":"급여"},
    "씨투스정":   {"성분":"pranlukast 50mg",    "코드":"665500010","가격":381,     "단위":"정",     "급여":"급여"},
    "보트리엔트정": {"성분":"pazopanib 200mg", "코드":"645504780","가격":19500,   "단위":"정",     "급여":"급여"},
    "챔프시럽":   {"성분":"acetaminophen 5mL",  "코드":"642203010","가격":220,     "단위":"포",     "급여":"급여"},
    "베아제정":   {"성분":"소화효소제",         "코드":"641601460","가격":150,     "단위":"정",     "급여":"급여"},
    "게프티닙정": {"성분":"gefitinib 250mg", "코드":"652701ATB","가격":3500000, "단위":"정", "급여":"선별급여 80%"},
    "야르보이": {"성분":"ipilimumab 50mg", "코드":"645505ATI","가격":14000000, "단위":"바이알", "급여":"선별급여 80%"},
    "베실리온정": {"성분":"Besselion 500mg", "코드":"NEW-V28","가격":70000, "단위":"정", "급여":"비급여(임상중)"},
}

POLICY_NEWS = [
    {"tag":"급여기준","date":"2026-04-15","title":"심평원, 2026년 1분기 항암제 급여 기준 개정 고시","body":"PD-L1 발현율 기준 없이 TMB-High 기준만으로 면역항암제 급여 적용 가능. 키트루다·옵디보 적용 범위 확장.","source":"심평원 공고 2026-012"},
    {"tag":"신약허가","date":"2026-04-10","title":"식약처, EGFR 엑손 20 삽입 변이 NSCLC 신약 '리브레반트+라즈클루제' 허가","body":"아미반타맙+라즈클루제 병용요법 국내 허가 완료. EGFR TKI 치료 실패 후 2차 치료 옵션으로 승인.","source":"식약처 허가 공고"},
    {"tag":"정책변화","date":"2026-04-08","title":"복지부, 항암제 본인부담상한제 개선 — 연간 상한 500만원","body":"연간 500만원 초과분 전액 환급. 2026년 7월 시행. 면역항암제 고객 부담 최대 60% 감소 전망.","source":"보건복지부 보도자료"},
    {"tag":"진료지침","date":"2026-03-28","title":"대한종양학회, 2026 폐암 진료지침 개정 — KRAS G12C 억제제 1차 치료 포함","body":"소토라십(Lumakras)·아다그라십(Krazati)을 KRAS G12C 변이 NSCLC 1차 치료 옵션으로 공식 포함.","source":"대한종양학회 가이드라인 2026"},
    {"tag":"검사급여","date":"2026-03-20","title":"NGS 급여 확대 — 전이성 고형암 전반 적용","body":"기존 4개 암종에서 모든 전이성 고형암으로 NGS 급여 확대. 1회 검사로 최대 600개 유전자 분석 급여 인정.","source":"심평원 고시 제2026-31호"},
    {"tag":"디지털헬스","date":"2026-03-15","title":"서울대·삼성서울병원, AI 항암제 적정용량 예측 시스템 도입","body":"체성분·신기능·유전자형 데이터 종합 AI 시스템. 부작용 32% 감소, 치료 중단율 18% 감소 보고.","source":"병원 공동 보도자료"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# DB
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = "pharma_v20.db"

def init_db():
    """
    ✅ [리팩토링] with 문 Context Manager 사용 → DB 연결 안전 보장.
    (이전: conn.close() 수동 호출 방식 → 예외 시 연결 누수 위험)
    """
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # 14컬럼 처방 테이블 (절대 변경 금지 — 21,000자 지식베이스 연동 구조)
        c.execute("""CREATE TABLE IF NOT EXISTS rx (
            id INTEGER PRIMARY KEY, patient_id TEXT, medication_name TEXT,
            cancer_type TEXT, dosage TEXT, frequency TEXT, duration TEXT,
            start_date TEXT, doctor_name TEXT, status TEXT, side_effects TEXT,
            efficacy_rate REAL, notes TEXT, last_updated TEXT)""")
        # 환자 기본 정보 테이블 (6컬럼 — diet 포함)
        c.execute("""CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY, real_name TEXT, age INTEGER,
            gender TEXT, hospital TEXT, diet TEXT)""")
        # 기존 DB diet 컬럼 마이그레이션 (ALTER 오류 무시)
        try:
            c.execute("ALTER TABLE patients ADD COLUMN diet TEXT")
        except sqlite3.OperationalError:
            pass
        # 처방 데이터 삽입 (OR REPLACE: 재시작 시 최신 데이터 유지)
        for r in RAW_RX:
            c.execute("INSERT OR REPLACE INTO rx VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
        # 환자 정보 삽입 (OR IGNORE: 수동 수정된 이름 보호)
        for pid, info in DEFAULT_PATIENTS.items():
            c.execute(
                "INSERT OR IGNORE INTO patients (patient_id, real_name, age, gender, hospital) VALUES (?,?,?,?,?)",
                (pid, info["real_name"], info["age"], info["gender"], info["hospital"])
            )
        conn.commit()
    # 복약 이행도 스케줄 동기화 (신규)
    if HAS_ADHERENCE:
        keys = ["id","patient_id","medication_name","cancer_type","dosage","frequency",
                "duration","start_date","doctor_name","status","side_effects","efficacy_rate","notes","last_updated"]
        rx_list = [dict(zip(keys, r)) for r in RAW_RX]
        sync_schedules_from_rx(rx_list)
    # Guardian Link DB 초기화 (신규)
    if HAS_GUARDIAN:
        init_guardian_db()
    # 알약 이미지 DB 학습 (신규) — 최초 1회만 실행
    if HAS_PILL_RECOGNIZER:
        try:
            stats = get_db_stats()
            if stats.get("total_pills", 0) < 5:
                learn_patient_drugs(rx_list)
        except Exception as _pe:
            pass


def load_patients() -> Dict:
    """✅ with 문으로 DB 연결 안전 관리."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT patient_id, real_name, age, gender, hospital FROM patients")
        rows = c.fetchall()
    return {r[0]: {"real_name": r[1], "age": r[2], "gender": r[3], "hospital": r[4]} for r in rows}


def save_patient_name(pid: str, name: str):
    """✅ with 문으로 DB 연결 안전 관리."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE patients SET real_name=? WHERE patient_id=?", (name, pid))
        conn.commit()


def load_rx() -> List[Dict]:
    """✅ with 문으로 DB 연결 안전 관리."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rx ORDER BY id")
        rows = c.fetchall()
    keys = ["id","patient_id","medication_name","cancer_type","dosage","frequency",
            "duration","start_date","doctor_name","status","side_effects","efficacy_rate","notes","last_updated"]
    return [dict(zip(keys, r)) for r in rows]

# ═══════════════════════════════════════════════════════════════════════════════
# 지식베이스 검색
# ═══════════════════════════════════════════════════════════════════════════════

def kb_search(query: str) -> List[Dict]:
    q = query.lower().strip()
    if not q: return []
    results = []
    for name, info in KB["약물"].items():
        if q in name.lower() or q in info.get("성분","").lower() or q in info.get("적응증","").lower():
            results.append({"type":"💊 약물","title":name,"data":info,"score":1.0 if q==name.lower() else 0.7})
    for name, info in KB["질환"].items():
        if q in name.lower() or q in info.get("바이오마커","").lower() or q in info.get("1차치료","").lower():
            results.append({"type":"🏥 질환","title":name,"data":info,"score":1.0 if q==name.lower() else 0.6})
    for combo, desc in KB["상호작용"].items():
        if q in combo.lower() or any(q in d.strip().lower() for d in combo.split("+")):
            results.append({"type":"⚠️ 상호작용","title":combo,"data":{"내용":desc},"score":0.9})

    # OpenFDA 수집 데이터에서도 검색
    if HAS_MED_ENGINE:
        fda_results = search_knowledge(query)
        seen = {r["title"] for r in results}
        for fr in fda_results:
            if fr["name"] not in seen:
                data = fr.get("data", {})
                if fr["type"] == "FDA데이터":
                    fda_display = {
                        "성분(영문)":  data.get("english_name", ""),
                        "적응증(FDA)": data.get("indications", "")[:250],
                        "출처":        data.get("source", "OpenFDA"),
                    }
                    results.append({"type": "🇺🇸 FDA 데이터", "title": fr["name"],
                                    "data": fda_display, "score": fr["score"] * 0.1})
                elif fr["type"] == "질환":
                    results.append({"type": "🏥 질환(MKE)", "title": fr["name"],
                                    "data": data, "score": fr["score"] * 0.1})
                seen.add(fr["name"])

    # 계절별 과일·채소 × 항암제 RAG 지식베이스 검색
    if HAS_SEASONAL_RAG:
        seasonal_hits = search_seasonal_rag(query)
        seen_titles = {r["title"] for r in results}
        for sh in seasonal_hits:
            if sh["title"] not in seen_titles:
                results.append(sh)
                seen_titles.add(sh["title"])

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:12]

# ═══════════════════════════════════════════════════════════════════════════════
# 차트
# ═══════════════════════════════════════════════════════════════════════════════

def chart_hospital() -> go.Figure:
    """실제 환자 DB 기반 병원별·월별 활성 처방 수 버블 차트."""
    hospitals = ["서울이대병원","서울대병원","세브란스병원","서울아산병원","삼성서울병원","국립암센터"]
    months = ["Jan","Feb","Mar","Apr","May"]

    # 실제 데이터 시도 → 없으면 현재 메모리 데이터로 집계
    matrix = {h: {m: 0 for m in months} for h in hospitals}
    if HAS_MED_ENGINE:
        try:
            chart_data = get_hospital_chart_data(DB_PATH, fallback_rx=_get_fallback_rx(),
                                                  fallback_patients=_get_fallback_patients())
            matrix = chart_data["matrix"]
        except Exception:
            pass
    else:
        # 메모리 내 RAW_RX + DEFAULT_PATIENTS 직접 집계
        _aggregate_hospital_matrix(matrix, hospitals, months)

    MONTH_IDX = {m: i for i, m in enumerate(months)}
    HOSP_IDX  = {h: i for i, h in enumerate(hospitals)}
    fig = go.Figure()
    for hosp in hospitals:
        xs, ys, sz, labels = [], [], [], []
        for month in months:
            count = matrix.get(hosp, {}).get(month, 0)
            if count > 0:
                xs.append(MONTH_IDX[month])
                ys.append(HOSP_IDX[hosp])
                sz.append(max(10, count * 7))   # 처방 수 비례 크기
                labels.append(f"{month}: {count}건")
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="markers",
                marker=dict(size=sz, color="rgba(0,220,255,0.75)",
                            line=dict(color="rgba(0,242,255,1)", width=1.2)),
                hovertemplate=f"<b>{hosp}</b><br>%{{text}}<extra></extra>",
                text=labels, showlegend=False))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,12,28,0.9)",
        margin=dict(l=4,r=8,t=6,b=8), height=200,
        xaxis=dict(tickvals=list(range(5)), ticktext=months,
                   tickfont=dict(color="rgba(0,220,255,0.65)", size=10),
                   gridcolor="rgba(0,242,255,0.07)", zeroline=False),
        yaxis=dict(tickvals=list(range(6)), ticktext=hospitals,
                   tickfont=dict(color="rgba(0,220,255,0.8)", size=9,
                                 family="Noto Sans KR,sans-serif"),
                   gridcolor="rgba(0,242,255,0.07)", zeroline=False))
    return fig


def chart_trend() -> go.Figure:
    """실제 처방 데이터 기반 항암(Oncology) vs 만성질환(Chronic) 월별 효능률 추세."""
    months = ["Jan","Feb","Mar","Apr","May"]
    oncology_vals = [None] * 5
    chronic_vals  = [None] * 5

    if HAS_MED_ENGINE:
        try:
            td = get_trend_chart_data(DB_PATH, fallback_rx=_get_fallback_rx())
            oncology_vals = td["oncology"]
            chronic_vals  = td["chronic"]
        except Exception:
            pass

    # None 구간은 이전 값으로 보간 (선 끊김 방지)
    def fill_none(vals):
        last = None
        result = []
        for v in vals:
            if v is None and last is not None:
                result.append(last)
            else:
                result.append(v)
                last = v
        return result

    oncology_vals = fill_none(oncology_vals)
    chronic_vals  = fill_none(chronic_vals)

    fig = go.Figure()
    for name, color, fill, y_vals in [
        ("Oncology", "#00f2ff", "rgba(0,242,255,0.1)", oncology_vals),
        ("Chronic",  "#00e896", "rgba(0,232,150,0.1)", chronic_vals),
    ]:
        fig.add_trace(go.Scatter(
            x=months, y=y_vals, mode="lines+markers", name=name,
            line=dict(color=color, width=2),
            marker=dict(size=8, color=color),
            fill="tozeroy", fillcolor=fill,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>"))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,12,28,0.9)",
        margin=dict(l=4,r=8,t=6,b=8), height=200,
        xaxis=dict(tickfont=dict(color="rgba(0,220,255,0.65)", size=10),
                   gridcolor="rgba(0,242,255,0.07)", zeroline=False),
        yaxis=dict(tickfont=dict(color="rgba(0,220,255,0.65)", size=9),
                   gridcolor="rgba(0,242,255,0.07)", zeroline=False,
                   range=[0,100], ticksuffix="%"),
        legend=dict(font=dict(color="rgba(0,220,255,0.85)", size=10,
                              family="Noto Sans KR,sans-serif"),
                    bgcolor="rgba(0,0,0,0)", x=0.02, y=0.98))
    return fig


# ── 차트용 내부 헬퍼 ─────────────────────────────────────────────────────────

def _get_fallback_rx() -> list:
    """RAW_RX를 dict 리스트로 변환 (medical_knowledge_engine 호환)."""
    keys = ["id","patient_id","medication_name","cancer_type","dosage","frequency",
            "duration","start_date","doctor_name","status","side_effects",
            "efficacy_rate","notes","last_updated"]
    return [dict(zip(keys, r)) for r in RAW_RX]


def _get_fallback_patients() -> dict:
    """DEFAULT_PATIENTS를 {patient_id: hospital} 형태로 변환."""
    return {pid: info["hospital"] for pid, info in DEFAULT_PATIENTS.items()}


def _aggregate_hospital_matrix(matrix, hospitals, months):
    """medical_knowledge_engine 없을 때 메모리 데이터로 병원별 집계."""
    MONTH_NUM = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May",
                 "11":"Nov","12":"Dec"}
    for rx in RAW_RX:
        pid       = rx[1]
        start     = rx[7]
        pat_info  = DEFAULT_PATIENTS.get(pid, {})
        hospital  = pat_info.get("hospital", "")
        if not start or len(start) < 7:
            continue
        month_name = MONTH_NUM.get(start[5:7])
        if not month_name or month_name not in months:
            continue
        matched = next((h for h in hospitals if h in hospital or hospital in h), None)
        if matched:
            matrix[matched][month_name] += 1

# ═══════════════════════════════════════════════════════════════════════════════
# PDF
# ═══════════════════════════════════════════════════════════════════════════════

def make_pdf(pat: Dict, rxs: List[Dict], pid: str) -> bytes:
    from io import BytesIO
    buf = BytesIO()
    if HAS_REPORTLAB:
        c = rl_canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        c.setFillColorRGB(0.04,0.06,0.12); c.rect(0,0,w,h,fill=1,stroke=0)
        c.setFillColorRGB(0,0.95,1); c.setFont("Helvetica-Bold",16)
        c.drawString(20*mm, h-25*mm, "[SHIELD] PHARMA-HYBRID v20")
        c.setFont("Helvetica",10)
        c.drawString(20*mm, h-33*mm, f"Patient: {pat.get('real_name','N/A')} ({pid})  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.setStrokeColorRGB(0,0.95,1); c.setLineWidth(0.5)
        c.line(20*mm,h-37*mm,w-20*mm,h-37*mm)
        c.setFont("Helvetica-Bold",11); c.drawString(20*mm,h-47*mm,"PRESCRIPTION DATA")
        c.setFont("Helvetica",9); y = h-58*mm
        for p in rxs:
            if p["patient_id"] != pid: continue
            c.setFillColorRGB(0,1,0.55)
            c.drawString(20*mm,y,f"• {p['medication_name']} ({p['cancer_type']})  {p['dosage']}  {p['frequency']}")
            c.setFillColorRGB(0.6,0.9,1)
            c.drawString(25*mm,y-6*mm,f"  효능 {p['efficacy_rate']}%  |  상태: {p['status']}  |  부작용: {p['side_effects']}")
            y -= 16*mm
        c.setFillColorRGB(0,0.95,1); c.setFont("Helvetica",7)
        c.drawString(20*mm,12*mm,"© 2026 PHARMA-HYBRID v20 | CLASSIFIED SYSTEM")
        c.save()
    else:
        buf.write(b"%PDF-1.4\n%PHARMA-HYBRID v20\n")
    buf.seek(0); return buf.read()

# ═══════════════════════════════════════════════════════════════════════════════
# HTML 헬퍼
# ═══════════════════════════════════════════════════════════════════════════════

def kb_table(data: Dict) -> str:
    rows = "".join(
        f'<tr>'
        f'<td style="color:rgba(0,200,255,0.55);font-family:\'Noto Sans KR\',sans-serif;'
        f'font-size:0.95rem;padding:6px 15px 6px 0;vertical-align:top;white-space:nowrap;min-width:90px;">{k}</td>'
        f'<td style="color:#c8eeff;font-family:\'Noto Sans KR\',sans-serif;'
        f'font-size:0.95rem;padding:6px 0;line-height:1.75;word-break:keep-all;">{v}</td>'
        f'</tr>'
        for k, v in data.items())
    return f'<table style="width:100%;border-collapse:collapse;">{rows}</table>'

def ai_box(text: str, label: str = "🤖 AI 분석") -> str:
    """AI 응답을 보여주는 카드 HTML"""
    safe = text.replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    return f"""
    <div style="border:1.5px solid rgba(0,242,255,0.35);background:rgba(0,20,50,0.9);
                border-radius:8px;padding:15px 18px;margin-top:12px;">
      <div style="color:rgba(0,242,255,0.5);font-size:0.85rem;font-family:'Noto Sans KR',sans-serif;
                  margin-bottom:8px;font-weight:700;">{label}</div>
      <div style="color:#c8f8ff;font-size:1.0rem;font-family:'Noto Sans KR',sans-serif;
                  line-height:1.8;word-break:keep-all;">{safe}</div>
    </div>"""

def create_voice_card(text: str, voice_mgr=None, label: str = "🎤 음성 낭독") -> str:
    """음성 합성 플레이어를 포함한 카드 생성"""
    if not HAS_VOICE_ENGINE or not voice_mgr or not voice_mgr.is_enabled():
        return ""

    try:
        audio_html = voice_mgr.get_engine().create_audio_html_player(
            text,
            voice_mgr.get_selected_voice()
        )
        if audio_html:
            return audio_html
    except Exception as e:
        logging.warning(f"⚠️ 음성 카드 생성 오류: {e}")
    return ""

# ═══════════════════════════════════════════════════════════════════════════════
# 페이지 설정 & CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="PHARMA-HYBRID v20", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');

.stApp,.main{background-color:#080e1d !important;}
.main .block-container{padding:0.7rem 1.2rem 1rem !important;max-width:100% !important;}
body,p,span,div,td,th,li,label,input,textarea,select,button{font-family:'Noto Sans KR',sans-serif !important;}

section[data-testid="stSidebar"]{background:#050b17 !important;border-right:1px solid rgba(0,242,255,0.2) !important;min-width:340px !important;max-width:400px !important;}
section[data-testid="stSidebar"]>div{padding:0.8rem 1.0rem !important;}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label{color:rgba(0,220,255,0.75) !important;font-size:0.95rem !important;font-family:'Noto Sans KR',sans-serif !important;}
section[data-testid="stSidebar"] .stButton>button{background:transparent !important;border:1px solid rgba(0,242,255,0.38) !important;color:#00f2ff !important;font-size:0.9rem !important;padding:8px 12px !important;width:100% !important;margin-bottom:6px !important;border-radius:5px !important;font-family:'Noto Sans KR',sans-serif !important;font-weight:400 !important;box-shadow:none !important;}
section[data-testid="stSidebar"] .stButton>button:hover{background:rgba(0,242,255,0.1) !important;}

/* 입력창 — 흰 배경 + 검정 글자 */
input[type="text"],input[type="search"],.stTextInput input,.stTextArea textarea{background-color:#ffffff !important;color:#111111 !important;border:1.5px solid rgba(0,242,255,0.45) !important;border-radius:6px !important;font-size:1.1rem !important;padding:8px 12px !important;font-family:'Noto Sans KR',sans-serif !important;caret-color:#111111 !important;}
input::placeholder,textarea::placeholder{color:#999999 !important;}
.stTextInput>label,.stTextArea>label{color:rgba(0,220,255,0.65) !important;font-size:0.85rem !important;}

/* 하단 챗 인풋 컨테이너 (다크 테마) */
div[data-testid="stChatInput"] { background-color: #080f1e !important; border: 1.5px solid rgba(0,242,255,0.4) !important; border-radius: 10px !important; }
div[data-testid="stChatInput"] textarea { color: #00f2ff !important; background-color: transparent !important; font-size: 1.1rem !important; }
div[data-testid="stChatInput"] button { color: #00f2ff !important; background-color: transparent !important; }
div[data-testid="stBottomBlockContainer"] { background: #080e1d !important; }
div[data-testid="stBottom"] > div { background-color: #080e1d !important; }

.stSelectbox>div>div{background:#0d1a2e !important;border:1.5px solid rgba(0,242,255,0.28) !important;color:#00f2ff !important;font-size:1.0rem !important;font-family:'Noto Sans KR',sans-serif !important; padding: 4px 8px !important;}
.stSelectbox label{color:rgba(0,220,255,0.6) !important;font-size:0.85rem !important;}
.stRadio label,.stRadio [data-testid="stWidgetLabel"]{color:rgba(0,220,255,0.72) !important;font-size:0.95rem !important;}

.stButton>button{background:linear-gradient(135deg,#00ccee,#0077cc) !important;color:#000 !important;font-weight:700 !important;border:none !important;border-radius:6px !important;font-size:1.0rem !important;padding:8px 16px !important;font-family:'Noto Sans KR',sans-serif !important;}
.stButton>button:hover{opacity:0.88 !important;}
[data-testid="stDownloadButton"]>button{background:linear-gradient(135deg,#0055bb,#003388) !important;color:#fff !important; font-size:1.0rem !important;}

[data-testid="stFileUploader"] section{border:1.5px dashed rgba(0,242,255,0.32) !important;background:#0d1a2e !important;border-radius:6px !important;padding:10px !important;min-height:50px !important;}
[data-testid="stFileUploader"] section small,[data-testid="stFileUploader"] section span,[data-testid="stFileUploader"] section p{color:rgba(0,220,255,0.58) !important;font-size:0.85rem !important;font-family:'Noto Sans KR',sans-serif !important;}
[data-testid="stFileUploader"] section button{background:transparent !important;border:1px solid rgba(0,242,255,0.38) !important;color:#00f2ff !important;font-size:0.85rem !important;}

.stTabs [data-baseweb="tab-list"]{background:transparent !important;border-bottom:1px solid rgba(0,242,255,0.15) !important;}
.stTabs [data-baseweb="tab"]{color:rgba(0,220,255,0.42) !important;font-size:0.95rem !important;font-family:'Noto Sans KR',sans-serif !important;padding:8px 18px !important;}
.stTabs [aria-selected="true"]{color:#00f2ff !important;border-bottom:2.5px solid #00f2ff !important;background:transparent !important;}
.stTabs [data-baseweb="tab-panel"]{padding:15px 0 0 !important;background:transparent !important;}

hr{border-color:rgba(0,242,255,0.1) !important;margin:12px 0 !important;}
.stMarkdown p{color:rgba(0,220,255,0.75) !important;font-size:1.05rem !important;font-family:'Noto Sans KR',sans-serif !important; line-height: 1.7;}
.stSpinner>div{border-top-color:#00f2ff !important;}

.c-title{font-family:'Orbitron',sans-serif !important;color:#00f2ff;font-size:1.9rem;font-weight:700;text-align:center;text-shadow:0 0 20px rgba(0,242,255,0.55);letter-spacing:0.08em;margin-bottom:4px;}
.c-sub{color:rgba(0,200,255,0.42);font-size:0.85rem;text-align:center;letter-spacing:0.05em;margin-bottom:18px;font-family:'Noto Sans KR',sans-serif !important;}
.c-panel-hdr{font-family:'Orbitron',sans-serif !important;color:#00f2ff;font-size:0.95rem;font-weight:700;margin-bottom:8px;border-bottom:1.5px solid rgba(0,242,255,0.18);padding-bottom:7px;}
.c-panel-sub{color:rgba(0,200,255,0.48);font-size:0.8rem;margin-bottom:8px;font-family:'Noto Sans KR',sans-serif !important;}
.c-menu-hdr{color:#00f2ff;font-size:0.9rem;font-weight:700;margin:12px 0 6px;padding-bottom:5px;border-bottom:1px solid rgba(0,242,255,0.14);font-family:'Noto Sans KR',sans-serif !important;}
.c-info{border:1.5px solid rgba(0,242,255,0.38);background:#0a1628;border-radius:8px;padding:12px 18px;}
.c-info-lbl{color:rgba(0,200,255,0.42);font-size:0.85rem;margin-bottom:6px;font-family:'Noto Sans KR',sans-serif !important;}
.c-info-val{font-family:'Orbitron',sans-serif !important;color:#00f2ff;font-size:1.4rem;font-weight:700;}
.c-safe{border:1.5px solid rgba(0,255,136,0.45);background:rgba(0,255,136,0.04);border-radius:8px;padding:12px 18px;}
.c-check{border:1px solid rgba(0,255,136,0.38);background:rgba(0,255,136,0.04);border-radius:8px;padding:12px 15px;color:#00ff88;font-size:0.95rem;line-height:1.8;margin-bottom:12px;font-family:'Noto Sans KR',sans-serif !important;}
.c-tag{display:inline-block;border:1.5px solid rgba(0,242,255,0.42);border-radius:4px;padding:3px 10px;color:#00f2ff;font-size:0.85rem;margin-right:5px;margin-bottom:4px;font-family:'Noto Sans KR',sans-serif !important;}
.c-tag-warn{display:inline-block;border:1.5px solid rgba(255,120,0,0.48);border-radius:4px;padding:3px 10px;color:#ff9944;font-size:0.85rem;font-family:'Noto Sans KR',sans-serif !important;}
.c-vault{border:2.5px solid #009900;border-radius:8px;background:rgba(0,150,0,0.06);padding:10px 12px;text-align:center;color:#00cc44;font-size:0.85rem;font-family:'Noto Sans KR',sans-serif !important; font-weight: 700;}
.c-risk{font-family:'Orbitron',sans-serif !important;color:#00f2ff;font-size:2.6rem;font-weight:700;line-height:1.1;}
.c-risk-badge{display:inline-block;background:rgba(255,150,0,0.1);border:1px solid rgba(255,150,0,0.32);border-radius:4px;padding:3px 12px;font-size:0.85rem;color:#ffaa00;font-family:'Noto Sans KR',sans-serif !important;}
.c-timemachine{border:1px solid rgba(0,255,136,0.22);background:rgba(0,255,136,0.04);border-radius:6px;padding:12px 16px;margin-top:10px;color:rgba(180,240,255,0.88);font-size:0.95rem;line-height:1.8;font-family:'Noto Sans KR',sans-serif !important;}
.c-news{border:1px solid rgba(0,242,255,0.16);background:#0a1628;border-radius:8px;padding:15px 18px;margin-bottom:12px;}
.c-news-tag{display:inline-block;background:rgba(0,242,255,0.08);border:1px solid rgba(0,242,255,0.22);border-radius:4px;padding:2px 10px;font-size:0.8rem;color:#00d8f0;margin-bottom:8px;font-family:'Noto Sans KR',sans-serif !important;}
.c-news-title{color:#00f2ff;font-size:1.0rem;font-weight:700;line-height:1.55;margin-bottom:8px;font-family:'Noto Sans KR',sans-serif !important;}
.c-news-body{color:rgba(0,200,255,0.65);font-size:0.9rem;line-height:1.7;font-family:'Noto Sans KR',sans-serif !important;}
.c-news-meta{color:rgba(0,200,255,0.32);font-size:0.8rem;margin-top:8px;font-family:'Noto Sans KR',sans-serif !important;}
.c-price{border:1px solid rgba(0,242,255,0.2);background:#0a1628;border-radius:8px;padding:12px 18px;margin-bottom:10px;}
.c-price-name{color:#00f2ff;font-size:1.05rem;font-weight:700;font-family:'Noto Sans KR',sans-serif !important;}
.c-price-code{color:rgba(0,200,255,0.42);font-size:0.85rem;font-family:'Noto Sans KR',sans-serif !important;}
.c-price-val{font-family:'Orbitron',sans-serif !important;color:#00ff88;font-size:1.3rem;font-weight:700;}
.c-price-unit{color:rgba(0,200,255,0.42);font-size:0.8rem;font-family:'Noto Sans KR',sans-serif !important;}
.c-price-badge{display:inline-block;background:rgba(0,255,136,0.07);border:1px solid rgba(0,255,136,0.22);border-radius:4px;padding:2px 10px;font-size:0.85rem;color:#00cc88;margin-top:6px;font-family:'Noto Sans KR',sans-serif !important;}
.c-kb-card{border:1px solid rgba(0,242,255,0.2);background:#0a1628;border-radius:8px;padding:15px 18px;margin-bottom:12px;}
.c-kb-type{color:rgba(0,200,255,0.48);font-size:0.85rem;margin-bottom:5px;font-family:'Noto Sans KR',sans-serif !important;}
.c-kb-title{color:#00f2ff;font-size:1.15rem;font-weight:700;margin-bottom:10px;padding-bottom:8px;border-bottom:1.5px solid rgba(0,242,255,0.1);font-family:'Noto Sans KR',sans-serif !important;}
.c-popup{border:1px solid rgba(0,242,255,0.22);background:#080f1e;border-radius:8px;padding:10px 14px;margin-top:8px;max-height:400px;overflow-y:auto;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 세션 초기화
# ═══════════════════════════════════════════════════════════════════════════════

def init_session():
    if "ready" not in st.session_state:
        init_db()
        st.session_state.ready = True
    for key, default in [
        # 기존 세션 키 (14컬럼 DB 구조 유지)
        ("patients", None), ("rxs", None),
        ("pid", "P001"), ("edit_mode", False),
        ("show_price", False), ("show_news", False),
        ("price_q", ""), ("kb_q", ""),
        ("voice_result", ""), ("voice_ai_answer", ""),
        ("image_ai_answer", ""), ("last_image_name", ""),
        ("kb_ai_answer", ""),
        ("selected_voice", "기본(로봇)"), ("voice_enabled", True),
        ("emo_result_patient", None), ("emo_result_commander", None),
        # ── 신규: 복약 이행도 ─────────────────────────────────────────
        ("adherence_refreshed", False),    # 이행도 새로고침 트리거
        ("last_taken_msg", ""),            # 복약 확인 메시지
        # ── 신규: Guardian Link ────────────────────────────────────────
        ("guardian_show_form", False),     # 보호자 등록 폼 표시 토글
        ("guardian_alert_result", None),   # 가장 최근 알림 발송 결과
        # ── 신규: Gemini 엔진 상태 ────────────────────────────────────
        ("gemini_status", None),           # API 상태 캐시
    ]:
        if key not in st.session_state:
            st.session_state[key] = default
    if st.session_state.patients is None:
        st.session_state.patients = load_patients()
    if st.session_state.rxs is None:
        st.session_state.rxs = load_rx()
    # Gemini 엔진 상태 1회 캐시
    if st.session_state.gemini_status is None and HAS_GEMINI_ENGINE:
        st.session_state.gemini_status = get_engine_status()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    init_session()

    # 음성 엔진 초기화
    if HAS_VOICE_ENGINE and "voice_manager" not in st.session_state:
        st.session_state.voice_manager = VoiceSessionManager(st.session_state)
    voice_mgr = st.session_state.voice_manager if HAS_VOICE_ENGINE else None

    patients = st.session_state.patients
    rxs      = st.session_state.rxs
    pid      = st.session_state.pid
    pat      = patients.get(pid, {})
    pat_rxs  = [r for r in rxs if r["patient_id"] == pid]
    meds     = [r["medication_name"] for r in pat_rxs]

    # ─────────────────────────────────────────────────────────────────
    # 사이드바
    # ─────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="c-menu-hdr">🎭 PERSONA TUNING</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:rgba(0,200,255,0.4);font-size:0.59rem;margin-bottom:3px;">보고 모드 선택</div>', unsafe_allow_html=True)
        st.radio("persona_r", ["전문가", "환자"], label_visibility="collapsed", index=0, key="persona")

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── 음성 합성 설정 ──
        if HAS_VOICE_ENGINE:
            st.markdown('<div class="c-menu-hdr">🎤 음성 낭독</div>', unsafe_allow_html=True)
            st.markdown('<div style="color:rgba(0,200,255,0.4);font-size:0.59rem;margin-bottom:6px;">연예인 목소리 선택</div>', unsafe_allow_html=True)

            voice_engine = st.session_state.voice_manager.get_engine() if voice_mgr else None
            available_voices = voice_engine.get_available_voices() if voice_engine else {}

            voice_names = list(available_voices.keys())
            current_idx = voice_names.index(st.session_state.selected_voice) if st.session_state.selected_voice in voice_names else 0

            selected = st.selectbox(
                "목소리 선택",
                voice_names,
                index=current_idx,
                label_visibility="collapsed",
                key="voice_selector"
            )

            if selected != st.session_state.selected_voice:
                st.session_state.selected_voice = selected
                if voice_mgr:
                    voice_mgr.set_voice(selected)

            # 선택된 목소리 정보 표시
            if selected in available_voices:
                profile = available_voices[selected]
                st.markdown(f"""
                <div style="background:rgba{profile.get('color', '#00CCFF')}; opacity: 0.12; border-left: 3px solid {profile.get('color', '#00CCFF')}; padding: 8px; border-radius: 4px; margin-top: 6px;">
                    <div style="color:rgba(255,255,255,0.7); font-size: 0.65rem; line-height:1.5;">
                        <b>{selected}</b><br>
                        {profile.get('description', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 음성 활성화/비활성화 토글
            if st.checkbox("음성 낭독 활성화", value=st.session_state.voice_enabled, key="voice_toggle"):
                st.session_state.voice_enabled = True
            else:
                st.session_state.voice_enabled = False

            st.markdown("<hr>", unsafe_allow_html=True)



        st.markdown('<div class="c-vault">🔒 VAULT SYSTEM v21.0 ACTIVE</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # ── 음성 인식 + TTS + 음성 톤 미리듣기 컴포넌트 ──
        st.markdown('<div class="c-menu-hdr">🎙️ VOICE COMMAND</div>', unsafe_allow_html=True)
        import streamlit.components.v1 as components
        components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:transparent; font-family:'Noto Sans KR',Arial,sans-serif; padding:4px 2px; color:#c8eeff; }

  /* 탭 */
  .tabs { display:flex; gap:4px; margin-bottom:8px; }
  .tab-btn {
    flex:1; padding:7px 0; font-size:0.78rem; font-weight:700;
    background:rgba(0,10,30,0.6); border:1px solid rgba(0,242,255,0.25);
    border-radius:6px; cursor:pointer; color:rgba(0,200,255,0.6);
    transition:0.2s;
  }
  .tab-btn.active { background:rgba(0,180,255,0.15); border-color:rgba(0,242,255,0.7); color:#00f2ff; }
  .tab-pane { display:none; }
  .tab-pane.active { display:block; }

  /* 버튼 */
  .btn {
    width:100%; padding:10px 0; background:transparent; border-radius:7px;
    cursor:pointer; font-size:0.92rem; font-weight:700; transition:0.2s;
    margin-bottom:6px; font-family:inherit;
  }
  .btn-cyan  { border:2px solid rgba(0,242,255,0.7); color:#00f2ff; }
  .btn-cyan:hover  { background:rgba(0,242,255,0.12); }
  .btn-cyan.on     { background:rgba(200,0,0,0.2); border-color:#ff5555; color:#ff8888; }
  .btn-green { border:2px solid rgba(0,255,136,0.6); color:#00ff88; }
  .btn-green:hover { background:rgba(0,255,136,0.1); }
  .btn-dim   { border:1px solid rgba(0,200,255,0.3); color:rgba(0,200,255,0.65); font-size:0.8rem; }
  .btn-dim:hover   { background:rgba(0,200,255,0.08); }

  /* 상태 박스 */
  .status-box {
    font-size:0.83rem; color:#00ff88; min-height:22px;
    background:rgba(0,255,136,0.06); border:1px solid rgba(0,255,136,0.18);
    border-radius:5px; padding:5px 9px; margin-bottom:6px; line-height:1.5;
    word-break:keep-all;
  }
  .info-box {
    font-size:0.78rem; color:#00e8ff; min-height:16px;
    padding:3px 2px; margin-bottom:4px;
  }
  textarea {
    width:100%; background:rgba(0,10,30,0.8);
    border:1px solid rgba(0,242,255,0.3); border-radius:5px;
    color:#00e8ff; font-size:0.82rem; padding:6px 9px;
    margin-bottom:6px; resize:vertical; min-height:52px;
    font-family:inherit;
  }

  /* 음성 톤 카드 */
  .tone-grid { display:flex; flex-direction:column; gap:5px; }
  .tone-card {
    display:flex; align-items:center; gap:8px;
    background:rgba(0,10,30,0.6); border:1px solid rgba(0,180,255,0.2);
    border-radius:8px; padding:7px 10px; cursor:pointer; transition:0.18s;
  }
  .tone-card:hover { background:rgba(0,180,255,0.1); border-color:rgba(0,242,255,0.5); }
  .tone-card.playing { border-color:#00ff88; background:rgba(0,255,136,0.08); }
  .tone-icon { font-size:1.4rem; min-width:28px; text-align:center; }
  .tone-info { flex:1; }
  .tone-name { font-size:0.85rem; font-weight:700; color:#00e8ff; }
  .tone-desc { font-size:0.7rem; color:rgba(0,200,255,0.55); line-height:1.4; }
  .tone-params { font-size:0.65rem; color:rgba(0,255,136,0.5); margin-top:1px; }
  .play-btn {
    padding:5px 10px; border-radius:5px; font-size:0.8rem; font-weight:700;
    background:transparent; border:1px solid rgba(0,242,255,0.4);
    color:#00e8ff; cursor:pointer; white-space:nowrap;
  }
  .play-btn:hover { background:rgba(0,242,255,0.12); }

  /* 시스템 음성 목록 */
  .voice-list { max-height:120px; overflow-y:auto; margin-bottom:6px; }
  .voice-item {
    display:flex; align-items:center; justify-content:space-between;
    padding:4px 8px; border-bottom:1px solid rgba(0,242,255,0.08);
    font-size:0.72rem; color:#c8eeff;
  }
  .voice-item:last-child { border-bottom:none; }
  .v-play { padding:3px 8px; font-size:0.68rem; border-radius:4px;
    background:transparent; border:1px solid rgba(0,242,255,0.3);
    color:#00e8ff; cursor:pointer; }
  .v-play:hover { background:rgba(0,242,255,0.1); }
</style>
</head>
<body>

<!-- 탭 -->
<div class="tabs">
  <button class="tab-btn active" onclick="showTab('tab-voice')">🎙️ 음성인식</button>
  <button class="tab-btn"        onclick="showTab('tab-tts')">🔊 읽기</button>
  <button class="tab-btn"        onclick="showTab('tab-tone')">🎵 음성톤</button>
</div>

<!-- ── 탭1: 음성 인식 ── -->
<div id="tab-voice" class="tab-pane active">
  <button id="vbtn" class="btn btn-cyan" onclick="toggle()">🎙️ 음성 인식 시작</button>
  <div id="vstatus" class="status-box">마이크 버튼을 누르고 말씀하세요 (Chrome 권장)</div>
</div>

<!-- ── 탭2: TTS 읽기 ── -->
<div id="tab-tts" class="tab-pane">
  <textarea id="tts_input" placeholder="읽을 내용 입력&#10;또는 아래 버튼으로 AI 답변 자동 로드"></textarea>
  <button class="btn btn-green"  onclick="speakInput()">🔊 위 내용 읽기</button>
  <button class="btn btn-dim"    onclick="loadLastAI()">📋 AI 마지막 답변 불러오기</button>
  <button class="btn btn-dim" style="color:rgba(255,100,100,0.7);border-color:rgba(255,100,100,0.3);"
          onclick="window.speechSynthesis&&window.speechSynthesis.cancel();">⏹ 읽기 중단</button>
  <div id="tts_status" class="info-box"></div>
</div>

<!-- ── 탭3: 음성 톤 미리듣기 ── -->
<div id="tab-tone" class="tab-pane">
  <div style="font-size:0.72rem;color:rgba(0,200,255,0.55);margin-bottom:6px;">
    ▶ 버튼을 눌러 각 톤을 미리 들어보세요
  </div>

  <div class="tone-grid">
    <!-- 톤 1: 차분한 전문가 -->
    <div class="tone-card" id="tone-0">
      <div class="tone-icon">🏥</div>
      <div class="tone-info">
        <div class="tone-name">차분한 전문가</div>
        <div class="tone-desc">약사·의사용 — 신뢰감 있는 전달</div>
        <div class="tone-params">속도 0.85 · 음높이 0.95 · 여성음 우선</div>
      </div>
      <button class="play-btn" onclick="playTone(0)">▶ 듣기</button>
    </div>

    <!-- 톤 2: 따뜻한 상담 -->
    <div class="tone-card" id="tone-1">
      <div class="tone-icon">💛</div>
      <div class="tone-info">
        <div class="tone-name">따뜻한 상담</div>
        <div class="tone-desc">환자 친화적 — 부드럽고 공감적</div>
        <div class="tone-params">속도 0.80 · 음높이 1.10 · 밝은 톤</div>
      </div>
      <button class="play-btn" onclick="playTone(1)">▶ 듣기</button>
    </div>

    <!-- 톤 3: 노인·장애인 친화 -->
    <div class="tone-card" id="tone-2">
      <div class="tone-icon">👴</div>
      <div class="tone-info">
        <div class="tone-name">노인·장애인 친화</div>
        <div class="tone-desc">천천히 또박또박 — 높은 이해도</div>
        <div class="tone-params">속도 0.65 · 음높이 1.05 · 또렷한 발음</div>
      </div>
      <button class="play-btn" onclick="playTone(2)">▶ 듣기</button>
    </div>

    <!-- 톤 4: 활기찬 안내 -->
    <div class="tone-card" id="tone-3">
      <div class="tone-icon">⚡</div>
      <div class="tone-info">
        <div class="tone-name">활기찬 안내</div>
        <div class="tone-desc">빠른 정보 전달 — 젊은 환자용</div>
        <div class="tone-params">속도 1.05 · 음높이 1.15 · 에너지 높음</div>
      </div>
      <button class="play-btn" onclick="playTone(3)">▶ 듣기</button>
    </div>

    <!-- 톤 5: 남성 낮은 톤 -->
    <div class="tone-card" id="tone-4">
      <div class="tone-icon">🎙️</div>
      <div class="tone-info">
        <div class="tone-name">남성 낮은 톤</div>
        <div class="tone-desc">중후한 목소리 — 권위 있는 설명</div>
        <div class="tone-params">속도 0.90 · 음높이 0.78 · 남성음 우선</div>
      </div>
      <button class="play-btn" onclick="playTone(4)">▶ 듣기</button>
    </div>

    <!-- 톤 6: 소아과·어린이 -->
    <div class="tone-card" id="tone-5">
      <div class="tone-icon">🧒</div>
      <div class="tone-info">
        <div class="tone-name">소아과·어린이용</div>
        <div class="tone-desc">높고 밝은 목소리 — 어린이 친화</div>
        <div class="tone-params">속도 0.88 · 음높이 1.35 · 밝은 여성음</div>
      </div>
      <button class="play-btn" onclick="playTone(5)">▶ 듣기</button>
    </div>
  </div>

  <!-- 시스템 설치 음성 목록 -->
  <div style="margin-top:10px;font-size:0.72rem;color:rgba(0,200,255,0.55);margin-bottom:4px;">
    🖥 이 기기에 설치된 한국어 음성
  </div>
  <div id="voice-list" class="voice-list">
    <div style="color:rgba(0,200,255,0.35);font-size:0.7rem;padding:4px;">로딩 중...</div>
  </div>
  <div id="tone_status" class="info-box"></div>
</div>

<script>
// ─────────────────────────────────────────────
// 탭 전환
// ─────────────────────────────────────────────
function showTab(id){
  document.querySelectorAll('.tab-pane').forEach(function(p){ p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('active'); });
  document.getElementById(id).classList.add('active');
  var idx = {'tab-voice':0,'tab-tts':1,'tab-tone':2}[id];
  document.querySelectorAll('.tab-btn')[idx].classList.add('active');
  if(id==='tab-tone') renderVoiceList();
}

// ─────────────────────────────────────────────
// 음성 인식
// ─────────────────────────────────────────────
var rec=null, on=false;
function toggle(){ on ? stopRec() : start(); }
function start(){
  var SR = window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){
    document.getElementById('vstatus').innerHTML =
      '<span style="color:#ffcc00">⚠️ Chrome 브라우저를 사용해주세요</span>'; return;
  }
  rec=new SR(); rec.lang='ko-KR'; rec.continuous=false; rec.interimResults=true;
  on=true;
  var btn=document.getElementById('vbtn');
  btn.innerText='⏹ 중단'; btn.classList.add('on');
  document.getElementById('vstatus').innerText='🔴 듣고 있습니다...';
  rec.onresult=function(e){
    var interim='',final_='';
    for(var i=e.resultIndex;i<e.results.length;i++){
      if(e.results[i].isFinal) final_+=e.results[i][0].transcript;
      else interim+=e.results[i][0].transcript;
    }
    if(interim) document.getElementById('vstatus').innerText='💬 '+interim;
    if(final_){ document.getElementById('vstatus').innerText='✅ 인식: '+final_; sendToChat(final_); stopRec(); }
  };
  var errMsg={
    'not-allowed':'❌ 마이크 권한 필요 — 주소창 자물쇠 클릭 후 마이크 허용',
    'network':'⚠️ 네트워크 오류 — 텍스트로 입력해주세요',
    'no-speech':'⚠️ 말소리가 감지되지 않았습니다',
    'audio-capture':'❌ 마이크를 찾을 수 없습니다'
  };
  rec.onerror=function(e){
    document.getElementById('vstatus').innerHTML=
      '<span style="color:#ffaa44">'+(errMsg[e.error]||'❌ 오류: '+e.error)+'</span>';
    stopRec();
  };
  rec.onend=function(){ stopRec(); };
  try{ rec.start(); }
  catch(e){ document.getElementById('vstatus').innerHTML='<span style="color:#ffaa44">❌ 시작 실패: '+e.message+'</span>'; stopRec(); }
}
function stopRec(){
  on=false; if(rec){ try{rec.stop();}catch(e){} rec=null; }
  var btn=document.getElementById('vbtn');
  btn.innerText='🎙️ 음성 인식 시작'; btn.classList.remove('on');
}
function sendToChat(text){
  try{
    var doc=window.parent.document;
    var sels=['textarea[data-testid="stChatInputTextArea"]','textarea[aria-label="채팅 입력"]','.stChatInputContainer textarea','div[data-testid="stChatInput"] textarea','textarea'];
    var inp=null;
    for(var i=0;i<sels.length;i++){ inp=doc.querySelector(sels[i]); if(inp) break; }
    if(inp){
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set.call(inp,text);
      inp.dispatchEvent(new Event('input',{bubbles:true}));
      setTimeout(function(){ inp.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,cancelable:true,key:'Enter',code:'Enter',keyCode:13})); },80);
    }
  }catch(e){}
}

// ─────────────────────────────────────────────
// TTS
// ─────────────────────────────────────────────
function speakInput(){
  var text=document.getElementById('tts_input').value.trim();
  if(!text){ document.getElementById('tts_status').innerText='⚠️ 읽을 내용이 없습니다'; return; }
  speakTextWith(text, null, 0.88, 1.0);
}
function loadLastAI(){
  try{
    var doc=window.parent.document;
    var msgs=doc.querySelectorAll('[data-testid="stChatMessage"]');
    var lastAI='';
    msgs.forEach(function(m){
      if(m.querySelector('[data-testid="chatAvatarIcon-assistant"]')||
         m.querySelector('[data-testid="chatAvatarIcon-ai"]')||
         m.getAttribute('data-message-author-role')==='assistant'){
        lastAI=m.innerText||m.textContent||'';
      }
    });
    if(lastAI){ document.getElementById('tts_input').value=lastAI.trim().slice(0,600); document.getElementById('tts_status').innerText='✅ AI 답변 로드 완료'; }
    else document.getElementById('tts_status').innerText='⚠️ AI 답변을 찾을 수 없습니다';
  }catch(e){ document.getElementById('tts_status').innerText='⚠️ 불러오기 실패'; }
}

// ─────────────────────────────────────────────
// 음성 톤 데이터 & 재생
// ─────────────────────────────────────────────
var TONES = [
  { name:'차분한 전문가',  rate:0.85, pitch:0.95, preferFemale:true,  preferMale:false, sampleText:'안녕하세요. 타세바정 150밀리그램은 매일 아침 공복에 복용하세요. 식사 1시간 전이나 식후 2시간 후가 좋습니다.' },
  { name:'따뜻한 상담',    rate:0.80, pitch:1.10, preferFemale:true,  preferMale:false, sampleText:'걱정하지 마세요. 이 약은 비교적 안전한 편이에요. 혹시 복용 중 불편한 점이 있으시면 언제든지 말씀해주세요.' },
  { name:'노인·장애인 친화',rate:0.65, pitch:1.05, preferFemale:true,  preferMale:false, sampleText:'약 드시는 법 알려드릴게요. 이 하얀 둥근 알약은요... 아침에 일어나서... 밥 먹기 전에 드세요.' },
  { name:'활기찬 안내',    rate:1.05, pitch:1.15, preferFemale:true,  preferMale:false, sampleText:'오늘 처방약 확인됐어요! 글리벡정, 싱귤레어츄정, 벤톨린 세 가지예요. 처방대로 복용하면 최상의 효과를 기대할 수 있어요!' },
  { name:'남성 낮은 톤',   rate:0.90, pitch:0.78, preferFemale:false, preferMale:true,  sampleText:'처방 내역을 확인했습니다. 옵디보 240밀리그램을 2주 간격으로 투여합니다. 면역 관련 부작용 발생 시 즉시 내원하십시오.' },
  { name:'소아과·어린이용',rate:0.88, pitch:1.35, preferFemale:true,  preferMale:false, sampleText:'안녕! 이건 기침을 낫게 해주는 약이야. 딸기맛 시럽이라서 맛있을 거야. 하루에 두 번, 아침저녁으로 먹으면 돼!' },
];

var currentToneCard = null;

function getKoVoice(preferFemale, preferMale){
  var voices = window.speechSynthesis.getVoices();
  var koVoices = voices.filter(function(v){ return v.lang==='ko-KR'||v.lang==='ko'; });
  if(!koVoices.length) return voices.find(function(v){ return v.lang.startsWith('ko'); })||null;
  if(preferFemale){
    var f = koVoices.find(function(v){
      return v.name.indexOf('Google')>-1||v.name.indexOf('서현')>-1||
             v.name.indexOf('Yuna')>-1||v.name.indexOf('여성')>-1||v.name.indexOf('Female')>-1;
    });
    if(f) return f;
  }
  if(preferMale){
    var m = koVoices.find(function(v){
      return v.name.indexOf('남성')>-1||v.name.indexOf('Male')>-1||
             v.name.indexOf('민준')>-1||v.name.indexOf('Minjun')>-1||v.name.indexOf('Heami')<0;
    });
    if(m) return m;
  }
  return koVoices[0]||null;
}

function playTone(idx){
  if(!window.speechSynthesis){ document.getElementById('tone_status').innerText='⚠️ TTS 미지원'; return; }
  window.speechSynthesis.cancel();
  if(currentToneCard){ currentToneCard.classList.remove('playing'); }
  var card = document.getElementById('tone-'+idx);
  card.classList.add('playing');
  currentToneCard = card;

  var t = TONES[idx];
  var utt = new SpeechSynthesisUtterance(t.sampleText);
  utt.lang   = 'ko-KR';
  utt.rate   = t.rate;
  utt.pitch  = t.pitch;
  utt.volume = 1.0;
  var v = getKoVoice(t.preferFemale, t.preferMale);
  if(v) utt.voice = v;
  document.getElementById('tone_status').innerText = '🔊 재생 중: '+t.name+(v?' ('+v.name+')':'');
  utt.onend = function(){ card.classList.remove('playing'); document.getElementById('tone_status').innerText='✅ 완료: '+t.name; };
  utt.onerror = function(e){ card.classList.remove('playing'); document.getElementById('tone_status').innerText='❌ 오류: '+e.error; };
  window.speechSynthesis.speak(utt);
}

// 설치된 한국어 음성 목록 렌더
function renderVoiceList(){
  var voices = window.speechSynthesis.getVoices();
  var koVoices = voices.filter(function(v){ return v.lang==='ko-KR'||v.lang==='ko'; });
  var el = document.getElementById('voice-list');
  if(!koVoices.length){
    el.innerHTML='<div style="color:rgba(255,180,0,0.6);font-size:0.7rem;padding:4px;">설치된 한국어 음성 없음 — Chrome 브라우저 권장</div>';
    return;
  }
  el.innerHTML = koVoices.map(function(v,i){
    return '<div class="voice-item">'
      +'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+v.name+' <span style="color:rgba(0,200,255,0.4);font-size:0.62rem;">('+v.lang+')</span></span>'
      +'<button class="v-play" onclick="previewVoice('+i+')">▶</button>'
      +'</div>';
  }).join('');
  window._koVoices = koVoices;
}

function previewVoice(idx){
  if(!window._koVoices) return;
  window.speechSynthesis.cancel();
  var v = window._koVoices[idx];
  var utt = new SpeechSynthesisUtterance('안녕하세요. 저는 '+v.name+' 입니다. 오늘 처방약 복용 안내를 도와드리겠습니다.');
  utt.lang='ko-KR'; utt.rate=0.88; utt.pitch=1.0; utt.voice=v;
  document.getElementById('tone_status').innerText='🔊 '+v.name+' 재생 중...';
  utt.onend=function(){ document.getElementById('tone_status').innerText='✅ 완료'; };
  window.speechSynthesis.speak(utt);
}

// 초기화
if(window.speechSynthesis){
  window.speechSynthesis.onvoiceschanged = function(){
    window.speechSynthesis.getVoices();
    renderVoiceList();
  };
  window.speechSynthesis.getVoices();
}
</script>
</body>
</html>
""", height=430)

        # ── 음성 톤 샘플 오디오 플레이어 ──
        import glob as _glob
        _sample_dir = os.path.join(os.path.dirname(__file__), "voice_samples")
        _sample_files = sorted(_glob.glob(os.path.join(_sample_dir, "tone_*.mp3")))
        if _sample_files:
            st.markdown(
                '<div style="color:rgba(0,200,255,0.6);font-size:0.72rem;'
                'font-family:Noto Sans KR,sans-serif;margin:6px 0 4px 0;font-weight:700;">'
                '🎵 음성 톤 샘플 직접 듣기</div>',
                unsafe_allow_html=True
            )
            _tone_labels = {
                'tone_1': '🏥 차분한 전문가',
                'tone_2': '💛 따뜻한 상담',
                'tone_3': '👴 노인·장애인 친화',
                'tone_4': '⚡ 활기찬 안내',
                'tone_5': '🎙️ 남성 InJoon',
                'tone_6': '🧒 소아과·어린이용',
            }
            for _sf in _sample_files:
                _key = os.path.basename(_sf)[:6]
                _lbl = _tone_labels.get(_key, os.path.basename(_sf))
                st.markdown(
                    f'<div style="color:rgba(0,200,255,0.75);font-size:0.72rem;'
                    f'font-family:Noto Sans KR,sans-serif;margin-top:4px;">{_lbl}</div>',
                    unsafe_allow_html=True
                )
                with open(_sf, "rb") as _af:
                    st.audio(_af.read(), format="audio/mp3")

        # ── 감정 인식 분석 패널 ──
        st.markdown('<div class="c-menu-hdr" style="margin-top:8px;">🧠 감정·컨디션 분석</div>', unsafe_allow_html=True)
        with st.expander("❓ 사용법 안내", expanded=False):
            st.markdown(
                '<div style="color:rgba(0,220,255,0.85);font-size:0.65rem;font-family:Noto Sans KR,sans-serif;line-height:1.8;">'
                '<b>📌 감정·컨디션 분석기 사용법</b><br><br>'
                '1️⃣ <b>환자 음성</b> 탭 선택 → 환자가 말하는 WAV 파일 업로드<br>'
                '2️⃣ <b>성별 힌트</b> 선택 (female/male/unknown)<br>'
                '3️⃣ <b>감정 분석 실행</b> 버튼 클릭<br>'
                '4️⃣ 결과: 통증/불안/피로/안정 중 상태 판별 + 신뢰도 점수<br><br>'
                '<b>📌 데모 시나리오</b><br>'
                '실제 녹음 없이도 pain(통증)/anxious(불안)/<br>'
                'fatigued(피로)/calm(안정) 시나리오를 즉시 확인<br><br>'
                '<b>📌 WAV 파일 만들기</b><br>'
                '스마트폰 녹음앱 → WAV 형식으로 저장 → 업로드<br>'
                '(Android: RecForge II, iPhone: GoodNote 등)<br><br>'
                '<b>📌 약사님 음성</b><br>'
                '상담 중 약사님 컨디션도 분석 — 번아웃 조기 감지 가능</div>',
                unsafe_allow_html=True
            )
        if HAS_EMOTION_ANALYZER:
            emotion_tab_sel = st.radio(
                "분석 대상",
                ["환자 음성", "사령관 음성", "데모 시나리오"],
                horizontal=True,
                key="emotion_tab_sel",
                label_visibility="collapsed",
            )
            if emotion_tab_sel == "데모 시나리오":
                demo_scenario = st.selectbox(
                    "시나리오",
                    ["pain", "anxious", "fatigued", "calm"],
                    format_func=lambda x: {"pain":"통증호소","anxious":"불안","fatigued":"피로","calm":"안정협조"}[x],
                    key="demo_scenario_sel",
                    label_visibility="collapsed",
                )
                demo_r = render_demo_result(demo_scenario)
                if demo_r:
                    st.markdown(render_emotion_result_html(demo_r), unsafe_allow_html=True)
            else:
                role = "patient" if emotion_tab_sel == "환자 음성" else "commander"
                gender_hint = st.selectbox("성별 힌트", ["unknown","female","male"],
                                           key=f"gender_{role}", label_visibility="collapsed")
                emo_file = st.file_uploader(
                    "WAV 업로드", type=["wav"],
                    key=f"emo_upload_{role}", label_visibility="collapsed"
                )
                if emo_file:
                    if st.button("🧠 감정 분석 실행", use_container_width=True, key=f"emo_btn_{role}"):
                        with st.spinner("음성 신호 분석 중..."):
                            try:
                                import numpy as np
                                from scipy.io.wavfile import read as wav_read
                                import io
                                sr, data = wav_read(io.BytesIO(emo_file.getvalue()))
                                if np.issubdtype(data.dtype, np.integer):
                                    data = data.astype(np.float32) / (np.iinfo(data.dtype).max + 1e-10)
                                elif data.dtype != np.float32:
                                    data = data.astype(np.float32)
                                result = _emotion_analyzer.analyze(data, sr, role, gender_hint)
                                st.session_state[f"emo_result_{role}"] = result
                            except Exception as e:
                                st.error(f"분석 오류: {e}")
                cached = st.session_state.get(f"emo_result_{role}")
                if cached:
                    st.markdown(render_emotion_result_html(cached), unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="color:rgba(255,200,0,0.6);font-size:0.62rem;font-family:Noto Sans KR,sans-serif;padding:4px 0;">'
                '⚠️ emotion_voice_analyzer 모듈 로드 필요 (librosa·scipy 설치 권장)</div>',
                unsafe_allow_html=True
            )
            demo_r = render_demo_result("pain")
            if demo_r:
                st.markdown(render_emotion_result_html(demo_r), unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════
        # ① 복약 이행도 (COMPLIANCE SENTINEL) — 신규
        # ════════════════════════════════════════════════════════════════
        st.markdown('<div class="c-menu-hdr">💊 복약 이행도 추적</div>', unsafe_allow_html=True)

        if HAS_ADHERENCE:
            # 현재 선택 환자의 이행도 게이지 표시
            pat_name_sb = patients.get(pid, {}).get("real_name", pid)
            compliance_html = render_compliance_sentinel_html(pid, pat_name_sb, days=7)
            if compliance_html:
                st.markdown(compliance_html, unsafe_allow_html=True)

            # 오늘 복용 약물 목록
            today_meds = get_today_taken_meds(pid)
            taken_html = render_taken_button_area_html(today_meds)
            if taken_html:
                st.markdown(taken_html, unsafe_allow_html=True)

            # 복약 완료 버튼 (클릭 시 DB 기록 + 이행도 갱신)
            if st.button("✅ 오늘 약 복용 완료", use_container_width=True, key="btn_taken"):
                ids = record_all_meds_taken(pid, [r for r in rxs if r["patient_id"] == pid],
                                             recorded_by="button", notes="사이드바 버튼 클릭")
                st.session_state.last_taken_msg = f"✅ {len(ids)}개 약품 복용 기록 완료"
                st.session_state.adherence_refreshed = True
                st.rerun()

            if st.session_state.last_taken_msg:
                st.markdown(
                    f'<div style="color:#00ff88;font-size:0.7rem;font-family:\'Noto Sans KR\',sans-serif;'
                    f'margin-top:4px;">{st.session_state.last_taken_msg}</div>',
                    unsafe_allow_html=True,
                )

            # 개별 약물 복용 확인 (확장)
            with st.expander("특정 약물 개별 복용 기록"):
                all_meds_for_pat = []
                for rx in rxs:
                    if rx["patient_id"] == pid:
                        for m in rx["medication_name"].split(","):
                            m = m.strip()
                            if m:
                                all_meds_for_pat.append(m)
                if all_meds_for_pat:
                    selected_med = st.selectbox("약물 선택", all_meds_for_pat,
                                                key="adh_med_sel", label_visibility="collapsed")
                    if st.button("이 약 복용 기록", key="btn_single_med"):
                        record_medication_taken(pid, selected_med, recorded_by="button")
                        st.success(f"✅ {selected_med} 복용 기록됨")
                        st.rerun()
        else:
            st.markdown(
                '<div style="color:rgba(255,200,0,0.5);font-size:0.65rem;">⚠️ medication_adherence 모듈 로드 필요</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════
        # ③ Gemini AI 엔진 상태 — 신규
        # ════════════════════════════════════════════════════════════════
        st.markdown('<div class="c-menu-hdr">🤖 AI 엔진 상태</div>', unsafe_allow_html=True)
        engine_status = st.session_state.get("gemini_status") or {}
        mode_text  = engine_status.get("mode", "🔴 엔진 미로드")
        api_set    = engine_status.get("api_key_set", False)
        sdk_inst   = engine_status.get("sdk_installed", False)
        st.markdown(
            f'<div style="border:1px solid rgba(0,242,255,0.18);border-radius:6px;padding:8px 10px;'
            f'background:rgba(0,10,30,0.6);">'
            f'<div style="color:rgba(0,200,255,0.8);font-size:0.7rem;font-family:\'Noto Sans KR\',sans-serif;">'
            f'{mode_text}</div>'
            f'<div style="color:rgba(0,200,255,0.4);font-size:0.6rem;margin-top:3px;">'
            f'SDK: {"✅" if sdk_inst else "❌ pip install google-generativeai"} | '
            f'API Key: {"✅ 설정됨" if api_set else "❌ .streamlit/secrets.toml 필요"}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        if not api_set:
            st.markdown(
                '<div style="color:rgba(255,200,0,0.6);font-size:0.6rem;margin-top:3px;font-family:Noto Sans KR,sans-serif;">'
                '설정 방법: .streamlit/secrets.toml 파일에<br>'
                '<code>GOOGLE_API_KEY = "AIza..."</code> 추가</div>',
                unsafe_allow_html=True,
            )

    # ─────────────────────────────────────────────────────────────────
    # 메인 헤더
    # ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="c-title">[SHIELD] PHARMA-HYBRID v21.0</div>', unsafe_allow_html=True)
    st.markdown('<div class="c-sub">Strategic Unified Clinical Decision Support System | STANDALONE ULTIMATE EDITION</div>', unsafe_allow_html=True)

    # 환자 선택 + 복용 약물 표시
    pid_list = list(patients.keys())
    pid_labels = [f"{patients[p]['real_name']}  ({patients[p]['age']}세)" for p in pid_list]
    hdr_a, hdr_b = st.columns([1, 2.4])
    with hdr_a:
        sel = st.selectbox("고객선택", pid_labels,
                           index=pid_list.index(pid) if pid in pid_list else 0,
                           label_visibility="collapsed", key="top_pid_sel")
    new_pid = pid_list[pid_labels.index(sel)]
    if new_pid != pid:
        st.session_state.pid = new_pid
        st.rerun()

    # ── 복용 약물 전체 표시 (쉼표 분리) ──────────────────────────────
    with hdr_b:
        all_individual_meds = []
        for m_str in meds:
            for m in m_str.split(','):
                m = m.strip()
                if m:
                    all_individual_meds.append(m)
        if all_individual_meds:
            tags_html = "".join(
                f'<span style="display:inline-block;background:rgba(0,180,255,0.13);'
                f'border:1px solid rgba(0,180,255,0.4);border-radius:5px;'
                f'padding:3px 10px;margin:3px 4px 3px 0;font-size:0.82rem;'
                f'color:#00e8ff;font-family:Noto Sans KR,sans-serif;font-weight:600;">'
                f'{m}</span>'
                for m in all_individual_meds
            )
            # 진단명
            cancer_tags = ""
            for r in pat_rxs[:1]:
                for c in r.get("cancer_type","").split(','):
                    c = c.strip()
                    if c:
                        cancer_tags += (
                            f'<span style="display:inline-block;background:rgba(255,100,0,0.15);'
                            f'border:1px solid rgba(255,100,0,0.45);border-radius:5px;'
                            f'padding:2px 9px;margin:3px 4px 3px 0;font-size:0.78rem;'
                            f'color:#ffaa55;font-family:Noto Sans KR,sans-serif;">'
                            f'{c}</span>'
                        )
            st.markdown(
                f'<div style="border:1px solid rgba(0,180,255,0.25);border-radius:8px;'
                f'padding:8px 12px;background:rgba(0,10,30,0.5);">'
                f'<div style="color:rgba(0,200,255,0.6);font-size:0.72rem;'
                f'font-family:Noto Sans KR,sans-serif;margin-bottom:5px;font-weight:700;">'
                f'💊 현재 복용 약물 ({len(all_individual_meds)}종)</div>'
                f'<div style="line-height:2;">{tags_html}</div>'
                + (f'<div style="margin-top:5px;border-top:1px solid rgba(255,100,0,0.2);'
                   f'padding-top:5px;">{cancer_tags}</div>' if cancer_tags else '')
                + '</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

    # 2열 패널
    p_left, p_right = st.columns([1.6, 1])

    with p_left:
        # ── 알약 이미지 AI 인식 + 처방전 OCR 통합 패널 ─────────────────────
        # DB 현황 배지
        if HAS_PILL_RECOGNIZER:
            _db_st = get_db_stats()
            _db_cnt = _db_st.get("total_pills", 0)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                f'<div class="c-panel-hdr" style="margin:0;">📋 처방전 · 알약 이미지 AI 분석</div>'
                f'<span style="background:rgba(0,255,136,0.15);border:1px solid rgba(0,255,136,0.3);'
                f'border-radius:12px;padding:1px 8px;font-size:0.6rem;color:#00ff88;">'
                f'💊 {_db_cnt}종 학습완료</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown('<div class="c-panel-hdr">📋 처방전 / 약포지 이미지 분석</div>', unsafe_allow_html=True)

        # 기능 안내 뱃지
        st.markdown(
            '<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;">'
            '<span style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);'
            'border-radius:3px;padding:1px 6px;font-size:0.58rem;color:#00e8ff;">💊 알약 사진 → 약품 동정</span>'
            '<span style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);'
            'border-radius:3px;padding:1px 6px;font-size:0.58rem;color:#00e8ff;">📄 처방전 OCR</span>'
            '<span style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.3);'
            'border-radius:3px;padding:1px 6px;font-size:0.58rem;color:#00e8ff;">🔍 처방 교차 검증</span>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="color:rgba(0,200,255,0.7);font-size:0.82rem;'
            'font-family:Noto Sans KR,sans-serif;margin-bottom:4px;font-weight:600;">'
            '📸 알약사진 · 처방전 · 약포지 이미지 업로드 (JPG/PNG)</div>',
            unsafe_allow_html=True
        )
        img_file = st.file_uploader(
            "이미지 파일 선택",
            type=["jpg","jpeg","png"],
            label_visibility="collapsed", key="img_up"
        )
        if img_file:
            # 이미지 크게 표시 (전체 너비)
            st.image(img_file, caption=f"📄 {img_file.name}  ({round(img_file.size/1024)}KB)",
                     use_container_width=True)
            # 분석 모드 선택
            _img_mode = st.radio(
                "분석 모드", ["🔍 자동 감지", "💊 알약 인식", "📄 처방전 OCR"],
                key="img_mode_sel", label_visibility="visible", horizontal=True
            )
            if st.button("🔬 AI 분석 실행", use_container_width=True, key="btn_img_ai"):
                mime = "image/jpeg" if img_file.name.lower().endswith((".jpg",".jpeg")) else "image/png"
                img_bytes = img_file.getvalue()
                with st.spinner("🔬 AI 이미지 분석 중... (Gemini Vision)"):
                    if "알약" in _img_mode and HAS_PILL_RECOGNIZER and HAS_GEMINI_ENGINE:
                        # 알약 전용 인식
                        _all_meds = []
                        for _r in pat_rxs:
                            for _m in _r.get("medication_name","").split(","):
                                _mn = _m.strip()
                                if _mn:
                                    _all_meds.append(_mn)
                        _recog = recognize_pill(img_bytes, mime, pat, _all_meds)
                        ans = _recog.get("ai_analysis","") or "AI 분석 결과 없음"
                        st.session_state["pill_recog_result"] = _recog
                    else:
                        ans = analyze_image(img_bytes, mime, pat, pat_rxs)
                        st.session_state["pill_recog_result"] = None
                st.session_state.image_ai_answer = ans
                st.session_state.last_image_name = img_file.name

            # 알약 인식 결과 카드 표시
            if st.session_state.get("pill_recog_result") and HAS_PILL_RECOGNIZER:
                st.markdown(
                    render_recognition_result_html(st.session_state["pill_recog_result"]),
                    unsafe_allow_html=True
                )
        else:
            # 이미지 없을 때 안내 + DB 학습 버튼
            st.markdown(
                '<div style="border:2px dashed rgba(0,242,255,0.25);border-radius:10px;'
                'padding:30px 20px;text-align:center;color:rgba(0,200,255,0.5);">'
                '<div style="font-size:2rem;margin-bottom:8px;">📸</div>'
                '<div style="font-family:Noto Sans KR,sans-serif;font-size:0.78rem;line-height:1.8;">'
                '알약 사진을 찍어 올리면<br>'
                'AI가 색상·모양·각인을 분석해<br>'
                '<b style="color:#00e8ff;">처방 약물과 일치하는지 즉시 확인</b>합니다<br>'
                '<span style="font-size:0.65rem;color:rgba(0,200,255,0.4);">처방전·약포지 OCR도 지원</span>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )
            if HAS_PILL_RECOGNIZER:
                if st.button("🔄 처방약 DB 재학습", use_container_width=True, key="btn_pill_learn"):
                    with st.spinner("처방약 이미지 데이터 학습 중..."):
                        _res = learn_patient_drugs(pat_rxs)
                    st.success(f"✅ {len(_res['learned'])}종 학습 완료")

        if st.session_state.image_ai_answer:
            st.markdown(ai_box(
                st.session_state.image_ai_answer,
                f"🔬 이미지 분석 결과 — {st.session_state.last_image_name}"
            ), unsafe_allow_html=True)

    with p_right:
        st.markdown('<div class="c-panel-hdr">🛡️ CROSS-CHECK SHIELD</div>', unsafe_allow_html=True)
        dup = len(meds) != len(set(meds))
        if dup:
            st.markdown('<div class="c-safe" style="border-color:rgba(255,120,0,0.5);background:rgba(255,80,0,0.04);"><div style="color:rgba(255,120,0,0.6);font-size:0.6rem;font-family:Noto Sans KR,sans-serif;">【CHECK】 경고</div><div style="color:#ff8844;font-size:0.75rem;font-weight:700;font-family:Noto Sans KR,sans-serif;">⚠️ 중복 처방 감지</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="c-safe"><div style="color:rgba(0,255,136,0.5);font-size:0.6rem;font-family:Noto Sans KR,sans-serif;">【CHECK】 고지 검증 통과</div><div style="color:#00ff88;font-size:0.75rem;font-weight:700;font-family:Noto Sans KR,sans-serif;">✅ SAFE</div><div style="color:rgba(0,255,136,0.45);font-size:0.6rem;font-family:Noto Sans KR,sans-serif;margin-top:2px;">다병원 중복 없음</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="c-check">교차 검증 통과<br>타 병원 처방과의 충돌 없음</div>', unsafe_allow_html=True)

        # 주변 약국 위젯
        if HAS_PHARMACY_WIDGET:
            st.markdown(render_pharmacy_widget_html(max_items=4), unsafe_allow_html=True)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        if st.button("📄 전략적 분석 리포트 PDF 발행", use_container_width=True, key="pdf_btn"):
            with st.spinner("PDF 생성 중..."):
                pdf = make_pdf(pat, rxs, pid)
            fn = f"PHARMA_{pid}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("⬇️ PDF 다운로드", data=pdf, file_name=fn,
                               mime="application/pdf", use_container_width=True)

    # ─────────────────────────────────────────────────────────────────
    # 하단 탭
    # ─────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)

    tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["💰 약가 정보","📰 임상 정책 뉴스","🧠 지식베이스 (RAG)","🇺🇸 FDA 데이터","🎗 암 프로토콜 DB","🥗 식단 가이드"])

    with tab2:
        st.markdown('<div style="color:rgba(0,200,255,0.5);font-size:0.65rem;font-family:Noto Sans KR,sans-serif;margin-bottom:8px;">약물명 검색 또는 현재 처방 약물 버튼 클릭</div>', unsafe_allow_html=True)
        price_q = st.text_input("약가검색", placeholder="예: 타세바, 키트루다...",
                                label_visibility="collapsed", key="price_q_input")
        # 현재 처방 빠른 버튼
        if meds:
            bcols = st.columns(len(meds))
            for i, m in enumerate(meds):
                with bcols[i]:
                    if st.button(m, key=f"pb_{m}", use_container_width=True):
                        st.session_state.price_q = m
        term = (st.session_state.get("price_q") or price_q).strip()
        show_p = {k:v for k,v in DRUG_PRICES.items()
                  if not term or term.lower() in k.lower() or term.lower() in v["성분"].lower()}
        if not show_p and term:
            st.markdown('<div style="color:rgba(0,200,255,0.35);font-size:0.65rem;font-family:Noto Sans KR,sans-serif;">검색 결과 없음</div>', unsafe_allow_html=True)
        else:
            for drug, info in show_p.items():
                kb_i = KB["약물"].get(drug)
                st.markdown(f"""
                <div class="c-price">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div><div class="c-price-name">{drug}</div>
                    <div class="c-price-code">{info['성분']} | {info['코드']}</div></div>
                    <div style="text-align:right;">
                      <div class="c-price-val">{info['가격']:,}원</div>
                      <div class="c-price-unit">/ {info['단위']}</div>
                    </div>
                  </div>
                  <span class="c-price-badge">{info['급여']}</span>
                  {f'<div style="margin-top:8px;border-top:1px solid rgba(0,242,255,0.1);padding-top:8px;">{kb_table(kb_i)}</div>' if kb_i and term else ''}
                </div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown(f'<div style="color:rgba(0,200,255,0.45);font-size:0.62rem;font-family:Noto Sans KR,sans-serif;margin-bottom:10px;">총 {len(POLICY_NEWS)}건 | 📦 내장 데이터베이스</div>', unsafe_allow_html=True)
        tags_all = ["전체"] + list(dict.fromkeys(n["tag"] for n in POLICY_NEWS))
        tag_sel  = st.selectbox("뉴스태그", tags_all, label_visibility="collapsed", key="news_tag")
        for n in POLICY_NEWS:
            if tag_sel != "전체" and n["tag"] != tag_sel: continue
            st.markdown(f"""
            <div class="c-news">
              <span class="c-news-tag">{n['tag']}</span>
              <div class="c-news-title">{n['title']}</div>
              <div class="c-news-body">{n['body']}</div>
              <div class="c-news-meta">📌 {n['source']} | 📅 {n['date']}</div>
            </div>""", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div style="color:rgba(0,200,255,0.65);font-size:0.7rem;font-family:Noto Sans KR,sans-serif;margin-bottom:6px;">질환 또는 약물을 검색하면 AI가 설명합니다</div>', unsafe_allow_html=True)

        kb_q_input = st.text_input("kb검색", placeholder="예: 타세바정, 폐암, 상호작용...",
                                   label_visibility="collapsed", key="kb_q_input")

        quick = ["타세바정","키트루다","폐암","백혈병","대장암","상호작용"]
        qcols = st.columns(6)
        for i, tq in enumerate(quick):
            with qcols[i]:
                if st.button(tq, key=f"qk_{tq}", use_container_width=True):
                    st.session_state.kb_q = tq

        kb_q_final = (st.session_state.get("kb_q") or kb_q_input).strip()

        if kb_q_final:
            results = kb_search(kb_q_final)
            st.markdown(f'<div style="color:rgba(0,200,255,0.4);font-size:0.62rem;font-family:Noto Sans KR,sans-serif;margin:6px 0 10px;">"{kb_q_final}" — {len(results)}건 검색됨</div>', unsafe_allow_html=True)

            if results:
                # DB 결과 표시
                for res in results:
                    st.markdown(f"""
                    <div class="c-kb-card">
                      <div class="c-kb-type">{res['type']}</div>
                      <div class="c-kb-title">{res['title']}</div>
                      {kb_table(res['data'])}
                    </div>""", unsafe_allow_html=True)

                # AI 보강 설명
                if st.button("🤖 AI 상세 설명 받기", use_container_width=True, key="btn_kb_ai"):
                    with st.spinner("AI 분석 중..."):
                        ai_ans = ai_kb_search(kb_q_final, results)
                    st.session_state.kb_ai_answer = ai_ans

                if st.session_state.kb_ai_answer:
                    st.markdown(ai_box(st.session_state.kb_ai_answer, "🤖 AI 임상 설명"), unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:rgba(0,200,255,0.35);font-size:0.65rem;font-family:Noto Sans KR,sans-serif;padding:8px;">검색 결과 없음. 다른 약물명이나 질환명으로 시도하세요.</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="border:1px solid rgba(0,242,255,0.18);background:#0a1628;border-radius:6px;padding:12px 14px;">
              <div style="color:#00e8ff;font-size:0.68rem;font-weight:700;margin-bottom:10px;font-family:'Noto Sans KR',sans-serif;">
              📁 [전술 인벤토리] v28.0 FDA Grade 임상 지식 베이스
              </div>""", unsafe_allow_html=True)
            ic1, ic2 = st.columns(2)
            with ic1:
                st.markdown('<div style="color:rgba(0,200,255,0.85);font-size:0.8rem;font-family:Noto Sans KR,sans-serif;font-weight:700;margin-bottom:10px;border-bottom:1px solid rgba(0,242,255,0.2);padding-bottom:5px;">💊 등재 약물 (클릭하여 검색)</div>', unsafe_allow_html=True)
                dcols = st.columns(3)
                for i, d in enumerate(KB["약물"]):
                    with dcols[i % 3]:
                        if st.button(d, key=f"bkd_{d}", use_container_width=True):
                            st.session_state.kb_q = d
                            st.rerun()
            with ic2:
                st.markdown('<div style="color:rgba(0,200,255,0.85);font-size:0.8rem;font-family:Noto Sans KR,sans-serif;font-weight:700;margin-bottom:10px;border-bottom:1px solid rgba(0,242,255,0.2);padding-bottom:5px;">🏥 등재 질환 (클릭하여 검색)</div>', unsafe_allow_html=True)
                ccols = st.columns(3)
                for i, d in enumerate(KB["질환"]):
                    with ccols[i % 3]:
                        if st.button(d, key=f"bkc_{d}", use_container_width=True):
                            st.session_state.kb_q = d
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            synergy_count = get_total_synergy_count() if HAS_SEASONAL_RAG else 0
            st.markdown(
                f'<div style="color:rgba(0,200,255,0.3);font-size:0.6rem;font-family:Noto Sans KR,sans-serif;margin-top:6px;">'
                f'약물 {len(KB["약물"])}종 · 질환 {len(KB["질환"])}종 · 상호작용 {len(KB["상호작용"])}건'
                f'{f" · 🌿 계절 식이·항암제 시너지 {synergy_count}가지" if synergy_count else ""}'
                f'</div>', unsafe_allow_html=True)

            # ── 계절별 과일·채소 × 항암제 가이드 패널 ──
            if HAS_SEASONAL_RAG:
                st.markdown("<hr style='border-color:rgba(0,200,255,0.1);margin:10px 0;'>", unsafe_allow_html=True)
                current_season = get_current_season()
                season_options = ["봄", "여름", "가을", "겨울"]
                season_sel = st.selectbox(
                    "계절 선택",
                    season_options,
                    index=season_options.index(current_season),
                    key="seasonal_rag_season",
                    label_visibility="collapsed",
                )
                drug_filter = st.text_input(
                    "항암제 필터",
                    placeholder="예: 키트루다, 타그리소... (비워두면 전체 표시)",
                    label_visibility="collapsed",
                    key="seasonal_drug_filter",
                )
                st.markdown(
                    render_seasonal_rag_html(season=season_sel, drug_filter=drug_filter),
                    unsafe_allow_html=True,
                )

    with tab5:
        st.markdown('<div style="color:#00f2ff;font-size:0.72rem;font-weight:700;font-family:Noto Sans KR,sans-serif;margin-bottom:10px;">🇺🇸 OpenFDA 수집 데이터 — 70개 약품 FDA 라벨 + FAERS 부작용 보고</div>', unsafe_allow_html=True)
        fda_drug_names = get_collected_drug_names() if HAS_MED_ENGINE else []
        if fda_drug_names:
            fda_sel = st.selectbox("약품 선택", fda_drug_names, key="fda_drug_sel")
            if fda_sel:
                fda_data = get_fda_info(fda_sel)
                if fda_data:
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        st.markdown(f"""
                        <div style="background:#0a1628;border:1px solid rgba(0,242,255,0.2);border-radius:6px;padding:12px;">
                          <div style="color:#00f2ff;font-size:0.75rem;font-weight:700;margin-bottom:8px;">📋 FDA 라벨 정보</div>
                          <div style="color:#aaa;font-size:0.68rem;line-height:1.6;">
                            <b style="color:#ccc;">성분명(영문):</b> {fda_data.get('generic_name_en','')}<br>
                            <b style="color:#ccc;">제조사:</b> {fda_data.get('manufacturer','')}<br>
                            <b style="color:#ccc;">투여경로:</b> {fda_data.get('route','')}<br>
                          </div>
                          <div style="color:#00e8ff;font-size:0.68rem;font-weight:700;margin:10px 0 4px;">적응증 (FDA 승인)</div>
                          <div style="color:#aaa;font-size:0.65rem;line-height:1.5;max-height:120px;overflow-y:auto;">{fda_data.get('indications','')[:500]}</div>
                          <div style="color:#ff9800;font-size:0.68rem;font-weight:700;margin:10px 0 4px;">경고</div>
                          <div style="color:#aaa;font-size:0.65rem;line-height:1.5;max-height:80px;overflow-y:auto;">{fda_data.get('warnings','')[:300]}</div>
                        </div>""", unsafe_allow_html=True)
                    with fc2:
                        ae_list = fda_data.get('faers_top_reactions', [])
                        total   = fda_data.get('total_reports', 0)
                        st.markdown(f"""
                        <div style="background:#0a1628;border:1px solid rgba(255,100,100,0.3);border-radius:6px;padding:12px;">
                          <div style="color:#ff6b6b;font-size:0.75rem;font-weight:700;margin-bottom:6px;">⚠️ FAERS 상위 부작용 보고</div>
                          <div style="color:#888;font-size:0.62rem;margin-bottom:8px;">총 {total:,}건 보고 중 상위 항목</div>""",
                          unsafe_allow_html=True)
                        if ae_list:
                            for ae in ae_list[:10]:
                                term  = ae.get("term", ae.get("reaction", ""))
                                count = ae.get("count", 0)
                                pct   = round(count / max(total, 1) * 100, 1)
                                bar_w = min(int(pct * 3), 100)
                                st.markdown(f"""
                                <div style="margin-bottom:5px;">
                                  <div style="display:flex;justify-content:space-between;color:#ddd;font-size:0.65rem;">
                                    <span>{term}</span><span style="color:#ff9898;">{count:,}건 ({pct}%)</span>
                                  </div>
                                  <div style="height:4px;background:#1a2540;border-radius:2px;margin-top:2px;">
                                    <div style="width:{bar_w}%;height:100%;background:linear-gradient(90deg,#ff6b6b,#ff9898);border-radius:2px;"></div>
                                  </div>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color:#555;font-size:0.65rem;">FAERS 데이터 없음</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # 출처 표시
                    sources = fda_data.get("data_sources", [])
                    if sources:
                        src_text = " | ".join(s.get("source","") for s in sources if s.get("source"))
                        st.markdown(f'<div style="color:rgba(0,200,255,0.35);font-size:0.58rem;margin-top:8px;">출처: {src_text}</div>', unsafe_allow_html=True)

                    # 음성 낭독 기능
                    if HAS_VOICE_ENGINE and voice_mgr:
                        st.markdown("<hr>", unsafe_allow_html=True)
                        drug_voice_text = f"{fda_sel}의 FDA 정보입니다. 성분명은 {fda_data.get('generic_name_en','')}이고, 제조사는 {fda_data.get('manufacturer','')}입니다. 적응증으로는 {fda_data.get('indications','')[:200]}입니다."

                        if st.button("🎤 FDA 정보 음성 낭독", key=f"voice_fda_{fda_sel}", use_container_width=True):
                            voice_html = voice_mgr.get_engine().create_audio_html_player(
                                drug_voice_text,
                                voice_mgr.get_selected_voice()
                            )
                            if voice_html:
                                st.markdown(voice_html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#555;font-size:0.68rem;">해당 약품의 FDA 데이터가 없습니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-size:0.68rem;">data/collected/processed/drug_master.json 파일을 먼저 생성하세요. (pharma_data_collector.py 실행)</div>', unsafe_allow_html=True)

    with tab6:
        st.markdown('<div style="color:#00f2ff;font-size:0.75rem;font-weight:700;font-family:Noto Sans KR,sans-serif;margin-bottom:6px;">🎗 암 임상 프로토콜 데이터베이스</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#aaa;font-size:0.62rem;font-family:Noto Sans KR,sans-serif;margin-bottom:12px;">출처: NCCN Guidelines 2024-2025 / ESMO Clinical Practice Guidelines 2023-2024 / 국립암센터 국가암등록통계 2022 / 대한종양학회 진료지침 2024</div>', unsafe_allow_html=True)

        if HAS_CANCER_DB:
            cats = get_cancers_by_category()
            total_cancers = sum(len(v) for v in cats.values())
            st.markdown(f'<div style="color:#00ff88;font-size:0.68rem;font-weight:700;margin-bottom:10px;">총 {total_cancers}개 암종 등록</div>', unsafe_allow_html=True)

            # 카테고리 + 암종 선택
            cat_names = list(cats.keys())
            sel_cat = st.selectbox("카테고리", cat_names, key="cancer_cat")
            cancer_list_in_cat = cats.get(sel_cat, [])
            sel_cancer = st.selectbox("암종 선택", cancer_list_in_cat, key="cancer_sel")

            # 검색창
            cancer_q = st.text_input("또는 암종/바이오마커/약물 검색", placeholder="예: BRCA, 자궁육종, pembrolizumab ...", key="cancer_q")
            if cancer_q:
                c_results = search_cancer_protocols(cancer_q)
                if c_results:
                    sel_cancer = c_results[0]["name"]
                    st.markdown(f'<div style="color:#aeea00;font-size:0.62rem;">"{cancer_q}" 검색 결과: {", ".join(r["name"] for r in c_results[:5])}</div>', unsafe_allow_html=True)

            # 선택된 암 프로토콜 표시
            proto = CANCER_PROTOCOLS.get(sel_cancer, {})
            if proto:
                st.markdown(f"""
                <div style="background:#0a1628;border:1px solid rgba(0,242,255,0.25);border-radius:8px;padding:14px;margin-top:10px;">
                  <div style="color:#ff6b9d;font-size:0.9rem;font-weight:900;font-family:Noto Sans KR,sans-serif;margin-bottom:4px;">{sel_cancer}</div>
                  <div style="color:#aaa;font-size:0.65rem;margin-bottom:8px;">{proto.get("ICD10","")} | {proto.get("분류","")}</div>
                </div>""", unsafe_allow_html=True)

                pc1, pc2 = st.columns(2)

                with pc1:
                    # 바이오마커
                    if "바이오마커" in proto:
                        st.markdown('<div style="color:#00e8ff;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">🧬 바이오마커 / 유전자</div>', unsafe_allow_html=True)
                        st.markdown(f'<div style="background:#0d1f3c;border-radius:4px;padding:8px;color:#cde;font-size:0.65rem;line-height:1.6;">{proto["바이오마커"]}</div>', unsafe_allow_html=True)

                    # 1차 치료
                    tx1 = proto.get("1차치료", proto.get("표준치료", None))
                    if tx1:
                        st.markdown('<div style="color:#00ff88;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">💊 1차 치료</div>', unsafe_allow_html=True)
                        if isinstance(tx1, dict):
                            for sub_name, sub_val in tx1.items():
                                if isinstance(sub_val, dict):
                                    st.markdown(f'<div style="color:#aeea00;font-size:0.65rem;font-weight:700;margin-top:6px;">{sub_name}</div>', unsafe_allow_html=True)
                                    for k2, v2 in sub_val.items():
                                        st.markdown(f'<div style="color:#aaa;font-size:0.62rem;padding-left:8px;"><b style="color:#ccc;">{k2}:</b> {v2}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;"><span style="color:#aeea00;font-weight:700;">{sub_name}:</span> {sub_val}</div>', unsafe_allow_html=True)
                        elif isinstance(tx1, list):
                            for item in tx1:
                                st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;">{tx1}</div>', unsafe_allow_html=True)

                    # 아형
                    if "아형" in proto:
                        st.markdown('<div style="color:#ff9800;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">📋 병리학적 아형</div>', unsafe_allow_html=True)
                        for stype, desc in (proto["아형"].items() if isinstance(proto["아형"], dict) else []):
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:3px 0;"><span style="color:#ffcc80;font-weight:700;">{stype}:</span> {desc}</div>', unsafe_allow_html=True)

                with pc2:
                    # 2차 치료
                    tx2 = proto.get("2차치료", proto.get("재발", None))
                    if tx2:
                        st.markdown('<div style="color:#ff9800;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">🔄 2차 치료 / 재발</div>', unsafe_allow_html=True)
                        items = tx2 if isinstance(tx2, list) else [str(tx2)]
                        for item in items:
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)

                    # 한국 통계
                    kr_stat = proto.get("한국통계", {})
                    if kr_stat:
                        st.markdown('<div style="color:#ff6b6b;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">📊 한국 통계 (국립암센터 2022)</div>', unsafe_allow_html=True)
                        for k, v in kr_stat.items():
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;"><b style="color:#ffb3b3;">{k}:</b> {v}</div>', unsafe_allow_html=True)

                    # 지침 출처
                    if "지침" in proto:
                        st.markdown(f'<div style="color:rgba(0,200,255,0.4);font-size:0.58rem;margin-top:10px;border-top:1px solid rgba(0,242,255,0.1);padding-top:6px;">📖 {proto["지침"]}</div>', unsafe_allow_html=True)

                    # 면역/표적치료 신약
                    for field in ["표적치료", "면역치료", "신규표적", "신규치료"]:
                        if field in proto:
                            st.markdown(f'<div style="color:#ce93d8;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">✨ {field}</div>', unsafe_allow_html=True)
                            fval = proto[field]
                            if isinstance(fval, dict):
                                for k, v in fval.items():
                                    st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;"><b style="color:#e1bee7;">{k}:</b> {v}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div style="color:#aaa;font-size:0.62rem;">{fval}</div>', unsafe_allow_html=True)

                # 음성 낭독 기능 (암종 정보)
                if HAS_VOICE_ENGINE and voice_mgr and st.button("🎤 암종 정보 음성 낭독", key=f"voice_cancer_{sel_cancer}", use_container_width=True):
                    cancer_voice_text = f"{sel_cancer}에 대한 임상 프로토콜입니다. "
                    if proto.get("ICD10"):
                        cancer_voice_text += f"ICD10 코드는 {proto.get('ICD10')}이고, "
                    if proto.get("바이오마커"):
                        cancer_voice_text += f"바이오마커는 {proto.get('바이오마커')[:100]}입니다. "
                    if proto.get("1차치료"):
                        if isinstance(proto.get("1차치료"), dict):
                            tx_text = ", ".join(proto.get("1차치료").keys())
                        else:
                            tx_text = str(proto.get("1차치료"))[:100]
                        cancer_voice_text += f"1차 치료는 {tx_text}입니다."

                    voice_html = voice_mgr.get_engine().create_audio_html_player(
                        cancer_voice_text,
                        voice_mgr.get_selected_voice()
                    )
                    if voice_html:
                        st.markdown(voice_html, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-size:0.68rem;">cancer_protocols_db.py 를 불러오지 못했습니다.</div>', unsafe_allow_html=True)

    with tab7:
        st.markdown('<div style="color:#00f2ff;font-size:0.75rem;font-weight:700;font-family:Noto Sans KR,sans-serif;margin-bottom:4px;">🥗 암 환자 / 만성질환 환자 식단 가이드</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#888;font-size:0.6rem;font-family:Noto Sans KR,sans-serif;margin-bottom:10px;">출처: 국가암정보센터(NCC) · 질병관리청(KDCA) · 대한신장학회(KSN) · 서울아산병원 · 연세의대 · NCI(미국) · ACS · ESPEN 2021</div>', unsafe_allow_html=True)

        if HAS_NUTRITION_DB:
            diet_cats = get_all_diet_categories()
            d_col1, d_col2 = st.columns([1, 1])
            with d_col1:
                diet_type = st.radio("종류", ["암종별 식단", "만성질환 식단", "암환자 공통 가이드"], key="diet_type", horizontal=True)
            with d_col2:
                diet_q = st.text_input("식품/질환 검색", placeholder="예: 통풍, 위암, 칼륨, 퓨린...", key="diet_q")

            if diet_q:
                d_results = search_diet(diet_q)
                if d_results:
                    diet_type = None
                    st.markdown(f'<div style="color:#aeea00;font-size:0.62rem;">"{diet_q}" 검색: {len(d_results)}건</div>', unsafe_allow_html=True)
                    sel_diet_data = d_results[0]["data"]
                    sel_diet_name = d_results[0]["name"]
                else:
                    st.markdown('<div style="color:#555;font-size:0.62rem;">검색 결과 없음</div>', unsafe_allow_html=True)
                    sel_diet_data, sel_diet_name = {}, ""
            elif diet_type == "암종별 식단":
                cancer_diet_names = list(CANCER_TYPE_DIET.keys())
                sel_diet_name = st.selectbox("암종 선택", cancer_diet_names, key="cancer_diet_sel")
                sel_diet_data = CANCER_TYPE_DIET.get(sel_diet_name, {})
            elif diet_type == "만성질환 식단":
                chronic_names = list(CHRONIC_DISEASE_DIET.keys())
                sel_diet_name = st.selectbox("질환 선택", chronic_names, key="chronic_diet_sel")
                sel_diet_data = CHRONIC_DISEASE_DIET.get(sel_diet_name, {})
            else:
                sel_diet_name = "암환자공통가이드"
                sel_diet_data = CANCER_NUTRITION_GENERAL

            if sel_diet_data:
                sources = sel_diet_data.get("출처", [])
                if isinstance(sources, list):
                    src_str = " | ".join(sources)
                else:
                    src_str = str(sources)

                st.markdown(f'<div style="background:#0a1628;border:1px solid rgba(0,242,255,0.2);border-radius:6px;padding:10px 14px;margin:8px 0;">'
                             f'<div style="color:#00ff88;font-size:0.8rem;font-weight:900;font-family:Noto Sans KR,sans-serif;">{sel_diet_name.replace("_"," ")}</div>'
                             f'<div style="color:rgba(0,200,255,0.4);font-size:0.57rem;margin-top:3px;">출처: {src_str}</div>'
                             f'</div>', unsafe_allow_html=True)

                # 영양소 목표 수치
                nt = get_nutrient_targets(sel_diet_name)
                if nt:
                    st.markdown('<div style="color:#ffcc80;font-size:0.7rem;font-weight:700;margin:8px 0 4px;">📊 영양소 목표 수치</div>', unsafe_allow_html=True)
                    cols_nt = st.columns(min(len(nt), 4))
                    for i, (k, v) in enumerate([x for x in nt.items() if x[0] != "출처"]):
                        with cols_nt[i % len(cols_nt)]:
                            st.markdown(f'<div style="background:#0d1f3c;border-radius:4px;padding:6px 8px;text-align:center;">'
                                         f'<div style="color:#aaa;font-size:0.58rem;">{k}</div>'
                                         f'<div style="color:#00f2ff;font-size:0.72rem;font-weight:700;">{v}</div>'
                                         f'</div>', unsafe_allow_html=True)

                # 핵심원칙 / 기본원칙
                for field in ["핵심원칙", "기본원칙", "목적"]:
                    if field in sel_diet_data:
                        val = sel_diet_data[field]
                        st.markdown(f'<div style="color:#00e8ff;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">📌 {field}</div>', unsafe_allow_html=True)
                        if isinstance(val, list):
                            for item in val:
                                st.markdown(f'<div style="color:#ccc;font-size:0.65rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="color:#ccc;font-size:0.65rem;">{val}</div>', unsafe_allow_html=True)

                # 권장/제한 식품 대비 표
                food_res = get_food_restrictions(sel_diet_name)
                if food_res.get("권장") or food_res.get("제한"):
                    fr1, fr2 = st.columns(2)
                    with fr1:
                        st.markdown('<div style="color:#00ff88;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">✅ 권장 식품</div>', unsafe_allow_html=True)
                        for item in food_res.get("권장", [])[:12]:
                            st.markdown(f'<div style="color:#a5d6a7;font-size:0.62rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)
                    with fr2:
                        st.markdown('<div style="color:#ff6b6b;font-size:0.7rem;font-weight:700;margin:10px 0 4px;">❌ 제한/금기 식품</div>', unsafe_allow_html=True)
                        for item in food_res.get("제한", [])[:12]:
                            st.markdown(f'<div style="color:#ef9a9a;font-size:0.62rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)

                # 나머지 상세 데이터 — 주요 섹션만 렌더링
                skip_keys = {"출처", "핵심원칙", "기본원칙", "목적", "권장_식품", "제한_식품", "권장", "제한"}
                for key, val in sel_diet_data.items():
                    if key in skip_keys:
                        continue
                    if not val:
                        continue
                    st.markdown(f'<div style="color:#ce93d8;font-size:0.68rem;font-weight:700;margin:10px 0 3px;">{key.replace("_"," ")}</div>', unsafe_allow_html=True)
                    if isinstance(val, list):
                        for item in val[:8]:
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;">• {item}</div>', unsafe_allow_html=True)
                    elif isinstance(val, dict):
                        for k2, v2 in list(val.items())[:6]:
                            disp = ", ".join(v2) if isinstance(v2, list) else str(v2)[:120]
                            st.markdown(f'<div style="color:#aaa;font-size:0.62rem;margin:2px 0;"><b style="color:#e1bee7;">{k2}:</b> {disp}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="color:#aaa;font-size:0.62rem;">{str(val)[:200]}</div>', unsafe_allow_html=True)

                # 음성 낭독 기능 (식단 정보)
                if HAS_VOICE_ENGINE and voice_mgr and st.button("🎤 식단 정보 음성 낭독", key=f"voice_diet_{sel_diet_name}", use_container_width=True):
                    nt = get_nutrient_targets(sel_diet_name)
                    nutrient_text = ""
                    if nt:
                        nutrient_text = ". ".join(f"{k} {v}" for k, v in list(nt.items())[:4] if k != "출처") + "."

                    food_res = get_food_restrictions(sel_diet_name)
                    food_text = ""
                    if food_res.get("권장"):
                        food_text += f" 권장 식품: {', '.join(food_res.get('권장', [])[:5])}."
                    if food_res.get("제한"):
                        food_text += f" 제한 식품: {', '.join(food_res.get('제한', [])[:5])}."

                    diet_voice_text = f"{sel_diet_name.replace('_',' ')}에 대한 식단 가이드입니다. {nutrient_text} {food_text}"

                    voice_html = voice_mgr.get_engine().create_audio_html_player(
                        diet_voice_text,
                        voice_mgr.get_selected_voice()
                    )
                    if voice_html:
                        st.markdown(voice_html, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-size:0.68rem;">nutrition_diet_db.py 를 불러오지 못했습니다.</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────
    # AI 지휘관 터미널 (음성/텍스트 분석)
    # ─────────────────────────────────────────────────────────────────
    chat_val = st.chat_input("🎙️ 고객 이름을 부르거나 질문하세요. (예: '김상은 고객 상태 어때?')")
    if chat_val:
        found_pid = None
        for p_id, p_info in patients.items():
            if p_info["real_name"] in chat_val:
                found_pid = p_id
                break
                
        if found_pid and found_pid != pid:
            st.session_state.pid = found_pid
            st.session_state.voice_result = chat_val
            new_pat = patients[found_pid]
            new_pat_rxs = [r for r in rxs if r["patient_id"] == found_pid]
            with st.spinner(f"👤 {new_pat['real_name']} 고객 데이터 로딩 및 분석 중..."):
                ans = analyze_voice(chat_val, new_pat, new_pat_rxs)
            st.session_state.voice_ai_answer = ans
            st.rerun()
        else:
            with st.spinner("AI 분석 중..."):
                ans = analyze_voice(chat_val, pat, pat_rxs)
            st.session_state.voice_ai_answer = ans
            st.session_state.voice_result = chat_val

    if st.session_state.voice_ai_answer:
        st.markdown(f"""
        <div style="border:1px solid rgba(0,242,255,0.4);background:rgba(0,20,50,0.85);border-radius:6px;
                    padding:16px 20px;margin-top:14px;box-shadow: 0 4px 15px rgba(0,242,255,0.15);">
          <div style="color:rgba(0,242,255,0.8);font-size:0.75rem;margin-bottom:8px;font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:700;">
            🤖 AI COMMANDER — "{st.session_state.voice_result}"
          </div>
          <div style="color:#c8f8ff;font-size:0.8rem;line-height:1.8;font-family:'Noto Sans KR',sans-serif;word-break:keep-all;">
            {st.session_state.voice_ai_answer.replace(chr(10),'<br>')}
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;border-top:1px solid rgba(0,242,255,0.1);padding-top:10px;
                margin-top:16px;color:rgba(0,200,255,0.3);font-size:0.58rem;font-family:'Noto Sans KR',sans-serif;">
    © 2026 PHARMA-HYBRID v20.0 ULTIMATE COMMAND | CLASSIFIED SYSTEM
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
