# 🎤 빠른 시작 가이드 (Quick Start Guide)

## 1️⃣ 설치 (Installation)

### 필수 패키지 설치
```bash
pip install -r requirements.txt
```

또는 개별 설치:
```bash
pip install streamlit gtts pyttsx3 plotly requests
```

---

## 2️⃣ 테스트 방법 (Testing Methods)

### 방법 1: 간단한 데모 앱 (Recommended)
가장 빠르고 직관적인 테스트 방법:

```bash
streamlit run streamlit_voice_demo.py
```

**특징:**
- 모든 음성을 한눈에 비교
- 직접 텍스트 입력 가능
- 의료 정보 샘플 포함
- 웹 브라우저에서 바로 테스트

---

### 방법 2: 파이썬 예제 실행 (Python Examples)
7가지 실용적인 예제 모음:

```bash
python demo_celebrity_voices.py
```

**포함된 예제:**
1. 기본 사용법 - 음성 합성 및 파일 저장
2. HTML5 오디오 플레이어 생성
3. 세션 관리자 사용
4. 의료 정보 음성화
5. 모든 음성 비교
6. 커스텀 음성 추가
7. 배치 처리

**출력:** 각 예제마다 MP3 파일 자동 생성

---

### 방법 3: 메인 의료 앱
완전한 의료 정보 시스템:

```bash
streamlit run main_app.py
```

**기능:**
- 7개 탭: 처방약, 약가, 뉴스, 지식베이스, FDA, 암프로토콜, 식단
- 모든 섹션에서 음성 낭독 가능
- 실제 의료 데이터 통합

---

## 3️⃣ 기본 파이썬 코드 예제

### 예제 1: 간단한 음성 합성
```python
from celebrity_voice_engine import CelebrityVoiceEngine

# 엔진 생성
engine = CelebrityVoiceEngine(engine_type="gtts")

# 음성 선택
engine.set_voice("장원영(Wonyoung)")

# 텍스트를 오디오로 합성
text = "안녕하세요. 약물 정보 시스템입니다."
audio = engine.synthesize_to_audio(text)

# 파일로 저장
with open("output.mp3", "wb") as f:
    f.write(audio)

print("✅ 음성 합성 완료!")
```

### 예제 2: Streamlit과 함께 사용
```python
import streamlit as st
from celebrity_voice_engine import CelebrityVoiceEngine

# 사이드바에서 음성 선택
voice = st.sidebar.selectbox("음성 선택", [
    "기본(로봇)",
    "장원영(Wonyoung)",
    "카리나(Karina)",
    "안유진(Yujin)"
])

# 텍스트 입력
text = st.text_area("변환할 텍스트")

# 변환 버튼
if st.button("🎤 음성 변환"):
    engine = CelebrityVoiceEngine(engine_type="gtts")
    engine.set_voice(voice)
    
    # HTML 플레이어 생성
    html = engine.create_audio_html_player(text, voice)
    st.markdown(html, unsafe_allow_html=True)
```

### 예제 3: 의료 정보 음성화
```python
from celebrity_voice_engine import CelebrityVoiceEngine

engine = CelebrityVoiceEngine(engine_type="gtts")

# 의료 정보들
medical_info = {
    "약품": "타세바정은 표피 성장 인자 수용체 억제제입니다.",
    "암종": "폐암 3기 환자의 1차 치료는 수술과 항암제입니다.",
    "식단": "항암제 복용 중에는 충분한 단백질 섭취가 필요합니다.",
}

# 각 정보를 장원영 음성으로 합성
engine.set_voice("장원영(Wonyoung)")
for info_type, text in medical_info.items():
    audio = engine.synthesize_to_audio(text)
    # 처리...
```

---

## 4️⃣ 음성 비교

