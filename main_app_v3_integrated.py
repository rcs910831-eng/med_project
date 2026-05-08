# 🏥 PHARMA-HYBRID v3.0 - 통합 의료 의사결정 지원 시스템
# 의료 전문가용 (Medical Professional Grade System)
# 2026-04-30 최신 버전 - 완벽한 약물 정보 + 실시간 안전 검증

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict
from drug_info_complete_db import DRUG_DATABASE, get_drug_info, search_drug_by_disease
from safety_validator_advanced import SafetyValidator

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="PHARMA-HYBRID v3.0 의료 의사결정 지원",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
    <style>
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .disease-priority-1 {
        border-left: 5px solid #ff3333;
        background-color: #ffe6e6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .disease-priority-2 {
        border-left: 5px solid #ff9933;
        background-color: #fff3e6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .safety-pass {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .safety-fail {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .critical-alert {
        background-color: #ffe6e6;
        border-left: 5px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        font-weight: bold;
    }
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
        "conditions": [],
        "drugs": []
    }

# ==================== 헤더 ====================
st.markdown("""
    <div class="header-gradient">
        <h1>🏥 PHARMA-HYBRID v3.0</h1>
        <p><strong>의료 전문가용 의료 의사결정 지원 시스템</strong></p>
        <p style="font-size: 12px;">FDA/NIH 임상 기준 + 실시간 약물 상호작용 검증 + 개인화 모니터링 일정</p>
    </div>
""", unsafe_allow_html=True)

# ==================== 사이드바 네비게이션 ====================
st.sidebar.title("📋 메뉴")
page = st.sidebar.radio(
    "페이지 선택",
    ["👤 환자 정보 입력", "💊 약물 정보 검색", "⚠️ 안전성 검증", "📊 처방 분석", "📚 약물 데이터베이스"]
)

