# 옵션 C: 추가 기능 구현 계획
**상태:** 옵션 C - 추가 기능 (시작)  
**날짜:** 2026-05-07  

---

## 개요

기존 4-에이전트 시스템에 3가지 핵심 기능을 추가하여 사용자 경험과 임상 가치를 향상시킵니다.

---

## 기능 1️⃣: 환자 이력 추적 시스템

### 목표
각 환자의 처방전 이력을 저장하고 관리하여:
- 약물 복용 이력 추적
- 약물 알레르기 기록
- 만성질환 관리
- 처방전 비교 분석

### 구현 세부사항

#### 데이터 모델
```python
@dataclass
class PatientRecord:
    """환자 기본 정보"""
    patient_id: str                    # 고유 ID (해시화된 이름+생년월일)
    name: str                          # 환자명
    age: int                          # 나이
    sex: str                          # 성별
    phone: str                        # 연락처 (선택)
    created_at: datetime              # 생성일
    last_updated: datetime            # 마지막 업데이트

@dataclass
class PrescriptionHistory:
    """처방전 이력"""
    prescription_id: str              # 고유 ID
    patient_id: str                   # 환자 ID
    prescription_date: date           # 처방일
    medications: List[Dict]           # 약물 목록
    diagnoses: List[str]             # 진단
    notes: str                        # 의료진 메모
    filepath: str                     # 원본 이미지 경로

@dataclass
class MedicationAllergy:
    """약물 알레르기 기록"""
    patient_id: str
    drug_name: str
    reaction: str                     # 알레르기 반응 설명
    severity: str                     # mild/moderate/severe
    recorded_date: datetime
    notes: str

@dataclass
class ChronicCondition:
    """만성질환 기록"""
    patient_id: str
    condition_name: str               # 질환명
    diagnosed_date: date              # 진단일
    status: str                       # active/inactive
    medications: List[str]            # 현재 약물
    notes: str
```

#### 저장소 구현
```
pharma_patients/
├── patient_{patient_id}.json         # 환자 기본 정보
├── history_{patient_id}.json         # 처방전 이력 (배열)
├── allergies_{patient_id}.json       # 알레르기 기록
└── conditions_{patient_id}.json      # 만성질환 기록
```

#### 핵심 메서드
```python
class PatientHistoryManager:
    """환자 이력 관리"""
    
    def create_or_get_patient(name: str, age: int, sex: str) -> str:
        """환자 ID 생성/조회"""
    
    def add_prescription_history(patient_id: str, prescription_data: Dict) -> bool:
        """처방전 이력 추가"""
    
    def get_prescription_history(patient_id: str, limit: int = 10) -> List[Dict]:
        """처방전 이력 조회 (최근 N개)"""
    
    def add_medication_allergy(patient_id: str, drug_name: str, reaction: str, severity: str) -> bool:
        """약물 알레르기 기록"""
    
    def get_medication_allergies(patient_id: str) -> List[Dict]:
        """알레르기 조회"""
    
    def check_drug_allergy(patient_id: str, drug_name: str) -> Optional[Dict]:
        """특정 약물 알레르기 확인"""
    
    def add_chronic_condition(patient_id: str, condition_name: str, medications: List[str]) -> bool:
        """만성질환 기록"""
    
    def get_chronic_conditions(patient_id: str) -> List[Dict]:
        """만성질환 조회"""
    
    def compare_prescriptions(patient_id: str, prescription_id_1: str, prescription_id_2: str) -> Dict:
        """두 처방전 비교 (약물 변화, 용량 변화 등)"""
```

#### 오케스트레이터 통합
```python
# agent_orchestrator.py에 추가

def process_prescription_with_history(image_path: str, patient_id: Optional[str] = None) -> Dict:
    """처방전 처리 + 이력 저장"""
    
    # 1. 처방전 분석 (기존)
    prescription_data = self.ocr_agent.analyze_prescription_image(image_path)
    
    # 2. 환자 이력 관리
    if patient_id is None:
        patient_id = self.history_manager.create_or_get_patient(
            name=prescription_data['patient']['name'],
            age=prescription_data['patient']['age'],
            sex=prescription_data['patient']['sex']
        )
    
    # 3. 알레르기 확인
    for med in prescription_data['medications']:
        allergy = self.history_manager.check_drug_allergy(patient_id, med['name'])
        if allergy:
            report['warnings'].append(f"⚠️ 알레르기 주의: {med['name']} - {allergy['reaction']}")
    
    # 4. 이력에 저장
    self.history_manager.add_prescription_history(patient_id, prescription_data)
    
    # 5. 비교 분석 (최근 처방전과 비교)
    prev_prescriptions = self.history_manager.get_prescription_history(patient_id, limit=2)
    if len(prev_prescriptions) > 1:
        comparison = self.history_manager.compare_prescriptions(...)
        report['comparison'] = comparison
    
    return report
```

