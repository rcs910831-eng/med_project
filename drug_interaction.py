#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
약물 상호작용 분석
여러 약물을 함께 복용할 때의 위험도 분석
"""

import sqlite3
import json
from typing import Dict, List, Optional

class DrugInteractionAnalyzer:
    """약물 상호작용 분석기"""

    SEVERITY_LEVELS = {
        'none': {'level': 0, 'emoji': '✅', 'text': '안전'},
        'mild': {'level': 1, 'emoji': '⚠️', 'text': '경미함'},
        'moderate': {'level': 2, 'emoji': '🔴', 'text': '주의'},
        'severe': {'level': 3, 'emoji': '🚫', 'text': '금지'}
    }

    def __init__(self, db_path: str = "pharma_mobile.db"):
        """약물 상호작용 분석기 초기화"""
        self.db_path = db_path
        self.interaction_cache = {}

    def analyze_interactions(self, medication_names: List[str]) -> Dict:
        """
        여러 약물 간의 상호작용 분석

        Args:
            medication_names: 약물명 리스트

        Returns:
            {
                'success': bool,
                'medications': [
                    {'name': str, 'found': bool}
                ],
                'interactions': [
                    {
                        'drugs': [str, str],
                        'severity': 'none' | 'mild' | 'moderate' | 'severe',
                        'description': str,
                        'recommendation': str
                    }
                ],
                'summary': str,
                'overall_safety': 'safe' | 'caution' | 'warning' | 'danger'
            }
        """

        try:
            # DB에서 약물 정보 로드
            medications_info = []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for med_name in medication_names:
                cursor.execute(
                    'SELECT name, drug_interactions FROM medications WHERE LOWER(name) = LOWER(?)',
                    (med_name,)
                )
                row = cursor.fetchone()
                if row:
                    interactions = json.loads(row[1]) if row[1] else []
                    medications_info.append({
                        'name': row[0],
                        'found': True,
                        'interactions': interactions
                    })
                else:
                    medications_info.append({
                        'name': med_name,
                        'found': False,
                        'interactions': []
                    })

            conn.close()

            # 상호작용 분석
            interaction_results = []
            max_severity = 'none'

            for i, med1 in enumerate(medications_info):
                if not med1['found']:
                    continue

                for med2 in medications_info[i+1:]:
                    if not med2['found']:
                        continue

                    interaction = self._check_interaction(
                        med1['name'],
                        med2['name'],
                        med1['interactions'],
                        med2['interactions']
                    )

                    if interaction:
                        interaction_results.append(interaction)

                        # 최고 심각도 업데이트
                        if self.SEVERITY_LEVELS[interaction['severity']]['level'] > \
                           self.SEVERITY_LEVELS[max_severity]['level']:
                            max_severity = interaction['severity']

            # 안전 등급 결정
            if max_severity == 'none':
                overall_safety = 'safe'
                summary = f"✅ 모든 약물의 상호작용이 없습니다 ({len(medication_names)}가지 약물 확인)"
            elif max_severity == 'mild':
                overall_safety = 'caution'
                summary = f"⚠️ 경미한 상호작용이 발견되었습니다. 의사와 상담하세요."
            elif max_severity == 'moderate':
                overall_safety = 'warning'
                summary = f"🔴 주의가 필요한 상호작용이 있습니다. 의료진 상담 필수!"
            else:
                overall_safety = 'danger'
                summary = f"🚫 위험한 상호작용입니다. 즉시 의료진에 문의하세요!"

            return {
                'success': True,
                'medications': [
                    {'name': m['name'], 'found': m['found']}
                    for m in medications_info
                ],
                'interactions': interaction_results,
                'summary': summary,
                'overall_safety': overall_safety,
                'total_medications': len(medication_names),
                'found_count': sum(1 for m in medications_info if m['found'])
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '상호작용 분석 중 오류 발생'
            }

    def _check_interaction(self, drug1: str, drug2: str, interactions1: List, interactions2: List) -> Optional[Dict]:
        """
        두 약물 간의 상호작용 확인

        Args:
            drug1: 약물 1
            drug2: 약물 2
            interactions1: 약물 1의 상호작용 목록
            interactions2: 약물 2의 상호작용 목록

        Returns:
            상호작용 정보 또는 None
        """

        # 상호작용 문자열에서 상대 약물명 검색
        for interaction_str in interactions1:
            if drug2.lower() in interaction_str.lower():
                return self._parse_interaction(drug1, drug2, interaction_str)

        for interaction_str in interactions2:
            if drug1.lower() in interaction_str.lower():
                return self._parse_interaction(drug1, drug2, interaction_str)

        # 기본 상호작용 없음
        return None

    def _parse_interaction(self, drug1: str, drug2: str, interaction_str: str) -> Dict:
        """
        상호작용 문자열 파싱

        예: "메트포민: 상호작용 없음"
        예: "설폰요소제: 저혈당 위험 증가"
        """

        # 심각도 판단
        severity = 'none'
        if '위험' in interaction_str or '증가' in interaction_str:
            if '심각' in interaction_str or '높음' in interaction_str:
                severity = 'severe'
            else:
                severity = 'moderate'
        elif '주의' in interaction_str:
            severity = 'mild'

        return {
            'drugs': [drug1, drug2],
            'severity': severity,
            'description': interaction_str,
            'recommendation': self._get_recommendation(severity),
            'emoji': self.SEVERITY_LEVELS[severity]['emoji']
        }

    def _get_recommendation(self, severity: str) -> str:
        """심각도에 따른 권고사항"""

        recommendations = {
            'none': '특별한 주의가 필요하지 않습니다. 안전하게 함께 복용하셔도 됩니다.',
            'mild': '의료진에게 알려두세요. 필요시 용량 조절이 가능합니다.',
            'moderate': '의사 또는 약사와 반드시 상담하세요. 복용 간격 조절이 필요할 수 있습니다.',
            'severe': '즉시 의료진에 문의하세요. 약물 변경이 필요할 수 있습니다.'
        }

        return recommendations.get(severity, '의료진 상담이 필요합니다.')

def get_drug_interactions(db_path: str, medication_names: List[str]) -> Dict:
    """
    약물 상호작용 분석 (간편 함수)

    Args:
        db_path: 약물 DB 경로
        medication_names: 약물명 리스트

    Returns:
        상호작용 분석 결과
    """

    analyzer = DrugInteractionAnalyzer(db_path)
    return analyzer.analyze_interactions(medication_names)

if __name__ == "__main__":
    print("[INFO] Drug Interaction Analyzer Module")
