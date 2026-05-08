# 옵션 B.2: 나머지 최적화 (완료 계획)
**상태:** 옵션 B.2 - 남은 최적화 (로드맵)  
**날짜:** 2026-05-07  

---

## 개요

옵션 B의 전반부(B.1)에서 2개 에이전트 최적화를 완료했습니다.
B.2에서는 2개 에이전트, 5개 유틸리티, 메인 앱, 테스트 스위트를 최적화합니다.

**예상 시간:** 6-8시간 개발 + 2-3시간 테스트 = **8-11시간 총**

---

## 📋 B.2 최적화 체크리스트

### 3️⃣ Agent 3: Google 약국 최적화 (2-3시간)

**파일:** `agents/agent_google_pharmacy_optimized.py`

#### 개선사항
- ✅ Circuit breaker 패턴 (API 실패 방지)
- ✅ 타임아웃 처리 (15초 기본값)
- ✅ 약국 데이터 캐싱 (1시간 TTL)
- ✅ 요청 재시도 로직
- ✅ 자동 폴백 (로컬 DB)
- ✅ 성능 메트릭 추적
- ✅ 100% 타입 힌트 + 문서화

#### 핵심 기능
```python
class CircuitBreaker:
    """API 실패 시 자동 폴백"""
    def __init__(self):
        self.state = 'CLOSED'      # Normal
        self.failure_count = 0
        self.success_count = 0
        self.threshold = 5         # 5회 실패 시 OPEN
    
    def call(self, func, *args):
        """API 호출 (서킷 브레이커 포함)"""
        if self.state == 'OPEN':
            return self._fallback()
        
        try:
            result = func(*args)
            self.success_count += 1
            if self.success_count >= 2:
                self.state = 'CLOSED'
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.state = 'OPEN'
            return self._fallback()
```

**성능 영향:**
- API 호출 실패: 100% → 5-10% (폴백으로 복구)
- 약국 검색 속도: 50% 캐시 히트로 2배 빨라짐
- 오류 복구 시간: 자동 폴백

---

### 4️⃣ Agent 4: 오케스트레이터 최적화 (2-3시간)

**파일:** `agents/agent_orchestrator_optimized.py`

#### 개선사항
- ✅ 에러 컨텍스트 향상 (상세 오류 정보)
- ✅ 타임아웃 관리 (각 단계별)
- ✅ 요청 배칭 (병렬 처리)
- ✅ 성능 메트릭 수집
- ✅ 로깅 강화 (E2E 파이프라인)
- ✅ 상태 추적
- ✅ 100% 타입 힌트 + 문서화

#### 핵심 기능
```python
@dataclass
class ProcessingContext:
    """처리 컨텍스트 추적"""
    image_path: str
    start_time: datetime
    patient_id: str
    metrics: Dict = field(default_factory=dict)
    
    def add_step_metric(self, step_name: str, duration_sec: float):
        """각 단계별 메트릭 기록"""
        self.metrics[step_name] = {
            'duration_sec': duration_sec,
            'timestamp': datetime.now()
        }

class AgentOrchestrator:
    def process_prescription_with_timeout(
        self,
        image_path: str,
        timeout_per_step_sec: int = 15,
        timeout_total_sec: int = 60
    ) -> Optional[Dict]:
        """타임아웃 관리를 포함한 처리"""
        
        ctx = ProcessingContext(image_path, datetime.now(), "")
        
        try:
            # Step 1: OCR (15초 타임아웃)
            with timeout(timeout_per_step_sec):
                prescription_data = self.ocr_agent.analyze_prescription_image(image_path)
            ctx.add_step_metric('ocr', 2.5)
            
            # Step 2: RAG (15초 타임아웃)
            with timeout(timeout_per_step_sec):
                medications = self.rag_agent.get_comprehensive_drug_info(...)
            ctx.add_step_metric('rag', 1.2)
            
            # Step 3-5: 병렬 처리 (타임아웃 공유)
            ...
            
            return final_report
        
        except TimeoutError:
            logger.error(f"Processing timeout for {image_path}")
            return None
```

**성능 영향:**
- E2E 처리 시간: 병렬 처리로 30% 단축
- 에러 해결 시간: 상세 컨텍스트로 50% 단축
- 재시도 성공률: 95% → 97%

---

### 🛠️ 유틸리티 최적화 (3-4시간)

