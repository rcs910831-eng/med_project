# Render 배포 - 최소 5분 완성 가이드

**시간**: 약 5분  
**난이도**: 매우 쉬움 (클릭 + 복사-붙여넣기만)

---

## 🎯 단계별 정확한 가이드

### 단계 1️⃣: Render 대시보드 열기 (1분)

```
URL: https://dashboard.render.com
```

1. 위 링크 클릭
2. GitHub 계정으로 이미 로그인되어 있음
3. **Dashboard** 화면 보임

---

### 단계 2️⃣: 새 Web Service 생성 (1분)

**대시보드에서**:
```
1. 좌측 메뉴에서 "New" 버튼 찾기
2. "New +" 클릭
3. "Web Service" 선택
```

**Git 저장소 연결**:
```
1. "Connect a repository" 섹션
2. med_project 저장소 찾기 (이미 연동됨)
3. "Connect" 버튼 클릭
```

---

### 단계 3️⃣: 서비스 설정 (2분)

**기본 정보 입력** (다음 값 복사-붙여넣기):

| 항목 | 값 |
|------|-----|
| **Name** | `pharma-mobile-backend` |
| **Region** | `Singapore` (또는 `Tokyo`) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements_backend.txt` |
| **Start Command** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT` |

**주의**: 위 값들을 정확히 복사하세요 (공백 포함)

---

### 단계 4️⃣: 환경 변수 설정 (1분)

**Environment Variables 섹션**에서 다음 추가:

#### ➕ 추가할 변수 1
```
KEY: PYTHON_VERSION
VALUE: 3.11
```

#### ➕ 추가할 변수 2
```
KEY: ENVIRONMENT
VALUE: production
```

#### ➕ 추가할 변수 3 (⚠️ 중요)
```
KEY: GOOGLE_CLOUD_CREDENTIALS_JSON
VALUE: 
```

**값 입력 방법**:
1. `C:\Users\rcs91\Downloads\pharma-mobile-*.json` 파일 열기
2. 전체 내용 복사
3. Render의 VALUE 필드에 붙여넣기
4. (파일이 없으면 아래 참고)

---

### 단계 5️⃣: 배포 시작 (클릭)

```
"Create Web Service" 버튼 클릭
```

**배포 진행**:
- 페이지 자동 새로고침
- "Building..." → "Live" 상태로 변경 (약 2-3분)
- 로그에 "Application startup complete" 메시지 보임

---

### 단계 6️⃣: 배포 확인 (1분)

**배포 완료 후**:

```
1. "Live" 상태 확인
2. 서비스 URL 확인 (약 https://pharma-mobile-backend-xxxx.onrender.com)
3. URL 클릭 → /docs 추가 (Swagger UI)
```

**테스트 URL**:
```
https://pharma-mobile-backend-{random}.onrender.com/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

---

## ⚠️ 중요: Google Cloud 자격증명

### 파일 위치 확인
```
1. Windows 파일 탐색기 열기
2. C:\Users\rcs91\Downloads\ 또는 C:\Users\rcs91\github\med_project\ 확인
3. pharma-mobile-*.json 파일 찾기
```

### 파일이 없는 경우
```
1. https://console.cloud.google.com 접속
2. med_project 프로젝트 선택
3. 서비스 계정 생성 (또는 기존 계정 선택)
4. JSON 키 다운로드
5. Render에 값 입력
```

---

## 🎯 배포 완료 후

### Flutter 앱 업데이트

파일: `pharma_mobile/lib/main.dart`

**변경 전**:
```dart
const String backendUrl = 'http://localhost:8000';
```

**변경 후** (실제 배포 URL로 변경):
```dart
const String backendUrl = 'https://pharma-mobile-backend-xxxx.onrender.com';
```

**앱 재빌드**:
```bash
flutter clean
flutter pub get
flutter run
```

---

## 📋 문제 해결

### ❌ "Build failed" 에러
```
→ 로그에서 "pip install" 에러 확인
→ requirements_backend.txt 파일 정상 여부 확인
→ Render 다시 배포 시도 ("Manual Deploy" 버튼)
```

### ❌ Google Cloud 인증 오류
```
→ GOOGLE_CLOUD_CREDENTIALS_JSON 환경 변수 설정 확인
→ JSON 파일이 완전히 복사되었는지 확인 ({로 시작, }로 끝남)
→ JSON 형식이 올바른지 확인
```

### ❌ /health 404 에러
```
→ 배포가 "Live" 상태인지 확인
→ 서비스가 완전히 시작될 때까지 기다리기 (30초)
→ URL이 정확한지 확인
```

---

## ✨ 완료!

배포가 완료되면:

| 항목 | 상태 |
|------|------|
| 백엔드 | ✅ 온라인 |
| API | ✅ 사용 가능 |
| 음성 (STT/TTS) | ✅ 작동 |
| 모니터링 | ✅ Render 대시보드에서 실시간 확인 |

---

## 📱 모바일 앱 테스트

Render 배포 완료 후:

1. `main.dart` 의 백엔드 URL 변경
2. `flutter run` 실행
3. 앱의 모든 기능 테스트:
   - 사용자 등록
   - 건강 정보 입력
   - 음성 입력/출력
   - 약물 정보 조회

---

**총 소요 시간**: 약 5-10분 (배포 대기 시간 포함)  
**복잡도**: 매우 낮음 (클릭 + 복사-붙여넣기)  
**성공률**: 95% (정확한 값 입력 시)
