from typing import Dict, Optional

class LogicResolver:
    """
    30년 경력 베테랑의 '직관'이 담긴 충돌 해결 엔진.
    단순한 데이터 비교를 넘어 환자의 안전을 최우선으로 하는 행동 지침을 제공합니다.
    """

    def resolve_prescription_conflict(self, ocr_data: Dict, vlm_pill_data: Dict) -> Dict:
        """
        처방전 텍스트(OCR)와 알약 이미지 분석 결과(VLM)를 대조합니다.
        불일치 시 '베테랑 약사'의 행동 지침을 생성합니다.
        """
        ocr_drug = ocr_data.get("drug_name")
        vlm_drug = vlm_pill_data.get("detected_drug")

        if ocr_drug == vlm_drug:
            return {
                "status": "MATCH",
                "message": f"처방전과 조제된 약이 일치합니다. ({ocr_drug})",
                "action": "PROCEED"
            }
        else:
            # 30년 경력 베테랑의 직관적 메시지
            advice = (
                f"[약사 확인 필요] 처방전에는 '{ocr_drug}'(으)로 적혀 있으나, "
                f"실제 약은 '{vlm_drug}'(으)로 보입니다. 오조제 가능성이 있으니 "
                f"약국 조제실에 반드시 다시 문의하시기 바랍니다."
            )
            return {
                "status": "CONFLICT",
                "message": advice,
                "action": "STOP_AND_VALDIATE",
                "expert_flag": True
            }

    def evaluate_bio_priority(self, dna_info: Dict, scan_results: Dict) -> Dict:
        """
        유전적 취약성과 현재 스캔 결과를 결합하여 정밀 관찰 가중치를 부여합니다.
        """
        priorities = []
        if dna_info.get("vulnerabilities") == "kidney" and scan_results.get("edema_level", 0) > 0.3:
            priorities.append("신장 부종 집중 모니터링")
        
        return {
            "focused_areas": priorities,
            "system_weight": "HIGH" if priorities else "NORMAL"
        }

# 싱글톤 인스턴스
logic_resolver = LogicResolver()
