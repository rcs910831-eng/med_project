import json
import os

class DatasetLoader:
    def __init__(self, db_root='C:/PharmaProject/database', legacy_kb_path='knowledge_base.json', kb_path=None):
        self.db_root = db_root
        self.legacy_kb_path = kb_path if kb_path is not None else legacy_kb_path
        self.kb = self._load_database()

    def _load_database(self):
        """
        [마이그레이션 로직] 
        C:/PharmaProject/database 하위의 분산된 데이터들을 통합하여 
        기존 시스템과 호환될 수 있는 kb 객체를 생성합니다.
        """
        db = {"hospitals": [], "drugs": [], "lifestyle_coaching": {}}
        
        # 1. 마스터 데이터 (약물 & 병원)
        master_path = os.path.join(self.db_root, "master_data")
        try:
            # Drugs 로드
            with open(os.path.join(master_path, "drugs.json"), 'r', encoding='utf-8') as f:
                db["drugs"] = json.load(f)
            # Hospitals 로드
            with open(os.path.join(master_path, "hospitals.json"), 'r', encoding='utf-8') as f:
                db["hospitals"] = json.load(f)
        except FileNotFoundError:
            print(f"[Warning] 신규 DB 경로({master_path})를 찾을 수 없어 레거시 파일을 시도합니다.")
            return self._load_legacy_kb()

        # 2. 임상 데이터 (가이드라인)
        clinical_path = os.path.join(self.db_root, "clinical", "clinical_rules.json")
        try:
            with open(clinical_path, 'r', encoding='utf-8') as f:
                clinical_data = json.load(f)
                db["lifestyle_coaching"] = clinical_data.get("lifestyle_coaching", {})
        except FileNotFoundError:
            pass

        return db

    def _load_legacy_kb(self):
        """기존 knowledge_base.json 로드 (폴백 용도)"""
        if not os.path.exists(self.legacy_kb_path):
            return {"drugs": []}
        with open(self.legacy_kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_patient(self, patient_id):
        """특정 환자 정보를 DB에서 로드합니다."""
        patient_path = os.path.join(self.db_root, "patients", f"{patient_id}.json")
        if os.path.exists(patient_path):
            with open(patient_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def find_drug_by_visual(self, detected_features):
        """
        VLM이 감지한 특징(form, color, imprint 등)을 기반으로 약물을 검색합니다.
        detected_features: dict (e.g., {'color': '청색', 'form': '연질캡슐'})
        """
        matches = []
        for drug in self.kb.get('drugs', []):
            viz = drug.get('visual_descriptors', {})
            score = 0
            for key, val in detected_features.items():
                if key in viz and val in viz[key]:
                    score += 1
            if score > 0:
                matches.append((score, drug))
        
        # 가장 점수가 높은 순으로 정렬
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1] if matches else None

    def find_drug_by_text(self, ocr_text):
        """
        OCR이 추출한 텍스트 키워드를 기반으로 약물을 검색합니다.
        ocr_text: str (약 봉투에서 읽은 텍스트)
        """
        for drug in self.kb.get('drugs', []):
            keywords = drug.get('packaging_text_samples', [])
            for kw in keywords:
                if kw in ocr_text:
                    return drug
        return None

    def cross_verify(self, ocr_data, vlm_data):
        """
        30년 경력 약사의 하이브리드 검수 로직:
        약 봉투에 적힌 정보(OCR)와 실제 알약의 외관(VLM)이 일치하는지 확인합니다.
        """
        drug_from_text = self.find_drug_by_text(ocr_data)
        drug_from_visual = self.find_drug_by_visual(vlm_data)

        if not drug_from_text or not drug_from_visual:
            return {
                "status": "warning",
                "message": "⚠️ 데이터 부족: 하나 이상의 소스에서 약물을 식별할 수 없습니다. 처방전과 알약을 다시 한 번 확인해주세요."
            }

        if drug_from_text['name'] == drug_from_visual['name']:
            return {
                "status": "success",
                "drug": drug_from_text,
                "message": f"✅ 검수 완료: 봉투의 정보와 실제 알약이 '{drug_from_text['name']}'으로 일치합니다. 안심하고 복용하세요."
            }
        else:
            return {
                "status": "critical",
                "message": f"🚨 30년 경력 약사 경고 (조제 오류 가능성!): 약 봉투에는 '{drug_from_text['name']}'으로 적혀있으나, 실제 알약은 '{drug_from_visual['name']}'으로 보입니다. 복용을 즉시 중단하고 약국에 문의하세요!"
            }

if __name__ == "__main__":
    # 간단한 테스트
    loader = DatasetLoader()
    
    # 시나리오 1: 정상 (타이레놀 봉투 + 타이레놀 알약)
    res1 = loader.cross_verify("이 약은 타이레놀입니다.", {"color": "흰색", "shape": "장방형"})
    print(res1['message'])

    # 시나리오 2: 조제 오류 (타이레놀 봉투 + 탁센 알약)
    res2 = loader.cross_verify("해열진통제 타이레놀 500mg", {"color": "청색", "form": "연질캡슐"})
    print(res2['message'])
