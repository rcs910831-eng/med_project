# [>>] PHARMA-MOBILE Render 배포 - 즉시 실행 가이드

## 상태: 배포 준비 완료 100%

모든 설정값이 준비되었습니다. 아래 단계를 따라 3분 안에 배포를 완료할 수 있습니다.

---

## Step 1: Render 대시보드 접속 (30초)

```
URL: https://dashboard.render.com
```

**할 일**:
1. 브라우저에서 위 URL 열기
2. GitHub 로그인 (이미 연동됨)
3. 대시보드 화면 확인

---

## Step 2: Web Service 생성 (1분)

**메뉴 경로**: New → Web Service

**저장소 선택**: med_project

[확인]: med_project 저장소가 보이면 선택

---

## Step 3: 배포 설정 입력 (2분)

### 기본 설정

| 항목 | 값 | 확인 |
|------|-----|------|
| **Name** | `pharma-mobile-backend` | 정확히 입력 |
| **Region** | `Singapore` | 드롭다운에서 선택 |
| **Branch** | `main` | 자동 감지 |

### Build & Start Commands

**Build Command** (따옴표 제외하고 입력):
```
pip install -r requirements_backend.txt
```

**Start Command** (따옴표 제외하고 입력):
```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT
```

---

## Step 4: 환경 변수 설정 (가장 중요)

### 환경 변수 1
```
KEY: PYTHON_VERSION
VALUE: 3.11
```

### 환경 변수 2
```
KEY: ENVIRONMENT
VALUE: production
```

### 환경 변수 3 (Google Cloud 자격증명 - 복사 준비됨)

```
KEY: GOOGLE_CLOUD_CREDENTIALS_JSON
VALUE: 아래의 JSON 전체 내용 복사
```

**JSON 파일 위치**:
```
C:\Users\rcs91\Downloads\pharma-mobile-495713-157aab5a9c77.json
```

**복사 방법**:
1. 위 파일을 메모장으로 열기
2. Ctrl+A (전체 선택)
3. Ctrl+C (복사)
4. Render의 VALUE 필드에 클릭
5. Ctrl+V (붙여넣기)

**검증**:
- VALUE가 `{` 문자로 시작하는가?
- VALUE가 `}` 문자로 끝나는가?
- 길이가 충분한가? (약 2KB)

---

## Step 5: 배포 시작 (클릭)

"Create Web Service" 버튼 클릭

### 배포 진행 상황

```
상태: Building... (약 2-3분)
     ↓
상태: Live (배포 완료!)
```

---

## Step 6: 배포 URL 확인 (1분)

배포 완료 후 화면에 표시되는 URL:

```
https://pharma-mobile-backend-{random}.onrender.com
```

**이 URL을 메모해두세요!** (다음 단계에서 필요)

---

## Step 7: 배포 검증 (자동)

배포 URL이 보이면 아래 명령어 실행:

```bash
python validate_deployment.py https://pharma-mobile-backend-{배포URL}.onrender.com
```

**예시**:
```bash
python validate_deployment.py https://pharma-mobile-backend-abc123.onrender.com
```

### 검증 항목
- [OK] Health Check
- [OK] API Endpoints
- [OK] Swagger UI
- [OK] Database
- [OK] Voice Features
- [OK] Performance

**결과**: 모두 통과 시 배포 성공!

---

## ✨ 배포 완료 후

### URL 복사
```
https://pharma-mobile-backend-{생성된_ID}.onrender.com
```

### 헬스 체크 (브라우저)
```
https://pharma-mobile-backend-{ID}.onrender.com/health
```

예상 응답:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-09T...",
  "version": "1.0.0"
}
```

### Swagger UI (API 문서)
```
https://pharma-mobile-backend-{ID}.onrender.com/docs
```

---

## 📋 빠른 체크리스트

```
배포 전:
  [ ] Chrome 브라우저 열기
  [ ] https://dashboard.render.com 접속
  [ ] GitHub 로그인

배포 설정:
  [ ] Name: pharma-mobile-backend
  [ ] Region: Singapore
  [ ] Build Command 복사
  [ ] Start Command 복사
  [ ] 환경변수 3개 입력

환경변수 중요!!:
  [ ] PYTHON_VERSION = 3.11
  [ ] ENVIRONMENT = production
  [ ] GOOGLE_CLOUD_CREDENTIALS_JSON = [JSON 전체]

배포:
  [ ] "Create Web Service" 클릭
  [ ] 2-3분 대기
  [ ] "Live" 상태 확인

검증:
  [ ] 배포 URL 복사
  [ ] python validate_deployment.py <URL> 실행
  [ ] 모든 테스트 통과 확인
```

---

## 🎯 이 가이드의 설정값이 정확한 이유

✅ auto_deploy.py에서 자동으로 검증됨
✅ 모든 파일 존재 확인됨
✅ Google Cloud 자격증명 유효성 검증됨
✅ JSON 형식 검증됨

---

## ⚠️ 주의사항

1. **Google Cloud JSON**: 전체 내용을 정확히 복사해야 합니다
2. **Start Command**: 매우 길므로 정확히 입력하세요
3. **환경변수 3개**: 모두 입력되어야 합니다 (하나라도 빠지면 실패)

---

**준비 완료! 위 단계를 따라 배포하세요.**

배포 완료 후 URL을 알려주시면, 검증 스크립트를 자동으로 실행하겠습니다.
