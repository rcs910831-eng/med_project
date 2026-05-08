# Render 배포 가이드 (PHARMA-MOBILE Backend)

## 📋 목차
1. [배포 전 준비](#배포-전-준비)
2. [Render 계정 및 프로젝트 생성](#render-계정-및-프로젝트-생성)
3. [단계별 배포](#단계별-배포)
4. [환경 변수 설정](#환경-변수-설정)
5. [배포 후 검증](#배포-후-검증)
6. [트러블슈팅](#트러블슈팅)

---

## 배포 전 준비

### ✅ 확인 사항
- [ ] GitHub 계정에 로그인
- [ ] Google Cloud 서비스 계정 JSON 파일 준비 (google-cloud-key.json)
- [ ] 로컬 테스트 완료 (모든 API 엔드포인트 정상 작동 확인)

### 📦 파일 구성 확인
```
med_project/
├── backend_main.py          # FastAPI 메인 앱
├── requirements_backend.txt # Python 의존성
├── Procfile                 # 실행 설정
├── render.yaml              # Render 설정 (선택사항)
├── .gitignore               # Git 무시 파일
├── google-cloud-key.json    # ⚠️ 로컬에만 있어야 함 (git 제외됨)
└── pharma_mobile.db         # SQLite 데이터베이스
```

---

## Render 계정 및 프로젝트 생성

### 1️⃣ Render 가입
1. https://render.com 접속
2. **Sign Up** 클릭
3. GitHub 계정으로 로그인 (권장)
4. 이메일 확인

### 2️⃣ GitHub 연동
1. Render 대시보드의 **Dashboard** 메뉴 선택
2. **GitHub** 탭 에서 "Connect GitHub"
3. med_project 저장소 선택 및 권한 부여

---

## 단계별 배포

### 단계 1: 새 웹 서비스 생성

1. Render 대시보드에서 **+ New** → **Web Service**
2. GitHub 저장소 선택: `med_project`
3. 다음 정보 입력:

| 항목 | 값 |
|------|-----|
| **Name** | pharma-mobile-backend |
| **Region** | Singapore (또는 Tokyo) |
| **Branch** | main |
| **Runtime** | Python 3.11 |
| **Build Command** | `pip install -r requirements_backend.txt` |
| **Start Command** | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT` |

### 단계 2: 환경 변수 설정

**Advanced** 섹션에서 환경 변수 추가:

| 키 | 값 | 설명 |
|-----|-----|------|
| `PYTHON_VERSION` | `3.11` | Python 버전 |
| `ENVIRONMENT` | `production` | 실행 환경 |
| `LOG_LEVEL` | `info` | 로그 레벨 |
| `DATABASE_PATH` | `/var/run/user/pharma_mobile.db` | SQLite DB 경로 |

### 단계 3: Google Cloud 자격증명 설정

⚠️ **중요: 자격증명 파일을 GitHub에 커밋하지 마세요!**

#### 옵션 A: Render 환경 변수 사용 (권장)
1. Google Cloud 서비스 계정 JSON 파일 열기
2. 전체 내용 복사
3. Render 대시보드에서 환경 변수 추가:
   - **키**: `GOOGLE_CLOUD_CREDENTIALS_JSON`
   - **값**: JSON 파일의 전체 내용 (붙여넣기)

4. `backend_main.py` 시작 부분에 추가:
```python
import json
import os

# Google Cloud 자격증명 설정
if os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON'):
    creds_json = json.loads(os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON'))
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/google-cloud-key.json'
    with open('/tmp/google-cloud-key.json', 'w') as f:
        json.dump(creds_json, f)
```

#### 옵션 B: Render Disk 사용
1. Render 대시보드에서 **Disks** 추가
2. 파일명: `pharma-db` (또는 원하는 이름)
3. 마운트 경로: `/var/data`
4. SSH로 접속하여 `google-cloud-key.json` 파일 업로드

### 단계 4: Disk 설정 (옵션)

SQLite 데이터베이스를 지속성 있게 저장:

1. Render 대시보드 → **Create Disk**
   - **Name**: `pharma-db`
   - **Mount Path**: `/var/data`
   - **Size**: 1 GB (또는 필요에 따라)

2. 시작 명령어 수정:
```
DATABASE_PATH=/var/data/pharma_mobile.db gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT
```

### 단계 5: 배포 시작

1. 모든 설정 확인
2. **Create Web Service** 클릭
3. 배포 진행 상황 관찰 (로그 보기)

---

## 환경 변수 설정

### Render 대시보드에서 설정

1. 배포된 서비스 선택
2. **Environment** 탭
3. 각 변수 추가:

```
PYTHON_VERSION=3.11
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_PATH=/var/run/user/pharma_mobile.db
GOOGLE_CLOUD_CREDENTIALS_JSON={json_content}
```

### 로컬 .env 파일 (개발용만)
`.env.local` 생성 (Git에서 제외됨):
```
ENVIRONMENT=development
LOG_LEVEL=debug
DATABASE_PATH=./pharma_mobile.db
GOOGLE_APPLICATION_CREDENTIALS=./google-cloud-key.json
```

---

## 배포 후 검증

### 1️⃣ 배포 상태 확인
```bash
# Render 대시보드에서:
# - Status: "Live" 상태인지 확인
# - 배포 로그에서 에러 확인
```

### 2️⃣ API 엔드포인트 테스트

배포 후 URL 형식: `https://pharma-mobile-backend.onrender.com`

#### 헬스 체크
```bash
curl https://pharma-mobile-backend.onrender.com/api/health
```

예상 응답:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-05-09T12:00:00.000000",
  "version": "1.0.0"
}
```

#### 모든 API 엔드포인트 테스트
```bash
# Swagger UI 접속
https://pharma-mobile-backend.onrender.com/docs

# 또는 재테스트 (테스트 요청)
curl -X POST https://pharma-mobile-backend.onrender.com/api/health/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "content": "혈압약 복용중입니다"}'
```

### 3️⃣ Flutter 앱 연결

Flutter 앱의 `main.dart`에서 백엔드 URL 업데이트:

```dart
// 변경 전
const String backendUrl = 'http://localhost:8000';

// 변경 후
const String backendUrl = 'https://pharma-mobile-backend.onrender.com';
```

앱 재빌드:
```bash
flutter clean
flutter pub get
flutter run
```

---

## 트러블슈팅

### ❌ "Build Failed" 에러

**원인**: 의존성 설치 실패

**해결책**:
1. `requirements_backend.txt` 확인
2. 불필요한 패키지 제거
3. 버전 호환성 확인

```bash
# 로컬에서 테스트
pip install -r requirements_backend.txt
```

### ❌ "Port 8000 already in use" 에러

**원인**: 포트 설정 오류

**해결책**:
- Render는 자동으로 포트 할당 (`$PORT` 환경 변수)
- 시작 명령어에 `--bind 0.0.0.0:$PORT` 포함 확인

### ❌ "Google Cloud credentials not found"

**원인**: 자격증명 파일 설정 누락

**해결책**:
1. Render 대시보드 → **Environment** 확인
2. `GOOGLE_CLOUD_CREDENTIALS_JSON` 환경 변수 설정 확인
3. JSON 형식이 올바른지 확인 (`{` 로 시작, `}` 로 끝남)

### ❌ "Database connection failed"

**원인**: 데이터베이스 경로 오류

**해결책**:
- SQLite 파일이 읽기/쓰기 가능한 디렉토리 사용
- Render Disk 마운트 경로 확인
- 로그에서 경로 확인

### ❌ 느린 응답 속도

**해결책**:
- 워커 프로세스 수 조정:
```
gunicorn -w 8 -k uvicorn.workers.UvicornWorker ...  # 기본값 4
```
- Render 플랜 업그레이드 (Standard 이상)

---

## 🚀 배포 완료!

### 다음 단계:
1. Flutter 앱 업데이트 (백엔드 URL 변경)
2. 모든 기능 E2E 테스트
3. 모니터링 설정 (Sentry 통합)
4. 자동 재배포 설정 (GitHub 연동)

### 배포된 서비스 URL:
```
https://pharma-mobile-backend.onrender.com
```

### 모니터링:
- Render 대시보드에서 실시간 로그 확인
- 오류 발생 시 즉시 알림 설정 가능

---

## 📚 참고 자료

- [Render 공식 가이드](https://render.com/docs)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn 문서](https://gunicorn.org/)
- [Google Cloud Python 클라이언트](https://googleapis.dev/python/google-cloud-speech/latest/)

---

## 문제 발생 시

1. Render 대시보드에서 **Logs** 확인
2. 로컬에서 `python backend_main.py` 실행하여 동일한 에러 재현
3. GitHub Issues에 문제 보고 (로그 포함)

---

**배포 완료일**: 2026-05-09
**상태**: ✅ 준비 완료
