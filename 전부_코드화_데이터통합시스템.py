#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-HYBRID v125.0 — AntiGravity Unified Final Edition
====================================================
전부_코드화_데이터통합시스템 + unified_execution_antigravity 완전 통합

• 시스템 무결성 자동 검증 (File / Env / Dataset)
• 환자 34인 처방전 실물 이미지 + 약품 이미지 동기화
• AntiGravity AI 데이터셋 (학습 21 / 검증 6 / 테스트 4) 내장
• 모바일 앱과 동일한 레이아웃: 처방전 이미지 ↔ 약품 카드
"""

import os, base64, re, random, sys, time, subprocess
from datetime import datetime
from pathlib import Path
import streamlit as st

# ── 1. 시스템 무결성 검증 (unified_execution_antigravity logic) ────────────────
def perform_system_integrity_check():
    checks = {"files": False, "env": False, "dataset": False}
    
    # 1.1 필수 파일 체크
    essential_files = [
        "전부_코드화_데이터통합시스템.py",
        "gemini_ai_engine.py",
        "drug_info_complete_db.py",
        "disease_knowledge_db.py",
        "real_patient_data.json",
        "prescription_index.json",
        "pharma_ai_antigravity.py",
    ]
    missing = [f for f in essential_files if not Path(f).exists()]
    checks["files"] = (len(missing) == 0)
    
    # 1.2 환경 체크
    try:
        import google.generativeai
        checks["env"] = True
    except ImportError:
        checks["env"] = False
        
    return checks, missing

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PHARMA-HYBRID v125.0 Unified",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 시스템 체크 실행
_SYS_CHECKS, _MISSING_FILES = perform_system_integrity_check()

PILL_DIR         = r"C:\Users\rcs91\github\med_project\pill_images"
PRESCRIPTION_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"
for d in [PILL_DIR, PRESCRIPTION_DIR]:
    os.makedirs(d, exist_ok=True)

# ── AntiGravity 데이터셋 로드 ─────────────────────────────────────────────────
_AG_LOADED = False
_AG_TRAIN, _AG_VAL, _AG_TEST, _AG_KB = [], [], [], {}
try:
    from pharma_ai_antigravity import (
        TRAINING_SET as _AG_TRAIN,
        VALIDATION_SET as _AG_VAL,
        TEST_SET as _AG_TEST,
        DRUG_KB as _AG_KB,
        verify_integrity
    )
    verify_integrity()
    _AG_LOADED = True
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# 데이터 — 환자 34인 마스터 로스터
# ═══════════════════════════════════════════════════════════════════════════════
DRUG_MUGGER_MAP = {
    "다이아벡스": {"depleted": "비타민 B12",           "reason": "메트포르민 장기 복용 시 흡수 저해",       "recom": "메틸코발라민 보충"},
    "노바스크":   {"depleted": "아연, 비타민 B6",       "reason": "혈압약 대사 과정서 미네랄 소모",         "recom": "아연 보충"},
    "리피토":     {"depleted": "코엔자임 Q10",          "reason": "합성 경로(HMG-CoA) 차단",              "recom": "CoQ10 100mg 병용"},
    "넥시움":     {"depleted": "마그네슘, B12",         "reason": "위산 저하로 인한 흡수 방해",            "recom": "고순도 마그네슘"},
    "라식스":     {"depleted": "칼륨, 칼슘, 마그네슘",  "reason": "이뇨 작용을 통한 배설 증가",            "recom": "전해질 균형 필수"},
    "트리테이스": {"depleted": "아연",                  "reason": "ACE 억제제는 아연 배설을 증가시킴",      "recom": "아연 수치 확인"},
    "후릭스":     {"depleted": "칼륨, 마그네슘",        "reason": "루프이뇨제 전해질 배설",                "recom": "칼륨 수치 주기 점검"},
    "알닥톤":     {"depleted": "나트륨",                "reason": "항알도스테론 → Na 배설",                "recom": "저염식 병행"},
}

STRATEGIC_WISDOM = [
    "임상은 '숫자'가 아니라 '사람'의 변화를 읽는 것입니다.",
    "가장 좋은 약은 '복약 순응도'입니다. 환자의 마음을 먼저 얻으십시오.",
    "고령 환자는 '약의 개수'를 줄이는 것이 건강의 지름길입니다.",
    "처방전 행간에 숨겨진 환자의 생활 습관을 읽어내는 것이 실력입니다.",
    "데이터는 거짓말을 하지 않지만, 해석은 전문가의 몫입니다.",
    "정확한 약물 개수는 환자 안전의 첫 번째 단추입니다.",
    "항암제 병용 처방은 상호작용 확인이 생명입니다.",
    "이뇨제 복수 처방 시 전해질 모니터링을 절대 빠뜨리지 마십시오.",
]

PATIENTS = {
    "P001":  {"name": "김상은",           "age": 68, "gender": "남", "diag": "제2형 당뇨병, 고혈압",
              "meds": [{"name": "노바스크정 5mg","dose":"1일 1회","days":30},{"name": "코자정 50mg","dose":"1일 1회","days":30},
                       {"name": "다이아벡스정 500mg","dose":"1일 2회","days":30},{"name": "아마릴정 2mg","dose":"1일 1회","days":30},
                       {"name": "보글리보스 0.3mg","dose":"1일 3회","days":30}], "file": "RX_P001.png"},
    "P002":  {"name": "박지현",           "age": 55, "gender": "여", "diag": "위암 / 항암후오심",
              "meds": [{"name": "젤로다정 500mg","dose":"1일 2회","days":42},{"name": "옥살리플라틴주","dose":"IV","days":1},
                       {"name": "맥페란정","dose":"1일 3회","days":5},{"name": "조프란정 4mg","dose":"1일 2회","days":3},
                       {"name": "노루모액", "dose": "필요시", "days": 14},
                       {"name": "스토가정 10mg","dose":"1일 2회","days":14}], "file": "RX_P002.png"},
    "P003":  {"name": "이준호",           "age": 34, "gender": "남", "diag": "심부전 / 천식",
              "meds": [{"name": "엔트레스토 50mg","dose":"1일 2회","days":60},{"name": "라식스정 40mg","dose":"1일 1회","days":60},
                       {"name": "딜라트렌정 3.125mg","dose":"1일 2회","days":60},{"name": "심비코트 터부헬러","dose":"1일 2회","days":60},
                       {"name": "싱귤레어정 10mg","dose":"1일 1회","days":60},
                       {"name": "닥터테오정 100mg", "dose": "1일 1회", "days": 60}], "file": "RX_P003.png"},
    "P004":  {"name": "최영민",           "age": 45, "gender": "남", "diag": "만성 위염 / 만성 피로",
              "meds": [{"name": "무코스타정","dose":"1일 3회","days":14},{"name": "파리에트정 10mg","dose":"1일 1회","days":14},
                       {"name": "가나톤정","dose":"1일 3회","days":14},{"name": "베아제정","dose":"필요시","days":14},
                       {"name": "우루사정 100mg","dose":"1일 3회","days":30},
                       {"name": "아로나민골드", "dose": "1일 1회", "days": 30},
                       {"name": "실리마린 140mg","dose":"1일 1회","days":30}], "file": "RX_P004.png"},
    "P005":  {"name": "신준호",           "age": 58, "gender": "남", "diag": "고혈압 (저항성)",
              "meds": [{"name": "딜라트렌정 12.5mg","dose":"1일 2회","days":30},{"name": "카나브정 60mg","dose":"1일 1회","days":30},
                       {"name": "노바스크정 5mg","dose":"1일 1회","days":30}], "file": "RX_P005.png"},
    "P006":  {"name": "임대균",           "age": 63, "gender": "남", "diag": "퇴행성관절염",
              "meds": [{"name": "탁센연질캡슐","dose":"1일 2회","days":30},{"name": "조인스정 200mg","dose":"1일 3회","days":30},
                       {"name": "무코스타정","dose":"1일 3회","days":30},{"name": "메디락디에스장용캡슐","dose":"1일 2회","days":30},
                       {"name": "우루사정 100mg", "dose": "1일 1회", "days": 30},
                       {"name": "가나톤정", "dose": "1일 3회", "days": 30},
                       {"name": "고덱스캡슐", "dose": "1일 3회", "days": 30}], "file": "RX_P006.png"},
    "P007":  {"name": "최민준",           "age": 51, "gender": "남", "diag": "가와사키병",
              "meds": [{"name": "아이비글로불린 SN주","dose":"2g/kg IV","days":1},{"name": "아스피린정 100mg","dose":"1일 1회","days":30},
                       {"name": "프레드니솔론정 5mg","dose":"1일 2회","days":14},
                       {"name": "무코스타정", "dose": "1일 3회", "days": 14},
                       {"name": "가나톤정", "dose": "1일 3회", "days": 14}], "file": "RX_P007.png"},
    "P008":  {"name": "한수진",           "age": 49, "gender": "여", "diag": "철결핍성 빈혈",
              "meds": [{"name": "훼로바유정","dose":"1일 1회","days":90},{"name": "비타민C 1000mg","dose":"1일 1회","days":90},
                       {"name": "폴산 1mg","dose":"1일 1회","days":90},{"name": "액티넘EX플러스","dose":"1일 1회","days":90},
                       {"name": "비타민D", "dose": "1일 1회", "days": 90},
                       {"name": "오메가3", "dose": "1일 1회", "days": 90},
                       {"name": "루테인 지아잔틴", "dose": "1일 1회", "days": 90}], "file": "RX_P008.png"},
    "P009":  {"name": "조영진",           "age": 67, "gender": "남", "diag": "비소세포폐암",
              "meds": [{"name": "타그리소정 80mg","dose":"1일 1회","days":28},{"name": "가나톤정","dose":"1일 3회","days":28},
                       {"name": "무코스타정","dose":"1일 3회","days":28},{"name": "코대원시럽","dose":"1일 3회","days":7}], "file": "RX_P009.png"},
    "P010":  {"name": "이지온",           "age": 42, "gender": "여", "diag": "급성 세기관지염",
              "meds": [{"name": "벤톨린 흡입액","dose":"필요시","days":30},{"name": "풀미코트 레스풀","dose":"1일 2회","days":14},
                       {"name": "무코펙트시럽","dose":"1일 3회","days":7},{"name": "메이액트세립","dose":"1일 3회","days":7}], "file": "RX_P010.png"},
    "P011":  {"name": "김도윤",           "age": 12, "gender": "남", "diag": "성장호르몬결핍증",
              "meds": [{"name": "지노트로핀주","dose":"취침전","days":30},{"name": "텐텐츄정","dose":"1일 2회","days":30},
                       {"name": "비타민D 드롭","dose":"1일 1회","days":30},{"name": "칼슘플러스정","dose":"1일 1회","days":30},
                       {"name": "비타민C 1000mg", "dose": "1일 1회", "days": 30},
                       {"name": "마그네슘 400mg", "dose": "1일 1회", "days": 30}], "file": "RX_P011.png"},
    "P012":  {"name": "이수진",           "age": 38, "gender": "여", "diag": "불안장애 / 우울증",
              "meds": [{"name": "렉사프로정 10mg","dose":"1일 1회","days":30},{"name": "데파스정","dose":"1일 2회","days":30},
                       {"name": "자낙스정 0.25mg","dose":"1일 1회","days":30},
                       {"name": "리피토정 20mg", "dose": "1일 1회", "days": 30}], "file": "RX_P012.png"},
    "P013":  {"name": "박서연",           "age": 25, "gender": "여", "diag": "골육종",
              "meds": [{"name": "시스플라틴주","dose":"100mg/m2 IV","days":1},{"name": "독소루비신주","dose":"25mg/m2 IV","days":1},
                       {"name": "메토트렉세이트주","dose":"12g/m2 IV","days":1},
                       {"name": "필그라스팀주", "dose": "IV", "days": 1}], "file": "RX_P013.png"},
    "P014":  {"name": "김철수",           "age": 75, "gender": "남", "diag": "알츠하이머형 치매 / 심부전",
              "meds": [{"name": "아리셉트정 5mg","dose":"1일 1회","days":30},{"name": "에빅사정 10mg","dose":"1일 2회","days":30},
                       {"name": "쿠에타핀정 12.5mg","dose":"취침전","days":30},{"name": "라식스정 40mg","dose":"1일 1회","days":30},
                       {"name": "알닥톤정 25mg","dose":"1일 1회","days":30},
                       {"name": "콩코르정 2.5mg", "dose": "1일 1회", "days": 30}], "file": "RX_P014.png"},
    "P015":  {"name": "정하은",           "age": 8,  "gender": "여", "diag": "소아 아토피 피부염",
              "meds": [{"name": "엘리델크림","dose":"1일 2회 도포","days":14},{"name": "페니라민시럽","dose":"5mL 1일 3회","days":7},
                       {"name": "제모스보습제", "dose": "1일 2회", "days": 14},
                       {"name": "락티케어로션", "dose": "1일 2회", "days": 14}], "file": "RX_P015.png"},
    "P016":  {"name": "James Lee",        "age": 52, "gender": "남", "diag": "알레르기 비염 / 천식",
              "meds": [{"name": "세티리진 10mg","dose":"1일 1회","days":30},{"name": "아바미스 스프레이","dose":"1일 1회","days":30},
                       {"name": "싱귤레어정 10mg","dose":"1일 1회","days":30},
                       {"name": "코대원정", "dose": "1일 3회", "days": 30}], "file": "RX_P016.png"},
    "P017":  {"name": "박소윤",           "age": 31, "gender": "여", "diag": "공황장애",
              "meds": [{"name": "알프람정 0.25mg","dose":"1일 3회","days":30},{"name": "인데놀정 10mg","dose":"1일 2회","days":30},
                       {"name": "스틸녹스정 10mg","dose":"취침전","days":14},
                       {"name": "렉사프로정 10mg", "dose": "1일 1회", "days": 30},
                       {"name": "자낙스정 0.25mg", "dose": "1일 1회", "days": 30}], "file": "RX_P017.png"},
    "P018":  {"name": "Michael Kim",      "age": 44, "gender": "남", "diag": "고혈압 / 고지혈증",
              "meds": [{"name": "노바스크정 5mg","dose":"1일 1회","days":90},{"name": "코자정 50mg","dose":"1일 1회","days":90},
                       {"name": "다이크로짇정 25mg","dose":"1일 1회","days":90},{"name": "리피토정 20mg","dose":"1일 1회","days":90}], "file": "RX_P018.png"},
    "P019":  {"name": "이정태",           "age": 59, "gender": "남", "diag": "고지혈증 / 간수치 상승",
              "meds": [{"name": "크레스토정 10mg","dose":"1일 1회","days":30},{"name": "에제티미브 10mg","dose":"1일 1회","days":30},
                       {"name": "고덱스캡슐","dose":"1일 3회","days":30},
                       {"name": "우루사정 100mg", "dose": "1일 3회", "days": 30},
                       {"name": "실리마린 140mg", "dose": "1일 1회", "days": 30}], "file": "RX_P019.png"},
    "P020":  {"name": "오창현",           "age": 36, "gender": "남", "diag": "울혈성 심부전",
              "meds": [{"name": "알닥톤정 25mg","dose":"1일 2회","days":30},{"name": "라식스정 20mg","dose":"1일 1회","days":30},
                       {"name": "토르세미드정 5mg","dose":"1일 1회","days":30}], "file": "RX_P020.png"},
    "P021":  {"name": "윤지영",           "age": 27, "gender": "여", "diag": "안구건조증 / 시력저하",
              "meds": [{"name": "루테인 지아잔틴","dose":"1일 1회","days":90},{"name": "오메가3","dose":"1일 1회","days":90},
                       {"name": "리레바점안액", "dose": "1일 3회", "days": 90}], "file": "RX_P021.png"},
    "P022":  {"name": "강민서",           "age": 19, "gender": "여", "diag": "신경병증성 통증",
              "meds": [{"name": "탁센연질캡슐","dose":"필요시","days":14},{"name": "마그네슘 400mg","dose":"1일 1회","days":30},
                       {"name": "리리카캡슐 25mg","dose":"1일 2회","days":30},
                       {"name": "인데놀정 10mg", "dose": "1일 2회", "days": 30},
                       {"name": "알프람정 0.25mg", "dose": "1일 3회", "days": 30}], "file": "RX_P022.png"},
    "P023":  {"name": "서동훈",           "age": 48, "gender": "남", "diag": "전이성 암 (혈관육종)",
              "meds": [{"name": "파클리탁셀주","dose":"80mg/m2 IV","days":1},{"name": "덱사메타손정 4mg","dose":"전처치","days":1},
                       {"name": "페니라민정", "dose": "1일 2회", "days": 1},
                       {"name": "가스터정", "dose": "1일 2회", "days": 1}], "file": "RX_P023.png"},
    "P024":  {"name": "한지민",           "age": 33, "gender": "여", "diag": "알레르기 비염",
              "meds": [{"name": "씨투스정 50mg","dose":"1일 2회","days":14},{"name": "싱귤레어츄정 5mg","dose":"1일 1회","days":14},
                       {"name": "나조넥스스프레이", "dose": "1일 1회", "days": 30}], "file": "RX_P024.png"},
    "P025":  {"name": "류태영",           "age": 41, "gender": "남", "diag": "만성 위염 / 역류성 식도염",
              "meds": [{"name": "스토가정 10mg","dose":"1일 2회","days":30},{"name": "가나톤정","dose":"1일 3회","days":30},
                       {"name": "넥시움정 20mg","dose":"1일 1회","days":30}], "file": "RX_P025.png"},
    "P026":  {"name": "송은주",           "age": 53, "gender": "여", "diag": "철결핍성 빈혈",
              "meds": [{"name": "훼로바유정","dose":"1일 1회","days":90},{"name": "폴산 1mg","dose":"1일 3회","days":90},
                       {"name": "비타민B12", "dose": "1일 1회", "days": 90},
                       {"name": "비타민C 1000mg", "dose": "1일 1회", "days": 90}], "file": "RX_P026.png"},
    "P027":  {"name": "최희정",           "age": 39, "gender": "여", "diag": "골다공증",
              "meds": [{"name": "포사맥스플러스디","dose":"주 1회","days":90},{"name": "칼슘 500mg","dose":"1일 1회","days":90},
                       {"name": "비타민D3 2000IU", "dose": "1일 1회", "days": 90}], "file": "RX_P027.png"},
    "P028":  {"name": "김현숙",           "age": 61, "gender": "여", "diag": "유방암 (HER2+)",
              "meds": [{"name": "허셉틴주","dose":"6mg/kg IV","days":21},{"name": "타목시펜정 20mg","dose":"1일 1회","days":365},
                       {"name": "비타민D","dose":"1일 1회","days":90},{"name": "졸라덱스데포주","dose":"월 1회","days":28}], "file": "RX_P028.png"},
    "P029":  {"name": "박명심 (자궁암)",  "age": 55, "gender": "여", "diag": "C55 자궁암 — 항암처방",
              "meds": [{"name": "보트리엔트정 400MG","dose":"1일 1회 공복","days":42},
                       {"name": "코슈정 60MG","dose":"1일 3회","days":7},
                       {"name": "코푸시럽 20ML","dose":"1일 3회","days":7},
                       {"name": "삼남아세트아미노펜정 500MG","dose":"1일 3회","days":7}],
              "file": "RX_P029.png",
              "warn": "⚠️ 보트리엔트+코슈정: 혈압 상승·CYP3A4 상호작용 | 보트리엔트+아세트아미노펜: 간독성 상가"},
    "P029B": {"name": "박명심 (심근병증)","age": 55, "gender": "여", "diag": "I42.7 확장성심근병증",
              "meds": [{"name": "트리테이스정 2.5MG","dose":"1일 1회","days":100},
                       {"name": "후릭스정 40MG","dose":"1일 1회 아침","days":100},
                       {"name": "알닥톤필름코팅정 25MG","dose":"1일 1회","days":100},
                       {"name": "콩코르정 2.5MG","dose":"1일 1회","days":100},
                       {"name": "자디앙정 10MG","dose":"1일 1회 아침","days":100},
                       {"name": "프로코란정 5MG","dose":"1일 2회","days":100}],
              "file": "RX_P029B.png",
              "warn": "⚠️ 트리테이스+알닥톤: 고칼륨혈증 | 후릭스+알닥톤: 전해질 모니터링 | 프로코란: 서맥 주의"},
    "P030":  {"name": "유창수",           "age": 34, "gender": "남", "diag": "J30.1 알레르기 비염 / J06.9 급성 상기도감염",
              "meds": [{"name": "살부타민정","dose":"1일 2회","days":7},
                       {"name": "코대원정 수에크네오케이정","dose":"1일 2회","days":7},
                       {"name": "슈다페드정 60MG","dose":"1일 2회","days":7},
                       {"name": "베아졸론정 4MG","dose":"1일 1회","days":7},
                       {"name": "라니넥스나잘스프레이","dose":"1일 1회","days":7}],
              "file": "스크린샷 2026-05-07 182007.png",
              "warn": "⚠️ 슈다페드+살부타민: 심계항진·혈압 상승 가능 | 베아졸론: 7일 초과 금지"},
}

MED_INFO = {
    "가나톤정": {"file": "가나톤정.png", "v_id": "분석된 정제", "warn": "식전 복용 권장. 위장관 운동 촉진."},
    "고덱스캡슐": {"file": "godex.png", "v_id": "캡슐제", "warn": "간수치 개선. 식후 복용."},
    "넥시움정 20mg": {"file": "nexium.png", "v_id": "분석된 정제", "warn": "위식도 역류 질환. 장기 복용 시 미네랄 부족 주의."},
    "노바스크정 5mg": {"file": "노바스크정.png", "v_id": "분석된 정제", "warn": "자몽주스 주의. 매일 일정한 시간 복용."},
    "다이아벡스정 500mg": {"file": "다이아벡스정.png", "v_id": "분석된 정제", "warn": "유산산증 주의. 식사 직후 복용."},
    "다이크로짇정 25mg": {"file": "dichlozid.png", "v_id": "분석된 정제", "warn": "전해질 불균형 주의. 아침 복용."},
    "데파스정": {"file": "depas.png", "v_id": "분석된 정제", "warn": "안정제. 졸음 및 의존성 주의."},
    "덱사메타손정 4mg": {"file": "덱사메타손정.png", "v_id": "분석된 정제", "warn": "강력한 항염증 스테로이드."},
    "독소루비신주": {"file": "독소루비신주.png", "v_id": "주사제", "warn": "심장 독성 주의. 소변색이 붉게 변할 수 있음."},
    "딜라트렌정 12.5mg": {"file": "dilatrend.png", "v_id": "분석된 정제", "warn": "서맥 및 저혈압 주의. 서서히 증량."},
    "딜라트렌정 3.125mg": {"file": "dilatrend.png", "v_id": "분석된 정제", "warn": "서맥 및 저혈압 주의. 서서히 증량."},
    "라니넥스나잘스프레이": {"file": "laninex.png", "v_id": "나잘스프레이", "warn": "비염 스테로이드 분무제."},
    "라식스정 20mg": {"file": "lasix.png", "v_id": "분석된 정제", "warn": "아침 식후 복용. 칼륨 수치 확인 필수."},
    "라식스정 40mg": {"file": "lasix.png", "v_id": "분석된 정제", "warn": "아침 식후 복용. 칼륨 수치 확인 필수."},
    "렉사프로정 10mg": {"file": "렉사프로정.png", "v_id": "분석된 정제", "warn": "우울증 치료제. 초기 불안 증가 가능성."},
    "루테인 지아잔틴": {"file": "루테인.png", "v_id": "분석된 정제", "warn": "눈 건강 보조. 황반 색소 밀도 유지."},
    "리리카캡슐 25mg": {"file": "lyrica.png", "v_id": "캡슐제", "warn": "신경병증 통증. 어지러움, 부종 주의."},
    "리피토정 20mg": {"file": "리피토정.png", "v_id": "분석된 정제", "warn": "간 수치 및 근육통 모니터링. CoQ10 보충 권장."},
    "마그네슘 400mg": {"file": "마그네슘.png", "v_id": "분석된 정제", "warn": "설사 주의. 근육 이완 보조."},
    "맥페란정": {"file": "맥페란정.png", "v_id": "분석된 정제", "warn": "추체외로 증상(떨림) 주의. 고령자 주의."},
    "메디락디에스장용캡슐": {"file": "메디락디에스장용캡슐.png", "v_id": "캡슐제", "warn": "정장제. 유산균 증식 보조."},
    "메이액트세립": {"file": "메이액트세립.png", "v_id": "시럽제", "warn": "항생제. 증상 호전되어도 끝까지 복용."},
    "메토트렉세이트주": {"file": "메토트렉세이트주.png", "v_id": "주사제", "warn": "골수 억제 주의. 엽산 보충 필요."},
    "무코스타정": {"file": "무코스타정.png", "v_id": "분석된 정제", "warn": "위점막 보호제. 식후 복용."},
    "무코펙트시럽": {"file": "무코펙트시럽.png", "v_id": "시럽제", "warn": "가래 배출 촉진. 수분 섭취 권장."},
    "베아제정": {"file": "베아제정.png", "v_id": "분석된 정제", "warn": "소화효소제. 필요시 복용."},
    "베아졸론정 4MG": {"file": "beasolon.png", "v_id": "분석된 정제", "warn": "단기간 사용 권장. 스테로이드."},
    "벤톨린 흡입액": {"file": "벤톨린.png", "v_id": "시럽제", "warn": "급성 천식 증상 완화. 과다 사용 금지."},
    "보글리보스 0.3mg": {"file": "보글리보스.png", "v_id": "분석된 정제", "warn": "식사 직전 복용. 장내가스 주의."},
    "보트리엔트정 400MG": {"file": "보트리엔트정.png", "v_id": "분석된 정제", "warn": "표적항암제. 공복 복용 필수. 간수치 확인."},
    "볼프코라진정 2.5MG": {"file": "볼프코라진정.png", "v_id": "분석된 정제", "warn": "협심증 완화. 두통 주의."},
    "비타민C 1000mg": {"file": "비타민C.png", "v_id": "분석된 정제", "warn": "신장결석 주의. 충분한 수분 섭취."},
    "비타민D": {"file": "비타민D.png", "v_id": "분석된 정제", "warn": "골다공증 예방. 칼슘 흡수 보강."},
    "비타민D 드롭": {"file": "비타민D.png", "v_id": "분석된 정제", "warn": "골다공증 예방. 칼슘 흡수 보강."},
    "살부타민정": {"file": "살부타민정.png", "v_id": "분석된 정제", "warn": "급성 기관지 확장. 떨림 주의."},
    "삼남아세트아미노펜정 500MG": {"file": "삼남아세트아미노펜정.png", "v_id": "분석된 정제", "warn": "간 손상 주의. 하루 4g 초과 금지."},
    "세티리진 10mg": {"file": "세티리진.png", "v_id": "분석된 정제", "warn": "졸음 주의. 알레르기 증상 완화."},
    "슈다페드정 60MG": {"file": "sudafed.png", "v_id": "분석된 정제", "warn": "심계항진, 불면 주의."},
    "스토가정 10mg": {"file": "스토가정.png", "v_id": "분석된 정제", "warn": "위점막 보호 및 산 분비 억제."},
    "스틸녹스정 10mg": {"file": "스틸녹스정.png", "v_id": "분석된 정제", "warn": "취침 직전 복용. 몽유병 등 이상행동 주의."},
    "시스플라틴주": {"file": "시스플라틴주.png", "v_id": "주사제", "warn": "신장 독성 주의. 충분한 수액 공급."},
    "실리마린 140mg": {"file": "실리마린캡슐.png", "v_id": "분석된 정제", "warn": "간세포 보호 및 독소 배출 보조."},
    "심비코트 터부헬러": {"file": "symbicort.png", "v_id": "흡입제", "warn": "흡입 후 입안을 반드시 헹굴 것(칸디다 예방)."},
    "싱귤레어정 10mg": {"file": "singulair.png", "v_id": "분석된 정제", "warn": "취침 전 복용. 정서 변화(우울 등) 모니터링."},
    "싱귤레어츄정 5mg": {"file": "singulair.png", "v_id": "분석된 정제", "warn": "취침 전 복용. 정서 변화(우울 등) 모니터링."},
    "씨투스정 50mg": {"file": "씨투스정.png", "v_id": "분석된 정제", "warn": "비염 치료제. 졸음 적음."},
    "아리셉트정 5mg": {"file": "aricept.png", "v_id": "분석된 정제", "warn": "치매 증상 완화. 서맥 및 소화기 장애 주의."},
    "아마릴정 2mg": {"file": "아마릴정.png", "v_id": "분석된 정제", "warn": "저혈당 주의. 규칙적인 식사 필수."},
    "아바미스 스프레이": {"file": "아바미스.png", "v_id": "나잘스프레이", "warn": "비강 스테로이드. 매일 일정한 시간 사용."},
    "아스피린정 100mg": {"file": "아스피린정.png", "v_id": "분석된 정제", "warn": "출혈 경향 주의. 지혈 지연 가능성."},
    "아이비글로불린 SN주": {"file": "아이비글로불린.png", "v_id": "주사제", "warn": "면역 조절. 주입 반응 모니터링."},
    "알닥톤정 25mg": {"file": "알닥톤정.png", "v_id": "분석된 정제", "warn": "고칼륨혈증 주의. 이뇨제."},
    "알닥톤필름코팅정 25MG": {"file": "알닥톤정.png", "v_id": "분석된 정제", "warn": "고칼륨혈증 주의. 이뇨제."},
    "알프람정 0.25mg": {"file": "알프람정.png", "v_id": "분석된 정제", "warn": "불안 조절. 의존성 주의."},
    "액티넘EX플러스": {"file": "actinum.png", "v_id": "시럽제", "warn": "비타민 B군 보충. 피로 회복."},
    "에빅사정 10mg": {"file": "ebixa.png", "v_id": "분석된 정제", "warn": "중등도 이상 치매. 어지러움 주의."},
    "에제티미브 10mg": {"file": "에제티미브.png", "v_id": "분석된 정제", "warn": "콜레스테롤 흡수 차단. 스타틴과 병용."},
    "엔트레스토 50mg": {"file": "entresto.png", "v_id": "분석된 정제", "warn": "심부전 악화 방지. 혈압 및 칼륨 모니터링."},
    "엘리델크림": {"file": "엘리델크림.png", "v_id": "외용제", "warn": "아토피 국소 치료. 작열감 주의."},
    "오메가3": {"file": "오메가3.png", "v_id": "분석된 정제", "warn": "혈행 개선. 출혈 경향 시 주의."},
    "옥살리플라틴주": {"file": "oxaliplatin.png", "v_id": "주사제", "warn": "말초신경병증 주의. 찬 것에 노출 금지."},
    "우루사정 100mg": {"file": "우루사정.png", "v_id": "분석된 정제", "warn": "간 기능 개선 및 담석 예방."},
    "인데놀정 10mg": {"file": "indenol.png", "v_id": "분석된 정제", "warn": "심계항진 완화. 서맥 주의."},
    "자낙스정 0.25mg": {"file": "xanax.png", "v_id": "분석된 정제", "warn": "급성 불안 조절. 알코올 금지."},
    "자디앙정 10MG": {"file": "자디앙정.png", "v_id": "분석된 정제", "warn": "당뇨 및 심부전 치료. 요로감염 주의."},
    "젤로다정 500mg": {"file": "젤로다정.png", "v_id": "분석된 정제", "warn": "손발증후군 주의. 비타민 B6 보충 권장."},
    "조인스정 200mg": {"file": "조인스정.png", "v_id": "분석된 정제", "warn": "천연물 관절염 치료제. 소화기계 주의."},
    "조프란정 4mg": {"file": "조프란정.png", "v_id": "분석된 정제", "warn": "두통, 변비 주의. 항암후 오심 조절."},
    "졸라덱스데포주": {"file": "졸라덱스데포주.png", "v_id": "주사제", "warn": "호르몬 억제. 폐경 증상 유발 가능."},
    "지노트로핀주": {"file": "지노트로핀주.png", "v_id": "주사제", "warn": "성장호르몬. 취침 전 피하 주사."},
    "카나브정 60mg": {"file": "kanarb.png", "v_id": "분석된 정제", "warn": "국산 ARB 고혈압약. 혈압 안정화."},
    "칼슘 500mg": {"file": "칼슘.png", "v_id": "분석된 정제", "warn": "변비 주의. 비타민 D와 병용 권장."},
    "칼슘플러스정": {"file": "칼슘플러스정.png", "v_id": "분석된 정제", "warn": "변비 주의. 비타민 D와 병용 권장."},
    "코대원시럽": {"file": "코대원시럽.png", "v_id": "시럽제", "warn": "졸음 주의. 기침 완화제."},
    "코대원정 수에크네오케이정": {"file": "codae_won.png", "v_id": "분석된 정제", "warn": "졸음 주의. 기침 완화제."},
    "코슈정 60MG": {"file": "sudafed.png", "v_id": "분석된 정제", "warn": "심계항진, 불면 주의. 코막힘 완화."},
    "코자정 50mg": {"file": "코자정.png", "v_id": "분석된 정제", "warn": "임의로 복용 중단 금지. 신장 기능 모니터링."},
    "코푸시럽 20ML": {"file": "codae_won.png", "v_id": "시럽제", "warn": "진해거담제. 졸음 주의."},
    "쿠에타핀정 12.5mg": {"file": "quetiapine.png", "v_id": "분석된 정제", "warn": "취침 전 복용. 기립성 저혈압 주의."},
    "크레스토정 10mg": {"file": "크레스토정.png", "v_id": "분석된 정제", "warn": "강력한 고지혈증 약. 근육통 주의."},
    "타그리소정 80mg": {"file": "tagrisso.png", "v_id": "분석된 정제", "warn": "폐암 표적치료제. 설사, 발진 모니터링."},
    "타목시펜정 20mg": {"file": "tamoxifen.png", "v_id": "분석된 정제", "warn": "유방암 재발 방지. 안면홍조 주의."},
    "탁센연질캡슐": {"file": "탁센연질캡슐.png", "v_id": "캡슐제", "warn": "위장장애 주의. 충분한 물과 함께 복용."},
    "텐텐츄정": {"file": "tenten.png", "v_id": "분석된 정제", "warn": "어린이 영양제. 과량 섭취 주의."},
    "토르세미드정 5mg": {"file": "torsemide.png", "v_id": "분석된 정제", "warn": "강력한 이뇨제. 전해질 주의."},
    "트리테이스정 2.5MG": {"file": "트리테이스정.png", "v_id": "분석된 정제", "warn": "어지러움, 마른 기침 주의. 혈압약."},
    "파리에트정 10mg": {"file": "파리에트정.png", "v_id": "분석된 정제", "warn": "강력한 산 분비 억제(PPI). 아침 공복 권장."},
    "파클리탁셀주": {"file": "파클리탁셀주.png", "v_id": "주사제", "warn": "과민 반응 주의. 탈모 가능성 높음."},
    "페니라민시럽": {"file": "페니라민시럽.png", "v_id": "시럽제", "warn": "강한 졸음 주의. 항히스타민제."},
    "포사맥스플러스디": {"file": "포사맥스플러스디.png", "v_id": "분석된 정제", "warn": "골다공증 치료. 복용 후 30분간 눕지 말 것."},
    "폴산 1mg": {"file": "폴산.png", "v_id": "분석된 정제", "warn": "세포 생성 보조. 빈혈 예방."},
    "풀미코트 레스풀": {"file": "풀미코트.png", "v_id": "분석된 정제", "warn": "스테로이드 흡입제. 구강 위생 필수."},
    "프레드니솔론정 5mg": {"file": "프레드니솔론정.png", "v_id": "분석된 정제", "warn": "스테로이드제. 임의 중단 금지. 위장장애."},
    "프로코란정 5MG": {"file": "프로코라란정.png", "v_id": "분석된 정제", "warn": "서맥 주의. 심박수 조절."},
    "허셉틴주": {"file": "허셉틴주.png", "v_id": "주사제", "warn": "HER2+ 표적치료. 심장 기능 주기적 확인."},
    "후릭스정 40MG": {"file": "후릭스정.png", "v_id": "분석된 정제", "warn": "이뇨제. 칼륨 보충 필요할 수 있음."},
    "훼로바유정": {"file": "훼로바유정.png", "v_id": "분석된 정제", "warn": "변비, 검은 변 주의. 비타민 C와 복용 시 흡수 증가."},
    "노루모액": {"file": "norumo.png", "v_id": "시럽제", "warn": "제산제. 식사 사이 복용 권장."},
    "닥터테오정 100mg": {"file": "닥터테오정.png", "v_id": "분석된 정제", "warn": "천식 및 COPD 치료제. 위장 장애 주의."},
    "아로나민골드": {"file": "aronamin.png", "v_id": "분석된 정제", "warn": "활성비타민 B군. 육체 피로 회복."},
    "필그라스팀주": {"file": "필그라스팀주.png", "v_id": "주사제", "warn": "백혈구 수치 증가. 뼈 통증 주의."},
    "콩코르정 2.5mg": {"file": "콩코르정.png", "v_id": "분석된 정제", "warn": "부정맥 및 고혈압 치료. 서맥 주의."},
    "제모스보습제": {"file": "xemos.png", "v_id": "외용제", "warn": "건조한 피부에 수분 공급."},
    "락티케어로션": {"file": "lacticare.png", "v_id": "외용제", "warn": "습진 및 피부염 치료 스테로이드."},
    "코대원정": {"file": "codae_won.png", "v_id": "분석된 정제", "warn": "졸음 주의. 기침 완화제."},
    "리레바점안액": {"file": "rireba.png", "v_id": "외용제", "warn": "인공눈물. 안구 건조 증상 완화."},
    "페니라민정": {"file": "pheniramine.png", "v_id": "분석된 정제", "warn": "강한 졸음 주의. 항히스타민제."},
    "가스터정": {"file": "gaster.png", "v_id": "분석된 정제", "warn": "위산 분비 억제. 식후 또는 취침 전 복용."},
    "나조넥스스프레이": {"file": "nasonex.png", "v_id": "나잘스프레이", "warn": "비염 치료 스테로이드 분무제."},
    "비타민B12": {"file": "비타민B12.png", "v_id": "분석된 정제", "warn": "빈혈 예방 및 신경계 건강 보조."},
    "비타민D3 2000IU": {"file": "비타민D3 2000IU.png", "v_id": "분석된 정제", "warn": "골다공증 예방. 칼슘 흡수 보강."},
    "살부타민정": {"file": "symbicort.png", "v_id": "분석된 정제", "warn": "급성 기관지 확장. 떨림 주의."},
    "볼프코라진정 2.5MG": {"file": "콩코르정.png", "v_id": "분석된 정제", "warn": "협심증 완화. 두통 주의."},
}


# ── 헬퍼 함수 ──────────────────────────────────────────────────────────────
def get_pill_img(pill_name: str):
    clean = re.sub(r'[^가-힣a-zA-Z0-9]', '', pill_name).lower()
    for key, info in MED_INFO.items():
        ck = re.sub(r'[^가-힣a-zA-Z0-9]', '', key).lower()
        if (ck in clean or clean in ck) and info["file"]:
            path = os.path.join(PILL_DIR, info["file"])
            if os.path.exists(path):
                with open(path, "rb") as f:
                    ext = info["file"].split('.')[-1].lower()
                    return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()
    return None

def get_med_info(name: str) -> dict:
    clean = re.sub(r'[^가-힣a-zA-Z0-9]', '', name).lower()
    for k, v in MED_INFO.items():
        ck = re.sub(r'[^가-힣a-zA-Z0-9]', '', k).lower()
        if ck in clean or clean in ck: return v
    return {"v_id": "정보 확인 중", "warn": "약사/의사 상담 필요"}

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
.stApp { background: radial-gradient(circle at top right,#0a192f,#020617); color:#fff; font-family:'Noto Sans KR',sans-serif; }
.glass-card { background:rgba(255,255,255,0.03); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.1);
    border-radius:20px; padding:20px; margin-bottom:20px; }
.med-card { background:rgba(0,0,0,0.35); border-radius:15px; padding:14px; margin-bottom:12px;
    border-left:5px solid #00f2ff; display:flex; align-items:center; gap:14px; }
.med-img-box { width:72px; height:72px; background:#000; border-radius:12px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.app-header { font-family:'Orbitron',sans-serif; text-align:center;
    background:linear-gradient(90deg,#00f2ff,#39ff14); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
</style>""", unsafe_allow_html=True)

