#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pill_recognizer.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
알약 이미지 AI 인식 모듈

인식 파이프라인:
  1. Gemini Vision Pro → 색상·모양·마킹·제형 추출
  2. 로컬 pill_image_db → 특징 기반 후보 약품 검색
  3. Gemini Vision → 후보군 중 최종 매칭 확인
  4. 환자 처방 교차 검증 → 맞으면 ✅ / 다른 약이면 ⚠️

Author: PHARMA-HYBRID Team
"""

import os
import json
import logging
import base64
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("pill_recognizer")

# ── .env 로드 ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
except ImportError:
    _ep = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_ep):
        for _l in open(_ep, encoding="utf-8"):
            _l = _l.strip()
            if _l and not _l.startswith("#") and "=" in _l:
                _k, _v = _l.split("=", 1)
                if _k.strip() and not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

from pill_image_db import (
    get_pill_from_db, search_by_features,
    get_db_stats, init_pill_db,
    PILL_FALLBACK_DB, INTL_PILL_DB,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Gemini Vision 분석
# ═══════════════════════════════════════════════════════════════════════════════

_FEATURE_EXTRACT_PROMPT = """
이 이미지에 있는 알약을 분석하여 아래 JSON 형식으로만 응답하세요.
다른 설명 없이 순수 JSON만 출력하세요.

{
  "pill_count": 1,
  "pills": [
    {
      "shape": "원형|타원형|장방형|삼각형|사각형|캡슐형|주사제|기타",
      "color_front": "하양|노랑|주황|분홍|빨강|갈색|초록|파랑|보라|회색|검정|투명",
      "color_back": "하양|노랑|... (단색이면 앞면과 동일)",
      "marking_front": "알약 앞면 각인/숫자/문자 (없으면 빈문자열)",
      "marking_back": "알약 뒷면 각인 (없으면 빈문자열)",
      "line": "있음|없음",
      "size_mm": "추정 크기 mm (모르면 null)",
      "coating": "필름코팅|당의정|나정|캡슐|주사제",
      "confidence": 0.9
    }
  ],
  "scene_type": "single_pill|multiple_pills|pill_bag|prescription|unknown",
  "notes": "기타 관찰사항"
}
"""

_MATCH_CONFIRM_PROMPT = """
아래 알약 이미지와 약품 정보를 비교하여 일치 여부를 판단하세요.

약품 정보:
{drug_info}

JSON 형식으로만 응답:
{{
  "match": true/false,
  "confidence": 0.0~1.0,
  "reason": "일치/불일치 근거 (한국어)"
}}
"""

_FULL_ANALYSIS_PROMPT = """
당신은 PHARMA-HYBRID 약품 이미지 분석 전문 AI입니다.

환자 현재 처방 약물: {patient_meds}
인식된 알약 특징: {features}
DB 매칭 후보: {candidates}

아래 항목을 모두 분석하세요:
1. **약품 동정**: 어떤 약인지 (DB 매칭 + 시각적 특징 종합)
2. **처방 일치 여부**: 환자 처방과 맞는지 ✅/⚠️/❌
3. **복용 안전 확인**: 이 약이 맞다면 복용 주의사항
4. **색상·모양·각인 설명**: 환자가 약을 구별할 수 있도록 쉽게 설명
5. **의심 시 확인 방법**: 약국·병원 재확인 필요 시 안내

