#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Places API를 사용한 약국 검색
실제 주변 약국의 위치, 영업시간, 별점 조회
API 키: .env 파일의 GOOGLE_API_KEY
"""

import requests
import json
import os
import math
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class GooglePlacesClient:
    """Google Places API 클라이언트"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: Optional[str] = None):
        """
        Google Places API 클라이언트 초기화

        Args:
            api_key: API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')

        if not self.api_key:
            print("[WARN] Google Places API 키 없음")
            self.api_key = None

    def nearby_search(
        self,
        latitude: float,
        longitude: float,
        keyword: str = "약국",
        radius: int = 2000,
        max_results: int = 5
    ) -> Dict:
        """
        위치 기반 주변 약국 검색

        Args:
            latitude: 위도
            longitude: 경도
            keyword: 검색 키워드 (기본값: "약국")
            radius: 검색 반경 (미터)
            max_results: 반환 결과 개수

        Returns:
            {
                'success': bool,
                'pharmacies': [
                    {
                        'name': str,
                        'latitude': float,
                        'longitude': float,
                        'distance_m': float,
                        'phone': str,
                        'address': str,
                        'rating': float,
                        'hours': str,
                        'place_id': str,
                        'url': str
                    }
                ],
                'message': str,
                'total_count': int
            }
        """

        if not self.api_key:
            return {
                'success': False,
                'pharmacies': [],
                'message': 'Google Places API 키가 설정되지 않았습니다',
                'recommendation': '로컬 약국 샘플 데이터 사용'
            }

        try:
            # Nearby Search API
            url = f"{self.BASE_URL}/nearbysearch/json"

            params = {
                'location': f"{latitude},{longitude}",
                'radius': radius,
                'keyword': keyword,
                'language': 'ko',
                'key': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data['status'] == 'OK':
                    pharmacies = []

                    for i, place in enumerate(data.get('results', [])[:max_results]):
                        # 약국 정보 추출
                        place_location = place['geometry']['location']
                        distance = self._calculate_distance(
                            latitude, longitude,
                            place_location['lat'], place_location['lng']
                        )

                        pharmacy = {
                            'name': place.get('name', ''),
                            'latitude': place_location['lat'],
                            'longitude': place_location['lng'],
                            'distance_m': int(distance * 1000),
                            'phone': place.get('formatted_phone_number', '미등록'),
                            'address': place.get('vicinity', '주소 미표시'),
                            'rating': place.get('rating', 0),
                            'place_id': place.get('place_id', ''),
                            'url': place.get('url', ''),
                            'is_open': place.get('opening_hours', {}).get('open_now', None),
                            'hours': self._get_hours(place.get('opening_hours', {}))
                        }

                        # 세부 정보 조회 (선택적)
                        if pharmacy['place_id']:
                            details = self._get_place_details(pharmacy['place_id'])
                            pharmacy.update(details)

                        pharmacies.append(pharmacy)

                    return {
                        'success': True,
                        'pharmacies': pharmacies,
                        'message': f'{len(pharmacies)}개 약국 검색됨 (Google Places)',
                        'total_count': len(pharmacies),
                        'search_location': {'latitude': latitude, 'longitude': longitude},
                        'search_radius_m': radius
                    }

                elif data['status'] == 'ZERO_RESULTS':
                    return {
                        'success': False,
                        'pharmacies': [],
                        'message': '검색 범위 내에 약국이 없습니다',
                        'suggestion': '검색 범위를 확대해주세요'
                    }
                else:
                    return {
                        'success': False,
                        'pharmacies': [],
                        'message': f'Google Places API 오류: {data["status"]}',
                        'error_message': data.get('error_message', '')
                    }
            else:
                return {
                    'success': False,
                    'pharmacies': [],
                    'message': f'HTTP 오류: {response.status_code}',
                    'error': response.text
                }

        except requests.Timeout:
            return {
                'success': False,
                'pharmacies': [],
                'message': 'Google Places API 연결 시간 초과'
            }
        except Exception as e:
            return {
                'success': False,
                'pharmacies': [],
                'message': f'Google Places API 오류: {str(e)}'
            }

    def _get_place_details(self, place_id: str) -> Dict:
        """
        장소의 세부 정보 조회

        Args:
            place_id: Google Place ID

        Returns:
            추가 정보 딕셔너리
        """

        if not self.api_key:
            return {}

        try:
            url = f"{self.BASE_URL}/details/json"

            params = {
                'place_id': place_id,
                'fields': 'formatted_phone_number,opening_hours,website,photos',
                'language': 'ko',
                'key': self.api_key
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data['status'] == 'OK':
                    result = data.get('result', {})
                    return {
                        'phone': result.get('formatted_phone_number', '미등록'),
                        'website': result.get('website', ''),
                        'detailed_hours': self._get_detailed_hours(
                            result.get('opening_hours', {})
                        )
                    }

            return {}

        except Exception as e:
            print(f"[WARN] 세부 정보 조회 실패: {e}")
            return {}

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine 공식으로 거리 계산 (km)"""
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def _get_hours(self, opening_hours: dict) -> str:
        """영업시간 문자열 생성"""

        if not opening_hours:
            return '영업시간 미표시'

        weekday_text = opening_hours.get('weekday_text', [])
        if weekday_text:
            return weekday_text[0]  # 오늘의 영업시간

        return '영업시간 미표시'

    def _get_detailed_hours(self, opening_hours: dict) -> Dict:
        """주간 영업시간 상세 정보"""

        if not opening_hours:
            return {}

        weekday_text = opening_hours.get('weekday_text', [])
        days = ['일', '월', '화', '수', '목', '금', '토']

        detailed = {}
        for i, hours in enumerate(weekday_text):
            day = days[i % 7]
            detailed[day] = hours

        return detailed