# ── 사이드바 ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 class='app-header'>⚕ COMMAND CENTER</h2>", unsafe_allow_html=True)
    
    # 시스템 무결성 상태 표시
    st.markdown("### 🛠 SYSTEM INTEGRITY")
    if _SYS_CHECKS["files"]: st.success("✅ 파일 무결성 확인")
    else: st.error(f"❌ 파일 누락: {', '.join(_MISSING_FILES)}")
    
    if _SYS_CHECKS["env"]: st.success("✅ 환경 구성 완료")
    else: st.warning("⚠️ Gemini SDK 누락")
    
    if _AG_LOADED: st.success("✅ AntiGravity AI 연동")
    else: st.info("ℹ️ AI 데이터셋 미연결")
    
    st.divider()
    view = st.radio("화면 선택", ["🏥 환자 처방전", "🧠 AntiGravity 데이터셋"])
    
    if view == "🏥 환자 처방전":
        sel_pid = st.selectbox("환자 선택", [None] + sorted(PATIENTS.keys()), 
                               format_func=lambda x: f"{PATIENTS[x]['name']} ({PATIENTS[x]['age']}세)" if x else "--- 선택 ---")
    else: sel_pid = None

# ── 메인 렌더링 ──────────────────────────────────────────────────────────────
if view == "🧠 AntiGravity 데이터셋":
    st.markdown("<h1 class='app-header'>🧠 AntiGravity AI Dataset</h1>", unsafe_allow_html=True)
    if _AG_LOADED:
        total = len(_AG_TRAIN) + len(_AG_VAL) + len(_AG_TEST)
        st.info(f"총 {total}건의 학습용 데이터셋이 로드되었습니다.")
        st.write(f"학습: {len(_AG_TRAIN)} | 검증: {len(_AG_VAL)} | 테스트: {len(_AG_TEST)}")
    else:
        st.warning("데이터셋 파일(pharma_ai_antigravity.py)을 로드할 수 없습니다.")
