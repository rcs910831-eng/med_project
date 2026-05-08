"""
환자 이력 관리 시스템 (Option C.1)
Patient History Management System

처방전 이력, 약물 알레르기, 만성질환 추적
Tracks prescriptions, drug allergies, chronic diseases
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AllergyRecord:
    """약물 알레르기 기록"""
    drug_name: str
    reaction_type: str  # 'rash', 'anaphylaxis', 'nausea', 'other'
    severity: str  # 'mild', 'moderate', 'severe'
    reported_date: str
    notes: str = ""


@dataclass
class ChronicDisease:
    """만성질환 기록"""
    disease_name: str
    icd10_code: str
    diagnosed_date: str
    status: str  # 'active', 'resolved', 'monitoring'
    related_medications: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PrescriptionRecord:
    """처방전 이력 기록"""
    prescription_id: str
    patient_id: str
    visit_date: str
    doctor_name: str
    clinic_name: str
    primary_diagnosis: str
    secondary_diagnoses: List[str]
    medications: List[Dict[str, Any]]  # [{name, dose, frequency, duration}]
    notes: str = ""
    image_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PatientProfile:
    """환자 프로필"""
    patient_id: str
    name: str
    age: int
    gender: str  # 'M', 'F'
    blood_type: str = ""
    contact_number: str = ""
    email: str = ""
    allergies: List[AllergyRecord] = field(default_factory=list)
    chronic_diseases: List[ChronicDisease] = field(default_factory=list)
    prescriptions: List[PrescriptionRecord] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class PatientHistoryManager:
    """
    환자 이력 관리자

    역할:
    - 환자 프로필 생성 및 관리
    - 처방전 이력 저장/조회
    - 약물 알레르기 추적
    - 만성질환 기록
    - 약물 상호작용 검사 (이전 약물과 비교)
    """

    def __init__(self, history_dir: str = "./patient_histories"):
        """
        초기화

        Args:
            history_dir: 환자 이력 저장 디렉토리
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True, parents=True)
        self.loaded_profiles: Dict[str, PatientProfile] = {}

    def create_patient_profile(
        self,
        patient_id: str,
        name: str,
        age: int,
        gender: str,
        blood_type: str = "",
        contact_number: str = "",
        email: str = ""
    ) -> PatientProfile:
        """환자 프로필 생성"""
        profile = PatientProfile(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            blood_type=blood_type,
            contact_number=contact_number,
            email=email
        )
        self._save_profile(profile)
        logger.info(f"✓ 환자 프로필 생성: {name} (ID: {patient_id})")
        return profile

    def get_patient_profile(self, patient_id: str) -> Optional[PatientProfile]:
        """환자 프로필 조회"""
        if patient_id in self.loaded_profiles:
            return self.loaded_profiles[patient_id]

        profile_path = self._get_profile_path(patient_id)
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profile = self._deserialize_profile(data)
                self.loaded_profiles[patient_id] = profile
                return profile

        logger.warning(f"⚠ 환자 프로필 없음: {patient_id}")
        return None

    def add_prescription_to_history(
        self,
        patient_id: str,
        prescription_id: str,
        visit_date: str,
        doctor_name: str,
        clinic_name: str,
        primary_diagnosis: str,
        secondary_diagnoses: List[str],
        medications: List[Dict[str, Any]],
        image_path: str = ""
    ) -> bool:
        """처방전을 환자 이력에 추가"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            logger.error(f"✗ 환자 프로필 없음: {patient_id}")
            return False

        rx_record = PrescriptionRecord(
            prescription_id=prescription_id,
            patient_id=patient_id,
            visit_date=visit_date,
            doctor_name=doctor_name,
            clinic_name=clinic_name,
            primary_diagnosis=primary_diagnosis,
            secondary_diagnoses=secondary_diagnoses,
            medications=medications,
            image_path=image_path
        )

        profile.prescriptions.append(rx_record)
        profile.last_updated = datetime.now().isoformat()
        self._save_profile(profile)
        self.loaded_profiles[patient_id] = profile

        logger.info(f"✓ 처방전 추가: {prescription_id} (환자: {profile.name})")
        return True

    def add_allergy_record(
        self,
        patient_id: str,
        drug_name: str,
        reaction_type: str,
        severity: str,
        notes: str = ""
    ) -> bool:
        """약물 알레르기 기록 추가"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            logger.error(f"✗ 환자 프로필 없음: {patient_id}")
            return False

        for allergy in profile.allergies:
            if allergy.drug_name.lower() == drug_name.lower():
                logger.warning(f"⚠ 이미 기록된 알레르기: {drug_name}")
                return False

        allergy = AllergyRecord(
            drug_name=drug_name,
            reaction_type=reaction_type,
            severity=severity,
            reported_date=datetime.now().isoformat(),
            notes=notes
        )

        profile.allergies.append(allergy)
        profile.last_updated = datetime.now().isoformat()
        self._save_profile(profile)
        self.loaded_profiles[patient_id] = profile

        logger.info(f"✓ 알레르기 기록 추가: {drug_name} ({severity}) - {profile.name}")
        return True

    def add_chronic_disease(
        self,
        patient_id: str,
        disease_name: str,
        icd10_code: str,
        diagnosed_date: str,
        status: str = 'active',
        related_medications: List[str] = None,
        notes: str = ""
    ) -> bool:
        """만성질환 기록 추가"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            logger.error(f"✗ 환자 프로필 없음: {patient_id}")
            return False

        disease = ChronicDisease(
            disease_name=disease_name,
            icd10_code=icd10_code,
            diagnosed_date=diagnosed_date,
            status=status,
            related_medications=related_medications or [],
            notes=notes
        )

        profile.chronic_diseases.append(disease)
        profile.last_updated = datetime.now().isoformat()
        self._save_profile(profile)
        self.loaded_profiles[patient_id] = profile

        logger.info(f"✓ 만성질환 기록: {disease_name} ({icd10_code}) - {profile.name}")
        return True

    def check_drug_interactions(
        self,
        patient_id: str,
        new_medications: List[str]
    ) -> Dict[str, List[str]]:
        """신규 약물과 기존 약물 간 상호작용 검사"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return {"error": "Patient not found"}

        existing_drugs = set()
        for rx in profile.prescriptions:
            for med in rx.medications:
                existing_drugs.add(med.get('name', '').lower())

        allergy_drugs = {allergy.drug_name.lower(): allergy.severity
                        for allergy in profile.allergies}

        interactions = {
            "warnings": [],
            "allergies": [],
            "history": []
        }

        for new_drug in new_medications:
            new_drug_lower = new_drug.lower()

            if new_drug_lower in allergy_drugs:
                severity = allergy_drugs[new_drug_lower]
                interactions["allergies"].append(
                    f"❌ {new_drug}: 알려진 알레르기 ({severity})"
                )

            if new_drug_lower in existing_drugs:
                interactions["history"].append(
                    f"✓ {new_drug}: 과거 사용 기록 있음"
                )

        logger.info(f"약물 상호작용 검사: {patient_id} ({len(new_medications)}개 약물)")
        return interactions

    def get_prescription_history(
        self,
        patient_id: str,
        limit: Optional[int] = None
    ) -> List[PrescriptionRecord]:
        """처방전 이력 조회"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return []

        sorted_rx = sorted(
            profile.prescriptions,
            key=lambda x: x.created_at,
            reverse=True
        )

        return sorted_rx[:limit] if limit else sorted_rx

    def get_allergy_list(self, patient_id: str) -> List[Dict[str, str]]:
        """환자 알레르기 목록"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return []

        return [asdict(allergy) for allergy in profile.allergies]

    def get_chronic_diseases(self, patient_id: str) -> List[Dict[str, Any]]:
        """환자 만성질환 목록"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return []

        return [asdict(disease) for disease in profile.chronic_diseases]

    def export_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """환자 정보 종합 리포트 생성"""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return {"error": "Patient not found"}

        return {
            "patient_profile": {
                "patient_id": profile.patient_id,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "blood_type": profile.blood_type,
                "last_updated": profile.last_updated
            },
            "prescriptions_count": len(profile.prescriptions),
            "recent_prescriptions": [
                asdict(rx) for rx in self.get_prescription_history(patient_id, limit=3)
            ],
            "allergies": self.get_allergy_list(patient_id),
            "chronic_diseases": self.get_chronic_diseases(patient_id),
            "statistics": {
                "total_visits": len(profile.prescriptions),
                "unique_medications": len(set(
                    med['name'] for rx in profile.prescriptions
                    for med in rx.medications
                )),
                "allergies_count": len(profile.allergies),
                "chronic_diseases_count": len(profile.chronic_diseases)
            }
        }

    def _get_profile_path(self, patient_id: str) -> Path:
        """환자 프로필 파일 경로"""
        return self.history_dir / f"patient_{patient_id}.json"

    def _save_profile(self, profile: PatientProfile) -> None:
        """프로필을 파일에 저장"""
        profile_path = self._get_profile_path(profile.patient_id)
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(self._serialize_profile(profile), f, indent=2, ensure_ascii=False)

    def _serialize_profile(self, profile: PatientProfile) -> Dict:
        """PatientProfile을 JSON 직렬화"""
        return {
            'patient_id': profile.patient_id,
            'name': profile.name,
            'age': profile.age,
            'gender': profile.gender,
            'blood_type': profile.blood_type,
            'contact_number': profile.contact_number,
            'email': profile.email,
            'allergies': [asdict(a) for a in profile.allergies],
            'chronic_diseases': [asdict(d) for d in profile.chronic_diseases],
            'prescriptions': [asdict(p) for p in profile.prescriptions],
            'last_updated': profile.last_updated
        }

    def _deserialize_profile(self, data: Dict) -> PatientProfile:
        """JSON을 PatientProfile로 역직렬화"""
        return PatientProfile(
            patient_id=data['patient_id'],
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            blood_type=data.get('blood_type', ''),
            contact_number=data.get('contact_number', ''),
            email=data.get('email', ''),
            allergies=[AllergyRecord(**a) for a in data.get('allergies', [])],
            chronic_diseases=[ChronicDisease(**d) for d in data.get('chronic_diseases', [])],
            prescriptions=[PrescriptionRecord(**p) for p in data.get('prescriptions', [])],
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = PatientHistoryManager()

    profile = manager.create_patient_profile(
        patient_id="P001",
        name="김철수",
        age=68,
        gender="M",
        blood_type="O+"
    )

    print(f"✓ 환자 프로필 생성: {profile.name}")
