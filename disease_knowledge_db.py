# -*- coding: utf-8 -*-
"""
disease_knowledge_db.py
25개 한국 환자 질병 종합 의학 데이터베이스
NCCN, ESMO, 대한암학회, 대한의학회 기준 (2024-2025)

주의: 이 데이터는 교육 목적입니다.
실제 처방 변경은 반드시 담당 의사/약사 검증 필수!
"""

# ════════════════════════════════════════════════════════════════════════════
# 질병 데이터베이스 (25개 질병)
# ════════════════════════════════════════════════════════════════════════════

DISEASE_DB = {
    # 1. 비소세포폐암 (NSCLC) - EGFR 돌연변이
    "비소세포폐암": {
        "english_name": "Non-Small Cell Lung Cancer (NSCLC) - EGFR Mutation",
        "diagnosis": "EGFR L858R/19-Del 양성",
        "first_line_drugs": [
            {
                "name": "타세바정 (Erlotinib)",
                "dosage": "150mg",
                "frequency": "1일 1회",
                "timing": "식사와 상관없이 복용",
                "form": "정제",
                "notes": "매일 같은 시간에, 물과 함께"
            },
            {
                "name": "지오트립정 (Gefitinib)",
                "dosage": "250mg",
                "frequency": "1일 1회",
                "timing": "식사와 상관없이",
                "form": "정제",
                "notes": "공복/식후 모두 가능"
            }
        ],
        "second_line_drugs": [
            {
                "name": "오시머티닙 (Osimertinib, Tagrisso)",
                "dosage": "80mg",
                "frequency": "1일 1회",
                "timing": "식사와 상관없이",
                "form": "정제"
            }
        ],
        "injectables": [
            {
                "name": "베바시주마브 (Bevacizumab, Avastin)",
                "dosage": "15mg/kg IV",
                "frequency": "2주마다 또는 3주마다",
                "route": "정맥주사 (IV)",
                "duration": "진행 또는 독성까지"
            },
            {
                "name": "페메트렉시드 (Pemetrexed)",
                "dosage": "500mg/m²",
                "frequency": "3주마다",
                "route": "정맥주사",
                "notes": "비소세포폐암 유지 치료"
            }
        ],
        "diet": {
            "recommended": "고단백, 항염증 식단 (오메가-3, 항산화제 풍부)",
            "avoid": "카페인 과다, 자극적 음식, 흡연(재발 위험)",
            "specific": "녹차, 블루베리, 시금치, 연어, 견과류"
        },
        "fruits_vegetables": [
            "블루베리 (항산화)",
            "당근 (카로틴)",
            "브로콜리 (설포라판)",
            "시금치 (엽산)",
            "토마토 (라이코펜)",
            "포도 (폴리페놀)"
        ],
        "vitamins_safe": [
            "Vitamin D (1000-2000 IU/day)",
            "Vitamin C (500-1000mg/day, 천연 출처)",
            "셀레늄 (200mcg/day)",
            "오메가-3 (1000mg EPA+DHA/day)"
        ],
        "vitamins_avoid": [
            "고용량 Vitamin A (베타-카로틴 고용량 - 재발 위험 증가)",
            "고용량 E (항암 효과 감소 가능)"
        ],
        "exercise": {
            "aerobic": "주 3-5회, 중강도 (걷기, 수영), 30분/회",
            "strength": "주 2-3회, 가벼운 저항 운동",
            "notes": "폐 용량 감소 주의, 호흡 운동 권장"
        },
        "drug_interactions": [
            {
                "drug_pair": "Erlotinib + CYP3A4 저해제 (케토코나졸, 클래리스로마이신)",
                "interaction": "Erlotinib 혈중 농도 증가 → 독성 위험",
                "management": "용량 감소 또는 약물 변경"
            },
            {
                "drug_pair": "Erlotinib + 제산제",
                "interaction": "흡수 감소",
                "management": "최소 2시간 간격 복용"
            }
        ],
        "side_effects": [
            "피부 발진 (80%, 경미→중등도)",
            "설사 (50-60%)",
            "구역질, 피로",
            "간 효소 상승",
            "간질성 폐렴 (드물지만 심각)"
        ],
        "monitoring": [
            "흉부 CT: 3개월마다",
            "간 기능 검사: 매 2주",
            "피부 상태 평가: 매 방문",
            "폐 기능 검사: 증상 시"
        ],
        "papers": [
            "EGFR-NICE 2023: EGFR 돌연변이 NSCLC 치료 지침",
            "NCCN Guidelines 2024: Lung Cancer",
            "대한폐암학회 (KCLS) 진료지침"
        ]
    },

    # 2. 악성흑색종 (Metastatic Melanoma) - Stage III/IV, BRAF V600E
    "악성흑색종": {
        "english_name": "Malignant Melanoma - BRAF V600E Mutation, Stage III-IV",
        "diagnosis": "BRAF V600E 양성, 전이성",
        "first_line_drugs": [
            {
                "name": "달라팀 (Dabrafenib, Tafinlar)",
                "dosage": "150mg",
                "frequency": "1일 2회",
                "timing": "아침·저녁 (12시간 간격)",
                "form": "캡슐"
            },
            {
                "name": "메킹정 (Trametinib, Mekinist)",
                "dosage": "2mg",
                "frequency": "1일 1회",
                "timing": "식사와 관계없이",
                "form": "정제",
                "notes": "Dabrafenib과 함께 사용 (병용 요법)"
            }
        ],
        "injectables": [
            {
                "name": "니볼루맙 (Nivolumab, Opdivo)",
                "dosage": "3mg/kg IV",
                "frequency": "2주마다",
                "route": "정맥주사",
                "duration": "진행까지"
            },
            {
                "name": "이필리무맙 (Ipilimumab, Yervoy)",
                "dosage": "1mg/kg IV",
                "frequency": "3주마다 (4회)",
                "route": "정맥주사",
                "notes": "유도 요법, 니볼루맙과 병용"
            }
        ],
        "diet": {
            "recommended": "항염증 식단, 면역 강화 식품",
            "avoid": "알코올(면역 억제), 가공식품",
            "specific": "강황(터머릭), 생강, 마늘, 해산물"
        },
        "fruits_vegetables": [
            "당근 (항산화)",
            "빨간 파프리카 (비타민 C)",
            "브로콜리 (글루코시놀레이트)",
            "양파/마늘 (알리신)",
            "시금치 (루테인, 엽산)",
            "석류 (폴리페놀)"
        ],
        "vitamins_safe": [
            "Vitamin D (2000 IU/day)",
            "Vitamin C (500mg/day, 면역 지원)",
            "프로바이오틱스 (면역 조절)",
            "셀레늄 (200mcg/day)"
        ],
        "vitamins_avoid": [
            "고용량 항산화제 (면역 억제 가능)",
            "생강 과다 (항응고제와 상호작용)"
        ],
        "exercise": {
            "aerobic": "주 3-5회, 중강도, 30-45분",
            "strength": "주 2회, 저항 운동",
            "notes": "면역 기능 강화, 스트레스 감소"
        },
        "drug_interactions": [
            {
                "drug_pair": "Dabrafenib + CYP3A4 저해제",
                "interaction": "약물 혈중 농도 증가",
                "management": "용량 조절 또는 약물 변경"
            },
            {
                "drug_pair": "Nivolumab + 자가면역 질환 약물",
                "interaction": "자가면역 반응 악화",
                "management": "면역 기능 모니터링 강화"
            }
        ],
        "side_effects": [
            "피부 발진, 광민감성",
            "설사, 복부 불편",
            "피로, 근육통",
            "면역 관련 이상반응 (pneumonitis, 갑상선염)"
        ],
        "monitoring": [
            "PET-CT: 8-12주마다",
            "LDH, S100: 매 방문",
            "갑상선 기능: 매 4주",
            "피부 검진: 매 방문"
        ],
        "papers": [
            "NCCN Guidelines 2024: Melanoma",
            "대한피부과학회 (KDA) 흑색종 진료지침",
            "ASCO 2023: Immunotherapy in Melanoma"
        ]
    },

    # 3. 간세포암 (Hepatocellular Carcinoma) - BCLC Stage B
    "간세포암": {
        "english_name": "Hepatocellular Carcinoma (HCC) - BCLC Stage B",
        "diagnosis": "Barcelona Clinic Liver Cancer Stage B",
        "first_line_drugs": [
            {
                "name": "소라페닙 (Sorafenib, Nexavar)",
                "dosage": "400mg",
                "frequency": "1일 2회",
                "timing": "식사 30분 전 또는 2시간 후",
                "form": "정제",
                "notes": "매일 일정한 시간에"
            },
            {
                "name": "렌바티닙 (Lenvatinib, Lenvima)",
                "dosage": "12mg (체중 >60kg) 또는 8mg (<60kg)",
                "frequency": "1일 1회",
                "timing": "식사와 관계없이",
                "form": "캡슐"
            }
        ],
        "injectables": [
            {
                "name": "수라페닙 (Regorafenib)",
                "dosage": "160mg",
                "frequency": "1일 1회 (21일 투약, 7일 휴약)",
                "route": "경구",
                "notes": "2차 선택약"
            },
            {
                "name": "카바진티닙 (Cabozantinib)",
                "dosage": "60mg",
                "frequency": "1일 1회",
                "route": "경구",
                "notes": "2차 선택약"
            }
        ],
        "diet": {
            "recommended": "저염, 저지방, 단백질 적절량",
            "avoid": "알코올(간 손상), 염장 음식, 과도한 염분",
            "specific": "두유, 생선, 살코기, 신선 야채"
        },
        "fruits_vegetables": [
            "브로콜리 (설포라판, 간 해독)",
            "당근 (카로티노이드)",
            "시금치 (글루타치온)",
            "수박 (라이코펜)",
            "자몽 (나린진)",
            "양배추 (인돌)"
        ],
        "vitamins_safe": [
            "Silymarin (밀크씨슬, 간 보호)",
            "NAC (N-acetylcysteine, 항산화)",
            "Vitamin E (간 보호, 400IU/day)",
            "오메가-3 (간 지방 감소)"
        ],
        "vitamins_avoid": [
            "고용량 철분 (철 축적 간독성)",
            "비타민 A (간독성 위험)",
            "알코올 관련 보충제"
        ],
        "exercise": {
            "aerobic": "주 3-4회, 저강도 (걷기), 20-30분",
            "strength": "주 1-2회, 매우 가벼운 운동",
            "notes": "간 기능 저하 주의, 과로 피할 것"
        },
        "drug_interactions": [
            {
                "drug_pair": "Sorafenib + CYP3A4 저해제",
                "interaction": "혈중 농도 증가",
                "management": "용량 감소"
            },
            {
                "drug_pair": "Sorafenib + 와파린",
                "interaction": "출혈 위험 증가",
                "management": "INR 모니터링"
            }
        ],
        "side_effects": [
            "손발 피부반응 증후군 (HFSR)",
            "설사, 피로",
            "혈압 상승",
            "간 기능 악화 가능"
        ],
        "monitoring": [
            "AFP, 간 초음파: 매 4-8주",
            "간 기능 검사 (AST, ALT, 빌리루빈): 매 2주",
            "혈압: 매 방문",
            "복부 CT/MRI: 매 8-12주"
        ],
        "papers": [
            "NCCN Guidelines 2024: Hepatocellular Carcinoma",
            "대한간학회 (KASL) 간세포암 진료지침",
            "ESMO 2023: HCC Treatment Guidelines"
        ]
    },

    # 4. 전이성 대장암 (Metastatic Colorectal Cancer)
    "전이성대장암": {
        "english_name": "Metastatic Colorectal Cancer (mCRC)",
        "diagnosis": "Stage IV, 원격 전이",
        "first_line_drugs": [
            {
                "name": "5-플루오로우라실 (5-FU)",
                "dosage": "400mg/m² bolus + 2400mg/m² 46h infusion",
                "frequency": "2주마다 (FOLFIRI, FOLFOX 병용)",
                "timing": "정맥주사",
                "form": "액제",
                "notes": "Leucovorin과 병용"
            },
            {
                "name": "카페시타빈 (Capecitabine, Xeloda)",
                "dosage": "1250mg/m²",
                "frequency": "1일 2회 (14일 투약, 7일 휴약)",
                "timing": "식후 30분 내",
                "form": "정제"
            }
        ],
        "injectables": [
            {
                "name": "옥살리플라틴 (Oxaliplatin)",
                "dosage": "85mg/m²",
                "frequency": "2주마다",
                "route": "정맥주사 (2시간)",
                "notes": "FOLFOX 요법의 일부"
            },
            {
                "name": "이리노테칸 (Irinotecan, CPT-11)",
                "dosage": "180mg/m²",
                "frequency": "2주마다",
                "route": "정맥주사 (90분)",
                "notes": "FOLFIRI 요법의 일부"
            },
            {
                "name": "베바시주마브 (Bevacizumab)",
                "dosage": "5-10mg/kg",
                "frequency": "2주마다 또는 3주마다",
                "route": "정맥주사",
                "notes": "항혈관신생, 화학요법과 병용"
            }
        ],
        "diet": {
            "recommended": "소화하기 쉬운 음식, 충분한 수분",
            "avoid": "높은 지방, 자극적 음식, 과도한 섬유질(설사 악화)",
            "specific": "죽, 흰쌀, 알레르기 없는 생선"
        },
        "fruits_vegetables": [
            "바나나 (칼륨, 에너지)",
            "당근 (삶은 것, 부드러움)",
            "호박 (부드러운 식감)",
            "토마토 (라이코펜, 항산화)",
            "블루베리 (항산화)",
            "딸기 (비타민 C)"
        ],
        "vitamins_safe": [
            "Vitamin B-complex (에너지 대사, 400mcg B12 + 800mcg 엽산)",
            "Vitamin C (에너지, 500mg/day)",
            "Zinc (200-400mg/day, 점막 보호)",
            "Glutamine (장 무결성 보호)"
        ],
        "vitamins_avoid": [
            "고용량 항산화제 (화학요법 효과 감소)",
            "고용량 E (출혈 위험 증가 가능)"
        ],
        "exercise": {
            "aerobic": "주 3-4회, 저-중강도, 20-30분",
            "strength": "주 1-2회, 가벼운 운동",
            "notes": "치료 일주일 후부터, 피로 주의"
        },
        "drug_interactions": [
            {
                "drug_pair": "Capecitabine + Warfarin",
                "interaction": "출혈 위험 증가",
                "management": "INR 모니터링"
            },
            {
                "drug_pair": "Irinotecan + UGT1A1 억제제",
                "interaction": "독성 증가",
                "management": "UGT1A1 유전자 검사 (호모자이고스 *28)"
            },
            {
                "drug_pair": "5-FU + Allopurinol",
                "interaction": "5-FU 독성 증가",
                "management": "약물 변경 고려"
            }
        ],
        "side_effects": [
            "구역질, 구토, 식욕 부진",
            "설사 또는 변비",
            "골수 억제 (빈혈, 감염 위험)",
            "신경병증 (손발 저림)",
            "점막염"
        ],
        "monitoring": [
            "CBC: 매 치료 전",
            "간 기능, 신 기능: 매 2주",
            "CEA: 매 6-8주",
            "복부 CT: 매 8-12주"
        ],
        "papers": [
            "NCCN Guidelines 2024: Colorectal Cancer",
            "대한대장항문학회 (KSRS) 진료지침",
            "ESMO 2023: mCRC Treatment"
        ]
    },

    # 5. CML (Chronic Myeloid Leukemia)
    "만성골수성백혈병": {
        "english_name": "Chronic Myeloid Leukemia (CML) - BCR-ABL Positive",
        "diagnosis": "BCR-ABL t(9;22) 양성",
        "first_line_drugs": [
            {
                "name": "글리벡정 (Imatinib, Gleevec)",
                "dosage": "400mg",
                "frequency": "1일 1회",
                "timing": "식사 중 또는 식사 직후",
                "form": "정제",
                "notes": "매일 같은 시간에, 넉넉한 물과 함께"
            },
            {
                "name": "대세티닙 (Dasatinib, Sprycel)",
                "dosage": "100mg",
                "frequency": "1일 1회",
                "timing": "식사와 관계없이",
                "form": "정제"
            },
            {
                "name": "닐로티닙 (Nilotinib, Tasigna)",
                "dosage": "300mg",
                "frequency": "1일 2회",
                "timing": "식사 2시간 전 또는 2시간 후",
                "form": "캡슐",
                "notes": "식사와 함께 하면 안됨"
            }
        ],
        "diet": {
            "recommended": "균형 잡힌 영양식, 고단백",
            "avoid": "자몽 주스 (약물 상호작용), 카페인 과다, 알코올",
            "specific": "저지방 단백질, 신선 과일, 야채"
        },
        "fruits_vegetables": [
            "블루베리 (항산화)",
            "시금치 (엽산)",
            "브로콜리 (설포라판)",
            "당근 (카로티노이드)",
            "오렌지 (비타민 C)",
            "토마토 (라이코펜)"
        ],
        "vitamins_safe": [
            "Vitamin D (1000-2000 IU/day, 골 건강)",
            "Folic acid (1-5mg/day)",
            "Vitamin B12 (500-1000mcg/day)",
            "칼슘 (1000-1200mg/day)"
        ],
        "vitamins_avoid": [
            "고용량 비타민 C (산화 스트레스 증가)",
            "자몽 추출물 (CYP3A4 저해)"
        ],
        "exercise": {
            "aerobic": "주 3-5회, 중강도, 30분",
            "strength": "주 2-3회, 골 건강 운동",
            "notes": "골다공증 위험 주의"
        },
        "drug_interactions": [
            {
                "drug_pair": "Imatinib + 자몽 주스",
                "interaction": "혈중 농도 급증 → 독성",
                "management": "자몽 완전히 피할 것"
            },
            {
                "drug_pair": "Nilotinib + CYP3A4 저해제",
                "interaction": "혈중 농도 증가",
                "management": "용량 조절"
            },
            {
                "drug_pair": "TKI + Acetaminophen (과다)",
                "interaction": "간 독성 증가",
                "management": "저용량 또는 대체약 사용"
            }
        ],
        "side_effects": [
            "근육 경련, 관절통",
            "수액 저류 (다리 부종, 체중 증가)",
            "구역질, 설사",
            "골다공증 위험",
            "간 또는 신 기능 이상"
        ],
        "monitoring": [
            "BCR-ABL 정량 RT-PCR: 매 3개월",
            "혈액 검사 (CBC, 생화학): 매 2주 (초기), 매 3개월 (유지)",
            "간 기능 검사: 매 3개월",
            "칼슘/비타민D: 매 6개월"
        ],
        "papers": [
            "NCCN Guidelines 2024: CML",
            "European LeukemiaNet (ELN) 2024 Recommendations",
            "대한혈액학회 CML 진료지침"
        ]
    },

    # 6. HER2+ 유방암 (Early Stage)
    "HER2양성유방암": {
        "english_name": "HER2-Positive Breast Cancer (Early Stage)",
        "diagnosis": "HER2 3+ (IHC) 또는 HER2:CEP17 ≥2.0 (FISH)",
        "first_line_drugs": [
            {
                "name": "타목시펜 (Tamoxifen)",
                "dosage": "20mg",
                "frequency": "1일 1회",
                "timing": "식사와 관계없이",
                "form": "정제"
            },
            {
                "name": "페마라정 (Letrozole)",
                "dosage": "2.5mg",
                "frequency": "1일 1회",
                "timing": "식사와 관계없이",
                "form": "정제"
            }
        ],
        "injectables": [
            {
                "name": "허셉틴 (Trastuzumab, Herceptin)",
                "dosage": "6mg/kg IV",
                "frequency": "3주마다",
                "route": "정맥주사",
                "duration": "1년"
            },
            {
                "name": "페르투주맙 (Pertuzumab, Perjeta)",
                "dosage": "840mg (로딩) → 420mg",
                "frequency": "3주마다",
                "route": "정맥주사",
                "notes": "Trastuzumab과 병용"
            }
        ],
        "diet": {
            "recommended": "식물 기반 식단, 저지방, 고섬유질",
            "avoid": "알코올(호르몬 증가), 가공육, 과체중",
            "specific": "십자화과 야채, 베리류, 통곡물"
        },
        "fruits_vegetables": [
            "브로콜리 (인돌-3-카비놀)",
            "양배추 (글루코시놀레이트)",
            "베리류 (폴리페놀)",
            "당근 (베타-카로틴)",
            "시금치 (항산화)",
            "토마토 (라이코펜)"
        ],
        "vitamins_safe": [
            "Vitamin D (2000 IU/day)",
            "Vitamin B-complex",
            "오메가-3 (항염증)",
            "CoQ10 (심 보호, 심독성 방지)"
        ],
        "vitamins_avoid": [
            "높은 용량 비타민 C (호르몬 민감성에 영향)",
            "에스트로겐 함유 보충제",
            "성 호르몬 유사 식물성 에스트로겐(과다)"
        ],
        "exercise": {
            "aerobic": "주 4-5회, 중강도, 30-45분",
            "strength": "주 2-3회, 저항 운동",
            "notes": "심 건강 모니터링 필수"
        },
        "drug_interactions": [
            {
                "drug_pair": "Tamoxifen + CYP2D6 억제제 (파록세틴)",
                "interaction": "Tamoxifen 활성화 감소",
                "management": "약물 변경 고려"
            },
            {
                "drug_pair": "Trastuzumab + Anthracycline",
                "interaction": "심독성 위험 증가",
                "management": "심 기능 모니터링 (EF 강화)"
            }
        ],
        "side_effects": [
            "핫플래시, 질 건조증, 성욕 감소",
            "근골격계 통증",
            "심독성 (심부전, EF 저하)",
            "신경병증 (Pertuzumab)"
        ],
        "monitoring": [
            "좌심실 분출률 (EF, 초음파): 베이스라인, 3개월, 6개월",
            "호르몬 수치: 매 3개월",
            "종양 표지자 (CEA, CA 15-3): 매 3-6개월",
            "흉부 X선/CT: 매 6-12개월"
        ],
        "papers": [
            "NCCN Guidelines 2024: Breast Cancer",
            "대한유방암학회 (KBCS) 진료지침",
            "ESMO 2023: HER2+ Breast Cancer"
        ]
    },

    # 7. 소아백혈병 + 천식
    "소아백혈병천식": {
        "english_name": "Pediatric Acute Lymphoblastic Leukemia (ALL) + Asthma",
        "diagnosis": "ALL 치료 중, 동반 천식",
        "first_line_drugs": [
            {
                "name": "다우노루비신 (Daunorubicin)",
                "dosage": "25mg/m²",
                "frequency": "주 1회 (4주)",
                "timing": "정맥주사",
                "form": "액제",
                "notes": "소아 용량"
            },
            {
                "name": "아스파라기나제 (Asparaginase)",
                "dosage": "6000IU/m²",
                "frequency": "3회/주",
                "timing": "정맥주사 또는 근육주사",
                "notes": "알레르기 주의"
            },
            {
                "name": "메토트렉세이트 (Methotrexate)",
                "dosage": "12mg/m² (척수강 주입)",
                "frequency": "2-4주마다",
                "timing": "척수강/정맥주사",
                "notes": "신경 예방 요법"
            }
        ],
        "asthma_drugs": [
            {
                "name": "살부타몰 (Albuterol, Ventolin) - 흡입",
                "dosage": "100-200mcg",
                "frequency": "필요시",
                "timing": "급성 증상",
                "notes": "응급용"
            },
            {
                "name": "플루티카손 + 살메테롤 (Advair)",
                "dosage": "45/21mcg 또는 110/21mcg",
                "frequency": "1일 2회",
                "timing": "아침·저녁",
                "notes": "유지 요법"
            }
        ],
        "diet": {
            "recommended": "면역 강화 식단, 고단백",
            "avoid": "인공 색소, 방부제, 우유(천식 악화 가능)",
            "specific": "달걀, 생선, 과일, 야채"
        },
        "fruits_vegetables": [
            "오렌지 (비타민 C, 면역)",
            "딸기 (항산화)",
            "블루베리 (항염증)",
            "브로콜리 (면역)",
            "당근",
            "포도"
        ],
        "vitamins_safe": [
            "Vitamin D (600-1000 IU/day, 소아)",
            "Vitamin C (45-75mg/day, 면역)",
            "Zinc (3-8mg/day)",
            "Probiotics (면역 조절)"
        ],
        "vitamins_avoid": [
            "과도한 철분 (독성 증가)",
            "St. John's Wort (약물 상호작용)"
        ],
        "exercise": {
            "aerobic": "의료진 승인 후, 천천히 시작, 저강도",
            "strength": "회복 후, 매우 가벼운 운동",
            "notes": "천식 악화 주의, 운동 유도성 천식 고려"
        },
        "drug_interactions": [
            {
                "drug_pair": "Methotrexate + NSAIDs",
                "interaction": "신 독성 증가",
                "management": "NSAIDs 피할 것"
            },
            {
                "drug_pair": "Asparaginase + 살부타몰",
                "interaction": "직접 상호작용 없음 (별도 모니터링)",
                "management": "증상 모니터링"
            },
            {
                "drug_pair": "화학요법 + 천식약",
                "interaction": "면역 억제 주의",
                "management": "감염 스크리닝 강화"
            }
        ],
        "side_effects": [
            "구역질, 구토, 식욕 부진",
            "탈모",
            "골수 억제",
            "신경독성 (고용량 MTX)",
            "심독성 (Daunorubicin)"
        ],
        "monitoring": [
            "CBC: 매 1-2주",
            "간 기능, 신 기능: 매 2주",
            "심 기능 (EF): 매 2-3개월",
            "CSF (척수액) 세포: 치료별",
            "천식 증상: 매 방문"
        ],
        "papers": [
            "COG (Children's Oncology Group) ALL 치료 프로토콜",
            "NCCN Guidelines: ALL (소아)",
            "Global Initiative for Asthma (GINA) 2024"
        ]
    },

    # 8. ALS + 중증근무력증
    "ALS중증근무력증": {
        "english_name": "Amyotrophic Lateral Sclerosis (ALS) + Myasthenia Gravis (MG)",
        "diagnosis": "ALS (상위/하위 운동 신경원 징후) + MG (항아세틸콜린 수용체 항체 양성)",
        "first_line_drugs": [
            {
                "name": "릴루졸 (Riluzole, Rilutek)",
                "dosage": "50mg",
                "frequency": "1일 2회",
                "timing": "식사와 관계없이",
                "form": "정제",
                "notes": "ALS 진행 지연"
            },
            {
                "name": "에다라본 (Edaravone, Radicut)",
                "dosage": "60mg IV",
                "frequency": "매일 14일, 휴약 14일",
                "timing": "정맥주사",
                "notes": "항산화, ALS 진행 지연"
            }
        ],
        "myasthenia_drugs": [
            {
                "name": "피리스티그민 (Pyridostigmine, Mestinon)",
                "dosage": "60mg",
                "frequency": "1일 3-4회",
                "timing": "식사 30분 전",
                "form": "정제",
                "notes": "아세틸콜린 에스테라제 억제제"
            },
            {
                "name": "아자티오프린 (Azathioprine)",
                "dosage": "1-2mg/kg",
                "frequency": "1일 1회",
                "timing": "식사와 함께",
                "form": "정제",
                "notes": "**CRITICAL: Allopurinol과 금지**"
            }
        ],
        "diet": {
            "recommended": "부드러운 음식, 충분한 영양, 삼킴 기능에 맞춘 식이",
            "avoid": "단단한 음식, 카페인(근육 악화), 알코올",
            "specific": "죽, 으깬 음식, 요거트, 스무디"
        },
        "fruits_vegetables": [
            "바나나 (칼륨, 부드러움)",
            "복숭아 (부드러움)",
            "당근 (삶은 것)",
            "호박 (부드러움)",
            "딸기",
            "블루베리"
        ],
        "vitamins_safe": [
            "CoQ10 (200-300mg/day, 신경 보호)",
            "오메가-3 (항염증)",
            "Vitamin E (400 IU/day)",
            "Vitamin D (2000 IU/day)"
        ],
        "vitamins_avoid": [
            "Allopurinol (Azathioprine과 금지!) - 뼈다귀 모양 독성 위험",
            "높은 용량 아미노산 (근 약화 악화)"
        ],
        "exercise": {
            "aerobic": "매우 가벼운 활동, 짧은 시간 (10-15분)",
            "strength": "피해야 함 (근육 악화)",
            "notes": "물리 치료, 호흡 운동, 삼킴 훈련"
        },
        "drug_interactions": [
            {
                "drug_pair": "Azathioprine + Allopurinol",
                "interaction": "⚠️ CRITICAL: 뼈다귀 모양 독성 (SCAR), 간 손상",
                "management": "절대 금지 - 약사 직접 확인 필수, Febuxostat 대체 가능"
            },
            {
                "drug_pair": "Pyridostigmine + 마취제",
                "interaction": "마비제 효과 연장",
                "management": "수술 전 의료진에 고지"
            },
            {
                "drug_pair": "ALS약 + 마그네슘 과다",
                "interaction": "근육 약화 악화",
                "management": "식단 조절"
            }
        ],
        "side_effects": [
            "메스꺼움, 구토, 복부 불편",
            "근육 경련, 근무력",
            "호흡곤란",
            "골수 억제 (Azathioprine)",
            "간 독성"
        ],
        "monitoring": [
            "근 강도 검사 (MRC, QMG): 매 1-2개월",
            "간 기능, CBC: 매 1-2개월 (Azathioprine 복용 시)",
            "폐 기능 검사 (FVC): 매 3개월",
            "신경계 영상 (MRI): 증상 진행 시",
            "항체 검사: 매 6-12개월"
        ],
        "papers": [
            "American Academy of Neurology (AAN) ALS 진료지침",
            "Myasthenia Gravis Foundation of America 권장사항",
            "대한신경과학회 ALS, MG 진료지침"
        ]
    },

    # 9. 진행성 대장암 + 위염
    "진행성대장암위염": {
        "english_name": "Advanced Colorectal Cancer + Chronic Gastritis",
        "diagnosis": "Stage IIIB-IV CRC, H. pylori+ 또는 자가면역 위염",
        "first_line_drugs": [
            {
                "name": "FOLFOX (5-FU + Leucovorin + Oxaliplatin)",
                "dosage": "복합 프로토콜",
                "frequency": "2주마다",
                "timing": "정맥주사",
                "notes": "상세: vision_engine.py 참조"
            }
        ],
        "gastritis_drugs": [
            {
                "name": "오메프라졸 (Omeprazole, 젤로셀정)",
                "dosage": "20mg",
                "frequency": "1일 1회",
                "timing": "아침 공복",
                "form": "정제",
                "notes": "식사 30분 전"
            },
            {
                "name": "판토프라졸 (Pantoprazole)",
                "dosage": "40mg",
                "frequency": "1일 1회",
                "timing": "아침 공복",
                "form": "정제"
            },
            {
                "name": "헬리코박터 제균제 (H. pylori 양성일 경우)",
                "dosage": "복합 요법 (PPI + 항생제 2종)",
                "frequency": "10-14일",
                "timing": "식사와 함께",
                "notes": "예: Omeprazole + Amoxicillin + Clarithromycin"
            }
        ],
        "diet": {
            "recommended": "부드럽고 소화하기 쉬운 음식",
            "avoid": "매운 음식, 카페인, 알코올, 고지방, 산성 음식",
            "specific": "흰쌀, 삶은 채소, 저지방 단백질, 흰살 생선"
        },
        "fruits_vegetables": [
            "호박 (부드러운 삶은 것)",
            "당근 (삶은 것)",
            "브로콜리 (익힌 것, 부드러움)",
            "바나나 (위 보호)",
            "수박 (순한 산성)",
            "파파야 (소화 효소)"
        ],
        "vitamins_safe": [
            "Vitamin B12 (500-1000mcg/day, PPI 사용 시 흡수 감소)",
            "Vitamin D (1000-2000 IU/day)",
            "Calcium (1000mg/day, PPI 사용 시)",
            "L-Glutamine (위 점막 보호)"
        ],
        "vitamins_avoid": [
            "높은 산성 비타민 C (위산 자극)",
            "철분 과다 (위 자극)",
            "NSAIDs (위염 악화)"
        ],
        "exercise": {
            "aerobic": "주 3-4회, 저-중강도, 20-30분",
            "strength": "주 1회, 가벼운 운동",
            "notes": "위 자극 주의, 식후 2시간 경과 후"
        },
        "drug_interactions": [
            {
                "drug_pair": "PPI + Clopidogrel",
                "interaction": "Clopidogrel 활성화 감소",
                "management": "Pantoprazole 사용 (CYP2C19 상호작용 적음)"
            },
            {
                "drug_pair": "Chemotherapy + PPI",
                "interaction": "특정 약물 흡수 감소 (Imatinib 등)",
                "management": "투약 시간 간격 조절"
            },
            {
                "drug_pair": "Clarithromycin + Omeprazole",
                "interaction": "Omeprazole 혈중 농도 증가",
                "management": "용량 조절"
            }
        ],
        "side_effects": [
            "구역질, 구토, 복부 불편",
            "설사 또는 변비",
            "비타민 B12 결핍 (PPI 장기 사용)",
            "골다공증 위험 (PPI 장기 사용)",
            "간질성 신염 (드물음)"
        ],
        "monitoring": [
            "CBC, 간 기능: 매 치료 전",
            "신 기능: 매 2주",
            "B12 수치: 매 6개월 (PPI 장기 사용 시)",
            "H. pylori 제균 확인: 4주 후 (urea breath test)"
        ],
        "papers": [
            "American Gastroenterological Association (AGA) PPI 지침",
            "대한소화기병학회 위염, PPI 진료지침",
            "NCCN mCRC Guidelines"
        ]
    },

    # 10. 선천성 심질환 (Tetralogy of Fallot, 수술 후)
    "선천성심질환": {
        "english_name": "Congenital Heart Disease (Tetralogy of Fallot, Post-Op)",
        "diagnosis": "TOF 근본적 수정술 후, 잔여 병변 추적",
        "first_line_drugs": [
            {
                "name": "푸로세미드 (Furosemide, 라식스정)",
                "dosage": "10-20mg",
                "frequency": "1일 1회",
                "timing": "아침 (이뇨 작용)",
                "form": "정제"
            },
            {
                "name": "시나프릴 (Enalapril, ACE 억제제)",
                "dosage": "2.5-5mg",
                "frequency": "1일 1-2회",
                "timing": "식사와 관계없이",
                "form": "정제",
                "notes": "심실 기능 보호"
            },
            {
                "name": "아스피린 (아동용 저용량)",
                "dosage": "3-5mg/kg",
                "frequency": "1일 1회",
                "timing": "식사 후",
                "form": "정제 또는 씹는약",
                "notes": "혈전증 예방"
            }
        ],
        "diet": {
            "recommended": "저염, 심장 건강식, 적절한 수분",
            "avoid": "과도한 염분, 카페인, 고지방 음식",
            "specific": "저지방 생선, 닭가슴살, 우유, 치즈"
        },
        "fruits_vegetables": [
            "바나나 (칼륨, 수액 균형)",
            "당근 (항산화)",
            "브로콜리 (엽산)",
            "시금치 (마그네슘, 칼륨)",
            "딸기 (항산화)",
            "포도 (폴리페놀)"
        ],
        "vitamins_safe": [
            "Vitamin D (600 IU/day, 소아)",
            "칼슘 (1000-1200mg/day)",
            "마그네슘 (200-400mg/day, 심 리듬)",
            "오메가-3 (항염증)"
        ],
        "vitamins_avoid": [
            "고용량 비타민 E (출혈 위험)",
            "과도한 나트륨 (수액 저류)"
        ],
        "exercise": {
            "aerobic": "의료진 승인 후, 점진적 증가, 중강도",
            "strength": "제한적, 복부 압력 피할 것",
            "notes": "운동 스트레스 테스트 후 진행"
        },
        "drug_interactions": [
            {
                "drug_pair": "ACE 억제제 + 칼륨 보충제",
                "interaction": "고칼륨혈증 위험",
                "management": "칼륨 수치 모니터링"
            },
            {
                "drug_pair": "Furosemide + NSAIDs",
                "interaction": "신 기능 악화",
                "management": "NSAIDs 피할 것"
            }
        ],
        "side_effects": [
            "탈진, 저혈압 (이뇨제)",
            "건성 기침 (ACE 억제제)",
            "저칼륨혈증 (이뇨제)",
            "부정맥 (심장 민감성)"
        ],
        "monitoring": [
            "심 기능 (EF, 초음파): 매 6-12개월",
            "혈압: 매 방문",
            "전해질 (K, Mg, Ca): 매 3개월",
            "심전도: 매 6-12개월",
            "운동 능력: 연 1회"
        ],
        "papers": [
            "American Academy of Pediatrics (AAP) CHD 추적 권장사항",
            "2024 AHA/ACC CHD Guidelines",
            "대한심장학회 선천성 심질환 진료지침"
        ]
    },

    # 11. 제1형 당뇨병 + ADHD
    "제1형당뇨병ADHD": {
        "english_name": "Type 1 Diabetes Mellitus + Attention-Deficit/Hyperactivity Disorder",
        "diagnosis": "T1DM (인슐린 의존), ADHD (혼합형)",
        "diabetes_drugs": [
            {
                "name": "인슐린 글라르긴 (Insulin Glargine, Lantus)",
                "dosage": "체중에 따라 개별화 (예: 10-20 IU)",
                "frequency": "1일 1회",
                "timing": "저녁 (자기 전)",
                "form": "주사",
                "notes": "기저 인슐린 (장시간)"
            },
            {
                "name": "인슐린 리스프로 (Insulin Lispro, Humalog)",
                "dosage": "식사 탄수화물에 따라 (예: 1 IU per 10-15g carb)",
                "frequency": "식사 시마다 3-4회",
                "timing": "식사 직전 15분",
                "form": "주사",
                "notes": "빠른 인슐린 (식후 혈당)"
            }
        ],
        "adhd_drugs": [
            {
                "name": "메틸페니데이트 (Methylphenidate, 리탈린)",
                "dosage": "5-10mg",
                "frequency": "1일 2회",
                "timing": "아침, 점심 (자기 전 피할 것)",
                "form": "정제"
            },
            {
                "name": "암페타민 (Amphetamine, 에델)")  # 또는 Adderall
                "dosage": "5mg",
                "frequency": "1일 1-2회",
                "timing": "아침, 필요시 정오",
                "form": "정제"
            }
        ],
        "diet": {
            "recommended": "저혈당지수(GI) 탄수화물, 균형 영양",
            "avoid": "고GI 음식, 단순 당분, 자극적 음식(ADHD 악화)",
            "specific": "통곡물, 콩, 저지방 단백질, 신선 과일·채소"
        },
        "fruits_vegetables": [
            "사과 (저GI, 섬유질)",
            "베리류 (항산화, 저GI)",
            "당근 (부분적 저GI)",
            "브로콜리 (섬유질)",
            "시금치 (미네랄)",
            "통곡물 귀리 (높은 섬유질)"
        ],
        "vitamins_safe": [
            "Vitamin D (600-1000 IU/day)",
            "Chromium (200mcg/day, 혈당 조절)",
            "Cinnamon (혈당 지원, 0.5-1g/day)",
            "오메가-3 (신경 건강)"
        ],
        "vitamins_avoid": [
            "과도한 카페인 (ADHD 악화, 혈당 변동)",
            "자극 보충제 (ADHD 약물과 상호작용)",
            "고용량 비타민 C (산화 스트레스)"
        ],
        "exercise": {
            "aerobic": "주 5회, 중강도, 30분",
            "strength": "주 2-3회, 저항 운동",
            "notes": "저혈당 위험 주의, 간식 준비, 혈당 모니터링"
        },
        "drug_interactions": [
            {
                "drug_pair": "ADHD 자극제 + 특정 항우울제",
                "interaction": "심박수 증가, 혈압 상승",
                "management": "혈압 모니터링"
            },
            {
                "drug_pair": "인슐린 + ADHD 자극제",
                "interaction": "대사율 변화 → 저혈당 위험 증가",
                "management": "혈당 모니터링 강화"
            },
            {
                "drug_pair": "인슐린 + 알코올 (청소년)",
                "interaction": "심한 저혈당 위험",
                "management": "완전 회피"
            }
        ],
        "side_effects": [
            "저혈당 (두근거림, 식은땀, 혼란)",
            "ADHD 자극제: 불면증, 식욕 부진, 불안",
            "혈당 변동 증가",
            "성장 지연 (장기 ADHD 약물)"
        ],
        "monitoring": [
            "HbA1c: 매 3개월",
            "혈당 자가 모니터링: 1일 4-6회",
            "혈압, 맥박: 매 1-3개월 (ADHD 약물)",
            "성장, 체중: 매 3-6개월",
            "심리 평가: 연 1회"
        ],
        "papers": [
            "American Diabetes Association (ADA) 2024 Standards of Care",
            "American Psychiatric Association (APA) ADHD 진단 기준",
            "대한당뇨병학회, 대한소아과학회 진료지침"
        ]
    },

    # 12. 크론병 (Crohn's Disease)
    "크론병": {
        "english_name": "Crohn's Disease (CD)",
        "diagnosis": "확진 크론병, 활성 또는 관해기",
        "first_line_drugs": [
            {
                "name": "메살라민 (5-ASA, 아스아정)",
                "dosage": "2-4g/day",
                "frequency": "1일 2-4회",
                "timing": "식사와 함께 또는 별도 (제제에 따라)",
                "form": "정제 또는 액제"
            },
            {
                "name": "코르티코스테로이드 (프레드니손)",
                "dosage": "40-60mg (로딩) → 점진적 감소",
                "frequency": "1일 1회",
                "timing": "아침 식사 후",
                "form": "정제",
                "notes": "유도 요법, 단기 사용"
            },
            {
                "name": "아자티오프린 (Azathioprine)",
                "dosage": "1-2mg/kg",
                "frequency": "1일 1회",
                "timing": "식사 후",
                "form": "정제",
                "notes": "**CRITICAL: Allopurinol과 금지!**"
            }
        ],
        "biologics": [
            {
                "name": "인플릭시맙 (TNF-α 억제제, Infliximab, Remicade)",
                "dosage": "5mg/kg IV",
                "frequency": "0, 2, 6주 후 8주마다",
                "route": "정맥주사",
                "notes": "활성 크론병, 누공성 질환"
            },
            {
                "name": "아달리무맙 (Adalimumab, Humira)",
                "dosage": "40mg SC",
                "frequency": "2주마다",
                "route": "피하주사",
                "notes": "유지 요법"
            }
        ],
        "diet": {
            "recommended": "저섬유질(활성기), 소화하기 쉬운 음식",
            "avoid": "매운 음식, 우유(락토스 불내증), 고지방, 고섬유질(활성기)",
            "specific": "흰쌀, 계란, 저지방 생선, 바나나"
        },
        "fruits_vegetables": [
            "바나나 (부드러움, 영양)",
            "파파야 (소화 효소)",
            "당근 (삶은 것)",
            "호박 (부드러움)",
            "백포도 (쉬운 소화)",
            "복숭아 (부드러움)"
        ],
        "vitamins_safe": [
            "Vitamin D (1000-2000 IU/day, 흡수 문제 주의)",
            "Vitamin B12 (500-1000mcg/day, 말단 회장 흡수 문제)",
            "엽산 (1mg/day, Azathioprine 복용 시 필수)",
            "철분 (흡수 문제 주의, 극단적 주입 고려)",
            "Probiotics (특정 균주, 논쟁적)"
        ],
        "vitamins_avoid": [
            "**Allopurinol (Azathioprine과 절대 금지!)**",
            "고용량 철분 (소장 자극)",
            "비타민 C 과다 (산화, 장 자극)"
        ],
        "exercise": {
            "aerobic": "활동기 피하고, 관해기에 주 3-4회",
            "strength": "가벼운 저항 운동",
            "notes": "장 천공 위험 주의"
        },
        "drug_interactions": [
            {
                "drug_pair": "Azathioprine + Allopurinol",
                "interaction": "⚠️ CRITICAL: SCAR, 뼈다귀 모양 독성, 간 손상",
                "management": "절대 금지 - Febuxostat 또는 다른 방법 사용"
            },
            {
                "drug_pair": "TNF-α 억제제 + 생백신",
                "interaction": "백신 감염 위험",
                "management": "생백신 금지, 불활화 백신만"
            },
            {
                "drug_pair": "코르티코스테로이드 + NSAIDs",
                "interaction": "위장 출혈, 천공 위험",
                "management": "NSAIDs 피할 것"
            }
        ],
        "side_effects": [
            "복부 통증, 설사(활성기)",
            "체중 감소, 영양 결핍",
            "골다공증 (스테로이드 장기 사용)",
            "감염 위험 (TNF-α 억제제)",
            "간 독성 (Azathioprine)"
        ],
        "monitoring": [
            "CRP, ESR, Fecal calprotectin: 매 4-8주",
            "CBC, 간 기능: 매 2주 (Azathioprine 초기), 매 3개월",
            "내시경 (colonoscopy): 진단, 증상 악화 시",
            "골밀도 (DEXA): 스테로이드 1년 이상 사용 시",
            "감염 스크리닝 (TNF-α 억제제 시작 전)"
        ],
        "papers": [
            "American Gastroenterological Association (AGA) CD 진료지침",
            "European Crohn's and Colitis Organisation (ECCO) 권장사항",
            "대한장애학회 염증성 장질환 진료지침"
        ]
    },

    # 더 이상 문자 제한으로 인해 13-25번 질병은 축약형으로 제공
    # (계속...)
}

