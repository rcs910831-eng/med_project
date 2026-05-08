#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHIELD PHARMA-HYBRID v21.0 - Streamlit Integration
기존 앱 + 새로운 4-Agent 시스템 통합
"""

import os
import streamlit as st
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Agent imports
try:
    from agents.agent_orchestrator import AgentOrchestrator
    HAS_AGENTS = True
except ImportError:
    HAS_AGENTS = False
    st.warning("Agent system not available")

# Existing imports
try:
    from medical_knowledge_engine import (
        search_knowledge,
        get_disease_protocol,
        DISEASE_PROTOCOLS,
    )
    HAS_MED_ENGINE = True
except ImportError:
    HAS_MED_ENGINE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="SHIELD PHARMA-HYBRID v21.0",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .agent-box {
        background-color: #f0f4f8;
        border-left: 4px solid #2e7bb4;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state"""
    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = AgentOrchestrator()
            st.session_state.orchestrator_ready = True
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            st.session_state.orchestrator_ready = False

    if "processing" not in st.session_state:
        st.session_state.processing = False

    if "last_report" not in st.session_state:
        st.session_state.last_report = None


def check_api_keys():
    """Check if required API keys are set"""
    from dotenv import load_dotenv
    load_dotenv()

    checks = {
        "ANTHROPIC_API_KEY": "❌",
        "GOOGLE_API_KEY": "✅" if os.getenv("GOOGLE_API_KEY") else "❌",
        "MFDS_API_KEY": "✅" if os.getenv("MFDS_API_KEY") else "❌"
    }

    missing = [k for k, v in checks.items() if v == "❌"]
    return checks, missing


def render_header():
    """Render page header"""
    st.markdown("# 💊 SHIELD PHARMA-HYBRID v21.0")
    st.markdown("**처방전 자동 분석 시스템** | 4-Agent AI 기반 의료 정보 제공")

    # API Key status
    checks, missing = check_api_keys()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Anthropic API", checks["ANTHROPIC_API_KEY"])

    with col2:
        st.metric("Google API", checks["GOOGLE_API_KEY"])

    with col3:
        st.metric("MFDS API", checks["MFDS_API_KEY"])

    if missing:
        st.markdown(f'<div class="warning-box">⚠️ 설정 필요: {", ".join(missing)}</div>',
                   unsafe_allow_html=True)

    return len(missing) == 0


