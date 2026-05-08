# -*- coding: utf-8 -*-
"""
cancer_protocols_db.py
종합 암 임상 프로토콜 데이터베이스

데이터 출처:
  - 국립암센터 국가암등록통계 2022 (2024년 발표)
  - 건강보험심사평가원(HIRA) 2024 암 진료 통계
  - NCCN Clinical Practice Guidelines in Oncology 2024-2025
  - ESMO Clinical Practice Guidelines 2024
  - 대한종양학회 진료지침 2024-2025
  - 대한부인종양학회 진료지침 2024
  - WHO Classification of Tumours (5th Edition)
  - UpToDate 2025 기준
"""

# ════════════════════════════════════════════════════════
# 암 프로토콜 DB (40+ 암종)
# ════════════════════════════════════════════════════════

CANCER_PROTOCOLS = {

    # ──────────────────────────────────────────────────
    # 부인암 (Gynecologic Cancers)
    # ──────────────────────────────────────────────────

    "자궁육종암": {
        "ICD10": "C54.1 / C55",
        "분류": "부인암 > 자궁육종 (Uterine Sarcoma)",
        "아형": {
            "자궁평활근육종(uLMS)": "가장 흔한 자궁육종(40%). 고도 악성. CDKN2A/RB1 변이 빈발.",
            "저등급자궁내막간질육종(LG-ESS)": "JAZF1-SUZ12 융합유전자. 호르몬 수용체 양성(ER+/PR+). 비교적 양호한 예후.",
            "고등급자궁내막간질육종(HG-ESS)": "YWHAE-NUTM2 또는 BCOR-ZC3H7B 융합. 공격적 임상경과.",
            "미분화자궁육종(UUS)": "예후 최악. 면역치료 반응성 일부 보고.",
            "자궁선근육종(Adenosarcoma)": "상피+간질 혼합형. 간질 과증식시 예후 불량.",
        },
        "바이오마커": "JAZF1-SUZ12, YWHAE-NUTM2, BCOR, TP53, CDKN2A, ER/PR, MDM2, CDK4",
        "병기": "FIGO 2023 병기 체계 사용 (I-IV기)",
        "1차치료": {
            "수술": "전자궁적출술 + 양측 난관난소절제술(TAH+BSO). 병기에 따라 림프절절제술 추가.",
            "자궁평활근육종": "수술 후 보조요법: Gemcitabine + Docetaxel (GD 요법) 4-6주기",
            "저등급ESS": "수술 후 호르몬치료: Letrozole 2.5mg 또는 Medroxyprogesterone acetate (MPA)",
            "고등급ESS/UUS": "수술 후 Gemcitabine + Docetaxel 또는 Doxorubicin 기반 항암요법",
        },
        "2차치료": [
            "Trabectedin (트라벡테딘) -- 연부조직육종 2차 표준",
            "Pazopanib (파조파닙) -- VEGFR 억제제, FDA 승인 연부조직육종",
            "Ifosfamide + Doxorubicin (AI 요법)",
            "Dacarbazine (DTIC)",
            "Eribulin -- LMS 특이적 FDA 승인 (2016)",
            "Pembrolizumab + Lenvatinib -- TMB-high/MSI-H 자궁육종 (KEYNOTE-775)",
            "Nivolumab + Ipilimumab -- 진행성/재발 육종 임상시험",
        ],
        "표적치료": {
            "저등급ESS": "Aromatase inhibitor (Letrozole, Anastrozole), Megestrol acetate",
            "MDM2/CDK4 증폭": "Abemaciclib (CDK4/6 억제제) 임상시험 단계",
            "NTRK 융합": "Larotrectinib, Entrectinib (아형 무관)",
        },
        "면역치료": "MSI-H/dMMR: Pembrolizumab 단독. TMB-H: Pembrolizumab+Lenvatinib (KEYNOTE-775 기반)",
        "한국통계": {
            "연간발생": "자궁체부암 전체 약 4,200명 (2022). 그 중 육종은 약 5-10% (210-420명)",
            "5년생존율": "I기 76%, II기 60%, III기 45%, IV기 29% (자궁평활근육종 기준)",
            "발생추이": "자궁체부암 전체는 증가 추세. 육종은 드물지만 고령화로 증가.",
        },
        "예후인자": "병기, 조직학적 등급, 핵 분열 지수(mitotic index), 종양 크기, 혈관 침범",
        "지침": "대한부인종양학회 2024 / ESMO Soft Tissue and Visceral Sarcomas Guidelines 2023 / NCCN Uterine Neoplasms v1.2025",
    },

    "난소암": {
        "ICD10": "C56",
        "분류": "부인암 > 난소암 (Ovarian Cancer)",
        "아형": {
            "고등급장액성난소암(HGSOC)": "가장 흔함(70%). BRCA1/2 변이 연관. TP53 거의 100% 변이.",
            "저등급장액성난소암(LGSOC)": "KRAS/BRAF/NRAS 변이. 화학치료 저항성 높음.",
            "투명세포암종(CCC)": "동아시아 여성에서 상대적 다발. 화학치료 저항성. PIK3CA 변이.",
            "자궁내막양난소암": "PTEN/CTNNB1 변이. 비교적 양호한 예후.",
            "점액성난소암": "드문 아형. 위암 유사 치료 접근.",
        },
        "바이오마커": "BRCA1/2, HRD(상동재조합결핍), CA-125, HE4, KRAS, PIK3CA, ARID1A, TP53",
        "1차치료": {
            "수술": "종양감축술(cytoreductive surgery) -- 완전절제(R0) 목표",
            "항암화학요법": "Carboplatin (AUC 5-6) + Paclitaxel 175mg/m² × 6주기 (표준)",
            "혈관억제제": "Bevacizumab 15mg/kg 병용 → 유지요법 (GOG-0218, ICON7 기반)",
            "PARP억제제유지": "BRCA 변이: Olaparib (올라파립) 300mg BID 유지 (SOLO-1 기반, PFS 56개월 vs 13.8개월)",
            "HRD 양성": "Niraparib (니라파립) 200-300mg QD 유지 (PRIMA 기반)",
        },
        "2차치료": [
            "Platinum-sensitive 재발: Carboplatin + Gemcitabine ± Bevacizumab",
            "Platinum-resistant 재발: Pegylated liposomal doxorubicin (PLD), Topotecan, Gemcitabine",
            "Mirvetuximab soravtansine -- FRalpha 양성 platinum-resistant 재발암 (FDA 2022 승인)",
            "Pembrolizumab -- MSI-H/TMB-H",
            "Dostarlimab -- dMMR 재발 난소암",
        ],
        "한국통계": {
            "연간발생": "약 3,200명 (2022). 부인암 중 사망률 1위",
            "5년생존율": "전체 65%, I기 93%, II기 73%, III기 41%, IV기 29%",
            "BRCA변이비율": "한국 HGSOC 환자에서 BRCA1/2 생식세포 변이 약 17-20%",
        },
        "지침": "NCCN Ovarian Cancer v2.2025 / ESMO Ovarian Cancer Guidelines 2023 / 대한부인종양학회 2024",
    },

    "자궁내막암": {
        "ICD10": "C54.1",
        "분류": "부인암 > 자궁내막암 (Endometrial Cancer)",
        "분자분류(TCGA)": {
            "POLE과돌연변이형": "최상의 예후. MMR 유지. 면역치료 효과 탁월.",
            "MSI-H/dMMR": "Lynch 증후군 관련. 면역치료 반응성 높음.",
            "NSMP(저이질성)": "중간 예후. ER/PR 양성 경우 호르몬치료 고려.",
            "p53이상형": "최불량 예후. 장액성/투명세포 암종 포함.",
        },
        "바이오마커": "POLE, MMR/MSI, ER/PR, HER2, PIK3CA/PTEN, p53, L1CAM",
        "1차치료": {
            "수술": "복강경/로봇 전자궁적출술 + BSO + 골반/대동맥주위림프절절제 또는 생검",
            "보조방사선": "병기 및 위험도에 따라 질강근접방사선, 골반방사선",
            "보조항암": "Carboplatin + Paclitaxel × 6주기 (III-IV기 또는 고위험군)",
        },
        "2차/진행성치료": [
            "Pembrolizumab + Lenvatinib -- MSS/MMR-정상 진행성 자궁내막암 표준 (KEYNOTE-775, FDA 2021)",
            "Dostarlimab + Carboplatin/Paclitaxel → Dostarlimab 유지 (RUBY trial, dMMR 1차)",
            "Pembrolizumab + Carboplatin/Paclitaxel (KEYNOTE-868, dMMR 1차)",
            "HER2 양성 (장액성): Trastuzumab 병용",
            "호르몬치료 (ER/PR+, 저위험): Medroxyprogesterone, Megestrol, Letrozole",
        ],
        "한국통계": {
            "연간발생": "약 3,800명 (2022). 최근 10년간 2.5배 증가 (비만·고령화)",
            "5년생존율": "전체 85%. I기 95%, IV기 23%",
        },
        "지침": "NCCN Uterine Neoplasms v1.2025 / ESMO Endometrial Cancer Guidelines 2022 / 대한부인종양학회 2024",
    },

    "자궁경부암": {
        "ICD10": "C53",
        "분류": "부인암 > 자궁경부암 (Cervical Cancer)",
        "바이오마커": "HPV 16/18 (고위험형), PD-L1 (CPS≥1), HER2, TMB",
        "1차치료": {
            "조기(I-IIA)": "근치적 자궁경부절제술 또는 근치적 자궁적출술 + 골반림프절절제",
            "국소진행(IIB-IVA)": "Cisplatin 동시항암방사선치료 (CCRT) 표준",
            "전신치료(재발/IV기)": "Pembrolizumab + Cisplatin/Carboplatin + Paclitaxel ± Bevacizumab (KEYNOTE-826, 1차)",
        },
        "2차치료": [
            "Pembrolizumab 단독 (PD-L1 CPS≥1, 2차 이상, FDA 2021)",
            "Cisplatin + Topotecan + Bevacizumab",
            "Cemiplimab (진행성/재발, PD-L1≥1%, EMPOWER-Cervical 1)",
            "Tisotumab vedotin (HER2/Nectin-4 ADC, FDA 2021)",
        ],
        "예방": "HPV 9가 백신 (가다실9) -- 9-45세. 한국 국가예방접종(NIP) 12-13세 여성 무료",
        "한국통계": {
            "연간발생": "약 3,100명 (2022). 감소 추세 (백신 효과)",
            "5년생존율": "I기 93%, II기 74%, III기 51%, IV기 18%",
        },
        "지침": "NCCN Cervical Cancer v1.2025 / ESMO Cervical Cancer Guidelines 2023",
    },

    "외음부암": {
        "ICD10": "C51",
        "분류": "부인암 > 외음부암 (Vulvar Cancer)",
        "바이오마커": "HPV 유무 (HPV 관련 vs 분화형), p53, PD-L1",
        "1차치료": "근치적 절제술 + 서혜부림프절절제. 진행성: Cisplatin 동시항암방사선치료",
        "2차치료": ["Pembrolizumab (PD-L1+)", "Cisplatin + 5-FU", "Paclitaxel + Carboplatin"],
        "한국통계": {"연간발생": "약 400명 (2022). 드문 암종"},
        "지침": "NCCN Vulvar Cancer v1.2025 / ESMO 2017",
    },

    "질암": {
        "ICD10": "C52",
        "분류": "부인암 > 질암 (Vaginal Cancer)",
        "특징": "원발성 드묾(전체 부인암 1-2%). 대부분 자궁경부암 전이. HPV 관련 편평상피세포암이 다수.",
        "1차치료": "방사선치료(근접+외부) 또는 수술. 진행성: Cisplatin CCRT",
        "지침": "NCCN Vaginal Cancer v1.2025",
    },

    # ──────────────────────────────────────────────────
    # 소화기암 (GI Cancers)
    # ──────────────────────────────────────────────────

    "위암": {
        "ICD10": "C16",
        "분류": "소화기암 > 위암 (Gastric Cancer)",
        "바이오마커": "HER2 (IHC 3+ 또는 ISH+), MSI/MMR, PD-L1 CPS, VEGFR2, FGFR2, Claudin 18.2, EBV",
        "1차치료": {
            "HER2양성": "Trastuzumab + Cisplatin + Capecitabine/5-FU (ToGA 기반) ± Pembrolizumab (KEYNOTE-811)",
            "HER2음성-PD-L1CPS≥5": "Nivolumab + Oxaliplatin + Capecitabine (CheckMate 649, 표준)",
            "전신상태양호(ECOG 0-1)": "FOLFOX (Folinic acid + 5-FU + Oxaliplatin) 또는 CAPOX",
            "수술가능(조기-국소진행)": "D2 위절제술 + 주변 림프절절제 → 보조: CAPOX 8주기 또는 S-1",
        },
        "2차치료": [
            "Ramucirumab (VEGFR2 단클론항체) ± Paclitaxel (RAINBOW)",
            "Irinotecan 단독",
            "Trifluridine/tipiracil (TAS-102) -- 3차",
            "Nivolumab (3차 이상, 아시아 데이터 ATTRACTION-2)",
        ],
        "신규표적": {
            "Claudin 18.2 양성": "Zolbetuximab (SPOTLIGHT, GLOW 임상. Claudin18.2+ HER2- 1차)",
            "FGFR2b 증폭": "Bemarituzumab 임상시험 (FIGHT 임상)",
        },
        "한국통계": {
            "연간발생": "약 28,000명 (2022). 세계 최고 수준 발생률. 한국 암 발생 2위.",
            "5년생존율": "전체 80%. 조기 위암(I기) 97%. IV기 7%.",
            "특징": "한국은 위내시경 국가검진으로 조기 발견율 세계 최고",
        },
        "지침": "NCCN Gastric Cancer v2.2025 / ESMO Gastric Cancer Guidelines 2022 / 대한위암학회 2024",
    },

    "대장암": {
        "ICD10": "C18-C20",
        "분류": "소화기암 > 대장암 (Colorectal Cancer)",
        "바이오마커": "RAS (KRAS/NRAS) 돌연변이, BRAF V600E, MSI/MMR, HER2, NTRK 융합, PIK3CA",
        "1차치료": {
            "MSI-H/dMMR": "Pembrolizumab 단독 200mg q3w (KEYNOTE-177, PFS 우월) 또는 Nivolumab+Ipilimumab",
            "RAS야생형-우측결장": "FOLFOXIRI + Bevacizumab 또는 FOLFOX + Cetuximab",
            "RAS야생형-좌측결장": "FOLFOX/FOLFIRI + Cetuximab (EGFR 억제제, 좌측 우세)",
            "RAS돌연변이형": "FOLFOXIRI + Bevacizumab 또는 FOLFOX/FOLFIRI + Bevacizumab",
            "BRAF V600E": "Encorafenib + Cetuximab ± Binimetinib (BEACON CRC, 2차 이상)",
        },
        "2차치료": [
            "FOLFIRI ± Bevacizumab 또는 Cetuximab (1차 FOLFOX 후)",
            "Trifluridine/tipiracil (TAS-102) -- 3차",
            "Regorafenib -- 3차",
            "Fruquintinib -- 3차 이상 (FRESCO-2)",
        ],
        "수술": "복강경/로봇 대장절제술. 간 전이 절제 가능하면 적극 수술.",
        "한국통계": {
            "연간발생": "약 32,000명 (2022). 한국 암 발생 1위.",
            "5년생존율": "전체 75%. I기 97%, II기 88%, III기 72%, IV기 19%.",
        },
        "지침": "NCCN Colon/Rectal Cancer v4.2025 / ESMO Colorectal Cancer Guidelines 2023",
    },

    "직장암": {
        "ICD10": "C20",
        "분류": "소화기암 > 직장암 (Rectal Cancer)",
        "특징": "대장암과 유사하나 국소치료 중요. TME (Total Mesorectal Excision) 표준.",
        "1차치료": {
            "국소진행(T3-4/N+)": "신보조: Capecitabine + 방사선(CCRT) → 수술 → CAPOX 보조. 또는 FOLFOX 신보조(TNT)",
            "MSI-H": "Dostarlimab 6주기 → 수술 (완전관해시 경과관찰) -- GARNET 기반",
            "수술": "TME, 저위전방절제술(LAR) 또는 복회음절제술(APR). 로봇수술 증가 추세.",
        },
        "지침": "NCCN Rectal Cancer v3.2025 / ESMO 2023",
    },

    "췌장암": {
        "ICD10": "C25",
        "분류": "소화기암 > 췌장암 (Pancreatic Ductal Adenocarcinoma, PDAC)",
        "바이오마커": "BRCA1/2, ATM, PALB2, KRAS, CDKN2A, SMAD4, TP53, MSI, NTRK 융합",
        "1차치료": {
            "절제가능": "근치적 절제(휘플수술/원위췌절제) → 보조: Modified FOLFIRINOX 또는 Gemcitabine+Capecitabine",
            "경계성절제가능": "신보조 FOLFIRINOX 또는 Gemcitabine+nab-Paclitaxel → 수술",
            "국소진행/전이": "FOLFIRINOX (5-FU+Leucovorin+Irinotecan+Oxaliplatin) -- 전신상태 양호",
            "전신상태불량": "Gemcitabine + nab-Paclitaxel (MPACT 기반)",
        },
        "2차치료": [
            "NALIRIFOX (Nanoliposomal irinotecan + 5-FU + Oxaliplatin, NAPOLI-3)",
            "Olaparib 유지요법 -- gBRCA1/2 변이, 1차 platinum 무진행 후 (POLO)",
            "Gemcitabine 기반 (1차 FOLFIRINOX 후)",
        ],
        "신규치료": "RAS 직접억제제 (Adagrasib KRAS G12C 돌연변이 -- 췌장암 KRAS G12C는 1-2%만),  KRAS G12D 억제제 임상 진행 중",
        "한국통계": {
            "연간발생": "약 9,200명 (2022). 사망률 암 중 4위.",
            "5년생존율": "전체 15%. 절제 가능 35%, 전이성 3%.",
            "특징": "증상이 없어 70% 이상이 이미 전이 상태에서 진단",
        },
        "지침": "NCCN Pancreatic Adenocarcinoma v3.2025 / ESMO 2023",
    },

    "간암": {
        "ICD10": "C22.0",
        "분류": "소화기암 > 간세포암 (Hepatocellular Carcinoma, HCC)",
        "바이오마커": "AFP, AFP-L3, DCP(PIVKA-II), HBV/HCV 상태, PD-L1, FGF19, MET",
        "1차치료": {
            "절제가능(소수 전이/Child-Pugh A)": "간절제술 또는 고주파소작술(RFA)",
            "간이식": "Milan 기준 충족시 최선의 치료",
            "TACE적응": "중간기(BCLC-B): TACE (Transarterial chemoembolization)",
            "전신치료1차": "Atezolizumab + Bevacizumab (IMbrave150, PFS 6.8개월 vs 4.3개월, 표준)",
            "1차대안": "Durvalumab + Tremelimumab (HIMALAYA, OS 비열등성 입증) 또는 Sorafenib",
        },
        "2차치료": [
            "Regorafenib (RESORCE, Sorafenib 후 진행)",
            "Cabozantinib (CELESTIAL)",
            "Ramucirumab (AFP≥400ng/mL, REACH-2)",
            "Pembrolizumab (KEYNOTE-394)",
        ],
        "한국통계": {
            "연간발생": "약 15,100명 (2022). 한국 암 사망 2위.",
            "5년생존율": "전체 40%. B형간염 연관 가장 많음(75%).",
            "국가검진": "40세 이상 고위험군(B/C형간염, 간경변) 6개월마다 초음파+AFP",
        },
        "지침": "NCCN Hepatocellular Carcinoma v2.2025 / ESMO HCC Guidelines 2022 / 대한간학회 2024",
    },

    "담도암": {
        "ICD10": "C22.1 (담관세포암) / C23-C24 (담낭·담도)",
        "분류": "소화기암 > 담도암 (Biliary Tract Cancer, BTC) -- 담낭암 + 담관암(간내/간외/팽대부)",
        "바이오마커": "FGFR2 융합(간내담관암 15-20%), IDH1/2, KRAS, BRAF, HER2, NTRK, MSI, TMB",
        "1차치료": {
            "절제가능": "근치적 절제술 (간절제, 췌십이지장절제 등) → 보조: Gemcitabine+Capecitabine (BILCAP)",
            "진행성/전이": "Gemcitabine + Cisplatin + Durvalumab (TOPAZ-1, OS 12.8개월 vs 11.5개월. 1차 표준)",
        },
        "2차치료": [
            "FGFR2 융합 양성: Pemigatinib (FDA 2020) 또는 Futibatinib (FDA 2022)",
            "IDH1 변이: Ivosidenib (ClarlDHy, PFS 개선)",
            "HER2 과발현/증폭: Trastuzumab deruxtecan (T-DXd) -- Zanidatamab (진행 중)",
            "NTRK 융합: Larotrectinib, Entrectinib",
            "MSI-H: Pembrolizumab",
            "BRAF V600E: Dabrafenib + Trametinib",
            "Gemcitabine + nab-Paclitaxel (2차)",
            "FOLFOX (ABC-06, 2차 표준)",
        ],
        "한국통계": {
            "연간발생": "담도암 약 7,200명 (2022). 담낭암 포함.",
            "5년생존율": "전체 30%. 절제가능 담관암 40-50%, 전이성 8%.",
            "특징": "한국은 담도암 발생률 세계 최고 수준 (담석 유병률 높음)",
        },
        "지침": "NCCN Biliary Tract Cancers v1.2025 / ESMO 2023 / 대한간담췌외과학회",
    },

    "식도암": {
        "ICD10": "C15",
        "분류": "소화기암 > 식도암 (Esophageal Cancer)",
        "아형": "편평상피세포암(SCC, 한국·동아시아 다수) / 선암(Adenocarcinoma, 서구 다수)",
        "바이오마커": "PD-L1 CPS, HER2, MSI, NTRK",
        "1차치료": {
            "절제가능(SCC)": "신보조 Cisplatin+5-FU+방사선 → 식도절제술 (CROSS 프로토콜) 또는 Nivolumab 신보조",
            "진행성SCC": "Nivolumab + Cisplatin + 5-FU (CheckMate 648, CPS≥1 표준)",
            "진행성선암": "Pembrolizumab + Cisplatin + 5-FU (KEYNOTE-590, CPS≥10 우월)",
            "수술후보조(SCC)": "Nivolumab 1년 (CheckMate 577, 신보조 CCRT 후 잔여병변)",
        },
        "2차치료": ["Pembrolizumab (PD-L1+)", "Ramucirumab ± Paclitaxel", "Docetaxel", "Irinotecan"],
        "한국통계": {
            "연간발생": "약 2,800명 (2022). 남성이 85% 이상.",
            "5년생존율": "전체 40%. 진행성 12%.",
            "위험인자": "흡연, 음주, 식이 요인 (뜨거운 음식, 절인 식품)",
        },
        "지침": "NCCN Esophageal/GEJ Cancer v2.2025 / ESMO 2022",
    },

    "항문암": {
        "ICD10": "C21",
        "분류": "소화기암 > 항문암 (Anal Cancer)",
        "특징": "HPV 관련 편평상피세포암이 85%+. 수술보다 항암방사선이 주된 치료.",
        "1차치료": "Mitomycin + 5-FU + 방사선 (Nigro 프로토콜. 완전관해율 80%+)",
        "진행성": "Carboplatin + Paclitaxel → Nivolumab (CARDINAL, 2차)",
        "한국통계": {"연간발생": "약 350명 (2022). 드문 암종"},
        "지침": "NCCN Anal Carcinoma v2.2025 / ESMO 2021",
    },

    "소장암": {
        "ICD10": "C17",
        "분류": "소화기암 > 소장암 (Small Bowel Cancer)",
        "아형": "선암(Adenocarcinoma), 신경내분비종양(NET), 육종, 림프종",
        "1차치료": {
            "선암": "FOLFOX 또는 CAPOX (대장암 준용). FOLFOXIRI 임상 진행 중.",
            "NET": "Lanreotide/Octreotide, Everolimus, Sunitinib, 펩타이드수용체방사선치료(PRRT)",
        },
        "지침": "NCCN Small Bowel Adenocarcinoma v1.2025 / ESMO NET Guidelines 2023",
    },

    # ──────────────────────────────────────────────────
    # 폐암 (Lung Cancers)
    # ──────────────────────────────────────────────────

    "비소세포폐암": {
        "ICD10": "C34",
        "분류": "폐암 > 비소세포폐암 (NSCLC) -- 선암, 편평상피세포암, 대세포암",
        "바이오마커": "EGFR, ALK, ROS1, KRAS G12C, BRAF V600E, MET엑손14, RET, NTRK, HER2, PD-L1 TPS, TMB",
        "1차치료": {
            "EGFR 변이(exon19del/L858R)": "Osimertinib (오시머티닙) 80mg QD (FLAURA. PFS 18.9개월 vs 10.2개월)",
            "ALK 재배열": "Alectinib (알렉티닙) 600mg BID (ALEX. PFS 34.8개월 vs 10.9개월)",
            "ROS1 재배열": "Crizotinib 또는 Entrectinib 또는 Lorlatinib",
            "KRAS G12C": "Sotorasib (Lumakras, FDA 2021) 또는 Adagrasib (Krazati, FDA 2022)",
            "MET엑손14": "Capmatinib 또는 Tepotinib",
            "BRAF V600E": "Dabrafenib + Trametinib",
            "RET 재배열": "Selpercatinib 또는 Pralsetinib",
            "NTRK 융합": "Larotrectinib 또는 Entrectinib",
            "HER2 변이": "Trastuzumab deruxtecan (T-DXd, DESTINY-Lung02)",
            "PD-L1 TPS≥50% (드라이버변이 없음)": "Pembrolizumab 단독 (KEYNOTE-024)",
            "PD-L1 TPS 1-49%": "Pembrolizumab + Platinum + Pemetrexed/Paclitaxel",
            "PD-L1<1%": "Pembrolizumab + Platinum + Pemetrexed (선암) 또는 + Carboplatin + Paclitaxel + nab-Paclitaxel (편암)",
        },
        "한국통계": {
            "연간발생": "약 29,500명 (2022). 암 사망 1위.",
            "5년생존율": "전체 35%. I기 84%, IV기 8%.",
            "EGFR변이율": "한국 비소세포폐암 선암에서 EGFR 변이 약 50-60% (서구 10-15% 대비 매우 높음)",
        },
        "지침": "NCCN NSCLC v4.2025 / ESMO 2023 / 대한종양학회 폐암지침 2024",
    },

    "소세포폐암": {
        "ICD10": "C34",
        "분류": "폐암 > 소세포폐암 (SCLC, Small Cell Lung Cancer)",
        "특징": "흡연 강관련. 초고속 성장. 진단 시 60-70%가 광범위기(ES-SCLC).",
        "1차치료": {
            "광범위기": "Atezolizumab + Carboplatin + Etoposide (IMpower133, OS 12.3개월. 1차 표준)",
            "광범위기 대안": "Durvalumab + Carboplatin/Cisplatin + Etoposide (CASPIAN)",
            "제한기": "Cisplatin + Etoposide + 동시 흉부방사선 → 예방적 전뇌방사선(PCI)",
        },
        "2차치료": ["Lurbinectedin (단독, FDA 2020)", "Topotecan", "Irinotecan", "AMG 757 (DLL3 BiTE, 임상)"],
        "한국통계": {
            "연간발생": "약 2,500명 (2022). 전체 폐암의 약 10-15%.",
            "5년생존율": "광범위기 5-10%, 제한기 25-30%.",
        },
        "지침": "NCCN SCLC v2.2025 / ESMO 2021",
    },

    # ──────────────────────────────────────────────────
    # 유방암 (Breast Cancer)
    # ──────────────────────────────────────────────────

    "유방암": {
        "ICD10": "C50",
        "분류": "유방암 (Breast Cancer)",
        "아형": {
            "Luminal A": "ER+/PR+/HER2-/Ki67 낮음. 예후 최상. 호르몬치료 주축.",
            "Luminal B": "ER+/HER2- Ki67 높음 또는 HER2+. 보다 공격적.",
            "HER2 과발현": "HER2+/ER-/PR-. 항HER2치료로 예후 크게 개선.",
            "삼중음성(TNBC)": "ER-/PR-/HER2-. 예후 불량. 면역치료+항암이 주축.",
        },
        "바이오마커": "ER/PR, HER2(IHC/ISH), Ki67, BRCA1/2, PD-L1, PIK3CA, ESR1, PTEN",
        "1차치료": {
            "Luminal(ER+/HER2-)": "보조 호르몬치료: Tamoxifen (폐경전) 또는 AI (아나스트로졸/레트로졸/엑세메스탄) 5-10년",
            "재발고위험 Luminal": "CDK4/6 억제제 + AI: Abemaciclib (monarchE, 2년) -- Ki67≥20%",
            "HER2양성 조기": "신보조: Pertuzumab + Trastuzumab + 항암 → 수술 → T-DM1 (잔여병변시, KATHERINE)",
            "HER2양성 전이": "Trastuzumab deruxtecan (T-DXd, DESTINY-Breast03, 1차. PFS 28.8개월 vs 6.8개월)",
            "TNBC PD-L1+": "Pembrolizumab + nab-Paclitaxel 신보조 → Pembrolizumab 보조 (KEYNOTE-522)",
            "gBRCA변이 TNBC": "Olaparib 또는 Talazoparib 보조요법 (OlympiA, talaPARP)",
        },
        "2차치료": [
            "ER+ ESR1 변이: Elacestrant (EMERALD, 2차 표준 FDA 2023)",
            "ER+ PIK3CA 변이: Alpelisib + Fulvestrant (SOLAR-1)",
            "HER2+: Tucatinib + Trastuzumab + Capecitabine (HER2CLIMB, 뇌전이 포함)",
            "TNBC: Sacituzumab govitecan (SG, ASCENT)",
            "TNBC PD-L1+: Atezolizumab + nab-Paclitaxel (IMpassion130)",
        ],
        "한국통계": {
            "연간발생": "약 29,000명 (2022). 여성 암 발생 1위. 지속 증가 추세.",
            "5년생존율": "전체 94%. I기 99%, IV기 42%.",
            "BRCA변이율": "한국 유방암 환자 BRCA1/2 생식세포 변이 약 7-10%",
        },
        "지침": "NCCN Breast Cancer v4.2025 / ESMO Breast Cancer Guidelines 2024 / 대한유방암학회 2023",
    },

    "남성유방암": {
        "ICD10": "C50 (남성)",
        "분류": "유방암 > 남성유방암 (Male Breast Cancer)",
        "특징": "전체 유방암의 0.5-1%. 거의 대부분 Luminal 형. BRCA2 변이 10-15%. 치료는 여성 준용.",
        "1차치료": "수술 + Tamoxifen (주로) 5-10년. HER2+: 항HER2 치료 병용.",
        "지침": "NCCN Breast Cancer v4.2025",
    },

    # ──────────────────────────────────────────────────
    # 혈액암 (Hematologic Malignancies)
    # ──────────────────────────────────────────────────

    "급성골수성백혈병": {
        "ICD10": "C91-C95",
        "분류": "혈액암 > AML (Acute Myeloid Leukemia)",
        "바이오마커": "FLT3-ITD/TKD, NPM1, IDH1/IDH2, CEBPA, TP53, KMT2A, RUNX1-RUNX1T1, CBFbeta-MYH11",
        "1차치료": {
            "강화유도": "'7+3' 요법: Cytarabine 7일 + Idarubicin 또는 Daunorubicin 3일",
            "FLT3 변이+": "Midostaurin + 7+3 유도 → Midostaurin 유지 (RATIFY)",
            "IDH1 변이+": "Ivosidenib + Azacitidine (고령/치료부적합, AGILE)",
            "IDH2 변이+": "Enasidenib (재발/불응)",
            "CD33+": "Gemtuzumab ozogamicin (GO) + 7+3 (적합 아형에서)",
            "치료부적합 고령": "Venetoclax + Azacitidine 또는 Decitabine (VIALE-A)",
        },
        "이식": "완전관해 후 적합한 경우 동종조혈모세포이식(알로-HSCT) 권고",
        "한국통계": {
            "연간발생": "약 1,800명 (2022).",
            "5년생존율": "전체 30-40%. 좋은 예후군(RUNX1-RUNX1T1, NPM1 변이 FLT3-ITD 없음) 60%+",
        },
        "지침": "NCCN AML v3.2025 / ELN 2022 권고안",
    },

    "급성림프모구백혈병": {
        "ICD10": "C91.0",
        "분류": "혈액암 > ALL (Acute Lymphoblastic Leukemia)",
        "바이오마커": "Ph(BCR-ABL1), Ph-like, KMT2A 재배열, CDKN2A, PAX5, TP53",
        "1차치료": {
            "성인": "Hyper-CVAD (Cyclophosphamide, Vincristine, Doxorubicin, Dexamethasone) 기반",
            "Ph+ ALL": "Ponatinib 또는 Dasatinib + Chemotherapy → 이식",
            "B-ALL CD22+": "Inotuzumab ozogamicin (INO-VATE, 재발/불응)",
            "CAR-T": "Tisagenlecleucel (25세 이하 재발/불응, ELIANA) / Brexucabtagene autoleucel (성인)",
            "Blinatumomab": "MRD 양성 또는 재발/불응 B-ALL (BiTE 기전)",
        },
        "한국통계": {
            "연간발생": "약 700명 (2022). 소아·청소년 가장 흔한 암.",
            "5년생존율": "소아 95%+, 성인 40-60%.",
        },
        "지침": "NCCN ALL v2.2025 / ESMO 2021",
    },

    "만성골수성백혈병": {
        "ICD10": "C92.1",
        "분류": "혈액암 > CML (Chronic Myeloid Leukemia)",
        "바이오마커": "BCR-ABL1 t(9;22) (필라델피아 염색체), ABL1 키나제 도메인 변이",
        "1차치료": {
            "만성기": "Imatinib 400mg QD (1세대) 또는 Dasatinib 100mg QD / Nilotinib 300mg BID (2세대)",
            "고위험/급진전": "Ponatinib (3세대) 또는 Asciminib (STAMP 억제제, T315I 포함)",
            "T315I 변이": "Ponatinib 또는 Asciminib 200mg BID",
        },
        "치료중단": "심층분자반응(DMR, MR4.5) 2년 이상 유지 시 치료중단(TFR) 시도 가능. 40-50%에서 성공.",
        "한국통계": {
            "연간발생": "약 700명 (2022).",
            "5년생존율": "이마티닙 시대 이후 90%+. 거의 정상 수명 기대.",
        },
        "지침": "NCCN CML v2.2025 / ELN 2020 권고안",
    },

    "만성림프구성백혈병": {
        "ICD10": "C91.1",
        "분류": "혈액암 > CLL (Chronic Lymphocytic Leukemia) / SLL",
        "바이오마커": "del17p, TP53, del11q, IGHV 변이 상태, BTK, BCL2, del13q",
        "1차치료": {
            "del17p/TP53없음": "Ibrutinib (BTK 억제제) 단독 또는 Venetoclax + Obinutuzumab (12주기 고정 기간)",
            "del17p/TP53 변이": "Ibrutinib, Acalabrutinib, 또는 Zanubrutinib -- BTK 억제제가 표준",
            "고령/허약": "Venetoclax + Obinutuzumab (CLL14)",
        },
        "2차치료": ["Pirtobrutinib (BTK 비공유결합형, 1차 BTK 억제제 내성)", "Venetoclax 기반 구제요법", "CAR-T (임상)"],
        "한국통계": {"연간발생": "약 450명 (2022). 한국은 서구 대비 발생률 낮음"},
        "지침": "NCCN CLL/SLL v2.2025 / iwCLL 2018 가이드라인",
    },

    "미만성거대B세포림프종": {
        "ICD10": "C83.3",
        "분류": "혈액암 > DLBCL (Diffuse Large B-Cell Lymphoma) -- 가장 흔한 비호지킨림프종",
        "바이오마커": "COO(ABC vs GCB 세포기원), MYC, BCL2, BCL6, TP53, CD20, EZH2",
        "1차치료": {
            "표준": "R-CHOP (Rituximab + Cyclophosphamide + Doxorubicin + Vincristine + Prednisolone) × 6주기",
            "고위험(IPI 3-5)": "R-CHOP ± Polatuzumab vedotin (Pola-R-CHP, POLARIX. EFS 향상)",
            "고령/허약": "R-miniCHOP",
        },
        "재발/불응": [
            "CAR-T (R/R 2차 이상): Axicabtagene ciloleucel (Yescarta, ZUMA-7), Lisocabtagene maraleucel (Breyanzi, TRANSFORM)",
            "Loncastuximab tesirine (LOTIS-2, CD19 ADC)",
            "Tafasitamab + Lenalidomide (L-MIND)",
            "자가조혈모세포이식 (CAR-T 이전 시대 표준, R-ICE/DHAP 구제 후)",
            "Bispecific: Epcoritamab, Glofitamab (CD20xCD3)",
        ],
        "한국통계": {"연간발생": "약 2,800명 (2022). 비호지킨림프종 중 30-35%"},
        "지침": "NCCN B-Cell Lymphoma v4.2025 / ESMO 2021",
    },

    "호지킨림프종": {
        "ICD10": "C81",
        "분류": "혈액암 > Hodgkin Lymphoma (HL)",
        "바이오마커": "CD30, CD15, EBV, PD-L1, Reed-Sternberg 세포",
        "1차치료": {
            "조기양호": "ABVD (Doxorubicin + Bleomycin + Vinblastine + Dacarbazine) × 2주기 + 방사선",
            "조기불량/진행": "ABVD × 4-6주기 ± 방사선 또는 BrECADD (Brentuximab vedotin + ECADD)",
            "진행(III-IV기)": "BV+AVD (Brentuximab vedotin + AVD, ECHELON-1. PFS 우월) 또는 BEACOPP (escalated)",
        },
        "재발": ["Brentuximab vedotin (BV, CD30 ADC)", "Pembrolizumab 또는 Nivolumab (높은 반응률 87%+)", "자가이식 후 BV 유지"],
        "한국통계": {
            "연간발생": "약 600명 (2022).",
            "5년생존율": "전체 90%+. 젊은 층 가장 치료 성공률 높은 암 중 하나.",
        },
        "지침": "NCCN Hodgkin Lymphoma v3.2025 / ESMO 2018",
    },

    "다발성골수종": {
        "ICD10": "C90.0",
        "분류": "혈액암 > Multiple Myeloma (MM)",
        "바이오마커": "FISH: del17p, t(4;14), t(14;16), t(11;14), 1q 증폭, BCMA, CD38, CD138",
        "1차치료": {
            "이식적합": "VRd (Bortezomib + Lenalidomide + Dexamethasone) 유도 → 자가이식(ASCT) → Lenalidomide 유지",
            "이식적합(신규표준)": "Daratumumab + VRd (PERSEUS, PFS 우월) → 자가이식 → Dara+Len 유지",
            "이식부적합": "DRd (Daratumumab + Lenalidomide + Dexamethasone, MAIA) 또는 DVd (Dara + VMP)",
        },
        "재발": [
            "BCMA 표적: Belantamab mafodotin (ADC), Idecabtagene vicleucel (Ide-cel, CAR-T), Ciltacabtagene autoleucel (Cilta-cel)",
            "Elotuzumab + Pomalidomide + Dex",
            "Carfilzomib 기반",
            "Selinexor (XPO1 억제제)",
            "Bispecific: Teclistamab, Talquetamab (CD38xCD3, GPRC5DxCD3)",
        ],
        "한국통계": {
            "연간발생": "약 1,800명 (2022).",
            "5년생존율": "50-60%. 최근 신치료로 지속 향상 중.",
        },
        "지침": "NCCN Multiple Myeloma v4.2025 / IMWG 권고안 / 대한혈액학회",
    },

    "여포성림프종": {
        "ICD10": "C82",
        "분류": "혈액암 > FL (Follicular Lymphoma) -- 가장 흔한 저등급 비호지킨림프종",
        "바이오마커": "BCL2-IGH t(14;18), CD20, EZH2, CREBBP, TNFRSF14",
        "1차치료": {
            "저부하": "관찰(Watchful waiting) -- GELF 기준 미충족시",
            "치료필요": "R-CHOP 또는 BR (Bendamustine + Rituximab) → Rituximab 2년 유지",
            "고위험": "Obinutuzumab + Chemotherapy → Obinutuzumab 유지 (GALLIUM)",
        },
        "재발": ["Tazemetostat (EZH2 변이, FDA 2020)", "PI3K 억제제 (Umbralisib, Copanlisib)", "CAR-T (Axicabtagene -- axi-cel)"],
        "지침": "NCCN Follicular Lymphoma v3.2025",
    },

    "외투세포림프종": {
        "ICD10": "C83.1",
        "분류": "혈액암 > MCL (Mantle Cell Lymphoma)",
        "바이오마커": "CCND1-IGH t(11;14), cyclin D1, SOX11, TP53, CDKN2A, BTK",
        "1차치료": {
            "이식적합": "R-CHOP/R-DHAP 교대 또는 Hyper-CVAD/R → 자가이식 → Rituximab 유지",
            "이식부적합": "BR (Bendamustine + Rituximab) → Rituximab 유지, 또는 VR-CAP",
            "BTK 억제제 1차(진행 중)": "Ibrutinib + R-CHOP (TRIANGLE 임상)",
        },
        "재발": ["Ibrutinib, Acalabrutinib, Zanubrutinib (BTK 억제제)", "Brexucabtagene autoleucel (CAR-T, ZUMA-2)", "Venetoclax"],
        "지침": "NCCN MCL v3.2025 / ESMO 2017",
    },

    # ──────────────────────────────────────────────────
    # 비뇨기계 암 (Urologic Cancers)
    # ──────────────────────────────────────────────────

    "신장암": {
        "ICD10": "C64",
        "분류": "비뇨기암 > 신장암 (Renal Cell Carcinoma, RCC)",
        "아형": "투명세포암(ccRCC, 75%), 유두상암(pRCC), 혐색소성암(chRCC), 수집관암",
        "바이오마커": "VHL 변이/메틸화, PBRM1, SETD2, BAP1, PD-L1, mTOR, HIF",
        "1차치료": {
            "저-중위험": "Pembrolizumab + Axitinib (KEYNOTE-426. OS, PFS 우월) 또는 Nivolumab + Cabozantinib",
            "고위험": "Nivolumab + Ipilimumab (CheckMate 214) 또는 Pembrolizumab + Axitinib",
            "절제가능": "근치적 신장절제술 + 보조 Pembrolizumab 1년 (KEYNOTE-564, DFS 향상)",
        },
        "2차치료": [
            "Cabozantinib (CABOSUN, METEOR)",
            "Lenvatinib + Everolimus",
            "Nivolumab 단독 (CheckMate 025, OS 향상 vs Everolimus)",
            "Belzutifan (HIF-2alpha 억제제, VHL 변이 또는 VHL 질환 관련 RCC)",
        ],
        "한국통계": {
            "연간발생": "약 5,500명 (2022). 지속 증가 중.",
            "5년생존율": "전체 79%. I기 97%, IV기 15%.",
        },
        "지침": "NCCN Kidney Cancer v4.2025 / ESMO 2021",
    },

    "방광암": {
        "ICD10": "C67",
        "분류": "비뇨기암 > 방광암 (Bladder Cancer)",
        "아형": "비근침윤성(NMIBC, 70-75%): Ta/T1/CIS / 근침윤성(MIBC, 25-30%): T2-T4",
        "바이오마커": "PD-L1, FGFR3, ERCC2, TMB, HER2, Nectin-4, TROP2",
        "1차치료": {
            "NMIBC": "경요도방광절제(TURBT) + BCG 방광내주입 (고위험군)",
            "MIBC": "신보조 Gemcitabine + Cisplatin → 근치적 방광절제술 (gold standard)",
            "수술부적합 MIBC": "Pembrolizumab 신보조 또는 CCRT",
            "전이성(1차)": "Enfortumab vedotin + Pembrolizumab (EV+P, EV-302. OS 31.5개월 vs 16.1개월. 2024 신표준)",
        },
        "2차치료": [
            "Erdafitinib (FGFR3 변이/융합, FDA 2019)",
            "Enfortumab vedotin (Nectin-4 ADC, EV-301)",
            "Sacituzumab govitecan (TROP2, TROPHY-U-01)",
            "Pembrolizumab (PD-L1+)",
        ],
        "BCG불응 NMIBC": "Pembrolizumab 또는 Nadofaragene firadenovec (유전자치료) 또는 Nogapendekin alfa inbakicept",
        "한국통계": {
            "연간발생": "약 5,800명 (2022). 남성이 80%.",
            "5년생존율": "NMIBC 85%+, MIBC 60%, 전이성 15%.",
        },
        "지침": "NCCN Bladder Cancer v3.2025 / EAU Bladder Cancer Guidelines 2024",
    },

    "전립선암": {
        "ICD10": "C61",
        "분류": "비뇨기암 > 전립선암 (Prostate Cancer)",
        "바이오마커": "PSA, Gleason/ISUP grade, BRCA1/2, ATM, CDK12, MSI, AR, PSMA, PD-L1",
        "1차치료": {
            "국소성": "근치적 전립선절제술(RP) 또는 방사선 + 단기 ADT (저-중위험). 방사선 + 장기 ADT (고위험)",
            "국소진행/고위험": "ADT + EBRT ± Apalutamide 또는 Enzalutamide (ATLAS, ARAGON)",
            "전이성호르몬감수성(mHSPC)": "ADT + Darolutamide + Docetaxel (ARASENS) 또는 ADT + Apalutamide (TITAN) 또는 ADT + Enzalutamide (ARCHES, ENZAMET)",
            "거세저항성(mCRPC)": "Enzalutamide 또는 Abiraterone + Prednisolone",
            "BRCA/HRR 변이 mCRPC": "Olaparib (PROfound) 또는 Rucaparib",
        },
        "표적/방사성핵종": {
            "PSMA 양성": "Lu-177-PSMA-617 (Lutetium vipivotide tetraxetan, VISION. rPFS+OS 향상, FDA 2022)",
            "진행성골전이": "Ra-223 (Radium-223, ALSYMPCA)",
        },
        "한국통계": {
            "연간발생": "약 17,500명 (2022). 급격히 증가 중 (PSA 검진 확산).",
            "5년생존율": "국소성 거의 100%, 전이성 35%.",
            "특징": "고령화로 급증. 한국 남성 암 발생 4위.",
        },
        "지침": "NCCN Prostate Cancer v3.2025 / EAU Prostate Cancer Guidelines 2024",
    },

    "고환암": {
        "ICD10": "C62",
        "분류": "비뇨기암 > 고환암 (Testicular Germ Cell Tumor)",
        "아형": "정상피종(Seminoma) vs 비정상피종성(NSGCT: 배아암종, 기형종, 난황낭종양, 융모막암종)",
        "바이오마커": "AFP, Beta-hCG, LDH, OCT4",
        "1차치료": {
            "I기 정상피종": "고위험 고환적출술 → 경과관찰 또는 Carboplatin 1-2주기 또는 방사선",
            "II-III기": "BEP (Bleomycin + Etoposide + Cisplatin) × 3-4주기",
        },
        "구제": ["TIP (Paclitaxel + Ifosfamide + Cisplatin)", "VeIP", "고용량 Carboplatin/Etoposide + 자가이식"],
        "한국통계": {
            "연간발생": "약 600명 (2022).",
            "5년생존율": "전체 97%. 전이성에서도 90%+ (치료 가능한 암).",
        },
        "지침": "NCCN Testicular Cancer v1.2025 / ESMO 2018",
    },

    "음경암": {
        "ICD10": "C60",
        "분류": "비뇨기암 > 음경암 (Penile Cancer)",
        "특징": "HPV 관련 50-60%. 주로 편평상피세포암. 드문 암.",
        "1차치료": "국소절제/부분절제 ± 서혜부림프절절제. 진행성: Cisplatin 기반 항암.",
        "지침": "NCCN Penile Cancer v1.2025 / EAU 2021",
    },

    # ──────────────────────────────────────────────────
    # 두경부암 (Head and Neck Cancers)
    # ──────────────────────────────────────────────────

    "두경부암": {
        "ICD10": "C00-C14, C30-C32",
        "분류": "두경부암 (Head and Neck Squamous Cell Carcinoma, HNSCC)",
        "아형": "구강암, 구인두암, 하인두암, 후두암, 비강·부비동암",
        "바이오마커": "HPV/p16 (구인두암 특히 중요), PD-L1 CPS, EGFR, PIK3CA, PTEN",
        "1차치료": {
            "국소진행": "Cetuximab + 방사선 (Bonner, 생물학적치료+RT) 또는 Cisplatin + 방사선 (CCRT, 표준)",
            "전이성1차": "Pembrolizumab + Platinum + 5-FU (KEYNOTE-048, PD-L1 CPS≥1 표준) 또는 Pembrolizumab 단독 (CPS≥20)",
        },
        "2차치료": ["Nivolumab (CheckMate 141, PD-L1+ vs Investigator choice)", "Cetuximab + Platinum/5-FU", "Methotrexate 단독"],
        "한국통계": {
            "연간발생": "약 5,500명 (2022). 구강/인두/후두 합산.",
            "5년생존율": "후두암 60%, 구인두 HPV+ 80%+, 구강암 60%.",
        },
        "지침": "NCCN Head and Neck Cancers v2.2025 / ESMO 2021",
    },

    "갑상선암": {
        "ICD10": "C73",
        "분류": "두경부암 > 갑상선암 (Thyroid Cancer)",
        "아형": {
            "유두상(PTC)": "가장 흔함(85%). BRAF V600E(50%), RET/PTC, NTRK 융합. 예후 매우 좋음.",
            "여포성(FTC)": "10-15%. RAS 변이, PAX8-PPARG 융합.",
            "수질성(MTC)": "RET 변이 (산발성/유전성). Calcitonin 표지자.",
            "역형성(ATC)": "가장 공격적. 불량 예후. BRAF V600E 50%, TP53.",
        },
        "바이오마커": "BRAF V600E, RET, NTRK, RAS, PAX8-PPARG, Thyroglobulin, Calcitonin, CEA",
        "1차치료": {
            "분화갑상선암": "갑상선절제술 → RAI(방사성요오드, 고위험군) → T4 억제요법",
            "RAI불응 진행성": "Lenvatinib (SELECT) 또는 Sorafenib (DECISION) -- 1차 표준",
            "BRAF V600E+ RAI불응": "Dabrafenib + Trametinib",
            "NTRK 융합": "Larotrectinib 또는 Entrectinib",
            "역형성(ATC)": "BRAF V600E+: Dabrafenib + Trametinib (반응률 69%). 방사선 병용.",
            "수질성": "Vandetanib 또는 Cabozantinib (1차). RET 변이+: Selpercatinib 또는 Pralsetinib (2차).",
        },
        "한국통계": {
            "연간발생": "약 33,000명 (2022). 한국 암 발생 1위. 여성에서 압도적 1위.",
            "5년생존율": "분화갑상선암 99%+. 역형성 5% 미만.",
            "특징": "초음파 국가검진으로 과잉진단 논란. 적극적 추적관찰(Active Surveillance) 확대 중.",
        },
        "지침": "NCCN Thyroid Carcinoma v2.2025 / ATA 2015 가이드라인 / 대한갑상선학회 2023",
    },

    "타액선암": {
        "ICD10": "C07-C08",
        "분류": "두경부암 > 타액선암 (Salivary Gland Cancer)",
        "아형": "선양낭성암(ACC), 점액표피양암(MEC), 선방세포암(AciCC), 다형성선암(PAC)",
        "바이오마커": "HER2, NTRK, FGFR, MYB-NFIB (ACC), CRTC1-MAML2 (MEC), AR (타액선관암)",
        "1차치료": "수술(근치적 절제) + 방사선. 전이성: Pembrolizumab, HER2+ T-DXd 또는 Pertuzumab+Trastuzumab",
        "지침": "NCCN Salivary Gland Tumors v1.2025",
    },

    # ──────────────────────────────────────────────────
    # 피부암 / 연부조직 (Skin & Soft Tissue)
    # ──────────────────────────────────────────────────

    "악성흑색종": {
        "ICD10": "C43",
        "분류": "피부암 > 흑색종 (Melanoma)",
        "바이오마커": "BRAF V600E/K (45-50%), NRAS, NF1, cKIT, PD-L1, TMB, MSI, HLA",
        "1차치료": {
            "BRAF V600E/K 변이": "Dabrafenib + Trametinib (COMBI-d/v. PFS 11.1개월) 또는 Vemurafenib + Cobimetinib 또는 Encorafenib + Binimetinib",
            "BRAF 야생형": "Pembrolizumab 단독 (KEYNOTE-006) 또는 Nivolumab + Ipilimumab (CheckMate 067. 10년 OS 49%)",
            "보조요법(III기 절제후)": "Pembrolizumab 1년 (KEYNOTE-054) 또는 Nivolumab 1년 (CheckMate 238) 또는 BRAF+: Dabrafenib + Trametinib 1년",
            "신보조": "Nivolumab + Relatlimab (RELATIVITY-047) 또는 Pembrolizumab",
        },
        "특수부위": {
            "포도막(Uveal) 흑색종": "Tebentafusp (TCR 이중특이항체, gp100xCD3, IMCgp100-202. OS 향상 FDA 2022)",
            "점막 흑색종": "Anti-PD-1 ± Anti-CTLA-4. KIT 변이: Imatinib",
        },
        "한국통계": {
            "연간발생": "약 1,200명 (2022). 서구 대비 매우 낮음.",
            "특징": "한국은 말단흑색종(Acral)·점막 흑색종 비율이 서구 대비 높음(BRAF 변이율 낮음).",
            "5년생존율": "전체 70%. IV기 30%.",
        },
        "지침": "NCCN Melanoma v3.2025 / ESMO 2023",
    },

    "피부기저세포암": {
        "ICD10": "C44",
        "분류": "피부암 > 기저세포암 (Basal Cell Carcinoma, BCC)",
        "특징": "가장 흔한 피부암. PTCH1/PTCH2 변이. 자외선 관련.",
        "1차치료": "수술적 절제 (Mohs microsurgery). 국소 진행성/전이성: Vismodegib 또는 Sonidegib (Hedgehog 억제제)",
        "면역치료": "Cemiplimab (전이성 BCC, Hedgehog 억제제 불응, FDA 2021)",
        "지침": "NCCN BCC v2.2025",
    },

    "피부편평세포암": {
        "ICD10": "C44",
        "분류": "피부암 > 편평세포암 (Cutaneous SCC, cSCC)",
        "특징": "두 번째로 흔한 피부암. 자외선, HPV. 면역억제 환자에서 위험 증가.",
        "1차치료": "수술 또는 방사선. 국소진행성/전이성: Cemiplimab (EMPOWER-cSCC-1, FDA 2018) 또는 Pembrolizumab",
        "지침": "NCCN cSCC v2.2025",
    },

    "메르켈세포암": {
        "ICD10": "C44",
        "분류": "피부암 > 메르켈세포암 (Merkel Cell Carcinoma, MCC)",
        "특징": "드물지만 공격적. MCV(Merkel Cell Polyomavirus) 관련 80%. 면역억제 환자에서 다발.",
        "1차치료": "수술 + 방사선. 전이성: Avelumab (1차, FDA 2017) 또는 Pembrolizumab",
        "지침": "NCCN Merkel Cell Carcinoma v2.2025",
    },

    "연부조직육종": {
        "ICD10": "C49",
        "분류": "연부조직육종 (Soft Tissue Sarcoma, STS)",
        "아형": "평활근육종(LMS), 지방육종(Liposarcoma), 활막육종(Synovial Sarcoma), 횡문근육종(RMS), 혈관육종(Angiosarcoma), GIST, 미분화다형육종(UPS), Desmoplastic small round cell tumor 등 50개 이상 아형",
        "바이오마커": "MDM2/CDK4 증폭(지방육종), SS18-SSX(활막육종), DDIT3(점액형지방육종), TFE3(폐포연부육종), CIC-DUX4, BCOR, NTRK",
        "1차치료": {
            "절제가능": "광범위절제술(WLE) ± 방사선. 고위험: 보조 Doxorubicin + Ifosfamide (AI)",
            "전이성 1차": "Doxorubicin 75mg/m² 단독 (표준, EORTC 62012) 또는 Doxorubicin + Ifosfamide (AI)",
            "아형별": {
                "활막육종": "Doxorubicin + Ifosfamide 우선",
                "점액형지방육종": "Trabectedin 또는 Eribulin",
                "평활근육종(비자궁)": "Gemcitabine + Docetaxel 또는 Trabectedin",
                "혈관육종": "Paclitaxel 단독 (반응률 높음)",
                "횡문근육종": "Vincristine + Actinomycin D + Cyclophosphamide (VAC)",
            },
        },
        "2차치료": ["Trabectedin", "Eribulin (지방육종/LMS)", "Pazopanib (비지방성 STS, PALETTE)", "Gemcitabine + Dacarbazine", "Regorafenib (REGOSARC)"],
        "면역치료": "NTRK 융합: Larotrectinib. MSI-H: Pembrolizumab. 일부 아형 면역치료 임상 진행 중.",
        "한국통계": {
            "연간발생": "약 1,500명 (2022).",
            "5년생존율": "전체 60%. 원격전이 25%.",
        },
        "지침": "NCCN Soft Tissue Sarcoma v2.2025 / ESMO Soft Tissue Sarcomas 2023",
    },

    "혈관육종": {
        "ICD10": "C49.0-C49.9 / C44 (피부)",
        "분류": "연부조직육종 > 혈관육종 (Angiosarcoma, AS)",
        "아형": {
            "피부혈관육종(Cutaneous AS)": "두피·안면에 호발. 고령 남성에서 다발. 50% 이상에서 MYC 증폭. 5년 생존율 20-35%.",
            "방사선후혈관육종(Secondary AS)": "유방암 방사선 후 수년~수십년 뒤 발생. 유방 실질 또는 피부에 발생.",
            "만성림프부종후혈관육종(Stewart-Treves)": "림프절 절제 후 만성 림프부종에서 발생. 상지 호발. 예후 불량.",
            "내장혈관육종(Visceral AS)": "간·비장·심장에 드물게 발생. 예후 극히 불량.",
            "유방혈관육종(Breast AS)": "원발성 또는 방사선 후 2차성. 고등급이 대부분.",
        },
        "바이오마커": "MYC 증폭(FISH), KDR(VEGFR2) 변이, TP53, PTPRB, PLCG1, CD31, CD34, ERG, Factor VIII-RAg (혈관 내피 마커)",
        "병기": "AJCC 8판 연부조직육종 병기 적용 (I-IV기). 고등급(G3)이 대부분 → 초기 진단시 전이 빈발.",
        "1차치료": {
            "국소절제가능": "광범위절제술(WLE) + 방사선치료(보조). 음성 절제연(R0) 확보 필수.",
            "피부혈관육종(절제불가/전이성)": "Paclitaxel 80mg/m² D1,D8,D15 4주기 (ORR 18-30%, Skubitz/NCCN)",
            "전이성 1차": "Paclitaxel 단독 (피부형 우선) 또는 Gemcitabine + Docetaxel",
            "Gemcitabine+Docetaxel": "Gemcitabine 900mg/m² D1,D8 + Docetaxel 75mg/m² D8. 3주 간격.",
        },
        "2차치료": [
            "Pazopanib 800mg QD (PALETTE trial, PFS 4.6개월 vs 1.6개월, FDA 2012 STS)",
            "Sorafenib 400mg BID (혈관육종 ORR 14%, anti-VEGFR 기전)",
            "Trabectedin 1.5mg/m² 24hr IV 3주 간격 (2차 STS 표준)",
            "Eribulin 1.4mg/m² D1,D8 3주기 (LMS/지방육종 특이 FDA 승인, STS 일반도 가능)",
            "Propranolol (비선택적 β차단제) + Vinblastine -- 피부/방사선후 혈관육종 임상보고",
            "Cabozantinib (MET/VEGFR2 억제제) -- 임상시험 단계",
        ],
        "표적치료": {
            "KDR변이": "Cabozantinib, Regorafenib (VEGFR2 억제 기전)",
            "MYC증폭": "임상시험 단계 (BET 억제제, CDK7 억제제)",
        },
        "면역치료": "PD-1/PD-L1 억제제 단독 반응률 낮음(10-15%). MSI-H 드뭄. Pembrolizumab 임상 진행 중 (SARC028).",
        "방사선": "Proton 방사선 (MYC 증폭 AS, 두피형) 고려. 일반 방사선 보조요법으로 활용.",
        "한국통계": {
            "연간발생": "전체 연부조직육종 1,500명 중 약 5-8%(혈관육종 75-120명). 드문 암.",
            "5년생존율": "전체 35%, 국소성 60%, 원격전이 15% 미만. 피부형이 내장형보다 다소 양호.",
        },
        "예후인자": "종양 크기(>5cm 불량), 위치(두피 > 유방 > 내장), 방사선후 발생, 원격전이, MYC 증폭",
        "지침": "NCCN Soft Tissue Sarcoma v2.2025 / ESMO Soft Tissue Sarcomas 2023 / 대한종양학회 2024",
    },

    "골육종": {
        "ICD10": "C40.2 (원위 대퇴골) / C40.0 (근위 상완골) / C41",
        "분류": "원발성 골종양 > 골육종 (Osteosarcoma, OS)",
        "아형": {
            "통상형골육종(Conventional OS)": "가장 흔함(80%). 골모세포형·연골모세포형·섬유모세포형 하위분류. 원위 대퇴골·근위 경골에 호발.",
            "유잉육종(Ewing Sarcoma)": "EWSR1-FLI1 융합(85%). 소아·청소년 2번째 흔한 골종양. 골반·대퇴골·늑골.",
            "연골육종(Chondrosarcoma)": "성인 이상에서 호발. IDH1/2 변이(중심형). 화학·방사선 저항성. 수술이 주치료.",
            "골거대세포종(GCTB)": "RANKL 과발현. 수술 ± 데노수맙. 비전이성 경우 예후 양호.",
        },
        "바이오마커": "Rb/TP53/MDM2 (골육종), EWSR1-FLI1/ERG (유잉), IDH1/2 (연골육종), CDK4/MDM2/HMGA2, RANKL (GCTB), IGF1R",
        "병기": "MSTS(Enneking) 외과적 병기 또는 AJCC 8판 사용. IA/IB/IIA/IIB/III기",
        "1차치료": {
            "골육종_MAP요법": "Methotrexate (고용량 8-12g/m²) + Doxorubicin 75mg/m² + Cisplatin 100mg/m² — 신보조 2-3주기 → 수술(광범위절제술) → 보조 MAP × 3-4주기",
            "조직반응": "수술 후 괴사율(necrosis rate) ≥90% → 좋은 반응 → 보조 MAP 지속. <90% → 이포스파마이드 추가 고려",
            "유잉육종": "VDC/IE 교대 (Vincristine + Doxorubicin + Cyclophosphamide / Ifosfamide + Etoposide) 14회 → 수술/방사선 → 유지",
            "연골육종": "광범위절제술(화학·방사선 저항성). IDH1/2 변이: Ivosidenib/Enasidenib 임상 단계",
        },
        "재발치료": [
            "Ifosfamide + Etoposide (IE, 골육종 구제) 또는 Ifosfamide 단독 고용량",
            "Gemcitabine + Docetaxel (골육종 2차, GD 요법)",
            "Cabozantinib 60mg QD (골육종 재발, 임상 3상 CABONE 진행 중)",
            "Regorafenib (유잉/OS 재발, REGOBONE)",
            "Irinotecan + Temozolomide (유잉육종 구제)",
            "SRC/VEGFR 억제제: 수니티닙, 소라페닙",
            "Dinutuximab beta (신경모세포종 연관 골종양, GD2 양성)",
        ],
        "면역치료": "유잉육종 GD2 양성에서 디누투시맙(항GD2) 임상 진행. PD-1 억제제 단독 반응률 낮음. NTRK 융합 드뭄.",
        "사지보존술": "현대 OS 치료의 80-90%에서 절단 없이 사지보존술(limb-salvage) 가능. 종양용 내부고정물(endoprosthesis) 또는 자가골이식 활용.",
        "한국통계": {
            "연간발생": "골육종 약 200명, 유잉육종 약 70명, 연골육종 약 130명 (2022). 10-25세 청소년/청년에서 다발.",
            "5년생존율": "골육종 국소성 70-80%, 전이성 25-30%. 유잉 국소성 70%, 전이성 30%.",
            "특이사항": "한국 소아·청소년 암 발생 2위 (백혈병 다음). 신장 급성장기(사춘기 전후)에 호발.",
        },
        "예후인자": "원격전이 여부, 종양 크기, 위치(원위 > 근위 > 축골), 수술 후 조직반응(괴사율), Rb/TP53 상태",
        "지침": "NCCN Bone Cancer v2.2025 / ESMO Bone Sarcomas 2022 / COSS 프로토콜 / COG AOST1321",
    },

    "위장관기질종양": {
        "ICD10": "C49.A",
        "분류": "GIST (Gastrointestinal Stromal Tumor)",
        "바이오마커": "KIT 엑손11/9 변이 (70-75%), PDGFRA D842V (5-8%), NF1, SDH 결손, BRAF, 야생형(10%)",
        "1차치료": {
            "절제가능": "수술적 완전절제 → 보조 Imatinib 3년 (중-고위험군, ACOSOG Z9001, SSG XVIII)",
            "전이성/절제불능": "Imatinib 400mg QD (표준, SWOG S0033. 반응률 60%+)",
            "PDGFRA D842V": "Avapritinib (NAVIGATOR. FDA 2020. 반응률 90%+)",
        },
        "2차치료": ["Sunitinib (이마티닙 내성, 2차 표준)", "Regorafenib (3차, GRID)", "Ripretinib (4차, INVICTUS)", "Cabozantinib (4차 이상)"],
        "한국통계": {
            "연간발생": "약 800명 (2022).",
            "5년생존율": "전체 75%. 전이성 40-50% (이마티닙 치료 시대).",
        },
        "지침": "NCCN GIST v1.2025 / ESMO 2022",
    },

    # ──────────────────────────────────────────────────
    # 중추신경계 (CNS Tumors)
    # ──────────────────────────────────────────────────

    "뇌종양": {
        "ICD10": "C71",
        "분류": "중추신경계종양 (CNS Tumors)",
        "아형": {
            "교모세포종(GBM)": "WHO grade 4. 가장 흔하고 예후 최악. IDH 야생형.",
            "IDH변이신경교종": "WHO grade 2-3 (IDH 변이). GBM보다 양호한 예후.",
            "수모세포종(Medulloblastoma)": "소아 가장 흔한 뇌종양. 분자분류 중요 (WNT, SHH, Group3, Group4).",
            "뇌막종(Meningioma)": "대부분 양성(WHO grade 1). 재발성/악성: 수술+방사선.",
        },
        "바이오마커": "IDH1/2 변이, 1p/19q 공동결실, MGMT 프로모터 메틸화, TERT, EGFR 증폭, CDKN2A, BRAF V600E (소아 신경교종)",
        "1차치료": {
            "GBM(MGMT 메틸화)": "Temozolomide + 방사선 (Stupp 프로토콜) → Temozolomide 유지 + Tumor Treating Fields(TTFields, Optune)",
            "GBM(MGMT 비메틸화)": "방사선 ± Temozolomide. 고령: 방사선 단독 또는 Temozolomide 단독",
            "재발GBM": "Bevacizumab, Lomustine, Temozolomide 재유도. Pembrolizumab 임상 (반응 제한적)",
        },
        "한국통계": {
            "연간발생": "약 2,800명 (2022). GBM은 연간 약 1,200명.",
            "5년생존율": "GBM 5-10%. IDH 변이 저등급 신경교종 70%+.",
        },
        "지침": "NCCN CNS Cancers v2.2025 / EANO 2023 가이드라인",
    },

    # ──────────────────────────────────────────────────
    # 내분비/기타 (Endocrine & Others)
    # ──────────────────────────────────────────────────

    "신경내분비종양": {
        "ICD10": "C7A / D3A",
        "분류": "신경내분비종양 (Neuroendocrine Tumor, NET / NEC)",
        "아형": "췌장NET(pNET), 소장NET, 폐 카르시노이드, 신경내분비암(NEC, G3)",
        "바이오마커": "Chromogranin A, Synaptophysin, Ki67(분화도), SSTR(소마토스타틴수용체), SST2A, DAXX/ATRX(pNET)",
        "1차치료": {
            "저등급(G1/G2)": "Octreotide LAR 또는 Lanreotide (소마토스타틴유사체, 기능성+비기능성 항종양 효과)",
            "pNET": "Everolimus 10mg QD (RADIANT-3. PFS 11개월 vs 4.6개월) 또는 Sunitinib 37.5mg QD",
            "소장NET": "Everolimus (RADIANT-4)",
            "PRRT": "Lu-177-DOTATATE (Lutathera, NETTER-1. PFS 우월. SSTR 양성 중장NET)",
        },
        "NEC(G3)": "Cisplatin + Etoposide 또는 FOLFIRINOX",
        "한국통계": {
            "연간발생": "약 2,200명 (2022). 증가 추세 (진단율 향상).",
            "5년생존율": "G1 90%+, G2 75%, G3 30%.",
        },
        "지침": "NCCN Neuroendocrine Tumors v2.2025 / ESMO NET 2023",
    },

    "부신암": {
        "ICD10": "C74",
        "분류": "부신암 (Adrenocortical Carcinoma, ACC) / 갈색세포종(Pheochromocytoma)",
        "바이오마커": "IGF2 과발현, TP53, CTNNB1, CDKN2A, SF-1, Ki67, TERT, RET(갈색세포종), SDHB",
        "1차치료": {
            "ACC 절제가능": "근치적 절제술 → 보조 Mitotane (스테로이드 생합성 억제제)",
            "ACC 전이성": "Mitotane + EDP (Etoposide + Doxorubicin + Cisplatin). 1차 표준.",
            "갈색세포종": "수술전 알파차단제(Phenoxybenzamine) → 수술. 전이성: 177Lu-DOTATATE 또는 CVD 항암",
        },
        "한국통계": {"연간발생": "ACC 약 100명 (2022). 갈색세포종 약 200명. 모두 드문 암"},
        "지침": "NCCN Adrenal Gland Tumors v1.2025 / ENSAT 가이드라인",
    },

    "흉선종": {
        "ICD10": "C37",
        "분류": "흉선종/흉선암 (Thymoma / Thymic Carcinoma)",
        "특징": "중종격동의 드문 종양. 흉선종(WHO A-AB-B1-B2-B3)과 흉선암(C)으로 구분. 중증근무력증 동반 30-40%.",
        "바이오마커": "GTF2I 변이(흉선종), TP53(흉선암), PD-L1, KIT",
        "1차치료": "수술적 완전절제. 절제불가/전이: Cisplatin + Doxorubicin + Cyclophosphamide (CAP) 또는 Carboplatin + Paclitaxel",
        "면역치료": "흉선종에서 면역치료(PD-1/PD-L1)는 중증근무력증 악화 위험 -- 주의 요함",
        "한국통계": {"연간발생": "약 500명 (2022)"},
        "지침": "NCCN Thymomas and Thymic Carcinomas v1.2025 / ESMO 2021",
    },

    "중피종": {
        "ICD10": "C45",
        "분류": "중피종 (Mesothelioma)",
        "특징": "석면 노출과 밀접 관련. 잠복기 20-40년. 대부분 흉막; 복막·심낭 드묾.",
        "바이오마커": "BAP1, CDKN2A(p16), NF2, TP53, Calretinin, WT1, D2-40, TTF-1(음성)",
        "1차치료": "Nivolumab + Ipilimumab (CheckMate 743. OS 18.1개월 vs 14.1개월. 비편평 상피형에서 특히 우월. FDA 2021)",
        "수술": "흉막폐절제술(EPP) 또는 흉막절제/피질제거(P/D). 선택적 환자군에서만.",
        "2차치료": "Pemetrexed + Cisplatin (1차 항암치료 역할 감소), Gemcitabine, Vinorelbine",
        "한국통계": {
            "연간발생": "약 250명 (2022). 석면 사용 규제 이후 감소 추세.",
            "5년생존율": "전체 10% 미만.",
        },
        "지침": "NCCN Malignant Pleural Mesothelioma v2.2025 / ESMO 2020",
    },

    "원발부위불명암": {
        "ICD10": "C80.1",
        "분류": "원발부위불명암 (Cancer of Unknown Primary, CUP)",
        "특징": "광범위 검사에도 원발부위 불명. 전체 암의 2-5%. 불량 예후.",
        "진단": "면역조직화학(IHC), NGS(차세대염기서열분석) 기반 조직기원 분류, Oncotype DX CancerType ID 등",
        "분류별치료": {
            "여성 복막전파(선암)": "난소암에 준하여 Carboplatin + Paclitaxel 치료",
            "남성 PSA 양성": "전립선암에 준하여 호르몬치료",
            "편평상피세포암-경부림프절": "두경부암에 준하여 CCRT",
            "MSI-H": "Pembrolizumab",
            "NTRK 융합": "Larotrectinib 또는 Entrectinib",
            "경험적치료": "Carboplatin + Paclitaxel 또는 Gemcitabine + Cisplatin",
        },
        "한국통계": {"연간발생": "약 4,000명 (2022). 5년생존율 20% 미만."},
        "지침": "NCCN Occult Primary (Cancer of Unknown Primary) v1.2025 / ESMO 2023",
    },


    # ──────────────────────────────────────────────────
    # 육종 (Sarcomas)
    # ──────────────────────────────────────────────────

    "혈관육종": {
        "ICD10": "C49 (연부조직) / C22.3 (간) / C38.0 (심장)",
        "분류": "육종 > 혈관육종 (Angiosarcoma)",
        "아형": {
            "두피·피부형(Cutaneous)": "두피·안면 다발. 고령 남성. UV·방사선 노출 관련. 5년 생존율 30-35%.",
            "유방_방사선후(Post-radiation)": "유방암 방사선 치료 수년 후 발생. 잠복기 평균 5-10년.",
            "간혈관육종(Hepatic)": "염화비닐·비소·Thorotrast 노출 관련. 극히 불량한 예후.",
            "심장혈관육종(Cardiac)": "우심방 기원 가장 흔함. 진단 시 이미 전이된 경우 많음. 중앙생존기간 6-11개월.",
        },
        "바이오마커": "CD31, CD34, ERG, FLI-1 (혈관내피 마커). VEGFR-2, KDR, TP53, CDKN2A 변이.",
        "병기": "AJCC 8판 연부조직육종 병기 체계 준용",
        "1차치료": {
            "국소병변_수술": "광범위 절제(R0) — 기능 보존 하 음성 절제연 확보",
            "두피형_방사선": "수술 후 보조방사선 60-66Gy (재발률 높아 표준 적용)",
            "항암화학요법_1차": "Paclitaxel 80mg/m² 주 1회 — 피부형 특히 효과적 (RR 30-45%)",
            "대안_1차": "Doxorubicin 단독 또는 Doxorubicin + Ifosfamide (AI 요법) — 심부·내장형 선호",
        },
        "2차치료": [
            "Gemcitabine + Docetaxel (GD 요법) — 2차 표준, ORR 35%",
            "Sorafenib 400mg BID — VEGFR/PDGFR 억제, 간·심장혈관육종 (Agulnik 2013 2상)",
            "Pazopanib 800mg QD — 진행성 연부조직육종 2차 (PALETTE trial)",
            "Pembrolizumab ± Axitinib — TMB-H/MSI-H 혈관육종 임상시험",
            "Trabectedin — 소규모 시리즈에서 부분반응 보고",
        ],
        "표적치료": {
            "VEGFR억제": "Sorafenib, Pazopanib, Sunitinib",
            "면역치료": "TMB-H/MSI-H: Pembrolizumab; Epithelioid 아형: Nivolumab+Ipilimumab 임상 중",
        },
        "한국통계": {
            "연간발생": "전체 혈관육종 약 50-100명 추정 (2022). 전 연부조직육종의 1-2%.",
            "5년생존율": "전체 20-35%. 피부형 35%, 내장형 15% 미만.",
        },
        "예후인자": "위치(피부>내장), 종양 크기, R0 달성 여부, CDKN2A 결실, 전이 여부",
        "지침": "ESMO Soft Tissue and Visceral Sarcomas Guidelines 2023 / NCCN Soft Tissue Sarcoma v1.2025 / 대한종양학회 육종분과 2024",
        "주요논문": [
            {
                "제목_한": "[번역] 진행성 혈관육종에서 파클리탁셀 효과: 체계적 문헌고찰 (Penel N et al., 2015)",
                "핵심내용": "파클리탁셀은 피부·두피형 혈관육종에서 반응률(RR) 30-45%로 가장 효과적인 단일 항암제. 주 1회(80mg/m²) 용량 분할 요법이 표준으로 정착. 내장형은 독소루비신 기반이 우선.",
                "출처": "Cancer Treatment Reviews 2015; 41(6): 527-532",
                "근거수준": "Level II (체계적 문헌고찰)",
            },
            {
                "제목_한": "[번역] 소라페닙의 혈관육종 대상 2상 임상시험 (Agulnik M et al., 2013)",
                "핵심내용": "소라페닙(400mg 1일 2회) 투여군에서 PFS 중앙값 3.8개월, 부분반응률 14%. 간·심장 혈관육종에서 임상적 이득 확인. VEGFR 억제 기전 활용.",
                "출처": "Journal of Clinical Oncology 2013; 31(1): 16-22",
                "근거수준": "Level II (2상 임상시험)",
            },
            {
                "제목_한": "[번역] 방사선 연관 유방혈관육종의 임상적 특성 및 예후 (Shon W et al., 2011)",
                "핵심내용": "방사선 연관 유방혈관육종은 방사선 치료 후 평균 5.9년 만에 발생. 광범위 절제 후에도 국소재발률 50% 이상. 수술 후 파클리탁셀 보조요법 권고.",
                "출처": "Annals of Surgical Oncology 2011; 18(12): 3399-3409",
                "근거수준": "Level III (후향적 코호트)",
            },
        ],
    },

    "골육종": {
        "ICD10": "C40 (사지), C41 (두개골·척추)",
        "분류": "육종 > 골육종 (Osteosarcoma)",
        "아형": {
            "고등급중심성(High-grade Central)": "가장 흔함(75%). 골수강 내 발생. 골모세포형, 연골모세포형, 섬유모세포형 구분.",
            "표재성저등급(Parosteal)": "골 표면 발생. 10-15% 비율. 느린 성장, 비교적 양호한 예후.",
            "소세포골육종(Small Cell)": "유잉육종과 감별 필요. 고등급.",
            "모세혈관확장성(Telangiectatic)": "혈액 충전 공간. 병리 골절 위험. 전통 항암제 잘 반응.",
        },
        "발생위치": "원위 대퇴골(30%) > 근위 경골(25%) > 근위 상완골(15%) > 기타",
        "발생연령": "10-20대 청소년 2/3 이상. 80세 이상 고령 제2피크 (Paget병 관련)",
        "바이오마커": "ALP (알칼리인산분해효소), LDH, TP53, RB1, CDKN2A, MET, VEGFA",
        "병기": "AJCC 8판 골 종양 병기 + Enneking 병기 (IIA/IIB/III)",
        "1차치료": {
            "표준_항암화학요법(MAP)": "고용량 메토트렉세이트(HD-MTX) + 독소루비신(Doxorubicin) + 시스플라틴(Cisplatin) — MAP 요법",
            "수술": "광범위 절제(R0 목표). 사지 보존 수술(LCS) vs 절단술. 성장판 고려(소아)",
            "전환요법": "수술 전 MAP 3주기 → 수술 → 조직학적 반응 평가(Huvos) → 수술 후 MAP 3주기",
            "술후반응평가(Huvos)": "Grade III-IV (>90% 괴사): 양호한 예후. Grade I-II (<90% 괴사): 예후 불량",
        },
        "2차치료": [
            "Ifosfamide + Etoposide (IE 요법) — MAP 실패 후",
            "Gemcitabine + Docetaxel (GD 요법)",
            "Sorafenib 400mg BID — VEGFR/mTOR 억제 (Italian Sarcoma Group 2상, DCR 49%)",
            "Regorafenib 160mg 3주/1주 휴약 — 재발 골육종 (REGOBONE 무작위 2상, PFS 이득)",
            "Cabozantinib (MET/VEGFR2 억제제) — 재발 골육종 2상 연구",
            "Pembrolizumab — TMB-H 또는 MSI-H 골육종",
            "Nivolumab + Ipilimumab — 재발 골육종 소아 임상시험",
        ],
        "방사선치료": "골육종은 방사선 저항성. 수술 불가능 축성(척추, 두개저) 병변에 한해 고선량(66Gy+) 또는 탄소이온/양성자 치료",
        "한국통계": {
            "연간발생": "소아청소년 골육종 약 150-200명 (2022). 전체 골종양의 35%.",
            "5년생존율": "국소 병변 65-75%, 전이성 20-30% (폐 전이 가장 흔함)",
            "호발연령": "10-14세 남아 피크. 여아는 2-3년 빠름 (성장급등기 일치)",
        },
        "추적관찰": "치료 종료 후 2년간 3개월마다 CT/X-ray. 이후 6개월마다. 폐 전이 모니터링 필수.",
        "예후인자": "전이 유무, 수술 후 괴사율(Huvos 등급), 종양 위치(사지>축성), ALP/LDH 정상화 여부",
        "지침": "NCCN Bone Cancer v1.2025 / ESMO Bone Sarcomas 2022 / 대한정형외과종양학회(KOTS) 2023",
        "주요논문": [
            {
                "제목_한": "[번역] 골육종 표준 MAP 요법: 다기관 전향적 연구 (Ferrari S et al., 2005)",
                "핵심내용": "MAP 요법(고용량 MTX + 독소루비신 + 시스플라틴)은 골육종 국소 병변에서 5년 생존율 70% 달성. 술전 항암 후 괴사율 90% 이상(좋은 반응군)에서 예후 현저히 개선. 현재 골육종 세계 표준 1차 요법으로 확립됨.",
                "출처": "Journal of Clinical Oncology 2005; 23(34): 8845-8852",
                "근거수준": "Level II (다기관 전향적)",
            },
            {
                "제목_한": "[번역] 재발 골육종에서 소라페닙+에베롤리무스 2상 임상시험 (Grignani G et al., 2015)",
                "핵심내용": "재발·불응 고등급 골육종 대상 소라페닙 단독: 4개월 무진행 생존율 46%. 소라페닙+에베롤리무스 병용: 의미있는 추가 이득. mTOR/VEGFR 이중 억제 전략 임상적 의미 입증. 재발 골육종 표준 2차 치료 옵션 중 하나.",
                "출처": "Lancet Oncology 2015; 16(1): 98-107",
                "근거수준": "Level II (2상 임상시험)",
            },
            {
                "제목_한": "[번역] 재발 골육종에서 레고라페닙의 무작위 2상 연구 REGOBONE (Duffaud F et al., 2019)",
                "핵심내용": "재발 골육종(n=38) 레고라페닙(160mg, 3주on/1주off) vs 위약 무작위. 레고라페닙군 PFS 중앙값 5.6개월 vs 위약 1.0개월(HR 0.42, p=0.017). 유의미한 무진행생존기간 개선. 재발 골육종 구제요법으로 EMA 허가 검토 중.",
                "출처": "Annals of Oncology 2019; 30(12): 2002-2009",
                "근거수준": "Level II (무작위 2상)",
            },
            {
                "제목_한": "[번역] 골육종 소아 환자에서 HD-MTX 약동학적 모니터링 (Tönz M et al., 2003)",
                "핵심내용": "MAP 요법에서 HD-MTX(12g/m²) 혈중 농도 모니터링(24h, 48h)이 독성 예방 및 치료 효과 최적화에 필수. leucovorin rescue 용량은 혈중 MTX 농도에 따라 개별화해야 함. 소아에서 신장 기능 보호 특히 중요.",
                "출처": "Pediatric Blood & Cancer 2003; 40(1): 57-62",
                "근거수준": "Level III (후향적 코호트)",
            },
        ],
    },

    "소아고형암": {
        "ICD10": "C64 / C69 / C49 / C72",
        "분류": "소아암 > 고형종양 (Pediatric Solid Tumors)",
        "주요아형": {
            "신아종(Wilms Tumor)": "WTOP1 변이. WT1, WTX 변이. 1-5세 다발. 5년 생존율 90%+.",
            "망막모세포종(Retinoblastoma)": "RB1 변이. 유전성(양측)/산발성(일측). 안구 보존 치료 추구.",
            "신경모세포종(Neuroblastoma)": "MYCN 증폭, 11q 결실. 영아에서 자연소실 경우도 있음.",
            "소아뇌종양": "수모세포종(Medulloblastoma), 저등급 신경교종(BRAF V600E/융합), DIPG(H3K27M)",
        },
        "한국통계": {
            "연간발생": "소아암 전체 약 1,500명 (0-14세, 2022). 소아암 생존율 80%+로 증가.",
            "5년생존율": "전체 소아암 85%.",
        },
        "지침": "COG (Children's Oncology Group) 프로토콜 / NCCN 각 소아암 가이드라인",
    },
}


