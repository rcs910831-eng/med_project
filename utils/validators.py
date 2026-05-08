"""
Validators - Data Validation and Safety Checks
Ensures medication safety and data integrity
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    severity: str  # "error", "warning", "info"
    message: str
    details: Optional[Dict] = None


class MedicationValidator:
    """Validates medication information for safety"""

    # Known dangerous drug interactions
    DANGEROUS_INTERACTIONS = {
        ("metformin", "contrast_media"): {
            "severity": "error",
            "message": "조영제 사용 시 메트포민 중단 필요 (신독성 위험)"
        },
        ("aspirin", "anticoagulants"): {
            "severity": "warning",
            "message": "아스피린 + 항응고제: 출혈 위험 증가"
        },
        ("amlodipine", "simvastatin"): {
            "severity": "warning",
            "message": "아밀로디핀 + 심바스타틴: 약물 농도 상승 가능"
        }
    }

    # Known contraindications with conditions
    CONTRAINDICATIONS = {
        "metformin": {
            "kidney_disease": {"severity": "error", "message": "신부전 환자 금기 (eGFR < 30)"},
            "liver_disease": {"severity": "error", "message": "간경변 환자 금기"},
            "acute_infection": {"severity": "warning", "message": "급성 감염 시 일시 중단 권장"}
        },
        "afatinib": {
            "pregnancy": {"severity": "error", "message": "임산부 절대 금기"},
            "lactation": {"severity": "error", "message": "수유부 금기"}
        },
        "amlodipine": {
            "shock": {"severity": "error", "message": "쇼크 상태 환자 금기"}
        }
    }

    @staticmethod
    def validate_dosage(
        drug_name: str,
        dose_mg: float,
        frequency: str
    ) -> ValidationResult:
        """
        Validate if dosage is within recommended range

        Args:
            drug_name: Name of drug
            dose_mg: Dose in milligrams
            frequency: Frequency (e.g., "once_daily", "twice_daily")

        Returns:
            ValidationResult object
        """
        # Known recommended dosages
        dosage_ranges = {
            "amlodipine": {"min": 2.5, "max": 10, "frequency": "once_daily"},
            "metformin": {"min": 500, "max": 2550, "frequency": "2-3_times_daily"},
            "afatinib": {"min": 150, "max": 150, "frequency": "once_daily"}
        }

        if drug_name not in dosage_ranges:
            return ValidationResult(
                is_valid=True,
                severity="info",
                message=f"{drug_name}에 대한 표준 용량 정보 없음 (수동 검토 필요)"
            )

        ranges = dosage_ranges[drug_name]

        if dose_mg < ranges["min"] or dose_mg > ranges["max"]:
            return ValidationResult(
                is_valid=False,
                severity="warning",
                message=f"{drug_name}: 표준 범위 ({ranges['min']}-{ranges['max']}mg) 벗어남",
                details={"recommended_range": f"{ranges['min']}-{ranges['max']}mg"}
            )

        return ValidationResult(
            is_valid=True,
            severity="info",
            message=f"{drug_name}: 적절한 용량"
        )

    @staticmethod
    def check_drug_interaction(drug_names: List[str]) -> List[ValidationResult]:
        """
        Check for known drug interactions

        Args:
            drug_names: List of drug names

        Returns:
            List of ValidationResult for interactions
        """
        results = []

        for i, drug1 in enumerate(drug_names):
            for drug2 in drug_names[i+1:]:
                # Check both orders
                key1 = (drug1.lower(), drug2.lower())
                key2 = (drug2.lower(), drug1.lower())

                for key in [key1, key2]:
                    if key in MedicationValidator.DANGEROUS_INTERACTIONS:
                        interaction_info = MedicationValidator.DANGEROUS_INTERACTIONS[key]
                        results.append(ValidationResult(
                            is_valid=interaction_info["severity"] != "error",
                            severity=interaction_info["severity"],
                            message=interaction_info["message"],
                            details={"drugs": [drug1, drug2]}
                        ))

        return results

    @staticmethod
    def check_contraindications(
        drug_name: str,
        patient_conditions: List[str]
    ) -> List[ValidationResult]:
        """
        Check if drug is contraindicated for patient conditions

        Args:
            drug_name: Drug name
            patient_conditions: List of patient conditions (e.g., ["pregnancy", "kidney_disease"])

        Returns:
            List of ValidationResult for contraindications
        """
        results = []

        if drug_name.lower() not in MedicationValidator.CONTRAINDICATIONS:
            return results

        contraindications = MedicationValidator.CONTRAINDICATIONS[drug_name.lower()]

        for condition in patient_conditions:
            if condition.lower() in contraindications:
                contra_info = contraindications[condition.lower()]
                results.append(ValidationResult(
                    is_valid=contra_info["severity"] != "error",
                    severity=contra_info["severity"],
                    message=contra_info["message"],
                    details={"condition": condition}
                ))

        return results

    @staticmethod
    def validate_patient_age(
        drug_name: str,
        patient_age: int
    ) -> Optional[ValidationResult]:
        """
        Validate drug usage for patient age

        Args:
            drug_name: Drug name
            patient_age: Patient age in years

        Returns:
            ValidationResult or None
        """
        age_restrictions = {
            "afatinib": {"min": 18, "max": 150},
            "amlodipine": {"min": 18, "max": 150, "elderly_caution": True}
        }

        if drug_name not in age_restrictions:
            return None

        restriction = age_restrictions[drug_name]

        if patient_age < restriction.get("min", 0):
            return ValidationResult(
                is_valid=False,
                severity="error",
                message=f"{drug_name}: {restriction['min']}세 미만 환자 금기"
            )

        if restriction.get("elderly_caution") and patient_age >= 65:
            return ValidationResult(
                is_valid=True,
                severity="warning",
                message=f"{drug_name}: {patient_age}세 고령 환자 - 용량 감소 및 모니터링 권장"
            )

        return None

    @staticmethod
    def validate_dosage_frequency(
        duration_days: int,
        daily_frequency: int
    ) -> ValidationResult:
        """
        Calculate and validate total doses

        Args:
            duration_days: Duration of medication in days
            daily_frequency: Number of doses per day

        Returns:
            ValidationResult
        """
        total_doses = duration_days * daily_frequency

        if total_doses > 180:  # More than 6 months of daily dosing
            return ValidationResult(
                is_valid=True,
                severity="warning",
                message=f"장기 투약 ({duration_days}일): 정기적 검사 및 모니터링 강력 권장"
            )

        return ValidationResult(
            is_valid=True,
            severity="info",
            message=f"예상 총 투약량: {total_doses}회"
        )

    @staticmethod
    def validate_pregnancy_safety(
        drug_name: str,
        is_pregnant: bool,
        trimester: Optional[int] = None
    ) -> Optional[ValidationResult]:
        """
        Check pregnancy safety of medication

        Args:
            drug_name: Drug name
            is_pregnant: Whether patient is pregnant
            trimester: Trimester (1-3) if known

        Returns:
            ValidationResult or None
        """
        if not is_pregnant:
            return None

        # FDA Pregnancy Categories
        pregnancy_categories = {
            "amlodipine": "C",
            "metformin": "B",
            "afatinib": "D",
            "aspirin": "C" if trimester != 3 else "D"
        }

        if drug_name not in pregnancy_categories:
            return ValidationResult(
                is_valid=True,
                severity="info",
                message=f"{drug_name}: 임신 중 사용 가능성에 대해 의사와 상담 필수"
            )

        category = pregnancy_categories[drug_name]

        category_info = {
            "A": {"safe": True, "message": "임신 중 안전함"},
            "B": {"safe": True, "message": "임신 중 상대적으로 안전함"},
            "C": {"safe": False, "message": "임신 중 위험 가능성 - 이득이 위험을 정당화하는 경우만"},
            "D": {"safe": False, "message": "임신 중 금기 - 기형 유발 위험"},
            "X": {"safe": False, "message": "임신 중 절대 금기 - 기형/유산 위험"}
        }

        info = category_info.get(category, {})

        return ValidationResult(
            is_valid=info.get("safe", False),
            severity="error" if not info.get("safe") else "info",
            message=f"{drug_name} (FDA Category {category}): {info.get('message', '')}"
        )


class PrescriptionValidator:
    """Validates prescription data structure and completeness"""

    @staticmethod
    def validate_prescription_data(prescription: Dict) -> List[ValidationResult]:
        """
        Validate complete prescription data

        Args:
            prescription: Dictionary with prescription data

        Returns:
            List of ValidationResult objects
        """
        results = []

        # Check required fields
        required_fields = ["patient", "medications", "metadata"]
        for field in required_fields:
            if field not in prescription:
                results.append(ValidationResult(
                    is_valid=False,
                    severity="error",
                    message=f"필수 필드 누락: {field}"
                ))

        # Validate patient info
        if "patient" in prescription:
            patient = prescription["patient"]
            patient_fields = ["name", "age", "sex"]
            for field in patient_fields:
                if field not in patient:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity="warning",
                        message=f"환자 정보 부족: {field}"
                    ))

        # Validate medications
        if "medications" in prescription:
            if not isinstance(prescription["medications"], list):
                results.append(ValidationResult(
                    is_valid=False,
                    severity="error",
                    message="medications must be a list"
                ))
            elif len(prescription["medications"]) == 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity="error",
                    message="약물 정보가 없습니다"
                ))

        return results

    @staticmethod
    def extract_patient_age(age_text: str) -> Optional[int]:
        """
        Extract age from text

        Args:
            age_text: Age text (e.g., "68세", "68 years old")

        Returns:
            Age as integer or None
        """
        # Match Korean format
        korean_match = re.search(r"(\d+)\s*세", age_text)
        if korean_match:
            return int(korean_match.group(1))

        # Match English format
        english_match = re.search(r"(\d+)\s*years?\s*old", age_text)
        if english_match:
            return int(english_match.group(1))

        # Just numbers
        number_match = re.search(r"(\d+)", age_text)
        if number_match:
            age = int(number_match.group(1))
            if 0 <= age <= 150:
                return age

        return None

    @staticmethod
    def extract_dosage(dose_text: str) -> Optional[Tuple[float, str]]:
        """
        Extract dosage from text

        Args:
            dose_text: Dosage text (e.g., "5mg", "1정 500mg")

        Returns:
            (amount, unit) tuple or None
        """
        # Match pattern: number + unit
        match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|mcg|unit|정|ml|cc)", dose_text, re.IGNORECASE)
        if match:
            return (float(match.group(1)), match.group(2))

        return None


class DataValidator:
    """Validates data format and structure"""

    @staticmethod
    def validate_json_structure(data: Dict) -> ValidationResult:
        """Validate JSON structure"""
        try:
            if not isinstance(data, dict):
                return ValidationResult(
                    is_valid=False,
                    severity="error",
                    message="Data must be a dictionary"
                )
            return ValidationResult(
                is_valid=True,
                severity="info",
                message="Valid JSON structure"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity="error",
                message=f"JSON validation error: {str(e)}"
            )

    @staticmethod
    def sanitize_pii(text: str) -> str:
        """
        Sanitize personally identifiable information

        Args:
            text: Text potentially containing PII

        Returns:
            Text with PII masked
        """
        # Mask phone numbers
        text = re.sub(r"\d{2,3}-\d{3,4}-\d{4}", "XXX-XXXX-XXXX", text)

        # Mask email
        text = re.sub(r"\S+@\S+", "XXXX@XXXX", text)

        # Mask ID numbers
        text = re.sub(r"\d{6}-\d{7}", "XXXXXX-XXXXXXX", text)

        return text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test validators
    result = MedicationValidator.validate_dosage("amlodipine", 5.0, "once_daily")
    print(f"Dosage validation: {result}")

    interactions = MedicationValidator.check_drug_interaction(["amlodipine", "metformin"])
    print(f"Interactions: {interactions}")

    contra = MedicationValidator.check_contraindications(
        "metformin", ["kidney_disease"]
    )
    print(f"Contraindications: {contra}")
