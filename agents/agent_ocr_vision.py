"""
Agent 1: OCR & Vision Specialist
Analyzes prescription images and extracts structured medical information
"""

import os
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path
import base64

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AgentOCRVision:
    """OCR & Vision Specialist - Prescription Image Analysis"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR Vision Agent

        Args:
            api_key: Anthropic API key (uses environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-7"  # High-resolution vision support

        self.system_prompt = """당신은 의료 처방전 이미지 분석 전문가입니다.

역할:
1. 처방전 이미지에서 환자 정보 추출 (이름, 나이, 성별, 진료일자)
2. 진료 병명 식별 (주진료, 부진료)
3. 처방약물 정보 추출 (약물명, 용량, 수량, 빈도)
4. 처방 정당성 검증 (의사 서명, 인장)

출력 형식은 반드시 유효한 JSON이어야 합니다.
"""

        logger.info("AgentOCRVision initialized")

    def analyze_prescription_image(
        self,
        image_path: str
    ) -> Optional[Dict]:
        """
        Analyze a prescription image and extract structured data

        Args:
            image_path: Path to prescription image

        Returns:
            Dictionary with extracted prescription data or None
        """
        try:
            # Verify file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None

            # Read and encode image
            image_data = self._read_image_as_base64(image_path)
            if not image_data:
                logger.error("Failed to read image")
                return None

            # Determine media type
            media_type = self._get_media_type(image_path)

            # Call Claude Vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": """이 처방전 이미지를 분석해주세요.

다음 정보를 JSON 형식으로 추출해주세요:
{
  "patient": {
    "name": "환자명",
    "age": 나이,
    "sex": "M/F",
    "diagnosis_primary": "주진료 병명",
    "diagnosis_secondary": "부진료 병명 (없으면 null)"
  },
  "medications": [
    {
      "name": "약물명",
      "strength": "용량",
      "quantity": "수량",
      "frequency": "빈도"
    }
  ],
  "metadata": {
    "prescription_date": "처방일자",
    "doctor_signature_verified": true/false,
    "hospital_seal_verified": true/false,
    "image_quality": "high/medium/low"
  }
}

주의: 반드시 유효한 JSON 형식으로만 응답해주세요. 다른 설명은 하지 마세요."""
                            }
                        ],
                    }
                ]
            )

            # Extract JSON from response
            response_text = response.content[0].text
            prescription_data = self._parse_json_response(response_text)

            if prescription_data:
                logger.info("Successfully extracted prescription data")
                return prescription_data
            else:
                logger.warning("Failed to parse prescription data from response")
                return None

        except Exception as e:
            logger.error(f"Error analyzing prescription image: {e}")
            return None

    def batch_analyze_prescriptions(
        self,
        image_directory: str
    ) -> List[Dict]:
        """
        Analyze multiple prescription images from a directory

        Args:
            image_directory: Directory containing prescription images

        Returns:
            List of dictionaries with extracted data
        """
        results = []

        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        image_dir = Path(image_directory)

        if not image_dir.exists():
            logger.error(f"Directory not found: {image_directory}")
            return results

        # Find all image files
        image_files = [
            f for f in image_dir.glob("*")
            if f.suffix.lower() in image_extensions
        ]

        logger.info(f"Found {len(image_files)} images to analyze")

        for idx, image_file in enumerate(image_files, 1):
            logger.info(f"Processing {idx}/{len(image_files)}: {image_file.name}")

            prescription_data = self.analyze_prescription_image(str(image_file))

            if prescription_data:
                prescription_data["source_file"] = image_file.name
                results.append(prescription_data)
            else:
                logger.warning(f"Failed to analyze: {image_file.name}")

        logger.info(f"Successfully analyzed {len(results)}/{len(image_files)} images")

        return results

    def _read_image_as_base64(self, image_path: str) -> Optional[str]:
        """
        Read image file and encode as base64

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image data or None
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            return base64.standard_b64encode(image_data).decode("utf-8")
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return None

    @staticmethod
    def _get_media_type(image_path: str) -> str:
        """
        Determine media type from file extension

        Args:
            image_path: Path to image file

        Returns:
            MIME type string
        """
        extension = Path(image_path).suffix.lower()

        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }

        return media_types.get(extension, "image/jpeg")

    @staticmethod
    def _parse_json_response(response_text: str) -> Optional[Dict]:
        """
        Parse JSON from Claude response

        Args:
            response_text: Response text from Claude

        Returns:
            Parsed JSON dictionary or None
        """
        try:
            # Try to find JSON block in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)

            logger.warning("No JSON found in response")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None

    def validate_extracted_data(self, prescription_data: Dict) -> bool:
        """
        Validate extracted prescription data completeness

        Args:
            prescription_data: Extracted prescription data

        Returns:
            True if data is valid
        """
        required_fields = ["patient", "medications", "metadata"]

        # Check top-level fields
        for field in required_fields:
            if field not in prescription_data:
                logger.warning(f"Missing field: {field}")
                return False

        # Check patient fields
        patient_fields = ["name", "age", "sex"]
        for field in patient_fields:
            if field not in prescription_data.get("patient", {}):
                logger.warning(f"Missing patient field: {field}")
                return False

        # Check medications
        if not isinstance(prescription_data.get("medications"), list):
            logger.warning("Medications must be a list")
            return False

        if len(prescription_data.get("medications", [])) == 0:
            logger.warning("No medications found")
            return False

        logger.info("Prescription data validation passed")
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    agent = AgentOCRVision()

    # Test with a single prescription image
    prescription_dir = "./prescription_images"

    if os.path.exists(prescription_dir):
        results = agent.batch_analyze_prescriptions(prescription_dir)

        # Print results
        for result in results[:3]:
            print(json.dumps(result, indent=2, ensure_ascii=False))

        print(f"\nTotal analyzed: {len(results)}")
    else:
        print(f"Directory not found: {prescription_dir}")
