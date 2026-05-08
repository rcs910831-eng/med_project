import json
from typing import Dict, List
from privacy_guard import privacy_guard
from logic_resolver import logic_resolver
from vision_engine import VisionEngine

class MedicalAgent:
    """
    [med] 하이브리드 AI 약료 에이전트 - 중앙 엔진
    30년 경력 베테랑의 지혜를 알고리즘화한 시스템입니다.
    VLM과 OCR 등 시각 지능 모듈을 결합하여 복합적인 환자 정보를 분석합니다.
    """

    def __init__(self, knowledge_base_path: str = "knowledge_base.json"):
        try:
            with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                self.kb = json.load(f)
        except FileNotFoundError:
            self.kb = {"hospitals": [], "drugs": [], "lifestyle_coaching": {}}
            print("[Warning] knowledge_base.json이 없어 빈 DB로 초기화합니다.")
        
        # 비전 엔진 초기화 (OCR + VLM)
        self.vision = VisionEngine(llm_type="gemini")

    # --- 1단계: [기상 & 감지] Visual Intake Node ---
    def bio_scanning(self, user_dna_info: Dict, camera_feed_data: Dict) -> Dict:
        """
        VLM 기반 안면 및 손 데이터 분석 (시뮬레이션 유지)
        """
        print("[Node 1] 모닝 바이오 스캐닝 시작...")
        vulnerability = user_dna_info.get("vulnerabilities")
        edema_level = camera_feed_data.get("edema_value", 0.0)
        
        message = "평상시와 비슷한 컨디션입니다."
        if vulnerability == "kidney" and edema_level > 0.05:
            message = f"유전적 신장 저하 요인이 있어 부종을 정밀 관찰했습니다. 안색이 {int(edema_level*100)}% 어둡고 부어있습니다."
            
        return {
            "stage": 1,
            "analysis": message
        }

    # --- 2단계: [처방 & 확인] Semantic Extraction Node (VLM & OCR 연동) ---
    def analyze_prescription(self, prescription_img_path: str, pill_img_path: str) -> Dict:
        """
        OCR과 VLM을 활용한 시각지능 결합 약료 판독.
        실제 처방전 이미지와 약 이미지를 Vision Engine에 넘깁니다.
        """
        print("[Node 2] 처방전(OCR) 및 알약(VLM) 이중 판독 중...")
        
        # 1. Vision Engine 구동
        vision_result = self.vision.process_hybrid_vision(prescription_img_path, pill_img_path)
        
        # 2. 로컬 프라이버시 마스킹 (OCR로 추출된 텍스트에서 개인정보 지우기)
        raw_ocr = vision_result.get("ocr_text", "")
        masked_prescription_text = privacy_guard.mask_rrn(raw_ocr)
        
        # 3. LLM 페르소나 분석 (시각 데이터 요약) - 논리 충돌 회피용 단순화
        vlm_data = vision_result.get("vlm_analysis", {})
        
        # Mock 로직 연동 (실제 추출값 기반)
        ocr_extracted_drug = "리리카캡슐" if "리리카캡슐" in masked_prescription_text else "처방약 인식불가"
        vlm_detected_drug = vlm_data.get("detected_drug", "식별불가 약물")
        
        ocr_simulated = {"drug_name": ocr_extracted_drug, "source": "OCR 처방전"}
        vlm_simulated = {"detected_drug": vlm_detected_drug, "mark": vlm_data.get("mark")}
        
        # 논리 엔진으로 처방전 약과 실제 낱알 약이 같은지 교차 검증
        resolution = logic_resolver.resolve_prescription_conflict(ocr_simulated, vlm_simulated)
        
        return {
            "stage": 2,
            "masked_prescription_text": masked_prescription_text,
            "vlm_pill_data": vlm_data,
            "verification_result": resolution
        }

    # --- 3단계: [심화 분석] Intelligence Hub Node (RAG) ---
    def deep_analysis(self, drug_name: str, ct_mri_report: str) -> Dict:
        """경량 JSON RAG 기반 심화 분석"""
        print("[Node 3] 초정밀 데이터 매칭 (RAG) 중...")
        drug_info = next((d for d in self.kb.get("drugs", []) if d.get("name") == drug_name), {})
        
        insights = []
        if "간" in ct_mri_report and "liver" in drug_info.get("interactions", {}):
            insights.append(f"CT상 간 수치가 경계선에 있으니 {drug_name} 복용 시 음주를 피하고 밀크씨슬과 3시간 간격을 두세요. (30년 경력 약사 조언)")
            
        return {
            "stage": 3,
            "drug_info": drug_info,
            "expert_insights": insights
        }

    # --- 4단계 및 5단계 생략 (기존 노트북 테스트 유지 호환용) ---
    def run(self, user_query: str):
        # 기본 LLM 호출용 호환성 메서드
        return f"[Pharmacist AI] 증상({user_query})이 확인되었습니다. 자세한 분석을 위해 처방전 사진을 업로드해주세요."

if __name__ == "__main__":
    agent = MedicalAgent()
    print("30년 경력 약사 AI가 비전 지능(OCR+VLM)을 장착하여 준비되었습니다.")
