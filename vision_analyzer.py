#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Vision API를 사용한 처방전 이미지 분석
약물명, 용량, 횟수 등을 자동으로 추출
"""

import base64
import json
import os
from typing import Dict, List, Optional

def encode_image_to_base64(image_bytes: bytes) -> str:
    """이미지 바이트를 Base64로 인코딩"""
    return base64.standard_b64encode(image_bytes).decode("utf-8")

def analyze_prescription_image(image_bytes: bytes) -> Dict:
    """
    Claude Vision API를 사용하여 처방전 이미지 분석

    Args:
        image_bytes: 이미지 파일의 바이트 데이터

    Returns:
        {
            'success': bool,
            'patient_name': str,
            'patient_age': int or None,
            'medications': [
                {'name': str, 'dosage': str, 'frequency': str},
                ...
            ],
            'diseases': [str],
            'doctor_info': str,
            'prescription_date': str,
            'confidence': float (0-1),
            'extracted_text': str,
            'warnings': [str]
        }
    """

    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            'success': False,
            'error': 'Anthropic SDK not installed. Run: pip install anthropic',
            'message': '처방전 분석을 위해 Anthropic SDK 설치 필요'
        }

    # API 키 확인
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            'success': False,
            'error': 'ANTHROPIC_API_KEY not set',
            'message': '환경변수 ANTHROPIC_API_KEY를 설정해주세요',
            'example': 'export ANTHROPIC_API_KEY="sk-ant-..."'
        }

    try:
        # 이미지 인코딩
        image_base64 = encode_image_to_base64(image_bytes)

        # Claude Vision API 호출
        client = Anthropic(api_key=api_key)

        analysis_prompt = """
        이 이미지는 의료 처방전입니다. 다음 정보를 한국어 JSON 형식으로 추출해주세요.

        필수 추출 정보:
        1. 환자명 (patient_name)
        2. 환자 나이 (patient_age) - 없으면 null
        3. 환자 성별 (patient_gender) - M/F/Unknown
        4. 진료 질병명 (primary_disease)
        5. 부진료 질병명 (secondary_disease) - 없으면 null
        6. 약물 정보 배열 (medications):
           - name: 약물명 (한글)
           - dosage: 용량 (예: "5mg")
           - frequency: 투여 횟수 (예: "1일 1회")
           - quantity: 수량 (예: "30정")
        7. 처방 날짜 (prescription_date) - YYYY-MM-DD 형식
        8. 의사 정보 (doctor_info) - 의사명, 병원명 등
        9. 신뢰도 (confidence) - 0.0~1.0 (1.0 = 확실함)
        10. 경고 사항 (warnings) - 추출 중 문제가 있으면 기록

        JSON 예시:
        {
            "patient_name": "김철수",
            "patient_age": 65,
            "patient_gender": "M",
            "primary_disease": "고혈압",
            "secondary_disease": "당뇨병",
            "medications": [
                {"name": "노바스크정", "dosage": "5mg", "frequency": "1일 1회", "quantity": "30정"},
                {"name": "글루코판정", "dosage": "500mg", "frequency": "1일 2회", "quantity": "60정"}
            ],
            "prescription_date": "2026-05-09",
            "doctor_info": "김의사 (서울대학교병원 내과)",
            "confidence": 0.95,
            "warnings": []
        }

        반드시 유효한 JSON만 반환하세요. 설명 텍스트는 제외하세요.
        """

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ],
                }
            ],
        )

        # 응답 파싱
        response_text = message.content[0].text

        # JSON 추출 (```json ... ``` 감싸기 처리)
        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_str = response_text.split('```')[1].split('```')[0].strip()
        else:
            json_str = response_text.strip()

        prescription_data = json.loads(json_str)

        return {
            'success': True,
            'patient_name': prescription_data.get('patient_name'),
            'patient_age': prescription_data.get('patient_age'),
            'patient_gender': prescription_data.get('patient_gender', 'Unknown'),
            'primary_disease': prescription_data.get('primary_disease'),
            'secondary_disease': prescription_data.get('secondary_disease'),
            'medications': prescription_data.get('medications', []),
            'prescription_date': prescription_data.get('prescription_date'),
            'doctor_info': prescription_data.get('doctor_info'),
            'confidence': prescription_data.get('confidence', 0.0),
            'warnings': prescription_data.get('warnings', []),
            'extracted_text': response_text
        }

    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON parsing error: {str(e)}',
            'message': 'Claude의 응답을 파싱할 수 없습니다',
            'raw_response': response_text if 'response_text' in locals() else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'처방전 분석 중 오류 발생: {str(e)}'
        }

if __name__ == "__main__":
    print("[INFO] Vision Analyzer Module")
    print("Usage: from vision_analyzer import analyze_prescription_image")
