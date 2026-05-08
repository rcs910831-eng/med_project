"""
Agent 3: Google Places & Real-time Information Specialist
약국 검색 및 실시간 약가 정보 제공
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

from anthropic import Anthropic
from utils.google_api_helper import GoogleAPIHelper, Pharmacy
from utils.mfds_api_helper import MFDSAPIHelper

logger = logging.getLogger(__name__)


@dataclass
class PharmacyWithPricing:
    """약국 정보 + 약가"""
    pharmacy: Pharmacy
    drug_prices: Dict[str, float]  # {drug_name: price}
    estimated_total: float = 0.0


class AgentGooglePharmacy:
    """Google Places & 실시간정보 전문가"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Pharmacy Agent

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-6"  # Cost-optimized

        # Initialize API helpers
        try:
            self.google_helper = GoogleAPIHelper()
            logger.info("Google API Helper initialized")
        except Exception as e:
            logger.warning(f"Google API Helper init failed: {e}")
            self.google_helper = None

        try:
            self.mfds_helper = MFDSAPIHelper()
            logger.info("MFDS API Helper initialized")
        except Exception as e:
            logger.warning(f"MFDS API Helper init failed: {e}")
            self.mfds_helper = None

        self.system_prompt = """당신은 약국 정보 검색 및 실시간 약가 조회 전문가입니다.

역할:
1. Google Maps API로 주변 약국 검색 (반경 2km)
2. 약국명, 주소, 전화, 영업시간 제공
3. MFDS 공시약가 조회
4. 약국 배달 가능 여부 확인
5. 거리 기반 약국 정렬

데이터 출처:
- Google Places API (위치, 영업시간, 평점)
- MFDS 공식 약가 데이터
"""

        logger.info("AgentGooglePharmacy initialized")

    def search_nearby_pharmacies(
        self,
        latitude: float,
        longitude: float,
        address: str = "",
        radius_km: int = 2,
        max_results: int = 10
    ) -> List[PharmacyWithPricing]:
        """
        Search nearby pharmacies with pricing information

        Args:
            latitude: Location latitude
            longitude: Location longitude
            address: Address string (for logging)
            radius_km: Search radius
            max_results: Maximum results to return

        Returns:
            List of PharmacyWithPricing objects
        """
        try:
            if not self.google_helper:
                logger.error("Google API Helper not available")
                return []

            # Search pharmacies
            pharmacies = self.google_helper.search_pharmacies(
                latitude,
                longitude,
                radius_km=radius_km,
                max_results=max_results
            )

            if not pharmacies:
                logger.warning(f"No pharmacies found near {address}")
                return []

            # Enrich with pricing
            pharmacies_with_pricing = []
            for pharmacy in pharmacies:
                pharm_with_pricing = PharmacyWithPricing(
                    pharmacy=pharmacy,
                    drug_prices={}
                )
                pharmacies_with_pricing.append(pharm_with_pricing)

            logger.info(f"Found {len(pharmacies_with_pricing)} pharmacies near {address}")
            return pharmacies_with_pricing

        except Exception as e:
            logger.error(f"Error searching pharmacies: {e}")
            return []

    def get_drug_pricing(self, drug_names: List[str]) -> Dict[str, float]:
        """
        Get MFDS official pricing for drugs

        Args:
            drug_names: List of drug names

        Returns:
            Dictionary mapping drug names to prices
        """
        try:
            if not self.mfds_helper:
                logger.warning("MFDS API Helper not available")
                return {}

            pricing = {}

            for drug_name in drug_names:
                price_info = self.mfds_helper.get_drug_pricing(drug_name)
                if price_info:
                    pricing[drug_name] = price_info.get("mfds_official_price", 0)
                    logger.info(
                        f"{drug_name}: {price_info.get('mfds_official_price')}원"
                    )
                else:
                    # Fallback to local database if available
                    pricing[drug_name] = self._get_local_pricing(drug_name)

            return pricing

        except Exception as e:
            logger.error(f"Error getting pricing: {e}")
            return {}

    def enrich_pharmacies_with_prices(
        self,
        pharmacies: List[PharmacyWithPricing],
        drug_names: List[str]
    ) -> List[PharmacyWithPricing]:
        """
        Add drug pricing to pharmacy information

        Args:
            pharmacies: List of pharmacies
            drug_names: List of drugs to price

        Returns:
            Updated list with pricing
        """
        try:
            # Get pricing for all drugs
            drug_prices = self.get_drug_pricing(drug_names)

            # Add to each pharmacy (same prices for all in MFDS system)
            for pharm in pharmacies:
                pharm.drug_prices = drug_prices.copy()
                pharm.estimated_total = sum(drug_prices.values())

            logger.info(f"Enriched {len(pharmacies)} pharmacies with pricing")
            return pharmacies

        except Exception as e:
            logger.error(f"Error enriching pharmacies: {e}")
            return pharmacies

    def rank_pharmacies(
        self,
        pharmacies: List[PharmacyWithPricing],
        criteria: Dict = None
    ) -> List[PharmacyWithPricing]:
        """
        Rank pharmacies based on criteria

        Args:
            pharmacies: List of pharmacies
            criteria: Ranking criteria (distance, rating, hours, etc.)

        Returns:
            Sorted list of pharmacies
        """
        try:
            if criteria is None:
                criteria = {"distance": 1.0, "rating": 0.5, "hours": 0.3}

            # Default: sort by distance
            sorted_pharmacies = sorted(
                pharmacies,
                key=lambda x: x.pharmacy.distance_km
            )

            logger.info(f"Ranked {len(sorted_pharmacies)} pharmacies by distance")
            return sorted_pharmacies

        except Exception as e:
            logger.error(f"Error ranking pharmacies: {e}")
            return pharmacies

    def format_pharmacy_info(
        self,
        pharmacies: List[PharmacyWithPricing]
    ) -> List[Dict]:
        """
        Format pharmacy information for output

        Args:
            pharmacies: List of PharmacyWithPricing

        Returns:
            List of formatted pharmacy dictionaries
        """
        try:
            formatted = []

            for pharm in pharmacies:
                pharmacy_dict = {
                    "name": pharm.pharmacy.name,
                    "address": pharm.pharmacy.address,
                    "phone": pharm.pharmacy.phone,
                    "distance_km": round(pharm.pharmacy.distance_km, 2),
                    "hours": pharm.pharmacy.hours,
                    "rating": pharm.pharmacy.rating,
                    "is_open": pharm.pharmacy.is_open,
                    "drug_prices": pharm.drug_prices,
                    "estimated_total": round(pharm.estimated_total, 0),
                    "website": pharm.pharmacy.website,
                    "place_id": pharm.pharmacy.place_id
                }
                formatted.append(pharmacy_dict)

            return formatted

        except Exception as e:
            logger.error(f"Error formatting pharmacy info: {e}")
            return []

    def get_full_pharmacy_search(
        self,
        latitude: float,
        longitude: float,
        drug_names: List[str],
        radius_km: int = 2,
        max_results: int = 10
    ) -> Dict:
        """
        Full pharmacy search with pricing

        Args:
            latitude: Location latitude
            longitude: Location longitude
            drug_names: Drugs to price
            radius_km: Search radius
            max_results: Max results

        Returns:
            Comprehensive pharmacy search result
        """
        try:
            # Search nearby pharmacies
            pharmacies = self.search_nearby_pharmacies(
                latitude, longitude,
                radius_km=radius_km,
                max_results=max_results
            )

            if not pharmacies:
                logger.warning("No pharmacies found")
                return {
                    "success": False,
                    "pharmacies": [],
                    "error": "약국을 찾을 수 없습니다"
                }

            # Enrich with pricing
            pharmacies = self.enrich_pharmacies_with_prices(pharmacies, drug_names)

            # Rank pharmacies
            pharmacies = self.rank_pharmacies(pharmacies)

            # Format output
            formatted_pharmacies = self.format_pharmacy_info(pharmacies)

            result = {
                "success": True,
                "pharmacies": formatted_pharmacies,
                "total_found": len(formatted_pharmacies),
                "search_radius_km": radius_km,
                "drugs_searched": drug_names
            }

            logger.info(f"Full search completed: {len(formatted_pharmacies)} pharmacies")
            return result

        except Exception as e:
            logger.error(f"Error in full pharmacy search: {e}")
            return {
                "success": False,
                "pharmacies": [],
                "error": str(e)
            }

    def check_delivery_availability(self, pharmacy_name: str) -> bool:
        """
        Check if pharmacy offers delivery service

        Args:
            pharmacy_name: Name of pharmacy

        Returns:
            True if delivery available
        """
        try:
            # TODO: Implement API call to check delivery
            # For now, return true for major chains
            major_chains = ["약국", "한약국", "명약국"]
            for chain in major_chains:
                if chain in pharmacy_name:
                    return True
            return False

        except Exception as e:
            logger.error(f"Error checking delivery: {e}")
            return False

    @staticmethod
    def _get_local_pricing(drug_name: str) -> float:
        """
        Get local pricing from RAG database as fallback

        Args:
            drug_name: Drug name

        Returns:
            Price or 0
        """
        try:
            import json
            from pathlib import Path

            db_path = Path("rag_db/drug_info_index.json")
            if db_path.exists():
                with open(db_path, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    for drug in db.get("drugs", []):
                        if drug_name.lower() in drug.get("korean_name", "").lower():
                            return float(drug.get("mfds_official_price", 0))
            return 0

        except Exception as e:
            logger.warning(f"Error getting local pricing: {e}")
            return 0

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates

        Args:
            address: Address string

        Returns:
            (latitude, longitude) tuple or None
        """
        try:
            if not self.google_helper:
                return None

            coords = self.google_helper.get_coordinates_from_address(address)
            return coords

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        agent = AgentGooglePharmacy()

        # Example: Search near Seoul (37.5665, 126.9780)
        result = agent.get_full_pharmacy_search(
            latitude=37.5665,
            longitude=126.9780,
            drug_names=["노바스크정", "글루코판정"],
            radius_km=2,
            max_results=5
        )

        if result["success"]:
            print(f"\n약국 검색 결과: {result['total_found']}개")
            for pharm in result["pharmacies"][:3]:
                print(f"- {pharm['name']} ({pharm['distance_km']}km)")
                print(f"  가격: {pharm['estimated_total']}원")
        else:
            print(f"검색 실패: {result.get('error')}")

    except Exception as e:
        print(f"Error: {e}")
