"""
MFDS API Helper - Korean FDA Drug Information Integration
Manages MFDS OpenAPI for drug pricing, ingredients, and warnings
"""

import os
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


@dataclass
class DrugInfo:
    """Drug information from MFDS database"""
    drug_id: str
    korean_name: str
    english_name: str
    active_ingredient: str
    strength: str
    manufacturer: str
    approved_date: str
    mfds_official_price: Optional[float] = None
    dosage_form: Optional[str] = None
    standard_code: Optional[str] = None


class MFDSAPIHelper:
    """Wrapper for MFDS (Korean FDA) APIs"""

    def __init__(self):
        self.api_key = os.getenv("MFDS_API_KEY")
        if not self.api_key:
            logger.warning("MFDS_API_KEY not found in environment")

        self.base_url = "https://apis.data.go.kr/1471000"
        self.service_key = self.api_key

        logger.info("MFDSAPIHelper initialized")

    def search_drug_by_name(self, drug_name: str) -> List[DrugInfo]:
        """
        Search for drug information by name

        Args:
            drug_name: Korean or English drug name

        Returns:
            List of DrugInfo objects
        """
        try:
            # MFDS Service 01: MdcinGrnIdntfcInfoService01
            url = f"{self.base_url}/MdcinGrnIdntfcInfoService01/getMdcinGrnIdntfcList"
            params = {
                "ServiceKey": self.service_key,
                "numOfRows": "100",
                "pageNo": "1",
                "sickCd": "",
                "mdcinName": drug_name,
                "mdcinEngName": drug_name,
                "itemSeq": "",
                "dataType": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            drugs = []
            if result.get("response", {}).get("body", {}).get("items"):
                items = result["response"]["body"]["items"]

                # Handle single item (returned as dict) or multiple items (returned as list)
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    drug = DrugInfo(
                        drug_id=item.get("itemSeq", ""),
                        korean_name=item.get("itemName", ""),
                        english_name=item.get("itemEngName", ""),
                        active_ingredient=item.get("mainIngr", ""),
                        strength=item.get("dosageForm", ""),
                        manufacturer=item.get("entpName", ""),
                        approved_date=item.get("aprvPermitDate", ""),
                        dosage_form=item.get("dosageForm", ""),
                        standard_code=item.get("itemSeq", "")
                    )
                    drugs.append(drug)

            logger.info(f"Found {len(drugs)} drugs for '{drug_name}'")
            return drugs

        except Exception as e:
            logger.error(f"Error searching drugs: {e}")
            return []

    def get_drug_pricing(self, drug_name: str) -> Optional[Dict]:
        """
        Get MFDS official drug pricing

        Args:
            drug_name: Drug name

        Returns:
            Dictionary with pricing information or None
        """
        try:
            # This would use the MFDS pricing service if available
            # For now, return from local database
            logger.info(f"Querying MFDS pricing for {drug_name}")

            # Service 02: MdcinGrnIdntfcInfoService02 (pricing)
            url = f"{self.base_url}/MdcinGrnIdntfcInfoService02/getMdcinGrnIdntfcList"
            params = {
                "ServiceKey": self.service_key,
                "numOfRows": "100",
                "pageNo": "1",
                "mdcinName": drug_name,
                "dataType": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("response", {}).get("body", {}).get("items"):
                items = result["response"]["body"]["items"]
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    return {
                        "drug_name": item.get("itemName", ""),
                        "mfds_official_price": float(item.get("price", 0)),
                        "effective_date": item.get("effectDate", ""),
                        "unit": item.get("unitName", "")
                    }

            return None

        except Exception as e:
            logger.warning(f"Could not retrieve MFDS pricing: {e}")
            return None

    def get_drug_warnings_and_precautions(self, drug_id: str) -> Optional[Dict]:
        """
        Get drug warnings and precautions

        Args:
            drug_id: Drug item sequence number

        Returns:
            Dictionary with warnings or None
        """
        try:
            # Service 03: Drug safety information
            url = f"{self.base_url}/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcList"
            params = {
                "ServiceKey": self.service_key,
                "numOfRows": "10",
                "pageNo": "1",
                "itemSeq": drug_id,
                "dataType": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("response", {}).get("body", {}).get("items"):
                items = result["response"]["body"]["items"]
                if isinstance(items, dict):
                    items = [items]

                if items:
                    item = items[0]
                    return {
                        "warnings": item.get("warning", ""),
                        "precautions": item.get("caution", ""),
                        "side_effects": item.get("sideEffect", ""),
                        "contraindications": item.get("contraIndication", "")
                    }

            return None

        except Exception as e:
            logger.warning(f"Could not retrieve drug warnings: {e}")
            return None

    def get_drug_interactions(self, drug_names: List[str]) -> Dict[str, List[str]]:
        """
        Check for drug interactions

        Args:
            drug_names: List of drug names

        Returns:
            Dictionary of potential interactions
        """
        try:
            interactions = {}

            for i, drug1 in enumerate(drug_names):
                for drug2 in drug_names[i+1:]:
                    # Query MFDS for known interactions
                    # This is a simplified approach
                    key = f"{drug1} + {drug2}"
                    interactions[key] = []

                    # In production, would query actual database
                    logger.debug(f"Checking interaction: {key}")

            return interactions

        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")
            return {}

    def search_by_indications(self, disease_name: str) -> List[DrugInfo]:
        """
        Search drugs by indications/disease

        Args:
            disease_name: Disease or condition name

        Returns:
            List of DrugInfo objects
        """
        try:
            # MFDS Service with disease search
            url = f"{self.base_url}/MdcinGrnIdntfcInfoService01/getMdcinGrnIdntfcList"
            params = {
                "ServiceKey": self.service_key,
                "numOfRows": "100",
                "pageNo": "1",
                "sickCd": disease_name,  # Disease code
                "dataType": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            drugs = []
            if result.get("response", {}).get("body", {}).get("items"):
                items = result["response"]["body"]["items"]
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    drug = DrugInfo(
                        drug_id=item.get("itemSeq", ""),
                        korean_name=item.get("itemName", ""),
                        english_name=item.get("itemEngName", ""),
                        active_ingredient=item.get("mainIngr", ""),
                        strength=item.get("strength", ""),
                        manufacturer=item.get("entpName", ""),
                        approved_date=item.get("aprvPermitDate", "")
                    )
                    drugs.append(drug)

            logger.info(f"Found {len(drugs)} drugs for disease '{disease_name}'")
            return drugs

        except Exception as e:
            logger.error(f"Error searching by indications: {e}")
            return []

    def verify_drug_approval(self, drug_name: str) -> bool:
        """
        Verify if drug is officially approved by MFDS

        Args:
            drug_name: Drug name

        Returns:
            True if approved, False otherwise
        """
        try:
            drugs = self.search_drug_by_name(drug_name)
            return len(drugs) > 0
        except Exception as e:
            logger.error(f"Error verifying drug approval: {e}")
            return False

    @staticmethod
    def format_dosage_instruction(strength: str, frequency: str, duration: int) -> str:
        """
        Format dosage instruction in Korean

        Args:
            strength: Drug strength (e.g., "5mg")
            frequency: Frequency (e.g., "1회 1정 (1일 1회)")
            duration: Duration in days

        Returns:
            Formatted instruction
        """
        return f"{strength} - {frequency} - {duration}일"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    helper = MFDSAPIHelper()

    # Example: Search for amlodipine
    drugs = helper.search_drug_by_name("아밀로디핀")
    for drug in drugs[:3]:
        print(f"{drug.korean_name} ({drug.english_name})")
        print(f"  Active Ingredient: {drug.active_ingredient}")
        print(f"  Manufacturer: {drug.manufacturer}")

    # Get pricing
    pricing = helper.get_drug_pricing("노바스크정")
    if pricing:
        print(f"\nPricing: {pricing}")
