# -*- coding: utf-8 -*-
"""
medical_knowledge_engine.py
종합 의료 지식 엔진

통합 데이터 소스:
- 식약처 의약품안전나라 공공 API (nedrug.mfds.go.kr / data.go.kr)
- AI Hub 의약품 제형 이미지 데이터 (dataSetSn=576)
- 국립암센터 국가암등록통계 2024
- 건강보험심사평가원(HIRA) 공개 통계
- 대한종양학회·대한내과학회 진료지침 2025-2026
- 프로젝트 로컬 데이터 (knowledge_base.json, medication_info_aihub.json)
- 프로젝트 처방 이미지 (data/images/)
- OpenFDA 수집 데이터 (data/collected/processed/drug_master.json) — 70개 약품 FDA 라벨 + FAERS 부작용
- cancer_protocols_db.py — 50개 암종 임상 프로토콜 (NCCN/ESMO/국내 지침 기반)
"""

import os
import json
import sqlite3
import base64
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

try:
    from cancer_protocols_db import (
        CANCER_PROTOCOLS as _CANCER_PROTOCOLS_EXT,
        get_cancer_protocol,
        search_cancer_protocols,
        get_all_cancer_names,
        get_cancers_by_category,
    )
    HAS_CANCER_DB = True
except ImportError:
    HAS_CANCER_DB = False
    _CANCER_PROTOCOLS_EXT = {}
    def get_cancer_protocol(_): return None
    def search_cancer_protocols(_): return []
    def get_all_cancer_names(): return []
    def get_cancers_by_category(): return {}

try:
    from nutrition_diet_db import (
        CANCER_NUTRITION_GENERAL,
        CANCER_TYPE_DIET,
        CHRONIC_DISEASE_DIET,
        DATA_SOURCES as DIET_DATA_SOURCES,
        get_cancer_diet,
        get_chronic_diet,
        search_diet,
        get_food_restrictions,
        get_all_diet_categories,
        get_nutrient_targets,
    )
    HAS_NUTRITION_DB = True
except ImportError:
    HAS_NUTRITION_DB = False
    CANCER_NUTRITION_GENERAL = {}
    CANCER_TYPE_DIET = {}
    CHRONIC_DISEASE_DIET = {}
    DIET_DATA_SOURCES = {}
    def get_cancer_diet(_): return {}
    def get_chronic_diet(_): return {}
    def search_diet(_): return []
    def get_food_restrictions(_): return {}
    def get_all_diet_categories(): return {}
    def get_nutrient_targets(_): return {}

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ════════════════════════════════════════════════════════════════════════════════
# 1. 약품 이미지 매핑 (로컬 data/images/ 기반)
# ════════════════════════════════════════════════════════════════════════════════

DRUG_IMAGE_MAP: Dict[str, str] = {
    # 만성질환 / 일반약
    "다이아벡스정":   "data/images/Diabex_500mg.jpg",        # 메트포르민 (당뇨)
    "노바스크정":     "data/images/Norvasc_5mg.jpg",         # 암로디핀 (고혈압)
    "플라빅스정":     "data/images/Plavix_75mg.jpg",         # 클로피도그렐 (혈전)
    "타이레놀정":     "data/images/Tylenol_500mg.jpg",       # 아세트아미노펜 (해열)
    "보트리엔트정":   "data/images/Votrient_200mg.jpg",      # 파조파닙 (표적항암)
    "챔프시럽":       "data/images/Champ_Syrup_Guide.jpg",   # 소아 해열 (아세트아미노펜)
    "모드콜S":        "data/images/Modecol_S.jpg",           # 종합감기약
    "탁센연질캡슐":   "data/images/Tak_Sen.jpg",             # 나프록센 (소염진통)
    "게보린정":       "data/images/Geworin_Tab.jpg",         # 해열진통 복합제
    "베아제정":       "data/images/Bearse_Tab.jpg",          # 소화효소제
    "훼스탈플러스정": "data/images/Festal_Plus.jpg",         # 소화제
    "노루모듀얼액션": "data/images/Norumo_Dual.jpg",         # 제산제
    "씨투스정":       "data/images/Citus_Tab_Guide.jpg",     # 류코트리엔 길항제 (천식)
}

# 처방전 템플릿 이미지 (OCR 학습/테스트용)
PRESCRIPTION_IMAGES: List[str] = [
    f"data/images/prescriptions/template_{i}.jpg" for i in range(20)
] + [
    "data/images/prescriptions/prescription_sample_2.jpg",
    "data/images/prescriptions/prescription_sample_3.jpg",
]

# 약봉지 이미지 (약봉지 인식용)
PILL_BAG_IMAGES: List[str] = [
    "data/images/bags/pill_bag_sample_1.jpg",
    "data/images/bags/bag_sample_162933.jpg",
    "data/images/bags/bag_sample_164816.jpg",
]

# 약물 외형 정보 (AI Hub dataSetSn=576 기반)
DRUG_APPEARANCE_DB: Dict[str, Dict] = {
    "노바스크정":   {"색상": "흰색", "모양": "팔각형", "각인": "앞PF/뒤NV5",  "제형": "정제"},
    "다이아벡스정": {"색상": "흰색", "모양": "원형",   "각인": "앞DW/뒤D",    "제형": "정제"},
    "플라빅스정":   {"색상": "분홍색","모양": "원형",  "각인": "앞75/뒤1171", "제형": "정제"},
    "보트리엔트정": {"색상": "흰색", "모양": "장방형", "각인": "앞GS/뒤JT",   "제형": "정제"},
    "타이레놀정":   {"색상": "흰색", "모양": "장방형", "각인": "TYLENOL",     "제형": "정제"},
    "챔프시럽":     {"색상": "투명", "모양": "액체",   "각인": "-",           "제형": "시럽"},
    "씨투스정":     {"색상": "흰색", "모양": "원형",   "각인": "SIT",         "제형": "정제"},
    "게보린정":     {"색상": "흰색", "모양": "원형",   "각인": "GEWORIN",     "제형": "정제"},
}


# ════════════════════════════════════════════════════════════════════════════════
# 2. 종합 질환-약물 프로토콜
#    (국립암센터·대한종양학회·대한내과학회·NICE 가이드라인 기반)
# ════════════════════════════════════════════════════════════════════════════════

