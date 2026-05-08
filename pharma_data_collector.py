# -*- coding: utf-8 -*-
"""
pharma_data_collector.py
공공데이터 + OpenFDA 기반 의약품 종합 데이터 수집기

=========================================================
데이터 출처 (Data Sources)
=========================================================
[1] 공공데이터포털 - 식약처 의약품안전나라 (data.go.kr)
    URL    : https://apis.data.go.kr/1471000/
    키     : MFDS_API_KEY (공공데이터포털 발급 인증키)
    서비스 : DrbEasyDrugInfoService       — 의약품 쉬운 정보
             MdcinGrnIdntfcInfoService01  — 의약품 낱알 식별 정보 (이미지 포함)
             DrugPrdtPrmsnInfoService04   — 의약품 허가 상세 정보
    주의   : 각 서비스를 data.go.kr에서 '활용신청' 완료 후 사용 가능
             (신청 → 즉시 또는 1-2일 내 승인)

[2] 미국 FDA OpenFDA API (api.fda.gov)
    URL    : https://api.fda.gov/drug/
    키     : 불필요 (공개 API, 1000회/일 무료)
    서비스 : label.json   — 약품 라벨 (성분, 적응증, 경고, 부작용)
             event.json   — 부작용 자발 보고(FAERS) 통계
             ndc.json     — 미국 국가약품코드 디렉토리

[3] 프로젝트 로컬 데이터
    - knowledge_base.json
    - medication_info_aihub.json (AI Hub 의약품 제형 이미지 데이터 기반)
    - med_dataset_master.json
    - data/images/ 약품 이미지

수집 결과 저장 위치: data/collected/
=========================================================
"""

import os
import sys
import json
import time
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import requests
    requests.packages.urllib3.disable_warnings()
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[오류] pip install requests 필요")

# ════════════════════════════════════════════════════════════════════════════════
# 설정
# ════════════════════════════════════════════════════════════════════════════════

