# 🎤 음성 기능 빠른 참고 (Quick Reference)

## 🚀 5분 만에 시작하기

### 1️⃣ Google Cloud 설정 (10분)

```bash
# Step 1: Console 접속
# https://console.cloud.google.com/

# Step 2: 프로젝트 생성 (pharma-mobile)

# Step 3: 2개 API 활성화
# - Cloud Speech-to-Text API
# - Cloud Text-to-Speech API

# Step 4: 서비스 계정 생성 후 JSON 키 다운로드
# -> google-cloud-key.json 파일 저장

# Step 5: 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS="./google-cloud-key.json"
```

### 2️⃣ 백엔드 실행

```bash
cd /path/to/med_project
pip install -r requirements_backend.txt  # (필요시)
python backend_main.py
```

**출력:**
```
╔════════════════════════════════════════════════════════════╗
║         🏥 PHARMA-MOBILE FastAPI Backend v1.0             ║
║  📍 http://localhost:8000                                 ║
║  📖 API 문서: http://localhost:8000/docs                 ║
╚════════════════════════════════════════════════════════════╝
```

### 3️⃣ Flutter 앱 실행

```bash
cd pharma_mobile
flutter pub get
flutter run -d chrome
```

### 4️⃣ 음성 테스트

1. Flutter 앱에서 사용자명 입력
2. "사용자 등록" 버튼 클릭
3. 🎤 **음성 녹음** 버튼 클릭
4. 증상을 음성으로 말하기
5. 📤 **음성 분석** 버튼 클릭
6. 🔊 음성 응답 자동 재생 (완료!)

---

## 📚 핵심 파일

| 파일 | 용도 | 줄 수 |
|------|------|------|
| `voice_handler.py` | Google Cloud STT/TTS 통합 | 200+ |
| `backend_main.py` | 3개 음성 API 엔드포인트 | +539 |
| `pharma_mobile/lib/main.dart` | 음성 UI 및 녹음 기능 | 390 |
| `VOICE_FEATURES_GUIDE.md` | 완전한 사용 설명서 | 531 |
| `IMPLEMENTATION_SUMMARY.md` | 구현 상세 보고서 | 485 |

---

## 🎯 3개 API 엔드포인트

### 1. STT (음성 → 텍스트)
```bash
curl -F "audio_file=@voice.wav" \
  "http://localhost:8000/api/voice/transcribe?user_id=user001"
```

### 2. TTS (텍스트 → 음성)
```bash
curl -X POST "http://localhost:8000/api/voice/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text":"복약 정보를 알려드립니다","user_id":"user001"}'
```

### 3. 음성 건강 분석 ⭐ (권장)
```bash
curl -F "audio_file=@symptom.wav" \
  "http://localhost:8000/api/voice/health-analyze?user_id=user001"
```

---

## 🔧 문제 해결

### ❌ "GOOGLE_APPLICATION_CREDENTIALS not found"
```bash
# 확인 1: 파일 존재 여부
ls -la google-cloud-key.json

# 확인 2: 환경 변수 설정
echo $GOOGLE_APPLICATION_CREDENTIALS

# 설정:
export GOOGLE_APPLICATION_CREDENTIALS="./google-cloud-key.json"
python backend_main.py
```

### ❌ "Permission denied" (마이크 권한)
- Flutter 앱 시작 시 권한 요청 팝업 → **Allow** 클릭
- 또는 시스템 설정에서 브라우저 마이크 허용

### ❌ "Audio file is empty"
- 충분히 길게 음성 녹음 (최소 2-3초)
- 마이크가 제대로 작동하는지 확인

### ❌ "Confidence too low"
- 조용한 환경에서 다시 녹음
- 마이크를 입 가까이 두기
- 천천히, 명확하게 말하기

---

## ⚡ 성능 팁

| 최적화 | 방법 |
|------|------|
| 빠른 인식 | 짧은 문장으로 나누기 |
| 정확성 향상 | 조용한 환경, 명확한 발음 |
| 네트워크 | 안정적인 인터넷 연결 |
| 메모리 | 장시간 녹음 피하기 (1-2분 권장) |

---

## 📊 지원되는 것들

