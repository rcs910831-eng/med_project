# 🎤 Celebrity Voice TTS Feature Guide
## 연예인 목소리 음성 합성 기능 가이드

### 📋 개요 (Overview)

의료 정보 시스템에 고품질의 한국어 음성 합성 기능이 추가되었습니다. 로봇 음성이 아닌 연예인 목소리 옵션으로 자연스러운 정보 전달이 가능합니다.

- **기본(로봇)**: 표준 시스템 음성
- **장원영(Wonyoung)**: IVE - 밝고 맑은 목소리 (부드럽고 친근한 느낌)
- **카리나(Karina)**: aespa - 깊고 매력있는 목소리 (세련되고 신뢰감 있는 느낌)
- **안유진(Yujin)**: IVE - 따뜻하고 부드러운 목소리 (편안하고 안정적인 느낌)

### 🚀 빠른 시작 (Quick Start)

#### 1. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

**필수 라이브러리:**
- `gtts` (Google Translate TTS) - 무료 한국어 음성 합성
- `pyttsx3` - 로컬 TTS 엔진 (대체)
- `streamlit` - 웹 앱 프레임워크

#### 2. 앱 실행
```bash
streamlit run main_app.py
```

#### 3. 음성 설정
좌측 사이드바에서:
1. **🎤 음성 낭독** 섹션 찾기
2. "목소리 선택" 드롭다운에서 원하는 연예인 목소리 선택
3. "음성 낭독 활성화" 체크박스로 기능 활성화

### 📖 사용 가능한 기능 (Available Features)

#### Tab 5: 🇺🇸 FDA데이터
- 약품 선택 후 **"🎤 FDA 정보 음성 낭독"** 버튼 클릭
- FDA 승인 정보, 제조사, 적응증 등이 선택한 음성으로 합성됨
- HTML5 오디오 플레이어에서 재생 가능

#### Tab 6: 🎗 암프로토콜DB
- 암종 선택 후 **"🎤 암종 정보 음성 낭독"** 버튼 클릭
- ICD10 코드, 바이오마커, 1차 치료 정보가 음성으로 제공됨
- 복잡한 의료 정보를 자연스럽게 설명

#### Tab 7: 🥗 식단가이드
- 암종별 또는 질환별 식단 선택 후 **"🎤 식단 정보 음성 낭독"** 버튼 클릭
- 영양 목표 수치, 권장 식품, 제한 식품 정보가 음성으로 제공됨
- 환자 친화적인 설명으로 이해도 향상

### 🔧 기술 구조 (Technical Architecture)

#### 음성 엔진 선택 (Voice Engine Priority)
```
1. Google Translate TTS (gTTS)  - 무료, 효과적
2. pyttsx3                      - 로컬, 오프라인 지원
3. Google Cloud TTS             - 고급 기능 (API 키 필요)
```

#### 음성 프로필 구조
```python
{
    "name": "Wonyoung",           # 영문 이름
    "group": "IVE",               # 그룹/분류
    "description": "밝고 맑은...", # 음성 설명
    "pitch": 1.2,                 # 음높이 (0.5-2.0)
    "speed": 0.95,                # 속도 (0.5-2.0)
    "style": "bright_clear",      # 음성 스타일
    "color": "#FF69B4"            # UI 색상
}
```

### 💻 프로그래머 가이드 (Developer Guide)

#### 새로운 음성 추가
```python
from celebrity_voice_engine import CelebrityVoiceEngine

engine = CelebrityVoiceEngine(engine_type="gtts")

# 새로운 음성 추가
new_voice = {
    "name": "NewVoice",
    "group": "Group Name",
    "description": "설명",
    "pitch": 1.0,
    "speed": 1.0,
    "style": "style",
    "color": "#HexColor"
}
engine.CELEBRITY_VOICES["신규음성"] = new_voice
```

