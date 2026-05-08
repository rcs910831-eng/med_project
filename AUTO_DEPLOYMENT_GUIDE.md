
+==================================================================+
|          [>>] PHARMA-MOBILE 자동 배포 준비 완료                   |
+==================================================================+

[*] 배포 정보
===================================================================

Google Cloud 프로젝트: pharma-mobile-495713
서비스 계정: pharma-voice-service@pharma-mobile-495713.iam.gserviceaccount.com
JSON 파일: C:\Users\rcs91\Downloads\pharma-mobile-495713-157aab5a9c77.json

배포 대상: Render
서비스명: pharma-mobile-backend
지역: Singapore
타입: Web Service (Python)

===================================================================

[OK] 배포 전 확인사항 (완료)
===================================================================

백엔드 파일
  [OK] backend_main.py
  [OK] voice_handler.py
  [OK] pharma_mobile.db
  [OK] requirements_backend.txt

배포 설정
  [OK] Procfile
  [OK] render.yaml
  [OK] .gitignore

Google Cloud
  [OK] JSON 파일 유효성 검증 완료
  [OK] 프로젝트 ID 확인
  [OK] 서비스 계정 확인

===================================================================

[>>] 배포 프로세스
===================================================================

Step 1: Render 대시보드 준비
  → https://dashboard.render.com
  → GitHub 로그인 (이미 연동됨)

Step 2: Web Service 생성
  → New → Web Service
  → med_project 선택
  → 설정값 자동 입력

Step 3: 환경 변수 설정
  → PYTHON_VERSION = 3.11
  → ENVIRONMENT = production
  → GOOGLE_CLOUD_CREDENTIALS_JSON = (자동 입력)

Step 4: 배포 시작
  → Create Web Service 클릭
  → 2-3분 대기
  → "Live" 상태 확인

Step 5: 자동 검증
  → python validate_deployment.py <URL>
  → 모든 API 테스트
  → 성공 리포트 생성

===================================================================

[!]  중요 사항
===================================================================

Render 대시보드에서 다음을 입력할 때:

1. Build Command:
   pip install -r requirements_backend.txt

2. Start Command:
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT

3. 환경 변수 - GOOGLE_CLOUD_CREDENTIALS_JSON:
   파일: C:\Users\rcs91\Downloads\pharma-mobile-495713-157aab5a9c77.json
   
   [주의] 실제 JSON 내용은 다음 파일에서 복사하세요:
   C:\Users\rcs91\Downloads\pharma-mobile-495713-157aab5a9c77.json
   
   복사 방법:
   1. 파일을 메모장으로 열기
   2. Ctrl+A (전체 선택)
   3. Ctrl+C (복사)
   4. Render 대시보드의 VALUE 필드에 붙여넣기 (Ctrl+V)

===================================================================

[*] 다음 단계
===================================================================

1. Render 대시보드 열기
   https://dashboard.render.com

2. New → Web Service 선택

3. med_project 저장소 선택

4. 위의 설정값 입력

5. Create Web Service 클릭

6. 배포 완료 후 URL 확인

===================================================================

배포 준비 완료! 위 단계를 따라 진행하세요. [*]
