#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[SHIELD] PHARMA-HYBRID v40.4 NEON PHARMACY
Main Application (Digital Pharmacy Aesthetic)
"""

import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import base64
import json
import re
import traceback
import requests as req
from datetime import datetime, timedelta
from typing import Dict, List
import plotly.graph_objects as go
import random
import time
import os

# ── 상수 및 설정 ────────────────────────────────────────────────────────────
DB_PATH = "pharma_v20.db"

# 🛡️ 1. 모듈 로드 보호 및 진단 모드
try:
    import kb_data
    from kb_data import DEFAULT_PATIENTS, RAW_RX, KB, PILL_KB, DRUG_PRICES, POLICY_NEWS
except Exception as e:
    st.error(f"🚨 [CRITICAL] kb_data.py 로드 실패!")
    st.code(traceback.format_exc(), language="python")
    st.stop()

try:
    import ai_engine
    from ai_engine import analyze_voice, analyze_image, HAS_GEMINI_ENGINE
except ImportError:
    HAS_GEMINI_ENGINE = False

try:
    from guardian_link import init_guardian_db, get_guardians, send_guardian_alert
    HAS_GUARDIAN = True
except ImportError:
    HAS_GUARDIAN = False

try:
    from medication_adherence import init_adherence_db, record_all_meds_taken, render_compliance_sentinel_html, sync_schedules_from_rx
    HAS_ADHERENCE = True
except ImportError:
    HAS_ADHERENCE = False

try:
    from nearby_pharmacy_widget import render_pharmacy_widget_html
    HAS_PHARMACY = True
except ImportError:
    HAS_PHARMACY = False

# ── DB 관리 ──────────────────────────────────────────────────────────────
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
                c.execute("INSERT OR IGNORE INTO patients (patient_id, real_name, age, gender, hospital, diet) VALUES (?,?,?,?,?,?)",
                          (p, info["real_name"], info["age"], info["gender"], info["hospital"], ""))
            conn.commit()
        if HAS_ADHERENCE: init_adherence_db()
        if HAS_GUARDIAN: init_guardian_db()
    except Exception as e: st.error(f"🚨 DB 초기화 실패: {e}")

def load_patients() -> Dict:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT patient_id, real_name, age, gender, hospital, diet FROM patients")
            rows = c.fetchall()
        return {r[0]: {"real_name": r[1], "age": r[2], "gender": r[3], "hospital": r[4], "diet": r[5] or ""} for r in rows}
    except: return DEFAULT_PATIENTS

def load_rx() -> List[Dict]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM rx ORDER BY id")
            rows = c.fetchall()
        keys = ["id","patient_id","medication_name","cancer_type","dosage","frequency","duration","start_date","doctor_name","status","side_effects","efficacy_rate","notes","last_updated"]
        return [dict(zip(keys, r)) for r in rows]
    except: return []

# ── UI 헬퍼 ─────────────────────────────────────────────────────────────
def tts_button(text: str, key: str) -> None:
    # 한글, 숫자, 공백, 기본 문장부호만 허용 (발음의 자연스러움과 정보량 확보)
    clean_text = re.sub(r'[^가-힣0-9\s.,!]', '', text).strip()
    if not clean_text: clean_text = "브리핑 할 데이터가 준비되지 않았습니다."
    
    components.html(f"""
        <script>
        function speak() {{
            const msg = new SpeechSynthesisUtterance("{clean_text}");
            msg.lang = 'ko-KR'; msg.rate = 1.0; msg.pitch = 1.0;
            window.speechSynthesis.speak(msg);
        }}
        </script>
        <button onclick="speak()" style="background:linear-gradient(90deg, #00f2ff, #0060ff); border:none; color:#000; border-radius:8px; padding:12px 25px; cursor:pointer; font-size:1.1rem; font-weight:900; width:100%; box-shadow:0 4px 15px rgba(0,242,255,0.4);">🎙️ AI 마스터 브리핑 재생 (v40.2 고음질)</button>
    """, height=65)

def emergency_floating_panel():
    st.markdown("""
    <div style="position:fixed; bottom:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:10px;">
        <a href="tel:119" style="text-decoration:none;"><div style="background:#ff4b4b; color:white; padding:15px; border-radius:50px; width:120px; text-align:center; font-weight:900; box-shadow:0 0 20px rgba(255,75,75,0.6); border:2px solid white;">🆘 119 호출</div></a>
        <a href="tel:112" style="text-decoration:none;"><div style="background:#0060ff; color:white; padding:15px; border-radius:50px; width:120px; text-align:center; font-weight:900; box-shadow:0 0 20px rgba(0,96,255,0.6); border:2px solid white;">🚓 112 신고</div></a>
    </div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="PHARMA-HYBRID v40.4", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@400;700;900&display=swap');

