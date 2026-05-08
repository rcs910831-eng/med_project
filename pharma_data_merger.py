import json
import os

MASTER_DATA_DIR = r'C:\PharmaProject\database\master_data'
OUTPUT_FILE = os.path.join(MASTER_DATA_DIR, 'master_medication_dictionary_extended_v25.json')

FILES_TO_MERGE = [
    os.path.join(MASTER_DATA_DIR, 'drugs.json'),
    os.path.join(MASTER_DATA_DIR, 'master_medication_dictionary.json'),
    os.path.join(MASTER_DATA_DIR, 'comprehensive_medication_db_v24.json'),
    r'C:\PharmaProject\database\clinical\cancer_master_db_v24.json'
]

def merge_intelligence():
    unified_db = {}
    
    for file_path in FILES_TO_MERGE:
        if not os.path.exists(file_path):
            print(f"[Skip] File not found: {file_path}")
            continue
            
        print(f"[Process] Merging: {os.path.basename(file_path)}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 1. drugs.json 스타일 (리스트 형태)
            if isinstance(data, list):
                for item in data:
                    name = item.get('name')
                    if not name: continue
                    if name not in unified_db: unified_db[name] = {}
                    unified_db[name].update(item)
            
            # 2. 마스터 사전 스타일 (medications 키 포함)
            elif 'medications' in data:
                # 리스트 형태 medications
                if isinstance(data['medications'], list):
                    for item in data['medications']:
                        name = item.get('name')
                        if not name: continue
                        if name not in unified_db: unified_db[name] = {}
                        unified_db[name].update(item)
                # 딕셔너리 형태 (diseases 아래)
                elif isinstance(data['medications'], dict):
                    for m_id, m_info in data['medications'].items():
                        name = m_info.get('name', m_id)
                        if name not in unified_db: unified_db[name] = {}
                        unified_db[name].update(m_info)
            
            # 3. v24 종합 DB 스타일 (diseases 키 아래)
            if 'diseases' in data:
                for d_id, d_info in data['diseases'].items():
                    if 'medications' in d_info:
                        for med in d_info['medications']:
                            name = med.get('name')
                            if not name: continue
                            if name not in unified_db: unified_db[name] = {}
                            unified_db[name].update(med)
                            unified_db[name]['category'] = d_info.get('name', d_id)
                            
            # 4. 암종 DB 스타일 (cancers 키 아래)
            if 'cancers' in data:
                for c_id, c_info in data['cancers'].items():
                    name = c_info.get('korean_name', c_id)
                    if name not in unified_db: unified_db[name] = {}
                    unified_db[name].update(c_info)
                    unified_db[name]['is_cancer_data'] = True

    # 최종 저장
    final_data = {
        "metadata": {
            "version": "25.0 ULTIMATE",
            "last_merged": "2026-04-27",
            "total_entries": len(unified_db),
            "description": "All medication and cancer data unified with extra explanations preserved."
        },
        "medications": list(unified_db.values())
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SUCCESS] Unified Database Created: {OUTPUT_FILE}")
    print(f"Total Unique Entries: {len(unified_db)}")

if __name__ == "__main__":
    merge_intelligence()