DISEASE_PROTOCOLS: Dict[str, Dict] = {

    # ── 암종 ──────────────────────────────────────────────────────────────────
    "폐암": {
        "ICD10": "C34", "분류": ["NSCLC(비소세포폐암) 85%", "SCLC(소세포폐암) 15%"],
        "아형": ["선암(Adenocarcinoma)", "편평세포암", "대세포암"],
        "바이오마커": ["EGFR(exon 19/21)", "ALK 재배열", "ROS1", "KRAS G12C", "PD-L1(TPS)", "MET exon14"],
        "1차_치료": {
            "EGFR 변이":    ["타그리소(osimertinib)", "타세바정(erlotinib)", "지오트리프(afatinib)", "알레센자(alectinib)"],
            "ALK 양성":     ["알레센자(alectinib)", "자이카디아(ceritinib)", "로브레나(lorlatinib)"],
            "PD-L1≥50%":   ["키트루다(pembrolizumab) 단독"],
            "PD-L1 1-49%": ["키트루다 + 백금기반 화학요법"],
            "KRAS G12C":   ["소토라십(Lumakras)", "아다그라십(Krazati)"],
            "일반":         ["카보플라틴+파클리탁셀", "FOLFOX"],
        },
        "2차_치료": ["탁소테레(docetaxel)", "알림타(pemetrexed)", "옵디보(nivolumab)"],
        "모니터링": ["CT 8-12주마다", "LVEF(타그리소)", "간기능(TKI류)", "피부발진", "설사"],
        "한국_통계": {"발생순위": "남1위·여3위", "5년생존율": "전체 36.8%, 조기 80-90%, 전이 5-10%", "출처": "국립암센터 2024"},
        "가이드라인": "대한종양학회 폐암 진료지침 2026",
        "생활습관": "금연 최우선. EGFR TKI 복용 중 자몽주스 금지. 피부 건조 예방 보습제 사용.",
    },

    "흑색종": {
        "ICD10": "C43", "분류": ["피부 흑색종", "안구 흑색종", "점막 흑색종"],
        "바이오마커": ["BRAF V600E/K(~50%)", "NRAS", "c-KIT", "PD-L1"],
        "1차_치료": {
            "BRAF V600E":   ["다브라페닙+트라메티닙(BRAF+MEK 이중차단)"],
            "면역항암":     ["키트루다(pembrolizumab)", "옵디보(nivolumab)", "야르보이(ipilimumab)+옵디보 병용"],
            "일반":         ["키트루다 단독(PD-L1 무관)"],
        },
        "2차_치료": ["야르보이(ipilimumab)", "IL-2 고용량"],
        "모니터링": ["뇌 MRI(전이 확인)", "간기능", "갑상선기능(면역항암제 irAE)"],
        "한국_통계": {"발생순위": "희귀암", "5년생존율": "국소 98%, 전이 25%", "출처": "SEER 2024"},
        "가이드라인": "대한피부과학회·대한종양학회 2025",
        "생활습관": "자외선 차단(SPF50+) 필수. ABCDE 기준 정기 자가점검.",
    },

    "간암": {
        "ICD10": "C22", "분류": ["간세포암(HCC) 75-85%", "담관세포암(ICC) 10-15%"],
        "바이오마커": ["AFP", "PIVKA-II", "Child-Pugh 점수", "BCLC 병기"],
        "1차_치료": {
            "조기(BCLC 0-A)": ["간절제술", "고주파열치료(RFA)", "경피적 에탄올 주입"],
            "중기(BCLC B)":   ["TACE(경동맥화학색전술)"],
            "진행(BCLC C)":   ["소라페닙(넥사바정)", "렌바티닙(렌비마)", "아테졸리주맙+베바시주맙"],
        },
        "2차_치료": ["레고라페닙", "카보잔티닙", "라무시루맙(AFP≥400)"],
        "모니터링": ["AFP 추적", "간기능(Child-Pugh)", "혈압(넥사바)", "수족증후군"],
        "한국_통계": {"발생순위": "남2위·여6위", "5년생존율": "전체 39.3%, 진행 10-15%", "출처": "국립암센터 2024"},
        "가이드라인": "대한간암학회 진료지침 2026",
        "생활습관": "B·C형 간염 치료 병행. 6개월마다 초음파+AFP 검사. 금주 필수.",
    },

    "대장암": {
        "ICD10": "C18-C20", "분류": ["결장암 60%", "직장암 40%"],
        "바이오마커": ["MSI/dMMR", "KRAS", "NRAS", "BRAF V600E", "HER2"],
        "1차_치료": {
            "1차":       ["FOLFOX(옥살리플라틴+5-FU+류코보린)", "FOLFIRI", "CAPOX"],
            "표적치료":  ["베바시주맙(아바스틴, VEGF)", "세툭시맙(EGFR, RAS 야생형)", "파니투무맙"],
            "면역치료":  ["키트루다(MSI-H/dMMR)"],
        },
        "2차_치료": ["론서프정(trifluridine/tipiracil)", "레고라페닙", "젤로다(카페시타빈)"],
        "모니터링": ["CEA 추적", "CBC(골수억제)", "말초신경병증(옥살리플라틴)", "수족증후군(젤로다)"],
        "한국_통계": {"발생순위": "전체 2위", "5년생존율": "전체 73.1%, IV기 18%", "출처": "국립암센터 2024"},
        "가이드라인": "대한대장항문학회 2026",
        "생활습관": "옥살리플라틴 투여 후 찬 것 접촉 절대 금지(한랭과민). 수족부 보습.",
    },

    "유방암": {
        "ICD10": "C50", "분류": ["HR+(ER/PR+) 70%", "HER2+ 15-20%", "삼중음성(TNBC) 10-15%"],
        "바이오마커": ["ER", "PR", "HER2", "Ki-67", "BRCA1/2", "PD-L1(TNBC)"],
        "1차_치료": {
            "HR+ HER2-":    ["호르몬요법(페마라·아로마신·타목시펜) ± CDK4/6억제제(입랜스·버제니오)"],
            "HER2+":        ["허셉틴(트라스투주맙) ± 퍼투주맙 + 화학요법", "캐싸일라(T-DM1)"],
            "TNBC":         ["화학요법", "키트루다(PD-L1+)", "올라파립(BRCA변이)"],
            "HR+ 전이성":   ["입랜스(팔보시클립)+페마라", "버제니오(아베마시클립)"],
        },
        "골전이_추가": ["엑스지바(데노수맙)", "졸레드론산"],
        "모니터링": ["심기능(허셉틴→LVEF)", "CBC(CDK4/6억제제→호중구감소)", "골밀도(호르몬요법)"],
        "한국_통계": {"발생순위": "여성 1위", "5년생존율": "전체 93.8%, IV기 38%", "출처": "국립암센터 2024"},
        "가이드라인": "대한유방암학회 2025",
        "생활습관": "정기 유방촬영술(40세부터 2년마다). 체중관리 및 규칙적 운동.",
    },

    "백혈병": {
        "ICD10": "C91-C95", "분류": ["CML(만성골수성백혈병)", "AML(급성골수성)", "CLL", "ALL"],
        "바이오마커": ["BCR-ABL(CML 필수)", "FLT3", "NPM1", "IDH1/2", "Philadelphia 염색체"],
        "1차_치료": {
            "CML":   ["글리벡(이마티닙 400mg)", "스프라이셀(다사티닙)", "타시그나(닐로티닙)"],
            "AML":   ["7+3 화학요법(사이타라빈+다우노루비신)", "이다루비신", "미도스타우린(FLT3+)"],
            "ALL":   ["하이퍼-CVAD", "VPAD 요법", "블린사이토(블리나투모맙, CD19+)"],
        },
        "모니터링": ["PCR 추적(BCR-ABL 수치)", "CBC 주간", "간기능", "혈당"],
        "한국_통계": {"발생순위": "혈액암 1위", "5년생존율": "CML >90%, AML 30-35%", "출처": "국립암센터 2024"},
        "가이드라인": "대한혈액학회 2025",
        "생활습관": "글리벡은 식사와 함께 복용(위장장애 감소). 자몽주스 금지.",
    },

    "소아백혈병": {
        "ICD10": "C91.0", "분류": ["ALL(급성림프모구백혈병, 소아의 80%)"],
        "바이오마커": ["BCR-ABL(Ph+)", "TEL-AML1", "ETV6-RUNX1", "MRD(미세잔존병)"],
        "1차_치료": {
            "표준위험군": ["관해유도(빈크리스틴+덱사메타손+L-아스파라기나제)", "공고요법", "유지요법(2-3년)"],
            "고위험·Ph+": ["글리벡(이마티닙)+화학요법 병용", "조혈모세포이식"],
        },
        "모니터링": ["MRD(치료반응)", "성장발달 지연", "신경독성", "이차암 장기 추적"],
        "한국_통계": {"5년생존율": "80-90% 이상", "출처": "국립암센터 소아암 통계 2024"},
        "가이드라인": "대한소아혈액종양학회 2025",
        "생활습관": "감염 예방(손위생). 학교 생활 정상화 지원. 백신 접종 스케줄 확인.",
    },

    "췌장암": {
        "ICD10": "C25", "분류": ["췌관선암(PDAC) 90%"],
        "바이오마커": ["CA19-9", "BRCA1/2", "KRAS G12D", "MSI"],
        "1차_치료": {
            "절제 가능":   ["수술(휘플수술) + 보조항암(젬시타빈+카페시타빈)"],
            "국소진행":    ["FOLFIRINOX(이리노테칸+옥살리플라틴+5-FU+류코보린)"],
            "전이성":      ["젬시타빈+나브-파클리탁셀", "FOLFIRINOX"],
            "BRCA 변이":   ["올라파립(유지요법)"],
        },
        "모니터링": ["CA19-9 추적", "혈당(췌장외분비기능)", "체중"],
        "한국_통계": {"발생순위": "8위", "5년생존율": "전체 15.2%, 절제 25%", "출처": "국립암센터 2024"},
        "가이드라인": "대한췌장담도학회 2025",
        "생활습관": "조기 발견 어려움 → 황달·복통·체중감소 즉시 검사. 금주·금연.",
    },

    "자궁경부암": {
        "ICD10": "C53", "분류": ["편평세포암(70%)", "선암(25%)"],
        "바이오마커": ["HPV(16·18형 고위험)", "p16", "PD-L1"],
        "1차_치료": {
            "조기":   ["수술(자궁절제술)", "방사선+시스플라틴 동시화학방사선"],
            "진행":   ["시스플라틴+파클리탁셀", "베바시주맙(아바스틴) 추가"],
            "면역":   ["키트루다(PD-L1 CPS≥1, 2차 이후)"],
        },
        "모니터링": ["HPV 추적", "신기능(시스플라틴)", "CBC"],
        "한국_통계": {"5년생존율": "전체 80%, 조기 95%", "출처": "국립암센터 2024"},
        "가이드라인": "대한부인종양학회 2025",
        "생활습관": "HPV 백신(9-26세 권장). 2년마다 팝스미어 검사.",
    },

    "액상 생검(MCED)": {
        "ICD10": "Z12(선별검사)", "분류": ["다중암조기검출(MCED)", "단일암 ctDNA 추적"],
        "바이오마커": ["ctDNA(순환종양DNA)", "CTC(순환종양세포)", "cfDNA 메틸화"],
        "적용_암종": ["대장암", "폐암", "유방암", "난소암", "간암 등 50+종"],
        "검사_플랫폼": ["Galleri(GRAIL)", "FoundationOne Liquid CDx", "코바스 ctDNA"],
        "현황": "FDA 승인 동반진단 기기 제한적. 임상 도입 단계(2025-2026 확대 예정).",
        "정확도": "특이도 >99%, 민감도 암종·병기별 상이(조기 40-70%, 진행 90%+)",
        "출처": "Cancer Discovery 2025, NEJM 2024",
        "한국_현황": "2026년 심평원 선별급여 논의 중. 일부 상급종합병원 시범 도입.",
    },

    # ── 심혈관 / 내분비 ──────────────────────────────────────────────────────
    "고혈압": {
        "ICD10": "I10", "분류": ["1도(130-139/80-89)", "2도(≥140/90)", "저항성 고혈압"],
        "바이오마커": ["혈압(ABPM)", "eGFR", "소변 미세알부민", "심전도"],
        "1차_치료": {
            "단독":   ["암로디핀(노바스크정)", "로살탄(코자)", "에날라프릴(레니텍)"],
            "복합":   ["암로디핀+ARB", "ARB+HCTZ(이뇨제)"],
            "저항성": ["스피로놀락톤 추가(알닥톤)"],
        },
        "목표혈압": "130/80 mmHg 미만(당뇨·만성신부전 동반 시 더 엄격)",
        "모니터링": ["혈압 자가 측정(2회/일)", "eGFR", "전해질(이뇨제)"],
        "한국_통계": {"유병률": "성인 28.3%(2023 국민건강영양조사)", "인지율": "73%"},
        "가이드라인": "대한고혈압학회 2022 개정판",
        "생활습관": "저염식(6g/일 이하). 규칙적 유산소 운동(주 150분). 절주·금연.",
    },

    "심부전": {
        "ICD10": "I50", "분류": ["HFrEF(LVEF<40%)", "HFmrEF(40-49%)", "HFpEF(≥50%)"],
        "바이오마커": ["NT-proBNP(진단·예후)", "LVEF(심초음파)", "eGFR", "혈청 전해질"],
        "1차_치료": {
            "HFrEF 4대_약제": ["ARNI(엔트레스토=sacubitril/valsartan)", "베타차단제(콩코르=bisoprolol)", "MRA(알닥톤=spironolactone)", "SGLT2억제제(포시가=dapagliflozin)"],
            "이뇨제":         ["라식스(furosemide)—증상 완화"],
            "심방세동_병용":  ["디고신(디고신엘릭시르)"],
        },
        "ACE억제제_주의": "엔트레스토 시작 36시간 전 ACE억제제 완전 중단 필수(혈관부종 위험)",
        "모니터링": ["NT-proBNP 추적", "체중 매일 측정(2kg/일 증가 시 이뇨제 증량)", "eGFR·전해질", "LVEF 6개월마다"],
        "한국_통계": {"유병률": "성인 1-2%", "5년생존율": "약 50%"},
        "가이드라인": "대한심부전학회 2022, ESC Heart Failure 2021",
        "생활습관": "수분 제한(1.5-2L/일). 염분 제한(2g/일). 독감·폐렴구균 예방접종 필수.",
    },

    "선천성 심질환": {
        "ICD10": "Q20-Q26", "분류": ["VSD(심실중격결손)", "ASD(심방중격결손)", "PDA", "활로4징"],
        "바이오마커": ["심초음파", "흉부 X선", "심전도", "산소포화도"],
        "1차_치료": {
            "약물":   ["디고신(강심)", "라식스(이뇨)", "알닥톤(칼륨보존)", "인도메타신(PDA 약물 폐쇄)"],
            "수술":   ["심장교정수술(병변 유형별)", "카테터 중재술"],
            "RSV예방": ["시나지스(palivizumab, 고위험 영아 월 1회 근주)"],
        },
        "모니터링": ["산소포화도", "체중 증가 속도", "수유량", "NT-proBNP"],
        "한국_통계": {"발생률": "신생아 1000명당 8-10명", "출처": "대한소아심장학회"},
        "가이드라인": "대한소아심장학회 2024",
        "생활습관": "호흡기 감염 예방 최우선(RSV 위험). 수유·영양 지원.",
    },

    "제1형 당뇨병": {
        "ICD10": "E10", "분류": ["자가면역성 췌장 β세포 파괴", "LADA(성인 잠복 자가면역 당뇨)"],
        "바이오마커": ["자가항체(GAD·IA-2·ZnT8)", "C-펩타이드(저·무 분비)", "HbA1c"],
        "1차_치료": {
            "인슐린_기저": ["란투스(glargine, 24시간 지속)", "트레시바(degludec)"],
            "인슐린_초속효성": ["휴말로그(lispro)", "노보로그(aspart)—식전 15분"],
            "기기치료": ["연속혈당측정기(CGM)", "인슐린펌프(CSII)"],
        },
        "목표": "HbA1c <7.0%(소아청소년 <7.5%)",
        "모니터링": ["HbA1c 3개월마다", "저혈당 일지", "신장·망막·신경 합병증 연1회"],
        "한국_통계": {"유병률": "소아·청소년 10만명당 3-5명"},
        "가이드라인": "대한당뇨병학회 2023",
        "생활습관": "탄수화물 계산법(Carb counting) 교육. 운동 전후 혈당 측정. 저혈당 응급키트 상시 휴대.",
    },

    "제2형 당뇨병": {
        "ICD10": "E11", "분류": ["인슐린 저항성 중심", "진행성 β세포 기능 저하"],
        "바이오마커": ["HbA1c", "공복혈당", "식후2시간혈당", "eGFR(합병증)"],
        "1차_치료": {
            "1단계": ["메트포르민(다이아벡스정·다이아벡스정) 500mg → 단계 증량"],
            "2단계_추가": ["SGLT2억제제(포시가·자디앙)", "DPP-4억제제(자누비아·트라젠타)", "GLP-1 수용체 작용제(빅토자·오젬픽)"],
            "인슐린": ["란투스(기저)", "휴말로그(식전)—경구약 실패 시"],
        },
        "목표": "HbA1c <6.5-7.0%(개별화)", "심혈관고위험군_우선": "SGLT2억제제·GLP-1 수용체 작용제",
        "모니터링": ["HbA1c 3개월마다", "공복혈당 자가측정", "eGFR·소변알부민 연1회", "발 검진"],
        "한국_통계": {"유병률": "성인 16.7%(2022)", "인지율": "70%"},
        "가이드라인": "대한당뇨병학회 2023",
        "생활습관": "저GI 식품. 식후 30분 산책. 메트포르민 CT 조영제 시 일시 중단.",
    },

    # ── 호흡기 / 소화기 / 면역 ────────────────────────────────────────────────
    "COPD": {
        "ICD10": "J44", "분류": ["GOLD 1-4 단계(FEV1 기준)", "잦은 악화형"],
        "바이오마커": ["FEV1/FVC <0.7(폐기능검사)", "혈중 호산구(type 2 염증)"],
        "1차_치료": {
            "GOLD 1-2_경증": ["SABA(벤톨린) 필요시", "LAMA(스피리바=tiotropium)"],
            "GOLD 3-4_중증": ["LAMA+LABA(울티브로·아노로)", "ICS+LABA(심비코트=budesonide/formoterol)"],
            "잦은악화_생물학적": ["듀필루맙(IL-4/13 억제제, 호산구 300↑)"],
        },
        "응급_악화": "전신 스테로이드(메틸프레드니솔론) + 광범위 항생제 + 산소",
        "모니터링": ["FEV1 연1회 이상", "SpO2", "흡입기 기법 확인", "백신(독감·폐렴구균)"],
        "한국_통계": {"유병률": "40세 이상 12.3%", "진단율": "2.3%(심각한 과소진단)", "출처": "질병관리청 2023"},
        "가이드라인": "GOLD 2025, 대한결핵및호흡기학회 2023",
        "생활습관": "금연(가장 효과적). 배가 부르지 않게 소식. 복식호흡·입술 오므리기 호흡 연습.",
    },

    "천식": {
        "ICD10": "J45", "분류": ["알레르기성(아토피)", "비알레르기성", "운동유발", "직업성"],
        "바이오마커": ["호산구(혈중·객담)", "FeNO(호기산화질소)", "총 IgE", "알레르겐 피부반응"],
        "1차_치료": {
            "경증 간헐성": ["SABA(벤톨린네뷸=salbutamol) 필요시"],
            "경증 지속성": ["저용량 ICS(플루티카손)", "류코트리엔길항제(싱귤레어=montelukast)"],
            "중증":        ["ICS+LABA(심비코트)", "항IgE(졸레어=omalizumab)", "항IL-5(파센라)"],
            "소아":        ["씨투스정(pranlukast)", "싱귤레어츄정(montelukast 5mg)"],
        },
        "응급": "벤톨린 반복 흡입 + 전신 스테로이드 + 산소",
        "모니터링": ["ACQ/ACT 설문(증상 조절)", "FEV1/PEF", "흡입기 기법", "알레르겐 회피"],
        "한국_통계": {"유병률": "성인 4.7%, 소아 9.6%"},
        "가이드라인": "GINA 2025, 대한결핵및호흡기학회",
        "생활습관": "ICS 흡입 후 반드시 입안 헹굼(구강 칸디다증 예방). 미세먼지 마스크.",
    },

    "RSV 감염": {
        "ICD10": "J21.0", "분류": ["영유아 모세기관지염", "소아 폐렴", "고령자 하기도 감염"],
        "바이오마커": ["RSV 항원 신속검사", "비인두 PCR"],
        "1차_치료": {
            "예방(고위험 영아)": ["시나지스(palivizumab) 15mg/kg 월 1회 근주(11월~3월)"],
            "예방(성인)":        ["아브리스보(RSV 백신, 60세 이상)", "mResvia(mRNA RSV 백신)"],
            "치료":              ["산소 공급(SpO2 유지)", "수액 공급", "필요시 고유량 비강 산소(HFNC)"],
        },
        "모니터링": ["SpO2", "호흡수", "수유량", "탈수 징후"],
        "한국_통계": {"입원율": "2세 미만 10명 중 1명", "출처": "질병관리청 2023"},
        "가이드라인": "대한소아감염학회 2024",
        "생활습관": "비말 감염 주의(손씻기). 형제자매·보호자 마스크. 11월-3월 집중 관리.",
    },

    "크론병": {
        "ICD10": "K50", "분류": ["소장형", "대장형", "소장대장형", "상부위장관형"],
        "바이오마커": ["CRP", "대변 칼프로텍틴", "ANCA·ASCA", "내시경·조직검사"],
        "1차_치료": {
            "경증":   ["메살라진(펜타사=mesalazine)", "부데소나이드(경구 스테로이드)"],
            "중등증": ["아자티오프린(이뮤란=azathioprine)", "메토트렉세이트"],
            "중증":   ["TNF-α 억제제(휴미라=adalimumab)", "베돌리주맙(킨텔레스=vedolizumab)", "우스테키누맙(스텔라라)"],
        },
        "이뮤란_주의": "알로퓨리놀과 병용 절대 금기(골수억제 4-5배 증가)",
        "모니터링": ["CRP·칼프로텍틴", "CBC(골수억제)", "간기능(이뮤란)", "결핵 잠복(TNF-α 전)"],
        "한국_통계": {"유병률": "10만명당 약 40명(급격히 증가)", "출처": "HIRA 2023"},
        "가이드라인": "대한장연구학회 IBD 지침 2024",
        "생활습관": "저잔사식이(급성기). 스트레스 관리. 흡연 금지(악화 위험).",
    },

    "위염": {
        "ICD10": "K29", "분류": ["급성 위염", "만성 위축성 위염", "H.pylori 연관 위염", "자가면역 위염"],
        "바이오마커": ["H.pylori 검사(요소호기검사·혈청·대변항원)", "내시경·조직검사"],
        "1차_치료": {
            "H.pylori 양성": ["제균 3제요법(PPI+아목시실린+클래리트로마이신 7-14일)"],
            "위산 억제":     ["PPI(오메프라졸·에소메프라졸)", "H2RA(스토가=lafutidine)"],
            "점막보호":      ["무코스타정(rebamipide)", "알마겔(알루미늄 제산제)"],
            "오심·구토":     ["맥페란정(metoclopramide)—5일 이내"],
        },
        "모니터링": ["제균 판정(6주 후 요소호기검사)", "위내시경(위축성→암 모니터링)"],
        "한국_통계": {"H.pylori_감염률": "성인 40-50%", "위암_전구병변": "위축성→장상피화생→이형성"},
        "가이드라인": "대한소화기학회 H.pylori 제균 지침 2022",
        "생활습관": "자극적 음식 제한. 소량 자주 식사. 음주·흡연·NSAID 최소화.",
    },

    # ── 신경 / 정신 / 희귀 ────────────────────────────────────────────────────
    "루게릭병": {
        "ICD10": "G12.2", "분류": ["근위축성측삭경화증(ALS)", "진행성 근위축증(PMA)"],
        "바이오마커": ["신경전도검사(EMG)", "SOD1·C9orf72 유전자 변이", "혈청 신경필라멘트"],
        "1차_치료": {
            "약물":   ["리루텍정(riluzole 50mg 1일2회)—생존 연장", "에다라본(라디컷 정맥주사)", "토퍼센(안티센스, SOD1 변이)"],
            "보조":   ["호흡보조(BiPAP)", "위루술(경피내시경위루술, PEG)", "코엔자임Q10"],
        },
        "모니터링": ["폐기능(FVC) 3-6개월마다", "간기능(리루텍)", "영양·연하기능", "우울증 선별"],
        "한국_통계": {"유병률": "10만명당 3-5명", "진단 후 생존기간": "평균 3-5년"},
        "가이드라인": "대한신경과학회·ALS협회 2024",
        "생활습관": "다학제 팀(신경과·재활의학·영양·언어치료·심리). 고열량 식이.",
    },

    "중증근무력증": {
        "ICD10": "G70.0", "분류": ["전신형", "안구형", "흉선종 연관"],
        "바이오마커": ["항AChR 항체(85%)", "항MuSK 항체(항AChR 음성의 40%)", "흉선 CT"],
        "1차_치료": {
            "증상완화":     ["메스티논정(pyridostigmine 60mg 1일3-4회)"],
            "면역억제":     ["프레드니솔론(스테로이드)", "아자티오프린(이뮤란)", "사이클로스포린"],
            "중증·위기":   ["IVIG(면역글로불린 정맥주사)", "혈장교환(PLEX)"],
            "수술":        ["흉선절제술(항AChR 양성 60세 미만 전신형)"],
            "보체억제":    ["에쿨리주맙(솔리리스)—항AChR 양성 중증"],
        },
        "근무력성_위기_유발약": "일부 항생제(플루오로퀴놀론·아미노글리코사이드)·β차단제·마그네슘—절대 주의",
        "모니터링": ["QMG 점수(임상 중증도)", "호흡기능(FVC)", "흉선 잔존 여부"],
        "가이드라인": "대한신경과학회 2023",
        "생활습관": "감염 예방(증상 악화 유발). 과로 회피. 복용 금기 약물 목록 항상 휴대.",
    },

    "파킨슨병": {
        "ICD10": "G20", "분류": ["원발성(특발성) 파킨슨병", "파킨슨증후군"],
        "바이오마커": ["DAT 스캔(도파민 운반체 SPECT)", "후각 이상·REM 수면장애(초기 징후)"],
        "1차_치료": {
            "도파민 보충": ["마도파(levodopa/benserazide)", "스타레보(levodopa+carbidopa+entacapone)"],
            "도파민 효능제": ["리큅(ropinirole)", "미라펙스(pramipexole)"],
            "MAO-B 억제제": ["아질렉트(rasagiline)", "셀레질린"],
            "COMT 억제제":  ["콤탄(entacapone)—Wearing-off 감소"],
            "심한 진전":    ["DBS(뇌심부자극술)"],
        },
        "Wearing-off_관리": "레보도파 분할 투여 or 엔타카폰 추가 or 도파민 효능제 병용",
        "모니터링": ["UPDRS 점수", "기립성 저혈압(혈압)", "충동조절장애(도파민 효능제)", "환각"],
        "한국_통계": {"유병률": "65세 이상 1%, 80세 이상 4%"},
        "가이드라인": "대한파킨슨병및이상운동질환학회 2024",
        "생활습관": "레보도파와 고단백 식사 분리(흡수 방해). 낙상 예방. 수영·태극권 권장.",
    },

    "소아 뇌전증": {
        "ICD10": "G40", "분류": ["부분발작(초점성)", "전신발작(강직간대·결신)", "영아연축"],
        "바이오마커": ["뇌파(EEG)—발작파 확인", "MRI(구조적 원인)", "유전자 패널(SCN1A 등)"],
        "1차_치료": {
            "부분발작":   ["케프라시럽(levetiracetam)", "옥스카바제핀(트리렙탈)"],
            "전신발작":   ["데파코트스프링클(divalproex sodium)—광범위", "에토석시미드(결신 발작)"],
            "보조요법":   ["엑세그란(zonisamide)", "라믹탈(lamotrigine)"],
            "영아연축":   ["ACTH(부신피질호르몬)", "비가바트린"],
            "케톤식이":   ["약물저항성 뇌전증 대안"],
        },
        "발작_응급": "디아제팜 직장·미다졸람 비강—5분 이상 발작 시 즉시 사용",
        "모니터링": ["발작 일지(빈도·지속시간)", "EEG", "인지발달", "혈중 약물농도"],
        "한국_통계": {"유병률": "소아 1000명당 4-6명"},
        "가이드라인": "대한소아신경학회 2024",
        "생활습관": "발작 일지 앱 활용. 익수 사고 예방(목욕 혼자 금지). 학교 담당 교사 공지.",
    },

    "우울증": {
        "ICD10": "F32-F33", "분류": ["주요우울장애(MDD)", "지속성우울장애(기분저하증)", "산후 우울증"],
        "바이오마커": ["PHQ-9 설문(선별·중증도)", "갑상선기능(감별)", "비타민D(연관성)"],
        "1차_치료": {
            "1단계": ["SSRI(렉사프로=escitalopram 10-20mg, 졸로푸트=sertraline, 프로작=fluoxetine)"],
            "2단계": ["SNRI(사이발타=duloxetine, 이펙사=venlafaxine)"],
            "보조":  ["아빌리파이(aripiprazole) 소량 추가", "미르타자핀(수면 장애 동반 시)"],
            "심리치료": ["인지행동치료(CBT)—약물과 병행 권장"],
        },
        "중단_금지": "갑작스런 중단 시 불연속 증후군(현기증·전기충격감). 서서히 감량 필수",
        "모니터링": ["PHQ-9 4-8주마다", "자살 충동 정기 평가", "성기능 장애(SSRI 부작용)", "청소년 행동 관찰"],
        "가이드라인": "대한정신건강의학과학회 2023",
        "생활습관": "규칙적 햇볕 노출. 유산소 운동(주 3-5회). 수면 리듬 유지.",
    },

    "ADHD": {
        "ICD10": "F90", "분류": ["주의력결핍 우세형", "과잉행동-충동 우세형", "복합형"],
        "바이오마커": ["Conners 평가척도", "신경심리검사(CPT)", "임상 인터뷰"],
        "1차_치료": {
            "자극제":    ["콘서타(methylphenidate ER 18-54mg 1일1회)", "메디키넷(methylphenidate IR)", "비반스(lisdexamfetamine)"],
            "비자극제":  ["아토목세틴(스트라테라)—틱 동반, 남용 위험 시", "클로니딘ER"],
            "행동치료":  ["부모 훈련", "인지행동치료", "사회기술훈련"],
        },
        "모니터링": ["식욕·체중·신장(성장)", "심박수·혈압", "수면", "틱 발생"],
        "가이드라인": "대한소아청소년정신의학회 2023",
        "생활습관": "규칙적 수면·기상. 디지털 사용 규칙 설정. 아침 복용(불면 예방).",
    },

    # ── 기타 ──────────────────────────────────────────────────────────────────
    "통풍": {
        "ICD10": "M10", "분류": ["급성 통풍 발작", "만성 결절성 통풍"],
        "바이오마커": ["혈청 요산(≥6.8mg/dL 진단)", "관절액 요산염 결정(확진)", "eGFR"],
        "1차_치료": {
            "급성발작":   ["콜히친(0.5mg 1일2-3회, 발작 48시간 이내)", "NSAIDs(나프록센·인도메타신)", "스테로이드"],
            "요산강하":   ["알로퓨리놀(100→300mg, 서서히 증량)", "페부소스탯(아데뉴릭)"],
        },
        "목표": "혈청 요산 <6mg/dL (결절 있으면 <5mg/dL)",
        "이뮤란_병용_금기": "알로퓨리놀 + 아자티오프린 병용 시 독성 4-5배 증가—절대 금기",
        "모니터링": ["요산 수치 3-6개월마다", "eGFR(요산 신장 배설)", "간기능(페부소스탯)"],
        "가이드라인": "대한류마티스학회 2022",
        "생활습관": "퓨린 많은 음식 제한(내장·등푸른생선·맥주). 수분 충분(2L/일). 급격한 단식 금지.",
    },

    "두통/근육통/감기": {
        "ICD10": "G43/M79/J00", "분류": ["긴장형 두통", "편두통", "군발두통", "근육통", "급성 상기도 감염"],
        "1차_치료": {
            "일반 두통·발열": ["타이레놀정(acetaminophen 500mg 1-2정 1일 4회 이내)"],
            "염증성 두통·근육통": ["탁센연질캡슐(naproxen 250-500mg)", "이부프로펜"],
            "복합 두통":     ["게보린정(acetaminophen+isopropylantipyrine+caffeine)"],
            "편두통":        ["트립탄계(이미그란·조믹)", "예방: 베타차단제·토피라마트"],
            "감기":          ["모드콜S(종합감기약)", "슈다페드(코막힘)", "코대원(기침·가래)"],
        },
        "주의": "타이레놀 1일 최대 4g 초과 금지(간독성). 음주 후 아세트아미노펜 금지. 게보린 15세 미만 금기.",
        "모니터링": ["두통 빈도 일지", "NSAIDs 장기 복용 시 위장관·신기능"],
        "생활습관": "충분한 수면·수분. 카페인 과다 섭취 주의(반동성 두통). 규칙적 생활 리듬.",
    },
}

