#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[SHIELD] PHARMA-HYBRID AI Engine Module
- Gemini AI 연동 로직 (Voice, Image, Text 분석)을 통합 관리합니다.
"""

import time
import base64
import json
import streamlit as st
from typing import Dict, List

# ── Gemini 실제 AI 엔진 연동 ──────────────────────────────────────────────────
try:
    from gemini_ai_engine import (
        call_gemini_compat,
        call_gemini_text,
        call_gemini_vision,
        call_gemini_voice,
        call_gemini_rag,
        get_engine_status,
    )
    HAS_GEMINI_ENGINE = True
except ImportError:
    HAS_GEMINI_ENGINE = False
    def call_gemini_compat(contents, system=""): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_text(p, **kw): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_vision(b, m, p, **kw): return "⚠️ Vision AI 로드 실패"
    def call_gemini_voice(t, pi, rx): return "⚠️ Gemini 엔진 로드 실패"
    def call_gemini_rag(q, kb, **kw): return "⚠️ Gemini 엔진 로드 실패"
    def get_engine_status(): return {"mode": "🔴 엔진 로드 실패", "ready": False}

# ── 상호작용 및 시너지 지식베이스 ──────────────────────────────────────────────
def get_synergy_info(disease_str: str, pid: str = None) -> str:
    """[V28] 질환 맞춤형 정밀 시너지 분석"""
    disease_map = {
        "폐암": {"채소_과일": "브로콜리, 토마토, 사과", "영양제": "비타민 D, 오메가3", "운동": "가벼운 산책 (일 20분)", "시너지": "항산화 작용으로 폐 세포 보호 및 염증 수치 감소"},
        "간암": {"채소_과일": "당근, 시금치, 배", "영양제": "실리마린, 비타민 B군", "운동": "스트레칭 및 명상", "시너지": "간 해독 능력 보완 및 에너지 대사 효율 증대"},
        "대장암": {"채소_과일": "사과, 양배추, 고구마", "영양제": "프로바이오틱스", "운동": "규칙적인 걷기", "시너지": "장내 미생물 균형 복구 및 면역력 강화"},
        "흑색종": {"채소_과일": "베리류, 당근, 케일", "영양제": "비타민 C, E", "운동": "요가", "시너지": "피부 재생 촉진 및 면역 세포 활성화"},
        "백혈병": {"채소_과일": "익힌 채소, 바나나", "영양제": "엽산, 철분 (상담 필수)", "운동": "가벼운 실내 운동", "시너지": "혈액 생성 지원 및 전신 면역 체계 강화"},
        "유방암": {"채소_과일": "콩류, 브로콜리, 베리류", "영양제": "칼슘, 비타민 D", "운동": "근력 운동 (주 3회)", "시너지": "호르몬 조절 보조 및 뼈 건강 유지"}
    }
    
    matched = {"채소_과일": [], "영양제": [], "운동": [], "시너지": []}
    for d in disease_map:
        if d in disease_str:
            for k in matched: matched[k].append(disease_map[d][k])
    
    if not matched["시너지"]:
        matched = {"채소_과일": ["신선한 제철 과일"], "영양제": ["종합 비타민"], "운동": ["규칙적인 유산소 운동"], "시너지": ["전신 컨디션 회복 및 면역 증강"]}
    else:
        for k in matched: matched[k] = ", ".join(list(set(matched[k])))

    return (
        f"<div style='font-size: 1.1rem; line-height: 1.7; background-color: rgba(0, 50, 100, 0.3); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,242,255,0.2); margin-top:15px;'>"
        f"<h4 style='color: #00ff88; margin-top: 0; margin-bottom: 12px; font-size: 1.2rem;'>🧬 임상 데이터 시너지 분석</h4>"
        f"<ul style='list-style-type: none; padding-left: 0; margin: 0;'>"
        f"<li style='margin-bottom: 8px;'>🚶 <strong style='color:#ffffff;'>권장 활동:</strong> <span style='color: #bbddff;'>{matched['운동']}</span></li>"
        f"<li style='margin-bottom: 8px;'>💊 <strong style='color:#ffffff;'>보조 영양:</strong> <span style='color: #bbddff;'>{matched['영양제']}</span></li>"
        f"<li style='margin-bottom: 0px;'>✨ <strong style='color:#ffffff;'>기대 효과:</strong> <span style='color: #bbddff;'>{matched['시너지']}</span></li>"
        f"</ul></div>"
    )

def call_gemini(contents: list, system: str = "", pid: str = None) -> str:
    """통합 Gemini API 호출부"""
    if HAS_GEMINI_ENGINE:
        try:
            result = call_gemini_compat(contents, system=system)
            user_text = ""
            for part in contents[0].get("parts", []):
                if "text" in part: user_text += part["text"]
            synergy = get_synergy_info(user_text, pid)
            if synergy and "SYNERGY" not in result:
                result += f"\n\n{synergy}"
            return result
        except Exception as e:
            return f"⚠️ Gemini 호출 오류: {str(e)}"

    # 폴백 시뮬레이션
    time.sleep(0.8)
    return "🤖 [시뮬레이션 모드] 실제 API 키가 설정되지 않았거나 엔진 로드에 실패했습니다."

def analyze_voice(text: str, patient_info: Dict, prescriptions: List[Dict], pid: str = None) -> str:
    """음성 텍스트 임상 분석"""
    if HAS_GEMINI_ENGINE:
        try:
            pat_info_with_pid = {**patient_info, "patient_id": pid or ""}
            return call_gemini_voice(text, pat_info_with_pid, prescriptions)
        except Exception as e:
            return f"⚠️ 음성 분석 오류: {str(e)}"
    
    # 시뮬레이션 폴백
    return f"🗣️ 입력된 음성: '{text}'\n(실제 분석을 위해선 Gemini 엔진이 필요합니다.)"

def analyze_image(image_bytes: bytes, mime_type: str, patient_info: Dict, prescriptions: List[Dict], pid: str = None) -> str:
    """이미지/처방전 Vision 분석"""
    rx_summary = ", ".join([r["medication_name"] for r in prescriptions])
    prompt = f"현재 환자 처방: {rx_summary}\n이미지를 분석하여 약품 목록과 주의사항을 정리해 주세요."
    
    if HAS_GEMINI_ENGINE:
        try:
            return call_gemini_vision(image_bytes, mime_type, prompt)
        except Exception as e:
            return f"⚠️ 이미지 분석 오류: {str(e)}"
            
    return "🖼️ [시뮬레이션] 이미지 분석 결과입니다. (Gemini Vision AI 활성화 필요)"

def ai_kb_search(query: str, kb_results: List[Dict], patient_context: str = "") -> str:
    """지식베이스 RAG 보강 설명"""
    if HAS_GEMINI_ENGINE:
        try:
            return call_gemini_rag(query, kb_results, patient_context=patient_context)
        except Exception as e:
            return f"⚠️ AI 검색 오류: {str(e)}"
            
    return f"🔍 '{query}'에 대한 지식베이스 검색 결과입니다."
