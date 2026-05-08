# 옵션 D: 배포 준비
**상태:** 옵션 D - 배포 준비 (시작)  
**날짜:** 2026-05-07  

---

## 개요

SHIELD PHARMA-HYBRID v21.0을 프로덕션 환경에 배포하기 위한 완벽한 준비 가이드.

---

## 1️⃣ Docker 컨테이너화

### Dockerfile 작성

```dockerfile
# Dockerfile

FROM python:3.11-slim

LABEL maintainer="SHIELD PHARMA <team@shield-pharma.com>"
LABEL version="21.0"
LABEL description="SHIELD PHARMA-HYBRID v21.0 - Medical Prescription Analysis"

# 작업 디렉토리
WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY . .

# 디렉토리 생성
RUN mkdir -p pharma_output pharma_voice_comp pharma_patients

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 포트 노출
EXPOSE 8501

# 기본 명령어
CMD ["streamlit", "run", "main_app_v2_agents.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--logger.level=info"]
```

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  pharma-app:
    build: .
    container_name: shield-pharma-v21
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MFDS_API_KEY=${MFDS_API_KEY}
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    volumes:
      - ./pharma_output:/app/pharma_output
      - ./pharma_voice_comp:/app/pharma_voice_comp
      - ./pharma_patients:/app/pharma_patients
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - pharma-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 옵션: 데이터베이스 (향후 SQLite → PostgreSQL 마이그레이션)
  postgres:
    image: postgres:15-alpine
    container_name: pharma-db
    environment:
      POSTGRES_DB: shield_pharma
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pharma_db_data:/var/lib/postgresql/data
    networks:
      - pharma-network
    restart: unless-stopped
    profiles: ["with-db"]

volumes:
  pharma_db_data:

networks:
  pharma-network:
    driver: bridge
```

### .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.env.local
.git
.gitignore
.pytest_cache
.coverage
dist/
build/
*.egg-info/
.vscode/
.idea/
.DS_Store
prescription_images/
pharma_output/*
pharma_voice_comp/*
logs/*
benchmark_results.json
*.log
```

### 환경 변수 파일

```bash
# .env.production

# API 키 (배포 환경에서 설정)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
MFDS_API_KEY=...

# 시스템 설정
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=False

# 데이터베이스 (향후)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shield_pharma
DB_USER=pharma_admin
DB_PASSWORD=...

# 모니터링
SENTRY_DSN=...
DATADOG_API_KEY=...

# 보안
ALLOWED_HOSTS=localhost,127.0.0.1,*.shield-pharma.com
CORS_ORIGINS=https://shield-pharma.com
```

---

## 2️⃣ Kubernetes 배포 매니페스트

### Namespace & ConfigMap

```yaml
# kubernetes/namespace.yaml

apiVersion: v1
kind: Namespace
metadata:
  name: shield-pharma
  labels:
    name: shield-pharma
    environment: production
```

```yaml
# kubernetes/configmap.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: pharma-config
  namespace: shield-pharma
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  MAX_RETRIES: "3"
  API_TIMEOUT_SEC: "15"
  CACHE_TTL_HOURS: "1"
```

### Secret (API 키)

```yaml
# kubernetes/secret.yaml

apiVersion: v1
kind: Secret
metadata:
  name: pharma-secrets
  namespace: shield-pharma
type: Opaque
data:
  ANTHROPIC_API_KEY: <base64-encoded>
  GOOGLE_API_KEY: <base64-encoded>
  MFDS_API_KEY: <base64-encoded>
  DB_PASSWORD: <base64-encoded>
```

### Deployment

```yaml
# kubernetes/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: shield-pharma
  namespace: shield-pharma
  labels:
    app: shield-pharma
    version: v21.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: shield-pharma
  template:
    metadata:
      labels:
        app: shield-pharma
        version: v21.0
    spec:
      containers:
      - name: pharma-app
        image: shield-pharma:v21.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8501
          protocol: TCP
        
        # 환경 변수
        envFrom:
        - configMapRef:
            name: pharma-config
        - secretRef:
            name: pharma-secrets
        
        # 리소스 요청/제한
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        
        # 헬스체크
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 40
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # 볼륨 마운트
        volumeMounts:
        - name: pharma-output
          mountPath: /app/pharma_output
        - name: pharma-patients
          mountPath: /app/pharma_patients
        - name: logs
          mountPath: /app/logs
      
      # 보안 설정
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      
      # 볼륨
      volumes:
      - name: pharma-output
        persistentVolumeClaim:
          claimName: pharma-output-pvc
      - name: pharma-patients
        persistentVolumeClaim:
          claimName: pharma-patients-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: pharma-logs-pvc
```

### Service & Ingress

```yaml
# kubernetes/service.yaml

apiVersion: v1
kind: Service
metadata:
  name: shield-pharma-service
  namespace: shield-pharma
  labels:
    app: shield-pharma
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
    name: http
  selector:
    app: shield-pharma
```