# cancer_protocols_db 의 50개 암종을 DISEASE_PROTOCOLS에 병합
if HAS_CANCER_DB:
    DISEASE_PROTOCOLS.update(_CANCER_PROTOCOLS_EXT)


# ════════════════════════════════════════════════════════════════════════════════
# 3. 식약처 공공 API 연동
#    - 식품의약품안전처 의약품안전나라 (nedrug.mfds.go.kr)
#    - 공공데이터포털 API (data.go.kr) — 서비스키 필요
# ════════════════════════════════════════════════════════════════════════════════

MFDS_EASY_API = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
MFDS_DRUG_API = "http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService04/getDrugPrdtPrmsnDtlInq04"

def search_mfds_drug(drug_name: str, api_key: str = "") -> Dict:
    """
    식약처 의약품안전나라 공공 API 조회 (easyDrugInfo).
    api_key: 공공데이터포털에서 발급한 서비스키 (없으면 로컬 DB 폴백)
    """
    if not HAS_REQUESTS or not api_key:
        return {"status": "로컬DB 사용", "drug_name": drug_name,
                "note": "공공데이터포털 API 키 미설정. 내부 DB 사용 중."}
    try:
        params = {
            "serviceKey": api_key,
            "itemName": drug_name,
            "type": "json",
            "numOfRows": 5,
        }
        resp = requests.get(MFDS_EASY_API, params=params, timeout=5)
        data = resp.json()
        items = data.get("body", {}).get("items", [])
        if items:
            item = items[0]
            return {
                "status": "API 성공",
                "약품명": item.get("itemName"),
                "성분": item.get("material"),
                "효능": item.get("efcyQesitm"),
                "용법": item.get("useMethodQesitm"),
                "주의사항": item.get("atpnQesitm"),
                "부작용": item.get("seQesitm"),
                "보관법": item.get("depositMethodQesitm"),
                "출처": "식약처 의약품안전나라",
            }
        return {"status": "결과 없음", "drug_name": drug_name}
    except Exception as e:
        return {"status": "API 오류", "error": str(e), "drug_name": drug_name}