마지막에 한 줄 요약 추가: "✅ [약품명] 확인됨" 또는 "⚠️ 처방 약물과 다를 수 있습니다"
"""


def _call_gemini_vision_raw(image_bytes: bytes, mime_type: str, prompt: str) -> str:
    """Gemini Vision API 직접 호출."""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            return ""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        import PIL.Image
        import io
        img = PIL.Image.open(io.BytesIO(image_bytes))
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Vision 호출 실패: {e}")
        return ""


def extract_pill_features(image_bytes: bytes, mime_type: str) -> Optional[Dict]:
    """
    Gemini Vision으로 알약 특징 추출.

    Returns
    -------
    dict: {"shape": ..., "color_front": ..., "marking_front": ..., ...}
          or None (API 실패 시)
    """
    raw = _call_gemini_vision_raw(image_bytes, mime_type, _FEATURE_EXTRACT_PROMPT)
    if not raw:
        return None
    try:
        # JSON 블록 추출
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            pills = data.get("pills", [])
            if pills:
                feat = pills[0]
                feat["scene_type"] = data.get("scene_type", "unknown")
                feat["notes"]      = data.get("notes", "")
                return feat
    except json.JSONDecodeError:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 매칭 엔진
# ═══════════════════════════════════════════════════════════════════════════════

def _score_candidate(features: Dict, candidate: Dict) -> float:
    """특징 유사도 점수 (0~1)."""
    score = 0.0
    weights = {"shape": 0.35, "color_front": 0.30, "marking_front": 0.25, "coating": 0.10}

    shape_map   = {"원형":"원형","타원형":"타원형","장방형":"장방형","캡슐형":"캡슐형"}
    color_map   = {"하양":"하양","흰색":"하양","노랑":"노랑","황색":"노랑",
                   "분홍":"분홍","핑크":"분홍","빨강":"빨강","갈색":"갈색","투명":"투명"}

    f_shape  = features.get("shape","")
    f_color  = color_map.get(features.get("color_front",""), features.get("color_front",""))
    f_mark   = (features.get("marking_front","") or "").upper().replace(" ","")
    f_coat   = features.get("coating","")

    c_shape  = candidate.get("shape","")
    c_color  = color_map.get(candidate.get("color_front",""), candidate.get("color_front",""))
    c_mark_f = (candidate.get("marking_front","") or "").upper().replace(" ","")
    c_mark_b = (candidate.get("marking_back","")  or "").upper().replace(" ","")
    c_form   = candidate.get("form_type","")

    if f_shape and c_shape and f_shape in c_shape:
        score += weights["shape"]
    if f_color and c_color and (f_color in c_color or c_color in f_color):
        score += weights["color_front"]
    if f_mark and (f_mark in c_mark_f or f_mark in c_mark_b):
        score += weights["marking_front"]
    if f_coat and c_form and (f_coat in c_form or c_form in f_coat):
        score += weights["coating"]

    return round(score, 3)


def find_matching_pills(features: Dict, top_k: int = 5) -> List[Dict]:
    """특징 기반 DB 후보 검색 + 점수 정렬."""
    color   = features.get("color_front", "")
    shape   = features.get("shape", "")
    marking = features.get("marking_front", "")

    candidates = search_by_features(color=color, shape=shape, marking=marking, limit=20)

    # 점수 계산
    scored = []
    for c in candidates:
        s = _score_candidate(features, c)
        scored.append({**c, "_score": s})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:top_k]


# ═══════════════════════════════════════════════════════════════════════════════
# 메인 인식 함수
# ═══════════════════════════════════════════════════════════════════════════════

def recognize_pill(
    image_bytes: bytes,
    mime_type: str,
    patient_info: Dict,
    patient_meds: List[str],
) -> Dict:
    """
    알약 이미지 → 종합 인식 결과.

    Parameters
    ----------
    image_bytes  : 이미지 바이너리
    mime_type    : "image/jpeg" / "image/png"
    patient_info : 환자 정보 dict
    patient_meds : 환자 처방 약물명 리스트

    Returns
    -------
    dict:
      features    : 추출된 알약 특징
      candidates  : DB 매칭 후보 (점수순)
      ai_analysis : Gemini 종합 분석 텍스트
      match_status: "confirmed" / "warning" / "unknown"
      top_match   : 최유력 약품명
      confidence  : 신뢰도 0~1
    """
    init_pill_db()
    result = {
        "features":     None,
        "candidates":   [],
        "ai_analysis":  "",
        "match_status": "unknown",
        "top_match":    None,
        "confidence":   0.0,
    }

    # ── Step 1: Gemini Vision 특징 추출 ─────────────────────────────────────
    features = extract_pill_features(image_bytes, mime_type)
    result["features"] = features

    if not features:
        # API 실패 시 기본 분석으로 fallback
        result["ai_analysis"] = _fallback_analysis(image_bytes, mime_type, patient_info, patient_meds)
        return result

    logger.info(f"🔍 특징 추출: {features.get('shape')} / {features.get('color_front')} / {features.get('marking_front')}")

    # ── Step 2: DB 후보 검색 ─────────────────────────────────────────────────
    candidates = find_matching_pills(features, top_k=5)
    result["candidates"] = candidates

    # ── Step 3: Gemini 종합 분석 ─────────────────────────────────────────────
    cand_summary = "\n".join(
        f"- {c.get('drug_name_kr','')} ({c.get('color_front','')} {c.get('shape','')}"
        f" / 각인: {c.get('marking_front','')} / 점수: {c.get('_score',0):.2f})"
        for c in candidates[:3]
    ) if candidates else "해당 약품 DB 없음"

    prompt = _FULL_ANALYSIS_PROMPT.format(
        patient_meds=", ".join(patient_meds) if patient_meds else "처방 없음",
        features=json.dumps(features, ensure_ascii=False),
        candidates=cand_summary,
    )
    ai_text = _call_gemini_vision_raw(image_bytes, mime_type, prompt)

    if not ai_text:
        ai_text = _fallback_text(features, candidates, patient_meds)

    result["ai_analysis"] = ai_text

    # ── Step 4: 매칭 상태 결정 ───────────────────────────────────────────────
    top = candidates[0] if candidates else None
    if top and top.get("_score", 0) >= 0.6:
        top_name = top.get("drug_name_kr", "")
        result["top_match"]  = top_name
        result["confidence"] = top["_score"]

        # 환자 처방 일치 확인
        matched = any(
            top_name in med or med in top_name
            for med in patient_meds
        )
        result["match_status"] = "confirmed" if matched else "warning"
    elif top and top.get("_score", 0) >= 0.3:
        result["top_match"]  = top.get("drug_name_kr","")
        result["confidence"] = top["_score"]
        result["match_status"] = "warning"
    else:
        result["match_status"] = "unknown"

    return result


def _fallback_analysis(image_bytes, mime_type, patient_info, patient_meds):
    """Gemini 특징 추출 실패 시 일반 Vision 분석."""
    prompt = (
        f"환자 처방약: {', '.join(patient_meds)}\n\n"
        "이 이미지의 알약/약품을 분석해주세요:\n"
        "1. 알약 색상, 모양, 각인 설명\n"
        "2. 환자 처방약과 일치 가능성\n"
        "3. 복용 전 확인사항"
    )
    return _call_gemini_vision_raw(image_bytes, mime_type, prompt) or (
        "⚠️ AI 분석을 완료하지 못했습니다. Google API 키를 확인하세요."
    )


def _fallback_text(features: Dict, candidates: List[Dict], patient_meds: List[str]) -> str:
    """AI 응답 없을 때 규칙 기반 텍스트 생성."""
    shape = features.get("shape","알 수 없음")
    color = features.get("color_front","알 수 없음")
    mark  = features.get("marking_front","없음")

    lines = [
        f"🔍 **알약 특징 분석**",
        f"- 모양: {shape}",
        f"- 색상: {color}",
        f"- 각인: {mark or '없음'}",
        f"- 제형: {features.get('coating','알 수 없음')}",
        "",
    ]
    if candidates:
        lines.append(f"💊 **DB 매칭 후보** (신뢰도순)")
        for c in candidates[:3]:
            lines.append(
                f"  • {c.get('drug_name_kr','')} — {c.get('manufacturer','')} "
                f"(일치도: {int(c.get('_score',0)*100)}%)"
            )
    else:
        lines.append("⚠️ DB에서 일치하는 약품을 찾지 못했습니다.")

    lines += ["", "📋 **처방 약물 대조**"]
    for med in patient_meds:
        lines.append(f"  ✓ {med}")

    lines.append("\n⚠️ 약품 동정은 반드시 약사·의사에게 최종 확인하세요.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 헬퍼
# ═══════════════════════════════════════════════════════════════════════════════

def render_recognition_result_html(result: Dict) -> str:
    """인식 결과 → Streamlit HTML 카드 (DB 이미지 포함)."""
    import sqlite3, base64
    from pill_image_db import PILL_DB

    status = result.get("match_status", "unknown")
    conf   = result.get("confidence", 0)
    top    = result.get("top_match", "")
    feats  = result.get("features") or {}

    status_map = {
        "confirmed": ("✅ 처방 약물 일치",    "#00ff88", "rgba(0,255,136,0.08)"),
        "warning":   ("⚠️ 처방과 다를 수 있음","#ffaa00", "rgba(255,170,0,0.08)"),
        "unknown":   ("❓ 확인 필요",          "#aaaaaa", "rgba(150,150,150,0.08)"),
    }
    label, color, bg = status_map.get(status, status_map["unknown"])

    # 특징 태그
    feat_html = ""
    if feats:
        def tag(icon, val):
            if not val:
                return ""
            return (
                f'<span style="background:rgba(0,242,255,0.1);border:1px solid rgba(0,242,255,0.3);'
                f'border-radius:4px;padding:2px 8px;font-size:0.72rem;color:#00e8ff;">{icon} {val}</span>'
            )
        feat_html = (
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:6px;">'
            + tag("🔵", feats.get("shape",""))
            + tag("🎨", feats.get("color_front",""))
            + tag("🔤", feats.get("marking_front",""))
            + "</div>"
        )

    # DB 이미지 표시 (후보 약물 이미지)
    img_html = ""
    cands = result.get("candidates", [])
    if cands:
        imgs = []
        try:
            conn = sqlite3.connect(PILL_DB)
            for c in cands[:4]:
                name = c.get("drug_name_kr", "")
                row = conn.execute(
                    "SELECT drug_name_kr, image_data FROM pills WHERE drug_name_kr LIKE ? AND image_data IS NOT NULL LIMIT 1",
                    (f"%{name[:5]}%",)
                ).fetchone()
                if row and row[1] and len(row[1]) > 500:
                    b64 = base64.b64encode(row[1]).decode()
                    score = int(c.get("_score", 0) * 100)
                    imgs.append(
                        f'<div style="text-align:center;flex:1;min-width:90px;max-width:130px;">'
                        f'<img src="data:image/jpeg;base64,{b64}" '
                        f'style="width:100%;max-height:90px;object-fit:contain;border-radius:6px;'
                        f'border:1px solid rgba(0,242,255,0.25);" />'
                        f'<div style="color:#c8eeff;font-size:0.68rem;margin-top:3px;'
                        f'font-family:Noto Sans KR,sans-serif;word-break:keep-all;">'
                        f'{row[0][:14]}</div>'
                        f'<div style="color:#00e8ff;font-size:0.62rem;">{score}% 일치</div>'
                        f'</div>'
                    )
            conn.close()
        except Exception:
            pass
        if imgs:
            img_html = (
                f'<div style="margin-top:10px;">'
                f'<div style="color:rgba(0,200,255,0.7);font-size:0.72rem;'
                f'font-family:Noto Sans KR,sans-serif;margin-bottom:6px;font-weight:600;">'
                f'📸 DB 매칭 후보 이미지</div>'
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;">'
                + "".join(imgs)
                + "</div></div>"
            )

    # 점수 바 (이미지 없는 후보)
    cand_html = ""
    if cands and not img_html:
        cand_html = (
            '<div style="margin-top:8px;">'
            '<div style="color:rgba(0,200,255,0.6);font-size:0.7rem;margin-bottom:5px;">DB 매칭 후보</div>'
        )
        for c in cands[:3]:
            bar = int(c.get("_score", 0) * 100)
            cand_html += (
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
                f'<span style="color:#c8eeff;font-size:0.72rem;min-width:130px;'
                f'font-family:Noto Sans KR,sans-serif;">{c.get("drug_name_kr","")[:18]}</span>'
                f'<div style="flex:1;background:rgba(0,0,0,0.4);border-radius:3px;height:7px;">'
                f'<div style="background:#00e8ff;width:{bar}%;height:7px;border-radius:3px;"></div></div>'
                f'<span style="color:#00e8ff;font-size:0.65rem;min-width:34px;">{bar}%</span>'
                f'</div>'
            )
        cand_html += "</div>"

    top_div = (
        f'<div style="color:#00f2ff;font-size:0.8rem;margin-top:5px;font-weight:700;'
        f'font-family:Noto Sans KR,sans-serif;">{top}</div>'
    ) if top else ""

    return (
        f'<div style="border:2px solid {color};border-radius:10px;padding:12px 14px;'
        f'background:{bg};margin-top:8px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="color:{color};font-size:0.88rem;font-weight:700;'
        f'font-family:Noto Sans KR,sans-serif;">{label}</span>'
        f'<span style="color:rgba(255,255,255,0.6);font-size:0.72rem;">'
        f'신뢰도 {int(conf * 100)}%</span>'
        f'</div>'
        f'{top_div}'
        f'{feat_html}'
        f'{img_html}'
        f'{cand_html}'
        f'</div>'
    )
