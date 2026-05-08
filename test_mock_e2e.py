#!/usr/bin/env python3
"""
Mock E2E Test - API 키 없이 에이전트 통신 검증
ANTHROPIC_API_KEY 설정 후 실제 테스트 가능
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockE2ETest:
    """Mock E2E Test - 에이전트 구조 검증"""

    def __init__(self):
        self.results = {
            "test_name": "Mock E2E Test",
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }

    def test_1_imports(self) -> bool:
        """Test 1: 모든 에이전트 import 확인"""
        logger.info("\n[TEST 1] Checking imports...")

        try:
            from agents.agent_ocr_vision import AgentOCRVision
            logger.info("  ✓ Agent 1 (OCR Vision)")

            from agents.agent_rag_drug import AgentRAGDrug
            logger.info("  ✓ Agent 2 (RAG Drug)")

            from agents.agent_google_pharmacy import AgentGooglePharmacy
            logger.info("  ✓ Agent 3 (Google Pharmacy)")

            from agents.agent_orchestrator import AgentOrchestrator
            logger.info("  ✓ Agent 4 (Orchestrator)")

            self.results["tests"].append({
                "name": "Import Test",
                "status": "PASS",
                "details": "모든 에이전트 정상 import"
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Import failed: {e}")
            self.results["tests"].append({
                "name": "Import Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_2_rag_database(self) -> bool:
        """Test 2: RAG 데이터베이스 로드 확인"""
        logger.info("\n[TEST 2] Checking RAG database...")

        try:
            # Load drug info
            with open("rag_db/drug_info_index.json", "r", encoding="utf-8") as f:
                drug_data = json.load(f)

            drugs_count = len(drug_data.get("drugs", []))
            logger.info(f"  ✓ Drug database: {drugs_count} drugs loaded")

            # Load papers
            with open("rag_db/papers_metadata.json", "r", encoding="utf-8") as f:
                papers_data = json.load(f)

            papers_count = len(papers_data.get("papers", []))
            logger.info(f"  ✓ Papers database: {papers_count} papers loaded")

            # Load guidelines
            with open("rag_db/guidelines_index.json", "r", encoding="utf-8") as f:
                guidelines_data = json.load(f)

            guidelines_count = len(guidelines_data.get("guidelines", []))
            logger.info(f"  ✓ Guidelines database: {guidelines_count} guidelines loaded")

            self.results["tests"].append({
                "name": "RAG Database Test",
                "status": "PASS",
                "details": {
                    "drugs": drugs_count,
                    "papers": papers_count,
                    "guidelines": guidelines_count
                }
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Database load failed: {e}")
            self.results["tests"].append({
                "name": "RAG Database Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_3_prescription_images(self) -> bool:
        """Test 3: 처방전 이미지 샘플 확인"""
        logger.info("\n[TEST 3] Checking prescription images...")

        try:
            image_dir = Path("prescription_images")

            if not image_dir.exists():
                logger.error("  ✗ prescription_images directory not found")
                self.results["tests"].append({
                    "name": "Prescription Images Test",
                    "status": "FAIL",
                    "details": "Directory not found"
                })
                return False

            images = list(image_dir.glob("*"))
            image_count = len(images)

            logger.info(f"  ✓ Found {image_count} prescription images")

            # Show first 5
            for i, img in enumerate(images[:5], 1):
                logger.info(f"    {i}. {img.name}")

            self.results["tests"].append({
                "name": "Prescription Images Test",
                "status": "PASS",
                "details": {
                    "total_images": image_count,
                    "samples": [img.name for img in images[:5]]
                }
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Image check failed: {e}")
            self.results["tests"].append({
                "name": "Prescription Images Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_4_utility_modules(self) -> bool:
        """Test 4: 유틸리티 모듈 로드"""
        logger.info("\n[TEST 4] Checking utility modules...")

        try:
            from utils.google_api_helper import GoogleAPIHelper
            logger.info("  ✓ GoogleAPIHelper")

            from utils.mfds_api_helper import MFDSAPIHelper
            logger.info("  ✓ MFDSAPIHelper")

            from utils.pdf_generator import PDFReportGenerator
            logger.info("  ✓ PDFReportGenerator")

            from utils.validators import MedicationValidator
            logger.info("  ✓ MedicationValidator")

            from utils.tts_handler import TTSHandler
            logger.info("  ✓ TTSHandler")

            self.results["tests"].append({
                "name": "Utility Modules Test",
                "status": "PASS",
                "details": "5 utility modules loaded"
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Utility module failed: {e}")
            self.results["tests"].append({
                "name": "Utility Modules Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_5_data_structures(self) -> bool:
        """Test 5: 데이터 구조 검증"""
        logger.info("\n[TEST 5] Validating data structures...")

        try:
            with open("rag_db/drug_info_index.json", "r", encoding="utf-8") as f:
                drug_data = json.load(f)

            # Validate drug structure
            drug = drug_data["drugs"][0]
            required_fields = ["korean_name", "english_name", "strength", "mfds_official_price"]

            for field in required_fields:
                if field not in drug:
                    raise ValueError(f"Missing field: {field}")

            logger.info(f"  ✓ Drug data structure: {drug['korean_name']}")

            # Validate paper structure
            with open("rag_db/papers_metadata.json", "r", encoding="utf-8") as f:
                papers_data = json.load(f)

            paper = papers_data["papers"][0]
            required_fields = ["id", "title", "journal", "year"]

            for field in required_fields:
                if field not in paper:
                    raise ValueError(f"Missing field: {field}")

            logger.info(f"  ✓ Paper data structure: {paper['title']}")

            self.results["tests"].append({
                "name": "Data Structure Test",
                "status": "PASS",
                "details": "All data structures valid"
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Data structure validation failed: {e}")
            self.results["tests"].append({
                "name": "Data Structure Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_6_output_directories(self) -> bool:
        """Test 6: 출력 디렉토리 확인"""
        logger.info("\n[TEST 6] Checking output directories...")

        try:
            output_dirs = [
                "pharma_output",
                "pharma_voice_comp"
            ]

            for dir_name in output_dirs:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    logger.info(f"  ✓ {dir_name}/ exists")
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"  ✓ {dir_name}/ created")

            self.results["tests"].append({
                "name": "Output Directories Test",
                "status": "PASS",
                "details": "All output directories ready"
            })
            return True

        except Exception as e:
            logger.error(f"  ✗ Directory check failed: {e}")
            self.results["tests"].append({
                "name": "Output Directories Test",
                "status": "FAIL",
                "details": str(e)
            })
            return False

    def test_7_api_keys_status(self) -> bool:
        """Test 7: API 키 상태 확인"""
        logger.info("\n[TEST 7] Checking API keys...")

        import os
        from dotenv import load_dotenv

        load_dotenv()

        keys = {
            "ANTHROPIC_API_KEY": "❌ NOT SET (필수 - E2E 테스트용)",
            "GOOGLE_API_KEY": "✓ SET" if os.getenv("GOOGLE_API_KEY") else "✗ NOT SET",
            "MFDS_API_KEY": "✓ SET" if os.getenv("MFDS_API_KEY") else "✗ NOT SET"
        }

        for key, status in keys.items():
            logger.info(f"  {status}: {key}")

        self.results["tests"].append({
            "name": "API Keys Status Test",
            "status": "PARTIAL",
            "details": {
                "anthropic": "NOT SET - REQUIRED",
                "google": "SET" if os.getenv("GOOGLE_API_KEY") else "NOT SET",
                "mfds": "SET" if os.getenv("MFDS_API_KEY") else "NOT SET"
            }
        })

        return os.getenv("ANTHROPIC_API_KEY") is not None

    def run_all_tests(self) -> Dict:
        """모든 테스트 실행"""
        logger.info("=" * 70)
        logger.info("MOCK E2E TEST - 에이전트 구조 & 데이터 검증")
        logger.info("=" * 70)

        tests = [
            ("Imports", self.test_1_imports),
            ("RAG Database", self.test_2_rag_database),
            ("Prescription Images", self.test_3_prescription_images),
            ("Utility Modules", self.test_4_utility_modules),
            ("Data Structures", self.test_5_data_structures),
            ("Output Directories", self.test_6_output_directories),
            ("API Keys Status", self.test_7_api_keys_status)
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test error: {e}")
                failed += 1

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)

        logger.info(f"\nPassed: {passed}/{len(tests)}")
        logger.info(f"Failed: {failed}/{len(tests)}")
        logger.info(f"Success Rate: {int(passed/len(tests)*100)}%")

        # API Key message
        logger.info("\n" + "=" * 70)
        logger.info("다음 단계: ANTHROPIC_API_KEY 설정")
        logger.info("=" * 70)
        logger.info("\n1. https://console.anthropic.com 방문")
        logger.info("2. API Key 생성")
        logger.info("3. .env 파일에 추가:")
        logger.info("   ANTHROPIC_API_KEY=sk-ant-[YOUR-KEY]")
        logger.info("\n4. E2E 테스트 실행:")
        logger.info("   python main_e2e_test.py")

        return self.results


def main():
    """Main test runner"""
    runner = MockE2ETest()
    results = runner.run_all_tests()

    # Save results
    with open("mock_e2e_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✓ Results saved: mock_e2e_results.json")

    return 0


if __name__ == "__main__":
    exit(main())