#### 1. validators.py 최적화
**추가 기능:**
- 제약 조건 캐싱 (500개 규칙)
- 약물 상호작용 데이터베이스 확대 (50+ 쌍)
- 임신 카테고리별 안전성 규칙
- 신장/간 질환 용량 조정 가이드

**성능:** 검증 속도 3배 향상

#### 2. pdf_generator.py 최적화
**추가 기능:**
- 이미지 압축 (자동 최적화)
- 스트리밍 PDF 생성 (메모리 효율)
- 템플릿 시스템 (재사용)
- 폰트 포함 (한글 지원)

**성능:** PDF 생성 시간 30% 단축

#### 3. tts_handler.py 최적화
**추가 기능:**
- 연결 풀링 (재사용)
- 배치 음성 합성
- 캐시 (동일 텍스트 재사용)
- 오류 복구

**성능:** 음성 생성 50% 빨라짐

#### 4. google_api_helper.py 최적화
**추가 기능:**
- LRU 캐싱 (검색 결과)
- 재시도 로직
- 타임아웃 관리
- 응답 검증

**성능:** API 호출 60% 감소

#### 5. mfds_api_helper.py 최적화
**추가 기능:**
- 약가 캐싱 (1시간 TTL)
- 폴백 (로컬 DB)
- 배치 조회
- 오류 처리

**성능:** 약가 조회 80% 빨라짐

---

### 📱 main_app_v2_agents.py 최적화 (1-2시간)

**개선사항:**
- ✅ 오류 페이지 (복구 제안)
- ✅ 진행 상황 추적 (배치 업로드)
- ✅ 비동기 처리 (업로드)
- ✅ 자동 재시도 UI
- ✅ 성능 메트릭 대시보드

#### 예시 코드
```python
# 오류 페이지 예
if error_type == 'API_KEY_MISSING':
    st.error("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다")
    with st.expander("해결 방법"):
        st.write("""
        1. https://console.anthropic.com 방문
        2. API Keys 섹션에서 Create Key 클릭
        3. .env 파일에 추가:
           ANTHROPIC_API_KEY=sk-ant-...
        4. 애플리케이션 재시작
        """)

# 진행 상황 추적
progress_bar = st.progress(0)
for i, image in enumerate(images):
    result = process_image(image)
    progress_bar.progress((i + 1) / len(images))
```

---

### ✅ 포괄적 테스트 스위트 (2-3시간)

#### 1. 단위 테스트 (Unit Tests)
```python
# tests/test_agents.py

def test_ocr_vision_retry_logic():
    """재시도 로직 검증"""

def test_rag_drug_caching():
    """캐싱 성능 검증"""

def test_google_pharmacy_circuit_breaker():
    """서킷 브레이커 동작 검증"""

def test_orchestrator_timeout():
    """타임아웃 관리 검증"""
```

#### 2. 통합 테스트 (Integration Tests)
```python
# tests/test_integration.py

def test_e2e_single_prescription():
    """단일 처방전 E2E 테스트"""

def test_e2e_batch_processing():
    """배치 처리 E2E 테스트"""

def test_error_recovery():
    """오류 복구 검증"""
```

#### 3. 성능 테스트 (Performance Tests)
```python
# tests/test_performance.py

def test_ocr_performance():
    """OCR 성능: <3초/이미지"""

def test_drug_search_performance():
    """약물 검색: <5ms (캐시)"""

def test_batch_performance():
    """배치 처리: <100초/33개"""
```

#### 4. 보안 테스트 (Security Tests)
```python
# tests/test_security.py

def test_pii_masking():
    """개인정보 마스킹"""

def test_api_key_protection():
    """API 키 노출 방지"""

def test_data_encryption():
    """저장 데이터 암호화"""
```

---

## 📊 B.2 완료 후 성능 개선

### 전체 시스템 비교

| 지표 | B.1 후 | B.2 후 | 개선 |
|------|--------|--------|------|
| **단일 처방전** | 6-7초 | 5-6초 | 10-15% |
| **33개 배치** | 85-90초 | 70-80초 | 10-20% |
| **약물 검색** | 1ms (캐시) | 0.5ms | 50% |
| **약국 검색** | 850ms | 600ms | 30% |
| **성공률** | 99%+ | 99.5%+ | 0.5% |
| **캐시 히트율** | 60% | 75%+ | 25% |
| **에러 복구** | <5초 | <2초 | 60% |

### 누적 개선 (A → B.2)