# ════════════════════════════════════════════════════════════════════════════
# 추가 13-25 질병 (축약형)
# ════════════════════════════════════════════════════════════════════════════

# 13. 전이성 유방암
DISEASE_DB["전이성유방암"] = {
    "english_name": "Metastatic Breast Cancer (mBC)",
    "first_line_drugs": [
        {"name": "파클리탁셀 (Paclitaxel)", "dosage": "175mg/m²", "frequency": "3주마다"},
        {"name": "허셉틴 (Trastuzumab)", "dosage": "6mg/kg", "frequency": "3주마다"}
    ],
    "diet": "항염증 식단, 고단백",
    "vitamins_safe": ["Vitamin D", "오메가-3", "CoQ10"],
    "monitoring": ["CEA, CA 15-3: 매 2-3개월", "CT: 매 8-12주"],
    "papers": ["NCCN 2024: Breast Cancer", "ESMO 2023: mBC"]
}

# 14. 파킨슨병 + 심부전
DISEASE_DB["파킨슨병심부전"] = {
    "english_name": "Parkinson's Disease + Heart Failure",
    "parkinson_drugs": [
        {"name": "카르비도파/레보도파 (Carbidopa/Levodopa)", "dosage": "25/100mg", "frequency": "1일 3-4회"},
        {"name": "프라미펙솔 (Pramipexole)", "dosage": "0.125-0.5mg", "frequency": "1일 3회"}
    ],
    "hf_drugs": [
        {"name": "메토프롤롤 (Metoprolol)", "dosage": "25-50mg", "frequency": "1일 2회"},
        {"name": "에날라프릴 (Enalapril)", "dosage": "2.5-5mg", "frequency": "1일 2회"}
    ],
    "diet": "저염, 적절한 단백질, 제한된 수분",
    "vitamins_safe": ["Vitamin D", "CoQ10 (심 건강)", "B-complex"],
    "monitoring": ["EF (심 초음파): 매 6개월", "Parkinson 증상 평가: 매 3개월"],
    "papers": ["American Neurology Association 2024", "ACC/AHA Heart Failure Guidelines"]
}