MFDS_API_KEY = "3333b43c676617db26970c7a5ec6533ab613cc80b82309e175c3b3df764d4262"
OUTPUT_DIR   = Path("data/collected")
RAW_DIR      = OUTPUT_DIR / "raw"
PROCESSED_DIR= OUTPUT_DIR / "processed"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/xml, */*",
}

REQUEST_DELAY = 0.5  # API 요청 사이 딜레이(초)

# ── 한글 약품명 → 영문(FDA 검색용) 매핑 ────────────────────────────────────────
DRUG_KR_TO_EN: Dict[str, str] = {
    # ── 항암제 ──────────────────────────────────────────────────────────────
    "타세바정":      "erlotinib",
    "타그리소":      "osimertinib",
    "알레센자":      "alectinib",
    "지오트리프":    "afatinib",
    "게프티닙정":    "gefitinib",
    "키트루다":      "pembrolizumab",
    "옵디보":        "nivolumab",
    "야르보이":      "ipilimumab",
    "넥사바정":      "sorafenib",
    "글리벡정":      "imatinib",
    "허셉틴":        "trastuzumab",
    "아바스틴":      "bevacizumab",
    "입랜스":        "palbociclib",
    "페마라":        "letrozole",
    "엑스지바":      "denosumab",
    "론서프정":      "trifluridine",
    "보트리엔트정":  "pazopanib",
    "젤로다":        "capecitabine",
    "베실리온정":    "besylate supplement",
    # ── 심혈관 ──────────────────────────────────────────────────────────────
    "노바스크정":    "amlodipine",
    "플라빅스정":    "clopidogrel",
    "라식스":        "furosemide",
    "알닥톤":        "spironolactone",
    "디고신엘릭시르": "digoxin",
    "콩코르":        "bisoprolol",
    "엔트레스토":    "sacubitril valsartan",
    "리피토":        "atorvastatin",
    # ── 당뇨 / 내분비 ───────────────────────────────────────────────────────
    "다이아벡스정":  "metformin",
    "란투스":        "insulin glargine",
    "휴말로그":      "insulin lispro",
    "자누비아":      "sitagliptin",
    "포시가":        "dapagliflozin",
    # ── 호흡기 ──────────────────────────────────────────────────────────────
    "벤톨린네뷸":    "salbutamol",
    "싱귤레어츄정":  "montelukast",
    "스피리바":      "tiotropium",
    "심비코트":      "budesonide formoterol",
    "씨투스정":      "pranlukast",
    "시나지스":      "palivizumab",
    # ── 소화기 / 면역 ────────────────────────────────────────────────────────
    "무코스타정":    "rebamipide",
    "스토가정":      "lafutidine",
    "맥페란정":      "metoclopramide",
    "훼스탈플러스정": "pancreatin",
    "베아제정":      "pancreatin enzyme",
    "노루모듀얼액션": "sodium alginate",
    "휴미라":        "adalimumab",
    "이뮤란":        "azathioprine",
    "펜타사":        "mesalamine",
    # ── 신경 / 희귀 ──────────────────────────────────────────────────────────
    "리루텍정":      "riluzole",
    "메스티논정":    "pyridostigmine",
    "마도파":        "levodopa benserazide",
    "리큅":          "ropinirole",
    "케프라시럽":    "levetiracetam",
    "데파코트스프링클": "divalproex sodium",
    "엑세그란":      "zonisamide",
    "코엔자임큐텐":  "coenzyme q10",
    # ── 정신건강 ─────────────────────────────────────────────────────────────
    "렉사프로":      "escitalopram",
    "콘서타":        "methylphenidate",
    # ── 일반 의약품 ──────────────────────────────────────────────────────────
    "타이레놀정":    "acetaminophen",
    "챔프시럽":      "acetaminophen",
    "게보린정":      "acetaminophen",
    "탁센연질캡슐":  "naproxen",
    "알로퓨리놀":    "allopurinol",
    "덱사메타손":    "dexamethasone",
    "포사맥스":      "alendronate",
    "케토스테릴":    "ketoanalogues",
    "코대원정":      "dihydrocodeine",
    "모드콜S":       "acetaminophen pseudoephedrine",
    "슈다페드정":    "pseudoephedrine",
    "베아솔론정":    "methylprednisolone",
    "라니넥스나잘스프레이": "mometasone",
}

# ── 약품 → 질환 매핑 (출처 표기용) ──────────────────────────────────────────────
DRUG_DISEASE_MAP: Dict[str, List[str]] = {
    "타세바정": ["비소세포폐암(EGFR변이)"],
    "타그리소": ["비소세포폐암(EGFR T790M)"],
    "알레센자": ["비소세포폐암(ALK양성)"],
    "키트루다": ["흑색종", "비소세포폐암", "두경부암", "MSI-H 고형암"],
    "옵디보":   ["흑색종", "비소세포폐암", "신세포암", "대장암(MSI-H)"],
    "글리벡정": ["만성골수성백혈병(CML)", "GIST"],
    "허셉틴":   ["HER2양성 유방암", "HER2양성 위암"],
    "아바스틴": ["대장암", "폐암", "교모세포종"],
    "노바스크정":["고혈압", "협심증"],
    "플라빅스정":["혈전예방", "뇌졸중/심근경색 재발방지"],
    "라식스":   ["부종", "고혈압", "심부전"],
    "엔트레스토":["만성 심부전(HFrEF)"],
    "다이아벡스정":["제2형 당뇨병"],
    "란투스":   ["제1형·제2형 당뇨병"],
    "자누비아": ["제2형 당뇨병"],
    "포시가":   ["제2형 당뇨병", "심부전", "만성콩팥병"],
    "벤톨린네뷸":["천식 급성 발작"],
    "싱귤레어츄정":["천식", "알레르기비염"],
    "스피리바": ["COPD"],
    "심비코트": ["천식", "COPD"],
    "시나지스": ["RSV 감염 예방(고위험 영아)"],
    "리루텍정": ["루게릭병(ALS)"],
    "메스티논정":["중증근무력증"],
    "마도파":   ["파킨슨병"],
    "케프라시럽":["소아 뇌전증"],
    "데파코트스프링클":["소아 뇌전증", "조증"],
    "렉사프로": ["우울증", "불안장애"],
    "콘서타":   ["ADHD"],
    "휴미라":   ["크론병", "류마티스관절염"],
    "이뮤란":   ["크론병", "장기이식 거부반응"],
    "펜타사":   ["크론병", "궤양성대장염"],
    "알로퓨리놀":["통풍", "고요산혈증"],
    "타이레놀정":["두통", "발열", "근육통"],
}


# ════════════════════════════════════════════════════════════════════════════════
# 디렉토리 초기화
# ════════════════════════════════════════════════════════════════════════════════

def _init_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def _save_json(data: dict, path: Path, label: str = ""):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = path.stat().st_size / 1024
    print(f"  [저장] {path.name} ({size_kb:.1f}KB) {label}")


# ════════════════════════════════════════════════════════════════════════════════
# [1] 공공데이터포털 -- 식약처 의약품안전나라
# ════════════════════════════════════════════════════════════════════════════════

class MFDSCollector:
    """
    출처: 공공데이터포털 - 식품의약품안전처 의약품안전나라
    URL : https://apis.data.go.kr/1471000/
    주의: data.go.kr에서 각 서비스 '활용신청' 필요
          [신청 절차] data.go.kr 로그인 → 검색('식약처 의약품') → 활용신청 → 승인대기(1-2일)
    """

    BASE = "https://apis.data.go.kr/1471000"

    SERVICES = {
        "easy_drug":  "/DrbEasyDrugInfoService/getDrbEasyDrugList",       # 쉬운 의약품 정보
        "pill_id":    "/MdcinGrnIdntfcInfoService01/getMdcinGrnIdntfcInfoList01",  # 낱알 식별
        "perm_info":  "/DrugPrdtPrmsnInfoService04/getDrugPrdtPrmsnDtlInq04",      # 허가 상세
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, service_key: str, params: dict) -> Optional[dict]:
        """API 호출 (오류 시 None 반환)."""
        if not HAS_REQUESTS:
            return None
        url = self.BASE + self.SERVICES[service_key]
        p = {"serviceKey": self.api_key, "type": "json", "numOfRows": 10, **params}
        try:
            r = requests.get(url, params=p, timeout=10, headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                items = data.get("body", {}).get("items", [])
                return {"status": "success", "items": items,
                        "source": f"공공데이터포털 식약처 {service_key}",
                        "source_url": url, "collected_at": datetime.now().isoformat()}
            else:
                return {"status": f"HTTP_{r.status_code}",
                        "note": "data.go.kr 서비스 활용신청 필요",
                        "how_to_fix": "https://data.go.kr 로그인 → 해당 서비스 검색 → 활용신청",
                        "source": f"공공데이터포털 식약처 {service_key}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_drug_info(self, drug_name: str) -> dict:
        """식약처 의약품 쉬운 정보 조회."""
        result = self._get("easy_drug", {"itemName": drug_name})
        if result and result.get("status") == "success" and result.get("items"):
            item = result["items"][0]
            return {
                "drug_name_kr": drug_name,
                "drug_name_official": item.get("itemName", ""),
                "efficacy": item.get("efcyQesitm", ""),
                "usage": item.get("useMethodQesitm", ""),
                "precaution": item.get("atpnQesitm", ""),
                "side_effects": item.get("seQesitm", ""),
                "storage": item.get("depositMethodQesitm", ""),
                "source": "식품의약품안전처 의약품안전나라",
                "source_api": "data.go.kr/1471000/DrbEasyDrugInfoService",
                "collected_at": datetime.now().isoformat(),
            }
        return {"drug_name_kr": drug_name, "status": result.get("status", "unknown"),
                "note": "data.go.kr 활용신청 필요",
                "service_url": "https://www.data.go.kr/data/15075057/openapi.do"}

    def get_pill_appearance(self, drug_name: str) -> dict:
        """식약처 낱알 식별 정보 (이미지 URL 포함) 조회."""
        result = self._get("pill_id", {"itemName": drug_name})
        if result and result.get("status") == "success" and result.get("items"):
            item = result["items"][0]
            return {
                "drug_name_kr": drug_name,
                "color_front": item.get("colorClass1", ""),
                "color_back": item.get("colorClass2", ""),
                "shape": item.get("chart", ""),
                "form": item.get("formCodeName", ""),
                "print_front": item.get("printFront", ""),
                "print_back": item.get("printBack", ""),
                "image_url": item.get("itemImage", ""),
                "length_long": item.get("lengLong", ""),
                "length_short": item.get("lengShort", ""),
                "source": "식품의약품안전처 낱알 식별 정보",
                "source_api": "data.go.kr/1471000/MdcinGrnIdntfcInfoService01",
                "collected_at": datetime.now().isoformat(),
            }
        return {"drug_name_kr": drug_name, "status": result.get("status", "unknown"),
                "note": "data.go.kr 낱알식별 서비스 활용신청 필요",
                "service_url": "https://www.data.go.kr/data/15057639/openapi.do"}

    def collect_all(self, drug_names: List[str]) -> dict:
        """전체 약품 목록 수집."""
        print(f"\n[식약처 API] {len(drug_names)}개 약품 수집 시도...")
        results = {}
        for drug in drug_names:
            info = self.get_drug_info(drug)
            pill = self.get_pill_appearance(drug)
            results[drug] = {
                "drug_info": info,
                "pill_appearance": pill,
            }
            time.sleep(REQUEST_DELAY)
            sys.stdout.write(f"\r  진행: {list(drug_names).index(drug)+1}/{len(drug_names)} - {drug}    ")
            sys.stdout.flush()
        print()
        return results


# ════════════════════════════════════════════════════════════════════════════════
# [2] 미국 FDA OpenFDA API (키 불필요, 완전 공개)
# ════════════════════════════════════════════════════════════════════════════════

class OpenFDACollector:
    """
    출처: 미국 FDA OpenFDA
    URL : https://api.fda.gov/drug/
    키  : 불필요 (공개 API, 1,000 요청/일 무료 / API Key 등록 시 120,000요청/일)
    데이터: 미국 FDA 공식 약품 데이터 (영문, 국제 성분명 기준)
    """

    BASE = "https://api.fda.gov/drug"

    def _get(self, endpoint: str, params: dict) -> Optional[dict]:
        if not HAS_REQUESTS:
            return None
        url = f"{self.BASE}/{endpoint}"
        try:
            r = requests.get(url, params=params, timeout=15,
                             headers=HEADERS, verify=False)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception as e:
            print(f"  [OpenFDA 오류] {endpoint}: {e}")
            return None

    def get_drug_label(self, generic_name: str) -> dict:
        """FDA 약품 라벨 정보 (적응증, 경고, 부작용, 용법)."""
        data = self._get("label.json",
                         {"search": f'openfda.generic_name:"{generic_name}"',
                          "limit": 1})
        if not data or not data.get("results"):
            # brand_name으로 재시도
            data = self._get("label.json",
                             {"search": f'openfda.brand_name:"{generic_name}"',
                              "limit": 1})
        if data and data.get("results"):
            item = data["results"][0]
            openfda = item.get("openfda", {})
            return {
                "generic_name_en": generic_name,
                "brand_names": openfda.get("brand_name", []),
                "manufacturer": openfda.get("manufacturer_name", []),
                "route": openfda.get("route", []),
                "indications": (item.get("indications_and_usage") or [""])[0][:500],
                "dosage": (item.get("dosage_and_administration") or [""])[0][:400],
                "warnings": (item.get("warnings") or [""])[0][:400],
                "adverse_reactions": (item.get("adverse_reactions") or [""])[0][:400],
                "contraindications": (item.get("contraindications") or [""])[0][:400],
                "drug_interactions": (item.get("drug_interactions") or [""])[0][:300],
                "pregnancy_category": (item.get("pregnancy") or [""])[0][:200],
                "source": "미국 FDA OpenFDA - Drug Label (SPL)",
                "source_url": "https://api.fda.gov/drug/label.json",
                "collected_at": datetime.now().isoformat(),
            }
        return {"generic_name_en": generic_name, "status": "not_found",
                "source": "미국 FDA OpenFDA"}

    def get_adverse_events_top(self, generic_name: str, top_n: int = 10) -> dict:
        """약물 부작용 자발보고(FAERS) 상위 반응 통계."""
        data = self._get("event.json", {
            "search": f'patient.drug.medicinalproduct:"{generic_name.upper()}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": top_n,
        })
        if data and data.get("results"):
            events = [{"reaction": r["term"], "count": r["count"]}
                      for r in data["results"]]
            return {
                "generic_name_en": generic_name,
                "top_adverse_events": events,
                "total_reports": data.get("meta", {}).get("results", {}).get("total", 0),
                "source": "미국 FDA FAERS (부작용 자발보고 시스템)",
                "source_url": "https://api.fda.gov/drug/event.json",
                "note": "FAERS 보고는 인과관계를 의미하지 않으며 보고 빈도 기반 통계입니다.",
                "collected_at": datetime.now().isoformat(),
            }
        return {"generic_name_en": generic_name, "top_adverse_events": [],
                "source": "미국 FDA FAERS"}

    def get_ndc_info(self, generic_name: str) -> dict:
        """미국 NDC(국가약품코드) 디렉토리 정보."""
        data = self._get("ndc.json", {
            "search": f'generic_name:"{generic_name}"',
            "limit": 3,
        })
        if data and data.get("results"):
            results = []
            for item in data["results"]:
                results.append({
                    "brand_name": item.get("brand_name", ""),
                    "labeler": item.get("labeler_name", ""),
                    "dosage_form": item.get("dosage_form", ""),
                    "route": item.get("route", []),
                    "active_ingredients": item.get("active_ingredients", []),
                    "product_ndc": item.get("product_ndc", ""),
                })
            return {
                "generic_name_en": generic_name,
                "ndc_products": results,
                "source": "미국 FDA NDC 국가약품코드 디렉토리",
                "source_url": "https://api.fda.gov/drug/ndc.json",
                "collected_at": datetime.now().isoformat(),
            }
        return {"generic_name_en": generic_name, "ndc_products": [],
                "source": "미국 FDA NDC"}

    def collect_all(self, drug_map: Dict[str, str]) -> dict:
        """전체 약품 OpenFDA 데이터 수집."""
        print(f"\n[OpenFDA] {len(drug_map)}개 약품 수집 중...")
        results = {}
        items = list(drug_map.items())
        for idx, (kr_name, en_name) in enumerate(items):
            sys.stdout.write(f"\r  [{idx+1}/{len(items)}] {kr_name} ({en_name})    ")
            sys.stdout.flush()

            label     = self.get_drug_label(en_name)
            adverse   = self.get_adverse_events_top(en_name, top_n=8)
            ndc       = self.get_ndc_info(en_name)

            results[kr_name] = {
                "korean_name":  kr_name,
                "english_name": en_name,
                "diseases":     DRUG_DISEASE_MAP.get(kr_name, []),
                "fda_label":    label,
                "faers_top_ae": adverse,
                "ndc_info":     ndc,
            }
            time.sleep(REQUEST_DELAY)
        print()
        return results


# ════════════════════════════════════════════════════════════════════════════════
# [3] 로컬 데이터 통합 로더
# ════════════════════════════════════════════════════════════════════════════════

class LocalDataCollector:
    """
    출처: 프로젝트 로컬 데이터 파일
    - knowledge_base.json           : 병원 식이·약물 지식
    - medication_info_aihub.json    : AI Hub 의약품 제형 이미지 데이터 (dataSetSn=576)
    - med_dataset_master.json       : 의약품 마스터 데이터셋
    - data/images/                  : 약품·처방전·약봉지 이미지 13종
    """

    def collect(self, base_dir: str = ".") -> dict:
        print("\n[로컬 데이터] 수집 중...")
        result = {}

        files = {
            "knowledge_base":   os.path.join(base_dir, "knowledge_base.json"),
            "aihub_drug_info":  os.path.join(base_dir, "data/raw/texts/medication_info_aihub.json"),
            "med_master":       os.path.join(base_dir, "data/raw/texts/med_dataset_master.json"),
        }

        for key, path in files.items():
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    result[key] = {
                        "data": data,
                        "source": f"프로젝트 로컬 파일: {os.path.basename(path)}",
                        "source_original": self._get_source_desc(key),
                        "file_path": path,
                        "count": len(data) if isinstance(data, list) else len(data.keys()),
                    }
                    print(f"  [{key}] {result[key]['count']}건 로드")
                except Exception as e:
                    result[key] = {"error": str(e)}
            else:
                result[key] = {"status": "파일 없음", "path": path}

        # 이미지 파일 목록
        image_dir = os.path.join(base_dir, "data/images")
        images = {}
        for root, dirs, files_list in os.walk(image_dir):
            for fname in files_list:
                if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    rel_path = os.path.relpath(os.path.join(root, fname), base_dir)
                    category = os.path.basename(root)
                    if category not in images:
                        images[category] = []
                    images[category].append(rel_path.replace("\\", "/"))

        result["images"] = {
            "data": images,
            "source": "프로젝트 로컬 이미지 (data/images/)",
            "source_original": "AI Hub 의약품 제형 이미지 데이터 (dataSetSn=576) + 처방전/약봉지 샘플",
            "total_count": sum(len(v) for v in images.values()),
        }
        print(f"  [이미지] {result['images']['total_count']}개 발견")

        return result

    @staticmethod
    def _get_source_desc(key: str) -> str:
        sources = {
            "knowledge_base":  "병원 식이·약물 지식 베이스 (프로젝트 구축)",
            "aihub_drug_info": "AI Hub 의약품 제형 이미지 데이터 (dataSetSn=576) + 식약처 가이드라인",
            "med_master":      "국내 의약품 마스터 데이터셋 (식약처·약학정보원 기반)",
        }
        return sources.get(key, "내부 데이터")


# ════════════════════════════════════════════════════════════════════════════════
# 통합 수집 실행
# ════════════════════════════════════════════════════════════════════════════════

def run_collection(drug_subset: Optional[List[str]] = None) -> dict:
    """
    전체 데이터 수집 실행.
    drug_subset: 특정 약품만 수집할 경우 목록 지정 (None이면 전체)
    """
    _init_dirs()
    drug_names = drug_subset or list(DRUG_KR_TO_EN.keys())
    drug_map   = {k: v for k, v in DRUG_KR_TO_EN.items() if k in drug_names}

    print("=" * 60)
    print("PHARMA 데이터 수집기 시작")
    print(f"수집 약품: {len(drug_names)}개")
    print(f"출력 경로: {OUTPUT_DIR.absolute()}")
    print("=" * 60)

    # ── [1] 공공데이터포털 (식약처) ────────────────────────────────────────────
    print("\n[1/3] 공공데이터포털 -- 식약처 의약품안전나라")
    mfds = MFDSCollector(MFDS_API_KEY)
    mfds_data = mfds.collect_all(drug_names)
    mfds_path = RAW_DIR / f"mfds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    _save_json({
        "source": "공공데이터포털 - 식품의약품안전처 의약품안전나라",
        "source_url": "https://apis.data.go.kr/1471000/",
        "api_key_note": "인증키: data.go.kr 발급 (서비스별 활용신청 필요)",
        "service_ids": {
            "의약품쉬운정보": "https://www.data.go.kr/data/15075057/openapi.do",
            "낱알식별정보":   "https://www.data.go.kr/data/15057639/openapi.do",
        },
        "collected_at": datetime.now().isoformat(),
        "data": mfds_data,
    }, mfds_path, "← 공공데이터포털 식약처")

    # ── [2] OpenFDA ────────────────────────────────────────────────────────────
    print("\n[2/3] 미국 FDA OpenFDA API")
    fda = OpenFDACollector()
    fda_data = fda.collect_all(drug_map)
    fda_path = RAW_DIR / f"openfda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    _save_json({
        "source": "미국 FDA OpenFDA (api.fda.gov)",
        "source_urls": {
            "label":  "https://api.fda.gov/drug/label.json",
            "events": "https://api.fda.gov/drug/event.json",
            "ndc":    "https://api.fda.gov/drug/ndc.json",
        },
        "license": "CC0 Public Domain (미국 정부 공개 데이터)",
        "note": "영문 데이터. 미국 FDA 승인 기준으로 한국 허가 내용과 다를 수 있음.",
        "collected_at": datetime.now().isoformat(),
        "data": fda_data,
    }, fda_path, "← OpenFDA")

    # ── [3] 로컬 데이터 ────────────────────────────────────────────────────────
    print("\n[3/3] 로컬 데이터 파일 통합")
    local_collector = LocalDataCollector()
    local_data = local_collector.collect()
    local_path = RAW_DIR / f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    _save_json({
        "source": "프로젝트 로컬 데이터",
        "files": ["knowledge_base.json", "medication_info_aihub.json",
                  "med_dataset_master.json", "data/images/"],
        "collected_at": datetime.now().isoformat(),
        "data": local_data,
    }, local_path, "← 로컬")

    # ── 통합 마스터 데이터셋 생성 ─────────────────────────────────────────────
    print("\n[통합] 마스터 데이터셋 생성 중...")
    master = _build_master_dataset(drug_names, drug_map, mfds_data, fda_data, local_data)
    master_path = PROCESSED_DIR / "drug_master.json"
    _save_json(master, master_path, "← 최종 통합 마스터")

    # ── 수집 요약 ──────────────────────────────────────────────────────────────
    summary = _build_summary(mfds_data, fda_data, local_data)
    summary_path = PROCESSED_DIR / "collection_summary.json"
    _save_json(summary, summary_path, "← 수집 요약")

    print("\n" + "=" * 60)
    print("수집 완료!")
    print(f"  총 약품    : {len(drug_names)}개")
    print(f"  공공데이터 : {summary['mfds']['success']}개 성공 / {summary['mfds']['pending']}개 활용신청 필요")
    print(f"  OpenFDA    : {summary['openfda']['label_found']}개 FDA 라벨 확보")
    print(f"  FAERS 부작용: {summary['openfda']['ae_found']}개 약품 통계 확보")
    print(f"  로컬 데이터 : {summary['local']['image_count']}개 이미지")
    print(f"\n  저장 위치  : {OUTPUT_DIR.absolute()}")
    print("=" * 60)

    return {"master_path": str(master_path), "summary": summary}


def _build_master_dataset(drug_names, drug_map, mfds_data, fda_data, local_data) -> dict:
    """세 소스를 약품 단위로 통합."""
    drugs_master = {}

    for kr_name in drug_names:
        en_name = drug_map.get(kr_name, "")
        mfds = mfds_data.get(kr_name, {})
        fda  = fda_data.get(kr_name, {})
        diseases = DRUG_DISEASE_MAP.get(kr_name, [])

        drug_entry = {
            "korean_name":  kr_name,
            "english_name": en_name,
            "diseases":     diseases,
            "data_sources": [],

            # 공공데이터포털 식약처
            "mfds_easy_info": mfds.get("drug_info", {}),
            "mfds_appearance": mfds.get("pill_appearance", {}),

            # OpenFDA
            "fda_label":    fda.get("fda_label", {}),
            "faers_top_ae": fda.get("faers_top_ae", {}),
            "ndc_info":     fda.get("ndc_info", {}),
        }

        # 출처 표기
        if mfds.get("drug_info", {}).get("source"):
            drug_entry["data_sources"].append({
                "source": mfds["drug_info"]["source"],
                "url": "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService",
            })
        if fda.get("fda_label", {}).get("source"):
            drug_entry["data_sources"].append({
                "source": fda["fda_label"]["source"],
                "url": "https://api.fda.gov/drug/label.json",
                "license": "CC0 Public Domain",
            })
        if fda.get("faers_top_ae", {}).get("source"):
            drug_entry["data_sources"].append({
                "source": fda["faers_top_ae"]["source"],
                "url": "https://api.fda.gov/drug/event.json",
            })

        drugs_master[kr_name] = drug_entry

    return {
        "version": "1.0",
        "description": "PHARMA-HYBRID 의약품 통합 마스터 데이터셋",
        "generated_at": datetime.now().isoformat(),
        "total_drugs": len(drugs_master),
        "data_sources": [
            {
                "name": "공공데이터포털 - 식품의약품안전처 의약품안전나라",
                "url": "https://data.go.kr",
                "api_key": "인증키 필요 (data.go.kr 발급)",
                "services": ["의약품 쉬운 정보", "낱알 식별 정보", "의약품 허가 상세"]
            },
            {
                "name": "미국 FDA OpenFDA",
                "url": "https://api.fda.gov/drug/",
                "api_key": "불필요 (공개 API)",
                "license": "CC0 Public Domain",
                "note": "영문 데이터, 미국 FDA 기준"
            },
            {
                "name": "AI Hub 의약품 제형 이미지 데이터",
                "url": "https://www.aihub.or.kr",
                "dataset_id": "dataSetSn=576",
                "note": "낱알 외형 정보 + 이미지 기반"
            },
            {
                "name": "프로젝트 내부 임상 지식 베이스",
                "url": "local",
                "note": "대한종양학회·대한내과학회 가이드라인 기반 구축"
            }
        ],
        "drugs": drugs_master,
    }


def _build_summary(mfds_data, fda_data, local_data) -> dict:
    """수집 현황 요약."""
    mfds_success = sum(
        1 for v in mfds_data.values()
        if v.get("drug_info", {}).get("source", "").startswith("식품")
    )
    fda_label_found = sum(
        1 for v in fda_data.values()
        if v.get("fda_label", {}).get("indications")
    )
    ae_found = sum(
        1 for v in fda_data.values()
        if v.get("faers_top_ae", {}).get("top_adverse_events")
    )
    image_count = local_data.get("images", {}).get("total_count", 0)

    return {
        "generated_at": datetime.now().isoformat(),
        "mfds": {
            "success": mfds_success,
            "pending": len(mfds_data) - mfds_success,
            "note": "pending 항목은 data.go.kr에서 서비스 활용신청 후 재수집 가능",
            "how_to_activate": [
                "1. https://data.go.kr 로그인",
                "2. '식약처 의약품 낱알 식별 정보' 검색",
                "3. '활용신청' 클릭 → 즉시 또는 1-2일 내 승인",
                "4. 승인 후 pharma_data_collector.py 재실행",
            ]
        },
        "openfda": {
            "label_found": fda_label_found,
            "ae_found": ae_found,
            "source": "api.fda.gov (미국 FDA 공개 API)",
        },
        "local": {
            "image_count": image_count,
            "files_loaded": [k for k, v in local_data.items()
                             if isinstance(v, dict) and "error" not in v and v.get("data")],
        },
    }


# ════════════════════════════════════════════════════════════════════════════════
# 로드 함수 (medical_knowledge_engine.py에서 사용)
# ════════════════════════════════════════════════════════════════════════════════

def load_collected_data() -> dict:
    """
    data/collected/processed/drug_master.json 로드.
    없으면 빈 dict 반환.
    """
    master_path = PROCESSED_DIR / "drug_master.json"
    if master_path.exists():
        with open(master_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_drug_from_collected(drug_name_kr: str) -> dict:
    """약품명으로 수집 데이터에서 정보 조회."""
    master = load_collected_data()
    return master.get("drugs", {}).get(drug_name_kr, {})


def get_fda_adverse_events(drug_name_kr: str) -> list:
    """약품의 FDA FAERS 상위 부작용 목록 반환."""
    drug = get_drug_from_collected(drug_name_kr)
    return drug.get("faers_top_ae", {}).get("top_adverse_events", [])


def get_fda_indications(drug_name_kr: str) -> str:
    """약품의 FDA 적응증 (영문) 반환."""
    drug = get_drug_from_collected(drug_name_kr)
    return drug.get("fda_label", {}).get("indications", "")


# ════════════════════════════════════════════════════════════════════════════════
# 메인 실행
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PHARMA 데이터 수집기")
    parser.add_argument("--drugs", nargs="*", help="특정 약품만 수집 (예: 타이레놀정 노바스크정)")
    parser.add_argument("--quick", action="store_true", help="주요 10개만 빠르게 테스트")
    args = parser.parse_args()

    if args.quick:
        subset = ["타이레놀정", "노바스크정", "키트루다", "글리벡정",
                  "다이아벡스정", "벤톨린네뷸", "렉사프로", "이뮤란",
                  "리루텍정", "마도파"]
        run_collection(drug_subset=subset)
    elif args.drugs:
        run_collection(drug_subset=args.drugs)
    else:
        run_collection()  # 전체 수집