| 음성 | 특징 | 용도 |
|------|------|------|
| **기본(로봇)** | 중립적, 명확함 | 객관적 정보 전달 |
| **장원영(Wonyoung)** | 밝고 맑음 | 긍정적, 친근한 정보 |
| **카리나(Karina)** | 깊고 매력적 | 신뢰감, 전문적 정보 |
| **안유진(Yujin)** | 따뜻하고 부드러움 | 공감, 편안한 정보 |

---

## 5️⃣ 자주 묻는 질문 (FAQ)

### Q1: gTTS가 작동 안 합니다
**A:** 인터넷 연결 확인 후 재설치:
```bash
pip install --upgrade gtts
```

### Q2: 한글이 이상하게 나옵니다
**A:** 파이썬 파일 인코딩 확인:
```python
# -*- coding: utf-8 -*-  # 파일 맨 위에 추가
```

### Q3: 로컬에서만 사용하고 싶습니다
**A:** pyttsx3 사용 (인터넷 불필요):
```python
engine = CelebrityVoiceEngine(engine_type="pyttsx3")
```

### Q4: 음성 특성을 변경할 수 있나요?
**A:** 가능합니다:
```python
engine.CELEBRITY_VOICES["장원영(Wonyoung)"]["pitch"] = 1.5  # 더 높게
engine.CELEBRITY_VOICES["장원영(Wonyoung)"]["speed"] = 0.8  # 더 천천히
```

### Q5: 여러 텍스트를 한 번에 처리할 수 있나요?
**A:** demo_celebrity_voices.py의 예제 7 참고 (배치 처리)

---

## 6️⃣ 트러블슈팅 (Troubleshooting)

### 문제: "ModuleNotFoundError: No module named 'celebrity_voice_engine'"
```bash
# 같은 디렉토리에 celebrity_voice_engine.py가 있는지 확인
# 없으면 설치된 경로 확인
python -c "import celebrity_voice_engine; print(celebrity_voice_engine.__file__)"
```

### 문제: "No audio support"
```bash
# 브라우저 재시작 또는 다른 브라우저 시도
# HTML5 오디오 지원 확인
```

### 문제: 느린 음성 합성
```python
# 더 빠른 엔진 사용
engine = CelebrityVoiceEngine(engine_type="pyttsx3")
```

---

## 7️⃣ 파일 구조

```
med_project/
├── celebrity_voice_engine.py      # 핵심 음성 엔진
├── main_app.py                    # 의료 정보 통합 앱
├── streamlit_voice_demo.py        # 간단한 데모 앱 ⭐ 추천
├── demo_celebrity_voices.py       # 7가지 파이썬 예제
├── requirements.txt               # 필수 패키지
├── VOICE_FEATURE_GUIDE.md         # 상세 설명서
└── QUICK_START.md                 # 이 파일
```

---

## 8️⃣ 다음 단계 (Next Steps)

### 초급 사용자
1. `streamlit_voice_demo.py` 실행
2. 각 음성 들어보기
3. 직접 텍스트 입력해보기

### 중급 사용자
1. `demo_celebrity_voices.py` 실행
2. 예제 코드 분석
3. 자신의 텍스트로 수정해보기

### 고급 사용자
1. `main_app.py` 통합 앱 사용
2. 코드 커스터마이징
3. 새로운 음성 추가

---

## 9️⃣ 문의 및 지원 (Support)

문제 발생 시:
1. `demo_celebrity_voices.py` 실행하여 기본 기능 확인
2. 콘솔 로그 메시지 확인
3. 필수 패키지 재설치
4. `VOICE_FEATURE_GUIDE.md` 상세 설명서 참고

---

## 🔟 라이센스 및 저작권

- **gTTS**: Apache License 2.0
- **pyttsx3**: MIT License
- **Streamlit**: Apache License 2.0
- **이 프로젝트**: MIT License

---

**최종 업데이트:** 2026-04-29
**상태:** ✅ 완전 작동 (Fully Functional)
**버전:** 1.0

🎉 **행운을 빕니다! 즐거운 음성 합성 경험되세요!**
