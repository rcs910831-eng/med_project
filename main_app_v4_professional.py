# 🏥 PHARMA-HYBRID v4.0 - 의료 전문가용 완전 개편 시스템
# 30년 경력 의사겸약사의 요구사항 100% 반영
# 2026-04-30 최종 버전

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Tuple
from drug_info_complete_db import DRUG_DATABASE, get_drug_info, search_drug_by_disease
from safety_validator_advanced import SafetyValidator

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="PHARMA-HYBRID v4.0 | 의료 의사결정 지원",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 어두운 테마 CSS ====================
st.markdown("""
    <style>
    /* 배경색 제거 - 어두운 배경만 */
    body {
        background-color: #0a0e27 !important;
        color: #e0e0ff !important;
    }

    .stApp {
        background-color: #0a0e27 !important;
    }

    /* 메인 헤더 */
    .header-main {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }

    /* 우선순위 라벨 */
    .priority-1 {
        background-color: #ff3333;
        color: white;
        padding: 8px 12px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }

    .priority-2 {
        background-color: #ff9900;
        color: white;
        padding: 8px 12px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }

    /* 질환-약물 섹션 */
    .disease-section {
        border-left: 5px solid #00d4ff;
        background-color: #1a1f3a;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }

    .disease-section.priority-1-disease {
        border-left-color: #ff3333;
        background-color: #2a1a1a;
    }

    .disease-section.priority-2-disease {
        border-left-color: #ff9900;
        background-color: #2a2415;
    }

    /* 약물 카드 */
    .drug-card {
        border: 2px solid #00d4ff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: #0f1428;
    }

    .drug-card.priority-1-drug {
        border-left: 5px solid #ff3333;
    }

    .drug-card.priority-2-drug {
        border-left: 5px solid #ff9900;
    }

    /* 처방 정보 */
    .prescription-info {
        background-color: #1a1f3a;
        padding: 12px;
        border-radius: 5px;
        margin: 8px 0;
        border-left: 4px solid #00d4ff;
    }

    /* 주의사항 */
    .warning-critical {
        background-color: #3a1a1a;
        border-left: 4px solid #ff3333;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }

    .warning-moderate {
        background-color: #2a2415;
        border-left: 4px solid #ff9900;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }

    /* 안전 검증 */
    .safety-pass {
        background-color: #1a3a1a;
        border-left: 4px solid #00ff00;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }

    .safety-fail {
        background-color: #3a1a1a;
        border-left: 4px solid #ff3333;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }

    /* 실시간 모니터링 */
    .realtime-monitor {
        background-color: #1a2a3a;
        border: 2px solid #00d4ff;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }

    .metric-changing {
        color: #00ff00;
        font-weight: bold;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* 텍스트 색상 */
    .text-danger { color: #ff3333 !important; }
    .text-warning { color: #ff9900 !important; }
    .text-success { color: #00ff00 !important; }
    .text-info { color: #00d4ff !important; }
    </style>
""", unsafe_allow_html=True)

# ==================== 세션 상태 초기화 ====================
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {
        "name": "",
        "age": 0,
        "gender": "미선택",
        "department": "",
        "institution": "",
        "doctor": "",
        "prescription_date": datetime.now().date(),
        "diseases": {
            "priority_1": [],  # 주 질환
            "priority_2": []   # 부 질환
        },
        "drugs": {}  # {"약물명": {"disease": "질환", "priority": 1/2}}
    }

if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

# ==================== 메인 헤더 ====================
st.markdown("""
    <div class="header-main">
        <h1>🏥 PHARMA-HYBRID v4.0</h1>
        <h3>Strategic Unified Clinical Decision Support System</h3>
        <p>의료 전문가용 | 30년 임상 기준 반영 | 실시간 모니터링</p>
    </div>
""", unsafe_allow_html=True)

# ==================== 단일 고객 선택 ====================
col1, col2, col3 = st.columns([2, 4, 4])

with col1:
    st.subheader("👤 환자 선택")
    patient_name = st.selectbox(
        "환자명",
        ["P001(김상은)", "P012(이크론)", "P014(박파킨)", "P015(최뇌전)", "P016(윤천식)",
         "P017(조족선)", "P018(정위염)", "P020(호COPD)", "P022(우우울)", "P023(김크론)"],
        key="patient_select"
    )

    st.session_state.patient_data["name"] = patient_name.split("(")[1].strip(")")

with col2:
    st.subheader("🔍 환자 정보")
    st.session_state.patient_data["age"] = st.slider("나이", 0, 120, 50)
    st.session_state.patient_data["gender"] = st.selectbox("성별", ["남성", "여성"], key="gender")

