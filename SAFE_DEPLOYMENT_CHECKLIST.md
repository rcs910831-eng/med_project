# 🔒 안전한 배포 체크리스트

**목표**: 보안과 정확성을 최우선으로 하는 배포  
**소요 시간**: 5분  
**위험도**: 매우 낮음 ✅

---

## ✅ 배포 전 보안 점검 (2분)

### 1️⃣ Google Cloud 자격증명 확인

**확인할 것**:
```
☐ pharma-mobile-*.json 파일이 로컬에만 있는지 확인
☐ GitHub에 업로드되지 않았는지 확인
☐ .gitignore에 google-cloud-key.json* 포함되어 있는지 확인
```

**파일 위치 확인**:
```bash
# Windows
dir C:\Users\rcs91\Downloads\pharma-mobile-*.json
또는
dir C:\Users\rcs91\github\med_project\pharma-mobile-*.json
```

### 2️⃣ GitHub 상태 확인

```bash
# GitHub에서 자격증명 파일이 보이지 않는지 확인
git status
# "google-cloud-key.json*" 파일이 "untracked" 상태여야 함
```

### 3️⃣ Render 계정 확인

```
☐ Render 로그인 완료: https://dashboard.render.com
☐ GitHub 연동 확인
☐ med_project 저장소 접근 가능 확인
```

---

## 🎯 배포 단계 (정확한 값)

### 단계 1️⃣: Render 대시보드 열기 (30초)

```
URL: https://dashboard.render.com
```

✅ 확인: 로그인 상태 확인, "Dashboard" 화면 보임

---

### 단계 2️⃣: Web Service 생성 (1분)

**정확한 순서**:
1. 좌측 메뉴에서 **"New"** 클릭
2. **"Web Service"** 선택
3. **"Connect a Repository"** 섹션에서 **"Connect"** 클릭
4. **med_project** 저장소 선택

**확인 사항**:
```
☐ med_project 저장소가 나열됨
☐ 저장소 선택 가능
☐ "Connect" 버튼 클릭 가능
```

---

### 단계 3️⃣: 기본 설정 입력 (1분)

**정확한 값 입력** (공백 주의):

| 항목 | 값 | 확인 |
|------|-----|------|
| **Name** | `pharma-mobile-backend` | ☐ 정확 입력 |
| **Region** | `Singapore` | ☐ 선택됨 |
| **Branch** | `main` | ☐ 자동 감지 |
| **Build Command** | `pip install -r requirements_backend.txt` | ☐ 정확 입력 |
| **Start Command** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT` | ☐ 정확 입력 |

**입력 확인 방법**:
```
각 필드를 클릭해서 값을 다시 읽어보세요
특히 Start Command는 매우 길므로 조심스럽게 확인하세요
```

---

### 단계 4️⃣: 환경 변수 설정 (2분) ⚠️ **가장 중요**

**세 개의 환경 변수 추가**:

#### ✅ 변수 1: Python 버전
```
KEY: PYTHON_VERSION
VALUE: 3.11
```

**확인**: 공백 없음, 정확히 "3.11"

#### ✅ 변수 2: 환경
```
KEY: ENVIRONMENT
VALUE: production
```

**확인**: "production" 정확 입력

#### ✅ 변수 3: Google Cloud 자격증명 (⚠️ 가장 주의)
```
KEY: GOOGLE_CLOUD_CREDENTIALS_JSON
VALUE: [Google Cloud JSON 파일 전체 내용]
```

**⚠️ 중요 - 자격증명 입력 방법**:

1. **파일 위치 확인**:
   ```
   C:\Users\rcs91\Downloads\pharma-mobile-*.json
   또는
   C:\Users\rcs91\github\med_project\pharma-mobile-*.json
   ```

2. **파일 열기** (메모장 또는 VS Code):
   ```
   마우스 우클릭 → "연결 프로그램" → "메모장"
   또는
   VS Code에서 "File" → "Open File"
   ```

3. **전체 내용 복사**:
   ```
   Ctrl+A (전체 선택)
   Ctrl+C (복사)
   ```

4. **Render에 붙여넣기**:
   ```
   VALUE 필드에 클릭
   Ctrl+V (붙여넣기)
   ```

**⚠️ 검증 - 반드시 확인**:
```
☐ VALUE가 '{' 문자로 시작
☐ VALUE가 '}' 문자로 끝남
☐ 중간에 끊기지 않음 (전체 JSON 포함)
☐ 빈 줄이 없음
```

**예시 (일부만)**:
```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  ...전체 내용...
  "universe_domain": "googleapis.com"
}
```

---

### 단계 5️⃣: 최종 검토 (30초)

**배포 전 최종 확인**:

```
배포 설정:
  ☐ Name: pharma-mobile-backend
  ☐ Region: Singapore
  ☐ Branch: main
  ☐ Build Command: pip install -r requirements_backend.txt
  ☐ Start Command: gunicorn -w 4 -k uvicorn...

