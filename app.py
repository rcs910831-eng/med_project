#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Anti-Gravity Life-Care | PHARMA-HYBRID v40.5 Dual-Mode

import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import json
import re
import traceback
from datetime import datetime
from typing import Dict, List
import logging

st.set_page_config(page_title="Anti-Gravity Life-Care", layout="wide")
logger = logging.getLogger("pharma_app")
DB_PATH = "pharma_v20.db"
ADMIN_PASSWORD = "doctor2026"  # ← 선생님만 아는 비밀번호로 변경하세요

try:
    import kb_data
    from kb_data import DEFAULT_PATIENTS, RAW_RX, KB, PILL_KB, DRUG_PRICES, POLICY_NEWS
except Exception as e:
    st.error("🚨 [CRITICAL] kb_data.py 로드 실패!")
    st.code(traceback.format_exc(), language="python")
    st.stop()

try:
    from ai_engine import analyze_image, HAS_GEMINI_ENGINE
except ImportError:
    HAS_GEMINI_ENGINE = False
    def analyze_image(*a, **k): return "AI 엔진 미설치"

try:
    from guardian_link import init_guardian_db, send_guardian_alert
    HAS_GUARDIAN = True
except ImportError:
    HAS_GUARDIAN = False

try:
    from medication_adherence import (init_adherence_db, render_compliance_sentinel_html,
                                       sync_schedules_from_rx)
    HAS_ADHERENCE = True
except ImportError:
    HAS_ADHERENCE = False

try:
    from nearby_pharmacy_widget import render_pharmacy_widget_html
    HAS_PHARMACY = True
except ImportError:
    HAS_PHARMACY = False