# 샘플 약국 데이터 (API 실패 시 사용)
SAMPLE_PHARMACIES = [
    {
        'name': '강남중앙약국',
        'latitude': 37.4979,
        'longitude': 127.0276,
        'distance_m': 250,
        'phone': '02-511-1234',
        'address': '서울시 강남구 강남대로 123',
        'rating': 4.8,
        'hours': '월~금 09:00-22:00, 토 09:00-21:00, 일 11:00-20:00',
        'is_open': True
    },
    {
        'name': '강남약국',
        'latitude': 37.4985,
        'longitude': 127.0290,
        'distance_m': 450,
        'phone': '02-512-5678',
        'address': '서울시 강남구 강남대로 456',
        'rating': 4.6,
        'hours': '매일 09:00-22:00',
        'is_open': True
    },
    {
        'name': '역삼약국',
        'latitude': 37.4938,
        'longitude': 127.0368,
        'distance_m': 850,
        'phone': '02-513-9999',
        'address': '서울시 강남구 역삼로 789',
        'rating': 4.5,
        'hours': '월~금 09:00-21:00, 토 09:00-20:00, 일 휴무',
        'is_open': False
    }
]

def get_pharmacies_with_fallback(
    api_key: Optional[str],
    latitude: float,
    longitude: float,
    radius_km: int = 2
) -> Dict:
    """
    Google Places API를 시도하고, 실패 시 로컬 샘플 사용

    Args:
        api_key: Google API 키
        latitude: 위도
        longitude: 경도
        radius_km: 검색 반경 (km)

    Returns:
        약국 정보
    """

    if api_key:
        client = GooglePlacesClient(api_key)
        result = client.nearby_search(latitude, longitude, radius=radius_km * 1000)

        if result['success']:
            return {
                'success': True,
                'source': 'Google Places API',
                'pharmacies': result['pharmacies'],
                'total_count': result['total_count']
            }

    # Fallback: 샘플 데이터 (거리 재계산)
    def calc_dist(lat1, lon1, lat2, lon2):
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    filtered_pharmacies = []
    for pharmacy in SAMPLE_PHARMACIES:
        distance = calc_dist(latitude, longitude, pharmacy['latitude'], pharmacy['longitude'])
        if distance <= radius_km:
            pharmacy_copy = pharmacy.copy()
            pharmacy_copy['distance_km'] = round(distance, 2)
            filtered_pharmacies.append(pharmacy_copy)

    filtered_pharmacies.sort(key=lambda x: x['distance_m'])

    return {
        'success': True,
        'source': 'Sample Data (Google Places API 미설정)',
        'pharmacies': filtered_pharmacies,
        'total_count': len(filtered_pharmacies),
        'warning': 'Google Places API를 설정하면 실제 약국 데이터를 조회할 수 있습니다'
    }

if __name__ == "__main__":
    print("[INFO] Google Places API Module")
    print("Usage: from google_places_api import GooglePlacesClient, get_pharmacies_with_fallback")

    api_key = os.getenv('GOOGLE_API_KEY')
    print(f"API Key configured: {bool(api_key)}")