else:
    if not sel_pid:
        st.markdown("<h1 class='app-header'>🏥 PHARMA-HYBRID v125.0</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card' style='text-align:center;padding:50px;'><h2>환자를 선택하여 처방 분석을 시작하세요</h2></div>", unsafe_allow_html=True)
    else:
        p = PATIENTS[sel_pid]
        st.markdown(f"<h1 class='app-header'>🏥 {p['name']} 처방 분석</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### 📄 처방전 원본")
            img_path = os.path.join(PRESCRIPTION_DIR, p["file"])
            if os.path.exists(img_path): st.image(img_path, width='stretch')
            else: st.info("처방전 이미지 파일이 없습니다.")
            
        with col2:
            st.markdown("### 💊 처방 약물 정보")
            
            # 환자별 종합 주의사항 표시 (P029, P029B, P030 등)
            if "warn" in p:
                st.error(p["warn"])
                
            for med in p["meds"]:
                img_data = get_pill_img(med["name"])
                info = get_med_info(med["name"])
                st.markdown(f"""
                <div class='med-card'>
                    <div class='med-img-box'>
                        {f'<img src="{img_data}" width="72">' if img_data else '💊'}
                    </div>
                    <div>
                        <div style='color:#00f2ff;font-weight:700;'>{med["name"]}</div>
                        <div style='font-size:0.8rem;color:#aaa;'>{med["dose"]} | {info["v_id"]}</div>
                        <div style='color:#39ff14;font-size:0.85rem;'>➔ {info["warn"]}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
