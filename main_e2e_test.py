#!/usr/bin/env python3
"""
E2E Test - End-to-End Prescription Processing
33개 처방전 샘플로 완전한 파이프라인 검증
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from agents.agent_orchestrator import AgentOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """E2E Test Runner"""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.results = {
            "total_tests": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "processed_prescriptions": [],
            "errors": []
        }

    def discover_prescription_images(self, directory: str = "prescription_images") -> List[Path]:
        """
        Discover prescription image files

        Args:
            directory: Directory to search

        Returns:
            List of image file paths
        """
        image_dir = Path(directory)

        if not image_dir.exists():
            logger.error(f"Directory not found: {directory}")
            return []

        # Supported image formats
        extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        images = [f for f in image_dir.glob("*") if f.suffix.lower() in extensions]

        logger.info(f"Found {len(images)} prescription images")
        return sorted(images)

    def process_single_prescription(self, image_path: Path) -> Dict:
        """
        Process single prescription image

        Args:
            image_path: Path to prescription image

        Returns:
            Processing result
        """
        result = {
            "image": image_path.name,
            "status": "pending",
            "error": None,
            "report_id": None,
            "files_generated": []
        }

        try:
            logger.info(f"Processing: {image_path.name}")

            # Process prescription
            report = self.orchestrator.process_prescription_image(str(image_path))

            if not report:
                result["status"] = "failed"
                result["error"] = "Failed to generate report"
                return result

            # Generate output files
            files = self.orchestrator.generate_reports(report)

            result["status"] = "success"
            result["report_id"] = report.get("report_id")
            result["files_generated"] = list(files.keys())

            logger.info(f"✓ {image_path.name}: {report.get('report_id')}")

            return result

        except Exception as e:
            logger.error(f"✗ {image_path.name}: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            return result

    def run_e2e_tests(self, max_samples: int = None) -> Dict:
        """
        Run E2E tests on prescription images

        Args:
            max_samples: Maximum samples to process (None = all)

        Returns:
            Test results summary
        """
        logger.info("=" * 70)
        logger.info("E2E TEST - PRESCRIPTION PROCESSING PIPELINE")
        logger.info("=" * 70)

        # Discover images
        images = self.discover_prescription_images()

        if not images:
            logger.error("No prescription images found")
            return self.results

        if max_samples:
            images = images[:max_samples]

        self.results["total_tests"] = len(images)

        # Process each image
        for idx, image_path in enumerate(images, 1):
            logger.info(f"\n[{idx}/{len(images)}] Processing {image_path.name}")

            result = self.process_single_prescription(image_path)

            if result["status"] == "success":
                self.results["successful"] += 1
            elif result["status"] == "failed":
                self.results["failed"] += 1
                self.results["errors"].append({
                    "image": image_path.name,
                    "error": result.get("error")
                })
            else:
                self.results["skipped"] += 1

            self.results["processed_prescriptions"].append(result)

        # Finalize results
        self.results["end_time"] = datetime.now().isoformat()

        return self.results

    def generate_test_report(self, output_file: str = "e2e_test_report.json") -> None:
        """
        Generate test report

        Args:
            output_file: Output file path
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            logger.info(f"\nTest report saved: {output_file}")

        except Exception as e:
            logger.error(f"Error saving test report: {e}")

    def print_summary(self) -> None:
        """Print test summary"""
        print("\n" + "=" * 70)
        print("E2E TEST SUMMARY")
        print("=" * 70)

        print(f"\nTotal Tests: {self.results['total_tests']}")
        print(f"Successful: {self.results['successful']} ({self._percentage(self.results['successful'], self.results['total_tests'])}%)")
        print(f"Failed: {self.results['failed']} ({self._percentage(self.results['failed'], self.results['total_tests'])}%)")
        print(f"Skipped: {self.results['skipped']}")

        if self.results["errors"]:
            print(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results["errors"][:5]:  # Show first 5
                print(f"  - {error['image']}: {error['error'][:60]}...")

        success_rate = self._percentage(self.results['successful'], self.results['total_tests'])
        print(f"\nSuccess Rate: {success_rate}%")
        print(f"Start Time: {self.results['start_time']}")
        print(f"End Time: {self.results['end_time']}")

        if success_rate >= 90:
            print("\n✓ E2E TEST PASSED")
        elif success_rate >= 70:
            print("\n⚠ E2E TEST PARTIAL PASS (70-90%)")
        else:
            print("\n✗ E2E TEST FAILED")

    @staticmethod
    def _percentage(value: int, total: int) -> int:
        """Calculate percentage"""
        return int((value / total * 100)) if total > 0 else 0


def main():
    """Main test function"""
    try:
        # Initialize test runner
        runner = E2ETestRunner()

        # Run E2E tests (limit to 5 for quick test, remove for full)
        results = runner.run_e2e_tests(max_samples=5)

        # Generate report
        runner.generate_test_report()

        # Print summary
        runner.print_summary()

        return 0 if runner.results["failed"] == 0 else 1

    except Exception as e:
        logger.error(f"Test runner error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
