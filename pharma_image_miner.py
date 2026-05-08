#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[SHIELD] PHARMA-IMAGE-MINER v1.0
처방전 이미지 폴더 자동 OCR 스캔 ➡️ 식약처 API 연동 고화질 알약 이미지 다운로더
"""

import os
import re
import requests
import traceback
import time
# 사령관님이 기존에 구축해 두신 실제 Gemini 엔진 모듈 연동
from gemini_ai_engine import call_gemini_vision

# ── [전술 설정] 환경 경로 및 API 설정 ──────────────────────────────────
RX_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"
PILL_DIR = r"C:\Users\rcs91\github\med_project\pill_images"

# 공공데이터포털 마이페이지에서 발급받은 '일반 인증키(Decoding)'를 입력하세요
PUBLIC_DATA_API_KEY = "3333b43c676617db26970c7a5ec6533ab613cc80b82309e175c3b3df764d4262"

# 안전 폴더 자동 생성
os.makedirs(PILL_DIR, exist_ok=True)

def extract_pill_names_via_gemini(image_path: str) -> list:
    """처방전 이미지 한 장을 Gemini Vision AI에 던져 알약 이름 리스트만 파싱"""
    print(f"🔬 [OCR] 처방전 분석 중: {os.path.basename(image_path)}")
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        mime_type = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        
        # 실제 Gemini 엔진에 처방전 텍스트 추출용 타격 프롬프트 전달
        prompt = (
            "이 처방전 이미지에서 의사나 약사가 처방한 알약 및 주사제의 '순수한 제품명(약품이름)'만 "
            "추출해줘. 용량이나 영문 표기는 빼고 오직 한글 제품명만 쉼표(,)로 구분해서 한 줄의 텍스트로 답해줘. "
            "예시: 타세바정, 베실리온정, 무코스타정"
        )
        
        # gemini_ai_engine 모듈의 API 인터페이스 호출
        raw_response = call_gemini_vision(image_bytes, mime_type, prompt)
        
        # 불필요한 마크다운 기호 제거 및 파싱
        clean_text = re.sub(r'[^\w\s,가-힣0-9]', '', raw_response)
        pill_names = [name.strip() for name in clean_text.split(",") if name.strip()]
        return list(set(pill_names)) # 중복 제거
    except Exception as e:
        print(f"❌ Gemini OCR 실패 ({os.path.basename(image_path)}): {e}")
        return []

def download_pill_image_from_kfda(pill_name: str):
    """식약처 낱알식별정보 OpenAPI를 타격하여 고화질 이미지 URL을 따낸 뒤 저장"""
    # 일부 처방용 가이드 텍스트 정제
    clean_name = pill_name.split("(")[0].strip()
    
    # 알약 이미지 중복 다운로드 차단
    save_path = os.path.join(PILL_DIR, f"{clean_name}.jpg")
    if os.path.exists(save_path):
        print(f"⏭️  이미 보유 중인 알약 데이터: {clean_name}")
        return

    # 공공데이터포털 식품의약품안전처 의약품 낱알식별정보 표준 엔드포인트
    url = "http://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService01/getMdcinGrnIdntfcInfoList01"
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "item_name": clean_name,
        "type": "json",
        "numOfRows": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            items = res_data.get("body", {}).get("items", [])
            
            if items and isinstance(items, list):
                # 식약처 알약 이미지 필드 'ITEM_IMAGE' 추출
                img_url = items[0].get("ITEM_IMAGE")
                if img_url:
                    print(f"📥 이미지 다운로드 시작 ➡️ {clean_name}")
                    img_res = requests.get(img_url, timeout=15)
                    if img_res.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_res.content)
                        print(f"✅ 격리 금고 저장 완료: {clean_name}.jpg")
                        return
            print(f"⚠️  식약처 DB 내 이미지 매핑 정보 없음: {clean_name}")
    except Exception as e:
        print(f"❌ 식약처 통신 트래픽 장애 또는 파싱 실패 ({clean_name}): {e}")

# ── [전술 실행 제어 컨트롤러] ──────────────────────────────────────────
def run_pipeline():
    if not os.path.exists(RX_DIR):
        print(f"❌ 에러: 지정된 처방전 폴더가 존재하지 않습니다: {RX_DIR}")
        return
        
    supported_extensions = (".jpg", ".jpeg", ".png")
    rx_files = [f for f in os.listdir(RX_DIR) if f.lower().endswith(supported_extensions)]
    
    print(f"📡 총 {len(rx_files)}개의 처방전 파일 발견. 마이닝 작업을 전개합니다.")
    
    for rx_file in rx_files:
        full_path = os.path.join(RX_DIR, rx_file)
        # 1. 처방전 분석해서 알약 이름 따내기
        detected_pills = extract_pill_names_via_gemini(full_path)
        print(f"🎯 검출된 알약 목록: {detected_pills}")
        
        # 2. 검출된 알약 순회하며 식약처에서 이미지 긁어오기
        for pill in detected_pills:
            download_pill_image_from_kfda(pill)
            # 트래픽 차단 예방용 안전 휴식기 배치 (무중력 비행 준수)
            time.sleep(1.0)
            
    print("\\n🏁 모든 처방전 데이터 분석 및 알약 이미지 아카이빙 시퀀스가 완료되었습니다!")

if __name__ == "__main__":
    run_pipeline()