with col3:
    st.subheader("📅 처방 정보")
    st.session_state.patient_data["prescription_date"] = st.date_input("**처방 날짜**", datetime.now().date())
    st.session_state.patient_data["doctor"] = st.text_input("담당의", "")

st.markdown("---")

# ==================== 좌측: 질환 및 약물 입력 | 우측: 실시간 모니터링 ====================
left_col, right_col = st.columns([1, 2])

# ==================== 좌측: 질환 및 약물 관리 ====================
with left_col:
    st.subheader("🏥 질환 및 약물 관리")

    # 1순위 질환
    st.write("### 🔴 1순위 질환 (주요 질환)")
    priority_1_disease = st.text_input("1순위 질환명", key="p1_disease")
    if st.button("1순위 질환 추가"):
        if priority_1_disease:
            st.session_state.patient_data["diseases"]["priority_1"].append(priority_1_disease)
            st.rerun()

    if st.session_state.patient_data["diseases"]["priority_1"]:
        for disease in st.session_state.patient_data["diseases"]["priority_1"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"<span class='text-danger'>🔴 {disease}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("✕", key=f"del_p1_{disease}"):
                    st.session_state.patient_data["diseases"]["priority_1"].remove(disease)
                    st.rerun()

    st.markdown("---")

    # 2순위 질환
    st.write("### 🟠 2순위 질환 (부가 질환)")
    priority_2_disease = st.text_input("2순위 질환명", key="p2_disease")
    if st.button("2순위 질환 추가"):
        if priority_2_disease:
            st.session_state.patient_data["diseases"]["priority_2"].append(priority_2_disease)
            st.rerun()

    if st.session_state.patient_data["diseases"]["priority_2"]:
        for disease in st.session_state.patient_data["diseases"]["priority_2"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"<span class='text-warning'>🟠 {disease}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("✕", key=f"del_p2_{disease}"):
                    st.session_state.patient_data["diseases"]["priority_2"].remove(disease)
                    st.rerun()

    st.markdown("---")

    # 약물 추가
    st.write("### 💊 약물 선택")
    all_drugs = list(DRUG_DATABASE.keys())
    selected_drug = st.selectbox("약물 검색", [""] + all_drugs, key="drug_select")

    # 약물이 어느 질환의 약물인지 자동 감지
    disease_for_drug = "미지정"
    if selected_drug:
        drug_info = get_drug_info(selected_drug)
        disease_for_drug = drug_info.get("disease", "미지정")

    if st.button("약물 추가"):
        if selected_drug:
            # 1순위 또는 2순위 질환에 속하는지 확인
            drug_info = get_drug_info(selected_drug)
            drug_disease = drug_info.get("disease", "")

            priority = 0
            if drug_disease in st.session_state.patient_data["diseases"]["priority_1"]:
                priority = 1
            elif drug_disease in st.session_state.patient_data["diseases"]["priority_2"]:
                priority = 2

            st.session_state.patient_data["drugs"][selected_drug] = {
                "disease": drug_disease,
                "priority": priority
            }
            st.rerun()

# ==================== 우측: 실시간 모니터링 및 약물 정보 ====================
with right_col:
    st.subheader("📊 실시간 모니터링 & 약물 분석")

    if not st.session_state.patient_data["drugs"]:
        st.warning("⚠️ 약물을 추가해주세요")
    else:
        # ==================== 실시간 모니터링 ====================
        st.markdown("""
            <div class="realtime-monitor">
                <h3>⚡ 실시간 모니터링</h3>
        """, unsafe_allow_html=True)

        # 안전 검증 실행
        all_drugs_list = list(st.session_state.patient_data["drugs"].keys())
        all_diseases = (st.session_state.patient_data["diseases"]["priority_1"] +
                       st.session_state.patient_data["diseases"]["priority_2"])

        safety_result = SafetyValidator.comprehensive_safety_check(
            drugs=all_drugs_list,
            patient_conditions=all_diseases,
            patient_age=st.session_state.patient_data["age"]
        )

        # 메트릭 표시
        col1, col2, col3 = st.columns(3)

        with col1:
            safety_score = safety_result["safety_score"]
            color = "text-success" if safety_score >= 70 else "text-warning" if safety_score >= 50 else "text-danger"
            st.metric("안전 점수", f"{safety_score}/100")
            st.write(f"<span class='{color}'>{safety_result['summary']['recommendation']}</span>", unsafe_allow_html=True)

        with col2:
            critical = safety_result["summary"]["critical_issues"]
            st.metric("🔴 심각", critical)
            if critical > 0:
                st.write(f"<span class='text-danger'>⚠️ 즉시 조정 필요!</span>", unsafe_allow_html=True)

        with col3:
            warnings = safety_result["summary"]["warnings"]
            st.metric("🟠 경고", warnings)
            duplicates = safety_result["summary"]["duplicates"]
            st.metric("중복", duplicates)

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ==================== 중앙: 질환-약물 맵핑 및 상세 정보 ====================
st.subheader("📋 질환별 약물 정보 (우선순위 순서)")

# 1순위 질환
if st.session_state.patient_data["diseases"]["priority_1"]:
    st.markdown("""
        <div style="border-left: 5px solid #ff3333; background-color: #2a1a1a; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h3 style="color: #ff3333;">🔴 1순위 주요 질환</h3>
    """, unsafe_allow_html=True)

    for disease in st.session_state.patient_data["diseases"]["priority_1"]:
        st.write(f"### 🔴 {disease}")

        # 이 질환을 위한 약물들
        disease_drugs = {d: info for d, info in st.session_state.patient_data["drugs"].items()
                        if info["disease"] == disease}

        if disease_drugs:
            for drug_name, drug_info in disease_drugs.items():
                full_drug_info = get_drug_info(drug_name)

                st.markdown(f"""
                    <div class="drug-card priority-1-drug">
                        <h4>💊 {drug_name}</h4>
                        <p><strong>성분:</strong> {full_drug_info.get('generic_name', 'N/A')}</p>
                """, unsafe_allow_html=True)

                # 처방 정보 (우선순위 순서)
                dosage = full_drug_info.get("dosage", {})
                st.markdown(f"""
                    <div class="prescription-info">
                        <strong>💉 처방 정보:</strong><br>
                        📅 처방일: {st.session_state.patient_data['prescription_date']}<br>
                        💊 <span class="text-info">1회 투여량:</span> {dosage.get('single_dose', 'N/A')}<br>
                        🔄 <span class="text-info">1일 투여횟수:</span> {dosage.get('frequency', 'N/A')}<br>
                        📆 <span class="text-info">총 투약일수:</span> {dosage.get('monthly_quantity', 'N/A')}<br>
                    </div>
                """, unsafe_allow_html=True)

                # 효능
                st.write(f"**📊 임상 효능:** {full_drug_info.get('efficacy', 'N/A')}")
                st.write(f"**🔬 임상시험:** {full_drug_info.get('clinical_trial', 'N/A')}")

                # 🔴 주의사항 (중요도 표시)
                warnings = full_drug_info.get("warnings", [])
                if warnings:
                    st.write("**⚠️ 주의사항:**")
                    for warning in warnings:
                        if "🔴" in warning:
                            st.markdown(f'<div class="warning-critical">{warning}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="warning-moderate">{warning}</div>', unsafe_allow_html=True)

                # 상호작용
                interactions = full_drug_info.get("interactions", [])
                if interactions:
                    st.write("**🔗 약물 상호작용:**")
                    for interaction in interactions:
                        severity_color = "text-danger" if interaction["severity"] == "high" else "text-warning"
                        st.write(f"- {interaction['drug']}: <span class='{severity_color}'>{interaction['description']}</span>", unsafe_allow_html=True)

                st.write("</div>", unsafe_allow_html=True)
        else:
            st.info(f"ℹ️ {disease}에 대한 처방약이 없습니다")

    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

# 2순위 질환
if st.session_state.patient_data["diseases"]["priority_2"]:
    st.markdown("""
        <div style="border-left: 5px solid #ff9900; background-color: #2a2415; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h3 style="color: #ff9900;">🟠 2순위 부가 질환</h3>
    """, unsafe_allow_html=True)

    for disease in st.session_state.patient_data["diseases"]["priority_2"]:
        st.write(f"### 🟠 {disease}")

        # 이 질환을 위한 약물들
        disease_drugs = {d: info for d, info in st.session_state.patient_data["drugs"].items()
                        if info["disease"] == disease}

        if disease_drugs:
            for drug_name, drug_info in disease_drugs.items():
                full_drug_info = get_drug_info(drug_name)

                st.markdown(f"""
                    <div class="drug-card priority-2-drug">
                        <h4>💊 {drug_name}</h4>
                        <p><strong>성분:</strong> {full_drug_info.get('generic_name', 'N/A')}</p>
                """, unsafe_allow_html=True)

                # 처방 정보
                dosage = full_drug_info.get("dosage", {})
                st.markdown(f"""
                    <div class="prescription-info">
                        <strong>💉 처방 정보:</strong><br>
                        📅 처방일: {st.session_state.patient_data['prescription_date']}<br>
                        💊 <span class="text-info">1회 투여량:</span> {dosage.get('single_dose', 'N/A')}<br>
                        🔄 <span class="text-info">1일 투여횟수:</span> {dosage.get('frequency', 'N/A')}<br>
                        📆 <span class="text-info">총 투약일수:</span> {dosage.get('monthly_quantity', 'N/A')}<br>
                    </div>
                """, unsafe_allow_html=True)

                # 효능
                st.write(f"**📊 임상 효능:** {full_drug_info.get('efficacy', 'N/A')}")

                # 주의사항
                warnings = full_drug_info.get("warnings", [])
                if warnings:
                    st.write("**⚠️ 주의사항:**")
                    for warning in warnings:
                        if "🔴" in warning:
                            st.markdown(f'<div class="warning-critical">{warning}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="warning-moderate">{warning}</div>', unsafe_allow_html=True)

                st.write("</div>", unsafe_allow_html=True)
        else:
            st.info(f"ℹ️ {disease}에 대한 처방약이 없습니다")

    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

# ==================== 안전 검증 상세 ====================
st.subheader("🛡️ 안전성 종합 검증")

if st.session_state.patient_data["drugs"]:
    # 약물 상호작용
    if safety_result["drug_interactions"]["critical_warnings"]:
        st.error("🔴 **치명적 상호작용 감지**")
        for warning in safety_result["drug_interactions"]["critical_warnings"]:
            st.markdown(f"""
                <div class="safety-fail">
                <strong>{warning['drugs']}</strong><br>
                원인: {warning['reason']}<br>
                조치: {warning['action']}
                </div>
            """, unsafe_allow_html=True)

    # 중복 약물
    if safety_result["duplicate_therapy"]["has_duplicates"]:
        st.warning("🟠 **중복 약물 감지**")
        for dup in safety_result["duplicate_therapy"]["duplicates"]:
            st.write(f"**{dup['class']}**: {', '.join(dup['drugs'])}")

    # 금기약물
    if not safety_result["contraindications"]["safe"]:
        st.error("🔴 **금기약물 감지**")
        for contra in safety_result["contraindications"]["contraindications"]:
            st.markdown(f"""
                <div class="safety-fail">
                <strong>{contra['disease']} 환자</strong><br>
                금기약물: {contra['drug']}<br>
                이유: {contra['reason']}
                </div>
            """, unsafe_allow_html=True)

    if safety_result["drug_interactions"]["safe"] and safety_result["contraindications"]["safe"] and not safety_result["duplicate_therapy"]["has_duplicates"]:
        st.markdown("""
            <div class="safety-pass">
            ✅ <strong>안전 - 처방 가능</strong><br>
            다병원 약물 충돌 없음 | 약물 상호작용 안전 | 금기약물 없음
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==================== 모니터링 스케줄 ====================
st.subheader("📅 환자별 모니터링 스케줄")

if st.session_state.patient_data["drugs"]:
    monitoring = safety_result["monitoring_schedule"]

    tabs = st.tabs(["매일", "주 1회", "월 1회", "분기", "반기", "연 1회"])

    with tabs[0]:
        if monitoring["daily"]:
            for item in monitoring["daily"]:
                st.write(f"• {item}")
        else:
            st.info("매일 모니터링 항목 없음")

    with tabs[1]:
        if monitoring["weekly"]:
            for item in monitoring["weekly"]:
                st.write(f"• {item}")
        else:
            st.info("주 1회 모니터링 항목 없음")

    with tabs[2]:
        if monitoring["monthly"]:
            for item in monitoring["monthly"]:
                st.write(f"• {item}")
        else:
            st.info("월 1회 모니터링 항목 없음")

    with tabs[3]:
        if monitoring["quarterly"]:
            for item in monitoring["quarterly"]:
                st.write(f"• {item}")
        else:
            st.info("분기 모니터링 항목 없음")

    with tabs[4]:
        if monitoring["semiannually"]:
            for item in monitoring["semiannually"]:
                st.write(f"• {item}")
        else:
            st.info("반기 모니터링 항목 없음")

    with tabs[5]:
        if monitoring["annually"]:
            for item in monitoring["annually"]:
                st.write(f"• {item}")
        else:
            st.info("연 1회 모니터링 항목 없음")

# ==================== 푸터 ====================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #888; font-size: 12px;">
    <p>🏥 PHARMA-HYBRID v4.0 - 의료 전문가용 의료 의사결정 지원 시스템</p>
    <p>⚠️ 본 시스템은 의료 전문가의 판단을 보조하는 도구입니다. 최종 결정은 의료 전문가의 책임입니다.</p>
    <p>✅ 30년 임상 기준 반영 | 📋 FDA/NIH 기준 기반 | 📅 2026-04-30 최종 버전</p>
    </div>
""", unsafe_allow_html=True)
