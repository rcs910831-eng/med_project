#!/usr/bin/env python3
"""
Render 배포 검증 스크립트
배포된 서비스의 모든 엔드포인트를 자동으로 테스트합니다.
"""

import requests
import json
import sys
from datetime import datetime

class DeploymentValidator:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.results = []

    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")

    def print_test(self, name, status, details=""):
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
        if details:
            print(f"   └─ {details}")
        self.results.append((name, status))

    def test_health_check(self):
        """헬스 체크 테스트"""
        self.print_header("1️⃣ 헬스 체크 테스트")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    "Health Endpoint",
                    True,
                    f"Status: {data.get('status')}"
                )
                return True
            else:
                self.print_test("Health Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Health Endpoint", False, str(e))
            return False

    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        self.print_header("2️⃣ API 엔드포인트 테스트")

        endpoints = [
            ("GET", "/health", None),
            ("GET", "/docs", None),
            ("POST", "/api/user/register", {"user_id": "test", "password": "test"}),
            ("GET", "/api/user/test", None),
        ]

        passed = 0
        for method, endpoint, data in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"

                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(
                        url,
                        json=data,
                        timeout=5,
                        headers={"Content-Type": "application/json"}
                    )

                success = 200 <= response.status_code < 300
                self.print_test(
                    f"{method} {endpoint}",
                    success,
                    f"HTTP {response.status_code}"
                )
                if success:
                    passed += 1
            except Exception as e:
                self.print_test(f"{method} {endpoint}", False, str(e))

        return passed

    def test_swagger_ui(self):
        """Swagger UI 접근 테스트"""
        self.print_header("3️⃣ Swagger UI 테스트")

        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            success = response.status_code == 200 and "swagger" in response.text.lower()
            self.print_test(
                "Swagger UI",
                success,
                "API 문서 페이지 로드"
            )
            return success
        except Exception as e:
            self.print_test("Swagger UI", False, str(e))
            return False

    def test_database_connectivity(self):
        """데이터베이스 연결 테스트"""
        self.print_header("4️⃣ 데이터베이스 연결 테스트")

        try:
            response = requests.post(
                f"{self.base_url}/api/user/register",
                json={"user_id": f"test_{int(datetime.now().timestamp())}", "password": "test123"},
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code in [200, 201, 400]  # 400은 이미 존재하는 경우
            self.print_test(
                "Database Write",
                success,
                "사용자 등록 요청 성공"
            )
            return success
        except Exception as e:
            self.print_test("Database Write", False, str(e))
            return False

    def test_voice_endpoints(self):
        """음성 엔드포인트 테스트"""
        self.print_header("5️⃣ 음성 기능 테스트")

        endpoints = [
            "/api/voice/transcribe",
            "/api/voice/synthesize",
            "/api/voice/health-analyze"
        ]

        passed = 0
        for endpoint in endpoints:
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    timeout=5
                )
                # 엔드포인트가 존재하는지 확인 (400/422 = 존재, 404 = 없음)
                exists = response.status_code != 404
                self.print_test(
                    f"POST {endpoint}",
                    exists,
                    f"Endpoint Status: HTTP {response.status_code}"
                )
                if exists:
                    passed += 1
            except Exception as e:
                self.print_test(f"POST {endpoint}", False, str(e))

        return passed

    def test_performance(self):
        """성능 테스트"""
        self.print_header("6️⃣ 성능 테스트")

        try:
            import time
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=5)
            elapsed = (time.time() - start) * 1000  # milliseconds

            success = elapsed < 1000  # 1초 이내
            self.print_test(
                "Response Time",
                success,
                f"응답 시간: {elapsed:.0f}ms"
            )
            return success
        except Exception as e:
            self.print_test("Response Time", False, str(e))
            return False

    def print_summary(self):
        """요약 리포트"""
        self.print_header("📊 배포 검증 결과")

        total = len(self.results)
        passed = sum(1 for _, status in self.results if status)

        print(f"전체: {total}개")
        print(f"성공: {passed}개 ✅")
        print(f"실패: {total - passed}개 ❌")
        print(f"성공률: {(passed/total*100):.1f}%\n")

        if passed == total:
            print("🎉 모든 테스트 통과! 배포가 완벽하게 완료되었습니다!\n")
            return True
        else:
            print("⚠️  일부 테스트가 실패했습니다. 로그를 확인하세요.\n")
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        print(f"\n🚀 배포 검증 시작: {self.base_url}\n")
        print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.test_health_check()
        self.test_swagger_ui()
        self.test_api_endpoints()
        self.test_database_connectivity()
        self.test_voice_endpoints()
        self.test_performance()

        success = self.print_summary()

        return success


def main():
    if len(sys.argv) < 2:
        print("\n사용법:")
        print("  python validate_deployment.py <배포_URL>\n")
        print("예시:")
        print("  python validate_deployment.py https://pharma-mobile-backend-abc123.onrender.com\n")
        return False

    base_url = sys.argv[1]

    # URL 검증
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url

    validator = DeploymentValidator(base_url)
    success = validator.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
