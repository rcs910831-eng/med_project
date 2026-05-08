import json

file_path = r'c:\Users\rcs91\github\med_project\AI_Pharmacist_Tutorial.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        
        # Update DatasetLoader definition in Cell 4
        if "class DatasetLoader:" in source and "def __init__(self, kb_path='knowledge_base.json'):" in source:
            new_source = source.replace(
                "def __init__(self, kb_path='knowledge_base.json'):",
                "def __init__(self, db_root='C:/PharmaProject/database', legacy_kb_path='knowledge_base.json', kb_path=None):"
            )
            cell['source'] = [line + ("\n" if not line.endswith("\n") else "") for line in new_source.splitlines()]
            
        # Update MedicalAgent definition in Cell 5
        if "class MedicalAgent:" in source and "self.loader = DatasetLoader(kb_path=knowledge_base_path)" in source:
            new_source = source.replace(
                "def __init__(self, knowledge_base_path: str = \"knowledge_base.json\"): \n        # 데이터셋 로더 초기화\n        self.loader = DatasetLoader(kb_path=knowledge_base_path)",
                "def __init__(self, db_root: str = \"C:/PharmaProject/database\", kb_path: str = \"knowledge_base.json\"): \n        # 데이터셋 로더 초기화\n        self.loader = DatasetLoader(db_root=db_root, kb_path=kb_path)"
            )
            # Actually simpler to just target the line 447
            new_source = source.replace(
                "self.loader = DatasetLoader(kb_path=knowledge_base_path)",
                "self.loader = DatasetLoader(kb_path=knowledge_base_path) # Now supported by modules.dataset_loader"
            )
            # No, let's be more thorough if needed. 
            # But the fix in the module already makes the existing code work.

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Successfully updated the tutorial notebook.")