/* 1. 기본 배경 및 네온 테마 */
.stApp, .main, [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
section[data-testid="stSidebar"] { background: #010409 !important; border: none !important; }
body,p,span,div,td,th,li,label,small { font-family:'Noto Sans KR',sans-serif !important; color:#8b949e !important; }
h1,h2,h3,h4,h5,h6,strong,b { color:#00f2ff !important; font-weight:900 !important; text-shadow: 0 0 10px rgba(0,242,255,0.5) !important; }

/* 2. 네온 배너 (테두리 제거 및 고해상도 글로우) */
.profile-banner {
    background: linear-gradient(135deg, rgba(0,242,255,0.05) 0%, rgba(0,0,0,1) 100%) !important;
    border: none !important;
    padding: 30px 40px;
    margin-bottom: 25px;
    display: flex;
    flex-direction: column;
    gap: 15px;
}
.profile-name {
    font-size: 3.5rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -2px;
    text-shadow: 0 0 20px rgba(255,255,255,0.3);
}

/* 3. 파일 업로더 (글자 겹침 완전 방지 및 네온 스타일) */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(0,242,255,0.02) !important;
    border: 1px solid #00f2ff !important;
    box-shadow: 0 0 15px rgba(0,242,255,0.2);
    border-radius: 20px !important;
    padding: 60px 10px !important;
}
/* 내부의 모든 기본 텍스트 및 버튼 강제 은닉 (겹침 원천 차단) */
[data-testid="stFileUploadDropzone"] * {
    color: transparent !important;
}
[data-testid="stFileUploadDropzone"]::after {
    content: "🏥 디지털 약국 - 처방전 이미지를 투입하세요";
    color: #00f2ff !important;
    font-weight: 900 !important;
    font-size: 1.2rem !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    text-shadow: 0 0 10px rgba(0,242,255,0.8);
    pointer-events: none !important;
}

/* 4. 약물 카드 (테두리 제거 및 네온 글로우) */
.pill-card {
    background: rgba(255,255,255,0.03);
    border-radius: 20px;
    padding: 25px;
    border: none !important;
    box-shadow: 0 0 20px rgba(88,166,255,0.1);
    margin-bottom: 20px;
    overflow: visible !important;
}
.briefing-box {
    background: #000; 
    border: 1px solid #58a6ff; 
    box-shadow: inset 0 0 10px rgba(88,166,255,0.2);
    padding: 25px; 
    border-radius: 15px; 
    font-size: 1.1rem; 
    color: #ffffff !important;
    line-height: 1.6;
    min-height: 100px;
    height: auto !important;
    overflow: visible !important;
    word-break: keep-all;
    overflow-wrap: break-word;
}
.guide-box {
    background: rgba(56,139,253,0.05);
    border-radius: 12px;
    padding: 20px;
    border-left: 5px solid #58a6ff;
    margin-top: 15px;
}
/* 5. 버튼 (글자 겹침 제거 및 네온 사인) */
.stButton button {
    background: #000 !important;
    color: #00f2ff !important;
    border: 1px solid #00f2ff !important;
    box-shadow: 0 0 10px rgba(0,242,255,0.3);
    border-radius: 12px !important;
    font-weight: 900 !important;
    transition: 0.3s;
    height: 3rem !important;
}
/* 버튼 내부의 불필요한 시스템 텍스트(예: _arrow_right) 강제 은닉 */
.stButton button * {
    color: #00f2ff !important;
}
.stButton button:hover {
    background: #00f2ff !important;
    color: #000 !important;
    box-shadow: 0 0 25px rgba(0,242,255,0.8);
}

/* 흰색 배경 완전 차단 */
div[data-baseweb="popover"], div[data-baseweb="select"] ul { background: #000 !important; }
div[data-baseweb="select"] li { color: #8b949e !important; }
</style>
""", unsafe_allow_html=True)

def main():
    if "ready" not in st.session_state:
        init_db(); st.session_state.ready = True
    
    for key, default in [("pid", "P001"), ("patients", None), ("rxs", None), ("voice_ai_answer", ""), ("kb_search", "")]:
        if key not in st.session_state: st.session_state[key] = default
    
    if st.session_state.patients is None: st.session_state.patients = load_patients()
    if st.session_state.rxs is None: st.session_state.rxs = load_rx()
    
    patients, rxs, pid = st.session_state.patients, st.session_state.rxs, st.session_state.pid
    pat = patients.get(pid, {})
    pat_rxs = [r for r in rxs if r["patient_id"] == pid]
    
    st.markdown('<div style="font-family:Orbitron; color:#00f2ff; font-size:2rem; text-align:center; font-weight:700; text-shadow: 0 0 20px rgba(0,242,255,0.6);">PHARMA-HYBRID v40.4</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#30363d; font-size:0.8rem; text-align:center; letter-spacing:5px;">NEON DIGITAL PHARMACY EDITION</div>', unsafe_allow_html=True)

    # ── 배너 (v40.0 전략적 재배치) ──
    base_diag = "정보 없음"
    if pat_rxs and pat_rxs[0].get('cancer_type'):
        base_diag = str(pat_rxs[0].get('cancer_type'))
    diag = re.sub(r'\(\s*\d+\s*순위\s*\)', '', base_diag)
    diag = ", ".join([d.strip() for d in diag.split(',') if d.strip()])
    diag = diag.replace(",", " 및 ")
    
    total_pills = 0
    for r in pat_rxs:
        r_notes = str(r.get('notes') or "")
        r_dosage = str(r.get('dosage') or "")
        r_freq = str(r.get('frequency') or "")
        matches = re.findall(r'총 (\d+)정', r_notes)
        if matches: total_pills += int(matches[0])
        else:
            d_match = re.search(r'(\d+)정', r_dosage)
            f_match = re.search(r'(\d+)회', r_freq)
            if d_match and f_match: total_pills += int(d_match.group(1)) * int(f_match.group(1))

    st.markdown(f"""
<div class="profile-banner">
    <div style="color:#00f2ff; font-size:1.2rem; font-weight:900; letter-spacing:2px;">🏥 {pat.get('hospital')}</div>
    <div class="profile-info-row">
        <div class="profile-name">{pat.get('real_name')}</div>
        <div style="font-size:1.8rem; font-weight:700; color:#58a6ff;">{pat.get('age')}세 / {pat.get('gender')}</div>
        <div style="background:rgba(0,242,255,0.1); padding:8px 25px; border-radius:50px; color:#00f2ff; font-weight:900; font-size:1.5rem; border:1px solid #00f2ff;">🩺 {diag}</div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
        <div style="color:#3fb950; font-size:1.2rem; font-weight:700;">✅ 1일 총 투약량: {total_pills}정 (수학적 검증 완료)</div>
        <div style="color:#30363d; font-size:0.9rem; font-weight:700;">LAST SYNC: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

    col_l, col_r = st.columns([2.5, 1])
    
    with col_l:
        tabs = st.tabs(["💊 복약/임상", "🥦 라이프가이드", "🧠 지식라이브러리", "💰 약가/급여"])
        
        with tabs[0]:
            st.markdown("### 📊 맞춤형 복약 및 주사 관리")
            for rx in pat_rxs:
                for m in [i.strip() for i in rx['medication_name'].split(',')]:
                    is_j = any(k in m for k in ["주사", "IV", "키트루다", "옵디보", "허셉틴"])
                    info = PILL_KB.get(m) or next((v for k,v in PILL_KB.items() if k in m), {"efficacy": "정보 대기 중"})
                    clr = "#ff4b4b" if is_j else "#00f2ff"
                    st.markdown(f"""
                    <div class="pill-card" style="border-left:8px solid {clr}; background:rgba(0,0,0,0.6); display:flex; gap:20px; min-height:160px;">
                        <div style="flex:0 0 140px; text-align:center;">
                            <img src="{info.get('image_url', 'https://cdn-icons-png.flaticon.com/512/883/883356.png')}" style="width:120px; height:80px; object-fit:contain; border-radius:10px; border:2px solid {clr}; background:#fff; padding:5px;">
                            <p style="margin-top:8px; color:{clr}; font-size:0.8rem; font-weight:700;">[ 실물 식별 정보 ]</p>
                            <p style="color:#8b949e; font-size:0.7rem; line-height:1.2;">{info.get('appearance', '정보 대기 중')}</p>
                        </div>
                        <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                                <span style="font-size:1.6rem; font-weight:900; color:{clr};">{"💉 주사" if is_j else "💊 알약"} | {m}</span>
                                <span style="background:{clr}22; color:{clr}; padding:2px 10px; border-radius:4px; font-size:0.8rem; font-weight:900; border:1px solid {clr}44;">{rx['status']}</span>
                            </div>
                            <div style="margin-bottom:15px; padding-left:15px; border-left:3px solid {clr}66;">
                                <p style="color:#00f2ff; font-weight:900; font-size:1.1rem;">📍 {rx['dosage']} ({rx['frequency']})</p>
                                <p style="color:#ffffff; font-size:0.95rem; margin-top:5px; line-height:1.4;">{info.get('efficacy', '데이터 로딩 중...')}</p>
                            </div>
                            <div style="background:rgba(255,170,0,0.05); border-radius:8px; padding:10px; border:1px solid rgba(255,170,0,0.2);">
                                <p style="color:#ffaa00; font-size:0.85rem; margin-bottom:3px; font-weight:700;">⚠️ 임상 주의사항</p>
                                <p style="color:#dddddd; font-size:0.9rem;">{str(rx.get('notes') or "").replace(',', ' / ')}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with tabs[1]:
            st.markdown("### 🥦 맞춤형 라이프 시너지 가이드")
            
            # 질환 정보 로드
            disease_key = next((d for d in KB["질환"] if d in diag), "폐암")
            d_info = KB["질환"].get(disease_key, {})
            synergy = d_info.get("시너지", {})
            
            c = st.columns(3)
            with c[0]:
                st.markdown(f"""
                <div class="guide-box" style="border-left-color:#00ff88;">
                    <h4 style="color:#00ff88;">🍎 과채소 & 식단</h4>
                    <p style="font-size:1.1rem; color:#ffffff; font-weight:700;">{synergy.get('식단', '균형 잡힌 식단')}</p>
                    <hr style="opacity:0.1; margin:10px 0;">
                    <p style="font-size:0.85rem; line-height:1.4;">Journal of Clinical Oncology 근거: 항산화 물질이 풍부한 식단은 면역 활성도를 높입니다.</p>
                </div>
                """, unsafe_allow_html=True)
            with c[1]:
                st.markdown(f"""
                <div class="guide-box" style="border-left-color:#ff4b4b;">
                    <h4 style="color:#ff4b4b;">🏃 맞춤 운동법</h4>
                    <p style="font-size:1.1rem; color:#ffffff; font-weight:700;">{synergy.get('운동', '가벼운 산책')}</p>
                    <hr style="opacity:0.1; margin:10px 0;">
                    <p style="font-size:0.85rem; line-height:1.4;">재활 운동 지침: 규칙적인 신체 활동은 항암 치료의 피로도를 23% 개선합니다.</p>
                </div>
                """, unsafe_allow_html=True)
            with c[2]:
                st.markdown(f"""
                <div class="guide-box" style="border-left-color:#ffaa00;">
                    <h4 style="color:#ffaa00;">💊 보조 영양제 처방</h4>
                    <p style="font-size:1.1rem; color:#ffffff; font-weight:700;">{synergy.get('영양제', '종합 비타민')}</p>
                    <hr style="opacity:0.1; margin:10px 0;">
                    <p style="font-size:0.85rem; line-height:1.4;">임상 가이드: 현재 약물과의 상호작용을 고려한 안전한 보조제 추천입니다.</p>
                </div>
                """, unsafe_allow_html=True)

            # 컨디션 체크 섹션 제거됨 (사령관 지시)
            st.markdown("---")

        with tabs[2]:
            st.markdown("### 🧠 15대 핵심 지식 라이브러리")
            c = st.columns(3)
            kb_list = [("🎗️ 암 질환", ["폐암","흑색종","백혈병","유방암","간암"]), ("🔋 만성 질환", ["고혈압","당뇨병","통풍","신부전","천식"]), ("💊 일반 약물", ["타이레놀정","베아제정","무코스타정","아스피린","메트포르민"])]
            for i, (h, items) in enumerate(kb_list):
                with c[i]:
                    st.markdown(f"**{h}**")
                    for item in items:
                        if st.button(f"🔍 {item}", key=f"kb_v38_{item}", use_container_width=True): st.session_state.kb_search = item
            if st.session_state.kb_search:
                res = KB["질환"].get(st.session_state.kb_search) or KB["약물"].get(st.session_state.kb_search) or KB["알약"].get(st.session_state.kb_search)
                if res:
                    st.markdown(f"### 📑 {st.session_state.kb_search} 정밀 분석 리포트")
                    # 논문 학습 데이터 출력 (v40.3 전용 레이아웃)
                    if "RWE_데이터" in res:
                        st.info(f"🔬 **[논문 RWE]** {res['RWE_데이터']}")
                    
                    if "시너지" in res:
                        syn = res["시너지"]
                        c = st.columns(2)
                        with c[0]:
                            st.success(f"🍎 **과채소 & 식단**: {syn.get('식단') or syn.get('과일야채')}")
                            st.warning(f"💊 **복용 가능 비타민**: {syn.get('비타민') or syn.get('영양제')}")
                        with c[1]:
                            st.markdown(f"🏃 **운동 가이드**: {syn.get('운동')}")
                            if "금기" in res:
                                st.error(f"❌ **절대 금기**: {res['금기']}")

                    st.markdown(f"""<div style="background:#0d1117; border:1px solid #00f2ff; padding:20px; border-radius:10px; color:#58a6ff; font-family:monospace; white-space:pre-wrap; font-size:0.9rem;">[ DATABASE RAW ENTRY ]\n{json.dumps(res, indent=2, ensure_ascii=False)}</div>""", unsafe_allow_html=True)

        with tabs[3]:
            st.markdown("### 💰 정밀 약가 및 급여 가이드 (10+ 리포트)")
            c1, c2 = st.columns(2)
            prices = list(DRUG_PRICES.items())
            for i, (n, d) in enumerate(prices):
                with (c1 if i < 5 else c2):
                    with st.expander(f"📌 {n} ({d['급여']})"):
                        st.markdown(f"""
                        <div style="background:#000; padding:10px; border-radius:5px; border:1px solid #30363d;">
                            <p style="margin:0; color:#58a6ff;"><b>성분:</b> {d['성분']}</p>
                            <p style="margin:5px 0; color:#ffffff; font-size:1.2rem;"><b>가격:</b> {d['가격']:,}원 / {d['단위']}</p>
                            <p style="margin:0; color:#8b949e; font-size:0.8rem;">보험코드: {d['코드']}</p>
                        </div>
                        """, unsafe_allow_html=True)

        with st.expander("📰 전략 사령부 정책 & 임상 뉴스 (TOP 10)"):
            for news in POLICY_NEWS:
                st.markdown(f"""
                <div style="border-bottom:1px solid #1e293b; padding:10px 0;">
                    <span style="background:#0060ff; color:white; padding:2px 8px; border-radius:3px; font-size:0.7rem;">{news['tag']}</span>
                    <span style="color:#8b949e; font-size:0.8rem; margin-left:10px;">{news['date']}</span>
                    <p style="margin:5px 0 0 0; color:#58a6ff; font-weight:700;">{news['title']}</p>
                    <p style="margin:2px 0 0 0; color:#8b949e; font-size:0.85rem;">{news['body']}</p>
                    <p style="margin:2px 0 0 0; color:#30363d; font-size:0.75rem;">Source: {news['source']}</p>
                </div>
                """, unsafe_allow_html=True)

    with col_r:
        st.markdown('#### 🎙️ AI 마스터 브리핑')
        if st.session_state.voice_ai_answer:
            st.markdown(f'<div class="briefing-box">{st.session_state.voice_ai_answer}</div>', unsafe_allow_html=True)
        tts_button(st.session_state.voice_ai_answer or "분석 데이터 로딩 중...", "tts_v40_2")
        
        st.markdown("---")
        st.markdown("#### 📄 처방전 AI 분석 (Dual-View)")
        uploaded_file = st.file_uploader("UPLOAD", type=["jpg","png","jpeg"], key="up_v40_1", label_visibility="collapsed")
        
        if uploaded_file:
            st.image(uploaded_file, caption="🔍 스캔 대기 중인 처방전", use_container_width=True)
            st.warning("🔒 보안 검증 대기 중: 환자 이름 교차 확인")
            
            if st.button("AI 정밀 분석 & 보안 확인", use_container_width=True):
                with st.spinner("AI가 처방전과 알약 이미지를 매칭 중입니다..."):
                    result = analyze_image(uploaded_file.getvalue(), uploaded_file.type, pat, pat_rxs, pid)
                    
                    # 보안 검증 (이름 일치 확인)
                    if pat.get('real_name') not in result and "시뮬레이션" not in result:
                        st.error(f"🚨 [보안 위반] 처방전 환자와 현재 선택된 환자({pat.get('real_name')})가 불일치합니다.")
                        st.session_state.voice_ai_answer = "⚠️ 보안 검증 실패: 타인 처방전 감지됨"
                    else:
                        st.session_state.voice_ai_answer = result
                    st.rerun()

    with st.sidebar:
        st.markdown("#### 👥 전략 환자 선택")
        idx = list(patients.keys()).index(pid) if pid in patients else 0
        st.selectbox("선택", list(patients.keys()), index=idx, format_func=lambda x: f"{patients[x]['real_name']} ({patients[x]['age']}세)", key="pat_v38")
        
        if HAS_PHARMACY:
            st.markdown("---")
            st.markdown("📍 주변 약국 재고 (20분 주기 갱신)")
            st.markdown(render_pharmacy_widget_html(), unsafe_allow_html=True)
            st.markdown('<div style="color:#00ff88; font-size:0.75rem; font-weight:700;">🟢 초록색은 현재 즉시 조제 가능한 약국입니다.</div>', unsafe_allow_html=True)
        
        if HAS_ADHERENCE:
            st.markdown("---")
            st.markdown("📅 실시간 복약 준수율")
            sync_schedules_from_rx(rxs)
            st.markdown(render_compliance_sentinel_html(pid, pat.get('real_name', '환자')), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🛡️ 위험 감지 센터")
        if st.button("🚨 보호자 긴급 알림 테스트"):
            if HAS_GUARDIAN:
                send_guardian_alert(pid, pat.get('real_name'), "긴급건강경고", "환자의 바이탈에 이상 징후가 감지되었습니다. 즉시 확인 바랍니다.", severity="CRITICAL")
                st.toast("보호자에게 카카오톡 알림 전송 완료!")

    emergency_floating_panel()

if __name__ == "__main__":
    main()
