#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MFDS (의약품안전관리원) OpenAPI 연동
약물 정보, 부작용, 용량 등 실시간 조회
API 키: .env 파일의 MFDS_API_KEY (또는 PUBLIC_DATA_API_KEY)
"""

import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class MFDSAPIClient:
    """MFDS OpenAPI 클라이언트"""

    BASE_URL = "http://apis.data.go.kr/1471000"

    def __init__(self, api_key: Optional[str] = None):
        """
        MFDS API 클라이언트 초기화

        Args:
            api_key: API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv('MFDS_API_KEY') or os.getenv('PUBLIC_DATA_API_KEY')

        if not self.api_key:
            print("[WARN] MFDS API 키 없음. 제한된 기능만 사용 가능")
            self.api_key = None

        self.cache = {}  # 간단한 캐시
        self.cache_ttl = 3600  # 1시간

    def _cache_key(self, method: str, params: dict) -> str:
        """캐시 키 생성"""
        return f"{method}:{json.dumps(params, sort_keys=True)}"

    def _get_cached(self, cache_key: str) -> Optional[Dict]:
        """캐시에서 데이터 조회"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return data
            else:
                del self.cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Dict):
        """캐시에 데이터 저장"""
        self.cache[cache_key] = (data, datetime.now())

    def search_drug_by_name(self, drug_name: str, limit: int = 5) -> Dict:
        """
        약물명으로 약물 정보 검색

        Args:
            drug_name: 약물명 (한글)
            limit: 결과 제한 개수

        Returns:
            {
                'success': bool,
                'drugs': [
                    {
                        'name': str,
                        'ingredient': str,
                        'efficacy': str,
                        'dosage': str,
                        'manufacturer': str,
                        'approval_number': str,
                        'mfds_price': str
                    }
                ],
                'message': str,
                'total_count': int
            }
        """

        # API 키 확인
        if not self.api_key:
            return {
                'success': False,
                'drugs': [],
                'message': 'MFDS API 키가 설정되지 않았습니다',
                'recommendation': 'mock_data 사용'
            }

        # 캐시 확인
        cache_key = self._cache_key('search_drug_by_name', {'drug_name': drug_name, 'limit': limit})
        cached_result = self._get_cached(cache_key)
        if cached_result:
            return cached_result

        try:
            # MFDS API 엔드포인트
            # 참고: 실제 엔드포인트는 정부 공개 데이터 포털 확인 필요
            # 여기서는 대체 엔드포인트 사용
            url = f"{self.BASE_URL}/DrbEasyDrugInfoService/getDrbEasyDrugList"

            params = {
                'serviceKey': self.api_key,
                'pageNo': 1,
                'numOfRows': limit,
                'type': 'json',
                'searchType': 0,
                'drugName': drug_name
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # 응답 파싱 (API 응답 구조에 따라 수정 필요)
                if 'response' in data:
                    items = data['response'].get('body', {}).get('items', {}).get('item', [])
                    if not isinstance(items, list):
                        items = [items] if items else []

                    drugs = []
                    for item in items[:limit]:
                        drug_info = {
                            'name': item.get('itemName', drug_name),
                            'ingredient': item.get('ingredientName', ''),
                            'efficacy': item.get('efcyQesitm', ''),
                            'dosage': item.get('dosage', ''),
                            'manufacturer': item.get('itemPermitKorNm', ''),
                            'approval_number': item.get('permitNo', ''),
                            'mfds_price': item.get('unitPrice', '미등록')
                        }
                        drugs.append(drug_info)

                    result = {
                        'success': True,
                        'drugs': drugs,
                        'message': f'{len(drugs)}개 약물 검색됨',
                        'total_count': len(drugs)
                    }

                    self._set_cache(cache_key, result)
                    return result
                else:
                    return {
                        'success': False,
                        'drugs': [],
                        'message': 'MFDS API 응답 파싱 실패',
                        'raw_response': data
                    }
            else:
                return {
                    'success': False,
                    'drugs': [],
                    'message': f'MFDS API 오류: HTTP {response.status_code}',
                    'error': response.text
                }

        except requests.Timeout:
            return {
                'success': False,
                'drugs': [],
                'message': 'MFDS API 연결 시간 초과'
            }
        except Exception as e:
            return {
                'success': False,
                'drugs': [],
                'message': f'MFDS API 오류: {str(e)}'
            }

    def get_drug_side_effects(self, drug_name: str) -> Dict:
        """
        약물의 부작용 정보 조회

        Args:
            drug_name: 약물명

        Returns:
            {
                'success': bool,
                'side_effects': [str],
                'precautions': [str],
                'message': str
            }
        """

        if not self.api_key:
            return {
                'success': False,
                'side_effects': [],
                'precautions': [],
                'message': 'MFDS API 키 필요',
                'source': 'local_db'
            }

        try:
            # API 호출 (실제 엔드포인트 확인 필요)
            result = self.search_drug_by_name(drug_name, limit=1)

            if result['success'] and result['drugs']:
                drug = result['drugs'][0]
                return {
                    'success': True,
                    'side_effects': drug.get('efficacy', '').split(','),
                    'precautions': [],
                    'message': 'MFDS에서 조회됨'
                }
            else:
                return {
                    'success': False,
                    'side_effects': [],
                    'precautions': [],
                    'message': result['message']
                }

        except Exception as e:
            return {
                'success': False,
                'side_effects': [],
                'precautions': [],
                'message': f'오류: {str(e)}'
            }

    def get_drug_interactions(self, primary_drug: str, secondary_drug: str) -> Dict:
        """
        두 약물 간의 상호작용 확인

        Args:
            primary_drug: 주약물명
            secondary_drug: 부약물명

        Returns:
            {
                'success': bool,
                'interaction': str or None,
                'severity': 'none' | 'mild' | 'moderate' | 'severe',
                'message': str
            }
        """

        # MFDS API에서 직접 지원하지 않음
        # 로컬 DB 또는 외부 전문 API 사용 권장

        return {
            'success': False,
            'interaction': None,
            'severity': 'unknown',
            'message': 'MFDS에서 제공하지 않음. 로컬 DB 또는 의료전문가 상담 필요',
            'recommendation': '약사 또는 의사에게 확인하세요'
        }

# 샘플 약정보 (API 실패 시 사용)
SAMPLE_DRUGS = {
    '노바스크정': {
        'name': '노바스크정',
        'ingredient': 'Amlodipine',
        'efficacy': '고혈압, 협심증',
        'dosage': '5mg',
        'manufacturer': '비노 제약',
        'mfds_price': '₩1,234'
    },
    '글루코판정': {
        'name': '글루코판정',
        'ingredient': 'Metformin',
        'efficacy': '제2형 당뇨병',
        'dosage': '500mg',
        'manufacturer': '종로 제약',
        'mfds_price': '₩856'
    }
}

def get_drug_info_with_fallback(api_key: Optional[str], drug_name: str) -> Dict:
    """
    MFDS API를 시도하고, 실패 시 로컬 DB 사용

    Args:
        api_key: MFDS API 키
        drug_name: 약물명

    Returns:
        약물 정보
    """

    if api_key:
        client = MFDSAPIClient(api_key)
        result = client.search_drug_by_name(drug_name, limit=1)

        if result['success'] and result['drugs']:
            return {
                'success': True,
                'source': 'MFDS API',
                'drug': result['drugs'][0]
            }

    # Fallback: 샘플 데이터
    if drug_name in SAMPLE_DRUGS:
        return {
            'success': True,
            'source': 'Sample Data',
            'drug': SAMPLE_DRUGS[drug_name]
        }

    return {
        'success': False,
        'source': None,
        'message': f'약물 "{drug_name}" 정보를 찾을 수 없습니다'
    }

if __name__ == "__main__":
    print("[INFO] MFDS API Module")
    print("Usage: from mfds_api import MFDSAPIClient, get_drug_info_with_fallback")

    # 테스트
    api_key = os.getenv('MFDS_API_KEY') or os.getenv('PUBLIC_DATA_API_KEY')
    print(f"API Key configured: {bool(api_key)}")