# ==================== 1. 환자 정보 입력 ====================
if page == "👤 환자 정보 입력":
    st.header("👤 환자 정보 입력")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.session_state.patient_data["name"] = st.text_input(
            "환자명",
            value=st.session_state.patient_data["name"]
        )

    with col2:
        st.session_state.patient_data["age"] = st.number_input(
            "나이",
            min_value=0,
            max_value=120,
            value=st.session_state.patient_data["age"]
        )

    with col3:
        st.session_state.patient_data["gender"] = st.selectbox(
            "성별",
            ["미선택", "남성", "여성"],
            index=0
        )

    with col4:
        st.session_state.patient_data["department"] = st.text_input(
            "진료과",
            value=st.session_state.patient_data["department"]
        )

    col5, col6, col7 = st.columns(3)

    with col5:
        st.session_state.patient_data["institution"] = st.text_input(
            "의료기관",
            value=st.session_state.patient_data["institution"]
        )

    with col6:
        st.session_state.patient_data["doctor"] = st.text_input(
            "의사명",
            value=st.session_state.patient_data["doctor"]
        )

    with col7:
        st.session_state.patient_data["prescription_date"] = st.date_input(
            "처방일",
            value=st.session_state.patient_data["prescription_date"]
        )

    st.markdown("---")

    # 질환 입력
    st.subheader("🏥 주요 질환")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_condition = st.text_input(
            "질환명 입력 (예: 폐암, 당뇨병)",
            key="new_condition"
        )
    with col2:
        if st.button("추가", key="add_condition"):
            if new_condition and new_condition not in st.session_state.patient_data["conditions"]:
                st.session_state.patient_data["conditions"].append(new_condition)
                st.rerun()

    if st.session_state.patient_data["conditions"]:
        for i, condition in enumerate(st.session_state.patient_data["conditions"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {condition}")
            with col2:
                if st.button("삭제", key=f"del_cond_{i}"):
                    st.session_state.patient_data["conditions"].remove(condition)
                    st.rerun()

    st.markdown("---")

    # 약물 입력
    st.subheader("💊 처방 약물")
    all_drugs = list(DRUG_DATABASE.keys())

    col1, col2 = st.columns([3, 1])
    with col1:
        new_drug = st.selectbox(
            "약물명 검색",
            [""] + all_drugs,
            key="drug_select"
        )
    with col2:
        if st.button("추가", key="add_drug"):
            if new_drug and new_drug not in st.session_state.patient_data["drugs"]:
                st.session_state.patient_data["drugs"].append(new_drug)
                st.rerun()

    if st.session_state.patient_data["drugs"]:
        st.write("**현재 처방약:**")
        cols = st.columns(3)
        for i, drug in enumerate(st.session_state.patient_data["drugs"]):
            with cols[i % 3]:
                col_drug, col_del = st.columns([4, 1])
                with col_drug:
                    st.write(f"💊 {drug}")
                with col_del:
                    if st.button("✕", key=f"del_drug_{i}"):
                        st.session_state.patient_data["drugs"].remove(drug)
                        st.rerun()

# ==================== 2. 약물 정보 검색 ====================
elif page == "💊 약물 정보 검색":
    st.header("💊 약물 정보 검색")

    search_type = st.radio("검색 방식", ["약물명으로 검색", "질환으로 검색"])

    if search_type == "약물명으로 검색":
        drug_name = st.selectbox("약물 선택", list(DRUG_DATABASE.keys()))

        if drug_name:
            drug_info = get_drug_info(drug_name)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"💊 {drug_name}")
                st.write(f"**성분명:** {drug_info.get('generic_name', 'N/A')}")
                st.write(f"**약물 분류:** {drug_info.get('category', 'N/A')}")
                st.write(f"**질환:** {drug_info.get('disease', 'N/A')}")

            with col2:
                dosage = drug_info.get("dosage", {})
                st.write("**용량 정보**")
                st.write(f"• 단일 용량: {dosage.get('single_dose', 'N/A')}")
                st.write(f"• 용법: {dosage.get('frequency', 'N/A')}")
                st.write(f"• 형태: {dosage.get('form', 'N/A')}")
                st.write(f"• 월량: {dosage.get('monthly_quantity', 'N/A')}")

            # 적응증
            st.subheader("📋 적응증")
            indications = drug_info.get("indication", [])
            for indication in indications:
                st.write(f"• {indication}")

            # 임상 증거
            st.subheader("📊 임상 증거")
            st.write(f"**효능:** {drug_info.get('efficacy', 'N/A')}")
            st.write(f"**임상시험:** {drug_info.get('clinical_trial', 'N/A')}")

            # 경고
            st.subheader("⚠️ 경고 및 주의사항")
            warnings = drug_info.get("warnings", [])
            for warning in warnings:
                st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

            # 상호작용
            st.subheader("🔗 약물 상호작용")
            interactions = drug_info.get("interactions", [])
            if interactions:
                interaction_df = pd.DataFrame(interactions)
                st.dataframe(interaction_df, use_container_width=True)
            else:
                st.write("주요 상호작용 없음")

            # 부작용
            st.subheader("💢 부작용")
            side_effects = drug_info.get("side_effects", {})
            for effect, rate in side_effects.items():
                st.write(f"• {effect}: {rate}")

            # 모니터링
            st.subheader("📅 모니터링 일정")
            monitoring = drug_info.get("monitoring", {})
            for check, schedule in monitoring.items():
                st.write(f"• {check}: {schedule}")

            # 가격
            st.subheader("💰 가격")
            price = drug_info.get("price", {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**개당:** {price.get('per_unit', 'N/A')}")
            with col2:
                st.write(f"**월액:** {price.get('monthly', 'N/A')}")
            with col3:
                st.write(f"**보험:** {price.get('insurance', 'N/A')}")

    else:
        disease = st.text_input("질환명 입력")
        if disease:
            drugs_by_disease = search_drug_by_disease(disease)
            if drugs_by_disease:
                st.write(f"**{disease}에 사용되는 약물:**")
                for drug_name in drugs_by_disease.keys():
                    if st.button(drug_name, key=f"disease_{drug_name}"):
                        st.session_state.selected_drug = drug_name
                        st.rerun()
            else:
                st.warning(f"{disease}에 대한 약물이 없습니다.")

# ==================== 3. 안전성 검증 ====================
elif page == "⚠️ 안전성 검증":
    st.header("⚠️ 안전성 종합 검증")

    if not st.session_state.patient_data["drugs"]:
        st.warning("👤 먼저 약물을 입력해주세요. (환자 정보 입력 페이지)")
    else:
        # 종합 안전 검증 실행
        safety_result = SafetyValidator.comprehensive_safety_check(
            drugs=st.session_state.patient_data["drugs"],
            patient_conditions=st.session_state.patient_data["conditions"],
            patient_age=st.session_state.patient_data["age"]
        )

        # 안전 점수 표시
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            safety_score = safety_result["safety_score"]
            color = "green" if safety_score >= 70 else "orange" if safety_score >= 50 else "red"
            st.metric("안전 점수", f"{safety_score}/100", delta=None)

        with col2:
            st.metric("심각한 문제", safety_result["summary"]["critical_issues"])

        with col3:
            st.metric("경고", safety_result["summary"]["warnings"])

        with col4:
            st.metric("중복 약물", safety_result["summary"]["duplicates"])

        st.markdown("---")

        # 권장사항
        recommendation = safety_result["summary"]["recommendation"]
        if "✅" in recommendation:
            st.markdown(f'<div class="safety-pass">{recommendation}</div>', unsafe_allow_html=True)
        elif "🔴" in recommendation:
            st.markdown(f'<div class="critical-alert">{recommendation}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="safety-fail">{recommendation}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # 약물 상호작용
        st.subheader("🔗 약물 상호작용 검사")

        drug_interactions = safety_result["drug_interactions"]

        if drug_interactions["critical_warnings"]:
            st.error("🔴 **치명적 상호작용 발견**")
            for warning in drug_interactions["critical_warnings"]:
                st.markdown(f'''
                <div class="critical-alert">
                <strong>{warning['drugs']}</strong><br>
                원인: {warning['reason']}<br>
                조치: {warning['action']}
                </div>
                ''', unsafe_allow_html=True)

        if drug_interactions["interactions"]:
            st.warning("⚠️ **주의가 필요한 상호작용**")
            interaction_df = pd.DataFrame(drug_interactions["interactions"])
            st.dataframe(interaction_df, use_container_width=True)

        st.markdown("---")

        # 중복 약물
        st.subheader("🟡 중복 약물 검사")

        duplicate_therapy = safety_result["duplicate_therapy"]

        if duplicate_therapy["has_duplicates"]:
            st.warning("🟡 **중복된 약물 클래스 발견**")
            for dup in duplicate_therapy["duplicates"]:
                st.write(f'''
                **{dup['class']}** - {dup['count']}개 발견
                - 약물: {', '.join(dup['drugs'])}
                - {dup['action']}
                ''')
        else:
            st.success("✅ 중복 약물 없음")

        st.markdown("---")

        # 질환별 금기약물
        st.subheader("🚫 질환별 금기약물 검사")

        contraindications = safety_result["contraindications"]

        if not contraindications["safe"]:
            st.error("🔴 **금기약물 발견**")
            for contra in contraindications["contraindications"]:
                st.markdown(f'''
                <div class="critical-alert">
                <strong>{contra['disease']} 환자</strong><br>
                금기약물: {contra['drug']}<br>
                이유: {contra['reason']}<br>
                조치: {contra['action']}
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.success("✅ 금기약물 없음")

        st.markdown("---")

        # 모니터링 스케줄
        st.subheader("📅 맞춤형 모니터링 스케줄")

        monitoring = safety_result["monitoring_schedule"]

        tabs = st.tabs(["매일", "주 1회", "월 1회", "분기", "반기", "연 1회"])

        with tabs[0]:
            if monitoring["daily"]:
                for item in monitoring["daily"]:
                    st.write(f"• {item}")
            else:
                st.write("매일 모니터링 항목 없음")

        with tabs[1]:
            if monitoring["weekly"]:
                for item in monitoring["weekly"]:
                    st.write(f"• {item}")
            else:
                st.write("주 1회 모니터링 항목 없음")

        with tabs[2]:
            if monitoring["monthly"]:
                for item in monitoring["monthly"]:
                    st.write(f"• {item}")
            else:
                st.write("월 1회 모니터링 항목 없음")

        with tabs[3]:
            if monitoring["quarterly"]:
                for item in monitoring["quarterly"]:
                    st.write(f"• {item}")
            else:
                st.write("분기 모니터링 항목 없음")

        with tabs[4]:
            if monitoring["semiannually"]:
                for item in monitoring["semiannually"]:
                    st.write(f"• {item}")
            else:
                st.write("반기 모니터링 항목 없음")

        with tabs[5]:
            if monitoring["annually"]:
                for item in monitoring["annually"]:
                    st.write(f"• {item}")
            else:
                st.write("연 1회 모니터링 항목 없음")

        if monitoring["special_notes"]:
            st.info("**특별 주의사항:**\n" + "\n".join(monitoring["special_notes"]))

# ==================== 4. 처방 분석 ====================
elif page == "📊 처방 분석":
    st.header("📊 처방 분석")

    if not st.session_state.patient_data["drugs"]:
        st.warning("👤 먼저 약물을 입력해주세요. (환자 정보 입력 페이지)")
    else:
        # 환자 정보 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("환자명", st.session_state.patient_data["name"] or "미입력")
        with col2:
            st.metric("나이", st.session_state.patient_data["age"])
        with col3:
            st.metric("성별", st.session_state.patient_data["gender"])
        with col4:
            st.metric("진료과", st.session_state.patient_data["department"] or "미입력")

        st.markdown("---")

        # 질환별 약물 정리
        st.subheader("🏥 질환별 약물 정보")

        for condition in st.session_state.patient_data["conditions"]:
            with st.expander(f"🏥 {condition}", expanded=True):
                condition_drugs = search_drug_by_disease(condition)
                prescribed_for_condition = [d for d in st.session_state.patient_data["drugs"] if d in condition_drugs]

                if prescribed_for_condition:
                    for drug in prescribed_for_condition:
                        drug_info = get_drug_info(drug)
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**💊 {drug}**")
                            st.write(f"성분: {drug_info.get('generic_name', 'N/A')}")

                        with col2:
                            dosage = drug_info.get("dosage", {})
                            st.write(f"용량: {dosage.get('single_dose', 'N/A')} {dosage.get('frequency', '')}")

                        # 경고 표시
                        warnings = drug_info.get("warnings", [])
                        if warnings:
                            st.write("**주의사항:**")
                            for warning in warnings[:3]:  # 최상위 3개만
                                st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # 약물 통계
        st.subheader("📊 약물 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("총 약물 수", len(st.session_state.patient_data["drugs"]))

        with col2:
            all_categories = []
            for drug in st.session_state.patient_data["drugs"]:
                info = get_drug_info(drug)
                all_categories.append(info.get("category", "기타"))
            st.metric("약물 분류 수", len(set(all_categories)))

        with col3:
            # 중복 약물 클래스 계산
            duplicate_count = 0
            for drug_class, drugs in SafetyValidator.DUPLICATE_DRUG_CLASSES.items():
                found = [d for d in st.session_state.patient_data["drugs"] if d in drugs]
                if len(found) > 1:
                    duplicate_count += len(found) - 1
            st.metric("중복 약물", duplicate_count)

        st.markdown("---")

        # 약물 상호작용 네트워크
        st.subheader("🔗 약물 상호작용 매트릭스")

        if len(st.session_state.patient_data["drugs"]) > 1:
            interaction_matrix = []
            for i, drug1 in enumerate(st.session_state.patient_data["drugs"]):
                for drug2 in st.session_state.patient_data["drugs"][i+1:]:
                    interactions = SafetyValidator.DRUG_INTERACTIONS_DB.get(drug1, {}).get(drug2, {})
                    if interactions:
                        interaction_matrix.append({
                            "약물 1": drug1,
                            "약물 2": drug2,
                            "심각도": interactions.get("severity", "unknown"),
                            "설명": interactions.get("description", "")
                        })

            if interaction_matrix:
                interaction_df = pd.DataFrame(interaction_matrix)
                st.dataframe(interaction_df, use_container_width=True)
            else:
                st.info("주요 상호작용 없음")
        else:
            st.info("약물이 1개 이하이므로 상호작용 분석 불가")

# ==================== 5. 약물 데이터베이스 ====================
elif page == "📚 약물 데이터베이스":
    st.header("📚 전체 약물 데이터베이스")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.metric("등록된 약물 수", len(DRUG_DATABASE))

    with col2:
        categories = set()
        for drug_info in DRUG_DATABASE.values():
            categories.add(drug_info.get("category", "기타"))
        st.metric("약물 분류", len(categories))

    st.markdown("---")

    # 약물 검색
    search_term = st.text_input("약물명 또는 성분명으로 검색")

    drugs_to_display = []
    if search_term:
        for drug_name, info in DRUG_DATABASE.items():
            if search_term.lower() in drug_name.lower() or \
               search_term.lower() in info.get("generic_name", "").lower():
                drugs_to_display.append((drug_name, info))
    else:
        drugs_to_display = list(DRUG_DATABASE.items())

    st.write(f"**검색 결과: {len(drugs_to_display)}개**")

    # 약물 목록 표시
    for drug_name, info in drugs_to_display[:20]:  # 최대 20개 표시
        with st.expander(f"💊 {drug_name}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**성분명:** {info.get('generic_name', 'N/A')}")
                st.write(f"**분류:** {info.get('category', 'N/A')}")
                st.write(f"**질환:** {info.get('disease', 'N/A')}")

            with col2:
                dosage = info.get("dosage", {})
                st.write(f"**용량:** {dosage.get('single_dose', 'N/A')}")
                st.write(f"**용법:** {dosage.get('frequency', 'N/A')}")
                st.write(f"**월량:** {dosage.get('monthly_quantity', 'N/A')}")

            st.markdown("**적응증:** " + ", ".join(info.get("indication", [])))

# ==================== 푸터 ====================
st.markdown("---")

st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
    <p>⚕️ PHARMA-HYBRID v3.0 - 의료 의사결정 지원 시스템</p>
    <p>⚠️ 본 시스템은 의료 전문가의 판단을 보조하는 도구입니다. 최종 결정은 의료 전문가의 책임입니다.</p>
    <p>📋 FDA/NIH 임상 기준 기반 | 마지막 업데이트: 2026-04-30</p>
    </div>
""", unsafe_allow_html=True)