def render_agent_system():
    """Render Agent System Tab"""
    st.header("🤖 4-Agent System")

    st.markdown("""
    처방전 이미지를 업로드하면 다음 4개 전문 에이전트가 자동으로 분석합니다:
    """)

    # Agent descriptions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="agent-box">
        <h4>🎯 Agent 1: OCR & Vision</h4>
        처방전 이미지 → 구조화된 정보 추출
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="agent-box">
        <h4>💊 Agent 2: RAG & 약물정보</h4>
        약물명 → MFDS 정보 + 임상논문 + 안전성 검증
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="agent-box">
        <h4>🏪 Agent 3: Google 약국</h4>
        위치 → 주변 약국 + MFDS 공시약가 조회
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="agent-box">
        <h4>📋 Agent 4: 오케스트레이터</h4>
        결과 통합 → PDF/HTML/JSON/음성 보고서 생성
        </div>
        """, unsafe_allow_html=True)

    # File upload
    st.markdown("---")
    st.subheader("📸 처방전 이미지 분석")

    uploaded_file = st.file_uploader(
        "처방전 이미지 업로드 (PNG, JPG, JPEG)",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        # Show uploaded image
        col1, col2 = st.columns(2)

        with col1:
            st.image(uploaded_file, caption="업로드된 이미지", use_column_width=True)

        with col2:
            st.info("📋 이미지 정보")
            st.write(f"파일명: {uploaded_file.name}")
            st.write(f"크기: {uploaded_file.size / 1024:.1f} KB")

        # Process button
        if st.button("🚀 분석 시작", key="analyze_button"):
            if not st.session_state.orchestrator_ready:
                st.error("❌ Agent System이 준비되지 않았습니다.")
                st.stop()

            with st.spinner("⏳ 처방전 분석 중..."):
                try:
                    # Save uploaded file
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Process with orchestrator
                    report = st.session_state.orchestrator.process_prescription_image(temp_path)

                    if report:
                        st.session_state.last_report = report

                        # Show success message
                        st.markdown("""
                        <div class="success-box">
                        ✅ 분석 완료! 아래에서 결과를 확인하세요.
                        </div>
                        """, unsafe_allow_html=True)

                        # Display results
                        st.subheader("📊 분석 결과")

                        # Patient info
                        patient = report.get("patient", {})
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("환자명", patient.get("name", "미상"))

                        with col2:
                            st.metric("나이", f"{patient.get('age', '미상')}세")

                        with col3:
                            st.metric("성별", patient.get("sex", "미상"))

                        with col4:
                            st.metric("처방약물수", len(report.get("medications", [])))

                        # Medications
                        st.subheader("💊 처방약물")

                        for i, med in enumerate(report.get("medications", [])[:5], 1):
                            with st.expander(f"{i}. {med.get('name', '')} ({med.get('strength', '')})"):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.write(f"**분류**: {med.get('category', '미상')}")
                                    st.write(f"**공시약가**: {med.get('mfds_price', '미상')}원")

                                with col2:
                                    st.write("**주의사항**")
                                    for warning in med.get("warnings", [])[:3]:
                                        st.write(f"- {warning}")

                                with col3:
                                    st.write("**부작용**")
                                    for effect in med.get("side_effects", [])[:3]:
                                        st.write(f"- {effect}")

                        # Safety warnings
                        safety = report.get("safety", {})
                        if not safety.get("safe"):
                            st.markdown("""
                            <div class="error-box">
                            ⚠️ 안전 경고
                            </div>
                            """, unsafe_allow_html=True)
                            for error in safety.get("errors", []):
                                st.error(error)

                        # Warnings
                        warnings = report.get("warnings", [])
                        if warnings:
                            st.markdown("""
                            <div class="warning-box">
                            ⚠️ 주의사항
                            </div>
                            """, unsafe_allow_html=True)
                            for warning in warnings:
                                st.warning(warning)

                        # Pharmacies
                        pharmacies = report.get("pharmacies", [])
                        if pharmacies:
                            st.subheader("🏪 근처 약국")

                            for i, pharm in enumerate(pharmacies[:5], 1):
                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    st.write(f"**{i}. {pharm.get('name', '')}**")

                                with col2:
                                    st.write(f"거리: {pharm.get('distance_km', 0):.1f}km")

                                with col3:
                                    st.write(f"전화: {pharm.get('phone', '')}")

                                with col4:
                                    st.write(f"약가: {pharm.get('estimated_total', 0):.0f}원")

                        # Download report
                        st.subheader("📥 보고서 다운로드")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            report_json = json.dumps(report, indent=2, ensure_ascii=False)
                            st.download_button(
                                "📄 JSON",
                                report_json,
                                "report.json",
                                "application/json"
                            )

                        with col2:
                            st.info("📃 PDF - pharma_output 폴더 확인")

                        with col3:
                            st.info("🔊 음성 - pharma_voice_comp 폴더 확인")

                    else:
                        st.error("❌ 분석 실패. 다시 시도해주세요.")

                    # Cleanup
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                except Exception as e:
                    logger.error(f"Processing error: {e}")
                    st.error(f"❌ 오류 발생: {str(e)}")


def render_knowledge_base():
    """Render Knowledge Base Tab"""
    st.header("📚 의료 지식 검색")

    if not HAS_MED_ENGINE:
        st.warning("의료 지식 엔진을 사용할 수 없습니다.")
        return

    search_query = st.text_input("질병이나 약물 검색", placeholder="예: 고혈압, 아스피린")

    if search_query:
        results = search_knowledge(search_query)

        if results:
            st.subheader(f"'{search_query}' 검색 결과")

            for result in results[:5]:
                with st.expander(f"📋 {result.get('title', '제목 없음')}"):
                    st.write(result.get('content', '내용 없음'))

        else:
            st.info("검색 결과가 없습니다.")


def render_system_info():
    """Render System Info Tab"""
    st.header("⚙️ 시스템 정보")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 구현 현황")
        st.write("- ✅ Agent 1: OCR & Vision")
        st.write("- ✅ Agent 2: RAG & 약물정보")
        st.write("- ✅ Agent 3: Google 약국")
        st.write("- ✅ Agent 4: 오케스트레이터")
        st.write("- ✅ 5개 유틸리티 모듈")

    with col2:
        st.subheader("📊 데이터 현황")
        st.write("- 약물 정보: 3+ (MFDS 기반)")
        st.write("- 임상논문: 6개")
        st.write("- 진료 가이드라인: 5개")
        st.write("- 처방전 샘플: 33개")

    st.markdown("---")

    st.subheader("🔐 API 키 상태")
    checks, missing = check_api_keys()

    for api, status in checks.items():
        st.write(f"{api}: {status}")

    if missing:
        st.error(f"설정 필요: {', '.join(missing)}")
        st.info("""
        설정 방법:
        1. https://console.anthropic.com 방문
        2. API Keys 생성
        3. .env 파일에 추가: ANTHROPIC_API_KEY=sk-ant-...
        """)

    st.markdown("---")

    st.subheader("📖 문서")
    st.write("""
    - [SETUP_GUIDE.md](https://github.com) - 초기 설정
    - [PHASE2_COMPLETION_REPORT.md](https://github.com) - Phase 2 보고서
    - [FINAL_VALIDATION_REPORT.md](https://github.com) - 최종 검증
    """)


def main():
    """Main application"""
    init_session_state()

    # Header
    api_ready = render_header()

    if not HAS_AGENTS:
        st.error("❌ Agent System이 초기화되지 않았습니다.")
        st.stop()

    if not api_ready:
        st.warning("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. 기본 기능만 사용 가능합니다.")

    st.markdown("---")

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Agent 분석", "📚 지식 검색", "⚙️ 시스템"])

    with tab1:
        render_agent_system()

    with tab2:
        render_knowledge_base()

    with tab3:
        render_system_info()

    # Footer
    st.markdown("---")
    st.markdown("""
    <p style="text-align: center; color: gray; font-size: 12px;">
    SHIELD PHARMA-HYBRID v21.0 | 4-Agent Medical Analysis System<br>
    ⚠️ 이 시스템은 의료 정보 제공 목적입니다. 의료 결정은 반드시 의료 전문가와 상담하세요.
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
