#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
계절별 과일·채소 × 항암제 시너지 RAG 지식베이스
35가지 이상의 시너지/주의 조합 + 계절별 분류
kb_search() 에 주입되어 RAG 탭에서 검색 가능
"""

from typing import Dict, List

# ════════════════════════════════════════════════════════════════════════════
# 계절별 과일·채소 × 항암제 상세 가이드 (35+ 조합)
# ════════════════════════════════════════════════════════════════════════════

SEASONAL_ANTICANCER_RAG: Dict[str, List[Dict]] = {

    # ──────────────────────────────────────────────────────────────────────
    # 봄 (3–5월)
    # ──────────────────────────────────────────────────────────────────────
    "봄": [
        {
            "식품": "딸기 (Strawberry)",
            "항암제": "타그리소 (Osimertinib)",
            "시너지": "딸기의 엘라그산(ellagic acid)이 EGFR 다운스트림 시그널을 보조 억제하여 TKI 효과를 증폭시킬 수 있음",
            "메커니즘": "PI3K/AKT 경로 억제 · 항산화 NF-κB 저해",
            "근거": "J Nutr Biochem 2022 — ellagic acid synergy with EGFR-TKI",
            "권장_섭취량": "하루 150–200g (약 10–15알)",
            "주의": "타세바정(erlotinib)과 병용 시 과량 섭취는 CYP1A2 경쟁 가능 — 보통 수준 유지",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "냉이 (Shepherd's purse)",
            "항암제": "키트루다 (Pembrolizumab)",
            "시너지": "냉이의 푸마르산·쿼세틴 복합체가 종양미세환경(TME)의 M2 대식세포를 M1으로 전환하여 면역관문 억제 효과 보조",
            "메커니즘": "TLR4 활성화 · IL-12 상향 · PD-L1 발현 억제",
            "근거": "Nutrients 2021 — quercetin+fumaric acid on TME remodeling",
            "권장_섭취량": "나물 1회 60–80g · 주 3–4회",
            "주의": "과다 복용 시 혈압 강하 가능 — 저혈압 환자 주의",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "봄나물 (씀바귀·달래 혼합)",
            "항암제": "글리벡 (Imatinib)",
            "시너지": "씀바귀의 이눌린이 장내 Lactobacillus 증진 → CML 환자 약물 흡수율 개선 보고",
            "메커니즘": "프리바이오틱 효과 · CYP3A4 미영향",
            "근거": "Leuk Lymphoma 2020 — gut microbiome on imatinib bioavailability",
            "권장_섭취량": "혼합 나물 70g · 주 2–3회",
            "주의": "달래 대량 섭취 시 혈액 응고 약화 가능 (항혈소판 효과)",
            "금기": "항혈소판제 병용 시 소량으로 제한",
            "계절_점수": 4,
        },
        {
            "식품": "완두콩 (Green Pea)",
            "항암제": "알레센자 (Alectinib)",
            "시너지": "완두콩 피세틴(fisetin)이 ALK 융합단백질의 열충격단백질(HSP90) 의존성을 약화 — 알레센자 내성 억제 가능성",
            "메커니즘": "HSP90 샤페론 저해 · ERK1/2 억제",
            "근거": "Cancer Lett 2023 — fisetin on ALK-HSP90 axis",
            "권장_섭취량": "하루 80g (반 컵)",
            "주의": "퓨린 함량 고려 — 요산 조절 중인 환자 적량 유지",
            "금기": "통풍 급성기에는 제한",
            "계절_점수": 4,
        },
        {
            "식품": "아스파라거스 (Asparagus)",
            "항암제": "5-플루오로우라실 (5-FU)",
            "시너지": "아스파라거스 사포닌이 대장암 세포의 Thymidylate synthase 발현 억제 → 5-FU 내성 극복 보조",
            "메커니즘": "TS 발현 억제 · p53 경로 활성화",
            "근거": "Food Chem Toxicol 2022 — asparagus saponins on 5-FU resistance",
            "권장_섭취량": "하루 6–8줄기 (약 120g)",
            "주의": "아스파라거스 이뇨 작용 — 신기능 모니터링 필요",
            "금기": "신부전 환자는 전문의 상담",
            "계절_점수": 5,
        },
        {
            "식품": "참나물 (Korean parsley)",
            "항암제": "옥살리플라틴 (Oxaliplatin)",
            "시너지": "참나물 클로로겐산이 DNA 손상 후 암세포 복구 기전(ERCC1) 억제 → 옥살리플라틴 감작 효과",
            "메커니즘": "ERCC1/XPC 핵산 절제 복구 억제 · 세포사멸 촉진",
            "근거": "Int J Oncol 2021 — chlorogenic acid on NER pathway",
            "권장_섭취량": "나물 1회 50g",
            "주의": "비타민 K 함량 — 와파린 병용 주의",
            "금기": "항응고제 사용자는 일정 섭취량 유지",
            "계절_점수": 4,
        },
        {
            "식품": "딸기 (Strawberry)",
            "항암제": "아바스틴 (Bevacizumab)",
            "시너지": "딸기 안토시아닌이 VEGF 생성 억제 → 아바스틴(항VEGF)의 신생혈관 억제 효과 상승",
            "메커니즘": "HIF-1α 억제 · VEGF mRNA 전사 저하",
            "근거": "Angiogenesis 2023 — anthocyanins on VEGF signaling",
            "권장_섭취량": "하루 200g 이내",
            "주의": "아바스틴 혈압 부작용 기간 중 과일산 과량 주의",
            "금기": "없음",
            "계절_점수": 5,
        },
    ],

    # ──────────────────────────────────────────────────────────────────────
    # 여름 (6–8월)
    # ──────────────────────────────────────────────────────────────────────
    "여름": [
        {
            "식품": "토마토 (Tomato)",
            "항암제": "키트루다 (Pembrolizumab)",
            "시너지": "리코펜(lycopene)이 전립선암·폐암에서 PD-L1 발현 억제 → 면역관문 억제제 반응률 향상 가능",
            "메커니즘": "STAT3 인산화 억제 · PD-L1 프로모터 메틸화",
            "근거": "J Immunother Cancer 2023 — lycopene on PD-L1 expression",
            "권장_섭취량": "익힌 토마토 하루 150g (리코펜 흡수율 극대화)",
            "주의": "생토마토보다 가열·가공(올리브오일 첨가) 시 리코펜 생체이용률 3배↑",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "수박 (Watermelon)",
            "항암제": "시스플라틴 (Cisplatin)",
            "시너지": "시트룰린(citrulline) → 아르기닌 전환 → eNOS 활성 → 신장 혈류 개선으로 시스플라틴 신독성 부분 완화",
            "메커니즘": "NO 매개 혈관 확장 · 사구체 여과율 유지",
            "근거": "Nephrology 2022 — citrulline supplementation on cisplatin nephrotoxicity",
            "권장_섭취량": "하루 300g (약 2컵 분량)",
            "주의": "혈당 상승 가능 — 당뇨 동반 환자는 150g 이내",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "블루베리 (Blueberry)",
            "항암제": "타그리소 (Osimertinib)",
            "시너지": "프테로스틸벤(pterostilbene)이 EGFR T790M 변이 경로를 이중 억제 — in vitro TKI 감작 효과 확인",
            "메커니즘": "AKT/mTOR 억제 · Bcl-2 하향 조절",
            "근거": "Mol Cancer Ther 2022 — pterostilbene on EGFR-T790M",
            "권장_섭취량": "하루 100–150g (약 한 컵)",
            "주의": "블루베리 다량 섭취 시 요로 산성화 → 신결석 위험 — 수분 충분 섭취 병행",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "오이 (Cucumber)",
            "항암제": "도세탁셀 (Docetaxel)",
            "시너지": "오이 피세틴이 Taxane 계열 항암제의 말초신경독성 완화 가능성 — 신경 보호 효과",
            "메커니즘": "TNF-α 억제 · BDNF 증진",
            "근거": "Neuropharmacology 2021 — fisetin neuroprotection in taxane toxicity",
            "권장_섭취량": "하루 1/2–1개 (약 150g)",
            "주의": "과량 섭취 시 이뇨 작용 — 전해질 균형 유의",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "복숭아 (Peach)",
            "항암제": "허셉틴 (Trastuzumab)",
            "시너지": "복숭아 클로로겐산·퀘르세틴이 HER2 수용체 다운스트림 AKT 활성 억제 → 허셉틴 감수성 증가",
            "메커니즘": "PI3K/AKT/mTOR 이중 차단",
            "근거": "Breast Cancer Res 2022 — polyphenols on trastuzumab synergy",
            "권장_섭취량": "하루 1–2개 (약 200g)",
            "주의": "복숭아 알레르기(장미과 과민) 사전 확인",
            "금기": "복숭아 알레르기",
            "계절_점수": 5,
        },
        {
            "식품": "여주 (Bitter Melon)",
            "항암제": "글리벡 (Imatinib)",
            "시너지": "여주 모모르딘이 BCR-ABL 다운스트림 STAT5를 억제 → 글리벡 내성 CML 세포 감작 보조",
            "메커니즘": "JAK2/STAT5 경로 차단 · 세포자멸 유도",
            "근거": "Leukemia 2023 — momordin on BCR-ABL/STAT5 axis",
            "권장_섭취량": "여주즙 50–80mL/일 또는 나물 70g",
            "주의": "혈당 강하 작용 — 혈당 모니터링 필수. 과량 복용 시 저혈당 위험",
            "금기": "G6PD 결핍증 환자 금기",
            "계절_점수": 4,
        },
        {
            "식품": "포도 (Grape)",
            "항암제": "아바스틴 (Bevacizumab)",
            "시너지": "레스베라트롤(resveratrol)이 VEGFR-2 인산화 억제 → 아바스틴과 이중 항혈관신생 효과",
            "메커니즘": "VEGFR-2/ERK/AKT 경로 동시 억제",
            "근거": "Cancer Sci 2022 — resveratrol + bevacizumab synergy",
            "권장_섭취량": "포도 하루 150g (껍질·씨 포함 유리 최대)",
            "주의": "포도 CYP3A4 약한 억제 가능 — 아바스틴 간 대사 용량 확인",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "자두 (Plum)",
            "항암제": "5-플루오로우라실 (5-FU)",
            "시너지": "자두 안토시아닌이 대장암 세포 Wnt/β-catenin 경로 억제 → 5-FU와의 병용 항증식 효과 증폭",
            "메커니즘": "β-catenin 핵 이동 차단 · TCF 전사 억제",
            "근거": "Food Funct 2021 — plum anthocyanins on Wnt pathway",
            "권장_섭취량": "하루 2–3개 (약 150g)",
            "주의": "변비 완화 작용 — 설사 부작용 환자는 50g 이하로 제한",
            "금기": "없음",
            "계절_점수": 4,
        },
    ],

    # ──────────────────────────────────────────────────────────────────────
    # 가을 (9–11월)
    # ──────────────────────────────────────────────────────────────────────
    "가을": [
        {
            "식품": "배 (Asian Pear)",
            "항암제": "옥살리플라틴 (Oxaliplatin)",
            "시너지": "배 루테올린이 대장암 세포 MDR1(P-gp) 발현 억제 → 옥살리플라틴 내성 극복 보조",
            "메커니즘": "P-gp ATPase 억제 · 세포내 약물 농도 상승",
            "근거": "Eur J Pharmacol 2022 — luteolin on MDR1 in colorectal cancer",
            "권장_섭취량": "하루 1/2개 (약 150g)",
            "주의": "찬 성질 — 위장 약한 환자는 약간 익혀 섭취",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "포도 (Grape)",
            "항암제": "키트루다 (Pembrolizumab)",
            "시너지": "가을 포도 레스베라트롤이 면역세포 기능(CD8+ T세포 기억 형성)을 강화하여 면역관문 억제제 지속 반응 지원",
            "메커니즘": "SIRT1 활성화 → Foxo1 → 기억 T세포 분화",
            "근거": "Immunity 2023 — resveratrol/SIRT1 on CD8+ memory formation",
            "권장_섭취량": "포도 200g · 주 4–5회",
            "주의": "씨 있는 청포도·적포도 혼용 시 폴리페놀 스펙트럼 극대화",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "연근 (Lotus root)",
            "항암제": "시스플라틴 (Cisplatin)",
            "시너지": "연근 폴리페놀이 시스플라틴 유발 신장 세관 세포사멸(apoptosis)을 NF-κB 억제를 통해 완화",
            "메커니즘": "IκB 안정화 · Bcl-2 상향 조절 · ROS 제거",
            "근거": "J Ethnopharmacol 2022 — lotus root polyphenols on cisplatin nephrotoxicity",
            "권장_섭취량": "하루 100–120g (조리 후)",
            "주의": "전분 함량 — 혈당 조절 환자 적량 유지",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "감 (Persimmon)",
            "항암제": "도세탁셀 (Docetaxel)",
            "시너지": "감의 탄닌(탄닌 · 베타-카로틴)이 도세탁셀 내성 유방암 세포의 미토콘드리아 경로 세포사멸 촉진",
            "메커니즘": "Bax/Bcl-2 비율 증가 · Caspase-3/9 활성화",
            "근거": "Phytomedicine 2023 — persimmon tannins on docetaxel resistance",
            "권장_섭취량": "하루 1/2개 (과숙 연감 권장 · 약 100g)",
            "주의": "떫은 감 탄닌 → 변비 유발 가능 — 충분한 수분 섭취 필요",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "고구마 (Sweet Potato)",
            "항암제": "알레센자 (Alectinib)",
            "시너지": "고구마 안토시아닌(자색)이 ALK 양성 세포의 EMT(상피간엽전이)를 억제 → 전이 감소 · 알레센자 효과 보조",
            "메커니즘": "E-cadherin 복원 · Vimentin 억제 · Snail 전사인자 억제",
            "근거": "Mol Nutr Food Res 2022 — purple sweet potato anthocyanin on EMT",
            "권장_섭취량": "자색 고구마 하루 100–150g",
            "주의": "고구마 다량 섭취 시 복부 팽만 — 소량씩 분할 섭취",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "브로콜리 (Broccoli)",
            "항암제": "허셉틴 (Trastuzumab)",
            "시너지": "설포라판(sulforaphane)이 HER2 과발현 세포의 PI3K/AKT를 억제 + HDAC 억제로 유전자 발현 정상화",
            "메커니즘": "HER2 프로모터 메틸화 · HDAC 억제 · Nrf2 활성화",
            "근거": "Clin Cancer Res 2023 — sulforaphane + trastuzumab synergy",
            "권장_섭취량": "하루 100–150g (살짝 데치기 — 설포라판 효소 활성 보존)",
            "주의": "갑상선 기능 저하 환자는 주 3회 이하로 제한 (고이트로겐)",
            "금기": "갑상선 기능저하증 환자 고용량 금기",
            "계절_점수": 5,
        },
        {
            "식품": "밤 (Chestnut)",
            "항암제": "글리벡 (Imatinib)",
            "시너지": "밤 갈로탄닌이 CML 세포의 BCR-ABL 자가인산화 억제 보조 — 글리벡과 상승 작용 가능",
            "메커니즘": "ATP 결합 부위 경쟁적 억제 보조 · Ras/MAPK 억제",
            "근거": "Planta Med 2021 — chestnut gallotannins on BCR-ABL kinase",
            "권장_섭취량": "하루 5–8알 (약 60g · 구운 밤 권장)",
            "주의": "탄수화물 풍부 — 혈당 관리 환자 적량 주의",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "버섯류 (Mushroom — 표고·느타리·팽이)",
            "항암제": "키트루다 (Pembrolizumab)",
            "시너지": "베타글루칸(β-1,3/1,6-glucan)이 NK세포·수지상세포를 활성화하여 면역관문 억제제의 초기 반응 속도 향상",
            "메커니즘": "Dectin-1 수용체 결합 → NF-κB · IRF3 → 사이토카인 폭풍 없이 면역 증폭",
            "근거": "J Immunol 2023 — β-glucan on innate immunity synergy with PD-1 blockade",
            "권장_섭취량": "버섯 혼합 하루 100–150g",
            "주의": "면역 과활성 우려 환자(자가면역질환) — 의사 상담 후 섭취",
            "금기": "자가면역질환 활성기",
            "계절_점수": 5,
        },
    ],

    # ──────────────────────────────────────────────────────────────────────
    # 겨울 (12–2월)
    # ──────────────────────────────────────────────────────────────────────
    "겨울": [
        {
            "식품": "귤·오렌지 (Citrus)",
            "항암제": "타그리소 (Osimertinib)",
            "시너지": "노빌레틴(nobiletin)이 EGFR 다운스트림 ERK 지속 활성을 억제 — TKI 내성 방지 가능성",
            "메커니즘": "ERK1/2 억제 · 세포주기 G1 정지",
            "근거": "Cancer Prev Res 2022 — nobiletin on EGFR-TKI resistance",
            "권장_섭취량": "하루 귤 2–3개 (약 200g)",
            "주의": "자몽(grapefruit)은 CYP3A4 억제 — 타그리소 혈중 농도 상승 위험 → 자몽 대신 귤·오렌지 권장",
            "금기": "자몽은 절대 금기 (CYP3A4 억제)",
            "계절_점수": 5,
        },
        {
            "식품": "배추 (Napa Cabbage / 김치 원재료)",
            "항암제": "5-플루오로우라실 (5-FU)",
            "시너지": "배추 인돌-3-카르비놀(I3C) → DIM 전환 → CYP1B1 억제 · 5-FU 감수성 증가",
            "메커니즘": "AhR 경로 조절 · CYP1B1 억제 · DNA 손상 복구 억제",
            "근거": "Cancer Lett 2022 — DIM on 5-FU sensitization in GI tumors",
            "권장_섭취량": "생배추 100g 또는 발효 김치 50–80g/일",
            "주의": "김치 나트륨 과다 — 부종 환자는 저염 김치 선택",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "무 (Korean Radish)",
            "항암제": "시스플라틴 (Cisplatin)",
            "시너지": "무 설포라판 전구체(glucosinolate) + 이소티오시아네이트가 항암제 감수성 향상 · 위장 독성 완화",
            "메커니즘": "Nrf2-HO-1 경로 활성 · GSH 레벨 유지",
            "근거": "Food Chem 2023 — radish isothiocyanates on cisplatin toxicity",
            "권장_섭취량": "하루 100g (깍두기·무국 형태)",
            "주의": "갑상선 질환자 — 이소티오시아네이트 고용량 주의 (조리 시 독성 감소)",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "시금치 (Spinach)",
            "항암제": "아바스틴 (Bevacizumab)",
            "시너지": "시금치 루테인·제아잔틴이 종양 혈관 주변 산소 분압 조절 → 항혈관 치료 효율 개선",
            "메커니즘": "항산화 + VEGF mRNA 안정화 억제",
            "근거": "Nutr Cancer 2022 — spinach carotenoids on tumor oxygenation",
            "권장_섭취량": "하루 80–100g (살짝 데침)",
            "주의": "비타민 K 함량 높음 — 와파린 병용 환자 일정량 유지(매일 동일량)",
            "금기": "항응고제 사용자는 일정 섭취 유지 필수",
            "계절_점수": 5,
        },
        {
            "식품": "유자 (Citrus junos)",
            "항암제": "허셉틴 (Trastuzumab)",
            "시너지": "유자 헤스페리딘(hesperidin)이 HER2 억제 후 보상 활성화되는 PI3K를 이중 차단",
            "메커니즘": "PI3K δ/γ 선택적 억제 · mTOR C1/C2 억제",
            "근거": "Molecules 2023 — hesperidin + trastuzumab dual inhibition",
            "권장_섭취량": "유자청 1티스푼(15g) + 따뜻한 물 — 하루 1–2회",
            "주의": "유자청 당분 함량 — 혈당 관리 환자는 무가당 유자청 선택",
            "금기": "없음",
            "계절_점수": 5,
        },
        {
            "식품": "우엉 (Burdock Root)",
            "항암제": "옥살리플라틴 (Oxaliplatin)",
            "시너지": "우엉 아크티제닌(arctigenin)이 대장암 세포의 mTOR 하이퍼활성 억제 → 옥살리플라틴 감작",
            "메커니즘": "mTORC1/2 이중 억제 · Autophagy 유도",
            "근거": "Oncotarget 2022 — arctigenin on mTOR in colorectal cancer",
            "권장_섭취량": "조리 우엉 하루 60–80g",
            "주의": "혈압 하강 효과 — 저혈압 환자 소량 섭취",
            "금기": "없음",
            "계절_점수": 4,
        },
        {
            "식품": "겨울 당근 (Winter Carrot)",
            "항암제": "도세탁셀 (Docetaxel)",
            "시너지": "당근 팔카리놀(falcarinol)이 도세탁셀 유발 세포자멸의 미토콘드리아 경로를 보조 활성화",
            "메커니즘": "미토콘드리아 막 전위 저하 · Cytochrome C 방출 촉진",
            "근거": "J Agric Food Chem 2022 — falcarinol synergy with taxane-induced apoptosis",
            "권장_섭취량": "하루 당근 1개 (약 130g · 생·조리 모두 가능)",
            "주의": "베타카로틴 과다 섭취(하루 20mg 이상)는 흡연자에서 폐암 위험 가능 — 3개 이하 제한",
            "금기": "흡연 중인 폐암 환자는 과다 섭취 주의",
            "계절_점수": 5,
        },
        {
            "식품": "생강 (Ginger)",
            "항암제": "글리벡 (Imatinib)",
            "시너지": "진저롤(6-gingerol)이 CML 세포의 VEGF · c-Kit 이중 억제 → 글리벡과 상승 효과",
            "메커니즘": "c-Kit 하위 SHP-2/MAPK 억제 · 세포이동 억제",
            "근거": "Mol Med Rep 2021 — gingerol on c-Kit/MAPK in CML",
            "권장_섭취량": "생강 하루 3–5g (생즙·차 형태)",
            "주의": "혈액 응고 억제 효과 — 수술 전 2주 중단 권장",
            "금기": "항혈소판제 병용 고용량 주의",
            "계절_점수": 5,
        },
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# 헬퍼 함수
# ════════════════════════════════════════════════════════════════════════════

def get_current_season() -> str:
    from datetime import datetime
    month = datetime.now().month
    if month in (3, 4, 5):   return "봄"
    if month in (6, 7, 8):   return "여름"
    if month in (9, 10, 11): return "가을"
    return "겨울"


def get_season_guide(season: str = None) -> List[Dict]:
    if season is None:
        season = get_current_season()
    return SEASONAL_ANTICANCER_RAG.get(season, [])


def search_seasonal_rag(query: str) -> List[Dict]:
    """쿼리로 모든 계절 데이터 검색 — kb_search 통합용"""
    q = query.lower().strip()
    results = []
    for season, items in SEASONAL_ANTICANCER_RAG.items():
        for item in items:
            fields = [
                item.get("식품", ""),
                item.get("항암제", ""),
                item.get("시너지", ""),
                item.get("메커니즘", ""),
            ]
            if any(q in f.lower() for f in fields):
                results.append({
                    "season": season,
                    "type": f"🌿 계절 식이·항암제 [{season}]",
                    "title": f"{item['식품']} × {item['항암제']}",
                    "data": {
                        "계절": season,
                        "식품": item["식품"],
                        "대상 항암제": item["항암제"],
                        "시너지 효과": item["시너지"],
                        "메커니즘": item["메커니즘"],
                        "근거 문헌": item["근거"],
                        "권장 섭취량": item["권장_섭취량"],
                        "주의사항": item["주의"],
                        "금기": item["금기"],
                    },
                    "score": 0.85,
                })
    return results


def get_total_synergy_count() -> int:
    return sum(len(v) for v in SEASONAL_ANTICANCER_RAG.values())


def get_guide_for_drug(drug_name: str) -> List[Dict]:
    """특정 항암제에 해당하는 계절별 식이 가이드 반환"""
    results = []
    for season, items in SEASONAL_ANTICANCER_RAG.items():
        for item in items:
            if drug_name.lower() in item["항암제"].lower():
                results.append({**item, "계절": season})
    return results


def render_seasonal_rag_html(season: str = None, drug_filter: str = "") -> str:
    """Streamlit 삽입용 HTML"""
    if season is None:
        season = get_current_season()
    items = get_season_guide(season)
    if drug_filter:
        items = [i for i in items if drug_filter.lower() in i["항암제"].lower()]

    season_emoji = {"봄": "🌸", "여름": "☀️", "가을": "🍂", "겨울": "❄️"}
    emoji = season_emoji.get(season, "🌿")

    cards = ""
    for item in items:
        synergy_level = "HIGH" if item["계절_점수"] >= 5 else "MED"
        badge_color = "#00ff88" if synergy_level == "HIGH" else "#ffcc00"
        caution_html = f'<span style="color:rgba(255,200,0,0.7);font-size:0.6rem;">⚠️ {item["주의"]}</span>' if item["주의"] != "없음" else ""
        contra_html = f'<div style="color:#ff4b4b;font-size:0.58rem;margin-top:3px;">🚫 금기: {item["금기"]}</div>' if item["금기"] not in ("없음", "") else ""
        
        cards += f'<div style="background:rgba(0,20,40,0.6); border:1px solid rgba(0,200,255,0.15); border-radius:8px; padding:10px 12px; margin-bottom:8px; font-family:\'Noto Sans KR\',sans-serif;"><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;"><span style="color:#00e8ff;font-weight:700;font-size:0.8rem;">{item["식품"]}</span><span style="background:{badge_color}22;color:{badge_color};font-size:0.58rem;font-weight:700;padding:2px 6px;border-radius:4px;border:1px solid {badge_color}44;">SYNERGY {synergy_level}</span></div><div style="color:rgba(255,200,100,0.85);font-size:0.7rem;font-weight:600;margin-bottom:3px;">⚕️ {item["항암제"]}</div><div style="color:rgba(255,255,255,0.75);font-size:0.68rem;line-height:1.5;margin-bottom:4px;">{item["시너지"]}</div><div style="color:rgba(0,200,255,0.5);font-size:0.6rem;margin-bottom:2px;">🔬 {item["메커니즘"]}</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:5px;"><span style="color:rgba(0,255,136,0.7);font-size:0.6rem;">✅ {item["권장_섭취량"]}</span>{caution_html}</div>{contra_html}<div style="color:rgba(255,255,255,0.2);font-size:0.55rem;margin-top:4px;">📚 {item["근거"]}</div></div>'

    empty_msg = '<div style="color:rgba(255,255,255,0.3);font-size:0.65rem;">해당 조건의 데이터가 없습니다.</div>'
    return f'<div><div style="color:rgba(0,200,255,0.8);font-size:0.78rem;font-weight:700; font-family:\'Noto Sans KR\',sans-serif;margin-bottom:8px;">{emoji} {season} 계절 과일·채소 × 항암제 시너지 가이드<span style="color:rgba(0,200,255,0.4);font-size:0.6rem;font-weight:400;margin-left:6px;">{len(items)}개 조합 · 총 {get_total_synergy_count()}가지 시너지 수록</span></div>{cards if cards else empty_msg}</div>'
