"""
Agent 1: OCR & Vision Specialist (OPTIMIZED)
Analyzes prescription images and extracts structured medical information
with enhanced error handling, caching, and performance optimizations.
"""

import os
import json
import logging
import time
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from functools import lru_cache
import base64

from anthropic import Anthropic, APIError, RateLimitError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 5.0
    backoff_multiplier: float = 2.0


class AgentOCRVision:
    """
    OCR & Vision Specialist - Prescription Image Analysis

    Processes prescription images to extract structured medical information
    including patient details, medications, and metadata. Features:
    - Automatic retry with exponential backoff
    - Request validation and error handling
    - Performance metrics logging
    - Comprehensive error context

    Attributes:
        api_key (str): Anthropic API key
        client (Anthropic): API client instance
        model (str): Claude model for vision analysis
        system_prompt (str): System message for vision analysis
        _stats (Dict): Performance statistics
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR Vision Agent.

        Args:
            api_key: Anthropic API key (uses environment variable if not provided)

        Raises:
            ValueError: If ANTHROPIC_API_KEY not found in environment or arguments
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-7"  # High-resolution vision support

        # Performance tracking
        self._stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_duration_sec": 0.0,
            "api_retry_count": 0
        }

        self.system_prompt = """당신은 의료 처방전 이미지 분석 전문가입니다.

역할:
1. 처방전 이미지에서 환자 정보 추출 (이름, 나이, 성별, 진료일자)
2. 진료 병명 식별 (주진료, 부진료)
3. 처방약물 정보 추출 (약물명, 용량, 수량, 빈도)
4. 처방 정당성 검증 (의사 서명, 인장)