### UI 통합 (Streamlit)
```python
# main_app_v2_agents.py에 추가된 탭

with tab4:  # "📋 환자 이력"
    st.header("환자 처방전 이력")
    
    # 환자 검색
    patient_name = st.text_input("환자명 검색")
    
    if patient_name:
        patient_id = history_manager.find_patient_by_name(patient_name)
        
        if patient_id:
            # 기본 정보
            st.subheader("기본 정보")
            patient_info = history_manager.get_patient_info(patient_id)
            col1, col2, col3 = st.columns(3)
            col1.metric("나이", patient_info['age'])
            col2.metric("성별", patient_info['sex'])
            col3.metric("처방전 수", len(history_manager.get_prescription_history(patient_id)))
            
            # 알레르기
            st.subheader("약물 알레르기")
            allergies = history_manager.get_medication_allergies(patient_id)
            if allergies:
                for allergy in allergies:
                    st.warning(f"🚨 {allergy['drug_name']}: {allergy['reaction']} ({allergy['severity']})")
            else:
                st.info("기록된 알레르기 없음")
            
            # 처방전 이력
            st.subheader("처방전 이력")
            prescriptions = history_manager.get_prescription_history(patient_id)
            for px in prescriptions:
                with st.expander(f"{px['date']} - {len(px['medications'])}개 약물"):
                    for med in px['medications']:
                        st.write(f"- {med['name']} ({med['strength']})")
            
            # 만성질환
            st.subheader("만성질환")
            conditions = history_manager.get_chronic_conditions(patient_id)
            if conditions:
                for condition in conditions:
                    st.info(f"🏥 {condition['name']} (진단: {condition['diagnosed_date']})")
```

### 성능 고려사항
- JSON 파일 대신 SQLite 사용 고려 (1000+ 환자 시)
- 환자 ID 암호화 (개인정보보호)
- 접근 로깅 (감시 추적)

---

## 기능 2️⃣: 실시간 약가 업데이트

### 목표
MFDS 공시약가를 실시간으로 갱신하여:
- 최신 약가 제공
- 약가 변화 추적
- 환자에게 정확한 가격 정보 제시
- 약국별 가격 비교 (향후)

### 구현 세부사항

#### 약가 데이터 모델
```python
@dataclass
class DrugPrice:
    """약가 정보"""
    drug_id: str
    korean_name: str
    english_name: str
    strength: str
    mfds_official_price: float        # MFDS 공시약가
    last_updated: datetime            # 마지막 업데이트
    update_source: str                # "MFDS API" / "Local Cache"
    price_history: List[Dict]         # 가격 변화 이력
    
@dataclass
class PriceHistory:
    """가격 변화"""
    date: datetime
    price: float
    source: str
```

#### 약가 관리자
```python
class DrugPriceManager:
    """약가 실시간 관리"""
    
    def __init__(self):
        self.cache = {}                # 메모리 캐시
        self.last_sync: datetime = None # 마지막 동기화
        self.sync_interval: int = 3600  # 1시간마다 갱신
    
    def get_current_price(drug_name: str, force_refresh: bool = False) -> Optional[float]:
        """현재 약가 조회"""
        
        # 1. 캐시 확인
        if drug_name in self.cache:
            cached = self.cache[drug_name]
            if not force_refresh and self._is_fresh(cached['timestamp']):
                return cached['price']
        
        # 2. MFDS API 호출
        price = self._fetch_from_mfds(drug_name)
        if price:
            # 3. 캐시 업데이트
            self.cache[drug_name] = {
                'price': price,
                'timestamp': datetime.now(),
                'source': 'MFDS API'
            }
            # 4. 이력 저장
            self._save_price_history(drug_name, price)
            return price
        
        # 5. 폴백: 로컬 DB
        return self._get_from_local_db(drug_name)
    
    def get_price_history(drug_name: str, days: int = 30) -> List[Dict]:
        """가격 변화 추적 (N일간)"""
    
    def sync_all_prices(self) -> Dict[str, any]:
        """모든 약가 동기화 (배경 작업)"""
        
        start_time = time.time()
        updated_count = 0
        failed_count = 0
        
        drugs = self._get_all_drugs()
        
        for drug in drugs:
            try:
                price = self._fetch_from_mfds(drug['name'])
                if price:
                    self.cache[drug['name']] = {
                        'price': price,
                        'timestamp': datetime.now()
                    }
                    updated_count += 1
            except Exception as e:
                failed_count += 1
        
        self.last_sync = datetime.now()
        
        return {
            'total': len(drugs),
            'updated': updated_count,
            'failed': failed_count,
            'duration_sec': time.time() - start_time
        }
    
    def _fetch_from_mfds(drug_name: str) -> Optional[float]:
        """MFDS API에서 약가 조회"""
        try:
            response = requests.get(
                f"https://api.mfds.go.kr/drug/price",
                params={'name': drug_name},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('price')
            return None
        except Exception as e:
            logger.error(f"MFDS API error: {e}")
            return None
```

