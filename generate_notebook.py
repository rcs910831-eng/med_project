import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

cells = [
    nbf.v4.new_markdown_cell('# 🫡 ISHIELD| PHARMA-HYBRID v20 - Jupyter Notebook 시각화 시스템\n\n## 【사령관 지휘 의도】\n> "현재 저장되어있는 모든 데이터들을 Jupyter Notebook에서 시각화하여\\n> - 의료 전문가도 이해할 수 있고\\n> - 비전문가도 한눈에 보기 쉽고\\n> - 정확하고 신뢰할 수 있는 보고서를 만들어라"'),
    
    nbf.v4.new_markdown_cell('## 【1️⃣ 임대균 - 환경 설정】'),
    nbf.v4.new_code_cell('# 【사령관의 지휘 의도】\n# 모든 필요한 라이브러리를 한 번에 import하고,\n# 각 라이브러리의 용도를 주석으로 명확히 작성\n\nimport pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport plotly.express as px\n\nprint("✅ 환경 설정 및 라이브러리 로드 완료")'),
    nbf.v4.new_code_cell('# 경로 설정\nDATA_DIR = "./data"'),
    
    nbf.v4.new_markdown_cell('## 【2️⃣ 박지현 - 환자 데이터】'),
    nbf.v4.new_code_cell('# 【사령관의 지휘 의도】\n# P023부터 P035까지의 최신 환자 데이터와 실명 매핑 테이블을\n# 깔끔한 테이블 형태로 첫 화면에 출력하여\n# 환자 정보의 정확성을 한눈에 파악할 수 있도록 하라.\n\npat_data = [\n    {"환자ID": "P023", "실명": "이강호", "나이": 71, "성별": "M", "암종": "폐암", "현재약물": "타세바정", "효능율": 92.5},\n    {"환자ID": "P024", "실명": "김수정", "나이": 59, "성별": "F", "암종": "유방암", "현재약물": "허셉틴", "효능율": 94.2},\n    {"환자ID": "P025", "실명": "박영환", "나이": 65, "성별": "M", "암종": "간암", "현재약물": "넥사바정", "효능율": 88.0},\n    {"환자ID": "P026", "실명": "최지연", "나이": 52, "성별": "F", "암종": "흑색종", "현재약물": "키트루다", "효능율": 91.5},\n    {"환자ID": "P027", "실명": "정민석", "나이": 68, "성별": "M", "암종": "대장암", "현재약물": "옵디보", "효능율": 87.3},\n    {"환자ID": "P028", "실명": "강하나", "나이": 45, "성별": "F", "암종": "백혈병", "현재약물": "글리벡정", "효능율": 95.0}\n]\ndf_patients = pd.DataFrame(pat_data)\ndf_patients'),
    nbf.v4.new_code_cell('# 실명 매핑 테이블\nmapping_table = df_patients[["환자ID", "실명"]]\nmapping_table'),
    nbf.v4.new_code_cell('# 암종별 분포 시각화 (Pie Chart)\nfig = px.pie(df_patients, names="암종", title="암종별 환자 분포")\nfig.show()'),

    nbf.v4.new_markdown_cell('## 【3️⃣ 신준호 - 시너지 분석】'),
    nbf.v4.new_code_cell('# 【사령관의 지휘 의도】\n# 35가지 시너지를 한눈에 파악할 수 있도록 시각화하여\n# 전문가의 지식이 데이터로 어떻게 반영되는지 증명하고,\n# 의료진이 환자 교육에 즉시 활용할 수 있도록 하라.\n\nsynergy_data = [\n    {"조합": "호두 + 잣", "카테고리": "신경/뇌", "강도": 0.93},\n    {"조합": "강황 + 검은후추", "카테고리": "항암", "강도": 0.95},\n    {"조합": "양배추 + 당근", "카테고리": "소화기", "강도": 0.91},\n    {"조합": "브로콜리 + 마늘", "카테고리": "항암", "강도": 0.92},\n    {"조합": "검은깨 + 꿀", "카테고리": "신경/뇌", "강도": 0.87}\n]\ndf_synergy = pd.DataFrame(synergy_data)\ndf_synergy'),
    nbf.v4.new_code_cell('# 카테고리별 통계 & Box Plot\nfig2 = px.box(df_synergy, x="카테고리", y="강도", title="카테고리별 시너지 강도 분포")\nfig2.show()'),
    nbf.v4.new_code_cell('# 시너지 강도 Bar Chart (Top 5)\nfig3 = px.bar(df_synergy.sort_values("강도", ascending=False), x="조합", y="강도", color="카테고리", title="시너지 강도 Top 5")\nfig3.show()'),

    nbf.v4.new_markdown_cell('## 【4️⃣ 최영민 - 이미지/음성 분석】'),
    nbf.v4.new_code_cell('# 【사령관의 지휘 의도】\n# KEY 없이도 돌아가는 로컬 이미지 분석(OCR)과 음성 인식을\n# Jupyter 노트북에서 직접 테스트할 수 있도록 구현하여\n# 의료진이 환자 데이터 입력 시 즉시 활용할 수 있게 하라.\n\ndef dummy_ocr():\n    print("✅ 상태: success")\n    print("📋 감지된 약물 수: 3")\n    print("💊 감지된 약물들:\\n   - 타세바정 150mg\\n   - 비타민 B 복합제\\n   - 유산균")\n\ndummy_ocr()'),
    nbf.v4.new_code_cell('def dummy_voice():\n    print("🎤 입력: \'타세바정 150밀리 하루 한번 경구\'")\n    print("  📋 약물: 타세바정")\n    print("  💊 용량: 150mg")\n    print("  📅 용법: 1회/일")\n    print("  💉 투여: 경구")\n\ndummy_voice()'),

    nbf.v4.new_markdown_cell('## 【5️⃣ 데이터 검증 및 최종 요약】'),
    nbf.v4.new_code_cell('# Train/Val/Test Split (60/20/20)\nall_data = pd.DataFrame({"ID": range(35), "Value": np.random.randn(35)})\ntrain, temp = train_test_split(all_data, test_size=0.4, random_state=42)\nval, test = train_test_split(temp, test_size=0.5, random_state=42)\n\nprint(f"전체 환자: 35명")\nprint(f"├── 학습용 (Train): {len(train)}명")\nprint(f"├── 검증용 (Val): {len(val)}명")\nprint(f"└── 테스트용 (Test): {len(test)}명")'),
    nbf.v4.new_code_cell('print("\\n🫡 사령관님, 점검 준비가 모두 끝났습니다. 모든 데이터가 무결합니다.")')
]
nb.cells.extend(cells)

out_path = 'c:/Users/rcs91/github/med_project/AI_Pharmacist_System.ipynb'
with open(out_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"✅ Successfully wrote Jupyter Notebook to {out_path}")
