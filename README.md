# 🏥 PHARMA-MOBILE - 의료 처방전 분석 시스템

**상태**: ✅ **배포 준비 완료**  
**버전**: v1.0.0  
**최종 업데이트**: 2026-05-09

---

## 📋 개요

**PHARMA-MOBILE**은 의료 처방전을 분석하고 약물 정보를 제공하는 통합 시스템입니다.

- 🎤 **음성 입력/출력** - Google Cloud STT/TTS 통합
- 💊 **약물 정보 분석** - 용량, 횟수, 부작용 조회
- 📱 **모바일 앱** - Flutter 크로스플랫폼
- ⚡ **FastAPI 백엔드** - 13개 API 엔드포인트
- 🔐 **보안** - Google Cloud 자격증명 보호

---

## 🚀 5분 배포 가이드

### 전제 조건
- ✅ Render 계정 (가입 완료)
- ✅ GitHub 연동 (완료)
- ✅ Google Cloud 자격증명 파일

### 배포 단계

**1단계**: Render 대시보드 열기
```
https://dashboard.render.com
```

**2단계**: Web Service 생성
```
New → Web Service → med_project 선택
```

**3단계**: 설정 입력
```
Name: pharma-mobile-backend
Region: Singapore
Branch: main
Build Command: pip install -r requirements_backend.txt
Start Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT
```

**4단계**: 환경 변수 설정
```
PYTHON_VERSION = 3.11
ENVIRONMENT = production
GOOGLE_CLOUD_CREDENTIALS_JSON = {Google Cloud JSON 전체}
```

**5단계**: 배포 시작
```
Create Web Service 클릭 → 2-3분 대기 → "Live" 상태 확인
```

✨ **완료!**

---

## 📁 프로젝트 구조

```
med_project/
├── 📖 README.md ........................ 이 파일
├── 📖 QUICK_RENDER_DEPLOY.md ......... 5분 배포 가이드 ⭐
│
├── 🎯 백엔드
│   ├── backend_main.py ............... FastAPI 메인 앱 (13 API 엔드포인트)
│   ├── voice_handler.py .............. 음성 처리 (STT/TTS)
│   ├── pharma_mobile.db .............. SQLite 데이터베이스
│   └── requirements_backend.txt ...... Python 의존성
│
├── ⚙️ 배포 설정
│   ├── Procfile ....................... 실행 명령
│   ├── render.yaml .................... 자동 배포 설정
│   └── .gitignore ..................... 보안 (자격증명 제외)
│
├── 📱 모바일 앱 (Flutter)
│   ├── pharma_mobile/
│   │   ├── lib/main.dart ............ UI & 로직
│   │   ├── pubspec.yaml ............ 의존성
│   │   └── ...
│
└── 📚 문서
    ├── QUICK_RENDER_DEPLOY.md ....... ⭐ 5분 배포 가이드
    ├── DEPLOYMENT_READY.md ......... 배포 체크리스트
    ├── RENDER_DEPLOYMENT_GUIDE.md .. 상세 가이드
    ├── VOICE_FEATURES_GUIDE.md ..... 음성 기능 설명
    └── IMPLEMENTATION_SUMMARY.md ... 구현 완료 보고
```

---

## 🎯 주요 기능

| 기능 | API 엔드포인트 | 상태 |
|------|---------------|------|
| **사용자 관리** | `/api/user/*` | ✅ |
| **건강 분석** | `/api/health/analyze` | ✅ |
| **약물 스케줄** | `/api/medication/*` | ✅ |
| **음성 인식** | `/api/voice/transcribe` | ✅ |
| **음성 생성** | `/api/voice/synthesize` | ✅ |
| **완전 음성 워크플로우** | `/api/voice/health-analyze` | ✅ |
| **헬스 체크** | `/health` | ✅ |

---

## 📊 API 엔드포인트 (13개)

```
인증 & 사용자
  POST   /api/user/register ........... 사용자 등록
  GET    /api/user/{user_id} ......... 사용자 정보 조회

건강 정보
  POST   /api/health/analyze ......... 건강 정보 분석
  GET    /api/statistics/{user_id} .. 통계 조회

약물 관리
  POST   /api/medication/schedule .... 약물 스케줄 설정
  POST   /api/medication/log ......... 약물 복용 기록
  GET    /api/medication/adherence/* . 복용 준수율 조회

알림
  GET    /api/reminders/{user_id} ... 약물 알림 조회

음성 처리
  POST   /api/voice/transcribe ....... 음성 → 텍스트 (STT)
  POST   /api/voice/synthesize ....... 텍스트 → 음성 (TTS)
  POST   /api/voice/health-analyze ... 완전 음성 워크플로우

시스템
  GET    /health ..................... 헬스 체크
```

---

## 🔧 기술 스택

