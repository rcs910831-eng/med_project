#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 약사 상담
Claude API + RAG를 활용한 약물 상담
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional

def get_pharmacist_answer(question: str, db_path: str = "pharma_mobile.db") -> Dict:
    """
    약사 상담 질문에 대한 AI 답변

    Args:
        question: 사용자 질문
        db_path: 약물 DB 경로

    Returns:
        {
            'success': bool,
            'answer': str,
            'source': str,
            'related_drugs': [str],
            'recommendation': str
        }
    """

    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            'success': False,
            'error': 'Anthropic SDK not installed',
            'message': 'Claude API가 설정되지 않았습니다'
        }

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            'success': False,
            'error': 'API key not set',
            'message': 'ANTHROPIC_API_KEY 환경변수를 설정해주세요',
            'fallback': get_local_pharmacist_answer(question, db_path)
        }

    try:
        # 관련 약물 정보 조회 (RAG)
        relevant_drugs = extract_drugs_from_question(question, db_path)
        drug_context = build_drug_context(relevant_drugs, db_path)

        # Claude API 호출
        client = Anthropic(api_key=api_key)

        system_prompt = """당신은 경험 많은 약사입니다. 사용자의 약물 관련 질문에 정확하고 친절하게 답변해주세요.

다음 규칙을 따르세요:
1. 의료 조언이 아닌 일반 정보 제공 ("의료 전문가의 상담을 권장합니다"라고 명시)
2. 정확한 약물 정보 제공
3. 부작용, 상호작용 경고
4. 복약 지도
5. 의료진 상담이 필요한 경우 명확히 표시

약물 정보 DB의 정보를 참고하되, 항상 "의사나 약사와 상담하세요"라고 안내하세요."""

        user_message = f"""사용자 질문: {question}

{drug_context if drug_context else ''}

위 정보를 바탕으로 약사로서 친절하고 정확하게 답변해주세요."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        answer = message.content[0].text

        return {
            'success': True,
            'answer': answer,
            'source': 'Claude AI Pharmacist',
            'related_drugs': relevant_drugs,
            'recommendation': '약사나 의사와 직접 상담하시는 것을 권장합니다.'
        }

    except Exception as e:
        # Fallback: 로컬 답변
        return {
            'success': True,
            'answer': get_local_pharmacist_answer(question, db_path),
            'source': 'Local Knowledge Base',
            'related_drugs': extract_drugs_from_question(question, db_path),
            'recommendation': '자세한 상담을 위해 약사나 의사를 찾아주세요.',
            'note': f'Claude API 오류: {str(e)}'
        }

def extract_drugs_from_question(question: str, db_path: str) -> List[str]:
    """
    질문에서 약물명 추출

    Args:
        question: 사용자 질문
        db_path: 약물 DB 경로

    Returns:
        약물명 리스트
    """

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, generic_name FROM medications')
        drugs = cursor.fetchall()
        conn.close()

        found_drugs = []
        for drug_name, generic_name in drugs:
            if drug_name.lower() in question.lower() or \
               generic_name.lower() in question.lower():
                found_drugs.append(drug_name)

        return found_drugs[:3]  # 상위 3개만

    except Exception as e:
        print(f"[WARN] 약물 추출 실패: {e}")
        return []

def build_drug_context(drug_names: List[str], db_path: str) -> str:
    """
    약물 정보 컨텍스트 구성

    Args:
        drug_names: 약물명 리스트
        db_path: 약물 DB 경로

    Returns:
        컨텍스트 문자열
    """

    if not drug_names:
        return ""

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        context_parts = []
        for drug_name in drug_names:
            cursor.execute('''
            SELECT name, generic_name, indication, side_effects, special_warnings
            FROM medications WHERE LOWER(name) = LOWER(?)
            ''', (drug_name,))

            row = cursor.fetchone()
            if row:
                side_effects = json.loads(row[3]) if row[3] else []
                context_parts.append(f"""
관련 약물 정보:
- 약물명: {row[0]}
- 영문명: {row[1]}
- 효능: {row[2]}
- 부작용: {', '.join(side_effects[:3])}
- 주의사항: {row[4]}
""")

        conn.close()
        return "\n".join(context_parts) if context_parts else ""

    except Exception as e:
        print(f"[WARN] 컨텍스트 구성 실패: {e}")
        return ""

def get_local_pharmacist_answer(question: str, db_path: str) -> str:
    """
    로컬 약물 DB 기반 답변

    Args:
        question: 사용자 질문
        db_path: 약물 DB 경로

    Returns:
        답변 문자열
    """

    # 자주 있는 질문 처리
    q_lower = question.lower()

    if '부작용' in q_lower or 'side effect' in q_lower:
        return """약물의 부작용은 개인에 따라 다르게 나타날 수 있습니다.

일반적인 부작용:
- 경미한 부작용: 가려움, 두통, 소화불편
- 심각한 부작용: 호흡곤란, 심각한 알레르기 반응

부작용이 발생하면:
1. 즉시 약물 복용을 중지하세요
2. 의료진에 알리세요
3. 응급 상황이면 119에 신고하세요

약사나 의사와 상담하시기 바랍니다."""

    elif '복용' in q_lower or '어떻게' in q_lower:
        return """약물 복용 지침:

1. 약사의 지시를 따르세요
2. 정해진 시간에 정해진 용량을 복용하세요
3. 음식과의 상호작용 확인하세요
4. 다른 약물과의 상호작용 확인하세요
5. 복용을 놓쳤다면 즉시 의료진에 문의하세요

의약사와 반드시 상담하세요."""

    elif '상호작용' in q_lower or 'interaction' in q_lower:
        return """약물 상호작용은 위험할 수 있습니다.

주의사항:
- 여러 약물을 복용 중이면 반드시 알리세요
- 영양제, 한약도 포함합니다
- 음식과의 상호작용도 확인하세요

상호작용이 의심되면:
1. 약사에 문의하세요
2. 약물 복용 순서 조정이 필요할 수 있습니다
3. 약물 변경이 필요할 수 있습니다

반드시 의료진과 상담하세요."""

    elif '보관' in q_lower or 'storage' in q_lower:
        return """약물 보관 방법:

기본 원칙:
- 실온 (15-25°C)에 보관
- 직사광선을 피하세요
- 습도가 낮은 곳에 보관
- 어린이와 애완동물의 손이 닿지 않게 하세요

일부 약물:
- 냉장 보관 (2-8°C): 인슐린 등
- 실온 보관: 대부분의 약물

유효기간이 지난 약물은 폐기하세요.
약사에게 폐기 방법을 문의하세요."""

    else:
        return f""""{question}"에 대해 충분한 정보를 제공하기 어렵습니다.

권장사항:
1. 약국을 방문하여 약사와 상담하세요
2. 병원에서 의사와 상담하세요
3. 의료 상담 전화: 1339

정확하고 안전한 조언을 위해 의료전문가의 상담을 권장합니다."""

if __name__ == "__main__":
    print("[INFO] AI Pharmacist Module")
