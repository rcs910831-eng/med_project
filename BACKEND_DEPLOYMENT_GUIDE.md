# PHARMA-MOBILE FastAPI 백엔드 배포 가이드

## 📋 목차

1. [로컬 개발 환경](#로컬-개발-환경)
2. [Docker 배포](#docker-배포)
3. [Google Cloud Run 배포](#google-cloud-run-배포)
4. [API 테스트](#api-테스트)
5. [모니터링](#모니터링)

---

## 🚀 로컬 개발 환경

### 1. 환경 설정

```bash
# 저장소 클론 (이미 있으면 스킵)
cd C:\Users\rcs91\github\med_project

# 가상환경 생성
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements_backend.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY 등 실제 값 입력
```

### 2. 백엔드 실행

```bash
python backend_main.py
```

**출력 예시:**
```
╔════════════════════════════════════════════════════════════╗
║         🏥 PHARMA-MOBILE FastAPI Backend v1.0             ║
║                                                            ║
║  🚀 서버 시작 중...                                        ║
║  📍 http://localhost:8000                                 ║
║  📖 API 문서: http://localhost:8000/docs                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### 3. API 테스트 (Swagger 문서)

브라우저에서 접속:
```
http://localhost:8000/docs
```

**주요 엔드포인트:**
- ✅ `GET /health` - 서버 상태 확인
- ✅ `POST /api/user/register` - 사용자 등록
- ✅ `POST /api/health/analyze` - 건강 상태 분석
- ✅ `POST /api/medication/log` - 복약 기록
- ✅ `GET /api/medication/adherence/{user_id}` - 순응도 조회

---

## 🐳 Docker 배포

### 1. Docker 이미지 빌드

```bash
# 이미지 빌드
docker build -f Dockerfile_backend -t pharma-mobile-backend:latest .

# 확인
docker images | grep pharma
```

### 2. Docker 컨테이너 실행 (로컬)

```bash
# 환경 파일 준비
cp .env.example .env
# .env 파일 수정: GEMINI_API_KEY 등 설정

# 컨테이너 실행
docker run -d \
  --name pharma-backend \
  -p 8000:8000 \
  --env-file .env \
  -v pharma-data:/app/data \
  pharma-mobile-backend:latest

# 로그 확인
docker logs pharma-backend

# 정지
docker stop pharma-backend
```

### 3. Docker Compose (권장)

```bash
# docker-compose.yml 생성
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile_backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=sqlite:///pharma_mobile.db
      - API_PORT=8000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  pharma-data:
EOF

# 실행
docker-compose up -d

# 확인
docker-compose ps

# 로그 보기
docker-compose logs -f backend
```

---

## ☁️ Google Cloud Run 배포

### 1. Google Cloud 준비

```bash
# Google Cloud SDK 설치 (없으면)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# 프로젝트 설정
gcloud config set project pharma-mobile-project
gcloud auth configure-docker
```

### 2. 이미지 빌드 & 푸시

```bash
# 이미지 빌드
docker build -f Dockerfile_backend \
  -t gcr.io/pharma-mobile-project/backend:latest .

# Google Container Registry에 푸시
docker push gcr.io/pharma-mobile-project/backend:latest
```

### 3. Cloud Run 배포

```bash
gcloud run deploy pharma-backend \
  --image gcr.io/pharma-mobile-project/backend:latest \
  --platform managed \
  --region asia-northeast1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --max-instances 100
```

**출력:**
```
Service [pharma-backend] revision [pharma-backend-001] deployed

Service URL: https://pharma-backend-xxxxx.run.app
```

### 4. 환경 변수 설정 (Cloud Run)

```bash
gcloud run services update pharma-backend \
  --region asia-northeast1 \
  --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY}
```

---

## 🧪 API 테스트

### 1. curl로 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 사용자 등록
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "name": "김철수",
    "age": 68,
    "gender": "남",
    "medications": [
      {"name": "노바스크정 5mg", "dose": "1회 1정, 1일 1회"}
    ],
    "diagnoses": ["고혈압", "당뇨병"]
  }'

# 건강 상태 분석
curl -X POST http://localhost:8000/api/health/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "input_type": "text",
    "content": "다리가 좀 붓는 것 같아요"
  }'
```

### 2. Postman으로 테스트

```bash
# 컬렉션 생성
# 1. 각 엔드포인트를 Postman에서 직접 테스트
# 2. 또는 다음 JSON 임포트

{
  "info": {
    "name": "PHARMA-MOBILE API",
    "version": "1.0"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/health"
      }
    },
    {
      "name": "Register User",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/user/register",
        "body": {
          "mode": "raw",
          "raw": "..."
        }
      }
    }
  ]
}
```

### 3. Python 테스트 스크립트

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 사용자 등록
def register_user():
    data = {
        "user_id": "user001",
        "name": "김철수",
        "age": 68,
        "gender": "남",
        "medications": [
            {"name": "노바스크정 5mg", "dose": "1회 1정, 1일 1회"}
        ],
        "diagnoses": ["고혈압", "당뇨병"]
    }
    response = requests.post(f"{BASE_URL}/api/user/register", json=data)
    print(f"등록: {response.json()}")

# 건강 분석
def analyze_health():
    data = {
        "user_id": "user001",
        "input_type": "text",
        "content": "다리가 부어요"
    }
    response = requests.post(f"{BASE_URL}/api/health/analyze", json=data)
    print(f"분석: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 실행
if __name__ == "__main__":
    register_user()
    analyze_health()
```

---

## 📊 모니터링

### 1. 로그 확인

**로컬:**
```bash
tail -f logs/pharma_backend.log
```

**Docker:**
```bash
docker logs -f pharma-backend
```

**Cloud Run:**
```bash
gcloud run services logs read pharma-backend --region asia-northeast1 --limit 50
```

### 2. 성능 메트릭

**Cloud Run:**
```bash
gcloud monitoring timeseries list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="pharma-backend"'
```

### 3. 에러 추적

**Sentry 설정 (선택사항):**
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0
)
```

---

## 🔧 트러블슈팅

### 문제: GEMINI_API_KEY 오류

```
❌ Error: API key not configured
```

**해결:**
```bash
# .env 파일 확인
cat .env | grep GEMINI_API_KEY

# 또는 환경 변수 직접 설정
export GEMINI_API_KEY="your_actual_key"
python backend_main.py
```

### 문제: 포트 이미 사용 중

```
❌ Address already in use :8000
```

**해결:**
```bash
# 다른 포트 사용
python backend_main.py --port 8001

# 또는 기존 프로세스 종료
lsof -i :8000  # 프로세스 ID 확인
kill -9 <PID>
```

### 문제: 데이터베이스 오류

```
❌ sqlite3.OperationalError: unable to open database file
```

**해결:**
```bash
# 권한 확인
ls -la pharma_mobile.db

# 또는 재생성
rm pharma_mobile.db
python backend_main.py  # 자동 생성됨
```

---

## 📈 성능 최적화

### 1. 데이터베이스 인덱스

```sql
-- 쿼리 성능 향상
CREATE INDEX idx_user_id ON medication_logs(user_id);
CREATE INDEX idx_timestamp ON medication_logs(timestamp);
```

### 2. 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_profile(user_id: str):
    # 캐시된 결과 반환
    pass
```

### 3. 비동기 처리

```python
import asyncio

async def batch_process_health_inputs():
    # 여러 항목 병렬 처리
    tasks = [analyze_health(input) for input in inputs]
    results = await asyncio.gather(*tasks)
```

---

## 🚀 프로덕션 체크리스트

- [ ] GEMINI_API_KEY 설정 완료
- [ ] 환경 변수 모두 설정
- [ ] 데이터베이스 백업 구성
- [ ] 로그 모니터링 설정
- [ ] HTTPS 인증서 설정
- [ ] 속도 제한 (Rate Limiting) 설정
- [ ] 요청 검증 (Validation) 완료
- [ ] 에러 처리 완료
- [ ] API 문서 배포
- [ ] 헬스 체크 활성화

---

## 📞 지원

문제 발생 시:
1. 로그 확인
2. API 문서 참고
3. 테스트 스크립트 실행

**완료!** 🎉

백엔드가 준비되었습니다. Flutter 앱 개발로 진행하면 됩니다.