# 15. 소아 뇌전증
DISEASE_DB["소아뇌전증"] = {
    "english_name": "Pediatric Epilepsy",
    "first_line_drugs": [
        {"name": "레비티라세탐 (Levetiracetam, Keppra)", "dosage": "10mg/kg", "frequency": "1일 2회"},
        {"name": "발프로산 (Valproic acid)", "dosage": "10-20mg/kg", "frequency": "1일 2-3회"},
        {"name": "라모트리진 (Lamotrigine)", "dosage": "0.3-1mg/kg", "frequency": "1일 1-2회"}
    ],
    "diet": "균형 영양, 케톤 식단(난치성 경우)",
    "vitamins_safe": ["엽산 (2-5mg/day)", "Vitamin D", "Vitamin B6"],
    "vitamins_avoid": ["St. John's Wort"],
    "monitoring": ["약물 수치: 매 1-2주", "EEG: 임상 변화 시", "인지 평가: 연 1회"],
    "papers": ["American Academy of Pediatrics Epilepsy 지침", "ILAE 2023"]
}

# 16. 천식
DISEASE_DB["천식"] = {
    "english_name": "Asthma",
    "first_line_drugs": [
        {"name": "살부타몰 (Albuterol)", "dosage": "100-200mcg", "frequency": "필요시 (구제약)"},
        {"name": "플루티카손/살메테롤 (Advair)", "dosage": "45/21 또는 110/21mcg", "frequency": "1일 2회"}
    ],
    "diet": "항염증 식단, 충분한 수분",
    "vitamins_safe": ["Vitamin D", "Vitamin C", "마그네슘"],
    "monitoring": ["폐 기능 검사 (FEV1): 매 3-6개월", "증상 일지"],
    "papers": ["GINA 2024", "NAEPP Guidelines"]
}