# ════════════════════════════════════════════════════════════════════════════════
# 4. 실제 환자 DB 기반 차트 데이터 생성
# ════════════════════════════════════════════════════════════════════════════════

ONCOLOGY_KEYWORDS = ["암", "백혈병", "흑색종", "육종", "GIST", "종양", "림프종", "골수종"]
MONTHS_ORDER = ["Jan", "Feb", "Mar", "Apr", "May"]
MONTH_NUM_TO_NAME = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May",
                     "06":"Jun","07":"Jul","08":"Aug","09":"Sep",
                     "10":"Oct","11":"Nov","12":"Dec"}

# 병원-axis 표시용 (main_app.py chart_hospital 과 동기화)
HOSPITAL_AXIS = ["서울이대병원","서울대병원","세브란스병원","서울아산병원","삼성서울병원","국립암센터"]


def _load_rx_from_db(db_path: str) -> List[Dict]:
    """pharma_v20.db에서 처방 전체 로드."""
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT patient_id, medication_name, cancer_type, start_date, efficacy_rate FROM rx")
        rows = c.fetchall()
        conn.close()
        return [{"patient_id": r[0], "medication_name": r[1],
                 "cancer_type": r[2], "start_date": r[3], "efficacy_rate": r[4]} for r in rows]
    except Exception:
        return []