#### 커스텀 텍스트 음성 합성
```python
from celebrity_voice_engine import CelebrityVoiceEngine

engine = CelebrityVoiceEngine(engine_type="gtts")
engine.set_voice("장원영(Wonyoung)")

# 오디오 바이트 반환
audio_bytes = engine.synthesize_to_audio("합성할 텍스트")

# HTML 플레이어 생성
html = engine.create_audio_html_player("합성할 텍스트", "장원영(Wonyoung)")

# Base64 인코딩 (API 전송용)
b64 = engine.synthesize_to_base64("합성할 텍스트")
```

#### Streamlit 세션 통합
```python
from celebrity_voice_engine import VoiceSessionManager

# 세션 관리자 초기화
voice_mgr = VoiceSessionManager(st.session_state)

# 음성 설정
voice_mgr.set_voice("카리나(Karina)")

# 현재 선택된 음성
current = voice_mgr.get_selected_voice()

# 활성화 상태
if voice_mgr.is_enabled():
    audio_b64 = voice_mgr.synthesize("텍스트")
```

### ⚙️ 설정 옵션 (Configuration)

#### TTS 엔진 변경
`main_app.py`에서:
```python
voice_mgr = VoiceSessionManager(st.session_state)
engine = voice_mgr.get_engine()

# 엔진 타입: "gtts", "pyttsx3", "google"
```

#### 음성 특성 커스터마이징
```python
engine.CELEBRITY_VOICES["장원영(Wonyoung)"]["pitch"] = 1.3  # 더 높은 음성
engine.CELEBRITY_VOICES["장원영(Wonyoung)"]["speed"] = 0.85  # 더 느린 속도
```

### 🐛 트러블슈팅 (Troubleshooting)

#### Issue 1: gTTS가 설치되지 않음
**해결방법:**
```bash
pip install gtts
```

#### Issue 2: 오디오 재생 안됨
**확인사항:**
- 브라우저가 HTML5 오디오 지원하는지 확인
- 네트워크 연결 상태 확인 (gTTS는 인터넷 필요)
- 브라우저 콘솔에서 에러 메시지 확인

#### Issue 3: 한국어 인식 안됨
**해결방법:**
```bash
pip install --upgrade gtts
```

#### Issue 4: 음성 선택 안 됨
**확인사항:**
- `celebrity_voice_engine.py` 파일이 같은 디렉토리에 있는지 확인
- `import` 에러 메시지 확인
- 파이썬 인코딩이 UTF-8로 설정되어 있는지 확인

### 📊 성능 (Performance)

| 엔진 | 속도 | 품질 | 인터넷 필요 | 한국어 |
|------|------|------|-----------|-------|
| gTTS | 빠름 | 중간 | 필수 | ⭐⭐⭐⭐ |
| pyttsx3 | 중간 | 낮음 | 불필요 | ⭐⭐⭐ |
| Google Cloud | 빠름 | 높음 | 필수 | ⭐⭐⭐⭐⭐ |

### 🔐 보안 (Security)

- 음성 합성 시 실제 환자 이름은 합성되지 않음
- 의료 정보만 음성으로 변환됨
- 오디오 파일은 브라우저 메모리에만 존재
- 서버에 저장되지 않음

### 📝 로깅 (Logging)

음성 엔진은 로깅을 통해 디버깅 정보 제공:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

로그 메시지 예시:
```
✅ Google Translate TTS 엔진 로드됨
🎤 선택 목소리: 장원영(Wonyoung) - 밝고 맑은 목소리
🧠 음성 합성 중...
✅ 음성 합성 완료 (45KB)
```

### 🎯 향후 개선 사항 (Future Improvements)

- [ ] 실시간 음성 조정 (실시간 pitch/speed 조절)
- [ ] 감정 표현 추가 (행복, 슬픔, 중립)
- [ ] 다국어 지원 (영어, 중국어, 일본어)
- [ ] 음성 저장 및 재사용
- [ ] 배경음 추가
- [ ] 음성 정규화 (loudness 표준화)

### 📞 문의 (Support)

문제 발생 시:
1. `test_celebrity_voices.py` 실행하여 엔진 정상 작동 확인
2. `requirements.txt`에서 필수 패키지 설치 확인
3. 콘솔 로그에서 에러 메시지 확인

---

**Last Updated:** 2026-04-29
**Version:** 1.0
**Status:** Production Ready ✅