```yaml
# kubernetes/ingress.yaml

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shield-pharma-ingress
  namespace: shield-pharma
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - shield-pharma.com
    - api.shield-pharma.com
    secretName: shield-pharma-tls
  rules:
  - host: shield-pharma.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: shield-pharma-service
            port:
              number: 80
```

### Persistent Volume Claims

```yaml
# kubernetes/pvc.yaml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pharma-output-pvc
  namespace: shield-pharma
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pharma-patients-pvc
  namespace: shield-pharma
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pharma-logs-pvc
  namespace: shield-pharma
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
```

---

## 3️⃣ 운영 매뉴얼

### 배포 단계별 가이드

#### 단계 1: 사전 준비 (1시간)

```bash
# 1. Docker 이미지 빌드
docker build -t shield-pharma:v21.0 .

# 2. 이미지 테스트 (로컬)
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  shield-pharma:v21.0

# 3. 이미지 레지스트리에 푸시
docker push registry.example.com/shield-pharma:v21.0

# 4. Kubernetes 클러스터 준비
kubectl cluster-info
kubectl get nodes
```

#### 단계 2: Kubernetes 배포 (30분)

```bash
# 1. Namespace 생성
kubectl apply -f kubernetes/namespace.yaml

# 2. Secrets 생성
kubectl create secret generic pharma-secrets \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --from-literal=GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --from-literal=MFDS_API_KEY=$MFDS_API_KEY \
  -n shield-pharma

# 3. ConfigMap 생성
kubectl apply -f kubernetes/configmap.yaml

# 4. PVC 생성
kubectl apply -f kubernetes/pvc.yaml

# 5. Deployment 배포
kubectl apply -f kubernetes/deployment.yaml

# 6. Service 생성
kubectl apply -f kubernetes/service.yaml

# 7. Ingress 생성
kubectl apply -f kubernetes/ingress.yaml

# 8. 롤아웃 모니터링
kubectl rollout status deployment/shield-pharma -n shield-pharma
```

#### 단계 3: 검증 (30분)

```bash
# 1. Pod 상태 확인
kubectl get pods -n shield-pharma
kubectl describe pod <pod-name> -n shield-pharma

# 2. 로그 확인
kubectl logs -f deployment/shield-pharma -n shield-pharma

# 3. 헬스체크
kubectl exec -it <pod-name> -n shield-pharma -- \
  curl http://localhost:8501/_stcore/health

# 4. 서비스 접근
kubectl port-forward svc/shield-pharma-service 8501:80 -n shield-pharma
# http://localhost:8501 접속

# 5. E2E 테스트 실행
kubectl exec -it <pod-name> -n shield-pharma -- \
  python performance_benchmarks.py
```

### 일상 운영

#### 모니터링

```bash
# Pod 모니터링
kubectl get pods -n shield-pharma --watch

# 리소스 사용량
kubectl top pods -n shield-pharma
kubectl top nodes

# 로그 조회
kubectl logs -n shield-pharma -l app=shield-pharma --tail=100 -f

# 메트릭 수집 (Prometheus 연동)
kubectl port-forward -n shield-pharma \
  svc/prometheus 9090:9090
```

#### 업데이트 배포

```bash
# 새 버전 배포
docker build -t shield-pharma:v21.1 .
docker push registry.example.com/shield-pharma:v21.1

# Kubernetes 업데이트 (자동 롤링 업데이트)
kubectl set image deployment/shield-pharma \
  pharma-app=shield-pharma:v21.1 \
  -n shield-pharma

# 롤아웃 상태 확인
kubectl rollout status deployment/shield-pharma -n shield-pharma
```

#### 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/shield-pharma -n shield-pharma

# 특정 리비전으로 롤백
kubectl rollout history deployment/shield-pharma -n shield-pharma
kubectl rollout undo deployment/shield-pharma --to-revision=2 -n shield-pharma
```

---

## 4️⃣ 모니터링 & 알림 설정

### Prometheus 메트릭

```python
# utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# 카운터
prescription_processed = Counter(
    'prescriptions_processed_total',
    'Total prescriptions processed',
    ['status']  # success, failure
)

api_calls_total = Counter(
    'api_calls_total',
    'Total API calls',
    ['api_name', 'status']
)

# 히스토그램
processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Prescription processing duration',
    buckets=(0.5, 1, 2, 5, 10, 30, 60)
)

# 게이지
active_prescriptions = Gauge(
    'active_prescriptions',
    'Currently processing prescriptions'
)

