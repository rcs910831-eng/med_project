import streamlit as st
import os
from celebrity_voice_engine import CelebrityVoiceEngine

st.set_page_config(page_title="Celebrity AI Voice Demo", page_icon="🎙️", layout="wide")

st.title("🎙️ Celebrity AI Voice Engine Demo")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚙️ Voice Settings")
    persona_list = ["장원영(Wonyoung)", "카리나(Karina)", "안유진(AnYuJin)", "전문의(Doctor)"]
    selected_persona = st.selectbox("Select Persona", persona_list)
    
    text_input = st.text_area("Input Text", 
                              value="안녕하세요 사령관님! 장원영 AI 보이스입니다. 오늘 건강 상태는 어떠신가요? 뛰어 읽기가 잘 되는지 확인해 보세요.", 
                              height=150)
    
    if st.button("🚀 Generate & Play Voice", use_container_width=True):
        if text_input.strip():
            with st.spinner("Generating high-quality AI voice..."):
                try:
                    engine = CelebrityVoiceEngine(engine_type="gtts")
                    engine.set_voice(selected_persona)
                    audio_data = engine.synthesize_to_audio(text_input)
                    
                    if audio_data:
                        st.session_state.audio_data = audio_data
                        st.success(f"Successfully generated {selected_persona} voice!")
                    else:
                        st.error("Failed to generate audio data.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter some text.")

with col2:
    st.subheader("🔊 Audio Output")
    if "audio_data" in st.session_state:
        st.audio(st.session_state.audio_data, format="audio/mp3", autoplay=True)
        
        # Download button
        st.download_button(
            label="⬇️ Download MP3",
            data=st.session_state.audio_data,
            file_name=f"celebrity_voice_{selected_persona}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )
    else:
        st.info("Generated audio will appear here.")

st.markdown("---")
st.markdown("### 📝 Text Cleaning & Pausing Logic Test")
test_text = "건강 맞춤 안내: 방문 사유 분석]** 안녕하세요. 현재 폐암 치료를 위해 방문하셨네요."
clean_test = test_text.replace(']**', ']. ').replace('현재 ', '현재, ').replace('폐암', '폐암, ')
st.code(f"Original: {test_text}\nCleaned: {clean_test}")