def _load_patients_from_db(db_path: str) -> Dict:
    """pharma_v20.db에서 환자 정보 로드."""
    if not os.path.exists(db_path):
        return {}
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT patient_id, hospital FROM patients")
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def get_hospital_chart_data(db_path: str = "pharma_v20.db",
                            fallback_rx: list = None,
                            fallback_patients: dict = None) -> Dict:
    """
    실제 처방 DB 기반 병원별·월별 활성 처방 수 집계.
    Returns: {"hospitals": [...], "months": [...], "matrix": {hosp: {month: count}}}
    """
    rx_list = _load_rx_from_db(db_path) or (fallback_rx or [])
    pat_map = _load_patients_from_db(db_path) or (fallback_patients or {})

    # 병원별·월별 카운트
    matrix: Dict[str, Dict[str, int]] = {h: {m: 0 for m in MONTHS_ORDER} for h in HOSPITAL_AXIS}

    for rx in rx_list:
        pid = rx.get("patient_id", "")
        hospital = pat_map.get(pid, "")
        start = rx.get("start_date", "")
        if not hospital or not start or len(start) < 7:
            continue
        month_num = start[5:7]
        month_name = MONTH_NUM_TO_NAME.get(month_num)
        if not month_name or month_name not in MONTHS_ORDER:
            continue
        # 병원명 정규화 (짧은 표현이 축 라벨과 다를 수 있어 부분 매칭)
        matched_hosp = None
        for h in HOSPITAL_AXIS:
            if h in hospital or hospital in h:
                matched_hosp = h
                break
        if matched_hosp:
            matrix[matched_hosp][month_name] += 1

    return {"hospitals": HOSPITAL_AXIS, "months": MONTHS_ORDER, "matrix": matrix}