#### 스케줄러 통합
```python
# 백그라운드 작업으로 정기적 동기화

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def scheduled_price_sync():
    """1시간마다 약가 동기화"""
    result = price_manager.sync_all_prices()
    logger.info(f"Price sync: {result['updated']}/{result['total']} updated")

scheduler.add_job(scheduled_price_sync, 'interval', hours=1)
scheduler.start()
```

#### 오케스트레이터 통합
```python
# agent_orchestrator.py의 약국 정보에 실시간 약가 추가

for pharmacy in pharmacies:
    pharmacy['drug_prices'] = {}
    for med in medications:
        price = price_manager.get_current_price(med['name'])
        pharmacy['drug_prices'][med['name']] = price
    pharmacy['estimated_total'] = sum(pharmacy['drug_prices'].values())
```

#### UI 통합
```python
# 처방약물 표시 시 약가 정보 추가

with st.expander(f"{med['name']} ({med['strength']})"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**MFDS 공시약가**: {med['price']}원")
        # 최종 업데이트 시간
        st.caption(f"마지막 업데이트: {med['last_updated']}")
    
    with col2:
        # 가격 변화 그래프
        history = price_manager.get_price_history(med['name'], days=30)
        if history:
            st.line_chart({
                'date': [h['date'] for h in history],
                'price': [h['price'] for h in history]
            })
```

---

## 기능 3️⃣: 다국어 지원

### 목표
시스템을 다국어로 지원하여:
- 영어 사용자 지원
- 다문화 의료 환경 대응
- 국제 확장성 제공
- 의료 용어 정확성 유지

### 지원 언어
- ✅ 한국어 (기본)
- ✅ 영어 (추가)
- ⏳ 중국어 (향후)
- ⏳ 일본어 (향후)

### 구현 방식

#### 번역 시스템
```python
class LanguageManager:
    """다국어 관리"""
    
    SUPPORTED_LANGUAGES = {
        'ko': '한국어',
        'en': 'English',
        'zh': '中文',
        'ja': '日本語'
    }
    
    TRANSLATIONS = {
        # 기본 UI 문자열
        'patient_info': {
            'ko': '환자 정보',
            'en': 'Patient Information',
            'zh': '患者信息',
            'ja': '患者情報'
        },
        'medications': {
            'ko': '처방약물',
            'en': 'Medications',
            'zh': '药物',
            'ja': '薬剤'
        },
        'pharmacies': {
            'ko': '근처 약국',
            'en': 'Nearby Pharmacies',
            'zh': '附近药房',
            'ja': '近くの薬局'
        },
        # 의료 용어
        'hypertension': {
            'ko': '고혈압',
            'en': 'Hypertension',
            'zh': '高血压',
            'ja': '高血圧'
        },
        'diabetes': {
            'ko': '당뇨',
            'en': 'Diabetes',
            'zh': '糖尿病',
            'ja': '糖尿病'
        },
        # 약물 복용법
        'once_daily': {
            'ko': '하루 1회',
            'en': 'Once daily',
            'zh': '每天一次',
            'ja': '1日1回'
        },
        'twice_daily': {
            'ko': '하루 2회',
            'en': 'Twice daily',
            'zh': '每天两次',
            'ja': '1日2回'
        },
        # 경고/안내
        'allergy_warning': {
            'ko': '약물 알레르기 주의!',
            'en': 'Drug Allergy Alert!',
            'zh': '药物过敏警告！',
            'ja': '薬物アレルギーアラート！'
        },
        'consult_doctor': {
            'ko': '의사와 상담하세요',
            'en': 'Please consult your doctor',
            'zh': '请咨询医生',
            'ja': '医者に相談してください'
        }
    }
    
    @staticmethod
    def get_text(key: str, language: str = 'ko') -> str:
        """텍스트 조회"""
        return LanguageManager.TRANSLATIONS.get(key, {}).get(language, key)
    
    @staticmethod
    def translate_drug_info(drug_info: Dict, language: str) -> Dict:
        """약물 정보 번역"""
        translated = drug_info.copy()
        
        # 약물명 매칭 및 번역
        if language != 'ko':
            # 영문명 사용
            translated['name'] = drug_info.get('english_name', drug_info.get('korean_name'))
        
        # 카테고리 번역
        if 'category' in translated:
            translated['category'] = LanguageManager.get_text(
                translated['category'].lower().replace(' ', '_'),
                language
            )
        
        return translated
```

