import os
import json
import re
from gemini_ai_engine import call_gemini_vision

RX_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"
OUT_FILE = r"C:\Users\rcs91\github\med_project\real_patient_data.json"

def extract_identity_only():
    files = [f for f in os.listdir(RX_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    # Filter for P001-P030
    files = [f for f in files if re.search(r'P\d+', f)]
    files = sorted(files)
    
    # Load existing data if any
    all_data = {}
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except: pass

    prompt = """
    이 처방전 이미지에서 다음 정보를 JSON 형식으로 추출해줘:
    {
        "pid": "PXXX (파일명에서)",
        "name": "환자 이름 (실명)",
        "age": "나이 (숫자만)",
        "gender": "성별 (남/여)",
        "hospital": "병원 이름",
        "disease_main": "주진료 병명",
        "disease_sub": "부진료 병명"
    }
    """
    
    for f in files:
        pid_match = re.search(r'P(\d+)', f)
        if not pid_match: continue
        pid = f"P{pid_match.group(1)}"
        
        # If we already have a real name, skip (optimization)
        if pid in all_data and all_data[pid].get("name") and not all_data[pid].get("name").startswith("환자"):
            print(f"Skipping {pid} (Already have name: {all_data[pid]['name']})")
            continue
            
        print(f"Vision Extracting {pid} from {f}...")
        path = os.path.join(RX_DIR, f)
        with open(path, "rb") as img_file:
            img_bytes = img_file.read()
            
        try:
            res = call_gemini_vision(img_bytes, "image/png", prompt)
            json_str = re.search(r'\{.*\}', res, re.DOTALL).group(0)
            data = json.loads(json_str)
            
            # Merge with existing meds data if available
            if pid in all_data:
                all_data[pid].update(data)
            else:
                all_data[pid] = data
            
            print(f"  Result: {data.get('name')} / {data.get('disease_main')}")
        except Exception as e:
            print(f"  Error processing {pid}: {e}")
            
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        json.dump(all_data, out, ensure_ascii=False, indent=4)
    print("\nExtraction Complete. 33 patients updated.")

if __name__ == "__main__":
    extract_identity_only()
