import json

file_path = r'c:\Users\rcs91\github\med_project\AI_Pharmacist_Tutorial.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        
        # Correcting Cell 4 (DatasetLoader definition)
        if "class DatasetLoader:" in source_text and "def __init__(self," in source_text:
            new_code = [
                "import json\n",
                "import os\n",
                "\n",
                "class DatasetLoader:\n",
                "    def __init__(self, db_root='C:/PharmaProject/database', legacy_kb_path='knowledge_base.json', kb_path=None):\n",
                "        self.db_root = db_root\n",
                "        self.legacy_kb_path = kb_path if kb_path is not None else legacy_kb_path\n",
                "        self.kb = self._load_database()\n",
                "\n",
                "    def _load_database(self):\n",
                "        # 시뮬레이션: 실제 파일 시스템 로직은 modules/dataset_loader.py에 구현되어 있음\n",
                "        if os.path.exists(os.path.join(self.db_root, 'master_data')):\n",
                "            return {'drugs': []} # 신규 DB 모드\n",
                "        return self._load_legacy_kb()\n",
                "\n",
                "    def _load_legacy_kb(self):\n",
                "        if not os.path.exists(self.legacy_kb_path):\n",
                "            return {'drugs': [{'name': '타이레놀', 'visual_descriptors': {'color': '흰색', 'shape': '장방형'}}, {'name': '탁센', 'visual_descriptors': {'color': '청색', 'form': '연질캡슐'}}]}\n",
                "        with open(self.legacy_kb_path, 'r', encoding='utf-8') as f:\n",
                "            return json.load(f)\n",
                "\n",
                "    def find_drug_by_visual(self, detected_features):\n",
                "        matches = []\n",
                "        for drug in self.kb.get('drugs', []):\n",
                "            viz = drug.get('visual_descriptors', {})\n",
                "            score = 0\n",
                "            for key, val in detected_features.items():\n",
                "                if key in viz and val in viz[key]:\n",
                "                    score += 1\n",
                "            if score > 0: matches.append((score, drug))\n",
                "        matches.sort(key=lambda x: x[0], reverse=True)\n",
                "        return matches[0][1] if matches else None\n",
                "\n",
                "    def find_drug_by_text(self, ocr_text):\n",
                "        for drug in self.kb.get('drugs', []):\n",
                "            if drug['name'] in ocr_text: return drug\n",
                "        return None\n",
                "\n",
                "    def cross_verify(self, ocr_data, vlm_data):\n",
                "        drug_from_text = self.find_drug_by_text(ocr_data)\n",
                "        drug_from_visual = self.find_drug_by_visual(vlm_data)\n",
                "        if not drug_from_text or not drug_from_visual: return {'status': 'warning', 'message': '⚠️ 식별 실패'}\n",
                "        if drug_from_text['name'] == drug_from_visual['name']:\n",
                "            return {'status': 'success', 'message': f'✅ 일치: {drug_from_text[\"name\"]}'}\n",
                "        return {'status': 'critical', 'message': f'🚨 불일치: 봉투({drug_from_text[\"name\"]}) vs 실제({drug_from_visual[\"name\"]})'}\n",
                "\n",
                "if __name__ == '__main__':\n",
                "    loader = DatasetLoader()\n",
                "    print('DatasetLoader 초기화 완료')\n"
            ]
            cell['source'] = new_code

        # Correcting Cell 5 (MedicalAgent definition)
        if "class MedicalAgent:" in source_text and "self.loader = DatasetLoader" in source_text:
            # We want to make sure it uses the new init style
            new_code = [
                "from modules.privacy_guard import PrivacyGuard\n",
                "from modules.dataset_loader import DatasetLoader\n",
                "from vision_engine import VisionEngine\n",
                "\n",
                "privacy_guard = PrivacyGuard()\n",
                "\n",
                "class MedicalAgent:\n",
                "    def __init__(self, db_root='C:/PharmaProject/database', kb_path='knowledge_base.json'):\n",
                "        # 하위 호환성을 위해 kb_path를 DatasetLoader에 전달\n",
                "        self.loader = DatasetLoader(db_root=db_root, kb_path=kb_path)\n",
                "        self.kb = self.loader.kb\n",
                "        self.vision = VisionEngine()\n",
                "\n",
                "    def analyze_prescription(self, p_img, pill_img):\n",
                "        # 단순화된 데모 로직\n",
                "        vision_result = self.vision.process_hybrid_vision(p_img, pill_img)\n",
                "        masked_text = privacy_guard.mask_pii(vision_result['ocr_text'])\n",
                "        verification = self.loader.cross_verify(masked_text, vision_result['vlm_analysis'])\n",
                "        return {'verification_result': verification}\n",
                "\n",
                "if __name__ == '__main__':\n",
                "    agent = MedicalAgent()\n",
                "    print('MedicalAgent 초기화 완료')\n"
            ]
            cell['source'] = new_code

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print("Tutorial notebook fixed successfully.")