def get_trend_chart_data(db_path: str = "pharma_v20.db",
                         fallback_rx: list = None) -> Dict:
    """
    실제 처방 DB 기반 항암(Oncology) vs 만성질환(Chronic) 월별 평균 효능률 집계.
    Returns: {"months": [...], "oncology": [...], "chronic": [...]}
    """
    rx_list = _load_rx_from_db(db_path) or (fallback_rx or [])

    onco_by_month: Dict[str, List[float]] = defaultdict(list)
    chron_by_month: Dict[str, List[float]] = defaultdict(list)

    for rx in rx_list:
        cancer_type = rx.get("cancer_type", "")
        start = rx.get("start_date", "")
        efficacy = rx.get("efficacy_rate")
        if not start or len(start) < 7 or efficacy is None:
            continue
        month_num = start[5:7]
        month_name = MONTH_NUM_TO_NAME.get(month_num)
        if not month_name or month_name not in MONTHS_ORDER:
            continue
        is_onco = any(kw in cancer_type for kw in ONCOLOGY_KEYWORDS)
        if is_onco:
            onco_by_month[month_name].append(float(efficacy))
        else:
            chron_by_month[month_name].append(float(efficacy))

    def avg_or_none(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    onco_vals = [avg_or_none(onco_by_month[m]) for m in MONTHS_ORDER]
    chron_vals = [avg_or_none(chron_by_month[m]) for m in MONTHS_ORDER]

    return {"months": MONTHS_ORDER, "oncology": onco_vals, "chronic": chron_vals}


# ════════════════════════════════════════════════════════════════════════════════
# 5. 이미지 기능 — 약품 이미지 조회 / 처방전·약봉지 분석
# ════════════════════════════════════════════════════════════════════════════════

def get_drug_image_path(drug_name: str) -> Optional[str]:
    """약품명으로 로컬 이미지 경로 반환. 없으면 None."""
    # 정확한 이름 먼저
    path = DRUG_IMAGE_MAP.get(drug_name)
    if path and os.path.exists(path):
        return path
    # 부분 이름 매칭
    for name, p in DRUG_IMAGE_MAP.items():
        if drug_name in name or name in drug_name:
            if os.path.exists(p):
                return p
    return None


def get_all_drug_images() -> Dict[str, str]:
    """존재하는 약품 이미지 전체 반환."""
    return {name: path for name, path in DRUG_IMAGE_MAP.items() if os.path.exists(path)}


def get_prescription_images() -> List[str]:
    """존재하는 처방전 이미지 목록 반환."""
    return [p for p in PRESCRIPTION_IMAGES if os.path.exists(p)]


def get_pill_bag_images() -> List[str]:
    """존재하는 약봉지 이미지 목록 반환."""
    return [p for p in PILL_BAG_IMAGES if os.path.exists(p)]


def _image_to_base64(image_path: str) -> Tuple[str, str]:
    """이미지 파일을 base64로 인코딩. (data, media_type) 반환."""
    ext = Path(image_path).suffix.lower()
    media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                  "png": "image/png", "gif": "image/gif"}.get(ext.lstrip("."), "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def analyze_image_with_claude(image_path: str, prompt: str,
                               api_key: str = "") -> str:
    """
    Claude API (claude-sonnet-4-6 vision)으로 이미지 분석.
    api_key: ANTHROPIC_API_KEY (환경변수에서도 자동 로드)
    """
    if not HAS_ANTHROPIC:
        return "[Claude SDK 미설치] pip install anthropic 후 사용 가능합니다."
    if not os.path.exists(image_path):
        return f"[오류] 이미지 파일 없음: {image_path}"
    try:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
        img_data, media_type = _image_to_base64(image_path)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                                                  "media_type": media_type,
                                                  "data": img_data}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return message.content[0].text
    except Exception as e:
        return f"[Claude API 오류] {e}"


