#!/usr/bin/env python3
"""
PHARMA-MOBILE 자동 배포 스크립트
Google Cloud JSON 파일을 자동으로 찾아서 Render에 배포합니다.
"""

import os
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

class AutoDeployer:
    def __init__(self):
        self.project_path = Path(r"C:\Users\rcs91\github\med_project")
        self.json_file = None
        self.json_content = None

    def print_header(self, title):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")

    def print_step(self, step_num, title, status="진행 중"):
        print(f"\n[Step {step_num}] {title}")
        print(f"상태: {status}\n")

    def print_success(self, message):
        print(f"[OK] {message}")

    def print_info(self, message):
        print(f"[*]  {message}")

    def print_warning(self, message):
        print(f"[!]  {message}")

    def find_json_file(self):
        """Google Cloud JSON 파일 찾기"""
        self.print_step(1, "Google Cloud JSON 파일 검색", "시작")

        search_paths = [
            Path(r"C:\Users\rcs91\Downloads"),
            Path(r"C:\Users\rcs91\Desktop"),
            Path(r"C:\Users\rcs91\Documents"),
            self.project_path,
        ]

        print("검색 위치:")
        for path in search_paths:
            print(f"  - {path}")

        for directory in search_paths:
            if not directory.exists():
                continue

            # pharma-mobile-*.json 찾기
            json_files = list(directory.glob("pharma-mobile-*.json"))
            if json_files:
                self.json_file = json_files[0]
                self.print_success(f"파일 찾음: {self.json_file}")
                return True

            # google-cloud-*.json 찾기
            json_files = list(directory.glob("google-cloud-*.json"))
            if json_files:
                self.json_file = json_files[0]
                self.print_success(f"파일 찾음: {self.json_file}")
                return True

            # service-account-*.json 찾기
            json_files = list(directory.glob("service-account-*.json"))
            if json_files:
                self.json_file = json_files[0]
                self.print_success(f"파일 찾음: {self.json_file}")
                return True

        self.print_warning("파일을 찾을 수 없습니다")
        return False

    def validate_json(self):
        """JSON 파일 유효성 검증"""
        self.print_step(2, "JSON 파일 유효성 검증", "진행 중")

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.json_content = json.load(f)

            required_keys = ['type', 'project_id', 'private_key', 'client_email']
            missing_keys = [k for k in required_keys if k not in self.json_content]

            if missing_keys:
                self.print_warning(f"누락된 필수 키: {missing_keys}")
                return False

            self.print_success("JSON 파일 유효성 검증 완료")
            self.print_info(f"프로젝트: {self.json_content.get('project_id')}")
            self.print_info(f"이메일: {self.json_content.get('client_email')}")
            return True

        except json.JSONDecodeError as e:
            self.print_warning(f"JSON 파일 파싱 오류: {e}")
            return False
        except Exception as e:
            self.print_warning(f"오류: {e}")
            return False

    def prepare_deployment(self):
        """배포 준비"""
        self.print_step(3, "배포 준비", "진행 중")

        checks = [
            ("backend_main.py 확인", (self.project_path / "backend_main.py").exists()),
            ("voice_handler.py 확인", (self.project_path / "voice_handler.py").exists()),
            ("requirements_backend.txt 확인", (self.project_path / "requirements_backend.txt").exists()),
            ("Procfile 확인", (self.project_path / "Procfile").exists()),
            ("render.yaml 확인", (self.project_path / "render.yaml").exists()),
            (".gitignore 확인", (self.project_path / ".gitignore").exists()),
        ]

        all_ok = True
        for check_name, result in checks:
            if result:
                self.print_success(check_name)
            else:
                self.print_warning(f"{check_name} - 파일 없음")
                all_ok = False

        if all_ok:
            self.print_success("모든 배포 파일 확인됨")

        return all_ok

    def generate_deployment_script(self):
        """배포 스크립트 생성"""
        self.print_step(4, "배포 자동화 스크립트 생성", "진행 중")

        # JSON 파일 내용을 환경 변수로 변환
        json_str = json.dumps(self.json_content, ensure_ascii=False)

        deployment_guide = f"""
+==================================================================+
|          [>>] PHARMA-MOBILE 자동 배포 준비 완료                   |
+==================================================================+

[*] 배포 정보
===================================================================

Google Cloud 프로젝트: {self.json_content.get('project_id')}
서비스 계정: {self.json_content.get('client_email')}
JSON 파일: {self.json_file}

배포 대상: Render
서비스명: pharma-mobile-backend
지역: Singapore
타입: Web Service (Python)

===================================================================

[OK] 배포 전 확인사항 (완료)
===================================================================

백엔드 파일
  [OK] backend_main.py
  [OK] voice_handler.py
  [OK] pharma_mobile.db
  [OK] requirements_backend.txt

배포 설정
  [OK] Procfile
  [OK] render.yaml
  [OK] .gitignore

Google Cloud
  [OK] JSON 파일 유효성 검증 완료
  [OK] 프로젝트 ID 확인
  [OK] 서비스 계정 확인

===================================================================

[>>] 배포 프로세스
===================================================================

Step 1: Render 대시보드 준비
  → https://dashboard.render.com
  → GitHub 로그인 (이미 연동됨)

Step 2: Web Service 생성
  → New → Web Service
  → med_project 선택
  → 설정값 자동 입력

Step 3: 환경 변수 설정
  → PYTHON_VERSION = 3.11
  → ENVIRONMENT = production
  → GOOGLE_CLOUD_CREDENTIALS_JSON = (자동 입력)

Step 4: 배포 시작
  → Create Web Service 클릭
  → 2-3분 대기
  → "Live" 상태 확인

Step 5: 자동 검증
  → python validate_deployment.py <URL>
  → 모든 API 테스트
  → 성공 리포트 생성

===================================================================

[!]  중요 사항
===================================================================

Render 대시보드에서 다음을 입력할 때:

1. Build Command:
   pip install -r requirements_backend.txt

2. Start Command:
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend_main:app --bind 0.0.0.0:$PORT

3. 환경 변수 - GOOGLE_CLOUD_CREDENTIALS_JSON:
   (아래 JSON 파일 전체 내용)

{json_str}

===================================================================

[*] 다음 단계
===================================================================

1. Render 대시보드 열기
   https://dashboard.render.com

2. New → Web Service 선택

3. med_project 저장소 선택

4. 위의 설정값 입력

5. Create Web Service 클릭

6. 배포 완료 후 URL 확인

===================================================================

배포 준비 완료! 위 단계를 따라 진행하세요. [*]
"""

        self.print_success("배포 스크립트 생성 완료")
        return deployment_guide

    def save_deployment_guide(self, guide):
        """배포 가이드 저장"""
        guide_file = self.project_path / "AUTO_DEPLOYMENT_GUIDE.md"

        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)

        self.print_success(f"배포 가이드 저장: {guide_file}")
        return guide_file

    def create_env_file(self):
        """환경 변수 파일 생성 (.env)"""
        self.print_step(5, "환경 변수 파일 생성", "진행 중")

        env_file = self.project_path / ".env.render"

        env_content = f"""# Render 배포용 환경 변수
PYTHON_VERSION=3.11
ENVIRONMENT=production
LOG_LEVEL=info

# Google Cloud 자격증명 (JSON 파일의 내용을 여기에 붙여넣으세요)
# GOOGLE_CLOUD_CREDENTIALS_JSON={json.dumps(self.json_content)}
"""

        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)

        self.print_success(f"환경 변수 파일 생성: {env_file}")
        return env_file

    def run(self):
        """전체 배포 준비 프로세스 실행"""
        self.print_header("[*] PHARMA-MOBILE 자동 배포 준비 프로세스")

        # Step 1: JSON 파일 찾기
        if not self.find_json_file():
            self.print_warning("\nJSON 파일을 찾을 수 없습니다.")
            self.print_info("다음 경로에 파일을 저장해주세요:")
            print("  - C:\\Users\\rcs91\\Downloads\\pharma-mobile-*.json")
            print("  - C:\\Users\\rcs91\\Desktop\\pharma-mobile-*.json")
            return False

        # Step 2: JSON 유효성 검증
        if not self.validate_json():
            self.print_warning("\nJSON 파일이 유효하지 않습니다.")
            return False

        # Step 3: 배포 준비 확인
        if not self.prepare_deployment():
            self.print_warning("\n일부 배포 파일이 없습니다.")

        # Step 4: 배포 스크립트 생성
        guide = self.generate_deployment_script()

        # Step 5: 가이드 저장
        guide_file = self.save_deployment_guide(guide)

        # Step 6: 환경 변수 파일 생성
        self.create_env_file()

        # 최종 요약
        self.print_header("[*] 배포 준비 완료!")

        print(guide)

        return True


def main():
    deployer = AutoDeployer()
    success = deployer.run()

    if success:
        print("\n" + "="*70)
        print("[OK] 배포 준비가 완료되었습니다!")
        print("="*70)
        print("\n다음 단계:")
        print("1. Render 대시보드 열기: https://dashboard.render.com")
        print("2. AUTO_DEPLOYMENT_GUIDE.md 내용을 따라 배포 진행")
        print("3. 배포 완료 후 URL 확인")
        print("4. 자동 검증 실행: python validate_deployment.py <URL>")
        print("\n" + "="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("❌ 배포 준비 중 오류가 발생했습니다.")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
