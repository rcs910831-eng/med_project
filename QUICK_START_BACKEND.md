# 🚀 PHARMA-MOBILE 백엔드 5분 빠른 시작

## ⚡ 지금 바로 시작하기

### Step 1️⃣: 의존성 설치 (2분)

```bash
# 현재 디렉토리: C:\Users\rcs91\github\med_project

# 의존성 설치
pip install -r requirements_backend.txt
```

### Step 2️⃣: API 키 설정 (1분)

```bash
# .env 파일 생성
copy .env.example .env
```

`.env` 파일 수정:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

> **API 키 얻는 방법:**
> 1. https://ai.google.dev 방문
> 2. "Get API Key" 클릭
> 3. 키 복사 → `.env`에 붙여넣기

### Step 3️⃣: 백엔드 실행 (1분)

```bash
python backend_main.py
```

**출력이 이렇게 나오면 성공!**
```
╔════════════════════════════════════════════════════════════╗
║         🏥 PHARMA-MOBILE FastAPI Backend v1.0             ║
║  🚀 서버 시작 중...                                        ║
║  📍 http://localhost:8000                                 ║
║  📖 API 문서: http://localhost:8000/docs                 ║
╚════════════════════════════════════════════════════════════╝
```

### Step 4️⃣: API 테스트 (1분)

**브라우저에서 열기:**
```
http://localhost:8000/docs
```

또는 명령어로 테스트:
```bash
curl http://localhost:8000/health
```

---

## 📱 첫 사용자 생성하기

**Swagger UI에서 또는 이 curl로:**

```bash
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "name": "김철수",
    "age": 68,
    "gender": "남",
    "medications": [
      {"name": "노바스크정 5mg", "dose": "1회 1정, 1일 1회", "note": "정시 복용"}
    ],
    "diagnoses": ["고혈압", "당뇨병"]
  }'
```

**응답:**
```json
{
  "status": "success",
  "user_id": "user001",
  "message": "김철수님의 프로필이 등록되었습니다"
}
```

---

## 🧠 건강 상태 AI 분석

```bash
curl -X POST http://localhost:8000/api/health/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "input_type": "text",
    "content": "다리가 좀 부어요"
  }'
```

**응답 예시:**
```json
{
  "status": "success",
  "analysis": {
    "status_summary": "고혈압으로 인한 부종 증상",
    "medication_order": [
      {
        "name": "노바스크정 5mg",
        "time": "아침 8:00",
        "reason": "혈관 이완으로 부종 완화"
      }
    ],
    "diet_recommendation": [
      {
        "food": "저염 식단",
        "benefit": "혈압 관리",
        "avoid": "염분 많은 음식"
      }
    ],
    "exercise": {
      "type": "부종 완화 요가",
      "duration": "10분",
      "intensity": "저강도",
      "timing": "식후 30분"
    }
  }
}
```

---

## 💾 복약 기록 저장

```bash
# 약을 먹었을 때
curl -X POST http://localhost:8000/api/medication/log \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "medication_name": "노바스크정 5mg",
    "taken": true
  }'

# 약을 안 먹었을 때
curl -X POST http://localhost:8000/api/medication/log \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "medication_name": "노바스크정 5mg",
    "taken": false,
    "side_effect": "너무 바빴어요"
  }'
```

---

## 📊 복약 순응도 조회

```bash
# 최근 7일 순응도
curl http://localhost:8000/api/medication/adherence/user001?days=7
```

**응답:**
```json
{
  "status": "success",
  "overall_rate": 85.5,
  "adherence": {
    "노바스크정 5mg": {
      "taken": 6,
      "not_taken": 1,
      "rate": 85.7
    }
  }
}
```

---

## 🎯 10가지 핵심 API

| # | 메서드 | 엔드포인트 | 기능 |
|----|--------|-----------|------|
| 1 | GET | `/health` | 서버 상태 |
| 2 | POST | `/api/user/register` | 사용자 등록 |
| 3 | GET | `/api/user/{user_id}` | 사용자 조회 |
| 4 | POST | `/api/health/analyze` | AI 건강 분석 |
| 5 | POST | `/api/medication/schedule` | 약물 스케줄 |
| 6 | POST | `/api/medication/log` | 복약 기록 |
| 7 | GET | `/api/medication/adherence/{user_id}` | 순응도 |
| 8 | GET | `/api/reminders/{user_id}` | 알림 조회 |
| 9 | GET | `/api/statistics/{user_id}` | 통계 |
| 10 | GET | `/docs` | API 문서 |

---

## 🐳 Docker로 실행 (선택사항)

```bash
# 이미지 빌드
docker build -f Dockerfile_backend -t pharma-backend .

# 실행
docker run -p 8000:8000 pharma-backend
```

---

## ☁️ Google Cloud Run 배포 (선택사항)

```bash
# Google Cloud에 배포
gcloud run deploy pharma-backend \
  --image gcr.io/pharma-mobile-project/backend:latest \
  --platform managed \
  --region asia-northeast1

# 배포 후 접속
# https://pharma-backend-xxxxx.run.app/docs
```

---

## 🔍 문제해결

### ❌ "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements_backend.txt
```

### ❌ "GEMINI_API_KEY" 오류
```bash
# .env 파일 확인
cat .env

# 또는 환경변수 직접 설정
export GEMINI_API_KEY="your_key"
```

### ❌ "Address already in use :8000"
```bash
# 다른 포트로 실행
python backend_main.py --port 8001
```

---

## 📱 다음: Flutter 모바일 앱 개발

이제 Flutter 앱에서 이 API를 사용할 수 있습니다:

```dart
// Flutter 코드 예시
final response = await dio.post(
  'http://localhost:8000/api/health/analyze',
  data: {
    'user_id': 'user001',
    'input_type': 'text',
    'content': '다리가 부어요'
  },
);
```

---

## ✅ 완료!

백엔드가 **완전히 준비**되었습니다! 🎉

**다음 단계:**
1. ✅ **백엔드 실행 중** (현재)
2. ⏳ **Flutter 앱 개발** (다음)
3. ⏳ **테스트 & 배포**

**통신 시작:**
```bash
# 터미널 1: 백엔드 실행
python backend_main.py

# 터미널 2: 테스트
curl http://localhost:8000/health
```

**API 문서:**
```
http://localhost:8000/docs
```

---

## 📞 더 필요한 것?

- 📖 전체 배포 가이드: `BACKEND_DEPLOYMENT_GUIDE.md`
- 🔧 환경변수 설정: `.env.example` → `.env`
- 🐳 Docker 배포: `Dockerfile_backend`
- 💬 Flask 대신 FastAPI: 성능 3배 빠름 ⚡

**완전한 의료 API 백엔드가 준비되었습니다!** 🏥✨