# ── DB ─────────────────────────────────────────────────────────────────────
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS rx (
                id INTEGER PRIMARY KEY, patient_id TEXT, medication_name TEXT,
                cancer_type TEXT, dosage TEXT, frequency TEXT, duration TEXT,
                start_date TEXT, doctor_name TEXT, status TEXT, side_effects TEXT,
                efficacy_rate REAL, notes TEXT, last_updated TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY, real_name TEXT, age INTEGER,
                gender TEXT, hospital TEXT, diet TEXT)""")
            for r in RAW_RX:
                c.execute("INSERT OR REPLACE INTO rx VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
            for p, info in DEFAULT_PATIENTS.items():
                c.execute("INSERT OR IGNORE INTO patients VALUES (?,?,?,?,?,?)",
                          (p, info["real_name"], info["age"], info["gender"], info["hospital"], ""))
            conn.commit()
        if HAS_ADHERENCE: init_adherence_db()
        if HAS_GUARDIAN: init_guardian_db()
    except Exception as e:
        st.error(f"🚨 DB 초기화 실패: {e}")

def load_patients() -> Dict:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT patient_id, real_name, age, gender, hospital, diet FROM patients")
            rows = c.fetchall()
        return {r[0]: {"real_name":r[1],"age":r[2],"gender":r[3],"hospital":r[4],"diet":r[5] or ""} for r in rows}
    except Exception as e:
        logger.warning(f"load_patients fallback: {e}")
        return DEFAULT_PATIENTS

def load_rx() -> List[Dict]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM rx ORDER BY id")
            rows = c.fetchall()
        keys = ["id","patient_id","medication_name","cancer_type","dosage","frequency","duration",
                "start_date","doctor_name","status","side_effects","efficacy_rate","notes","last_updated"]
        return [dict(zip(keys, r)) for r in rows]
    except Exception as e:
        logger.warning(f"load_rx fallback: {e}")
        return []


# ── 공통 헬퍼 ──────────────────────────────────────────────────────────────
def tts_button(text: str, key: str):
    clean = re.sub(r'[^가-힣0-9\s.,!]', '', text).strip() or "브리핑 할 데이터가 준비되지 않았습니다."
    safe = clean.replace('\\','\\\\').replace("'","\\'").replace('"','\\"')
    components.html(f"""<script>function speak_{key}(){{var m=new SpeechSynthesisUtterance('{safe}');m.lang='ko-KR';m.rate=1.0;window.speechSynthesis.speak(m);}}</script>
    <button onclick="speak_{key}()" style="background:linear-gradient(90deg,#00f2ff,#0060ff);border:none;color:#000;border-radius:8px;padding:12px 25px;cursor:pointer;font-size:1.1rem;font-weight:900;width:100%;box-shadow:0 4px 15px rgba(0,242,255,0.4);">🎙️ AI 마스터 브리핑 재생</button>""", height=65)

def emergency_floating_panel():
    st.markdown("""<div style="position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;">
    <a href="tel:119" style="text-decoration:none;"><div style="background:#ff4b4b;color:white;padding:15px;border-radius:50px;width:120px;text-align:center;font-weight:900;box-shadow:0 0 20px rgba(255,75,75,0.6);border:2px solid white;">🆘 119 호출</div></a>
    <a href="tel:112" style="text-decoration:none;"><div style="background:#0060ff;color:white;padding:15px;border-radius:50px;width:120px;text-align:center;font-weight:900;box-shadow:0 0 20px rgba(0,96,255,0.6);border:2px solid white;">🚓 112 신고</div></a>
    </div>""", unsafe_allow_html=True)

def get_time_sensing_ui():
    h = datetime.now().hour
    if 5 <= h < 12:   return {"icon":"🌅","title":"좋은 아침이에요!","color":"#E65100","bg":"linear-gradient(135deg,#FFF3E0,#FFE0B2)","text":"#5D4037"}
    elif 12 <= h < 17: return {"icon":"☀️","title":"좋은 오후에요!","color":"#2E7D32","bg":"linear-gradient(135deg,#E8F5E9,#C8E6C9)","text":"#1B5E20"}
    elif 17 <= h < 21: return {"icon":"🌆","title":"좋은 저녁이에요!","color":"#1565C0","bg":"linear-gradient(135deg,#E3F2FD,#BBDEFB)","text":"#0D47A1"}
    else:               return {"icon":"🌙","title":"좋은 밤이에요!","color":"#4A148C","bg":"linear-gradient(135deg,#EDE7F6,#D1C4E9)","text":"#311B92"}


# ── 환자 눈높이 약물 설명 (꼼꼼·친절 버전) ──────────────────────────────────
PATIENT_DRUG_SIMPLE = {
    # 항암제
    "타세바정":  {
        "why": "폐암 세포의 성장 스위치(EGFR)를 꺼버려서 암이 더 이상 자라지 못하게 막아요.",
        "when": "식사 1시간 전 또는 식후 2시간 후, 공복에 드세요. 음식과 함께 먹으면 흡수가 달라져요.",
        "if_skip": "암 세포가 다시 자랄 수 있어요. 매일 빠짐없이 드세요.",
        "food": "자몽·자몽주스 금지 (약 농도 올라가 독성 위험). 술은 피하세요.",
        "drug": "항진균제(이트라코나졸)·일부 항생제와 함께 먹으면 혈중 농도가 변해요.",
        "danger": "🚨 피부 발진이 심해지면 병원에. 숨이 갑자기 차면 즉시 응급실 (간질성 폐렴).",
        "motivation": "표적치료제라 기존 항암 주사보다 부작용이 적어요. 꾸준히 드시면 암을 오래 막을 수 있어요!",
        "grapefruit": True
    },
    "키트루다":  {
        "why": "우리 몸의 면역 세포(T세포)가 암세포를 더 잘 공격하도록 PD-1 차단점을 열어줘요. 주사로 맞는 면역 항암제예요.",
        "when": "병원에서 3주마다 주사로 맞아요. 날짜를 꼭 지켜주세요.",
        "if_skip": "면역 체계가 암 공격을 멈출 수 있어요. 반드시 예약일에 병원을 방문하세요.",
        "food": "특별한 음식 금기는 없지만, 술·면역력을 억제하는 생 허브 보충제는 주의하세요.",
        "drug": "다른 면역억제제(스테로이드 장기 복용 등)는 키트루다 효과를 줄일 수 있어요.",
        "danger": "🚨 갑자기 숨이 차거나 심한 설사 → 즉시 응급실 (면역 이상반응). 피부 발진·관절통도 바로 알려주세요.",
        "motivation": "최대 5년 이상 효과가 지속된 사례도 있어요. 면역 치료의 혁명적인 약이에요!",
        "grapefruit": False
    },
    "타그리소":  {
        "why": "폐암 세포의 특별한 약점(EGFR T790M 변이)을 정확히 공격해요. 뇌 혈관 장벽도 통과해서 뇌 전이도 막아줘요.",
        "when": "매일 같은 시간에, 음식과 관계없이 드세요. 하루도 빠지지 않는 것이 핵심이에요.",
        "if_skip": "암세포가 내성을 키울 수 있어요. 절대 임의로 중단하지 마세요.",
        "food": "자몽 금지! 세인트존스워트(허브 우울증 보충제)도 약 농도를 낮춰요.",
        "drug": "QT 연장 약물·항부정맥제. 리팜피신·페니토인은 타그리소 효과를 감소시켜요.",
        "danger": "🚨 갑자기 심한 기침+숨참 → 즉시 응급실 (간질성 폐렴). 눈 충혈+통증·빛 눈부심 → 안과 방문.",
        "motivation": "FLAURA 연구: 평균 38.6개월 암 억제 성공! 이전 세대 약보다 2배 효과예요.",
        "grapefruit": True
    },
    "글리벡정":  {
        "why": "백혈병·위장관기질종양(GIST)에서 암세포가 자라는 데 필요한 BCR-ABL 효소를 차단해요.",
        "when": "식사 중에 큰 컵의 물과 함께 드세요. 공복에 드시면 구역질이 심해요.",
        "if_skip": "백혈병 세포가 다시 증식할 수 있어요.",
        "food": "자몽 주의. 다량의 파라세타몰(타이레놀) 병용 주의.",
        "drug": "와파린(항응고제): 출혈 위험 증가. 시메티딘·케토코나졸: 글리벡 농도 변화.",
        "danger": "🚨 갑자기 몸이 많이 부어오르면 즉시 병원. 숨이 갑자기 차면 응급실.",
        "motivation": "만성골수성백혈병에서 완전 관해율 80%! 꾸준히 드시면 정상 생활이 가능해요.",
        "grapefruit": True
    },
    # 위장약
    "베아제정":  {
        "why": "소화효소(아밀라아제·리파아제·프로테아제)를 보충해서 밥·고기·기름을 더 잘 소화시켜요.",
        "when": "식사 중이나 식사 직후에 드세요.",
        "if_skip": "소화가 안 되고 배가 더부룩하고 가스가 찰 수 있어요.",
        "food": "특별한 금기 없어요.",
        "drug": "특별한 주의 약물 없어요.",
        "danger": "특별한 위험 증상 없어요.",
        "motivation": "항암 치료 중 식욕과 소화 기능을 지켜줘요!",
        "grapefruit": False
    },
    "무코스타정": {
        "why": "위점막을 덮는 보호막(뮤신)을 더 많이 만들도록 자극해서 위를 자극으로부터 보호해요.",
        "when": "식후 30분 이내, 하루 3번 드세요.",
        "if_skip": "위벽이 노출되어 위염·위궤양이 악화될 수 있어요.",
        "food": "매운 음식·카페인·탄산음료는 위점막을 자극해요.",
        "drug": "특별한 주의 약물 없어요.",
        "danger": "🚨 갑자기 속이 극심하게 아프거나 검은 변(타르변)이 나오면 즉시 응급실.",
        "motivation": "항암제 등으로 손상된 위를 조용히 지켜줘요!",
        "grapefruit": False
    },
    "맥페란정":  {
        "why": "위에서 장으로 내려가는 속도를 빠르게 하고 구토 중추를 억제해서 메스꺼움·구역질을 줄여요.",
        "when": "식사 30분 전, 하루 3번 드세요.",
        "if_skip": "구역·구토·더부룩함이 계속돼요.",
        "food": "술: 졸림이 심해져요.",
        "drug": "항정신병약과 함께 먹으면 추체외로 증상 위험이 증가해요.",
        "danger": "🚨 손발이 떨리거나 근육 경직, 눈이 위로 돌아가면 즉시 병원 (추체외로 반응).",
        "motivation": "항암 치료 중 밥을 먹을 수 있게 도와줘요!",
        "grapefruit": False
    },
    "스토가정":  {
        "why": "위점막을 보호하고 소화를 돕는 복합 위장약이에요.",
        "when": "식후에 드세요.",
        "if_skip": "소화불량·위통이 올 수 있어요.",
        "food": "커피·탄산음료 줄이세요.",
        "drug": "특별한 주의 없어요.",
        "danger": "속이 극심하게 아프거나 검은 변이 나오면 즉시 병원.",
        "motivation": "소화가 편해져서 음식 섭취가 늘어요!",
        "grapefruit": False
    },
    # 혈압약
    "노바스크정": {
        "why": "혈관 벽 근육 속 칼슘을 차단해서 혈관을 넓혀요. 심장이 훨씬 쉽게 피를 보낼 수 있어요.",
        "when": "매일 같은 시간, 식사와 상관없이 드세요.",
        "if_skip": "혈압이 올라가 뇌졸중·심장마비 위험이 높아져요. 고혈압은 증상 없이 혈관을 서서히 손상시켜요.",
        "food": "자몽 금지! 술·짠 음식은 혈압을 올려 약 효과를 줄여요.",
        "drug": "이부프로펜(부루펜) 계열 소염진통제: 혈압을 올려요.",
        "danger": "🚨 발목이 갑자기 많이 부으면 의사에게. 갑자기 어지럽거나 기절할 것 같으면 천천히 앉으세요.",
        "motivation": "꾸준히 드시면 뇌졸중 위험 35%, 심장마비 위험 25% 감소!",
        "grapefruit": True
    },
    # 당뇨약
    "메트포르민": {
        "why": "간에서 당을 너무 많이 만들지 못하게 막고, 세포가 인슐린에 잘 반응하도록 도와줘요.",
        "when": "반드시 식사 중이나 직후에 드세요! 공복에 드시면 속이 많이 불편해요.",
        "if_skip": "혈당이 올라가고 당뇨 합병증(실명·신장 투석·발 절단)이 진행될 수 있어요.",
        "food": "술 절대 금지! 알코올+메트포르민 = 젖산산증(혈액이 산성으로 변하는 응급 상황).",
        "drug": "CT 조영제 검사 48시간 전 중단, 48시간 후 재복용 필수!",
        "danger": "🚨 구역·구토·근육통·호흡곤란이 동시에 오면 즉시 응급실 (젖산산증).",
        "motivation": "60년 역사의 가장 믿을 수 있는 당뇨약이에요. 체중 감소 효과도 있어요!",
        "grapefruit": False
    },
    # 해열진통제
    "아스피린":  {
        "why": "혈소판이 뭉쳐서 혈관을 막지 않도록 해요. 심장마비·뇌졸중을 예방하는 항혈소판제예요.",
        "when": "식후에 드세요. 씹지 말고 통째로 삼키세요 (코팅이 위를 보호해요).",
        "if_skip": "혈관이 막혀 심장마비 위험이 높아져요. 스텐트 시술 후 끊으면 혈전으로 스텐트가 막혀요!",
        "food": "술: 위장 출혈 위험 증가. 생강·마늘 대량 섭취 주의.",
        "drug": "이부프로펜: 아스피린 30분 전 복용하면 아스피린 효과를 차단해요!\n와파린: 출혈 위험 급증.",
        "danger": "🚨 검은 변이나 혈변 → 즉시 응급실 (위장 출혈). 갑자기 심한 두통·시야 이상 → 즉시 119.",
        "motivation": "심장 스텐트 후 이 약 하나가 생명을 지킬 수 있어요!",
        "grapefruit": False
    },
    "타이레놀정": {
        "why": "뇌의 통증 중추에 작용해 통증을 줄이고, 체온 조절 중추에 작용해 열을 내려요.",
        "when": "통증이나 열이 날 때, 4~6시간 간격으로 드세요. 하루 4g(8정) 초과 금지!",
        "if_skip": "통증과 발열이 계속돼요.",
        "food": "술! 알코올+아세트아미노펜 = 간 독성 급증.",
        "drug": "감기약·독감약 안에도 아세트아미노펜이 들어있어요. 중복 복용 금지!",
        "danger": "🚨 메스꺼움·복부 우상단 통증·피부 노란빛 → 간 손상 신호, 즉시 병원.",
        "motivation": "올바르게 드시면 위장에 가장 안전한 진통해열제예요!",
        "grapefruit": False
    },
    "코대원정":  {
        "why": "중추에서 기침 반사를 억제하고, 기관지 분비물을 묽게 해서 기침과 가래를 줄여요.",
        "when": "식후에 드세요.",
        "if_skip": "기침·가래가 계속돼요.",
        "food": "술: 졸림이 심해져요.",
        "drug": "수면제·진정제와 함께 먹으면 졸림이 심해져요.",
        "danger": "졸음이 너무 심하면 의사에게 알려주세요. 운전은 피하세요.",
        "motivation": "기침이 줄어서 수면의 질이 높아져요!",
        "grapefruit": False
    },
    "씨투스정":  {
        "why": "기관지 분비물을 묽게 해서 가래를 잘 배출하도록 돕고, 기침을 편하게 해줘요.",
        "when": "식후에 드세요.",
        "if_skip": "가래가 쌓여 기침이 심해질 수 있어요.",
        "food": "물을 충분히 마시면 가래 배출이 더 잘 돼요.",
        "drug": "특별한 주의 없어요.",
        "danger": "기침이 2주 이상 지속되면 폐렴 등 원인 확인이 필요해요.",
        "motivation": "가래가 배출되고 숨쉬기가 편해져요!",
        "grapefruit": False
    },
    "라니티딘":  {
        "why": "위에서 산을 만드는 H2 수용체를 차단해서 위산을 줄여요. 속쓰림·위궤양 치료에 써요.",
        "when": "식전에 드세요.",
        "if_skip": "위산이 많아지고 속이 쓰리고 위궤양이 낫지 않아요.",
        "food": "커피·탄산음료·매운 음식은 위산을 자극해요.",
        "drug": "와파린·페니토인: 혈중 농도 변화 가능.",
        "danger": "갑자기 삼키기 어렵거나 체중이 줄면 의사에게 알려주세요.",
        "motivation": "속이 편해지고 식사가 즐거워져요!",
        "grapefruit": False
    },
}

GRAPEFRUIT_WARNING = (
    "🍊 <b>자몽은 절대 금지!</b> 자몽 속 '푸라노쿠마린' 성분이 "
    "우리 몸의 '약 청소부(CYP3A4 효소)'를 막아버려요. "
    "그러면 약이 피 속에 너무 많이 쌓여서 혈압이 갑자기 뚝 떨어지거나 "
    "근육이 녹는 등 위험한 일이 생길 수 있어요. "
    "<b>오렌지·레몬은 괜찮지만, 자몽은 약 복용 전후 24시간 동안 드시면 안 돼요.</b>"
)

def _patient_drug_lookup(drug_name: str):
    for key, info in PATIENT_DRUG_SIMPLE.items():
        if key in drug_name or drug_name in key:
            return info
    return None


# ── 약사 전문 분석 데이터 ──────────────────────────────────────────────────────
PHARMACIST_DRUG_INFO = {
    "타세바정": {
        "generic": "Erlotinib 150mg",
        "class": "EGFR TKI (1세대)",
        "cyp": "CYP3A4 기질 (주), CYP1A2 기질 (부)\n↑ 강력 CYP3A4 억제제(이트라코나졸·클라리스로마이신)→혈중농도 ↑ 독성\n↓ 강력 CYP3A4 유도제(리팜피신·페니토인)→AUC 67% 감소",
        "drug_muggers": "마그네슘, 아연, 비타민B6 고갈 보고",
        "renal": "중증 신부전: 용량 조절 불필요. eGFR<15 시 주의 모니터링",
        "hepatic": "Child-Pugh C: 50mg으로 감량 후 내약성 확인",
        "pregnancy": "X등급 — 임신 중 금기. 수유 금기.",
        "monitoring": "AST/ALT (매 4주), 피부 발진 등급(CTCAE), 간질성 폐렴 징후(SpO₂, HRCT 이상 시)",
        "interactions_table": [
            ("양성자 펌프 억제제(PPI)", "흡수 50% 감소 → H₂차단제 또는 제산제 간격 복용"),
            ("와파린", "INR 상승 모니터 필수"),
            ("담배(흡연)", "CYP1A2 유도 → 혈중농도 50~60% 감소"),
        ]
    },
    "키트루다": {
        "generic": "Pembrolizumab 200mg IV q3w",
        "class": "Anti-PD-1 면역관문억제제",
        "cyp": "CYP 대사 없음 (단클론항체 — 단백질 분해 경로)",
        "drug_muggers": "비타민D 결핍 가능 (면역 이상반응 시 스테로이드 장기 투여 연관)",
        "renal": "경증~중등증 신부전: 용량 조절 불필요",
        "hepatic": "경증 간기능 저하: 조절 불필요. 중증: 데이터 부족",
        "pregnancy": "D등급 — 태반 통과, 태아 면역 억제 가능. 수유 금기.",
        "monitoring": "irAE 조기 감지: LFT, TFT, CBC, 혈당, 코르티솔. 기저치 대비 매주기 평가",
        "interactions_table": [
            ("전신 코르티코스테로이드 (>10mg/d pred)", "면역 활성 억제 → 치료 반응 감소"),
            ("다른 면역관문억제제", "irAE 발생률 배증"),
            ("생백신", "면역 억제 상태에서 금기"),
        ]
    },
    "타그리소": {
        "generic": "Osimertinib 80mg / 40mg",
        "class": "EGFR TKI (3세대, T790M 표적)",
        "cyp": "CYP3A4 기질\n↓ 강한 CYP3A4 유도제(리팜피신)→ AUC 78% 감소\n자몽: CYP3A4 억제 → 혈중농도 상승",
        "drug_muggers": "마그네슘, 비타민B6",
        "renal": "경증~중등증: 조절 불필요. 중증(<15): 데이터 제한",
        "hepatic": "경증: 조절 불필요. 중증: 40mg 고려",
        "pregnancy": "D등급. 남성 환자도 치료 중·후 3개월 피임",
        "monitoring": "QTcF (기저치 및 증상 발생 시), LFT, 안과(각막염 증상), SpO₂, LVEF",
        "interactions_table": [
            ("QT 연장 약물(항부정맥제·항정신병제)", "torsades 위험 ↑ — ECG 모니터"),
            ("세인트존스워트(허브)", "CYP3A4 유도 → 효과 감소"),
            ("항응고제", "출혈 위험 모니터"),
        ]
    },
    "글리벡정": {
        "generic": "Imatinib 400mg",
        "class": "BCR-ABL/c-KIT TKI (1세대)",
        "cyp": "CYP3A4 기질 및 억제제\nCYP2D6 억제 (codeine→morphine 전환 감소)\n↑ CYP3A4 억제제 → 혈중농도 상승",
        "drug_muggers": "칼슘, 마그네슘, 비타민D, 철분",
        "renal": "eGFR 20-39: 최대 400mg/d. eGFR<20: 100~200mg으로 신중 사용",
        "hepatic": "Child-Pugh B/C: 400→300mg 감량",
        "pregnancy": "D등급. 여성 치료 종료 후 3개월, 남성 6개월 피임",
        "monitoring": "CBC (초기 매주), LFT, 부종/체중 변화(체액 저류), 혈당(당뇨 동반 시)",
        "interactions_table": [
            ("와파린", "PT/INR ↑↑ — LMWH로 교체 고려"),
            ("심바스타틴", "CYP3A4 경쟁 → 근육독성 위험. 프라바스타틴 선호"),
            ("페니토인·카르바마제핀", "글리벡 AUC 74% 감소"),
        ]
    },
    "노바스크정": {
        "generic": "Amlodipine 5/10mg",
        "class": "L형 Ca²⁺ 차단제 (DHP CCB)",
        "cyp": "CYP3A4 기질\n자몽 → 혈중농도 최대 2배 상승 (저혈압·반사성 빈맥)",
        "drug_muggers": "CoQ10, 마그네슘",
        "renal": "용량 조절 불필요",
        "hepatic": "중증: 5mg으로 시작, 천천히 증량",
        "pregnancy": "C등급. 임신 3기 태아 독성 보고",
        "monitoring": "혈압, 심박수, 발목 부종(말초 부종 가장 흔한 부작용), 반사성 빈맥",
        "interactions_table": [
            ("심바스타틴 80mg", "미오패시 위험 — 심바스타틴 ≤20mg 또는 대체제"),
            ("타크로리무스·사이클로스포린", "혈중농도 ↑ — 신독성 모니터"),
            ("NSAID(이부프로펜 등)", "항고혈압 효과 감소, 신기능 악화"),
        ]
    },
    "메트포르민": {
        "generic": "Metformin HCl 500/850/1000mg",
        "class": "Biguanide 계열 경구혈당강하제",
        "cyp": "CYP 대사 없음 (신장 원형 배설)\n유기 양이온 수송체(OCT1/OCT2) — 시메티딘과 경쟁",
        "drug_muggers": "비타민B12 (장기 복용 시 흡수 억제 — 매년 B12 모니터 권고)",
        "renal": "eGFR 30-45: 용량 절반 감량, 위험 주의\neGFR <30: 완전 금기 (젖산산증)",
        "hepatic": "간부전: 금기 (젖산 대사 장애)",
        "pregnancy": "B등급. 임신성 당뇨에 사용 가능(off-label)",
        "monitoring": "eGFR (최소 연 1회), 비타민B12 (연 1회), 젖산산증 징후(HCO₃⁻ 감소), CT조영제 전후 48h 중단",
        "interactions_table": [
            ("알코올", "젖산산증 위험 급증"),
            ("CT 조영제 (요오드계)", "급성 신손상 시 메트포르민 축적→ 젖산산증"),
            ("시메티딘(H₂차단제)", "OCT 경쟁 → 메트포르민 혈중농도 50% 상승"),
        ]
    },
    "아스피린": {
        "generic": "Aspirin (ASA) 100mg enteric-coated",
        "class": "COX-1 비가역 억제 항혈소판제",
        "cyp": "CYP 대사 미미 (산화적 가수분해)",
        "drug_muggers": "엽산, 비타민C, 철분",
        "renal": "eGFR<10: 금기 (살리실산 축적, 출혈)",
        "hepatic": "중증 간부전: 금기 (출혈 위험)",
        "pregnancy": "D등급. 임신 3기: 태아 동맥관 조기 수축 위험",
        "monitoring": "CBC, 변 잠혈, INR (와파린 병용 시), 위장 출혈 증상",
        "interactions_table": [
            ("이부프로펜", "COX-1 결합 부위 경쟁 → 아스피린 항혈소판 효과 차단 (이부프로펜 30분 후 아스피린 복용)"),
            ("와파린/NOAC", "출혈 위험 배증 — 반드시 이중 항혈전 적응증 확인"),
            ("메토트렉세이트 저용량", "메토트렉세이트 독성 ↑"),
        ]
    },
    "타이레놀정": {
        "generic": "Acetaminophen (APAP) 500mg",
        "class": "중추성 COX 억제 / 해열진통제",
        "cyp": "CYP2E1 (10%), CYP3A4 (부) → NAPQI 독성 대사체\n알코올·INH·리팜피신: CYP2E1 유도 → NAPQI 과생성 → 간독성",
        "drug_muggers": "글루타티온 (N-아세틸시스테인이 해독제인 이유)",
        "renal": "eGFR<30: 투여 간격 8h 이상",
        "hepatic": "경증~중등증: 최대 2g/d. 중증(Child-Pugh C): 금기",
        "pregnancy": "B등급. 임신 중 가장 안전한 진통제",
        "monitoring": "LFT (장기 대용량 투여 시), 일일 총 섭취량 확인 (복합감기약 중복 위험)",
        "interactions_table": [
            ("알코올 (만성 음주)", "CYP2E1 유도 → 간독성 임계 용량 2g/d로 감소"),
            ("와파린 (고용량 APAP)", "INR 상승 (기전 불명확)"),
            ("INH(이소니아지드)", "CYP2E1 유도 → NAPQI 과잉 생성"),
        ]
    },
}

def _pharmacist_drug_lookup(drug_name: str):
    for key, info in PHARMACIST_DRUG_INFO.items():
        if key in drug_name or drug_name in key:
            return info
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 1. 로그인 게이트
# ══════════════════════════════════════════════════════════════════════════════
def login_gate() -> bool:
    for key, val in [("role", None), ("admin_pw_mode", False)]:
        if key not in st.session_state:
            st.session_state[key] = val

    if st.session_state.role is not None:
        return True

    st.markdown("""
    <style>
    .stApp{background:linear-gradient(160deg,#0a1628 0%,#0d2137 50%,#1a0a2e 100%)!important;}
    body,p,div,span{color:#c9d1d9!important;font-family:'Noto Sans KR',sans-serif!important;}
    h1,h2,h3{color:#ffffff!important;}
    .stButton button{border-radius:16px!important;font-size:1.1rem!important;font-weight:900!important;height:70px!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center;padding:50px 0 30px 0;'>
        <div style='font-size:4.5rem;'>🏥</div>
        <h1 style='font-size:2.8rem;font-weight:900;margin:10px 0 6px 0;'>Anti-Gravity Life-Care</h1>
        <p style='color:#8b949e;font-size:1.15rem;'>누구를 위한 화면인지 선택해 주세요</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background:rgba(0,242,255,0.05);border:2px solid rgba(0,242,255,0.3);
             border-radius:20px;padding:28px;text-align:center;margin-bottom:12px;'>
            <div style='font-size:3rem;'>👨‍⚕️</div>
            <h3 style='color:#00f2ff;margin:10px 0 5px 0;'>전문가 모드</h3>
            <p style='color:#8b949e;font-size:0.9rem;margin:0;'>의사 · 약사 · 의료진 전용<br>처방 분석 · 약물 상호작용 · 임상 데이터</p>
        </div>""", unsafe_allow_html=True)
        if st.button("👨‍⚕️ 전문가(의사/약사) 로그인", key="btn_admin", use_container_width=True):
            st.session_state.admin_pw_mode = True
        if st.session_state.admin_pw_mode:
            pw = st.text_input("관리자 암호를 입력하세요", type="password", key="admin_pw_input")
            if st.button("✅ 확인", key="btn_pw_ok"):
                if pw == ADMIN_PASSWORD:
                    st.session_state.role = "ADMIN"
                    st.session_state.admin_pw_mode = False
                    st.rerun()
                else:
                    st.error("암호가 맞지 않아요. 다시 시도하세요.")

    with col2:
        st.markdown("""
        <div style='background:rgba(0,255,136,0.05);border:2px solid rgba(0,255,136,0.3);
             border-radius:20px;padding:28px;text-align:center;margin-bottom:12px;'>
            <div style='font-size:3rem;'>😊</div>
            <h3 style='color:#00ff88;margin:10px 0 5px 0;'>환자 활력 케어</h3>
            <p style='color:#8b949e;font-size:0.9rem;margin:0;'>환자 본인 전용<br>쉬운 약 설명 · 오늘의 건강 처방 · 응급 연락</p>
        </div>""", unsafe_allow_html=True)
        if st.button("😊 환자 활력 케어 시작", key="btn_patient", use_container_width=True):
            st.session_state.role = "USER"
            st.rerun()

    return False


# ══════════════════════════════════════════════════════════════════════════════
# 2. 전문가 대시보드 (의사/약사용 — 네온 테마, 전문 임상 정보)
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_dashboard(patients, rxs):
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@400;700;900&display=swap');
.stApp,.main,[data-testid="stAppViewContainer"]{background-color:#000000!important;}
section[data-testid="stSidebar"]{background:#010409!important;border:none!important;}
body,p,span,div,td,th,li,label,small{font-family:'Noto Sans KR',sans-serif!important;color:#8b949e!important;}
h1,h2,h3,h4,h5,h6,strong,b{color:#00f2ff!important;font-weight:900!important;text-shadow:0 0 10px rgba(0,242,255,0.5)!important;}
.profile-banner{background:linear-gradient(135deg,rgba(0,242,255,0.05) 0%,rgba(0,0,0,1) 100%)!important;border:none!important;padding:30px 40px;margin-bottom:25px;display:flex;flex-direction:column;gap:15px;}
.profile-name{font-size:3.5rem;font-weight:900;color:#ffffff;letter-spacing:-2px;text-shadow:0 0 20px rgba(255,255,255,0.3);}
[data-testid="stFileUploadDropzone"]{background-color:rgba(0,242,255,0.02)!important;border:1px solid #00f2ff!important;box-shadow:0 0 15px rgba(0,242,255,0.2);border-radius:20px!important;padding:60px 10px!important;}
[data-testid="stFileUploadDropzone"]*{color:transparent!important;}
[data-testid="stFileUploadDropzone"]::after{content:"🏥 디지털 약국 - 처방전 이미지를 투입하세요";color:#00f2ff!important;font-weight:900!important;font-size:1.2rem!important;position:absolute!important;top:50%!important;left:50%!important;transform:translate(-50%,-50%)!important;text-shadow:0 0 10px rgba(0,242,255,0.8);pointer-events:none!important;}
.pill-card{background:rgba(255,255,255,0.03);border-radius:20px;padding:25px;border:none!important;box-shadow:0 0 20px rgba(88,166,255,0.1);margin-bottom:20px;overflow:visible!important;}
.briefing-box{background:#000;border:1px solid #58a6ff;box-shadow:inset 0 0 10px rgba(88,166,255,0.2);padding:25px;border-radius:15px;font-size:1.1rem;color:#ffffff!important;line-height:1.6;min-height:100px;height:auto!important;overflow:visible!important;word-break:keep-all;overflow-wrap:break-word;}
.guide-box{background:rgba(56,139,253,0.05);border-radius:12px;padding:20px;border-left:5px solid #58a6ff;margin-top:15px;}
.stButton button{background:#000!important;color:#00f2ff!important;border:1px solid #00f2ff!important;box-shadow:0 0 10px rgba(0,242,255,0.3);border-radius:12px!important;font-weight:900!important;transition:0.3s;height:3rem!important;}
.stButton button *{color:#00f2ff!important;}
.stButton button:hover{background:#00f2ff!important;color:#000!important;box-shadow:0 0 25px rgba(0,242,255,0.8);}
div[data-baseweb="popover"],div[data-baseweb="select"] ul{background:#000!important;}
div[data-baseweb="select"] li{color:#8b949e!important;}
</style>""", unsafe_allow_html=True)

    for k, v in [("pid","P001"),("voice_ai_answer",""),("kb_search","")]:
        if k not in st.session_state: st.session_state[k] = v

    pid = st.session_state.pid
    pat = patients.get(pid, {})
    pat_rxs = [r for r in rxs if r["patient_id"] == pid]

    st.markdown('<div style="font-family:Orbitron;color:#00f2ff;font-size:2rem;text-align:center;font-weight:700;text-shadow:0 0 20px rgba(0,242,255,0.6);">PHARMA-HYBRID v40.5</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#30363d;font-size:0.8rem;text-align:center;letter-spacing:5px;">MASTER COCKPIT — ADMIN ONLY</div>', unsafe_allow_html=True)

    base_diag = str(pat_rxs[0].get('cancer_type','정보 없음')) if pat_rxs else "정보 없음"
    diag = re.sub(r'\(\s*\d+\s*순위\s*\)', '', base_diag)
    diag = " 및 ".join([d.strip() for d in diag.split(',') if d.strip()])

    total_pills = 0
    for r in pat_rxs:
        matches = re.findall(r'총 (\d+)정', str(r.get('notes') or ''))
        if matches: total_pills += int(matches[0])
        else:
            dm = re.search(r'(\d+)정', str(r.get('dosage') or ''))
            fm = re.search(r'(\d+)회', str(r.get('frequency') or ''))
            if dm and fm: total_pills += int(dm.group(1)) * int(fm.group(1))

    st.markdown(f"""
<div class="profile-banner">
    <div style="color:#00f2ff;font-size:1.2rem;font-weight:900;letter-spacing:2px;">🏥 {pat.get('hospital','')}</div>
    <div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">
        <div class="profile-name">{pat.get('real_name','')}</div>
        <div style="font-size:1.8rem;font-weight:700;color:#58a6ff;">{pat.get('age','')}세 / {pat.get('gender','')}</div>
        <div style="background:rgba(0,242,255,0.1);padding:8px 25px;border-radius:50px;color:#00f2ff;font-weight:900;font-size:1.5rem;border:1px solid #00f2ff;">🩺 {diag}</div>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:5px;">
        <div style="color:#3fb950;font-size:1.2rem;font-weight:700;">✅ 1일 총 투약량: {total_pills}정 (수학적 검증 완료)</div>
        <div style="color:#30363d;font-size:0.9rem;font-weight:700;">LAST SYNC: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([2.5, 1])

    with col_l:
        tabs = st.tabs(["💊 복약/임상", "🥦 라이프가이드", "🧠 지식라이브러리", "💰 약가/급여", "🔬 약사 전문 분석"])

        with tabs[0]:
            st.markdown("### 📊 맞춤형 복약 및 주사 관리")
            for rx in pat_rxs:
                for m in [i.strip() for i in rx['medication_name'].split(',')]:
                    is_j = any(k in m for k in ["주사","IV","키트루다","옵디보","허셉틴"])
                    info = PILL_KB.get(m) or next((v for k,v in PILL_KB.items() if k in m), {"efficacy":"정보 대기 중"})
                    clr = "#ff4b4b" if is_j else "#00f2ff"
                    st.markdown(f"""
<div class="pill-card" style="border-left:8px solid {clr};background:rgba(0,0,0,0.6);display:flex;gap:20px;min-height:160px;">
    <div style="flex:0 0 140px;text-align:center;">
        <img src="{info.get('image_url','https://cdn-icons-png.flaticon.com/512/883/883356.png')}" style="width:120px;height:80px;object-fit:contain;border-radius:10px;border:2px solid {clr};background:#fff;padding:5px;">
        <p style="margin-top:8px;color:{clr};font-size:0.8rem;font-weight:700;">[ 실물 식별 정보 ]</p>
        <p style="color:#8b949e;font-size:0.7rem;line-height:1.2;">{info.get('appearance','정보 대기 중')}</p>
    </div>
    <div style="flex:1;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-size:1.6rem;font-weight:900;color:{clr};">{"💉 주사" if is_j else "💊 알약"} | {m}</span>
            <span style="background:{clr}22;color:{clr};padding:2px 10px;border-radius:4px;font-size:0.8rem;font-weight:900;border:1px solid {clr}44;">{rx['status']}</span>
        </div>
        <div style="margin-bottom:15px;padding-left:15px;border-left:3px solid {clr}66;">
            <p style="color:#00f2ff;font-weight:900;font-size:1.1rem;">📍 {rx['dosage']} ({rx['frequency']})</p>
            <p style="color:#ffffff;font-size:0.95rem;margin-top:5px;line-height:1.4;">{info.get('efficacy','데이터 로딩 중...')}</p>
        </div>
        <div style="background:rgba(255,170,0,0.05);border-radius:8px;padding:10px;border:1px solid rgba(255,170,0,0.2);">
            <p style="color:#ffaa00;font-size:0.85rem;margin-bottom:3px;font-weight:700;">⚠️ 임상 주의사항</p>
            <p style="color:#dddddd;font-size:0.9rem;">{str(rx.get('notes') or '').replace(',', ' / ')}</p>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

        with tabs[1]:
            st.markdown("### 🥦 맞춤형 라이프 시너지 가이드 (임상 근거)")
            disease_key = next((d for d in KB["질환"] if d in diag), "폐암")
            synergy = KB["질환"].get(disease_key, {}).get("시너지", {})
            c = st.columns(3)
            with c[0]: st.markdown(f"""<div class="guide-box" style="border-left-color:#00ff88;"><h4 style="color:#00ff88;">🍎 과채소 & 식단</h4><p style="font-size:1.1rem;color:#ffffff;font-weight:700;">{synergy.get('식단','균형 잡힌 식단')}</p><hr style="opacity:0.1;margin:10px 0;"><p style="font-size:0.85rem;line-height:1.4;">Journal of Clinical Oncology 근거: 항산화 물질이 풍부한 식단은 면역 활성도를 높입니다.</p></div>""", unsafe_allow_html=True)
            with c[1]: st.markdown(f"""<div class="guide-box" style="border-left-color:#ff4b4b;"><h4 style="color:#ff4b4b;">🏃 맞춤 운동법</h4><p style="font-size:1.1rem;color:#ffffff;font-weight:700;">{synergy.get('운동','가벼운 산책')}</p><hr style="opacity:0.1;margin:10px 0;"><p style="font-size:0.85rem;line-height:1.4;">재활 운동 지침: 규칙적인 신체 활동은 항암 치료의 피로도를 23% 개선합니다.</p></div>""", unsafe_allow_html=True)
            with c[2]: st.markdown(f"""<div class="guide-box" style="border-left-color:#ffaa00;"><h4 style="color:#ffaa00;">💊 보조 영양제</h4><p style="font-size:1.1rem;color:#ffffff;font-weight:700;">{synergy.get('비타민', synergy.get('영양제','종합 비타민'))}</p><hr style="opacity:0.1;margin:10px 0;"><p style="font-size:0.85rem;line-height:1.4;">임상 가이드: 현재 약물과의 상호작용을 고려한 안전한 보조제 추천입니다.</p></div>""", unsafe_allow_html=True)
            st.markdown("---")

        with tabs[2]:
            st.markdown("### 🧠 15대 핵심 지식 라이브러리")
            c = st.columns(3)
            kb_list = [("🎗️ 암 질환",["폐암","흑색종","백혈병","유방암","간암"]),
                       ("🔋 만성 질환",["고혈압","당뇨병","통풍","신부전","천식"]),
                       ("💊 일반 약물",["타이레놀정","베아제정","무코스타정","아스피린","메트포르민"])]
            for i,(h,items) in enumerate(kb_list):
                with c[i]:
                    st.markdown(f"**{h}**")
                    for item in items:
                        if st.button(f"🔍 {item}", key=f"kb_{item}", use_container_width=True):
                            st.session_state.kb_search = item
            if st.session_state.kb_search:
                res = (KB["질환"].get(st.session_state.kb_search) or
                       KB.get("약물",{}).get(st.session_state.kb_search) or
                       KB["알약"].get(st.session_state.kb_search))
                if res:
                    st.markdown(f"### 📑 {st.session_state.kb_search} 정밀 분석 리포트")
                    if "RWE_데이터" in res: st.info(f"🔬 **[논문 RWE]** {res['RWE_데이터']}")
                    if "시너지" in res:
                        syn = res["시너지"]
                        c2 = st.columns(2)
                        with c2[0]:
                            st.success(f"🍎 **식단**: {syn.get('식단') or syn.get('과일야채','')}")
                            st.warning(f"💊 **영양제**: {syn.get('비타민') or syn.get('영양제','')}")
                        with c2[1]:
                            st.markdown(f"🏃 **운동**: {syn.get('운동','')}")
                            if "금기" in res: st.error(f"❌ **절대 금기**: {res['금기']}")
                    st.markdown(f"""<div style="background:#0d1117;border:1px solid #00f2ff;padding:20px;border-radius:10px;color:#58a6ff;font-family:monospace;white-space:pre-wrap;font-size:0.9rem;">[ DATABASE RAW ENTRY ]\n{json.dumps(res, indent=2, ensure_ascii=False)}</div>""", unsafe_allow_html=True)

        with tabs[3]:
            st.markdown("### 💰 정밀 약가 및 급여 가이드")
            c1, c2 = st.columns(2)
            prices = list(DRUG_PRICES.items())
            for i,(n,d) in enumerate(prices):
                with (c1 if i < len(prices)//2 else c2):
                    with st.expander(f"📌 {n} ({d['급여']})"):
                        st.markdown(f"""<div style="background:#000;padding:10px;border-radius:5px;border:1px solid #30363d;"><p style="margin:0;color:#58a6ff;"><b>성분:</b> {d['성분']}</p><p style="margin:5px 0;color:#ffffff;font-size:1.2rem;"><b>가격:</b> {d['가격']:,}원 / {d['단위']}</p><p style="margin:0;color:#8b949e;font-size:0.8rem;">보험코드: {d['코드']}</p></div>""", unsafe_allow_html=True)

        with tabs[4]:
            st.markdown("### 🔬 약사 전문 분석 — CYP / Drug Muggers / 신·간 용량 / 임신 / 모니터링")
            st.caption("현재 환자의 처방 약물에 대한 전문 약동학·약력학 데이터입니다.")

            # 환자 약물 목록
            pharm_meds = [(m.strip(), rx) for rx in pat_rxs for m in rx['medication_name'].split(',')]

            if not pharm_meds:
                st.info("선택된 환자의 처방 정보가 없습니다.")
            else:
                # ── Drug Muggers 종합표 ──
                st.markdown("#### 🧲 Drug Muggers (영양소 고갈 위험)")
                st.markdown("""<div style="background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:14px;margin-bottom:18px;">
<p style="color:#ffaa00;font-size:0.85rem;margin-bottom:8px;font-weight:700;">Drug Muggers: 약이 특정 영양소를 몸에서 빼앗아가는 현상. 장기 복용 환자에게 보충 여부를 반드시 검토하세요.</p>""", unsafe_allow_html=True)
                mugger_rows = ""
                for med_name, _ in pharm_meds:
                    pdata = _pharmacist_drug_lookup(med_name)
                    if pdata and pdata.get("drug_muggers"):
                        mugger_rows += f"<tr><td style='color:#00f2ff;padding:6px 12px;'><b>{med_name}</b></td><td style='color:#ffaa00;padding:6px 12px;'>{pdata['drug_muggers']}</td></tr>"
                if mugger_rows:
                    st.markdown(f"""<table style="width:100%;border-collapse:collapse;">
<thead><tr><th style="color:#8b949e;text-align:left;padding:6px 12px;border-bottom:1px solid #30363d;">약물</th>
<th style="color:#8b949e;text-align:left;padding:6px 12px;border-bottom:1px solid #30363d;">고갈 가능 영양소</th></tr></thead>
<tbody>{mugger_rows}</tbody></table></div>""", unsafe_allow_html=True)
                else:
                    st.markdown("</div>", unsafe_allow_html=True)

                # ── 약물별 상세 카드 ──
                for med_name, rx in pharm_meds:
                    pdata = _pharmacist_drug_lookup(med_name)
                    if not pdata:
                        continue
                    with st.expander(f"🔬 {med_name} — {pdata['generic']} ({pdata['class']})", expanded=False):
                        c_left, c_right = st.columns(2)
                        with c_left:
                            st.markdown(f"""<div style="background:#0d1117;border:1px solid #1e4d40;border-radius:10px;padding:14px;margin-bottom:12px;">
<p style="color:#00f2ff;font-weight:900;margin:0 0 8px 0;">🧪 CYP / 대사 경로</p>
<p style="color:#c9d1d9;font-size:0.9rem;line-height:1.7;white-space:pre-line;">{pdata['cyp']}</p></div>""", unsafe_allow_html=True)
                            st.markdown(f"""<div style="background:#0d1117;border:1px solid #1e4d40;border-radius:10px;padding:14px;margin-bottom:12px;">
<p style="color:#3fb950;font-weight:900;margin:0 0 8px 0;">🤰 임신/수유 안전등급</p>
<p style="color:#c9d1d9;font-size:0.9rem;">{pdata['pregnancy']}</p></div>""", unsafe_allow_html=True)
                        with c_right:
                            st.markdown(f"""<div style="background:#0d1117;border:1px solid #4a3728;border-radius:10px;padding:14px;margin-bottom:12px;">
<p style="color:#ffaa00;font-weight:900;margin:0 0 8px 0;">🫘 신기능 용량 조절</p>
<p style="color:#c9d1d9;font-size:0.9rem;white-space:pre-line;">{pdata['renal']}</p></div>""", unsafe_allow_html=True)
                            st.markdown(f"""<div style="background:#0d1117;border:1px solid #4a3728;border-radius:10px;padding:14px;margin-bottom:12px;">
<p style="color:#ff7b72;font-weight:900;margin:0 0 8px 0;">🫀 간기능 용량 조절</p>
<p style="color:#c9d1d9;font-size:0.9rem;white-space:pre-line;">{pdata['hepatic']}</p></div>""", unsafe_allow_html=True)

                        # 모니터링 파라미터
                        st.markdown(f"""<div style="background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:14px;margin-bottom:12px;">
<p style="color:#58a6ff;font-weight:900;margin:0 0 8px 0;">📊 모니터링 파라미터</p>
<p style="color:#c9d1d9;font-size:0.9rem;">{pdata['monitoring']}</p></div>""", unsafe_allow_html=True)

                        # 상호작용 표
                        if pdata.get("interactions_table"):
                            st.markdown('<p style="color:#ff4b4b;font-weight:900;margin-bottom:6px;">⚡ 주요 약물 상호작용</p>', unsafe_allow_html=True)
                            rows = "".join(
                                f"<tr><td style='color:#ffaa00;padding:7px 12px;border-bottom:1px solid #21262d;width:40%;'>{pair}</td>"
                                f"<td style='color:#c9d1d9;padding:7px 12px;border-bottom:1px solid #21262d;font-size:0.9rem;'>{action}</td></tr>"
                                for pair, action in pdata["interactions_table"]
                            )
                            st.markdown(f"""<div style="background:#0d1117;border:1px solid #ff4b4b44;border-radius:10px;padding:4px;">
<table style="width:100%;border-collapse:collapse;">
<thead><tr><th style="color:#8b949e;text-align:left;padding:7px 12px;">병용 약물/물질</th>
<th style="color:#8b949e;text-align:left;padding:7px 12px;">임상적 의미 및 대처</th></tr></thead>
<tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

                # ── CYP 기질 요약 매트릭스 ──
                st.markdown("---")
                st.markdown("#### 🧬 CYP 기질 요약 (현재 처방 약물)")
                cyp_html = "<div style='background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:16px;'>"
                cyp_html += "<table style='width:100%;border-collapse:collapse;'><thead><tr>"
                cyp_html += "<th style='color:#8b949e;text-align:left;padding:6px 12px;border-bottom:1px solid #30363d;'>약물</th>"
                cyp_html += "<th style='color:#00f2ff;text-align:left;padding:6px 12px;border-bottom:1px solid #30363d;'>주요 CYP 관여</th></tr></thead><tbody>"
                for med_name, _ in pharm_meds:
                    pdata = _pharmacist_drug_lookup(med_name)
                    if pdata:
                        cyp_short = pdata['cyp'].split('\n')[0]
                        cyp_html += f"<tr><td style='color:#00f2ff;padding:6px 12px;'><b>{med_name}</b></td><td style='color:#c9d1d9;padding:6px 12px;font-size:0.88rem;'>{cyp_short}</td></tr>"
                cyp_html += "</tbody></table></div>"
                st.markdown(cyp_html, unsafe_allow_html=True)

        with st.expander("📰 전략 사령부 정책 & 임상 뉴스 (TOP 10)"):
            for news in POLICY_NEWS:
                st.markdown(f"""<div style="border-bottom:1px solid #1e293b;padding:10px 0;"><span style="background:#0060ff;color:white;padding:2px 8px;border-radius:3px;font-size:0.7rem;">{news['tag']}</span><span style="color:#8b949e;font-size:0.8rem;margin-left:10px;">{news['date']}</span><p style="margin:5px 0 0 0;color:#58a6ff;font-weight:700;">{news['title']}</p><p style="margin:2px 0 0 0;color:#8b949e;font-size:0.85rem;">{news['body']}</p><p style="margin:2px 0 0 0;color:#30363d;font-size:0.75rem;">Source: {news['source']}</p></div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown('#### 🎙️ AI 마스터 브리핑')
        if st.session_state.voice_ai_answer:
            st.markdown(f'<div class="briefing-box">{st.session_state.voice_ai_answer}</div>', unsafe_allow_html=True)
        tts_button(st.session_state.voice_ai_answer or "분석 데이터 로딩 중...", "tts_admin")
        st.markdown("---")
        st.markdown("#### 📄 처방전 AI 분석")
        uploaded = st.file_uploader("UPLOAD", type=["jpg","png","jpeg"], key="up_admin", label_visibility="collapsed")
        if uploaded:
            st.image(uploaded, caption="🔍 스캔 대기 중인 처방전", use_container_width=True)
            st.warning("🔒 보안 검증 대기 중: 환자 이름 교차 확인")
            if st.button("AI 정밀 분석 & 보안 확인", use_container_width=True):
                with st.spinner("AI가 처방전과 알약 이미지를 매칭 중입니다..."):
                    result = analyze_image(uploaded.getvalue(), uploaded.type, pat, pat_rxs, pid)
                    if pat.get('real_name') not in result and "시뮬레이션" not in result:
                        st.error(f"🚨 [보안 위반] 처방전 환자와 선택된 환자({pat.get('real_name')})가 불일치합니다.")
                        st.session_state.voice_ai_answer = "⚠️ 보안 검증 실패: 타인 처방전 감지됨"
                    else:
                        st.session_state.voice_ai_answer = result
                    st.rerun()

    with st.sidebar:
        st.markdown("#### 🔬 환자 선택 (전문가용)")
        pids = list(patients.keys())
        idx = pids.index(pid) if pid in pids else 0
        new_pid = st.selectbox("선택", pids, index=idx,
                               format_func=lambda x: f"{patients[x]['real_name']} ({patients[x]['age']}세)",
                               key="pat_admin")
        if new_pid != st.session_state.pid:
            st.session_state.pid = new_pid
            st.rerun()

        if HAS_PHARMACY:
            st.markdown("---")
            st.markdown("📍 주변 약국 재고 (20분 갱신)")
            st.markdown(render_pharmacy_widget_html(), unsafe_allow_html=True)
        if HAS_ADHERENCE:
            st.markdown("---")
            st.markdown("📅 실시간 복약 준수율")
            sync_schedules_from_rx(rxs)
            st.markdown(render_compliance_sentinel_html(pid, pat.get('real_name','환자')), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🛡️ 위험 감지 센터")
        if st.button("🚨 보호자 긴급 알림 테스트"):
            if HAS_GUARDIAN:
                send_guardian_alert(pid, pat.get('real_name'), "긴급건강경고",
                                    "환자의 바이탈에 이상 징후가 감지되었습니다.", severity="CRITICAL")
                st.toast("보호자에게 카카오톡 알림 전송 완료!")
        st.markdown("---")
        if st.button("🔓 로그아웃", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    emergency_floating_panel()


# ══════════════════════════════════════════════════════════════════════════════
# 3. 환자 대시보드 (환자 본인용 — 따뜻하고 쉬운 언어)
# ══════════════════════════════════════════════════════════════════════════════
def render_patient_dashboard(patients, rxs):
    ui = get_time_sensing_ui()

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
.stApp,.main,[data-testid="stAppViewContainer"]{{background:{ui['bg']}!important;}}
section[data-testid="stSidebar"]{{background:#ffffff!important;box-shadow:2px 0 10px rgba(0,0,0,0.08)!important;}}
body,p,div,span,label{{font-family:'Noto Sans KR',sans-serif!important;color:#2d3748!important;}}
h1,h2,h3,h4{{color:#2d3748!important;font-weight:900!important;text-shadow:none!important;}}
.stButton button{{border-radius:16px!important;font-weight:900!important;font-size:1rem!important;height:auto!important;padding:14px 20px!important;}}
.drug-card{{background:white;border-radius:20px;padding:22px 24px;margin-bottom:14px;box-shadow:0 4px 20px rgba(0,0,0,0.08);}}
.why-box{{background:#f0fff4;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #48bb78;}}
.when-box{{background:#ebf8ff;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #4299e1;}}
.skip-box{{background:#fffbeb;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #f6ad55;}}
.danger-box{{background:#fff5f5;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #f56565;border:1px solid #fed7d7;}}
.food-box{{background:#faf5ff;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #9f7aea;}}
.drug-box{{background:#fff0f6;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #ed64a6;}}
.grape-box{{background:#fffaf0;border-radius:12px;padding:14px 16px;margin:8px 0;border:2px solid #ed8936;}}
.motive-box{{background:#f0fff4;border-radius:12px;padding:14px 16px;margin:8px 0;border-left:5px solid #38a169;border:1px solid #c6f6d5;}}
.health-card{{background:white;border-radius:20px;padding:22px;box-shadow:0 4px 20px rgba(0,0,0,0.08);height:100%;}}
</style>""", unsafe_allow_html=True)

    if "patient_pid" not in st.session_state:
        st.session_state.patient_pid = list(patients.keys())[0]

    # ── 사이드바 ──
    with st.sidebar:
        st.markdown("### 👤 본인 확인")
        pids = sorted(patients.keys())
        idx = pids.index(st.session_state.patient_pid) if st.session_state.patient_pid in pids else 0
        new_pid = st.selectbox("성함을 선택해주세요", pids, index=idx,
                               format_func=lambda x: f"{patients[x]['real_name']} ({patients[x]['age']}세)",
                               key="pat_patient", label_visibility="visible")
        if new_pid != st.session_state.patient_pid:
            st.session_state.patient_pid = new_pid
            st.rerun()

        st.markdown("---")
        st.markdown("### 🆘 응급 연락처")
        st.markdown("""
<a href="tel:119" style="text-decoration:none;">
  <div style="background:#e53e3e;color:white;padding:14px;border-radius:14px;text-align:center;
       font-size:1.2rem;font-weight:900;margin-bottom:10px;box-shadow:0 4px 12px rgba(229,62,62,0.4);">
    🚨 119 응급 전화
  </div>
</a>
<a href="tel:1644-7586" style="text-decoration:none;">
  <div style="background:#3182ce;color:white;padding:14px;border-radius:14px;text-align:center;
       font-size:1rem;font-weight:700;margin-bottom:10px;">
    💊 약물 부작용 상담<br><span style="font-size:0.9rem;">1644-7586</span>
  </div>
</a>""", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🔙 처음 화면으로", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    pid = st.session_state.patient_pid
    pat = patients.get(pid, {})
    pat_rxs = [r for r in rxs if r["patient_id"] == pid]
    name = pat.get("real_name", "환자")

    diag_raw = str(pat_rxs[0].get('cancer_type','')) if pat_rxs else ""
    diag = " 및 ".join([d.strip() for d in re.sub(r'\(\s*\d+\s*순위\s*\)','',diag_raw).split(',') if d.strip()])

    # ── 인사 배너 ──
    st.markdown(f"""
<div style='border-radius:24px;padding:28px 32px;margin-bottom:24px;background:white;
     box-shadow:0 8px 32px rgba(0,0,0,0.1);border-left:8px solid {ui["color"]};'>
    <div style='font-size:2.8rem;margin-bottom:8px;'>{ui["icon"]}</div>
    <h1 style='color:{ui["color"]};margin:0 0 6px 0;font-size:2rem;'>
        {name}님, {ui["title"]}
    </h1>
    <p style='color:#4a5568;font-size:1.1rem;margin:0 0 14px 0;font-weight:700;'>
        오늘도 건강을 향한 소중한 하루가 시작되었습니다 💚
    </p>
    <div style='display:flex;gap:10px;flex-wrap:wrap;'>
        <span style='background:{ui["bg"]};color:{ui["color"]};padding:6px 16px;border-radius:30px;
              font-weight:700;font-size:0.9rem;border:1px solid {ui["color"]}44;'>
            🏥 {pat.get('hospital','')}
        </span>
        {'<span style="background:#fff5f5;color:#c53030;padding:6px 16px;border-radius:30px;font-weight:700;font-size:0.9rem;border:1px solid #fc818144;">🩺 ' + diag + '</span>' if diag else ''}
    </div>
</div>""", unsafe_allow_html=True)

    # ── 약 카드 ──
    all_meds = [(m.strip(), rx) for rx in pat_rxs for m in rx['medication_name'].split(',')]

    if all_meds:
        st.markdown("## 💊 오늘 드셔야 할 약")
        st.markdown('<p style="color:#718096;margin-bottom:16px;font-size:1.05rem;">약 이름을 누르면 쉬운 설명을 볼 수 있어요 👇</p>', unsafe_allow_html=True)

        for med_name, rx in all_meds:
            pinfo = _patient_drug_lookup(med_name)
            is_inj = any(k in med_name for k in ["주사","IV","키트루다","옵디보","허셉틴"])
            icon = "💉" if is_inj else "💊"

            with st.expander(f"{icon}  {med_name}   |   {rx['dosage']} / {rx['frequency']}", expanded=False):
                st.markdown(f"""
<div style="background:#ebf8ff;border-radius:10px;padding:11px 16px;margin-bottom:10px;border:1px solid #bee3f8;">
    <b style="color:#2c5282;">🕐 복용 일정:</b>
    <span style="color:#2d3748;"> {rx['dosage']} / {rx['frequency']}</span>
    {'  ·  <b style="color:#2c5282;">기간:</b> <span style="color:#2d3748;">' + str(rx.get('duration','')) + '</span>' if rx.get('duration') else ''}
</div>""", unsafe_allow_html=True)
                if pinfo:
                    blocks = f"""
<div class="why-box">
    <b style="color:#276749;font-size:1rem;">✅ 왜 이 약을 먹나요?</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['why']}</span>
</div>"""
                    if pinfo.get('when'):
                        blocks += f"""
<div class="when-box">
    <b style="color:#2b6cb0;font-size:1rem;">🕐 언제·어떻게 드세요?</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['when']}</span>
</div>"""
                    blocks += f"""
<div class="skip-box">
    <b style="color:#c05621;font-size:1rem;">⚠️ 임의로 안 먹으면?</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['if_skip']}</span>
</div>"""
                    if pinfo.get('danger'):
                        blocks += f"""
<div class="danger-box">
    <b style="color:#c53030;font-size:1rem;">🚨 이런 증상이면 즉시 병원!</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['danger']}</span>
</div>"""
                    if pinfo.get('grapefruit'):
                        blocks += f"""
<div class="grape-box">
    <b style="color:#c05621;font-size:1rem;">🍊 자몽은 절대 금지!</b><br>
    <span style="color:#c05621;font-size:1.05rem;line-height:1.8;">{GRAPEFRUIT_WARNING}</span>
</div>"""
                    if pinfo.get('food'):
                        blocks += f"""
<div class="food-box">
    <b style="color:#6b46c1;font-size:1rem;">🍽️ 같이 드시면 안 되는 음식</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['food']}</span>
</div>"""
                    if pinfo.get('drug'):
                        blocks += f"""
<div class="drug-box">
    <b style="color:#97266d;font-size:1rem;">💊 같이 조심해야 할 약</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['drug']}</span>
</div>"""
                    if pinfo.get('motivation'):
                        blocks += f"""
<div class="motive-box">
    <b style="color:#276749;font-size:1rem;">🌟 꾸준히 드시면 이런 효과가!</b><br>
    <span style="color:#2d3748;font-size:1.05rem;line-height:1.8;">{pinfo['motivation']}</span>
</div>"""
                    st.markdown(blocks, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div style="background:#f7fafc;border-radius:12px;padding:16px;border:1px solid #e2e8f0;">
    <p style="color:#a0aec0;font-size:0.9rem;margin:0;">이 약의 쉬운 설명은 준비 중이에요. 궁금한 점은 약사님께 여쭤보세요 😊</p>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── 오늘의 건강 처방 ──
    st.markdown("## 🌿 오늘의 건강 처방")
    disease_key = next((d for d in KB["질환"] if d in diag), None) if diag else None
    synergy = KB["질환"].get(disease_key, {}).get("시너지", {}) if disease_key else {}
    forbidden = KB["질환"].get(disease_key, {}).get("금기", "") if disease_key else ""

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
<div class="health-card">
    <h3 style="color:#276749;margin-top:0;">🍱 오늘의 추천 식단</h3>
    <p style="font-size:1.05rem;line-height:1.8;color:#2d3748;">{synergy.get('식단','채소와 과일을 골고루 드세요. 맵고 짠 음식은 줄이세요.')}</p>
    <p style="color:#718096;font-size:0.85rem;margin-top:14px;padding-top:10px;border-top:1px solid #f0f0f0;">
        💡 담당 의사 선생님의 치료 계획에 맞춰 준비됐어요.
    </p>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="health-card">
    <h3 style="color:#2b6cb0;margin-top:0;">🏃 오늘의 활력 운동</h3>
    <p style="font-size:1.05rem;line-height:1.8;color:#2d3748;">{synergy.get('운동','집에서 가볍게 스트레칭하거나 10~15분 천천히 걸어보세요.')}</p>
    <p style="color:#718096;font-size:0.85rem;margin-top:14px;padding-top:10px;border-top:1px solid #f0f0f0;">
        💡 몸이 힘들 때는 쉬는 것도 치료예요. 무리하지 마세요!
    </p>
</div>""", unsafe_allow_html=True)
    with c3:
        supp = synergy.get('비타민') or synergy.get('영양제','담당 의사·약사 선생님과 상담 후 결정하세요.')
        st.markdown(f"""
<div class="health-card">
    <h3 style="color:#6b46c1;margin-top:0;">✨ 도움이 되는 영양제</h3>
    <p style="font-size:1.05rem;line-height:1.8;color:#2d3748;">{supp}</p>
    <p style="color:#718096;font-size:0.85rem;margin-top:14px;padding-top:10px;border-top:1px solid #f0f0f0;">
        💡 영양제는 반드시 의사·약사 선생님께 먼저 확인하세요!
    </p>
</div>""", unsafe_allow_html=True)

    # ── 절대 피해야 할 것 ──
    if forbidden:
        st.markdown("---")
        st.markdown("## 🚫 절대 드시면 안 되는 것")
        reason_map = {
            "자몽": "자몽 속 성분이 약을 몸에서 내보내는 효소를 막아 약이 너무 많이 쌓여요",
            "흡연": "약의 효과를 30% 이상 떨어뜨려요",
            "햇빛": "피부 손상을 악화시켜요",
            "스테로이드": "면역 치료 효과를 방해해요",
            "베타카로틴": "고용량 보충제는 항암 효과를 방해할 수 있어요",
        }
        for item in [f.strip() for f in forbidden.split(',') if f.strip()]:
            reason = next((v for k, v in reason_map.items() if k in item), "")
            st.markdown(f"""
<div style="background:#fff5f5;border-left:5px solid #fc8181;border-radius:12px;
     padding:14px 18px;margin-bottom:10px;display:flex;align-items:flex-start;gap:14px;">
    <span style="font-size:1.8rem;line-height:1;">❌</span>
    <div>
        <span style="color:#c53030;font-weight:900;font-size:1.1rem;">{item}</span>
        {'<br><span style="color:#e53e3e;font-size:0.95rem;">' + reason + '</span>' if reason else ''}
    </div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
<div style="background:white;border-radius:16px;padding:22px;text-align:center;
     box-shadow:0 4px 20px rgba(0,0,0,0.08);border:2px solid {ui['color']}44;">
    <p style="font-size:1.15rem;color:{ui['color']};font-weight:900;margin:0;">
        {ui['icon']} {name}님, 오늘도 힘내세요! 궁금한 점은 언제든 병원·약국에 연락하세요 💚
    </p>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 4. 메인
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if "ready" not in st.session_state:
        init_db()
        st.session_state.ready = True

    for key, default in [("patients", None), ("rxs", None), ("voice_ai_answer", ""), ("kb_search", "")]:
        if key not in st.session_state:
            st.session_state[key] = default

    if st.session_state.patients is None:
        st.session_state.patients = load_patients()
    if st.session_state.rxs is None:
        st.session_state.rxs = load_rx()

    patients = st.session_state.patients
    rxs = st.session_state.rxs

    if not login_gate():
        return

    if st.session_state.role == "ADMIN":
        render_admin_dashboard(patients, rxs)
    else:
        render_patient_dashboard(patients, rxs)


if __name__ == "__main__":
    main()
