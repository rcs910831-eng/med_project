# -*- coding: utf-8 -*-
"""
vision_engine.py
약사 AI 비전 모듈 — 처방전·약봉지·낱알 이미지 분석

지원 엔진 (우선순위):
  1. Claude API (claude-sonnet-4-6) — Anthropic SDK
  2. Gemini Vision (langchain-google-genai)
  3. Tesseract OCR (pytesseract)
  4. 로컬 이미지 매핑 (medical_knowledge_engine.DRUG_IMAGE_MAP)
  5. Mock 모드 (API 없을 때 시뮬레이션)
"""

import os
import base64
import json
from pathlib import Path
from typing import Dict, Optional

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    pytesseract = None
    HAS_TESSERACT = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from medical_knowledge_engine import (
        DRUG_IMAGE_MAP,
        DRUG_APPEARANCE_DB,
        get_drug_image_path,
        get_prescription_images,
        get_pill_bag_images,
    )
    HAS_MED_ENGINE = True
except ImportError:
    HAS_MED_ENGINE = False
    DRUG_IMAGE_MAP = {}
    DRUG_APPEARANCE_DB = {}

    def get_drug_image_path(_): return None
    def get_prescription_images(): return []
    def get_pill_bag_images(): return []


# ════════════════════════════════════════════════════════════════════════════════
# 이미지 유틸
# ════════════════════════════════════════════════════════════════════════════════

def _to_base64(image_path: str):
    """이미지 파일 → (base64_str, media_type)."""
    ext = Path(image_path).suffix.lower().lstrip(".")
    media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                  "png": "image/png", "gif": "image/gif"}.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8"), media_type


def _ocr_text(image_path: str) -> str:
    """Tesseract OCR로 텍스트 추출 (한국어+영어)."""
    if not HAS_TESSERACT or not HAS_PIL:
        return ""
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang="kor+eng").strip()
    except Exception as e:
        return f"[OCR 오류] {e}"


# ════════════════════════════════════════════════════════════════════════════════
# VisionEngine 클래스
# ════════════════════════════════════════════════════════════════════════════════

