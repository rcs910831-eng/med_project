# SHIELD PHARMA-HYBRID v21.0 - 설정 가이드

## Phase 2 구현 완료 상태

### ✅ 구현된 컴포넌트

**4개 에이전트 모두 완성:**
- ✅ Agent 1: OCR & Vision 전문가 (처방전 이미지 분석)
- ✅ Agent 2: RAG & 약물정보 전문가 (약물 정보 검색)
- ✅ Agent 3: Google 약국 전문가 (약국 검색 + 약가)
- ✅ Agent 4: 오케스트레이터 (보고서 생성)

**5개 유틸리티 모듈:**
- ✅ google_api_helper.py - Google Places API
- ✅ mfds_api_helper.py - MFDS 한국 FDA API
- ✅ pdf_generator.py - PDF/HTML 보고서
- ✅ validators.py - 의료 안전 검증
- ✅ tts_handler.py - Text-to-Speech

**테스트 프레임워크:**
- ✅ E2E 테스트 러너 (main_e2e_test.py)
- ✅ 33개 처방전 샘플 처리 준비 완료

---

## 🔐 API 키 설정

### 필수 API 키

**.env 파일에 다음 정보 추가:**

```env
# Anthropic API (필수 - Phase 2 실행용)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx

# Google API (이미 설정됨)
GOOGLE_API_KEY=AIzaSyCYmQ0yvogcrKB1reCqaZY5uF-DZVHxRQ8

# MFDS API (이미 설정됨)
MFDS_API_KEY=3333b43c676617db26970c7a5ec6533ab613cc80b82309e175c3b3df764d4262
```

### Anthropic API 키 획득:
1. https://console.anthropic.com 방문
2. 계정 생성/로그인
3. API Keys 섹션에서 새 키 생성
4. 복사하여 `.env` 파일에 `ANTHROPIC_API_KEY=` 뒤에 붙여넣기

---

## 🚀 E2E 테스트 실행

### 1단계: API 키 설정
`.env` 파일에 ANTHROPIC_API_KEY 추가 (위 참조)

### 2단계: 테스트 실행

```bash
# 빠른 테스트 (5개 샘플)
python main_e2e_test.py

# 전체 테스트 (33개 샘플) - 코드 수정 후
# main_e2e_test.py의 max_samples 파라미터 제거
```

### 3단계: 결과 확인

테스트 결과:
- JSON 리포트: `e2e_test_report.json`
- PDF 보고서: `pharma_output/report_*.pdf`
- HTML 보고서: `pharma_output/report_*.html`
- 음성 설명: `pharma_output/voice_*.mp3`

---

## 📊 예상 출력

### 성공한 처방전 처리:

```json
{
  "report_id": "RX_20240507_120000",
  "patient": {
    "name": "환자명",
    "age": 68,
    "sex": "남",
    "diagnosis_primary": "고혈압"
  },
  "medications": [
    {
      "name": "노바스크정",
      "strength": "5mg",
      "recommended_daily_dose": "1회 1정",
      "mfds_price": 1123,
      "warnings": ["자몽 주스 금지"]
    }
  ],
  "safety": {
    "safe": true,
    "warnings": ["고령자 저혈압 주의"]
  },
  "pharmacies": [
    {
      "name": "서울약국",
      "distance_km": 0.5,
      "estimated_total": 2000
    }
  ]
}
```

---

## 🔍 테스트 검증 항목

### Agent 1 검증:
- [ ] 처방전 이미지 → JSON 추출 정확도 > 95%
- [ ] 환자정보 (이름, 나이, 성별) 올바르게 추출
- [ ] 약물정보 (이름, 용량, 수량) 올바르게 추출

### Agent 2 검증:
- [ ] MFDS DB에서 약물 정보 검색
- [ ] 약물 부작용/주의사항 조회
- [ ] 임상 가이드라인 매칭
- [ ] 약물 상호작용 확인

### Agent 3 검증:
- [ ] Google Places API로 약국 검색
- [ ] MFDS 공시약가 조회
- [ ] 거리 기반 정렬
- [ ] 5개 이상 약국 반환

### Agent 4 검증:
- [ ] 3개 에이전트 결과 통합
- [ ] PDF 보고서 생성
- [ ] HTML 보고서 생성
- [ ] 음성 설명 생성
- [ ] JSON 데이터 출력

---

## ⚠️ 주의사항

### 의료 데이터 정확성
- 모든 약물 정보는 MFDS 공식 데이터 기반
- 용량/부작용 정보는 임상 가이드라인 기반
- 환자 안전이 최우선

### API 사용량 제한
- Google Places API: 월 25,000회 무료 호출
- MFDS API: 일일 10,000회 무료 호출
- Anthropic API: 사용량에 따라 비용 발생

### 보안 주의
- `.env` 파일에 API 키 보관
- 본 코드는 로컬 환경에서만 실행
- 환자 정보는 암호화하여 저장

---

## 🛠️ 문제 해결

### 문제: ANTHROPIC_API_KEY not found
**해결:** `.env` 파일에 ANTHROPIC_API_KEY 추가

### 문제: Google API connectivity failed
**해결:** GOOGLE_API_KEY 유효성 확인

### 문제: 처방전 이미지 분석 실패
**해결:** 
- 이미지 품질 확인 (최소 150 DPI)
- 이미지 형식 확인 (PNG, JPG, WebP 지원)
- 처방전이 명확하게 보이는지 확인

### 문제: 약물 정보 찾을 수 없음
**해결:** 
- 약물명 스펠링 확인
- RAG 데이터베이스에 약물 추가 필요

---

## 📈 성능 목표

| 지표 | 목표 | 상태 |
|------|------|------|
| E2E 처리 시간 | < 15초 | 준비 완료 |
| OCR 정확도 | > 95% | 검증 필요 |
| 안전성 검증 | 100% | 완성 |
| PDF 생성 | 성공 | 준비 완료 |
| 음성 생성 | 성공 | 준비 완료 |

---

## 📞 다음 단계

1. **ANTHROPIC_API_KEY 설정**
   - Anthropic 콘솔에서 API 키 생성
   - `.env` 파일에 추가

2. **E2E 테스트 실행**
   - `python main_e2e_test.py` 실행
   - 결과 확인

3. **결과 검증**
   - `e2e_test_report.json` 확인
   - PDF/HTML 보고서 품질 검사
   - 음성 설명 명확성 확인

4. **프로덕션 배포**
   - 33개 전체 샘플로 테스트
   - 의료 데이터 정확성 재확인
   - 보안 감사

---

**Version:** SHIELD PHARMA-HYBRID v21.0 - Phase 2  
**Last Updated:** 2024-05-07  
**Status:** 구현 완료, 테스트 대기
