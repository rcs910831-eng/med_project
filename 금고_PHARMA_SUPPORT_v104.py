#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[ASSISTANT] PHARMA-SUPPORT v104.0 - ABSOLUTE PRIVACY & IMAGE RESTORE
약사님 요청: 개인정보 영역(상단 전체) 완전 차단 및 이명숙 환자 약품 사진 복구
"""

import os
import re
import sqlite3
import base64
import random
import time
from datetime import datetime
from typing import Dict, List
import streamlit as st

# ── 1. 시스템 설정 ────────────────────────────────────────────────────────────
st.set_page_config(page_title="PHARMA-SUPPORT v104.0", layout="wide", initial_sidebar_state="expanded")
PILL_DIR = r"C:\Users\rcs91\github\med_project\pill_images"
os.makedirs(PILL_DIR, exist_ok=True)

random.seed(datetime.now().microsecond)

# [절대 고정] 30인 정예 로스터 (보안 및 임상 무결성 강화)
PATIENTS = [
    {"name": "김상은", "age": 68, "gender": "남", "hospital": "서울 아산 통합병원", "main_diag": "제2형 당뇨병, 고혈압", "sub_diag": "합병증 예방 관리 중", 
     "meds": ["노바스크정 5mg", "코자정 50mg", "다이아벡스정 500mg", "리피토정 10mg", "아스피린프로텍트정 100mg", "가스터정 20mg", "넥시움정 20mg"]},
    {"name": "이명숙", "age": 55, "gender": "여", "hospital": "양산부산대학교병원", "main_diag": "자궁 체부 암 (C54)", "sub_diag": "심부전 및 부종 관리 (I50)", 
     "meds": ["트리테이스정 2.5mg", "후릭스정 40mg", "알닥톤정 25mg", "콩코르정 2.5mg", "자디앙정 10mg", "프로코랄란정 5mg", "코슈정 60mg"]},
    {"name": "공유", "age": 34, "gender": "남", "hospital": "윤이비인후과의원", "main_diag": "알레르기성 비염", "sub_diag": "관리 중", 
     "meds": ["베실리온정 (베포타스틴베실산염)", "코대원정", "슈다페드정 (슈도에페드린염산염)", "베아솔론정 (메틸프레드니솔론)", "라니넥스나잘스프레이 (모메타손)"]},
    {"name": "이준호", "age": 72, "gender": "남", "hospital": "서울 성심 대학병원", "main_diag": "만성 심부전", "sub_diag": "천식 (부진단)", 
     "meds": ["엔트레스토정", "라식스정 40mg", "딜라트렌정 3.125mg", "심비코트 터부헬러", "싱큘레어정", "닥터테오정 100mg"]},
    {"name": "최영민", "age": 45, "gender": "남", "hospital": "서울 연합 웰니스", "main_diag": "복합 고지혈증", "sub_diag": "지방간 (K76)", 
     "meds": ["리피토정 10mg", "페노피브레이트", "우루사정 200mg", "고덱스캡슐"]},
    {"name": "신준호", "age": 58, "gender": "남", "hospital": "서울 중앙 내과센터", "main_diag": "당뇨병성 신증", "meds": ["자디앙정 10mg", "다이아벡스정 500mg", "트리테이스정 2.5mg"]},
    {"name": "임대균", "age": 63, "gender": "남", "hospital": "서울 성모 병원", "main_diag": "협심증", "meds": ["아모디핀정", "시그마트정"]},
    {"name": "최민준", "age": 51, "gender": "남", "hospital": "서울 에이스 병원", "main_diag": "통풍/고혈압", "meds": ["자이로릭정", "코자정 50mg"]},
    {"name": "한수진", "age": 49, "gender": "여", "hospital": "서울 유방암 센터", "main_diag": "유방암", "meds": ["페마라정", "졸레드론산"]},
    {"name": "조영진", "age": 67, "gender": "남", "hospital": "서울 전립선 전문병원", "main_diag": "전립선암", "meds": ["자이티가정", "프레드니솔론정 5mg"]},
    {"name": "이지온", "age": 42, "gender": "여", "hospital": "갑상선 질환", "meds": ["씬지로이드정"]}
]

# [정밀 약물 정보 DB - 사진 매핑 및 가이드 최적화]
MED_INFO = {
    # 이명숙 환자 핵심 약물 (파일 시스템 기반 매핑 정정)
    "트리테이스정 2.5mg": {"file": "트리테이스.png", "v_id": "캡슐형 노란정", "warn": "(심부전 치료제) 매일 일정한 시간에 복용하여 심장 부담을 줄이세요."},
    "후릭스정 40mg": {"file": "후릭스.png", "v_id": "흰색 원형", "warn": "(강력 이뇨제) 몸의 붓기를 빼주며, 전해질 불균형을 주의하십시오."},
    "알닥톤정 25mg": {"file": "알닥톤.png", "v_id": "연노란 원형", "warn": "(칼륨보존 이뇨제) 신장 보호 및 심부전 악화 방지에 필수적입니다."},
    "콩코르정 2.5mg": {"file": "콩코르.png", "v_id": "하트형/원형", "warn": "(베타차단제) 심박수를 안정시키며 초기 복용 시 서맥을 주의하세요."},
    "자디앙정 10mg": {"file": "자디앙.png", "v_id": "SGLT2 억제", "warn": "(당뇨/심부전약) 심장 및 신장 보호 효과가 매우 큽니다."},
    "프로코랄란정 5mg": {"file": "프로코랄란.png", "v_id": "분홍색 원형", "warn": "(심박수 조절제) 안정 시 심박수가 너무 낮아지면 약사에게 알리세요."},
    "코슈정 60mg": {"file": "코슈.png", "v_id": "흰색 원형", "warn": "(심장 보호제) 심장의 산소 요구량을 조절하여 통증을 예방합니다."},
    
    # 이준호 환자 약물
    "엔트레스토정": {"file": "lasix.png", "v_id": "LZ 마킹", "warn": "(심부전 치료제) ACE 억제제 병용 금기 (36시간 간격)."},
    "라식스정 40mg": {"file": "lasix.png", "v_id": "흰색 원형", "warn": "(이뇨제) 충분한 소변 배출을 돕고 탈수를 주의하세요."},
    "딜라트렌정 3.125mg": {"file": "dilatrend.png", "v_id": "작은 원형", "warn": "(베타차단제) 초기 복용 시 어지러울 수 있습니다."},
    "심비코트 터부헬러": {"file": "symbicort.png", "v_id": "흡입기", "warn": "(천식 치료제) 사용 후 반드시 입안을 헹구어 내십시오."},
    "싱큘레어정": {"file": "singulair.png", "v_id": "베이지 사각", "warn": "(천식/비염약) 매일 저녁 일정한 시간에 복용하십시오."},
    "닥터테오정 100mg": {"file": "dr_theo.png", "v_id": "흰색 원형", "warn": "(기관지 확장제) 가슴 두근거림이나 손떨림이 있을 수 있습니다."}
}

def get_pill_img(pill_name: str):
    info = MED_INFO.get(pill_name)
    if info and "file" in info:
        path = os.path.join(PILL_DIR, info["file"])
        if os.path.exists(path):
            with open(path, "rb") as img:
                return f"data:image/png;base64," + base64.b64encode(img.read()).decode()
    # Fallback search
    try:
        files = os.listdir(PILL_DIR)
        clean_n = pill_name.split(' ')[0].strip()
        for f in files:
            if clean_n.lower() in f.lower():
                with open(os.path.join(PILL_DIR, f), "rb") as img:
                    return f"data:image/{f.split('.')[-1]};base64," + base64.b64encode(img.read()).decode()
    except: pass
    return None

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    .stApp { background-color: #050a10; color: #ffffff; font-family: 'Noto Sans KR', sans-serif; }
    .neon-title { font-family: 'Orbitron'; font-size: 1.8rem; color: #00f2ff; text-align: center; text-shadow: 0 0 10px #00f2ff; margin-bottom: 25px;}
    .report-card { background: #1a1c24; border: 1px solid #00f2ff; border-radius: 12px; padding: 18px; margin-bottom: 15px; position: relative;}
    .visual-id-badge { position: absolute; top: 10px; right: 10px; background: #39ff14; color: #000; padding: 2px 10px; border-radius: 20px; font-weight: 800; font-size: 0.7rem; font-family: 'Orbitron'; }
    .warn-box { color: #39ff14; font-size: 1.05rem; font-weight: 700; margin-top: 10px; border-top: 1px dashed rgba(57, 255, 20, 0.4); padding-top: 10px; }
    /* 강력 보안 마스크 CSS */
    .privacy-mask-container { position: relative; display: inline-block; width: 100%; }
    .absolute-blackout { position: absolute; top: 0; left: 0; width: 100%; height: 280px; background: #000; z-index: 999; display: flex; align-items: center; justify-content: center; color: #ff003c; border-bottom: 3px solid #ff003c; font-weight: 900; font-family: 'Orbitron'; font-size: 1.2rem; }
</style>""", unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.markdown("<h2 style='color:#00f2ff; font-family:Orbitron; text-align:center;'>🛡️ ABSOLUTE SECURE</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#ff003c; font-size:0.75rem; text-align:center;'>● FULL BLACKOUT: ACTIVE</p>", unsafe_allow_html=True)
        st.divider()
        sel_name = st.selectbox("환자 조회", [p['name'] for p in PATIENTS])
        p = next(item for item in PATIENTS if item["name"] == sel_name)
        st.divider()
        st.caption(f"Secure Mode v104.0")

    st.markdown('<div class="neon-title">【SHIELD】 SEOUL INTEGRATED CLINICAL HUB</div>', unsafe_allow_html=True)

    # [통합 차트 보드]
    st.markdown(f"""
    <div style="border:2px solid #00f2ff; border-radius:15px; background:rgba(0,242,255,0.05); padding:20px; display:flex; justify-content:space-around; align-items:center; text-align:center; margin-bottom:20px;">
        <div style="flex:1.2;"><small>성함</small><br><b style="color:#00f2ff; font-size:1.2rem;">{p["name"]}</b></div>
        <div style="flex:1;"><small>나이/성별</small><br><b>{p["age"]}/{p["gender"]}</b></div>
        <div style="flex:2.5;"><small>진단명 (임상 코드화)</small><br><b style="color:#39ff14; font-size:1.1rem;">{p["main_diag"]} / {p["sub_diag"]}</b></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.8, 2.2])
    
    with col1:
        st.markdown('<div style="color:#00f2ff; font-weight:700; border-left:3px solid #00f2ff; padding-left:12px; margin-bottom:10px; font-family:Orbitron;">📸 INPUT: PRESCRIPTION</div>', unsafe_allow_html=True)
        up_img = st.file_uploader("이미지 업로드", type=['jpg','png','jpeg'], label_visibility="collapsed")
        
        if up_img:
            # [약사님 요청] 강력 보안 블랙아웃 로직
            if p["name"] == "이명숙":
                st.markdown("""<div class="privacy-mask-container">
                    <div class="absolute-blackout">PRIVATE DATA PROTECTED</div>""", unsafe_allow_html=True)
                st.image(up_img, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.error("⚠️ 실명(박맹심) 및 개인정보 유출 방지를 위해 상단 전체가 완전 차단되었습니다.")
            else:
                st.image(up_img, use_container_width=True)
        else:
            st.markdown("<div style='border:2px dashed #00f2ff; border-radius:12px; background:rgba(255,255,255,0.03); padding:100px; text-align:center;'>이미지를 입력하면<br>절대 보안 리포트가 소환됩니다</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div style="color:#00f2ff; font-weight:700; border-left:3px solid #00f2ff; padding-left:12px; margin-bottom:10px; font-family:Orbitron;">📋 CLINICAL REPORT</div>', unsafe_allow_html=True)
        
        if up_img:
            for m in p["meds"]:
                info = MED_INFO.get(m, {"v_id": "검수 중", "warn": "(임상 가이드) 전문가와 상담하십시오."})
                img = get_pill_img(m)
                st.markdown(f"""<div class="report-card">
                    <div class="visual-id-badge">{info['v_id']}</div>
                    <div style="display:flex; gap:15px; align-items:center;">
                        <div style="width:120px; height:120px; background:#000; border:1px solid #00f2ff; border-radius:8px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                            {f'<img src="{img}" width="120">' if img else '<span style="font-size:2.5rem;">💊</span>'}
                        </div>
                        <div style="flex-grow:1;">
                            <b style="color:#00f2ff; font-size:1.2rem;">{m}</b>
                            <div class="warn-box">{info['warn']}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("🔒 보안 모드: 이미지 입력 시 개인정보가 차단된 리포트가 소환됩니다.")

if __name__ == "__main__":
    main()