# 17. 흑색종 (Early)
DISEASE_DB["흑색종"] = {
    "english_name": "Melanoma (Stage I-II)",
    "surgery": "광범위 절제술 (WLE)",
    "adjuvant": [
        {"name": "이필리무맙 (Ipilimumab)", "dosage": "10mg/kg", "frequency": "3주마다 (4회)"}
    ],
    "diet": "항산화 식단, 자외선 차단",
    "monitoring": ["피부 검진: 매 3개월", "PET-CT: 증상 시"],
    "papers": ["NCCN Melanoma 2024"]
}

# 18. 위염
DISEASE_DB["위염"] = {
    "english_name": "Chronic Gastritis",
    "first_line_drugs": [
        {"name": "오메프라졸 (Omeprazole)", "dosage": "20mg", "frequency": "1일 1회"},
        {"name": "판토프라졸 (Pantoprazole)", "dosage": "40mg", "frequency": "1일 1회"}
    ],
    "h_pylori_eradication": [
        {"name": "H. pylori 제균제", "duration": "10-14일", "notes": "PPI + Amoxicillin + Clarithromycin"}
    ],
    "diet": "부드러운 음식, 낮은 산성",
    "vitamins_safe": ["B12", "Vitamin D", "칼슘"],
    "monitoring": ["H. pylori 검사 후 제균 확인"],
    "papers": ["대한소화기병학회 가이드라인"]
}

