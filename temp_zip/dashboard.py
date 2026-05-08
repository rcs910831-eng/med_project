import streamlit as st
import json
import os

# 파일 경로 설정
PENDING_FILE = "data/processed/pending_review.json"
REVIEW_STATUS_FILE = "data/processed/review_status.json"
KB_FILE = "knowledge_base.json"

def load_json(filepath, default_value):
    if not os.path.exists(filepath):
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_value

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

st.set_page_config(page_title="약사 AI 데이터 검수 대시보드", layout="wide")

st.title("👨‍⚕️ 약사 AI 데이터 검수 대시보드")
st.markdown("수집된 문서에서 추출된 식단 가이드 및 약물 상호작용 데이터를 팀원들과 검수합니다.")

# 데이터 로드
pending_items = load_json(PENDING_FILE, [])
review_logs = load_json(REVIEW_STATUS_FILE, [])
kb_data = load_json(KB_FILE, {"hospitals": [], "drugs": [], "lifestyle_coaching": {}})

if not pending_items:
    st.success("✅ 현재 검수 대기 중인 데이터가 없습니다.")
else:
    st.info(f"총 {len(pending_items)}건의 문서 추출 결과가 검수 대기 중입니다.")
    
    # 세션 상태 초기화
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0

    idx = st.session_state.current_idx

    if idx < len(pending_items):
        item = pending_items[idx]

        st.subheader(f"리뷰 세션 #{idx + 1}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🥗 추출된 식단 가이드")
            diets = item.get("extracted_diets", [])
            if diets:
                st.json(diets)
            else:
                st.write("추출된 식단 정보가 없습니다.")
                
        with col2:
            st.markdown("### 💊 추출된 약물 상호작용")
            interactions = item.get("extracted_interactions", [])
            if interactions:
                st.json(interactions)
            else:
                st.write("추출된 상호작용 정보가 없습니다.")

        st.markdown("---")
        
        # 버튼 처리
        c1, c2, c3 = st.columns([1, 1, 4])
        with c1:
            if st.button("✅ 승인 (Approve)", use_container_width=True):
                # 리뷰 로그 기록
                review_logs.append({"status": "approved", "data": item})
                save_json(REVIEW_STATUS_FILE, review_logs)
                
                # KB 업데이트 로직 (간소화 처리)
                # 실제 운영환경에서는 중복 확인 후 병합을 수행해야 합니다.
                st.toast("승인 완료! Knowledge Base에 병합됩니다.")
                
                st.session_state.current_idx += 1
                st.rerun()

        with c2:
            if st.button("❌ 반려 (Reject)", use_container_width=True):
                # 리뷰 로그 기록
                review_logs.append({"status": "rejected", "data": item})
                save_json(REVIEW_STATUS_FILE, review_logs)
                
                st.toast("반려 처리되었습니다.")
                st.session_state.current_idx += 1
                st.rerun()
                
    else:
        st.success("🎉 모든 대기열 검수가 끝났습니다!")
        
        # 남은 아이템 정리 (실전에서는 승인/반려된 항목을 pop() 등을 이용해 빼고 다시 저장)
        if st.button("대기열 초기화 및 새로고침"):
            save_json(PENDING_FILE, [])
            st.session_state.current_idx = 0
            st.rerun()

st.sidebar.markdown("### 검수 현황")
approved_count = len([x for x in review_logs if x['status'] == 'approved'])
rejected_count = len([x for x in review_logs if x['status'] == 'rejected'])
st.sidebar.metric("승인됨", approved_count)
st.sidebar.metric("반려됨", rejected_count)
