
import sys

# Define the data here (copied from the file for quick check)
# Actually, I'll just read the file and extract them with a regex to be safe.
with open('c:/Users/rcs91/github/med_project/전부_코드화_데이터통합시스템.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract PATIENTS and MED_INFO
# This is a bit hacky but works for a quick check.
import re

patients_match = re.search(r'PATIENTS = \{(.*?)\n\}', content, re.DOTALL)
med_info_match = re.search(r'MED_INFO = \{(.*?)\n\}', content, re.DOTALL)

if patients_match and med_info_match:
    # Use exec to load them into the current namespace (carefully)
    try:
        exec(patients_match.group(0))
        exec(med_info_match.group(0))
        
        missing_drugs = set()
        for pid, data in PATIENTS.items():
            for med in data['meds']:
                name = med['name']
                if name not in MED_INFO:
                    missing_drugs.add(name)
        
        if missing_drugs:
            print("Missing drugs in MED_INFO:")
            for d in sorted(missing_drugs):
                print(f"- {d}")
        else:
            print("All drugs in PATIENTS are present in MED_INFO.")
    except Exception as e:
        print(f"Error executing extracted code: {e}")
else:
    print("Could not find PATIENTS or MED_INFO dictionaries.")