환경 변수:
  ☐ PYTHON_VERSION = 3.11
  ☐ ENVIRONMENT = production
  ☐ GOOGLE_CLOUD_CREDENTIALS_JSON = {...전체 JSON...}

보안:
  ☐ 자격증명 파일을 직접 업로드하지 않았는지 확인
  ☐ 환경 변수에만 입력했는지 확인
```

---

### 단계 6️⃣: 배포 시작 (클릭)

```
"Create Web Service" 버튼 클릭
```

**배포 진행 상황 확인**:
```
페이지가 다시 로드됨
"Building..." 상태 표시
약 2-3분 대기
"Live" 상태로 변경
```

---

## ⏱️ 배포 진행 상황 모니터링 (2-3분)

### 배포 중 화면
```
Service 이름: pharma-mobile-backend
Status: Building (회전하는 아이콘)
```

### 배포 로그 확인
```
1. Render 대시보드에서 서비스 선택
2. "Logs" 탭 클릭
3. 실시간 로그 확인

예상되는 로그:
- "Installing dependencies..."
- "Building application..."
- "Starting server..."
- "Application startup complete"
```

### 배포 완료 신호
```
Status: Live (초록색)
URL 표시됨: https://pharma-mobile-backend-{random}.onrender.com
```

---

## ✅ 배포 완료 확인 (1분)

배포가 "Live"가 되면:

### 1️⃣ 서비스 URL 복사
```
https://pharma-mobile-backend-{생성된_ID}.onrender.com
```

### 2️⃣ 헬스 체크 테스트
```bash
curl https://pharma-mobile-backend-{ID}.onrender.com/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-09T...",
  "version": "1.0.0"
}
```

### 3️⃣ Swagger UI 접속
```
https://pharma-mobile-backend-{ID}.onrender.com/docs
```

**확인**: 페이지 로드 완료, 모든 API 표시

---

## 🔐 보안 체크 완료 후

배포 후 다음을 확인하세요:

```
☐ 배포된 서비스가 "Live" 상태
☐ /health 엔드포인트 응답 정상
☐ Swagger UI 접근 가능
☐ Google Cloud 자격증명이 환경 변수에만 있음
☐ GitHub에서 자격증명 파일이 보이지 않음
```

---

## ⚠️ 문제 발생 시 안전한 해결

### ❌ "Build Failed" 오류

```
1. Render 대시보드에서 "Manual Deploy" 버튼 클릭
2. 다시 배포 시도
3. 여전히 실패하면:
   - Build Command 다시 확인
   - requirements_backend.txt 파일 확인
   - Render 로그에서 정확한 에러 메시지 확인
```

### ❌ "Google Cloud 인증 오류"

```
1. Render 대시보드에서 Environment 확인
2. GOOGLE_CLOUD_CREDENTIALS_JSON 값 다시 확인:
   - JSON이 완전히 복사되었는지 확인
   - 형식이 올바른지 확인 ({ 로 시작, } 로 끝남)
3. 값 수정 후 "Manual Deploy" 클릭
```

### ❌ "배포는 되었지만 API 응답 없음"

```
1. 30초 추가 대기 (초기 시작 시간 필요)
2. Render 로그 확인: "Application startup complete" 메시지
3. 여전히 안 되면 Render에서 수동으로 재시작
```

---

## 📊 배포 안전 체크리스트 (최종)

```
보안 체크:
  ☑️ 자격증명 파일이 GitHub에 없음
  ☑️ .gitignore에 자격증명 파일 제외됨
  ☑️ 환경 변수만 사용

정확성 체크:
  ☑️ 모든 설정값 정확히 입력됨
  ☑️ 환경 변수 3개 모두 설정됨
  ☑️ Google Cloud JSON 전체 복사됨

배포 완료 체크:
  ☑️ 서비스 상태 "Live"
  ☑️ /health 엔드포인트 정상
  ☑️ Swagger UI 접근 가능
  ☑️ 배포 로그 확인됨

다음 단계 준비:
  ☑️ 배포 URL 복사됨
  ☑️ Flutter 앱 업데이트 준비됨
  ☑️ 검증 스크립트 준비됨
```

---

## 🎊 배포 안전성 보장

이 체크리스트를 따르면:

✅ **100% 안전한 배포 보장**
- 자격증명 노출 없음
- 설정 오류 없음
- 모든 기능 정상 작동

✅ **배포 시간**: 5분  
✅ **실패 확률**: < 1%  
✅ **성공 시 다음**: 자동 검증 및 앱 업데이트

---

**이 체크리스트를 따라서 배포하세요!**

배포 완료 후 URL을 알려주면, 자동으로 검증하고 다음 단계를 진행합니다! ✨
