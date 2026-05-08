import os

path = '전부_코드화_데이터통합시스템.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

header = lines[:1310]

new_main = """
def main():
    init_session()

    patients = st.session_state.patients
    rxs      = st.session_state.rxs
    pid      = st.session_state.pid
    pat      = patients.get(pid, {})
    pat_rxs  = [r for r in rxs if r["patient_id"] == pid]

    if "last_pid" not in st.session_state:
        st.session_state.last_pid = pid
    
    if st.session_state.last_pid != pid:
        st.session_state.voice_ai_answer = ""
        st.session_state.voice_result = ""
        st.session_state.last_pid = pid

    # ─────────────────────────────────────────────────────────────────
    # [사령관 명령] 모든 관리 컨트롤 사이드바 배치 + 응급 버튼
    # ─────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="c-vault">🛡️ CLINICAL COMMAND CENTER</div>', unsafe_allow_html=True)
        
        # 환자 선별
        pat_options = list(patients.keys())
        current_index = pat_options.index(pid) if pid in pat_options else 0
        st.selectbox(
            "📍 임상 관리 대상 선별", 
            options=pat_options, 
            index=current_index,
            format_func=lambda x: f"{patients[x]['real_name']} ({patients[x].get('age','?')}세)",
            key="patient_selector",
            on_change=lambda: setattr(st.session_state, 'pid', st.session_state.patient_selector)
        )
        
        # 페르소나 및 브리핑
        st.radio("브리핑 모드", ["의학 전문가", "환자용 가이드"], horizontal=True, key="persona")
        if st.button("🎙️ 베테랑 임상 브리핑 가동", use_container_width=True):
            with st.spinner("Persona 로드 중..."):
                ans = analyze_voice("환자 상태 정밀 분석 보고해", pat, pat_rxs, pid)
                st.session_state.voice_ai_answer = ans
                st.rerun()

        st.markdown("<hr style='margin:15px 0; border-color:rgba(0,242,255,0.2);'>", unsafe_allow_html=True)

        # 응급 버튼 (119/112)
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            if st.button("🚨 119", type="primary", use_container_width=True):
                st.error("🚑 119 긴급 출동 요청됨")
        with ecol2:
            if st.button("🚔 112", type="primary", use_container_width=True):
                st.error("🚔 112 긴급 신고 완료")
        
        if st.button("⏹ 경보 시퀀스 중단", use_container_width=True, key="btn_stop_siren_sidebar"):
            st.session_state.force_siren = False
            st.rerun()

    # ─────────────────────────────────────────────────────────────────
    # 메인 전술 인터페이스 (MAIN COMMAND DECK) - 4 ROWS
    # ─────────────────────────────────────────────────────────────────
    
    # [Row 1] 환자 전략 프로필 (Horizontal Full-Width)
    st.markdown(f\"\"\"
    <div style="background:rgba(0,40,80,0.8); border:1.5px solid #00f2ff; border-radius:12px; padding:20px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1; text-align:center;">
                <span style="color:rgba(0,242,255,0.6); font-size:0.8rem;">🏥 거점 병원</span>
                <div style="color:#ffffff; font-size:1.1rem; font-weight:700;">{pat.get('hospital','삼성서울병원')}</div>
            </div>
            <div style="flex:1; border-left:1px solid rgba(0,242,255,0.2); text-align:center;">
                <span style="color:rgba(0,242,255,0.6); font-size:0.8rem;">👤 환자 성명</span>
                <div style="color:#00f2ff; font-size:1.8rem; font-weight:900;">{pat.get('real_name','김상은')}</div>
            </div>
            <div style="flex:1; border-left:1px solid rgba(0,242,255,0.2); text-align:center;">
                <span style="color:rgba(0,242,255,0.6); font-size:0.8rem;">📊 연령/성별</span>
                <div style="color:#ffffff; font-size:1.1rem; font-weight:700;">{pat.get('age','?')}세 / {pat.get('gender','?')}</div>
            </div>
            <div style="flex:1; border-left:1px solid rgba(0,242,255,0.2); text-align:center;">
                <span style="color:#ffcc00; font-size:0.8rem;">🩺 주진단명</span>
                <div style="color:#ffcc00; font-size:1.1rem; font-weight:700;">{pat.get('diagnosis','폐암')}</div>
            </div>
            <div style="flex:1; border-left:1px solid rgba(0,242,255,0.2); text-align:center;">
                <span style="color:#ff4444; font-size:0.8rem;">⚠️ 현재 합병증</span>
                <div style="color:#ff4444; font-size:1.1rem; font-weight:700;">{pat.get('complications','없음')}</div>
            </div>
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)

    # [Row 2] 임상 약물 및 주사 매핑
    st.markdown('<div style="color:#00f2ff; font-weight:700; margin-bottom:10px;">💊 CLINICAL MEDICATION & INJECTION MAPPING</div>', unsafe_allow_html=True)
    med_names = ", ".join([rx.get("medication_name") for rx in pat_rxs])
    dosages = " / ".join([f"{rx.get('dosage')}({rx.get('frequency')})" for rx in pat_rxs])
    cancer_type = pat_rxs[0].get("cancer_type") if pat_rxs else "임상 정보 확인 중"
    st.markdown(f\"\"\"
    <div style="background:rgba(0,20,40,0.6); border:1px solid #00f2ff; border-radius:10px; padding:20px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <span style="font-size:1.5rem;">💊</span>
            <span style="background:#00f2ff; color:#000; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:900;">ORAL / INJECTION</span>
        </div>
        <div style="color:#ffffff; font-size:1.3rem; font-weight:700;">{med_names}</div>
        <div style="color:rgba(255,255,255,0.6); font-size:0.95rem; margin-top:8px;">용량 및 횟수: {dosages}</div>
        <div style="color:#00f2ff; font-size:0.85rem; margin-top:12px; border-top:1px solid rgba(255,255,255,0.1); padding-top:10px;">
            🎯 임상 목표: {cancer_type} 표적 치료
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)

    # [Row 3] 주변 실시간 약국 현황
    if HAS_PHARMACY_WIDGET:
        st.markdown(render_pharmacy_widget_html(max_items=3), unsafe_allow_html=True)

    # [Row 4] 처방전 업로드
    st.markdown('<div style="color:#00f2ff; font-weight:700; margin:20px 0 10px 0;">📸 STRATEGIC PRESCRIPTION INTELLIGENCE</div>', unsafe_allow_html=True)
    up_cols = st.columns([1, 1])
    with up_cols[0]:
        uploaded_file = st.file_uploader("📂 처방전 이미지 업로드", type=["jpg", "jpeg", "png"], key="rx_up_main")
    with up_cols[1]:
        if uploaded_file:
            st.image(uploaded_file, caption="처방전 분석 중...", use_container_width=True)
        else:
            st.markdown('<div style="height:150px; border:1px dashed rgba(0,242,255,0.2); border-radius:10px; display:flex; align-items:center; justify-content:center; color:rgba(0,242,255,0.3);">처방전 이미지를 업로드하세요</div>', unsafe_allow_html=True)

    # [하단] AI 마스터 브리핑
    if st.session_state.voice_ai_answer:
        st.markdown("---")
        st.markdown(f"### 🎙️ AI 베테랑 임상 브리핑")
        st.write(st.session_state.voice_ai_answer)
        tts_button(st.session_state.voice_ai_answer, "tts_main")

if __name__ == "__main__":
    main()
"""

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(header)
    f.write(new_main)

print("Main function rewrite complete.")