def identify_drug_from_image(image_path: str, api_key: str = "") -> Dict:
    """
    약품 낱알/포장 이미지에서 약품 정보 식별.
    1) 로컬 DRUG_IMAGE_MAP에서 파일명 매칭 (빠른 경로)
    2) Claude vision으로 외형 분석
    """
    filename = Path(image_path).name.lower()

    # 로컬 매핑 먼저 시도
    for drug_name, mapped_path in DRUG_IMAGE_MAP.items():
        if Path(mapped_path).name.lower() == filename:
            appearance = DRUG_APPEARANCE_DB.get(drug_name, {})
            return {
                "drug_name": drug_name,
                "match_method": "로컬 이미지 매핑",
                "appearance": appearance,
                "image_path": mapped_path,
            }

    # Claude vision 분석
    prompt = (
        "당신은 30년 경력 약사입니다. 이 이미지의 약품을 분석하여 아래 JSON 형식으로만 답하세요:\n"
        '{"약품명": "", "성분추정": "", "색상": "", "모양": "", "각인": "", "제형": "", "특이사항": ""}'
    )
    result_text = analyze_image_with_claude(image_path, prompt, api_key)
    try:
        import json as _json
        cleaned = result_text.strip().replace("```json", "").replace("```", "")
        parsed = _json.loads(cleaned)
        parsed["match_method"] = "Claude vision 분석"
        return parsed
    except Exception:
        return {"match_method": "Claude vision 분석", "raw_result": result_text}


def analyze_prescription(image_path: str, api_key: str = "") -> Dict:
    """
    처방전 이미지에서 처방 정보 추출 (OCR + Claude vision).
    """
    # pytesseract OCR 시도
    ocr_text = ""
    try:
        from PIL import Image as PILImage
        import pytesseract
        img = PILImage.open(image_path)
        ocr_text = pytesseract.image_to_string(img, lang="kor+eng").strip()
    except Exception:
        pass

    # Claude vision 분석
    prompt = (
        "당신은 의료 처방전 분석 전문가입니다. 이 처방전 이미지에서 정보를 추출하여 JSON으로 반환하세요:\n"
        '{"환자정보": {"나이": "", "성별": ""}, '
        '"처방약물": [{"약품명": "", "용량": "", "용법": "", "일수": ""}], '
        '"진단명": "", "처방의": "", "병원명": "", "처방일": ""}\n'
        "개인식별정보(이름·주민번호)는 마스킹 처리하세요."
    )
    claude_result = analyze_image_with_claude(image_path, prompt, api_key)

    import json as _json
    parsed = {}
    try:
        cleaned = claude_result.strip().replace("```json", "").replace("```", "")
        parsed = _json.loads(cleaned)
    except Exception:
        parsed = {"raw_result": claude_result}

    return {
        "ocr_text": ocr_text,
        "structured": parsed,
        "image_path": image_path,
    }


def analyze_pill_bag(image_path: str, api_key: str = "") -> Dict:
    """
    약봉지 이미지에서 복약 정보 추출.
    """
    ocr_text = ""
    try:
        from PIL import Image as PILImage
        import pytesseract
        img = PILImage.open(image_path)
        ocr_text = pytesseract.image_to_string(img, lang="kor+eng").strip()
    except Exception:
        pass

    prompt = (
        "당신은 약봉지(분포약) 분석 전문가입니다. 이 약봉지 이미지에서 정보를 추출하여 JSON으로 반환하세요:\n"
        '{"약품명_목록": [], "복용시간": "", "복용횟수": "", "복용일수": "", '
        '"주의사항": "", "보관법": "", "병원명": ""}\n'
        "환자 이름 등 개인정보는 마스킹하세요."
    )
    claude_result = analyze_image_with_claude(image_path, prompt, api_key)

    import json as _json
    parsed = {}
    try:
        cleaned = claude_result.strip().replace("```json", "").replace("```", "")
        parsed = _json.loads(cleaned)
    except Exception:
        parsed = {"raw_result": claude_result}

    return {
        "ocr_text": ocr_text,
        "structured": parsed,
        "image_path": image_path,
    }


# ════════════════════════════════════════════════════════════════════════════════
# 6. 수집된 데이터 통합 (pharma_data_collector 결과물)
# ════════════════════════════════════════════════════════════════════════════════

_COLLECTED_MASTER: Optional[Dict] = None  # 캐시

def load_collected_drug_master(base_dir: str = ".") -> Dict[str, Dict]:
    """
    pharma_data_collector.py 가 생성한 drug_master.json 을 로드.
    반환: {한국약품명: {korean_name, english_name, diseases, fda_label, faers_top_ae, ...}}
    """
    global _COLLECTED_MASTER
    if _COLLECTED_MASTER is not None:
        return _COLLECTED_MASTER

    path = os.path.join(base_dir, "data/collected/processed/drug_master.json")
    if not os.path.exists(path):
        _COLLECTED_MASTER = {}
        return _COLLECTED_MASTER
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        _COLLECTED_MASTER = raw.get("drugs", {})
    except Exception as e:
        print(f"[MKE] drug_master.json 로드 실패: {e}")
        _COLLECTED_MASTER = {}
    return _COLLECTED_MASTER


def get_fda_info(drug_kr: str) -> Dict:
    """
    한국 약품명으로 OpenFDA 수집 데이터 반환.
    반환 필드: generic_name_en, brand_names, indications, warnings,
               adverse_reactions, dosage, manufacturer, route,
               faers_top_reactions, total_reports, data_sources
    """
    master = load_collected_drug_master()
    entry = master.get(drug_kr, {})
    if not entry:
        return {}

    fda_label = entry.get("fda_label", {})
    faers     = entry.get("faers_top_ae", {})
    sources   = entry.get("data_sources", [])

    top_ae = faers.get("top_adverse_events", [])
    total  = faers.get("total_reports", 0) or sum(ae.get("count", 0) for ae in top_ae)

    mfr = fda_label.get("manufacturer", "")
    if isinstance(mfr, list):
        mfr = ", ".join(mfr[:2])

    return {
        "generic_name_en":    fda_label.get("generic_name_en", ""),
        "brand_names":        fda_label.get("brand_names", ""),
        "manufacturer":       mfr,
        "route":              fda_label.get("route", ""),
        "indications":        fda_label.get("indications", ""),
        "dosage":             fda_label.get("dosage", ""),
        "warnings":           fda_label.get("warnings", ""),
        "adverse_reactions":  fda_label.get("adverse_reactions", ""),
        "faers_top_reactions": top_ae,
        "total_reports":      total,
        "data_sources":       sources,
    }