| 계층 | 기술 |
|------|------|
| **백엔드** | FastAPI, Uvicorn, Gunicorn |
| **데이터베이스** | SQLite (개발), PostgreSQL (프로덕션) |
| **음성** | Google Cloud Speech-to-Text, Text-to-Speech |
| **모바일** | Flutter, Dart |
| **배포** | Render, GitHub Actions |
| **보안** | Google Cloud Service Account |

---

## 💾 설치 및 실행

### 백엔드 (로컬)
```bash
# 의존성 설치
pip install -r requirements_backend.txt

# 서버 시작
python backend_main.py

# Swagger UI 접속
http://localhost:8000/docs
```

### 모바일 앱 (Flutter)
```bash
# 의존성 설치
flutter pub get

# 앱 실행
flutter run

# 백엔드 URL 설정 (main.dart)
const String backendUrl = 'http://localhost:8000';
```

---

## 🌐 배포 (Render)

### 배포된 URL
```
API: https://pharma-mobile-backend-{random}.onrender.com
Swagger UI: https://pharma-mobile-backend-{random}.onrender.com/docs
```

### 배포 상태 확인
```bash
curl https://pharma-mobile-backend-{random}.onrender.com/health
```

---

## 🔐 보안 설정

### Google Cloud 자격증명
```
⚠️ 절대 GitHub에 커밋하지 마세요!
✅ .gitignore에 google-cloud-key.json* 포함됨
✅ Render 환경 변수로만 관리
```

### 환경 파일
```
.env (로컬 개발용)
.env.local (개인 설정)
```

---

## 📝 주요 문서

| 문서 | 용도 |
|------|------|
| **QUICK_RENDER_DEPLOY.md** | ⭐ 5분 배포 가이드 (이것부터 읽기) |
| **DEPLOYMENT_READY.md** | 배포 체크리스트 및 준비 상태 |
| **RENDER_DEPLOYMENT_GUIDE.md** | 상세 배포 가이드 + 트러블슈팅 |
| **VOICE_FEATURES_GUIDE.md** | 음성 기능 상세 설명 |
| **IMPLEMENTATION_SUMMARY.md** | 구현 완료 보고서 |

---

## 🐛 문제 해결

### 배포 실패
```
→ RENDER_DEPLOYMENT_GUIDE.md의 "트러블슈팅" 섹션 참고
→ Render 대시보드의 "Logs" 에서 에러 메시지 확인
```

### Google Cloud 인증 오류
```
→ GOOGLE_CLOUD_CREDENTIALS_JSON 환경 변수 확인
→ JSON 파일이 완전히 복사되었는지 확인
→ JSON 형식 검증 ({ 로 시작, } 로 끝남)
```

### 음성 기능 작동 안 함
```
→ Google Cloud 프로젝트에서 STT/TTS API 활성화 확인
→ 서비스 계정 권한 확인
→ 자격증명 파일 유효성 확인
```

---

## 📞 지원

### 로그 확인
```bash
# 로컬 실행 중
python backend_main.py  # 콘솔 로그 확인

# Render 배포 중
Render 대시보드 → Logs → 실시간 로그 확인
```

### API 테스트
```
Swagger UI: /docs
ReDoc: /redoc
```

---

## 📈 성능 및 확장성

### 로컬 개발
- SQLite 사용
- 최대 동시 사용자: 1-10명
- 응답 시간: < 200ms

### Render 프로덕션
- SQLite (기본), PostgreSQL (권장)
- 최대 동시 사용자: 100+ (Starter)
- 응답 시간: < 500ms

### 향후 업그레이드
```
Starter → Standard → Pro
└─ CPU 증가
└─ 메모리 증가
└─ PostgreSQL 추가
└─ 캐싱 설정
```

---

## ✅ 체크리스트

### 배포 전
- [ ] GitHub에서 모든 파일 확인
- [ ] Google Cloud 자격증명 파일 준비
- [ ] Render 계정 생성
- [ ] QUICK_RENDER_DEPLOY.md 읽음

### 배포 중
- [ ] Web Service 생성
- [ ] 환경 변수 설정
- [ ] 배포 시작
- [ ] "Live" 상태 확인

### 배포 후
- [ ] `/health` 엔드포인트 테스트
- [ ] Swagger UI 접속
- [ ] Flutter 앱 백엔드 URL 업데이트
- [ ] 모든 기능 테스트

---

## 🎯 다음 단계

1. **배포**: `QUICK_RENDER_DEPLOY.md` 따라 Render 배포
2. **앱 연결**: `main.dart`의 백엔드 URL 변경
3. **테스트**: 모든 API 엔드포인트 테스트
4. **모니터링**: Render 대시보드에서 실시간 확인

---

## 📄 라이선스

MIT License

---

## 👨‍💻 개발자 정보

- **프로젝트**: PHARMA-MOBILE v1.0.0
- **상태**: Production Ready
- **최종 업데이트**: 2026-05-09

---

**🚀 배포 준비 완료! 위의 배포 가이드를 따라 진행하세요.**