# 19. 고혈압 + 심부전
DISEASE_DB["고혈압심부전"] = {
    "english_name": "Hypertension + Heart Failure",
    "first_line_drugs": [
        {"name": "에날라프릴 (ACE 억제제)", "dosage": "5-10mg", "frequency": "1일 2회"},
        {"name": "메토프롤롤 (베타-차단제)", "dosage": "25-50mg", "frequency": "1일 2회"},
        {"name": "스피로놀락톤 (K-보존 이뇨제)", "dosage": "12.5-25mg", "frequency": "1일 1회"}
    ],
    "diet": "저염 (<2g/day), 적절한 수분, 칼륨 제한",
    "vitamins_safe": ["Vitamin D", "CoQ10", "마그네슘"],
    "vitamins_avoid": ["높은 칼륨 보충제"],
    "monitoring": ["혈압: 매일", "EF: 매 3-6개월", "전해질: 매 1-3개월"],
    "papers": ["ACC/AHA 2022 Hypertension Guidelines", "Heart Failure Society 2023"]
}

# 20. COPD
DISEASE_DB["만성폐쇄성폐질환"] = {
    "english_name": "Chronic Obstructive Pulmonary Disease (COPD)",
    "first_line_drugs": [
        {"name": "알부테롤/이프라트로피움 (DuoNeb)", "dosage": "혼합", "frequency": "1일 2-3회"},
        {"name": "티오트로피움 (Spiriva)", "dosage": "18mcg", "frequency": "1일 1회"}
    ],
    "diet": "고단백, 적절한 칼로리, 충분한 수분",
    "vitamins_safe": ["Vitamin D", "셀레늄", "비타민 C"],
    "monitoring": ["폐 기능 검사: 매 6-12개월", "흉부 X선: 증상 시"],
    "papers": ["GOLD 2024", "NCCN COPD Guidelines"]
}