def get_fda_adverse_events(drug_kr: str, top_n: int = 10) -> List[Dict]:
    """FAERS 상위 부작용 반환. [{term, count}, ...]"""
    info = get_fda_info(drug_kr)
    events = info.get("faers_top_reactions", [])
    return events[:top_n]


def get_fda_indications(drug_kr: str) -> str:
    """FDA 승인 적응증 텍스트 반환."""
    return get_fda_info(drug_kr).get("indications", "")


def get_collected_drug_names() -> List[str]:
    """수집된 약품명 목록 반환."""
    return list(load_collected_drug_master().keys())


# ════════════════════════════════════════════════════════════════════════════════
# 6b. 로컬 JSON 데이터 통합 로더
# ════════════════════════════════════════════════════════════════════════════════

def load_all_local_data(base_dir: str = ".") -> Dict:
    """
    프로젝트 내 모든 JSON 데이터 파일을 읽어 통합 반환.
    """
    result = {}
    json_files = {
        "knowledge_base":      os.path.join(base_dir, "knowledge_base.json"),
        "medication_info":     os.path.join(base_dir, "data/raw/texts/medication_info_aihub.json"),
        "med_dataset_master":  os.path.join(base_dir, "data/raw/texts/med_dataset_master.json"),
    }
    for key, path in json_files.items():
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    result[key] = json.load(f)
            except Exception as e:
                result[key] = {"error": str(e)}
        else:
            result[key] = {"error": "파일 없음"}

    result["drug_images"] = get_all_drug_images()
    result["prescription_images"] = get_prescription_images()
    result["pill_bag_images"] = get_pill_bag_images()
    return result


# ════════════════════════════════════════════════════════════════════════════════
# 7. 질환 검색 / 약물-질환 연결
# ════════════════════════════════════════════════════════════════════════════════

def get_disease_protocol(disease_name: str) -> Optional[Dict]:
    """질환명으로 치료 프로토콜 조회 (정확 + 부분 매칭)."""
    if disease_name in DISEASE_PROTOCOLS:
        return DISEASE_PROTOCOLS[disease_name]
    for name, protocol in DISEASE_PROTOCOLS.items():
        if disease_name in name or name in disease_name:
            return protocol
    return None


def get_diseases_for_drug(drug_name: str) -> List[str]:
    """약물명으로 적응 질환 목록 반환."""
    matched = []
    for disease, protocol in DISEASE_PROTOCOLS.items():
        for category, drugs in protocol.items():
            if isinstance(drugs, list) and any(drug_name in d for d in drugs):
                matched.append(disease)
            elif isinstance(drugs, dict):
                for sub_drugs in drugs.values():
                    if isinstance(sub_drugs, list) and any(drug_name in d for d in sub_drugs):
                        matched.append(disease)
                        break
    return list(set(matched))


def search_knowledge(query: str) -> List[Dict]:
    """질환명·약품명·바이오마커·성분으로 통합 검색."""
    q = query.strip().lower()
    results = []

    # 질환 프로토콜 검색
    for disease, protocol in DISEASE_PROTOCOLS.items():
        score = 0
        if q in disease.lower():
            score = 10
        elif any(q in str(v).lower() for v in protocol.values()):
            score = 5
        if score:
            results.append({"type": "질환", "name": disease,
                             "data": protocol, "score": score})

    # 약품 이미지 검색
    for drug_name, img_path in DRUG_IMAGE_MAP.items():
        if q in drug_name.lower():
            appearance = DRUG_APPEARANCE_DB.get(drug_name, {})
            results.append({"type": "약품이미지", "name": drug_name,
                             "data": {"image": img_path, "appearance": appearance},
                             "score": 8})

    # nutrition_diet_db 식단 검색
    if HAS_NUTRITION_DB:
        for diet_result in search_diet(query):
            already = any(r["name"] == diet_result["name"] for r in results)
            if not already:
                results.append({
                    "type": "식단가이드",
                    "name": diet_result["name"],
                    "data": diet_result["data"],
                    "score": 7,
                })

    # cancer_protocols_db 직접 검색 (50개 암종)
    if HAS_CANCER_DB:
        for cancer_result in search_cancer_protocols(query):
            already = any(r["name"] == cancer_result["name"] for r in results)
            if not already:
                results.append({
                    "type": "암프로토콜",
                    "name": cancer_result["name"],
                    "data": cancer_result["data"],
                    "score": cancer_result["score"],
                })

    # 수집된 OpenFDA / FAERS 데이터 검색
    for drug_kr, entry in load_collected_drug_master().items():
        drug_kr_lower = drug_kr.lower()
        en_name = entry.get("english_name", "").lower()
        fda_label = entry.get("fda_label", {})
        indications = str(fda_label.get("indications", "")).lower()
        score = 0
        if q in drug_kr_lower or q in en_name:
            score = 9
        elif q in indications:
            score = 4
        if score:
            already = any(r["name"] == drug_kr for r in results)
            if not already:
                results.append({
                    "type": "FDA데이터",
                    "name": drug_kr,
                    "data": {
                        "english_name": entry.get("english_name", ""),
                        "indications":  fda_label.get("indications", "")[:300],
                        "source":       "OpenFDA (CC0 Public Domain)",
                    },
                    "score": score,
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:8]


# ════════════════════════════════════════════════════════════════════════════════
# 8. 편의 함수 — Streamlit 용 이미지 렌더링
# ════════════════════════════════════════════════════════════════════════════════

def render_drug_image_html(drug_name: str, width: int = 200) -> str:
    """약품 이미지를 base64 인라인 HTML로 반환 (Streamlit st.markdown 용)."""
    path = get_drug_image_path(drug_name)
    if not path:
        return f"<div style='color:#aaa;font-size:0.8rem;'>이미지 없음: {drug_name}</div>"
    try:
        data, media_type = _image_to_base64(path)
        appearance = DRUG_APPEARANCE_DB.get(drug_name, {})
        desc = " | ".join(f"{k}: {v}" for k, v in appearance.items())
        return (
            f"<div style='text-align:center;'>"
            f"<img src='data:{media_type};base64,{data}' width='{width}' "
            f"style='border-radius:8px;border:1px solid #444;'/>"
            f"<div style='font-size:0.75rem;color:#88ccff;margin-top:4px;'>"
            f"{drug_name}<br><span style='color:#aaa'>{desc}</span></div>"
            f"</div>"
        )
    except Exception as e:
        return f"<div style='color:red;'>이미지 로드 오류: {e}</div>"


# ════════════════════════════════════════════════════════════════════════════════
# 9. 모듈 자체 실행 테스트
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Medical Knowledge Engine -- 자체 테스트")
    print("=" * 60)

    # 차트 데이터
    hosp = get_hospital_chart_data()
    print(f"\n[병원 차트] {len(hosp['hospitals'])}개 병원, {len(hosp['months'])}개 월")
    for h, months_data in hosp["matrix"].items():
        total = sum(months_data.values())
        if total:
            print(f"  {h}: {dict(months_data)}")

    trend = get_trend_chart_data()
    print(f"\n[트렌드 차트]")
    print(f"  Oncology : {trend['oncology']}")
    print(f"  Chronic  : {trend['chronic']}")

    # 질환 프로토콜
    protocol = get_disease_protocol("폐암")
    if protocol:
        print(f"\n[폐암 프로토콜] 바이오마커: {protocol.get('바이오마커')}")

    # 이미지 목록
    drug_imgs = get_all_drug_images()
    print(f"\n[약품 이미지] {len(drug_imgs)}개 확인됨")
    for name, path in drug_imgs.items():
        print(f"  {name}: {path}")

    rx_imgs = get_prescription_images()
    bag_imgs = get_pill_bag_images()
    print(f"[처방전 이미지] {len(rx_imgs)}개 | [약봉지 이미지] {len(bag_imgs)}개")

    # 로컬 데이터
    local = load_all_local_data()
    for k, v in local.items():
        if isinstance(v, list):
            print(f"[{k}] {len(v)}건")
        elif isinstance(v, dict) and "error" not in v:
            print(f"[{k}] 로드 성공")
        else:
            print(f"[{k}] {v}")
