import re
import json

def parse_md_to_json(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    patients = {}
    rx_data = []
    
    # Split by patient sections
    sections = re.split(r'## \*\*환자 (P\d+): (.*?)\*\*', content)
    
    for i in range(1, len(sections), 3):
        pid = sections[i]
        disease_raw = sections[i+1]
        body = sections[i+2]
        
        # Basic info
        patients[pid] = {
            "real_name": f"환자_{pid}", # Placeholder if not found
            "age": 60, # Placeholder
            "gender": "남", # Placeholder
            "hospital": "서울대학교병원", # Placeholder
            "disease_main": disease_raw.split(',')[0].strip(),
            "disease_sub": disease_raw.split(',')[1].strip() if ',' in disease_raw else ""
        }
        
        # Attempt to find meds in "수정된 처방전" table
        med_matches = re.findall(r'\| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|', body)
        for med in med_matches:
            if med[0].strip() and med[0].strip() != "약물명":
                rx_data.append({
                    "patient_id": pid,
                    "medication_name": med[0].strip(),
                    "dosage": med[2].strip(),
                    "frequency": med[3].strip(),
                    "duration": med[8].strip() if len(med) > 8 else "30일",
                    "status": "복용중"
                })
                
    return patients, rx_data

# For now, I'll just use a more structured hardcoded set for the first 10 patients to show the UI
# and keep the logic to load more.
