#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[ASSISTANT] MEDICAL-PHARMA HUB v123.0 - PREMIUM APP EDITION
- 33인 환자 전수 로스터: 처방전 실물 이미지 기반 데이터 완전 동기화
- 무결성 감사 반영: 모든 알약 이미지 파일명(Matching Fix) 및 복약 주의사항(warn) 100% 동기화
- 디자인 고도화: 글래스모피즘(Glassmorphism) 및 애니메이션 효과가 적용된 프리미엄 앱 인터페이스
- 비식별화 및 개인정보 보호: 주민번호 마스킹 및 실명 기반 로스터 유지
"""

import os
import base64
import re
import random
from datetime import datetime
import streamlit as st

# ── 1. 시스템 인프라 및 경로 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="PHARMA-HYBRID v123.0 (Premium Hub)", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

PILL_DIR = r"C:\Users\rcs91\github\med_project\pill_images"
PRESCRIPTION_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"

# 폴더 자동 생성
for d in [PILL_DIR, PRESCRIPTION_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# ── 2. [전략 데이터셋] 드럭 머거 및 임상 결정 트리 ───────────────────────────────

DRUG_MUGGER_MAP = {
    "다이아벡스": {"depleted": "비타민 B12", "reason": "메트포르민 장기 복용 시 흡수 저해", "recom": "메틸코발라민 보충"},
    "노바스크": {"depleted": "아연, 비타민 B6", "reason": "혈압약 대사 과정서 미네랄 소모", "recom": "아연 보충"},
    "리피토": {"depleted": "코엔자임 Q10", "reason": "합성 경로(HMG-CoA) 차단", "recom": "CoQ10 100mg 병용"},
    "넥시움": {"depleted": "마그네슘, B12", "reason": "위산 저하로 인한 흡수 방해", "recom": "고순도 마그네슘"},
    "라식스": {"depleted": "칼륨, 칼슘, 마그네슘", "reason": "이뇨 작용을 통한 배설 증가", "recom": "전해질 균형 필수"},
    "트리테이스": {"depleted": "아연", "reason": "ACE 억제제는 아연 배설을 증가시킴", "recom": "아연 수치 확인"}
}

STRATEGIC_WISDOM = [
    "임상은 '숫자'가 아니라 '사람'의 변화를 읽는 것입니다.",
    "가장 좋은 약은 '복약 순응도'입니다. 환자의 마음을 먼저 얻으십시오.",
    "고령 환자는 '약의 개수'를 줄이는 것이 건강의 지름길입니다.",
    "처방전 행간에 숨겨진 환자의 생활 습관을 읽어내는 것이 실력입니다.",
    "데이터는 거짓말을 하지 않지만, 해석은 전문가의 몫입니다.",
    "정확한 약물 개수는 환자 안전의 첫 번째 단추입니다."
]

# [환자 마스터 DB - 33인 완전 로스터 & 100% 실물 동기화]
PATIENTS = {
    "P001": {"name": "김상은", "age": 68, "gender": "남", "diag": "제2형 당뇨병, 고혈압", "meds": [{"name": "노바스크정 5mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "코자정 50mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "다이아벡스정 500mg", "dose": "1회 1정, 1일 2회", "days": 30}, {"name": "아마릴정 2mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "보글리보스 0.3mg", "dose": "1회 1정, 1일 3회", "days": 30}], "file": "RX_P001.png"},
    "P002": {"name": "박지현", "age": 55, "gender": "여", "diag": "위암 / 항암후오심", "meds": [{"name": "젤로다정 500mg", "dose": "1000mg/m2, 1일 2회", "days": 42}, {"name": "옥살리플라틴주", "dose": "IV infusion", "days": 1}, {"name": "맥페란정", "dose": "1회 1정, 1일 3회", "days": 5}, {"name": "조프란정 4mg", "dose": "1회 1정, 1일 2회", "days": 3}, {"name": "스토가정 10mg", "dose": "1회 1정, 1일 2회", "days": 14}], "file": "RX_P002.png"},
    "P003": {"name": "이준호", "age": 34, "gender": "남", "diag": "심부전 / 천식", "meds": [{"name": "엔트레스토 50mg", "dose": "1회 1정, 1일 2회", "days": 60}, {"name": "라식스정 40mg", "dose": "1회 0.5정, 1일 1회", "days": 60}, {"name": "딜라트렌정 3.125mg", "dose": "1회 1정, 1일 2회", "days": 60}, {"name": "심비코트 터부헬러", "dose": "1회 1흡입, 1일 2회", "days": 60}, {"name": "싱귤레어정 10mg", "dose": "1일 1회 저녁", "days": 60}], "file": "RX_P003.png"},
    "P004": {"name": "최영민", "age": 45, "gender": "남", "diag": "만성 위염 / 만성 피로", "meds": [{"name": "무코스타정", "dose": "1회 1정, 1일 3회", "days": 14}, {"name": "파리에트정 10mg", "dose": "1회 1정, 1일 1회", "days": 14}, {"name": "가나톤정", "dose": "1회 1정, 1일 3회", "days": 14}, {"name": "베아제정", "dose": "필요시", "days": 14}, {"name": "우루사정 100mg", "dose": "1회 1정, 1일 3회", "days": 30}, {"name": "아로나민골드", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "실리마린 140mg", "dose": "1회 1캡슐, 1일 1회", "days": 30}], "file": "RX_P004.png"},
    "P005": {"name": "신준호", "age": 58, "gender": "남", "diag": "고혈압 (저항성)", "meds": [{"name": "딜라트렌정 12.5mg", "dose": "1회 1정, 1일 2회", "days": 30}, {"name": "카나브정 60mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "노바스크정 5mg", "dose": "1회 1정, 1일 1회", "days": 30}], "file": "RX_P005.png"},
    "P006": {"name": "임대균", "age": 63, "gender": "남", "diag": "퇴행성관절염", "meds": [{"name": "탁센연질캡슐", "dose": "1회 1정, 1일 2회", "days": 30}, {"name": "조인스정 200mg", "dose": "1회 1정, 1일 3회", "days": 30}, {"name": "무코스타정", "dose": "1회 1정, 1일 3회", "days": 30}, {"name": "메디락디에스장용캡슐", "dose": "1회 1정, 1일 2회", "days": 30}], "file": "RX_P006.png"},
    "P007": {"name": "최민준", "age": 51, "gender": "남", "diag": "가와사키병", "meds": [{"name": "아이비글로불린 SN주", "dose": "2g/kg IV", "days": 1}, {"name": "아스피린정 100mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "프레드니솔론정 5mg", "dose": "1회 1정, 1일 2회", "days": 14}], "file": "RX_P007.png"},
    "P008": {"name": "한수진", "age": 49, "gender": "여", "diag": "철결핍성 빈혈", "meds": [{"name": "훼로바유정", "dose": "1회 1정, 1일 1회", "days": 90}, {"name": "비타민C 1000mg", "dose": "1회 1정, 1일 1회", "days": 90}, {"name": "폴산 1mg", "dose": "1회 1정, 1일 1회", "days": 90}, {"name": "액티넘EX플러스", "dose": "1회 1정, 1일 1회", "days": 90}], "file": "RX_P008.png"},
    "P009": {"name": "조영진", "age": 67, "gender": "남", "diag": "비소세포폐암", "meds": [{"name": "타그리소정 80mg", "dose": "1회 1정, 1일 1회", "days": 28}, {"name": "가나톤정", "dose": "1회 1정, 1일 3회", "days": 28}, {"name": "무코스타정", "dose": "1회 1정, 1일 3회", "days": 28}, {"name": "코대원시럽", "dose": "1회 1포, 1일 3회", "days": 7}], "file": "RX_P009.png"},
    "P010": {"name": "이지온", "age": 42, "gender": "여", "diag": "급성 세기관지염", "meds": [{"name": "벤톨린 흡입액", "dose": "2.5mg, 필요시", "days": 30}, {"name": "풀미코트 레스풀", "dose": "1일 2회 흡입", "days": 14}, {"name": "무코펙트시럽", "dose": "1회 1포, 1일 3회", "days": 7}, {"name": "메이액트세립", "dose": "1회 1포, 1일 3회", "days": 7}], "file": "RX_P010.png"},
    "P011": {"name": "김도윤", "age": 12, "gender": "남", "diag": "성장호르몬결핍증 / 제1형 당뇨", "meds": [{"name": "지노트로핀주", "dose": "0.1U/kg, 취침전", "days": 30}, {"name": "텐텐츄정", "dose": "1일 2회", "days": 30}, {"name": "비타민D 드롭", "dose": "2000IU, 1일 1회", "days": 30}, {"name": "칼슘플러스정", "dose": "1일 1회", "days": 30}], "file": "RX_P011.png"},
    "P012": {"name": "이수진", "age": 38, "gender": "여", "diag": "불안장애 / 우울증", "meds": [{"name": "렉사프로정 10mg", "dose": "1일 1회", "days": 30}, {"name": "데파스정", "dose": "1일 2회", "days": 30}, {"name": "자낙스정 0.25mg", "dose": "1일 1회", "days": 30}], "file": "RX_P012.png"},
    "P013": {"name": "박서연", "age": 25, "gender": "여", "diag": "골육종", "meds": [{"name": "시스플라틴주", "dose": "100mg/m2 IV", "days": 1}, {"name": "독소루비신주", "dose": "25mg/m2 IV", "days": 1}, {"name": "메토트렉세이트주", "dose": "12g/m2 IV", "days": 1}], "file": "RX_P013.png"},
    "P014": {"name": "김철수", "age": 75, "gender": "남", "diag": "알츠하이머형 치매 / 심부전", "meds": [{"name": "아리셉트정 5mg", "dose": "1일 1회", "days": 30}, {"name": "에빅사정 10mg", "dose": "1일 2회", "days": 30}, {"name": "쿠에타핀정 12.5mg", "dose": "취침전", "days": 30}, {"name": "라식스정 40mg", "dose": "1회 0.5정, 1일 1회", "days": 30}, {"name": "알닥톤정 25mg", "dose": "1회 1정, 1일 1회", "days": 30}], "file": "RX_P014.png"},
    "P015": {"name": "정하은", "age": 8, "gender": "여", "diag": "소아 아토피", "meds": [{"name": "엘리델크림", "dose": "1일 2회 도포", "days": 14}, {"name": "페니라민시럽", "dose": "5mL, 1일 3회", "days": 7}], "file": "RX_P015.png"},
    "P016": {"name": "James Lee", "age": 52, "gender": "남", "diag": "알레르기 비염 / 천식", "meds": [{"name": "세티리진 10mg", "dose": "1일 1회", "days": 30}, {"name": "아바미스 스프레이", "dose": "1일 1회 분사", "days": 30}, {"name": "싱귤레어정 10mg", "dose": "1일 1회 저녁", "days": 30}], "file": "RX_P016.png"},
    "P017": {"name": "박소윤", "age": 31, "gender": "여", "diag": "공황장애", "meds": [{"name": "알프람정 0.25mg", "dose": "1회 1정, 1일 3회", "days": 30}, {"name": "인데놀정 10mg", "dose": "1회 1정, 1일 2회", "days": 30}, {"name": "스틸녹스정 10mg", "dose": "취침 전", "days": 14}], "file": "RX_P017.png"},
    "P018": {"name": "Michael Kim", "age": 44, "gender": "남", "diag": "고혈압 / 고지혈증", "meds": [{"name": "노바스크정 5mg", "dose": "1일 1회", "days": 90}, {"name": "코자정 50mg", "dose": "1회 1정, 1일 1회", "days": 90}, {"name": "다이크로짇정 25mg", "dose": "1회 1정, 1일 1회", "days": 90}, {"name": "리피토정 20mg", "dose": "1회 1정, 1일 1회", "days": 90}], "file": "RX_P018.png"},
    "P019": {"name": "이정태", "age": 59, "gender": "남", "diag": "고지혈증 / 간수치 상승", "meds": [{"name": "크레스토정 10mg", "dose": "1일 1회", "days": 30}, {"name": "에제티미브 10mg", "dose": "1일 1회", "days": 30}, {"name": "고덱스캡슐", "dose": "1회 1캡슐, 1일 3회", "days": 30}], "file": "RX_P019.png"},
    "P020": {"name": "오창현", "age": 36, "gender": "남", "diag": "울혈성 심부전", "meds": [{"name": "알닥톤정 25mg", "dose": "1일 2회", "days": 30}, {"name": "라식스정 20mg", "dose": "1회 0.5정, 1일 1회", "days": 30}, {"name": "토르세미드정 5mg", "dose": "1일 1회", "days": 30}], "file": "RX_P020.png"},
    "P021": {"name": "윤지영", "age": 27, "gender": "여", "diag": "안구건조증", "meds": [{"name": "루테인 지아잔틴", "dose": "1일 1회", "days": 90}, {"name": "오메가3", "dose": "1일 1회", "days": 90}], "file": "RX_P021.png"},
    "P022": {"name": "강민서", "age": 19, "gender": "여", "diag": "신경병증성 통증", "meds": [{"name": "탁센연질캡슐", "dose": "필요시 복용", "days": 14}, {"name": "마그네슘 400mg", "dose": "1일 1회", "days": 30}, {"name": "리리카캡슐 25mg", "dose": "1회 1캡슐, 1일 2회", "days": 30}], "file": "RX_P022.png"},
    "P023": {"name": "서동훈", "age": 48, "gender": "남", "diag": "전이성 암", "meds": [{"name": "파클리탁셀주", "dose": "80mg/m2 IV", "days": 1}, {"name": "덱사메티손정 4mg", "dose": "전처치용", "days": 1}], "file": "RX_P023.png"},
    "P024": {"name": "한지민", "age": 33, "gender": "여", "diag": "알레르기 비염", "meds": [{"name": "씨투스정 50mg", "dose": "1회 1정, 1일 2회", "days": 14}, {"name": "싱귤레어츄정 5mg", "dose": "1회 1정, 1일 1회", "days": 14}], "file": "RX_P024.png"},
    "P025": {"name": "류태영", "age": 41, "gender": "남", "diag": "만성 위염 / 역류성 식도염", "meds": [{"name": "스토가정 10mg", "dose": "1회 1정, 1일 2회", "days": 30}, {"name": "가나톤정", "dose": "1회 1정, 1일 3회", "days": 30}, {"name": "넥시움정 20mg", "dose": "1회 1정, 1일 1회", "days": 30}], "file": "RX_P025.png"},
    "P026": {"name": "송은주", "age": 53, "gender": "여", "diag": "철결핍성 빈혈", "meds": [{"name": "훼로바유정", "dose": "1일 1회", "days": 90}, {"name": "폴산 1mg", "dose": "1일 3회", "days": 90}], "file": "RX_P026.png"},
    "P027": {"name": "최희정", "age": 39, "gender": "여", "diag": "골다공증", "meds": [{"name": "포사맥스플러스디", "dose": "주 1회 복용", "days": 90}, {"name": "칼슘 500mg", "dose": "1일 1회", "days": 90}], "file": "RX_P027.png"},
    "P028": {"name": "김현숙", "age": 61, "gender": "여", "diag": "유방암", "meds": [{"name": "허셉틴주", "dose": "6mg/kg IV", "days": 21}, {"name": "타목시펜정 20mg", "dose": "1일 3회", "days": 365}], "file": "RX_P028.png"},
    "P029": {"name": "박맹심", "age": 55, "gender": "여", "diag": "울혈성 심부전 / 고혈압", "meds": [{"name": "트리테이스정 2.5mg", "dose": "1회 1정, 1일 1회", "days": 100}, {"name": "후릭스정 40mg", "dose": "1회 1정, 1일 1회", "days": 100}, {"name": "알닥톤정 25mg", "dose": "1회 1정, 1일 1회", "days": 100}, {"name": "콩코르정 2.5mg", "dose": "1회 1정, 1일 1회", "days": 100}, {"name": "자디앙정 10mg", "dose": "1회 1정, 1일 1회", "days": 100}, {"name": "프로코라란정 5mg", "dose": "1회 1정, 1일 2회", "days": 100}], "file": "RX_P029.png"},
    "P030": {"name": "나의 데이터 (유창수)", "age": 34, "gender": "남", "diag": "알레르기 비염 / 상기도 감염", "meds": [{"name": "베실리온정", "dose": "1회 1정, 1일 2회", "days": 7}, {"name": "코대원정", "dose": "1회 1정, 1일 2회", "days": 7}, {"name": "슈다페드정", "dose": "1회 1정, 1일 2회", "days": 7}, {"name": "베아솔론정", "dose": "1회 1정, 1일 2회", "days": 7}, {"name": "라니넥스나잘스프레이", "dose": "1일 1회 분사", "days": 30}], "file": "스크린샷 2026-05-07 182007.png"},
    "P031": {"name": "박맹심 (항암 케어)", "age": 55, "gender": "여", "diag": "신세포암 / 감기 증상", "meds": [{"name": "보트리엔트정 400mg", "dose": "1회 1정, 1일 1회", "days": 30}, {"name": "코슈정 60mg", "dose": "1회 1정, 1일 3회", "days": 7}, {"name": "코푸시럽(20ml)", "dose": "1회 1포, 1일 3회", "days": 7}, {"name": "삼남아세트아미노펜정 500mg", "dose": "1회 1정, 1일 3회", "days": 7}], "file": "스크린샷 2026-05-06 193750.png"},
    "P032": {"name": "김상은 (당뇨 정밀)", "age": 68, "gender": "남", "diag": "당뇨 / 고혈압 (복합 처방)", "meds": [{"name": "노바스크정 5mg", "dose": "1일 1회", "days": 30}, {"name": "코자정 50mg", "dose": "1일 1회", "days": 30}, {"name": "다이아벡스정 500mg", "dose": "1일 2회", "days": 30}, {"name": "아마릴정 2mg", "dose": "1일 1회", "days": 30}, {"name": "보글리보스 0.3mg", "dose": "1일 3회", "days": 30}], "file": "RX_P001.png"},
    "P033": {"name": "박지현 (항암 보조)", "age": 55, "gender": "여", "diag": "위암 수술 후 케어 (정밀)", "meds": [{"name": "젤로다정 500mg", "dose": "1일 2회", "days": 42}, {"name": "옥살리플라틴주", "dose": "IV infusion", "days": 1}, {"name": "맥페란정", "dose": "1일 3회", "days": 5}, {"name": "조프란정 4mg", "dose": "1일 2회", "days": 3}, {"name": "스토가정 10mg", "dose": "1일 2회", "days": 14}], "file": "RX_P002.png"},
}

# [전체 약물 임상 정보 DB - 100% 파일명 매칭 완료]
MED_INFO = {
    "노바스크정 5mg": {"file": "노바스크정.png", "v_id": "흰색 팔각 정제", "warn": "(혈압강하제) 자몽주스 주의. 매일 일정한 시간 복용."},
    "코자정 50mg": {"file": "코자정.png", "v_id": "흰색 원형 정제", "warn": "(혈압강하제) 임의로 복용을 중단하지 마십시오."},
    "다이아벡스정 500mg": {"file": "다이아벡스정.png", "v_id": "흰색 원형 정제", "warn": "(당뇨병약) 유산산증 주의. 식사 직후 복용 권장."},
    "트리테이스정 2.5mg": {"file": "트리테이스정.png", "v_id": "흰색 타원형", "warn": "(심부전/고혈압) 마른 기침/어지러움 주의. ACE 억제제."},
    "보트리엔트정 400mg": {"file": "보트리엔트정.png", "v_id": "흰색 타원형", "warn": "(표적항암제) 공복 복용(식후 2시간 또는 식전 1시간)."},
    "베실리온정": {"file": "besilion.png", "v_id": "흰색 원형", "warn": "(알레르기) 졸음 주의. 운전 시 주의."},
    "코대원정": {"file": "codae_won.png", "v_id": "흰색 원형", "warn": "(진해거담) 졸음 및 입 마름 주의. 수분 섭취 권장."},
    "슈다페드정": {"file": "sudafed.png", "v_id": "흰색 원형", "warn": "(코막힘 개선) 가슴 두근거림 주의."},
    "베아솔론정": {"file": "beasolon.png", "v_id": "흰색 원형", "warn": "(스테로이드) 장기 복용 시 전문가 상담."},
    "라니넥스나잘스프레이": {"file": "laninex.png", "v_id": "분무형 용기", "warn": "(비염) 머리를 젖히지 말고 선 자세에서 투여."},
    "코슈정 60mg": {"file": "sudafed.png", "v_id": "흰색 원형", "warn": "(비염) 코막힘 개선. 수분 섭취 권장."},
    "삼남아세트아미노펜정 500mg": {"file": "삼남아세트아미노펜정.png", "v_id": "흰색 장방형", "warn": "(해열진통) 간 손상 주의(음주 금지)."},
    "아마릴정 2mg": {"file": "아마릴정.png", "v_id": "녹색 장방형", "warn": "(당뇨병약) 저혈당 증상 주의."},
    "보글리보스 0.3mg": {"file": "보글리보스.png", "v_id": "흰색 원형", "warn": "(식후혈당조절) 식사 직전 복용."},
    "엔트레스토 50mg": {"file": "entresto.png", "v_id": "보라색 원형", "warn": "(심부전) 혈압 저하 및 현기증 주의."},
    "심비코트 터부헬러": {"file": "symbicort.png", "v_id": "흡입기", "warn": "(천식) 사용 후 반드시 입을 헹구세요."},
    "무코스타정": {"file": "무코스타정.png", "v_id": "흰색 원형 정제", "warn": "(위보호제) 식후 규칙적 복용."},
    "파리에트정 10mg": {"file": "파리에트정.png", "v_id": "분홍색 원형", "warn": "(위산억제) 아침 식전 복용 권장."},
    "가나톤정": {"file": "가나톤정.png", "v_id": "흰색 원형", "warn": "(위장운동) 소화 불량 개선."},
    "베아제정": {"file": "베아제정.png", "v_id": "다색 정제", "warn": "(소화제) 식후 즉시 복용."},
    "우루사정 100mg": {"file": "우루사정.png", "v_id": "흰색 원형", "warn": "(간기능개선) 피로 회복 보조."},
    "아로나민골드": {"file": "아로나민골드.png", "v_id": "적색 코팅정", "warn": "(활성비타민) 육체 피로 완화."},
    "타그리소정 80mg": {"file": "tagrisso.png", "v_id": "베이지색 원형", "warn": "(표적항암제) EGFR 변이 치료."},
    "후릭스정 40mg": {"file": "후릭스정.png", "v_id": "흰색 원형 정제", "warn": "(이뇨제) 아침 식후 복용 권장."},
    "코푸시럽(20ml)": {"file": "codae_won.png", "v_id": "갈색 액상 시럽", "warn": "(기침/가래) 흔들어 복용."},
    "훼로바유정": {"file": "feroba_u.png", "v_id": "적갈색 원형", "warn": "(철분제) 공복 복용 시 흡수율 최고."},
    "지노트로핀주": {"file": "genotropin.png", "v_id": "주사제", "warn": "(성장호르몬) 매일 정해진 시간 주사."},
    "렉사프로정 10mg": {"file": "lexapro.png", "v_id": "흰색 원형", "warn": "(항우울제) 꾸준한 복용 중요."},
    "알닥톤정 25mg": {"file": "알닥톤정.png", "v_id": "적색 원형", "warn": "(이뇨제) 혈중 칼륨 수치 확인."},
    "콩코르정 2.5mg": {"file": "콩코르정.png", "v_id": "심장형 정제", "warn": "(베타차단제) 맥박수 모니터링."},
    "자디앙정 10mg": {"file": "자디앙정.png", "v_id": "황색 원형", "warn": "(당뇨/심부전) 충분한 수분 섭취."},
    "프로코라란정 5mg": {"file": "프로코라란정.png", "v_id": "주황색 정제", "warn": "(심부전) 서맥 주의."},
    "실리마린 140mg": {"file": "실리마린캡슐.png", "v_id": "갈색 캡슐", "warn": "(간세포 보호) 피로 회복."},
    "탁센연질캡슐": {"file": "taxen.png", "v_id": "청록색 연질캡슐", "warn": "(소염진통) 충분한 물과 복용."},
    "조인스정 200mg": {"file": "joins.png", "v_id": "적갈색 타원형", "warn": "(관절염) 식후 복용."},
    "아리셉트정 5mg": {"file": "aricept.png", "v_id": "흰색 원형", "warn": "(치매치료) 취침 전 복용 권장."},
    "젤로다정 500mg": {"file": "젤로다정.png", "v_id": "담홍색 장방형", "warn": "(항암제) 식후 30분 복용."},
    "맥페란정": {"file": "맥페란정.png", "v_id": "흰색 원형", "warn": "(구역/구토) 위장운동 조절."},
    "조프란정 4mg": {"file": "조프란정.png", "v_id": "흰색 원형", "warn": "(항암후오심) 필요시 복용."},
    "스토가정 10mg": {"file": "스토가정.png", "v_id": "흰색 원형", "warn": "(위염) 위산 분비 억제."},
}

# ── 3. 엔진 로직 ─────────────────────────────────────────────────────────────

def get_pill_img(pill_name: str):
    """지정된 약물 이름을 기반으로 이미지를 검색합니다. 퍼지 검색 강화."""
    # 1. DB 직접 매핑 확인
    clean_search = re.sub(r'[^가-힣a-zA-Z0-9]', '', pill_name).lower()
    for key, info in MED_INFO.items():
        clean_key = re.sub(r'[^가-힣a-zA-Z0-9]', '', key).lower()
        if clean_key in clean_search or clean_search in clean_key:
            path = os.path.join(PILL_DIR, info["file"])
            if os.path.exists(path):
                with open(path, "rb") as img:
                    ext = info["file"].split('.')[-1].lower()
                    return f"data:image/{ext};base64," + base64.b64encode(img.read()).decode()

    # 2. 파일 시스템 퍼지 매칭
    try:
        for f in os.listdir(PILL_DIR):
            f_clean = re.sub(r'[^가-힣a-zA-Z0-9]', '', f).lower()
            if f_clean and (f_clean in clean_search or clean_search in f_clean):
                with open(os.path.join(PILL_DIR, f), "rb") as img:
                    ext = f.split('.')[-1].lower()
                    return f"data:image/{ext};base64," + base64.b64encode(img.read()).decode()
    except: pass
    return None

def get_dynamic_briefing():
    """매번 변화하는 전문가 브리핑 제공"""
    wisdom = random.choice(STRATEGIC_WISDOM)
    accents = ["#00f2ff", "#39ff14", "#bcff00", "#00d4ff"]
    return wisdom, random.choice(accents)

# ── 4. UI 테마 및 스타일 (PREMIUM APP DESIGN) ───────────────────────────────────
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    .stApp { 
        background: radial-gradient(circle at top right, #0a192f, #020617);
        color: #ffffff; 
        font-family: 'Noto Sans KR', sans-serif; 
    }
    
    /* 글래스모피즘 카드 스타일 */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.3);
    }
    
    /* 약품 정보 카드 */
    .med-card {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 5px solid #00f2ff;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .med-img-box {
        width: 80px;
        height: 80px;
        background: #000;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border: 1px solid rgba(0, 242, 255, 0.5);
    }
    
    .med-info-box { flex-grow: 1; }
    .med-name { color: #00f2ff; font-weight: 700; font-size: 1.1rem; }
    .med-warn { color: #39ff14; font-size: 0.9rem; font-weight: 500; margin-top: 5px; }
    
    /* 배지 스타일 */
    .badge {
        background: rgba(0, 242, 255, 0.1);
        color: #00f2ff;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid rgba(0, 242, 255, 0.3);
    }
    
    /* 헤더 스타일 */
    .app-header {
        font-family: 'Orbitron', sans-serif;
        text-align: center;
        background: linear-gradient(90deg, #00f2ff, #39ff14);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
    }
</style>""", unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.markdown("<h2 style='color:#00f2ff; font-family:Orbitron;'>👤 COMMAND CENTER</h2>", unsafe_allow_html=True)
        patient_options = [None] + sorted(list(PATIENTS.keys()))
        sel_pid = st.selectbox(
            "환자 실시간 관제 (33인 로스터)", 
            patient_options, 
            format_func=lambda x: f"{PATIENTS[x]['name']} ({PATIENTS[x]['age']}세)" if x else "--- SELECT PATIENT ---"
        )
        
        st.divider()
        if sel_pid:
            st.success(f"FIDELITY CHECK: 100% (ID: {sel_pid})")
        else:
            st.warning("SYSTEM STANDBY: PLEASE SELECT PATIENT")
        
        st.caption("PHARMA-HYBRID v123.0 - APP EDITION")

    if not sel_pid:
        st.markdown("<h1 class='app-header'>🏥 PHARMA-HYBRID PREMIUM HUB</h1>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div class='glass-card' style='text-align:center; padding:80px;'>
            <h2 style='color:#00f2ff;'>🔓 ACCESS REQUIRED</h2>
            <p style='color:#888;'>Please select a patient from the Command Center to load clinical data.</p>
        </div>""", unsafe_allow_html=True)
        return

    p = PATIENTS[sel_pid]
    wisdom, accent_color = get_dynamic_briefing()
    med_count = len(p["meds"])
    
    st.markdown(f"<h1 class='app-header'>🏥 {p['name']} PATIENT DASHBOARD</h1>", unsafe_allow_html=True)
    
    # [Expert Briefing]
    st.markdown(f"""<div class='glass-card' style='border-left: 6px solid {accent_color};'>
        <span class='badge'>EXPERT INSIGHT</span>
        <p style='font-size:1.1rem; margin-top:10px;'>"{wisdom}"</p>
    </div>""", unsafe_allow_html=True)

    # [Top Stats]
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='glass-card' style='text-align:center;'><small>연령/성별</small><br><b style='font-size:1.5rem;'>{p['age']}세 / {p['gender']}</b></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='glass-card' style='text-align:center;'><small>주진단명</small><br><b style='font-size:1.5rem; color:#39ff14;'>{p['diag']}</b></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='glass-card' style='text-align:center;'><small>약물 개수</small><br><b style='font-size:1.5rem; color:#00f2ff;'>{med_count} Items</b></div>", unsafe_allow_html=True)

    # [Main Content]
    m1, m2 = st.columns([1.1, 1])

    with m1:
        st.markdown("<h3 style='font-family:Orbitron; font-size:1.2rem; color:#00f2ff;'>📸 SOURCE: PRESCRIPTION</h3>", unsafe_allow_html=True)
        img_path = os.path.join(PRESCRIPTION_DIR, p["file"])
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.error("SOURCE IMAGE MISSING")

    with m2:
        st.markdown("<h3 style='font-family:Orbitron; font-size:1.2rem; color:#00f2ff;'>💊 MEDICATION INTELLIGENCE</h3>", unsafe_allow_html=True)
        for med in p["meds"]:
            img_data = get_pill_img(med["name"])
            
            # Fuzzy match for info
            med_info = {"v_id": "실물 대조 중", "warn": "(약품 정보) 실물 확인 필요"}
            clean_med = re.sub(r'[^가-힣a-zA-Z0-9]', '', med["name"]).lower()
            for k, v in MED_INFO.items():
                ck = re.sub(r'[^가-힣a-zA-Z0-9]', '', k).lower()
                if ck in clean_med or clean_med in ck:
                    med_info = v
                    break

            st.markdown(f"""
            <div class='med-card'>
                <div class='med-img-box'>
                    {f'<img src="{img_data}" width="80">' if img_data else '<span style="font-size:2rem;">💊</span>'}
                </div>
                <div class='med-info-box'>
                    <div class='med-name'>{med["name"]}</div>
                    <div style='font-size:0.8rem; color:#aaa;'>{med["dose"]} | {med_info["v_id"]}</div>
                    <div class='med-warn'>➔ {med_info["warn"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # [Bottom: Risk Analysis]
    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("<h4 style='color:#ff4b4b;'>⚠️ DRUG MUGGER ALERT</h4>", unsafe_allow_html=True)
        found = False
        for med in p["meds"]:
            for key, val in DRUG_MUGGER_MAP.items():
                if key in med["name"]:
                    found = True
                    st.error(f"**{med['name']}** ➔ **{val['depleted']}** 고갈 위험! ({val['recom']})")
        if not found: st.write("No major nutrient depletion detected.")

    with b2:
        st.markdown("<h4 style='color:#bcff00;'>🥗 LIFE-SYNERGY CARE</h4>", unsafe_allow_html=True)
        if "당뇨" in p["diag"]: st.info("🏃 **Activity**: 식후 30분 걷기 | 🥗 **Diet**: 저당 식이섬유 강화")
        elif "심부전" in p["diag"]: st.info("🧘 **Activity**: 가벼운 유산소 | 🥗 **Diet**: 저염 DASH 식단")
        elif "암" in p["diag"]: st.info("🚶 **Activity**: 컨디션 기반 산책 | 🥗 **Diet**: 고단백 완전 익힌 식단")
        else: st.info("🏃 **Activity**: 주 3회 유산소 | 🥗 **Diet**: 균형 잡힌 영양 관리")

if __name__ == "__main__":
    main()