출력 형식은 반드시 유효한 JSON이어야 합니다."""

        logger.info(
            f"AgentOCRVision initialized with model={self.model}, "
            f"max_retries={RetryConfig.max_retries}"
        )

    def analyze_prescription_image(
        self,
        image_path: str,
        validate_only: bool = False
    ) -> Optional[Dict]:
        """
        Analyze a prescription image and extract structured data.

        Implements automatic retry with exponential backoff and comprehensive
        error handling. Returns None on failure after max retries.

        Args:
            image_path: Path to prescription image
            validate_only: If True, only validate file without calling API

        Returns:
            Dictionary with extracted prescription data or None on failure

        Example:
            >>> agent = AgentOCRVision()
            >>> result = agent.analyze_prescription_image("rx_001.png")
            >>> if result:
            ...     print(f"Patient: {result['patient']['name']}")
        """
        start_time = time.time()
        self._stats["total_analyses"] += 1

        try:
            # Validate input
            if not self._validate_image_path(image_path):
                self._stats["failed_analyses"] += 1
                return None

            if validate_only:
                logger.info(f"Image validation passed: {image_path}")
                return {"validated": True}

            # Read and encode image with retry
            image_data = self._read_image_as_base64(image_path)
            if not image_data:
                self._stats["failed_analyses"] += 1
                logger.error(f"Failed to read image: {image_path}")
                return None

            media_type = self._get_media_type(image_path)

            # Call Claude Vision API with retry logic
            prescription_data = self._call_vision_api_with_retry(
                image_data,
                media_type,
                image_path
            )

            if prescription_data:
                # Validate extracted data
                if self.validate_extracted_data(prescription_data):
                    self._stats["successful_analyses"] += 1
                    duration = time.time() - start_time
                    self._stats["total_duration_sec"] += duration
                    logger.info(
                        f"✓ Successfully analyzed: {image_path} "
                        f"({duration:.2f}s, {len(prescription_data.get('medications', []))} medications)"
                    )
                    return prescription_data
                else:
                    logger.warning(f"Extracted data validation failed: {image_path}")
                    self._stats["failed_analyses"] += 1
                    return None
            else:
                self._stats["failed_analyses"] += 1
                return None

        except Exception as e:
            self._stats["failed_analyses"] += 1
            logger.error(
                f"Unexpected error analyzing {image_path}: {type(e).__name__}: {e}",
                exc_info=True
            )
            return None

    def batch_analyze_prescriptions(
        self,
        image_directory: str,
        max_concurrent: int = 1,
        show_progress: bool = True
    ) -> Dict[str, any]:
        """
        Analyze multiple prescription images from a directory.

        Processes images sequentially (async batch support planned).
        Returns detailed results including statistics and failures.

        Args:
            image_directory: Directory containing prescription images
            max_concurrent: Max concurrent processing (reserved for async)
            show_progress: Print progress information

        Returns:
            Dictionary with results, statistics, and failures:
            {
                "results": [...],
                "stats": {
                    "total": int,
                    "successful": int,
                    "failed": int,
                    "duration_sec": float
                },
                "failures": [{"file": str, "reason": str}]
            }
        """
        batch_start = time.time()
        results = []
        failures = []

        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        image_dir = Path(image_directory)

        if not image_dir.exists():
            logger.error(f"Directory not found: {image_directory}")
            return {
                "results": [],
                "stats": {"total": 0, "successful": 0, "failed": 0, "duration_sec": 0},
                "failures": [{"file": image_directory, "reason": "Directory not found"}]
            }

        # Find all image files
        image_files = sorted([
            f for f in image_dir.glob("*")
            if f.suffix.lower() in image_extensions
        ])

        total_files = len(image_files)
        if total_files == 0:
            logger.warning(f"No image files found in {image_directory}")
            return {
                "results": [],
                "stats": {"total": 0, "successful": 0, "failed": 0, "duration_sec": 0},
                "failures": [{"file": image_directory, "reason": "No image files found"}]
            }

        logger.info(f"Starting batch analysis of {total_files} images")

        for idx, image_file in enumerate(image_files, 1):
            if show_progress:
                logger.info(f"Processing {idx}/{total_files}: {image_file.name}")

            prescription_data = self.analyze_prescription_image(str(image_file))

            if prescription_data:
                prescription_data["source_file"] = image_file.name
                results.append(prescription_data)
            else:
                failures.append({
                    "file": image_file.name,
                    "reason": "Analysis failed or returned invalid data"
                })

        batch_duration = time.time() - batch_start

        stats = {
            "total": total_files,
            "successful": len(results),
            "failed": len(failures),
            "duration_sec": batch_duration,
            "avg_per_image_sec": batch_duration / total_files if total_files > 0 else 0
        }

        logger.info(
            f"Batch analysis complete: {stats['successful']}/{total_files} successful "
            f"({stats['duration_sec']:.1f}s total)"
        )

        return {
            "results": results,
            "stats": stats,
            "failures": failures
        }

    def _call_vision_api_with_retry(
        self,
        image_data: str,
        media_type: str,
        image_path: str
    ) -> Optional[Dict]:
        """
        Call Claude Vision API with exponential backoff retry logic.

        Args:
            image_data: Base64 encoded image
            media_type: MIME type of image
            image_path: Original image path (for logging)

        Returns:
            Parsed JSON from response or None
        """
        retry_count = 0
        delay = RetryConfig.initial_delay

        while retry_count < RetryConfig.max_retries:
            try:
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
                    return prescription_data
                else:
                    logger.warning("Failed to parse JSON from API response")
                    return None

            except RateLimitError as e:
                retry_count += 1
                self._stats["api_retry_count"] += 1

                if retry_count >= RetryConfig.max_retries:
                    logger.error(
                        f"Rate limit exceeded after {retry_count} retries: {image_path}"
                    )
                    return None

                logger.warning(
                    f"Rate limited. Retry {retry_count}/{RetryConfig.max_retries} "
                    f"after {delay:.1f}s"
                )
                time.sleep(delay)
                delay = min(delay * RetryConfig.backoff_multiplier, RetryConfig.max_delay)

            except APIError as e:
                retry_count += 1
                self._stats["api_retry_count"] += 1

                if retry_count >= RetryConfig.max_retries:
                    logger.error(
                        f"API error after {retry_count} retries: {type(e).__name__}: {e}"
                    )
                    return None

                logger.warning(
                    f"API error: {type(e).__name__}. "
                    f"Retry {retry_count}/{RetryConfig.max_retries} after {delay:.1f}s"
                )
                time.sleep(delay)
                delay = min(delay * RetryConfig.backoff_multiplier, RetryConfig.max_delay)

            except Exception as e:
                logger.error(
                    f"Unexpected error calling Vision API: {type(e).__name__}: {e}",
                    exc_info=True
                )
                return None

        return None

    def _validate_image_path(self, image_path: str) -> bool:
        """
        Validate image path exists and is a supported format.

        Args:
            image_path: Path to check

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(image_path)

            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return False

            if not path.is_file():
                logger.error(f"Path is not a file: {image_path}")
                return False

            supported_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
            if path.suffix.lower() not in supported_extensions:
                logger.error(
                    f"Unsupported file type: {path.suffix}. "
                    f"Supported: {', '.join(supported_extensions)}"
                )
                return False

            # Check file size (max 20MB for safety)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 20:
                logger.error(f"File too large: {file_size_mb:.1f}MB (max 20MB)")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating image path: {e}")
            return False

    def _read_image_as_base64(self, image_path: str) -> Optional[str]:
        """
        Read image file and encode as base64.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image data or None
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            if len(image_data) == 0:
                logger.error(f"Image file is empty: {image_path}")
                return None

            return base64.standard_b64encode(image_data).decode("utf-8")

        except IOError as e:
            logger.error(f"I/O error reading image: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading image: {type(e).__name__}: {e}")
            return None

    @staticmethod
    def _get_media_type(image_path: str) -> str:
        """
        Determine MIME type from file extension.

        Args:
            image_path: Path to image file

        Returns:
            MIME type string (default: image/jpeg)
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
        Parse JSON from Claude response with error handling.

        Args:
            response_text: Response text from Claude

        Returns:
            Parsed JSON dictionary or None
        """
        try:
            # Find JSON block in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start == -1 or json_end <= json_start:
                logger.warning("No JSON found in response")
                return None

            json_str = response_text[json_start:json_end]

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {type(e).__name__}: {e}")
            return None

    def validate_extracted_data(self, prescription_data: Dict) -> bool:
        """
        Validate extracted prescription data completeness and structure.

        Args:
            prescription_data: Extracted prescription data

        Returns:
            True if data is valid, False otherwise
        """
        try:
            required_fields = ["patient", "medications", "metadata"]

            # Check top-level fields
            for field in required_fields:
                if field not in prescription_data:
                    logger.warning(f"Missing required field: {field}")
                    return False

            # Check patient fields
            patient = prescription_data.get("patient", {})
            patient_required = ["name", "age", "sex"]

            for field in patient_required:
                if field not in patient or patient[field] is None:
                    logger.warning(f"Missing patient field: {field}")
                    return False

            # Validate age is numeric
            try:
                age = int(patient.get("age", 0))
                if age < 0 or age > 150:
                    logger.warning(f"Invalid age value: {age}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Age is not numeric: {patient.get('age')}")
                return False

            # Check medications
            medications = prescription_data.get("medications", [])
            if not isinstance(medications, list):
                logger.warning("Medications field is not a list")
                return False

            if len(medications) == 0:
                logger.warning("No medications found in prescription")
                return False

            # Validate medication entries
            for idx, med in enumerate(medications):
                if not isinstance(med, dict):
                    logger.warning(f"Medication {idx} is not a dictionary")
                    return False

                if "name" not in med or not med.get("name"):
                    logger.warning(f"Medication {idx} missing name")
                    return False

            logger.info("Prescription data validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating data: {type(e).__name__}: {e}")
            return False

    def get_statistics(self) -> Dict:
        """
        Get performance statistics for this agent.

        Returns:
            Dictionary with statistics
        """
        total = self._stats["total_analyses"]
        successful = self._stats["successful_analyses"]

        return {
            "total_analyses": total,
            "successful_analyses": successful,
            "failed_analyses": self._stats["failed_analyses"],
            "success_rate_percent": (successful / total * 100) if total > 0 else 0,
            "total_duration_sec": self._stats["total_duration_sec"],
            "avg_duration_sec": self._stats["total_duration_sec"] / successful if successful > 0 else 0,
            "api_retry_count": self._stats["api_retry_count"]
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        agent = AgentOCRVision()

        prescription_dir = "./prescription_images"
        if os.path.exists(prescription_dir):
            # Batch analysis with statistics
            results = agent.batch_analyze_prescriptions(
                prescription_dir,
                show_progress=True
            )

            # Print statistics
            stats = agent.get_statistics()
            logger.info(f"\nAgent Statistics:")
            for key, value in stats.items():
                if isinstance(value, float):
                    logger.info(f"  {key}: {value:.2f}")
                else:
                    logger.info(f"  {key}: {value}")

            # Print summary
            logger.info(f"\nBatch Results:")
            logger.info(f"  Successful: {results['stats']['successful']}/{results['stats']['total']}")
            logger.info(f"  Duration: {results['stats']['duration_sec']:.1f}s")

            if results['failures']:
                logger.warning(f"\nFailures:")
                for failure in results['failures']:
                    logger.warning(f"  {failure['file']}: {failure['reason']}")
        else:
            logger.error(f"Directory not found: {prescription_dir}")

    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}", exc_info=True)
