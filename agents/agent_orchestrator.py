"""
Agent 4: Orchestrator & Final Report Generator
모든 에이전트 결과 통합 및 최종 보고서 생성
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os

from anthropic import Anthropic
from agents.agent_ocr_vision import AgentOCRVision
from agents.agent_rag_drug import AgentRAGDrug
from agents.agent_google_pharmacy import AgentGooglePharmacy
from utils.pdf_generator import PDFReportGenerator
from utils.tts_handler import TTSHandler
from utils.validators import MedicationValidator, PrescriptionValidator

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """오케스트레이터 & 최종 보고서 생성"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Orchestrator Agent

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-7"

        # Initialize sub-agents (optional)
        self.ocr_agent = None
        self.rag_agent = None
        self.pharmacy_agent = None

        try:
            self.ocr_agent = AgentOCRVision(api_key=self.api_key)
            logger.info("OCR Agent initialized")
        except Exception as e:
            logger.warning(f"OCR Agent init failed: {e}")

        try:
            self.rag_agent = AgentRAGDrug(api_key=self.api_key)
            logger.info("RAG Drug Agent initialized")
        except Exception as e:
            logger.warning(f"RAG Agent init failed: {e}")

        try:
            self.pharmacy_agent = AgentGooglePharmacy(api_key=self.api_key)
            logger.info("Pharmacy Agent initialized")
        except Exception as e:
            logger.warning(f"Pharmacy Agent init failed: {e}")

        # Initialize report generators
        self.pdf_generator = PDFReportGenerator()
        self.tts_handler = TTSHandler()

        self.system_prompt = """당신은 의료 정보 통합 및 최종 보고서 생성 전문가입니다.

역할:
1. Agent 1,2,3의 결과 통합
2. 데이터 일관성 검증
3. 약물 이미지 추가
4. 환자 맞춤형 경고 생성
5. PDF/HTML 보고서 생성
6. 음성 설명 스크립트 생성
7. 환자 이력 저장 (Memory Store)

최종 산출물:
- 구조화된 JSON 데이터
- PDF 의료 보고서
- HTML 웹 보고서
- 음성 설명 스크립트
"""

        logger.info("AgentOrchestrator initialized")

    def process_prescription_image(
        self,
        image_path: str,
        patient_location: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Full E2E prescription processing

        Args:
            image_path: Path to prescription image
            patient_location: {latitude, longitude, address}

        Returns:
            Comprehensive prescription report
        """
        try:
            logger.info(f"Processing prescription: {image_path}")

            # Step 1: OCR & Extract
            if not self.ocr_agent:
                logger.error("OCR Agent not available")
                return None

            prescription_data = self.ocr_agent.analyze_prescription_image(image_path)
            if not prescription_data:
                logger.error("Failed to extract prescription data")
                return None

            logger.info("✓ Step 1 complete: Prescription extracted")

            # Step 2: Drug Information Retrieval
            if not self.rag_agent:
                logger.error("RAG Agent not available")
                return None

            patient_info = prescription_data.get("patient", {})
            medications = prescription_data.get("medications", [])

            medication_details = []
            for med in medications:
                drug_info = self.rag_agent.get_comprehensive_drug_info(
                    med.get("name", ""),
                    patient_age=patient_info.get("age"),
                    patient_conditions=self._extract_conditions(patient_info)
                )

                if drug_info:
                    medication_details.append({
                        "prescribed": med,
                        "drug_info": drug_info["drug"],
                        "related_papers": drug_info.get("related_papers", []),
                        "special_considerations": drug_info.get("special_considerations", [])
                    })

            logger.info(f"✓ Step 2 complete: {len(medication_details)} drugs processed")

            # Step 3: Safety Validation
            safety_report = self.rag_agent.validate_medication_safety(
                medications,
                patient_age=patient_info.get("age"),
                patient_conditions=self._extract_conditions(patient_info)
            )

            logger.info(f"✓ Step 3 complete: Safety check {'PASSED' if safety_report['safe'] else 'WARNINGS'}")

            # Step 4: Pharmacy Search (if location provided)
            pharmacies = []
            if patient_location and self.pharmacy_agent:
                pharmacy_result = self.pharmacy_agent.get_full_pharmacy_search(
                    latitude=patient_location.get("latitude"),
                    longitude=patient_location.get("longitude"),
                    drug_names=[med.get("name") for med in medications],
                    radius_km=2,
                    max_results=10
                )

                if pharmacy_result.get("success"):
                    pharmacies = pharmacy_result.get("pharmacies", [])
                    logger.info(f"✓ Step 4 complete: {len(pharmacies)} pharmacies found")
                else:
                    logger.warning(f"Pharmacy search failed: {pharmacy_result.get('error')}")

            # Step 5: Generate Final Report
            final_report = self._generate_final_report(
                patient_info=patient_info,
                medications=medication_details,
                safety_report=safety_report,
                pharmacies=pharmacies,
                original_data=prescription_data
            )

            logger.info("✓ Step 5 complete: Final report generated")

            return final_report

        except Exception as e:
            logger.error(f"Error processing prescription: {e}")
            return None

    def _extract_conditions(self, patient_info: Dict) -> List[str]:
        """Extract medical conditions from patient info"""
        conditions = []

        diagnosis = patient_info.get("diagnosis_primary", "").lower()
        if "당뇨" in diagnosis or "diabetes" in diagnosis:
            conditions.append("diabetes")
        if "신" in diagnosis or "kidney" in diagnosis:
            conditions.append("kidney")
        if "간" in diagnosis or "liver" in diagnosis:
            conditions.append("liver")

        return conditions

    def _generate_final_report(
        self,
        patient_info: Dict,
        medications: List[Dict],
        safety_report: Dict,
        pharmacies: List[Dict],
        original_data: Dict
    ) -> Dict:
        """
        Generate comprehensive final report

        Args:
            patient_info: Patient information
            medications: Medication details
            safety_report: Safety validation results
            pharmacies: Nearby pharmacies
            original_data: Original prescription data

        Returns:
            Comprehensive report dictionary
        """
        try:
            # Map patient info for report generator
            patient_report_info = {
                "name": patient_info.get("name"),
                "age": patient_info.get("age"),
                "sex": patient_info.get("sex"),
                "primary_diagnosis": patient_info.get("diagnosis_primary"),
                "secondary_diagnosis": patient_info.get("diagnosis_secondary"),
                "prescription_date": original_data.get("metadata", {}).get("prescription_date", datetime.now().strftime("%Y-%m-%d"))
            }

            report = {
                "report_id": f"RX_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now().isoformat(),
                "patient": patient_report_info,
                "medications": self._format_medications(medications),
                "safety": safety_report,
                "pharmacies": pharmacies[:5],  # Top 5 pharmacies
                "warnings": self._generate_warnings(patient_info, medications, safety_report),
                "recommendations": self._generate_recommendations(medications),
                "meta": {
                    "total_medications": len(medications),
                    "total_estimated_cost": sum(
                        p.get("estimated_total", 0) for p in pharmacies
                    ) if pharmacies else 0,
                    "processing_complete": True
                }
            }

            return report

        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            return None

    def _format_medications(self, medications: List[Dict]) -> List[Dict]:
        """Format medication information for report"""
        formatted = []

        for med in medications:
            drug = med.get("drug_info", {})
            prescribed = med.get("prescribed", {})

            formatted_med = {
                "name": drug.get("korean_name"),
                "english_name": drug.get("english_name"),
                "strength": drug.get("strength"),
                "prescribed_dose": prescribed.get("strength"),
                "prescribed_quantity": prescribed.get("quantity"),
                "daily_dose": str(drug.get("recommended_daily_dose", "")),
                "frequency": prescribed.get("frequency", ""),
                "duration": prescribed.get("quantity", ""), # Fallback to quantity if duration not explicit
                "category": drug.get("category"),
                "price": drug.get("mfds_official_price"),
                "mfds_price": drug.get("mfds_official_price"),
                "side_effects": drug.get("side_effects", [])[:5],
                "warnings": ", ".join(drug.get("warnings", [])[:3]),
                "contraindications": drug.get("contraindications", []),
                "special_considerations": med.get("special_considerations", []),
                "related_papers": len(med.get("related_papers", []))
            }

            formatted.append(formatted_med)

        return formatted

    def _generate_warnings(
        self,
        patient_info: Dict,
        medications: List[Dict],
        safety_report: Dict
    ) -> List[str]:
        """Generate patient-specific warnings"""
        warnings = []

        # Age-based warnings
        age = patient_info.get("age", 0)
        if age >= 75:
            warnings.append("고령자(75세 이상): 정기적인 신기능/간기능 검사 필수")
        elif age >= 65:
            warnings.append("고령자(65세 이상): 저혈압 주의 필요")

        # Safety warnings
        if not safety_report.get("safe"):
            for error in safety_report.get("errors", []):
                warnings.append(f"⚠️ {error}")

        # Drug-specific warnings
        for med in medications:
            drug = med.get("drug_info", {})
            if drug.get("warnings"):
                warnings.extend(drug.get("warnings", [])[:2])

        return warnings[:10]  # Limit to 10 warnings

    def _generate_recommendations(self, medications: List[Dict]) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = [
            "의료 전문가의 처방 가이드에 따라 복용하세요",
            "정해진 시간에 일정하게 복용하세요",
            "음식과 함께 복용 여부는 약사에게 문의하세요"
        ]

        # Check for special considerations
        for med in medications:
            special = med.get("special_considerations", [])
            for item in special:
                if "고령" in str(item):
                    recommendations.append("정기적인 건강 검진 및 의사 상담 필수")
                    break

        return recommendations

    def generate_reports(
        self,
        report_data: Dict,
        output_dir: str = "./pharma_output"
    ) -> Dict:
        """
        Generate PDF, HTML, and voice reports

        Args:
            report_data: Comprehensive report data
            output_dir: Output directory

        Returns:
            Dictionary with file paths
        """
        try:
            files = {
                "json": None,
                "html": None,
                "pdf": None,
                "voice": None
            }

            # Save JSON
            json_file = f"{output_dir}/report_{report_data.get('report_id')}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            files["json"] = json_file
            logger.info(f"✓ JSON report: {json_file}")

            # Generate PDF
            patient = report_data.get("patient", {})
            medications = report_data.get("medications", [])
            pharmacies = report_data.get("pharmacies", [])
            warnings = report_data.get("warnings", [])

            pdf_file = self.pdf_generator.generate_report(
                patient_info=patient,
                medications=medications,
                pharmacies=pharmacies,
                warnings=warnings,
                filename=f"report_{report_data.get('report_id')}.pdf"
            )
            if pdf_file:
                files["pdf"] = pdf_file
                logger.info(f"✓ PDF report: {pdf_file}")

            # Generate HTML
            html_file = self.pdf_generator.generate_html_report(
                patient_info=patient,
                medications=medications,
                pharmacies=pharmacies,
                warnings=warnings,
                filename=f"report_{report_data.get('report_id')}.html"
            )
            if html_file:
                files["html"] = html_file
                logger.info(f"✓ HTML report: {html_file}")

            # Generate voice explanation
            try:
                voice_script = self._generate_voice_script(report_data)
                voice_file = f"{output_dir}/voice_{report_data.get('report_id')}.mp3"

                audio = self.tts_handler.synthesize_text(
                    voice_script,
                    language_code="ko-KR",
                    output_file=voice_file
                )

                if audio:
                    files["voice"] = voice_file
                    logger.info(f"✓ Voice report: {voice_file}")

            except Exception as e:
                logger.warning(f"Voice generation skipped: {e}")

            return files

        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            return {}

    def _generate_voice_script(self, report_data: Dict) -> str:
        """Generate voice explanation script"""
        patient = report_data.get("patient", {})
        medications = report_data.get("medications", [])

        script = f"""
{patient.get('name', '환자')}님의 처방약 정보를 설명드리겠습니다.

환자 정보:
나이는 {patient.get('age', '미상')}세, 성별은 {patient.get('sex', '미상')}입니다.
주된 진료 질환은 {patient.get('diagnosis_primary', '미상')}입니다.

처방 약물 정보입니다.
"""

        for idx, med in enumerate(medications[:3], 1):  # First 3 drugs only
            script += f"""
{idx}번 약물: {med.get('name', '')} {med.get('strength', '')}입니다.
약의 분류는 {med.get('category', '')}입니다.
주의할 점은 다음과 같습니다. """

            for warning in med.get("warnings", [])[:1]:
                script += f"{warning}. "

        script += """

처방전에 대한 더 자세한 정보는
인쇄된 보고서를 참조하거나 의료 전문가와 상담하세요.
감사합니다.
"""

        return script.strip()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        agent = AgentOrchestrator()
        logger.info("Orchestrator Agent ready for processing")

    except Exception as e:
        print(f"Error: {e}")