### 언어
- ✅ 한국어 (ko-KR) - 기본
- ✅ 영어 (en-US)
- ✅ 일본어 (ja-JP)
- ✅ 중국어 (zh-CN)

### 오디오 형식
- ✅ WAV (16kHz, 16-bit, Mono)
- ✅ MP3
- ✅ M4A

### 플랫폼
- ✅ Chrome Web Browser
- ✅ Android (설정 필요)
- ✅ iOS (설정 필요)

---

## 💡 사용 시나리오

### 고령 사용자 (권장 ⭐)
```
마이크 버튼 -> "다리가 좀 부어요" -> 음성 분석 -> 결과 청취
텍스트 입력 필요 없음 - 완전히 음성만으로 사용 가능
```

### 바쁜 상황
```
음성으로 빠르게 입력 (텍스트보다 3배 빠름)
운전 중, 요리 중에도 안전하게 사용 가능
```

### 청각장애자
```
음성 입력 사용 불가
텍스트 입력 + 음성 응답 청취 (자막 포함)
```

---

## 🎨 UI 구조

```
┌─ PHARMA-MOBILE ─────────────────┐
│                                 │
│ [사용자명 입력] [증상 입력]      │
│                                 │
│ [등록] [텍스트분석] [복약기록]   │
│                                 │
│ 🎤 음성 기반 분석               │
│ [🎤 음성녹음] [📤 음성분석]    │
│ 녹음시간: 0:05                  │
│                                 │
│ [분석 결과 표시 영역]           │
│                                 │
└─────────────────────────────────┘
```

---

## 🔐 보안

- ✅ 마이크 권한 요청 (사용자 승인)
- ✅ HTTPS 전송 (배포 시)
- ✅ 음성 데이터 암호화 (Google Cloud)
- ✅ PII 마스킹 (기존 privacy_guard.py 사용)

---

## 💰 비용

### 무료 할당량
- **STT**: 월 60분
- **TTS**: 월 100만 자

### 추가 비용
- **STT**: $0.006 / 15초
- **TTS**: $0.000016 / 자 (신경망)

### 예상 월 비용 (10명 사용)
```
10명 × 10분/일 = 100분/일
100분 × 30일 = 3,000분/월
3,000분 - 60분 (무료) = 2,940분
2,940분 ÷ 15초 = 11,760 요청
11,760 × $0.006 = ~$70/월

TTS: 100만 자 무료이므로 추가 비용 없음

총 예상: ~$70-100/월
```

---

## 📞 도움말

### Swagger UI (API 테스트)
```
http://localhost:8000/docs
```

### 상세 가이드
- [VOICE_FEATURES_GUIDE.md](./VOICE_FEATURES_GUIDE.md) - 완전 가이드
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 상세 보고서

### 로그 확인
```bash
tail -f pharma_backend.log
```

---

## ✨ 주요 개선점

기존 (텍스트만):
```
사용자 -> 텍스트 입력 -> API -> 분석 결과 표시
```

개선됨 (음성 추가):
```
사용자 -> 음성 녹음 -> STT -> AI 분석 -> TTS -> 음성 응답
         (완전 자동화)          (6-10초)
```

---

## 🎯 다음 단계

### 즉시 할 일
1. Google Cloud 계정 생성
2. google-cloud-key.json 받기
3. 환경 변수 설정
4. 음성 기능 테스트

### 며칠 후
- 모든 사용자에게 음성 기능 활성화
- 피드백 수집
- 성능 모니터링

### 향후 개선
- 약물 음성 명령어
- 감정 분석
- 배경음 제거
- 다국어 확대

---

## 🎉 축하합니다!

이제 **음성 기능**이 완전히 구현되었습니다!

👨‍💼 **관리자 (개발자)**
- API 엔드포인트 테스트 가능
- Swagger UI에서 음성 기능 테스트
- 성능 모니터링 시작

👨‍⚕️ **의료 전문가**
- 환자의 음성 입력으로 더 정확한 정보 수집
- 자동 분석 결과 검토
- 음성 피드백으로 환자 교육

👴 **고령 환자**
- 텍스트 입력 없이 음성으로 증상 전달
- 의료 분석 결과를 음성으로 청취
- 더 편한 의료 정보 접근

---

**Happy Voice! 🎤**

시작하려면: `python backend_main.py`
