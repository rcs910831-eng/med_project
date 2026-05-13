#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_ai_engine.py — google-genai SDK v1.x 기반
  - 텍스트 분석  : gemini-2.5-flash
  - 이미지 분석  : gemini-2.5-flash (Vision)
  - RAG 보강     : 지식베이스 + Gemini 설명 생성
  - 복약 독려    : 맞춤 격려 메시지

API KEY 우선순위:
  1) st.secrets["GOOGLE_API_KEY"]  (Streamlit Cloud 배포)
  2) 환경변수 GOOGLE_API_KEY        (로컬 .env)
  3) 없으면 → 시뮬레이션 모드 (오프라인 폴백)
"""

import os
import base64
import logging
from typing import List, Dict, Optional

# ── .env 자동 로드 ────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)
except ImportError:
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env_path):
        for _line in open(_env_path, encoding="utf-8"):
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if _k.strip() and not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

# ── google-genai SDK (신버전) ─────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None
    genai_types = None

logger = logging.getLogger("gemini_ai_engine")

# ── 전역 클라이언트 ───────────────────────────────────────────────────────────
_client: Optional[object] = None
_genai_ready: bool = False


def _load_api_key() -> str:
    try:
        import streamlit as st
        key = st.secrets.get("GOOGLE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY", "")


def _ensure_client() -> bool:
    global _client, _genai_ready
    if _genai_ready:
        return True
    key = _load_api_key()
    if not key or not HAS_GENAI:
        logger.warning("⚠️ GOOGLE_API_KEY 없음 또는 google-genai 미설치 → 시뮬레이션 모드")
        return False
    try:
        _client = genai.Client(api_key=key)
        _genai_ready = True
        logger.info("✅ Gemini API 클라이언트 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"❌ Gemini 초기화 실패: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 텍스트 분석
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_text(
    prompt: str,
    system_instruction: str = "",
    model_name: str = "gemini-2.5-flash",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    if not _ensure_client():
        return _simulate_text_response(prompt, system_instruction)
    try:
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction else None,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = _client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Gemini 텍스트 API 오류: {e}")
        return _simulate_text_response(prompt, system_instruction)


# ═══════════════════════════════════════════════════════════════════════════════
# Vision AI — 이미지 분석
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_vision(
    image_data,
    mime_type: str,
    prompt: str,
    system_instruction: str = "",
    model_name: str = "gemini-2.5-flash",
) -> str:
    """
    image_data: bytes (바이너리) 또는 str (base64 인코딩)
    """
    if not _ensure_client():
        return _simulate_vision_response(prompt)
    try:
        # base64 문자열이면 bytes로 변환
        if isinstance(image_data, str):
            img_bytes = base64.b64decode(image_data)
        else:
            img_bytes = image_data

        image_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction else None,
            max_output_tokens=2048,
            temperature=0.2,
        )
        response = _client.models.generate_content(
            model=model_name,
            contents=[image_part, prompt],
            config=config,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Gemini Vision API 오류: {e}")
        return _simulate_vision_response(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# RAG 보강 설명
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_rag(
    query: str,
    kb_results: List[Dict],
    patient_context: str = "",
) -> str:
    kb_text = ""
    for r in kb_results:
        kb_text += f"\n[{r.get('type','')} - {r.get('title','')}]\n"
        for k, v in r.get("data", {}).items():
            kb_text += f"  {k}: {str(v)[:300]}\n"

    system = (
        "당신은 PHARMA-HYBRID 임상 지식 AI입니다. "
        "제공된 임상 데이터베이스 정보를 바탕으로 쉽고 명확하게 설명합니다. "
        "의학 전문 용어는 괄호 안에 한글 설명을 추가하세요. "
        "중요한 주의사항은 ⚠️ 기호로 강조하세요. "
        "한국어로 600자 이내로 작성하세요."
    )
    user_prompt = (
        f"검색어: {query}\n"
        f"{('환자 정보: ' + patient_context) if patient_context else ''}\n\n"
        f"데이터베이스 정보:\n{kb_text}\n\n"
        "위 정보를 바탕으로 임상적으로 중요한 내용을 이해하기 쉽게 설명해주세요."
    )
    return call_gemini_text(user_prompt, system_instruction=system)


# ═══════════════════════════════════════════════════════════════════════════════
# 음성 질문 분석
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_voice(
    voice_text: str,
    patient_info: Dict,
    prescriptions: List[Dict],
) -> str:
    rx_summary = "\n".join([
        f"- {r.get('medication_name','')} ({r.get('cancer_type','')}) "
        f"{r.get('dosage','')} {r.get('frequency','')} "
        f"효능:{r.get('efficacy_rate','-')}% 부작용:{r.get('side_effects','-')}"
        for r in prescriptions
    ])
    system = (
        "당신은 PHARMA-HYBRID 임상 AI 어시스턴트입니다. "
        "항암제·처방약에 대한 전문적인 임상 정보를 한국어로 명확하게 답변합니다. "
        "의학적 조언은 반드시 담당의와 상담을 권장합니다. "
        "답변은 600자 이내로 핵심만 간결하게 작성하세요. "
        "주의사항은 ⚠️로, 중요 정보는 ✅로 표시하세요."
    )
    prompt = (
        f"현재 환자 정보:\n"
        f"- 나이: {patient_info.get('age', 'N/A')}세\n"
        f"- 병원: {patient_info.get('hospital', 'N/A')}\n"
        f"- 처방 내역:\n{rx_summary}\n\n"
        f"음성 질문: {voice_text}\n\n"
        "위 환자 정보를 참고하여 질문에 임상적으로 답변해주세요."
    )
    return call_gemini_text(prompt, system_instruction=system, temperature=0.4)


# ═══════════════════════════════════════════════════════════════════════════════
# 복약 이행도 AI 격려 메시지
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_adherence_advice(
    patient_name: str,
    compliance_rate: float,
    missed_drugs: List[str],
    disease: str,
) -> str:
    level = (
        "매우 위험" if compliance_rate < 50
        else "주의 필요" if compliance_rate < 75
        else "양호" if compliance_rate < 90
        else "우수"
    )
    system = (
        "당신은 환자 복약 상담 AI입니다. "
        "복약 이행도 데이터를 분석하여 환자가 이해하기 쉬운 따뜻한 말투로 복약을 독려하세요. "
        "전문적이면서도 어르신도 이해할 수 있는 쉬운 말을 사용하세요. "
        "200자 이내로 간결하게 작성하세요."
    )
    prompt = (
        f"환자: {patient_name}님\n"
        f"질환: {disease}\n"
        f"복약 이행도: {compliance_rate:.1f}% (수준: {level})\n"
        f"최근 복용 누락 약물: {', '.join(missed_drugs) if missed_drugs else '없음'}\n\n"
        "이 환자에게 복약을 독려하는 따뜻한 안내 메시지를 작성해주세요."
    )
    return call_gemini_text(prompt, system_instruction=system, temperature=0.7)


# ═══════════════════════════════════════════════════════════════════════════════
# 기존 코드 호환 래퍼
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_compat(contents: list, system: str = "") -> str:
    text_parts = []
    image_part = None
    for part in contents[0].get("parts", []):
        if "text" in part:
            text_parts.append(part["text"])
        elif "inlineData" in part:
            image_part = part["inlineData"]

    prompt_text = "\n".join(text_parts)
    if image_part:
        img_bytes = base64.b64decode(image_part["data"])
        mime = image_part.get("mimeType", "image/jpeg")
        return call_gemini_vision(img_bytes, mime, prompt_text, system_instruction=system)
    return call_gemini_text(prompt_text, system_instruction=system)


# ═══════════════════════════════════════════════════════════════════════════════
# 시뮬레이션 폴백
# ═══════════════════════════════════════════════════════════════════════════════

def _simulate_text_response(prompt: str, system: str = "") -> str:
    import time
    time.sleep(0.3)
    if "복약" in system or "adherence" in system.lower():
        return "💊 복약을 꾸준히 유지해 주세요. 정해진 시간에 약을 드시면 치료 효과가 높아집니다. [오프라인 모드]"
    if "임상 지식" in system or "RAG" in prompt[:30]:
        return (
            "📚 임상 데이터베이스 분석 결과: 해당 항목은 표준 치료법에 해당합니다. "
            "장기 복용 시 정기적인 혈액 검사를 권장합니다.\n"
            "⚠️ GOOGLE_API_KEY 설정 시 실제 Gemini AI 분석이 활성화됩니다."
        )
    return (
        "현재 오프라인 모드로 동작 중입니다. "
        "증상에 맞는 기본 케어를 권장 드립니다.\n"
        "⚠️ GOOGLE_API_KEY 설정 시 AI 실시간 분석이 활성화됩니다."
    )


def _simulate_vision_response(prompt: str) -> str:
    import re
    m = re.search(r"처방:?\s*([^\n]+)", prompt)
    rx_list = m.group(1) if m else "약물 목록"
    return (
        f"[Vision 오프라인 모드] 이미지 분석 불가. "
        f"처방전에서 약물을 직접 입력해 주세요: {rx_list}\n"
        "⚠️ GOOGLE_API_KEY 설정 시 처방전 자동 OCR이 활성화됩니다."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 상태 확인
# ═══════════════════════════════════════════════════════════════════════════════

def get_engine_status() -> Dict:
    ready = _ensure_client()
    return {
        "sdk_installed": HAS_GENAI,
        "api_key_set": bool(_load_api_key()),
        "ready": ready,
        "mode": "🟢 Gemini API 실제 연동" if ready else "🟡 오프라인 시뮬레이션 모드",
        "model_text": "gemini-2.5-flash",
        "model_vision": "gemini-2.5-flash",
    }
