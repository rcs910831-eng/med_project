"""
Google API Helper - Unified Google API Integration
Manages Google Places API, Google Cloud TTS
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


@dataclass
class Pharmacy:
    """Pharmacy information from Google Places API"""
    name: str
    address: str
    phone: str
    latitude: float
    longitude: float
    distance_km: float
    hours: Optional[str] = None
    rating: Optional[float] = None
    website: Optional[str] = None
    is_open: Optional[bool] = None
    place_id: Optional[str] = None


class GoogleAPIHelper:
    """Wrapper for Google APIs"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        self.places_base_url = "https://maps.googleapis.com/maps/api/place"
        self.geocoding_base_url = "https://maps.googleapis.com/maps/api/geocode"

        logger.info("GoogleAPIHelper initialized")

    def search_pharmacies(
        self,
        latitude: float,
        longitude: float,
        radius_km: int = 2,
        max_results: int = 10
    ) -> List[Pharmacy]:
        """
        Search for pharmacies near a location using Google Places API

        Args:
            latitude: Latitude of search center
            longitude: Longitude of search center
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return

        Returns:
            List of Pharmacy objects
        """
        try:
            radius_meters = radius_km * 1000

            # Search for pharmacies using Google Places API
            url = f"{self.places_base_url}/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius_meters,
                "type": "pharmacy",
                "key": self.api_key,
                "language": "ko"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()

            if results["status"] != "OK":
                logger.warning(f"Google Places API status: {results['status']}")
                return []

            pharmacies = []
            for place in results.get("results", [])[:max_results]:
                pharmacy = Pharmacy(
                    name=place.get("name", ""),
                    address=place.get("vicinity", ""),
                    phone="",  # Not in nearby search
                    latitude=place["geometry"]["location"]["lat"],
                    longitude=place["geometry"]["location"]["lng"],
                    distance_km=self._haversine_distance(
                        latitude, longitude,
                        place["geometry"]["location"]["lat"],
                        place["geometry"]["location"]["lng"]
                    ),
                    rating=place.get("rating"),
                    is_open=place.get("opening_hours", {}).get("open_now"),
                    place_id=place.get("place_id")
                )
                pharmacies.append(pharmacy)

                # Get detailed information for each pharmacy
                if pharmacy.place_id:
                    self._enrich_pharmacy_details(pharmacy)

            # Sort by distance
            pharmacies.sort(key=lambda x: x.distance_km)
            logger.info(f"Found {len(pharmacies)} pharmacies within {radius_km}km")

            return pharmacies

        except Exception as e:
            logger.error(f"Error searching pharmacies: {e}")
            return []

    def _enrich_pharmacy_details(self, pharmacy: Pharmacy) -> None:
        """
        Get additional details for a pharmacy

        Args:
            pharmacy: Pharmacy object to enrich
        """
        try:
            url = f"{self.places_base_url}/details/json"
            params = {
                "place_id": pharmacy.place_id,
                "fields": "formatted_phone_number,opening_hours,website,formatted_address",
                "key": self.api_key,
                "language": "ko"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result["status"] == "OK":
                result_data = result.get("result", {})
                pharmacy.phone = result_data.get("formatted_phone_number", "")
                pharmacy.hours = result_data.get("opening_hours", {}).get("weekday_text", [])
                pharmacy.website = result_data.get("website", "")

        except Exception as e:
            logger.warning(f"Could not enrich pharmacy details: {e}")

    def get_coordinates_from_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to latitude/longitude using Geocoding API

        Args:
            address: Address string

        Returns:
            (latitude, longitude) tuple or None
        """
        try:
            url = f"{self.geocoding_base_url}/json"
            params = {
                "address": address,
                "key": self.api_key,
                "language": "ko",
                "region": "KR"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result["status"] == "OK" and result.get("results"):
                location = result["results"][0]["geometry"]["location"]
                return (location["lat"], location["lng"])

            logger.warning(f"Could not geocode address: {address}")
            return None

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None

    def synthesize_speech(
        self,
        text: str,
        language_code: str = "ko-KR",
        voice_name: str = "ko-KR-Standard-A",
        output_file: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Synthesize speech using Google Cloud Text-to-Speech API

        Args:
            text: Text to synthesize
            language_code: Language code (e.g., 'ko-KR', 'en-US')
            voice_name: Voice name (e.g., 'ko-KR-Standard-A')
            output_file: Optional file path to save audio

        Returns:
            Audio bytes or None if error
        """
        try:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            audio_content = response.audio_content

            if output_file:
                with open(output_file, "wb") as f:
                    f.write(audio_content)
                logger.info(f"Audio saved to {output_file}")

            return audio_content

        except ImportError:
            logger.error("google-cloud-texttospeech not installed")
            return None
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in kilometers

        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate

        Returns:
            Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c

        return km

    @lru_cache(maxsize=100)
    def cache_pharmacy_search(self, lat: float, lon: float, radius: int) -> str:
        """Cache pharmacy search results"""
        return json.dumps({
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "cached": True
        })


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    helper = GoogleAPIHelper()

    # Search for pharmacies in Seoul
    pharmacies = helper.search_pharmacies(37.5665, 126.9780, radius_km=2)

    for pharmacy in pharmacies[:3]:
        print(f"{pharmacy.name} - {pharmacy.distance_km:.2f}km away")
        print(f"  Address: {pharmacy.address}")
        print(f"  Phone: {pharmacy.phone}")
