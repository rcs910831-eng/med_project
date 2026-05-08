#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_ai_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실제 Google Gemini API 연동 모듈
  - 텍스트 분석  : Gemini 1.5 Flash (빠름) / Pro (정확)
  - 이미지 분석  : Gemini 1.5 Pro Vision (처방전·약포지 OCR)
  - 음성 이후 RAG: 지식베이스 결과 + Gemini 보강 설명

설정 우선순위:
  1) st.secrets["GOOGLE_API_KEY"]  (Streamlit Cloud 배포)
  2) 환경변수 GOOGLE_API_KEY        (로컬 .env)
  3) 하드코딩 fallback (빈 문자열 → 시뮬레이션 모드)

Author: PHARMA-HYBRID Team
"""

import os
import base64
import logging
from typing import List, Dict, Optional

# ── .env 파일 자동 로드 (python-dotenv 있으면 사용, 없으면 직접 파싱) ──────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)
except ImportError:
    # dotenv 미설치 시 직접 파싱
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env_path):
        for _line in open(_env_path, encoding="utf-8"):
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if _k.strip() and not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

# ── Google Generative AI SDK 로드 ─────────────────────────────────────────────
try:
    import google.generativeai as genai          # pip install google-generativeai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None  # 타입 힌트용 빈 객체

logger = logging.getLogger("gemini_ai_engine")


# ═══════════════════════════════════════════════════════════════════════════════
# API KEY 로드
# ═══════════════════════════════════════════════════════════════════════════════

def _load_api_key() -> str:
    """
    Streamlit secrets → 환경변수 순으로 API 키 탐색.
    둘 다 없으면 빈 문자열 반환 → 자동으로 시뮬레이션 모드.
    """
    # 1순위: Streamlit secrets (배포 환경)
    try:
        import streamlit as st
        key = st.secrets.get("GOOGLE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # 2순위: 환경변수 (로컬 개발 / .env)
    return os.environ.get("GOOGLE_API_KEY", "")


# ── 전역 API 키 & SDK 초기화 ──────────────────────────────────────────────────
_API_KEY: str = ""
_genai_ready: bool = False


def _ensure_genai(api_key: str = "") -> bool:
    """
    SDK 초기화. 이미 초기화됐으면 True 즉시 반환.
    반환값: True = 실제 API 사용 가능, False = 시뮬레이션 모드
    """
    global _API_KEY, _genai_ready

    if _genai_ready:
        return True

    key = api_key or _load_api_key()
    if not key or not HAS_GENAI:
        logger.warning("⚠️ GOOGLE_API_KEY 없음 또는 google-generativeai 미설치 → 시뮬레이션 모드")
        return False

    try:
        genai.configure(api_key=key)
        _API_KEY = key
        _genai_ready = True
        logger.info("✅ Gemini API 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"❌ Gemini 초기화 실패: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 텍스트 분석 (Gemini 1.5 Flash)
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_text(
    prompt: str,
    system_instruction: str = "",
    model_name: str = "gemini-2.0-flash",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """
    텍스트 → Gemini 응답.

    Parameters
    ----------
    prompt            : 사용자 질문 / 분석 요청
    system_instruction: 역할 지시 (예: "당신은 임상 AI입니다")
    model_name        : 기본값 gemini-2.5-flash (빠름·저비용)
    max_tokens        : 최대 출력 토큰 수
    temperature       : 창의성 0.0(확정적) ~ 1.0(창의적)

    Returns
    -------
    str: Gemini 응답 텍스트 (API 실패 시 시뮬레이션 결과)
    """
    if not _ensure_genai():
        return _simulate_text_response(prompt, system_instruction)

    try:
        # system_instruction 포함 모델 초기화
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction if system_instruction else None,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        logger.error(f"❌ Gemini 텍스트 API 오류: {e}")
        return _simulate_text_response(prompt, system_instruction)


# ═══════════════════════════════════════════════════════════════════════════════
# Vision AI — 이미지 분석 (Gemini 1.5 Pro Vision)
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_vision(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    system_instruction: str = "",
    model_name: str = "gemini-2.0-flash",
) -> str:
    """
    이미지 + 텍스트 → Gemini Vision 분석.

    처방전·약포지 사진을 실제로 읽어 약품명·용량·주의사항을 OCR 수준으로 추출.
    파일명 대조 방식 완전 대체.

    Parameters
    ----------
    image_bytes  : 이미지 바이너리 (JPEG/PNG/WEBP 등)
    mime_type    : "image/jpeg" / "image/png" 등
    prompt       : 분석 요청 텍스트
    model_name   : Pro 모델 권장 (Vision 품질 우수)
    """
    if not _ensure_genai():
        return _simulate_vision_response(prompt)

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction if system_instruction else None,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2048,
                temperature=0.2,      # 이미지 분석은 낮은 온도 = 정확한 사실 위주
            ),
        )
        # 이미지 파트를 inline data로 전달
        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            }
        }
        response = model.generate_content([image_part, prompt])
        return response.text.strip()

    except Exception as e:
        logger.error(f"❌ Gemini Vision API 오류: {e}")
        return _simulate_vision_response(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 지식베이스 RAG 보강 설명
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_rag(
    query: str,
    kb_results: List[Dict],
    patient_context: str = "",
) -> str:
    """
    KB 검색 결과 + Gemini AI → 종합 임상 설명 생성.

    Parameters
    ----------
    query          : 원래 검색어
    kb_results     : kb_search() 반환 결과 리스트
    patient_context: 현재 환자 나이·병명·처방 (선택)
    """
    # KB 결과 텍스트 직렬화
    kb_text = ""
    for r in kb_results:
        kb_text += f"\n[{r['type']} - {r['title']}]\n"
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
        "위 정보를 바탕으로 임상적으로 중요한 내용을 이해하기 쉽게 설명해주세요. "
        "특히 주의사항과 환자 복약지도에 필요한 핵심을 강조해주세요."
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
    """
    음성 인식 텍스트 → 환자 맥락 + Gemini → 임상 답변.

    Parameters
    ----------
    voice_text   : STT 결과 텍스트
    patient_info : {"age": 68, "hospital": "삼성서울병원", ...}
    prescriptions: 현재 처방 리스트
    """
    # 처방 요약
    rx_summary = "\n".join([
        f"- {r['medication_name']} ({r['cancer_type']}) "
        f"{r['dosage']} {r['frequency']} "
        f"효능:{r.get('efficacy_rate','-')}% 부작용:{r.get('side_effects','-')}"
        for r in prescriptions
    ])

    system = (
        "당신은 PHARMA-HYBRID 임상 AI 어시스턴트입니다. "
        "항암제·처방약에 대한 전문적인 임상 정보를 한국어로 명확하게 답변합니다. "
        "고객 개인정보 보호를 준수하며, 의학적 조언은 반드시 담당의와 상담을 권장합니다. "
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
# 복약 이행도 AI 평가
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_adherence_advice(
    patient_name: str,
    compliance_rate: float,
    missed_drugs: List[str],
    disease: str,
) -> str:
    """
    복약 이행도 데이터 → Gemini → 환자별 맞춤 복약 독려 메시지.

    Parameters
    ----------
    patient_name   : 환자명
    compliance_rate: 0~100 (%)
    missed_drugs   : 최근 빠진 약 목록
    disease        : 주요 질환명
    """
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
# 시뮬레이션 폴백 (API 키 없을 때)
# ═══════════════════════════════════════════════════════════════════════════════

def _simulate_text_response(prompt: str, system: str = "") -> str:
    """API 키 없을 때의 로컬 시뮬레이션 응답."""
    import time
    time.sleep(0.8)  # 실제 API 응답 시간 흉내

    if "이미지 분석" in system or "Vision" in system:
        return _simulate_vision_response(prompt)
    if "복약" in system or "adherence" in system.lower():
        return "💊 복약을 꾸준히 유지해 주세요. 정해진 시간에 약을 드시면 치료 효과가 높아집니다. [시뮬레이션 모드 — GOOGLE_API_KEY 설정 필요]"
    if "임상 지식" in system or "RAG" in prompt[:30]:
        return (
            "📚 [엣지 AI 분석 완료 — 시뮬레이션]\n"
            "임상 데이터베이스 분석 결과: 해당 항목은 주요 가이드라인에서 권장되는 표준 치료법에 해당합니다. "
            "장기 복용 시 정기적인 혈액 검사와 상태 모니터링을 권장합니다.\n"
            "⚠️ [GOOGLE_API_KEY를 설정하면 실제 Gemini AI 분석이 활성화됩니다]"
        )
    return (
        "🎙️ [엣지 AI 분석 완료 — 시뮬레이션]\n"
        "명령하신 상황을 분석했습니다. 현재까지 수집된 데이터 상으로는 "
        "임상적 특이 소견이나 즉각적인 부작용 징후가 없습니다.\n"
        "⚠️ [GOOGLE_API_KEY를 설정하면 실제 Gemini AI 분석이 활성화됩니다]"
    )


def _simulate_vision_response(prompt: str) -> str:
    """Vision API 없을 때 파일명 기반 시뮬레이션 (기존 방식 호환)."""
    import re
    m = re.search(r"처방:?\s*([^\n]+)", prompt)
    rx_list = m.group(1) if m else "베실리온정, 코대원정, 슈다페드정, 베아솔론정"
    return (
        "🔬 [Vision AI 분석 완료 — 시뮬레이션]\n"
        f"이미지에서 약품 정보를 인식했습니다: {rx_list}\n\n"
        "식별된 약물에 심각한 상호작용은 없으나, "
        "자몽주스·고지방 식사는 피하시고 식후 복용을 권장합니다.\n"
        "⚠️ [GOOGLE_API_KEY + Gemini Pro Vision을 설정하면 실제 OCR 분석이 활성화됩니다]"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 편의 함수 — 기존 call_gemini 호환 래퍼
# ═══════════════════════════════════════════════════════════════════════════════

def call_gemini_compat(contents: list, system: str = "") -> str:
    """
    기존 call_gemini(contents, system) 시그니처 그대로 호환.
    내부적으로는 실제 Gemini API or 시뮬레이션으로 분기.
    """
    # contents 에서 텍스트·이미지 추출
    text_parts = []
    image_part = None

    for part in contents[0].get("parts", []):
        if "text" in part:
            text_parts.append(part["text"])
        elif "inlineData" in part:
            image_part = part["inlineData"]

    prompt_text = "\n".join(text_parts)

    # 이미지가 있으면 Vision 경로
    if image_part:
        img_bytes = base64.b64decode(image_part["data"])
        mime = image_part.get("mimeType", "image/jpeg")
        return call_gemini_vision(img_bytes, mime, prompt_text, system_instruction=system)

    # 텍스트 경로
    return call_gemini_text(prompt_text, system_instruction=system)


# ═══════════════════════════════════════════════════════════════════════════════
# 상태 확인
# ═══════════════════════════════════════════════════════════════════════════════

def get_engine_status() -> Dict:
    """현재 엔진 상태 반환 (UI 표시용)."""
    ready = _ensure_genai()
    return {
        "sdk_installed": HAS_GENAI,
        "api_key_set": bool(_load_api_key()),
        "ready": ready,
        "mode": "🟢 Gemini API 실제 연동" if ready else "🟡 시뮬레이션 모드",
        "model_text": "gemini-2.0-flash",
        "model_vision": "gemini-2.0-flash",
    }