class VisionEngine:
    """
    약사 AI — 비전 인식 통합 엔진.

    우선순위:
    1) Claude API  2) Gemini Vision  3) OCR만  4) Mock
    """

    def __init__(self, prefer: str = "claude", anthropic_key: str = "",
                 gemini_key: str = ""):
        self.prefer = prefer
        self.anthropic_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.gemini_key    = gemini_key    or os.environ.get("GOOGLE_API_KEY", "")

        self._claude_client = None
        self._vlm = None
        self._vlm_available = False

        self._init_claude()
        if not self._claude_client:
            self._init_gemini()

        engine_name = ("Claude" if self._claude_client
                       else "Gemini" if self._vlm_available
                       else "OCR+Mock")
        print(f"[VisionEngine] 활성 엔진: {engine_name}")

    # ── 초기화 ───────────────────────────────────────────────────────────────

    def _init_claude(self):
        if not HAS_ANTHROPIC:
            return
        try:
            self._claude_client = (
                anthropic.Anthropic(api_key=self.anthropic_key)
                if self.anthropic_key else anthropic.Anthropic()
            )
            print("[VisionEngine] Claude API 초기화 성공.")
        except Exception as e:
            print(f"[VisionEngine] Claude 초기화 실패: {e}")
            self._claude_client = None

    def _init_gemini(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._vlm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
            self._vlm_available = True
            print("[VisionEngine] Gemini Vision 초기화 성공.")
        except Exception:
            self._vlm_available = False

    # ── 핵심: Vision 호출 ────────────────────────────────────────────────────

    def _call_vision(self, image_path: str, prompt: str) -> str:
        """이미지 + 프롬프트 → 텍스트 응답 (Claude → Gemini → Mock 순서)."""
        if not os.path.exists(image_path):
            return f"[오류] 파일 없음: {image_path}"

        # 1) Claude API
        if self._claude_client:
            try:
                img_data, media_type = _to_base64(image_path)
                msg = self._claude_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": [
                        {"type": "image",
                         "source": {"type": "base64",
                                    "media_type": media_type,
                                    "data": img_data}},
                        {"type": "text", "text": prompt},
                    ]}],
                )
                return msg.content[0].text
            except Exception as e:
                print(f"[VisionEngine] Claude 호출 실패: {e}")

        # 2) Gemini Vision
        if self._vlm_available:
            try:
                from langchain_core.messages import HumanMessage
                img_data, _ = _to_base64(image_path)
                message = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}},
                ])
                resp = self._vlm.invoke([message])
                return resp.content
            except Exception as e:
                print(f"[VisionEngine] Gemini 호출 실패: {e}")

        # 3) Mock 응답
        return self._mock_response(image_path, prompt)

    def _mock_response(self, image_path: str, prompt: str) -> str:
        """Vision API 없을 때 로컬 매핑 기반 시뮬레이션."""
        filename = Path(image_path).name.lower()

        # 약품 이미지 매핑에서 검색
        for drug_name, mapped_path in DRUG_IMAGE_MAP.items():
            if Path(mapped_path).name.lower() == filename:
                appearance = DRUG_APPEARANCE_DB.get(drug_name, {})
                return json.dumps({
                    "약품명": drug_name,
                    "색상": appearance.get("색상", ""),
                    "모양": appearance.get("모양", ""),
                    "각인": appearance.get("각인", ""),
                    "제형": appearance.get("제형", ""),
                    "mock": True,
                }, ensure_ascii=False)

        # 처방전 / 약봉지 기본 Mock
        if "template" in filename or "prescription" in filename:
            return json.dumps({
                "처방약물": [{"약품명": "타세바정", "용량": "150mg", "용법": "1일1회"}],
                "진단명": "비소세포폐암 (EGFR 돌연변이)",
                "mock": True,
            }, ensure_ascii=False)
        if "bag" in filename or "pill" in filename:
            return json.dumps({
                "약품명_목록": ["타이레놀정 500mg", "노바스크정 5mg"],
                "복용시간": "식후 30분",
                "복용횟수": "1일 2회",
                "mock": True,
            }, ensure_ascii=False)

        return json.dumps({"result": "Vision API 없음. 이미지 분석 불가.", "mock": True},
                          ensure_ascii=False)

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def extract_text_from_prescription(self, image_path: str) -> str:
        """처방전 이미지에서 텍스트 추출 (OCR 우선, 없으면 Vision)."""
        ocr = _ocr_text(image_path)
        if len(ocr) > 30:
            return ocr

        prompt = (
            "이 처방전 이미지에 있는 모든 텍스트를 그대로 추출하세요. "
            "약품명, 용량, 용법, 진단명, 병원명, 날짜를 빠짐없이 포함하세요. "
            "환자 이름과 주민번호는 *** 로 마스킹하세요."
        )
        return self._call_vision(image_path, prompt)

    def analyze_pill_image(self, image_path: str) -> Dict:
        """낱알 이미지 분석 → 약품 외형 및 식별 정보."""
        # 로컬 매핑 우선 확인
        if HAS_MED_ENGINE:
            matched = get_drug_image_path(Path(image_path).stem)
            if matched:
                drug_name = next(
                    (n for n, p in DRUG_IMAGE_MAP.items()
                     if Path(p).stem.lower() == Path(image_path).stem.lower()), None)
                if drug_name:
                    return {
                        "detected_drug": drug_name,
                        "appearance": DRUG_APPEARANCE_DB.get(drug_name, {}),
                        "match_method": "로컬 이미지 매핑",
                    }

        prompt = (
            "당신은 30년 경력 약사입니다. 이 약 낱알 이미지를 분석하여 순수 JSON으로만 답하세요:\n"
            '{"shape": "모양", "color": "색상", "mark": "각인", '
            '"detected_drug": "약품명 추정", "form": "제형(정제/캡슐 등)"}'
        )
        raw = self._call_vision(image_path, prompt)
        try:
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception:
            return {"raw_result": raw}

    def analyze_prescription_full(self, image_path: str) -> Dict:
        """처방전 이미지 완전 구조화 분석."""
        ocr_text = _ocr_text(image_path)
        prompt = (
            "당신은 의료 처방전 분석 전문가입니다. 이미지의 처방전을 분석하여 JSON으로 반환하세요:\n"
            '{"환자정보": {"나이": "", "성별": ""}, '
            '"처방약물": [{"약품명": "", "용량": "", "용법": "", "일수": ""}], '
            '"진단명": "", "처방의": "", "병원명": "", "처방일": ""}\n'
            "이름·주민번호는 *** 마스킹. 순수 JSON만 반환."
        )
        raw = self._call_vision(image_path, prompt)
        structured = {}
        try:
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            structured = json.loads(cleaned)
        except Exception:
            structured = {"raw_result": raw}

        return {"ocr_text": ocr_text, "structured": structured,
                "image_path": image_path}

    def analyze_pill_bag(self, image_path: str) -> Dict:
        """약봉지 이미지 복약 정보 추출."""
        ocr_text = _ocr_text(image_path)
        prompt = (
            "당신은 약봉지 분석 전문가입니다. 이 약봉지에서 복약 정보를 JSON으로 추출하세요:\n"
            '{"약품명_목록": [], "복용시간": "", "복용횟수": "", '
            '"복용일수": "", "주의사항": "", "병원명": ""}\n'
            "환자 이름은 *** 마스킹. 순수 JSON만 반환."
        )
        raw = self._call_vision(image_path, prompt)
        structured = {}
        try:
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            structured = json.loads(cleaned)
        except Exception:
            structured = {"raw_result": raw}

        return {"ocr_text": ocr_text, "structured": structured,
                "image_path": image_path}

    def process_hybrid_vision(self, prescription_img_path: str,
                               pill_img_path: str) -> Dict:
        """처방전 OCR + 낱알 VLM 결합 분석 (기존 API 호환)."""
        print("[VisionEngine] 복합 비전 파이프라인 구동 중...")
        ocr_text = self.extract_text_from_prescription(prescription_img_path)
        vlm_data = self.analyze_pill_image(pill_img_path)
        return {"ocr_text": ocr_text, "vlm_analysis": vlm_data, "status": "success"}

    def get_available_drug_images(self) -> Dict[str, str]:
        """로컬에 이미지가 있는 약품 목록 반환."""
        return {name: path for name, path in DRUG_IMAGE_MAP.items()
                if os.path.exists(path)}

    def get_available_prescription_images(self) -> list:
        """로컬 처방전 이미지 목록."""
        return get_prescription_images()

    def get_available_pill_bag_images(self) -> list:
        """로컬 약봉지 이미지 목록."""
        return get_pill_bag_images()

    def batch_analyze_all_drug_images(self) -> Dict[str, Dict]:
        """
        로컬에 있는 모든 약품 이미지를 일괄 분석.
        실제 API 비용이 발생할 수 있으니 필요할 때만 호출.
        """
        results = {}
        for drug_name, img_path in DRUG_IMAGE_MAP.items():
            if not os.path.exists(img_path):
                continue
            print(f"[VisionEngine] 분석 중: {drug_name} ({img_path})")
            results[drug_name] = self.analyze_pill_image(img_path)
        return results


