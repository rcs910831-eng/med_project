"""
Agent 2: RAG & Drug Information Specialist
의약정보 검색 및 임상 가이드라인 제공
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AgentRAGDrug:
    """RAG & 약물정보 전문가"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG Drug Agent

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-7"

        # Load RAG databases
        self.drug_info = self._load_json("rag_db/drug_info_index.json")
        self.papers = self._load_json("rag_db/papers_metadata.json")
        self.guidelines = self._load_json("rag_db/guidelines_index.json")

        self.system_prompt = """당신은 의약정보 검색 및 임상 가이드라인 전문가입니다.

역할:
1. 약물명 → MFDS DB, 논문, 가이드라인에서 정보 검색
2. 1일 권장량 및 투여 횟수 조회
3. 1일 투여량 계산
4. 부작용 및 주의사항 조회
5. 약물 상호작용 검토
6. 환자 연령/상태별 특수 고려사항 제공

데이터 출처 (우선순위):
- 제공된 RAG 데이터베이스 (로컬)
- MFDS 공식 정보 (한국 FDA)
- 임상논문 및 가이드라인
- 의료 전문가 권고사항
"""

        logger.info("AgentRAGDrug initialized")

    def _load_json(self, filepath: str) -> Optional[Dict]:
        """Load JSON file from RAG database"""
        try:
            path = Path(filepath)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            logger.warning(f"File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return None

    def search_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Search drug information from RAG database

        Args:
            drug_name: Drug name (Korean or English)

        Returns:
            Dictionary with comprehensive drug information
        """
        try:
            if not self.drug_info:
                logger.error("Drug info database not loaded")
                return None

            # Search in drug database
            drugs = self.drug_info.get("drugs", [])

            matching_drug = None
            for drug in drugs:
                if (drug_name.lower() in drug.get("korean_name", "").lower() or
                    drug_name.lower() in drug.get("english_name", "").lower()):
                    matching_drug = drug
                    break

            if not matching_drug:
                logger.warning(f"Drug not found: {drug_name}")
                return None

            logger.info(f"Found drug: {matching_drug.get('korean_name')}")
            return matching_drug

        except Exception as e:
            logger.error(f"Error searching drug: {e}")
            return None

    def search_related_papers(self, drug_name: str) -> List[Dict]:
        """
        Search related clinical papers

        Args:
            drug_name: Drug name

        Returns:
            List of related papers
        """
        try:
            if not self.papers:
                return []

            papers = self.papers.get("papers", [])
            related_papers = []

            for paper in papers:
                if drug_name.lower() in str(paper.get("drug_references", [])).lower():
                    related_papers.append(paper)

            logger.info(f"Found {len(related_papers)} papers for {drug_name}")
            return related_papers

        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []

    def search_guidelines(self, disease_name: str) -> List[Dict]:
        """
        Search clinical guidelines for disease

        Args:
            disease_name: Disease name

        Returns:
            List of relevant guidelines
        """
        try:
            if not self.guidelines:
                return []

            guidelines = self.guidelines.get("guidelines", [])
            relevant_guidelines = []

            for guideline in guidelines:
                if disease_name.lower() in guideline.get("disease", "").lower():
                    relevant_guidelines.append(guideline)

            logger.info(f"Found {len(relevant_guidelines)} guidelines for {disease_name}")
            return relevant_guidelines

        except Exception as e:
            logger.error(f"Error searching guidelines: {e}")
            return []

    def check_drug_interactions(self, drug_names: List[str]) -> Dict:
        """
        Check for drug interactions

        Args:
            drug_names: List of drug names

        Returns:
            Dictionary with interaction information
        """
        try:
            if not self.drug_info:
                return {}

            interactions = {}
            drugs = self.drug_info.get("drugs", [])

            # Create drug lookup
            drug_map = {}
            for drug in drugs:
                korean = drug.get("korean_name", "").lower()
                english = drug.get("english_name", "").lower()
                drug_map[korean] = drug
                drug_map[english] = drug

            # Check interactions between each pair
            for i, drug1_name in enumerate(drug_names):
                for drug2_name in drug_names[i+1:]:
                    drug1 = drug_map.get(drug1_name.lower())
                    drug2 = drug_map.get(drug2_name.lower())

                    if drug1 and drug2:
                        interaction_key = f"{drug1.get('korean_name')} + {drug2.get('korean_name')}"
                        drug1_interactions = drug1.get("interactions", {})

                        interaction_info = drug1_interactions.get(
                            drug2_name.lower(),
                            drug1_interactions.get(
                                drug2.get("active_ingredient", "").lower(),
                                "상호작용 정보 없음"
                            )
                        )

                        interactions[interaction_key] = {
                            "drug1": drug1.get("korean_name"),
                            "drug2": drug2.get("korean_name"),
                            "interaction": interaction_info,
                            "severity": self._determine_severity(interaction_info)
                        }

            logger.info(f"Checked interactions for {len(drug_names)} drugs")
            return interactions

        except Exception as e:
            logger.error(f"Error checking interactions: {e}")
            return {}

    def get_comprehensive_drug_info(self, drug_name: str, patient_age: int = None,
                                   patient_conditions: List[str] = None) -> Optional[Dict]:
        """
        Get comprehensive drug information with patient-specific considerations

        Args:
            drug_name: Drug name
            patient_age: Patient age (optional)
            patient_conditions: Patient conditions (optional)

        Returns:
            Comprehensive drug information dictionary
        """
        try:
            # Get basic drug info
            drug_info = self.search_drug_info(drug_name)
            if not drug_info:
                return None

            # Get related papers
            papers = self.search_related_papers(drug_name)

            result = {
                "drug": drug_info,
                "related_papers": papers[:3],  # Top 3 papers
                "special_considerations": []
            }

            # Add age-specific considerations
            if patient_age:
                if patient_age >= 65:
                    result["special_considerations"].append({
                        "category": "고령자",
                        "note": drug_info.get("elderly_special_notes", "정기적 모니터링 권고")
                    })

                if patient_age < 18:
                    result["special_considerations"].append({
                        "category": "미성년자",
                        "note": "의료 전문가 상담 필수"
                    })

            # Add condition-specific considerations
            if patient_conditions:
                for condition in patient_conditions:
                    if condition.lower() == "pregnancy":
                        result["special_considerations"].append({
                            "category": "임신",
                            "note": f"FDA Category: {drug_info.get('pregnancy_category', 'C')}",
                            "warning": self._get_pregnancy_warning(drug_info.get("pregnancy_category"))
                        })

                    if condition.lower() == "kidney":
                        result["special_considerations"].append({
                            "category": "신부전",
                            "note": drug_info.get("renal_impairment", "용량 조정 가능")
                        })

                    if condition.lower() == "liver":
                        result["special_considerations"].append({
                            "category": "간질환",
                            "note": drug_info.get("hepatic_impairment", "용량 조정 가능")
                        })

            logger.info(f"Generated comprehensive info for {drug_name}")
            return result

        except Exception as e:
            logger.error(f"Error generating comprehensive info: {e}")
            return None

    def validate_medication_safety(self, medications: List[Dict], patient_age: int = None,
                                  patient_conditions: List[str] = None) -> Dict:
        """
        Validate medication safety for patient

        Args:
            medications: List of medications
            patient_age: Patient age
            patient_conditions: Patient conditions

        Returns:
            Safety validation report
        """
        try:
            report = {
                "safe": True,
                "warnings": [],
                "errors": [],
                "recommendations": []
            }

            drug_names = [med.get("name") for med in medications if med.get("name")]

            # Check drug interactions
            interactions = self.check_drug_interactions(drug_names)
            for interaction_key, interaction_data in interactions.items():
                if "위험" in interaction_data.get("interaction", ""):
                    report["errors"].append(f"경고: {interaction_key} - {interaction_data.get('interaction')}")
                    report["safe"] = False
                elif "주의" in interaction_data.get("interaction", ""):
                    report["warnings"].append(f"주의: {interaction_key} - {interaction_data.get('interaction')}")

            # Check age-specific safety
            if patient_age:
                if patient_age >= 75:
                    report["warnings"].append("고령자(75세 이상): 정기적인 신기능, 간기능 검사 필수")

            # Check condition-specific safety
            if patient_conditions:
                for med in medications:
                    drug_info = self.search_drug_info(med.get("name", ""))
                    if drug_info:
                        contraindications = drug_info.get("contraindications", [])
                        for condition in patient_conditions:
                            if condition.lower() in str(contraindications).lower():
                                report["errors"].append(
                                    f"금기: {med.get('name')} - {condition} 환자에게 금기"
                                )
                                report["safe"] = False

            logger.info(f"Medication safety validation complete. Safe: {report['safe']}")
            return report

        except Exception as e:
            logger.error(f"Error validating safety: {e}")
            return {"safe": False, "errors": [str(e)]}

    def generate_drug_explanation(self, drug_name: str, dose: str, frequency: str,
                                 duration: int) -> str:
        """
        Generate patient-friendly drug explanation

        Args:
            drug_name: Drug name
            dose: Dosage
            frequency: Frequency
            duration: Duration in days

        Returns:
            Formatted explanation
        """
        try:
            drug_info = self.search_drug_info(drug_name)
            if not drug_info:
                return "약물 정보를 찾을 수 없습니다."

            explanation = f"""
약물명: {drug_info.get('korean_name')} ({drug_info.get('english_name')})

처방내용:
- 용량: {dose}
- 복용횟수: {frequency}
- 복용기간: {duration}일

작용:
{drug_info.get('category', '')}으로 사용됩니다.

부작용:
"""
            for side_effect in drug_info.get("side_effects", [])[:3]:
                explanation += f"- {side_effect}\n"

            explanation += f"""
주의사항:
"""
            for warning in drug_info.get("warnings", [])[:3]:
                explanation += f"- {warning}\n"

            explanation += """
더 자세한 정보는 의료 전문가와 상담하세요.
"""
            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "약물 설명을 생성할 수 없습니다."

    @staticmethod
    def _determine_severity(interaction_text: str) -> str:
        """Determine interaction severity"""
        text_lower = interaction_text.lower()
        if "금기" in text_lower or "절대" in text_lower:
            return "critical"
        elif "위험" in text_lower or "높음" in text_lower:
            return "high"
        elif "주의" in text_lower or "중간" in text_lower:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _get_pregnancy_warning(category: str) -> str:
        """Get pregnancy warning based on FDA category"""
        warnings = {
            "A": "안전함 - 인체 임상시험에서 위험성 없음",
            "B": "상대적으로 안전함 - 동물 실험에서 안전, 인체 자료 제한적",
            "C": "위험 가능성 - 의사와 상담 필수",
            "D": "금기 - 기형 유발 위험",
            "X": "절대 금기 - 기형/유산 위험"
        }
        return warnings.get(category, "불명 - 의사와 상담하세요")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    try:
        agent = AgentRAGDrug()

        # Test 1: Search drug info
        drug_info = agent.search_drug_info("노바스크정")
        if drug_info:
            print(f"\n약물: {drug_info.get('korean_name')}")
            print(f"1일 권장량: {drug_info.get('recommended_daily_dose')}")

        # Test 2: Search papers
        papers = agent.search_related_papers("아밀로디핀")
        print(f"\n관련 논문: {len(papers)}개")

        # Test 3: Check interactions
        interactions = agent.check_drug_interactions(
            ["노바스크정", "글루코판정"]
        )
        print(f"\n약물 상호작용: {len(interactions)}개")

        # Test 4: Comprehensive info
        comp_info = agent.get_comprehensive_drug_info(
            "노바스크정",
            patient_age=68,
            patient_conditions=["hypertension"]
        )
        if comp_info:
            print(f"\n특수 고려사항: {len(comp_info.get('special_considerations', []))}개")

    except Exception as e:
        print(f"Error: {e}")