#### Streamlit UI 다국어 지원
```python
# main_app_v2_agents.py 상단에 추가

# 언어 선택기
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("## 🌐 언어 선택 | Language Selection")

language = st.radio(
    "Select Language",
    ["한국어", "English"],
    horizontal=True,
    index=0
)

selected_lang = 'ko' if language == "한국어" else 'en'

# 모든 텍스트에 번역 적용
st.title(LanguageManager.get_text('patient_info', selected_lang))
st.header(LanguageManager.get_text('medications', selected_lang))
st.header(LanguageManager.get_text('pharmacies', selected_lang))

# 처방약물 표시
for med in medications:
    translated_med = LanguageManager.translate_drug_info(med, selected_lang)
    st.write(f"**{translated_med['name']}** - {translated_med.get('strength', '')}")
```

#### OCR 에이전트 다국어 출력
```python
# agent_ocr_vision.py의 시스템 프롬프트를 언어별로 변경

def get_system_prompt(language: str = 'ko') -> str:
    """언어별 시스템 프롬프트"""
    
    prompts = {
        'ko': """당신은 의료 처방전 이미지 분석 전문가입니다.
        
역할:
1. 처방전 이미지에서 환자 정보 추출 (이름, 나이, 성별, 진료일자)
2. 진료 병명 식별 (주진료, 부진료)
3. 처방약물 정보 추출 (약물명, 용량, 수량, 빈도)
4. 처방 정당성 검증 (의사 서명, 인장)

출력은 유효한 JSON 형식이어야 합니다.""",
        
        'en': """You are an expert medical prescription image analyzer.

Roles:
1. Extract patient information from prescription images (name, age, sex, date)
2. Identify diagnoses (primary, secondary)
3. Extract prescribed medication information (name, dose, quantity, frequency)
4. Validate prescription authenticity (doctor signature, seal)

Output must be in valid JSON format."""
    }
    
    return prompts.get(language, prompts['ko'])
```

#### RAG 에이전트 다국어 지원
```python
# agent_rag_drug.py에 약물 정보 번역 추가

def get_comprehensive_drug_info_multilingual(
    drug_name: str,
    language: str = 'ko',
    patient_age: Optional[int] = None,
    patient_conditions: Optional[List[str]] = None
) -> Optional[Dict]:
    """다국어 약물 정보"""
    
    # 기본 약물 정보 조회
    drug_info = self.search_drug_info(drug_name)
    if not drug_info:
        return None
    
    # 언어에 따라 이름 선택
    if language == 'en':
        name = drug_info.get('english_name', drug_info.get('korean_name'))
    else:
        name = drug_info.get('korean_name')
    
    # 카테고리, 부작용 등 번역
    translated_info = drug_info.copy()
    translated_info['name_display'] = name
    translated_info['category'] = LanguageManager.get_text(
        drug_info.get('category', '').lower().replace(' ', '_'),
        language
    )
    
    return translated_info
```

---

## 구현 순서 및 시간 추정

| 기능 | 추정 시간 | 파일 수 | 상태 |
|------|---------|--------|------|
| **1. 환자 이력** | 3-4시간 | 2-3개 | ⏳ TODO |
| **2. 실시간 약가** | 2-3시간 | 1-2개 | ⏳ TODO |
| **3. 다국어** | 2-3시간 | 1-2개 | ⏳ TODO |
| **통합 & 테스트** | 2시간 | - | ⏳ TODO |
| **총계** | **9-12시간** | **4-7개** | ⏳ TODO |

---

## 다음 단계 (옵션 D로)

옵션 C 완료 후 **옵션 D: 배포 준비**로 진행하여:
- Docker 컨테이너화
- Kubernetes 배포 매니페스트
- 운영 매뉴얼
- 모니터링/알림 설정

---

**준비 상태:** 옵션 C 구현 준비 완료  
**예상 완료:** 오늘 오후/내일 오전  
**다음 단계:** 옵션 D로 진행