# 21. 제2형 당뇨병
DISEASE_DB["제2형당뇨병"] = {
    "english_name": "Type 2 Diabetes Mellitus (T2DM)",
    "first_line_drugs": [
        {"name": "메트포르민 (Metformin)", "dosage": "500-1000mg", "frequency": "1일 2-3회"},
        {"name": "글리메피리드 (Glimepiride)", "dosage": "1-4mg", "frequency": "1일 1회"},
        {"name": "더팔리글립틴 (GLP-1)", "dosage": "1.5mg SC", "frequency": "주 1회"}
    ],
    "diet": "저GI 탄수화물, 고섬유질, 제한된 당분",
    "vitamins_safe": ["Chromium", "비타민 D", "마그네슘"],
    "monitoring": ["HbA1c: 매 3개월", "혈당 자가 모니터링"],
    "papers": ["ADA 2024 Standards of Care"]
}

# 22. 우울증
DISEASE_DB["우울증"] = {
    "english_name": "Major Depressive Disorder (MDD)",
    "first_line_drugs": [
        {"name": "세르트랄린 (Sertraline, 졸로프트)", "dosage": "50-200mg", "frequency": "1일 1회"},
        {"name": "에스시탈로프람 (Escitalopram)", "dosage": "10-20mg", "frequency": "1일 1회"},
        {"name": "부프로피온 (Bupropion)", "dosage": "300mg", "frequency": "1일 1회"}
    ],
    "diet": "오메가-3, 항염증 식단",
    "vitamins_safe": ["Vitamin D", "엽산", "비타민 B6", "마그네슘"],
    "vitamins_avoid": ["St. John's Wort"],
    "monitoring": ["정신 상태 평가: 매 2-4주 (초기)", "자살 위험 평가"],
    "papers": ["APA DSM-5 2024", "American Psychiatry Association"]
}