# ════════════════════════════════════════════════════════════════════════════════
# 모듈 자체 실행 테스트
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = VisionEngine()

    print("\n=== 1. 로컬 약품 이미지 목록 ===")
    for name, path in engine.get_available_drug_images().items():
        print(f"  {name}: {path}")

    print("\n=== 2. 처방전 이미지 목록 ===")
    for p in engine.get_available_prescription_images()[:3]:
        print(f"  {p}")

    print("\n=== 3. 약봉지 이미지 목록 ===")
    for p in engine.get_available_pill_bag_images():
        print(f"  {p}")

    # 첫 번째 약품 이미지 분석 테스트
    drug_images = engine.get_available_drug_images()
    if drug_images:
        first_drug, first_path = next(iter(drug_images.items()))
        print(f"\n=== 4. 낱알 분석: {first_drug} ===")
        result = engine.analyze_pill_image(first_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 첫 번째 처방전 이미지 분석 테스트
    rx_images = engine.get_available_prescription_images()
    if rx_images:
        print(f"\n=== 5. 처방전 OCR: {rx_images[0]} ===")
        result = engine.analyze_prescription_full(rx_images[0])
        print(f"  OCR 길이: {len(result.get('ocr_text',''))}자")
        print(f"  구조화: {result.get('structured', {})}")