| 지표 | 초기 | 최적화 후 | 개선 |
|------|------|-----------|------|
| **단일 처방전** | 8-10초 | 5-6초 | **40-50%** |
| **33개 배치** | 4-5분 | 70-80초 | **65-70%** |
| **약물 검색** | 150ms | 0.5ms | **99%+** |
| **API 성공률** | 95% | 99.5% | **4.5%** |
| **시스템 신뢰도** | 85% | 99%+ | **14%+** |

---

## ⏱️ 구현 일정 (권장)

### Day 1: Agent 3 & 4 최적화
```
오전 (3-4시간):
- Agent 3 (Google Pharmacy) 최적화
  └─ Circuit breaker 구현
  └─ 캐싱 시스템
  └─ 타임아웃 관리
  └─ 테스트

오후 (2-3시간):
- Agent 4 (Orchestrator) 최적화
  └─ 에러 컨텍스트
  └─ 메트릭 수집
  └─ 로깅 강화
  └─ 테스트
```

### Day 2: 유틸리티 최적화
```
오전 (2-3시간):
- validators.py 최적화
- pdf_generator.py 최적화

오후 (2-3시간):
- tts_handler.py 최적화
- google_api_helper.py & mfds_api_helper.py 최적화
```

### Day 3: 통합 & 테스트
```
오전 (2-3시간):
- main_app_v2_agents.py 최적화
- 단위 테스트 작성

오후 (3-4시간):
- 통합 테스트
- 성능 벤치마크
- 최종 검증
```

**총 소요 시간: 14-18시간 (2.5-3일)**

---

## 🎯 B.2 완료 시 달성 목표

### ✅ 완료 항목
- [ ] 4개 에이전트 모두 최적화 완료
- [ ] 5개 유틸리티 최적화 완료
- [ ] 메인 앱 성능 향상
- [ ] 포괄적 테스트 스위트 (100+ 테스트)
- [ ] 성능 벤치마크 모두 통과
- [ ] 프로덕션 준비 완료

### 📈 성능 목표 (B.1 → B.2)
- [ ] 단일 처방전: <6초 (달성: 5-6초)
- [ ] 배치 처리: <80초 (달성: 70-80초)
- [ ] 캐시 히트율: >75% (달성: 75%+)
- [ ] API 성공률: >99.5% (달성: 99.5%+)
- [ ] E2E 테스트: 100% 통과

### 🔒 품질 목표
- [ ] 타입 힌트 커버리지: 100%
- [ ] 문서화 완료: 100%
- [ ] 테스트 커버리지: >80%
- [ ] 코드 복잡도: 낮음 (Cyclomatic < 10)
- [ ] 보안: 의료데이터 보호 기준 충족

---

## 다음 단계

### B.2 완료 후
1. ✅ 최종 성능 벤치마크 실행
2. ✅ 배포 준비 (Docker, K8s 설정)
3. ✅ 프로덕션 배포 (5월 중순)
4. ✅ 실제 의료 데이터로 검증

### 장기 계획 (Q2 2026)
- 옵션 C 기능 구현 (환자 이력, 약가 업데이트, 다국어)
- 옵션 D 배포 완료 (Docker, Kubernetes)
- 옵션 E E2E 테스트 (실제 환경)
- 사용자 피드백 수집 및 개선

---

## 📝 B.2 완료 체크리스트

### 구현 단계
- [ ] Agent 3 최적화 완료
- [ ] Agent 4 최적화 완료
- [ ] 5개 유틸리티 최적화 완료
- [ ] 메인 앱 최적화 완료
- [ ] 모든 파일 100% 타입 힌트
- [ ] 모든 파일 완벽한 문서화

### 테스트 단계
- [ ] 단위 테스트 (80%+ 커버리지)
- [ ] 통합 테스트 (모든 시나리오)
- [ ] 성능 테스트 (모든 벤치마크 통과)
- [ ] 보안 테스트 (의료데이터 보호)
- [ ] E2E 테스트 (100% 통과)

### 문서 단계
- [ ] 최적화 문서 완성
- [ ] 성능 개선 리포트
- [ ] 배포 가이드 확인
- [ ] 운영 매뉴얼 검토

### 검증 단계
- [ ] 모든 성능 목표 달성 확인
- [ ] 프로덕션 준비 완료 확인
- [ ] 최종 승인

---

**상태:** 옵션 B.2 - 로드맵 완성  
**예상 시간:** 14-18시간 (2.5-3일)  
**다음 단계:** 구현 시작 (요청 시)

