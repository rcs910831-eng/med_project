# SHIELD PHARMA-HYBRID v21.0 - Production Dockerfile
# 멀티 스테이지 빌드 (Multi-stage Build)

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements_agents.txt .
RUN pip install --no-cache-dir --user -r requirements_agents.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="SHIELD PHARMA Team <team@shieldpharma.com>"
LABEL version="21.0"
LABEL description="SHIELD PHARMA-HYBRID v21.0 - Medical Prescription Analysis System"

# 환경 변수
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    APP_HOME=/app

WORKDIR $APP_HOME

# 필수 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 1에서 설치된 Python 패키지 복사
COPY --from=builder /root/.local /root/.local

# PATH 설정
ENV PATH=/root/.local/bin:$PATH

# 애플리케이션 코드 복사
COPY . .

# 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/patient_histories \
    /app/price_database \
    /app/pharma_output \
    /app/logs \
    && chmod -R 755 /app

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# 비루트 사용자 생성
RUN useradd -m -u 1000 pharmauser && \
    chown -R pharmauser:pharmauser /app

USER pharmauser

# 포트 노출
EXPOSE 8501

# 애플리케이션 시작
CMD ["streamlit", "run", "main_app_v3_with_option_c.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--logger.level=info"]