# 23. 크론병 + 통풍
DISEASE_DB["크론병통풍"] = {
    "english_name": "Crohn's Disease + Gout (P023 CRITICAL)",
    "crohns_drugs": [
        {"name": "메살라민", "dosage": "2-4g/day"},
        {"name": "아자티오프린", "dosage": "1-2mg/kg", "notes": "**CRITICAL: Allopurinol 절대 금지!**"}
    ],
    "gout_drugs": [
        {"name": "페부크소스타트 (Febuxostat)", "dosage": "40-80mg", "frequency": "1일 1회", "notes": "안전한 대체약"},
        {"name": "콜키신 (Colchicine)", "dosage": "0.5mg", "frequency": "필요시"}
    ],
    "critical_warning": "P023: Azathioprine + Allopurinol = 뼈다귀 모양 독성 (SCAR), 간 손상 - 반드시 피할 것!",
    "diet": "저GI, 낮은 푸린(gout), 소화하기 쉬운 음식(Crohn)",
    "vitamins_avoid": ["Allopurinol", "높은 비타민 C (uric acid 증가)"],
    "monitoring": ["요산: 매월", "CRP/ESR: 매 4주", "간 기능: 매 2주 (초기)"],
    "papers": ["European League Against Rheumatism (EULAR) 2023", "대한류마티스학회", "대한장애학회"]
}

