#!/usr/bin/env python3
"""
Performance Benchmarking Suite for SHIELD PHARMA-HYBRID v21.0
Measures optimization improvements across all agents and utilities
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Run comprehensive performance benchmarks."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {},
            "summary": {}
        }

    def benchmark_drug_search(self):
        """Benchmark drug information search performance."""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Drug Information Search")
        logger.info("="*70)

        try:
            from agents.agent_rag_drug_optimized import AgentRAGDrug

            agent = AgentRAGDrug()

            # Test cases
            drugs = [
                "노바스크정",
                "글루코판정",
                "타그리소",
                "노바스크 정",  # Typo
                "Amlodipine"  # English name
            ]

            results = {
                "direct_lookup": [],
                "fuzzy_matching": [],
                "cache_hit_rate": 0
            }

            logger.info(f"Testing {len(drugs)} drug searches...")

            # First pass - cold cache
            cold_times = []
            for drug in drugs:
                start = time.time()
                result = agent.search_drug_info(drug, fuzzy_match=True)
                duration = (time.time() - start) * 1000  # Convert to ms
                cold_times.append(duration)
                logger.info(f"  {drug}: {duration:.2f}ms {'✓' if result else '✗'}")

            # Second pass - warm cache
            warm_times = []
            for drug in drugs:
                start = time.time()
                result = agent.search_drug_info(drug, fuzzy_match=True)
                duration = (time.time() - start) * 1000  # Convert to ms
                warm_times.append(duration)

            # Get statistics
            stats = agent.get_statistics()

            results["cold_cache_avg_ms"] = sum(cold_times) / len(cold_times)
            results["warm_cache_avg_ms"] = sum(warm_times) / len(warm_times)
            results["cache_hit_rate_percent"] = stats.get('cache_hit_rate_percent', 0)
            results["improvement_percent"] = (
                (results["cold_cache_avg_ms"] - results["warm_cache_avg_ms"]) /
                results["cold_cache_avg_ms"] * 100
            )

            logger.info(f"\nResults:")
            logger.info(f"  Cold cache average: {results['cold_cache_avg_ms']:.2f}ms")
            logger.info(f"  Warm cache average: {results['warm_cache_avg_ms']:.2f}ms")
            logger.info(f"  Improvement: {results['improvement_percent']:.1f}%")
            logger.info(f"  Cache hit rate: {results['cache_hit_rate_percent']:.1f}%")

            self.results["benchmarks"]["drug_search"] = results
            return results

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
            return None

    def benchmark_batch_prescription_processing(self):
        """Benchmark batch prescription image processing."""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Batch Prescription Processing")
        logger.info("="*70)

        try:
            from agents.agent_ocr_vision_optimized import AgentOCRVision

            agent = AgentOCRVision()
            image_dir = Path("./prescription_images")

            if not image_dir.exists():
                logger.warning(f"Image directory not found: {image_dir}")
                return None

            # Count images
            image_files = list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpg"))
            image_count = len(image_files)

            if image_count == 0:
                logger.warning("No prescription images found")
                return None

            logger.info(f"Found {image_count} prescription images")

            # Run batch processing
            logger.info(f"Starting batch processing...")
            start_time = time.time()

            results = agent.batch_analyze_prescriptions(
                str(image_dir),
                show_progress=True
            )

            total_duration = time.time() - start_time

            # Extract metrics
            stats = agent.get_statistics()

            benchmark_results = {
                "total_images": image_count,
                "successful": results['stats']['successful'],
                "failed": results['stats']['failed'],
                "success_rate_percent": (
                    results['stats']['successful'] / image_count * 100
                    if image_count > 0 else 0
                ),
                "total_duration_sec": total_duration,
                "avg_per_image_sec": total_duration / image_count if image_count > 0 else 0,
                "api_retry_count": stats.get('api_retry_count', 0),
                "failed_analyses": stats.get('failed_analyses', 0)
            }

            logger.info(f"\nResults:")
            logger.info(f"  Total images: {benchmark_results['total_images']}")
            logger.info(f"  Successful: {benchmark_results['successful']}")
            logger.info(f"  Success rate: {benchmark_results['success_rate_percent']:.1f}%")
            logger.info(f"  Total duration: {benchmark_results['total_duration_sec']:.1f}s")
            logger.info(f"  Average per image: {benchmark_results['avg_per_image_sec']:.2f}s")
            logger.info(f"  API retries: {benchmark_results['api_retry_count']}")

            self.results["benchmarks"]["batch_processing"] = benchmark_results
            return benchmark_results

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
            return None

    def benchmark_error_recovery(self):
        """Benchmark error recovery and retry logic."""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Error Recovery & Retry Logic")
        logger.info("="*70)

        try:
            from agents.agent_ocr_vision_optimized import AgentOCRVision, RetryConfig

            logger.info(f"Retry configuration:")
            logger.info(f"  Max retries: {RetryConfig.max_retries}")
            logger.info(f"  Initial delay: {RetryConfig.initial_delay}s")
            logger.info(f"  Max delay: {RetryConfig.max_delay}s")
            logger.info(f"  Backoff multiplier: {RetryConfig.backoff_multiplier}x")

            # Simulate retry delays
            delays = []
            delay = RetryConfig.initial_delay

            for attempt in range(1, RetryConfig.max_retries + 1):
                delays.append(delay)
                delay = min(
                    delay * RetryConfig.backoff_multiplier,
                    RetryConfig.max_delay
                )

            total_retry_time = sum(delays)

            results = {
                "max_retries": RetryConfig.max_retries,
                "backoff_sequence": delays,
                "total_max_retry_time_sec": total_retry_time,
                "success_rate_with_retries_percent": 95.0  # Estimated
            }

            logger.info(f"\nRetry Sequence:")
            for attempt, delay in enumerate(delays, 1):
                logger.info(f"  Attempt {attempt}: wait {delay}s")

            logger.info(f"\nResults:")
            logger.info(f"  Total max retry time: {total_retry_time:.1f}s")
            logger.info(f"  Estimated recovery rate: {results['success_rate_with_retries_percent']:.1f}%")

            self.results["benchmarks"]["error_recovery"] = results
            return results

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
            return None

    def benchmark_data_validation(self):
        """Benchmark data validation performance."""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK: Data Validation")
        logger.info("="*70)

        try:
            from agents.agent_ocr_vision_optimized import AgentOCRVision

            agent = AgentOCRVision()

            # Test cases
            test_data = [
                {
                    "name": "Valid prescription",
                    "data": {
                        "patient": {
                            "name": "김철수",
                            "age": 68,
                            "sex": "M",
                            "diagnosis_primary": "고혈압"
                        },
                        "medications": [
                            {"name": "노바스크정", "strength": "5mg", "quantity": "30"}
                        ],
                        "metadata": {"prescription_date": "2024-01-15"}
                    },
                    "should_pass": True
                },
                {
                    "name": "Missing patient field",
                    "data": {
                        "patient": {"name": "김철수"},
                        "medications": [{"name": "노바스크정"}],
                        "metadata": {}
                    },
                    "should_pass": False
                },
                {
                    "name": "Empty medications",
                    "data": {
                        "patient": {"name": "김철수", "age": 68, "sex": "M"},
                        "medications": [],
                        "metadata": {}
                    },
                    "should_pass": False
                },
                {
                    "name": "Invalid age",
                    "data": {
                        "patient": {"name": "김철수", "age": 999, "sex": "M"},
                        "medications": [{"name": "약물"}],
                        "metadata": {}
                    },
                    "should_pass": False
                }
            ]

            results = {
                "total_tests": len(test_data),
                "passed": 0,
                "failed": 0,
                "details": []
            }

            logger.info(f"Running {len(test_data)} validation tests...")

            for test in test_data:
                start = time.time()
                is_valid = agent.validate_extracted_data(test["data"])
                duration = (time.time() - start) * 1000

                passed = is_valid == test["should_pass"]

                results["details"].append({
                    "name": test["name"],
                    "expected": test["should_pass"],
                    "actual": is_valid,
                    "passed": passed,
                    "duration_ms": duration
                })

                if passed:
                    results["passed"] += 1
                    logger.info(f"  ✓ {test['name']} ({duration:.2f}ms)")
                else:
                    results["failed"] += 1
                    logger.error(f"  ✗ {test['name']} (expected {test['should_pass']}, got {is_valid})")

            results["success_rate_percent"] = (
                results["passed"] / results["total_tests"] * 100
                if results["total_tests"] > 0 else 0
            )

            logger.info(f"\nResults:")
            logger.info(f"  Passed: {results['passed']}/{results['total_tests']}")
            logger.info(f"  Success rate: {results['success_rate_percent']:.1f}%")

            self.results["benchmarks"]["data_validation"] = results
            return results

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
            return None

    def generate_summary(self) -> Dict:
        """Generate benchmark summary with recommendations."""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*70)

        summary = {
            "total_benchmarks": len(self.results["benchmarks"]),
            "completed": sum(
                1 for b in self.results["benchmarks"].values() if b is not None
            ),
            "targets_met": 0,
            "recommendations": []
        }

        # Check drug search performance
        if "drug_search" in self.results["benchmarks"]:
            ds = self.results["benchmarks"]["drug_search"]
            if ds and ds.get("warm_cache_avg_ms", 999) < 5:
                summary["targets_met"] += 1
                logger.info("✓ Drug search performance TARGET MET")
            else:
                summary["recommendations"].append(
                    "Optimize drug index building or consider more aggressive caching"
                )

        # Check batch processing performance
        if "batch_processing" in self.results["benchmarks"]:
            bp = self.results["benchmarks"]["batch_processing"]
            if bp and bp.get("avg_per_image_sec", 999) < 3:
                summary["targets_met"] += 1
                logger.info("✓ Batch processing performance TARGET MET")
            else:
                summary["recommendations"].append(
                    "Consider parallel processing for batch image analysis"
                )

            if bp and bp.get("success_rate_percent", 0) > 95:
                summary["targets_met"] += 1
                logger.info("✓ Success rate TARGET MET")
            else:
                summary["recommendations"].append(
                    "Improve retry logic or API error handling"
                )

        # Check validation performance
        if "data_validation" in self.results["benchmarks"]:
            dv = self.results["benchmarks"]["data_validation"]
            if dv and dv.get("success_rate_percent", 0) == 100:
                summary["targets_met"] += 1
                logger.info("✓ Data validation performance TARGET MET")
            else:
                summary["recommendations"].append(
                    "Review failing validation test cases"
                )

        self.results["summary"] = summary
        return summary

    def save_results(self, filename: str = "benchmark_results.json") -> str:
        """Save benchmark results to JSON file."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            logger.info(f"\nResults saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None

    def run_all_benchmarks(self):
        """Run all benchmarks and generate report."""
        logger.info("="*70)
        logger.info("SHIELD PHARMA-HYBRID v21.0 - PERFORMANCE BENCHMARKS")
        logger.info("="*70)

        self.benchmark_drug_search()
        self.benchmark_batch_prescription_processing()
        self.benchmark_error_recovery()
        self.benchmark_data_validation()

        self.generate_summary()

        # Save results
        self.save_results("benchmark_results.json")

        # Print final summary
        logger.info("\n" + "="*70)
        logger.info("FINAL RESULTS")
        logger.info("="*70)
        logger.info(f"Benchmarks completed: {self.results['summary']['completed']}/{self.results['summary']['total_benchmarks']}")
        logger.info(f"Performance targets met: {self.results['summary']['targets_met']}")

        if self.results['summary']['recommendations']:
            logger.info("\nRecommendations:")
            for i, rec in enumerate(self.results['summary']['recommendations'], 1):
                logger.info(f"  {i}. {rec}")

        return self.results


def main():
    """Main entry point."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()

    # Print JSON summary
    print("\n" + json.dumps(results["summary"], indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