# ════════════════════════════════════════════════════════
# 접근 편의 함수
# ════════════════════════════════════════════════════════

def get_cancer_protocol(name: str):
    """암명으로 프로토콜 조회. 부분 매칭 지원."""
    if name in CANCER_PROTOCOLS:
        return CANCER_PROTOCOLS[name]
    for key, val in CANCER_PROTOCOLS.items():
        if name in key or key in name:
            return val
    return None


def search_cancer_protocols(query: str):
    """쿼리로 암 프로토콜 검색. 약물명/유전자/암명/아형 모두 검색."""
    q = query.lower().strip()
    results = []
    for cancer_name, protocol in CANCER_PROTOCOLS.items():
        score = 0
        if q in cancer_name.lower():
            score = 10
        elif q in str(protocol).lower():
            score = 5
        if score:
            results.append({"name": cancer_name, "score": score, "data": protocol})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_all_cancer_names():
    """모든 등록된 암명 목록 반환."""
    return list(CANCER_PROTOCOLS.keys())


def get_cancers_by_category():
    """카테고리별 암 목록 반환."""
    categories = {}
    for name, proto in CANCER_PROTOCOLS.items():
        cat = proto.get("분류", "기타").split(">")[0].strip()
        cat = cat.split("(")[0].strip()
        categories.setdefault(cat, []).append(name)
    return categories


# ════════════════════════════════════════════════════════
# 모듈 자체 실행 테스트
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Cancer Protocols DB -- 자체 테스트")
    print(f"등록된 암종: {len(CANCER_PROTOCOLS)}개")
    print("=" * 60)

    cats = get_cancers_by_category()
    for cat, names in cats.items():
        print(f"\n[{cat}] {len(names)}개")
        for n in names:
            print(f"  - {n}")

    print("\n자궁육종암 프로토콜:")
    p = get_cancer_protocol("자궁육종암")
    if p:
        print(f"  ICD10: {p.get('ICD10')}")
        print(f"  바이오마커: {p.get('바이오마커')}")
        print(f"  지침: {p.get('지침')}")

    print("\n'BRCA' 검색:")
    for r in search_cancer_protocols("BRCA")[:5]:
        print(f"  {r['name']} (score: {r['score']})")