# 24. 급성 상기도 감염
DISEASE_DB["급성상기도감염"] = {
    "english_name": "Acute Upper Respiratory Infection (URI)",
    "treatment": "대증 치료 (self-limiting)",
    "drugs": [
        {"name": "아세트아미노펜 (Acetaminophen)", "dosage": "325-650mg", "frequency": "필요시 (4-6시간마다)"},
        {"name": "이부프로펜 (Ibuprofen)", "dosage": "200-400mg", "frequency": "필요시 (6-8시간마다)"},
        {"name": "덱스트로메토르판 (DXM, 기침약)", "dosage": "10-20mg", "frequency": "필요시"}
    ],
    "diet": "충분한 수분, 따뜻한 음료(국), 부드러운 음식",
    "vitamins": ["Vitamin C (500-1000mg/day)", "아연 (25mg, 초기 3일 내)"],
    "monitoring": ["증상 추적", "박테리아 2차 감염 여부"],
    "papers": ["CDC URI 가이드라인", "대한의학회"]
}

# 25. 편두통
DISEASE_DB["편두통"] = {
    "english_name": "Migraine",
    "acute_drugs": [
        {"name": "수마트립탄 (Sumatriptan, Imitrex)", "dosage": "50-100mg", "frequency": "편두통 시"}
    ],
    "preventive_drugs": [
        {"name": "프로프라놀롤 (Propranolol)", "dosage": "40-80mg", "frequency": "1일 2-3회"},
        {"name": "토피라메이트 (Topiramate)", "dosage": "25-100mg", "frequency": "1일 2회"}
    ],
    "diet": "편두통 트리거 회피(카페인, MSG, 적포도주, 숙성 치즈)",
    "vitamins_safe": ["마그네슘 (400mg/day)", "리보플라빈 (B2, 400mg/day)", "CoQ10"],
    "monitoring": ["편두통 일지", "증상 빈도/심도"],
    "papers": ["American Migraine Foundation 2024", "International Headache Society (IHS)"]
}


# ════════════════════════════════════════════════════════════════════════════
# 헬퍼 함수
# ════════════════════════════════════════════════════════════════════════════

def get_disease_info(disease_name: str) -> dict:
    """질병 정보 조회."""
    return DISEASE_DB.get(disease_name, {})

def get_diet_guide(disease_name: str) -> dict:
    """식단 가이드 조회."""
    disease = DISEASE_DB.get(disease_name, {})
    return {
        "recommended": disease.get("diet", {}).get("recommended", ""),
        "avoid": disease.get("diet", {}).get("avoid", ""),
        "fruits_vegetables": disease.get("fruits_vegetables", [])
    }

def get_vitamin_guide(disease_name: str) -> dict:
    """비타민 가이드 조회."""
    disease = DISEASE_DB.get(disease_name, {})
    return {
        "safe": disease.get("vitamins_safe", []),
        "avoid": disease.get("vitamins_avoid", [])
    }

def search_diseases(keyword: str) -> list:
    """질병명으로 검색."""
    return [name for name in DISEASE_DB.keys() if keyword.lower() in name.lower()]

def get_all_diseases() -> list:
    """모든 질병명 반환."""
    return list(DISEASE_DB.keys())

def get_critical_interactions() -> list:
    """중대 상호작용 경고."""
    return [
        "P023: Azathioprine + Allopurinol = SCAR (뼈다귀 모양 독성), 간 손상 - 절대 금지",
        "Imatinib + 자몽 주스 = 독성 위험",
        "TNF-α 억제제 + 생백신 = 감염 위험",
        "Trastuzumab + Anthracycline = 심독성 위험"
    ]

def get_monitoring_checklist(disease_name: str) -> list:
    """질병별 모니터링 체크리스트."""
    disease = DISEASE_DB.get(disease_name, {})
    return disease.get("monitoring", [])


# ════════════════════════════════════════════════════════════════════════════
# 사용 예시
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 모든 질병 목록
    print("=== 25개 환자 질병 목록 ===")
    for i, disease in enumerate(get_all_diseases(), 1):
        print(f"{i}. {disease}")

    # 예시: 비소세포폐암 정보
    print("\n=== 비소세포폐암 정보 ===")
    info = get_disease_info("비소세포폐암")
    print(f"진단: {info.get('diagnosis')}")
    print(f"1차 약물: {info.get('first_line_drugs', [])}")

    # 크론병 + 통풍 중대 경고
    print("\n=== 중대 상호작용 경고 ===")
    for warning in get_critical_interactions():
        print(f"⚠️  {warning}")

    # 검색
    print("\n=== 당뇨병 관련 질병 검색 ===")
    results = search_diseases("당뇨")
    print(results)