cache_hit_rate = Gauge(
    'cache_hit_rate_percent',
    'Cache hit rate percentage'
)
```

### Grafana 대시보드

```json
{
  "dashboard": {
    "title": "SHIELD PHARMA v21.0",
    "panels": [
      {
        "title": "처방전 처리 성공률",
        "targets": [
          {
            "expr": "rate(prescriptions_processed_total{status='success'}[5m])"
          }
        ]
      },
      {
        "title": "평균 처리 시간",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, processing_duration_seconds)"
          }
        ]
      },
      {
        "title": "캐시 히트율",
        "targets": [
          {
            "expr": "cache_hit_rate_percent"
          }
        ]
      },
      {
        "title": "API 호출 지연",
        "targets": [
          {
            "expr": "rate(api_calls_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### 알림 규칙 (AlertManager)

```yaml
# alerts.yml

groups:
- name: shield_pharma
  rules:
  - alert: HighFailureRate
    expr: |
      (sum(rate(prescriptions_processed_total{status='failure'}[5m])) /
       sum(rate(prescriptions_processed_total[5m]))) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "처방전 처리 실패율 높음 (5%+)"
      description: "실패율: {{ $value | humanizePercentage }}"
  
  - alert: HighProcessingLatency
    expr: histogram_quantile(0.95, processing_duration_seconds) > 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "높은 처리 지연 감지"
      description: "P95 지연: {{ $value }}초"
  
  - alert: LowCacheHitRate
    expr: cache_hit_rate_percent < 50
    for: 30m
    labels:
      severity: info
    annotations:
      summary: "캐시 히트율 낮음"
      description: "현재: {{ $value }}%"
```

---

## 5️⃣ CI/CD 파이프라인

### GitHub Actions 워크플로우

```yaml
# .github/workflows/deploy.yml

name: Build & Deploy to Kubernetes

on:
  push:
    branches: [main]
    paths:
      - 'agents/**'
      - 'utils/**'
      - 'main_app_v2_agents.py'
      - 'requirements.txt'
      - 'Dockerfile'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=agents --cov=utils
    
    - name: Run benchmarks
      run: python performance_benchmarks.py

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t shield-pharma:${{ github.sha }} .
        docker tag shield-pharma:${{ github.sha }} shield-pharma:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_REGISTRY_PASSWORD }} | docker login \
          -u ${{ secrets.DOCKER_REGISTRY_USER }} --password-stdin
        docker push shield-pharma:${{ github.sha }}
        docker push shield-pharma:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.27.0'
    
    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > $HOME/.kube/config
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/shield-pharma \
          pharma-app=shield-pharma:${{ github.sha }} \
          -n shield-pharma --record
    
    - name: Wait for rollout
      run: |
        kubectl rollout status deployment/shield-pharma \
          -n shield-pharma --timeout=10m
    
    - name: Run smoke tests
      run: |
        kubectl run smoke-test \
          --image=shield-pharma:${{ github.sha }} \
          --rm -it --restart=Never \
          -n shield-pharma -- python performance_benchmarks.py
```

---

## 6️⃣ 배포 체크리스트

### 배포 전 (Pre-Deployment)
- [ ] 모든 테스트 통과 (유닛, 통합, E2E)
- [ ] 성능 벤치마크 목표 달성
- [ ] 보안 검수 완료 (의료데이터 보호)
- [ ] 문서 최신화
- [ ] API 키 설정 확인
- [ ] 백업 전략 확인
- [ ] 롤백 계획 수립

### 배포 중 (During Deployment)
- [ ] 클러스터 상태 정상 확인
- [ ] 리소스 가용성 확인
- [ ] 롤아웃 진행 상황 모니터링
- [ ] 로그 실시간 확인
- [ ] 헬스체크 통과 확인

### 배포 후 (Post-Deployment)
- [ ] 모든 Pod 정상 작동 확인
- [ ] 헬스체크 엔드포인트 응답 확인
- [ ] 데이터베이스 연결 확인
- [ ] API 키 작동 확인
- [ ] E2E 테스트 재실행
- [ ] 사용자 접근 확인
- [ ] 모니터링 대시보드 정상 작동
- [ ] 알림 규칙 정상 작동

---

## 비용 추정 (월간, AWS 기준)

| 항목 | 사양 | 월간 비용 |
|------|------|----------|
| **Kubernetes (EKS)** | 3 nodes, t3.medium | $180 |
| **Storage (EBS)** | 20GB (output + patients + logs) | $20 |
| **Load Balancer** | Application Load Balancer | $16 |
| **Monitoring** | CloudWatch + Datadog | $50 |
| **Data Transfer** | Moderate traffic | $25 |
| **API 호출** | Anthropic, Google, MFDS | Variable |
| **총계** | | **~$300-500/월** |

---

## 다음 단계

1. ✅ Docker & Kubernetes 매니페스트 생성
2. ✅ 모니터링 & 알림 설정
3. ✅ CI/CD 파이프라인 구성
4. ✅ 운영 매뉴얼 작성
5. ⏳ **옵션 4: E2E 테스트 검토** (다음)

---

**준비 상태:** 옵션 D 구현 가이드 준비 완료  
**예상 배포 시간:** 1-2시간 (준비 + 배포 + 검증)  
**다음 단계:** 옵션 4 (E2E 테스트 검토)

