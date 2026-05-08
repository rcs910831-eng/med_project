import os
import json
import re
from gemini_ai_engine import call_gemini_vision

RX_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"
OUT_FILE = r"C:\Users\rcs91\github\med_project\real_patient_data.json"

def extract_screenshots():
    files = [f for f in os.listdir(RX_DIR) if "스냅샷" in f and f.lower().endswith((".png", ".jpg", ".jpeg"))]
    files = sorted(files)
    
    # Load existing data
    all_data = {}
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except: pass

    prompt = """
    이 처방전/의료기록 이미지에서 다음 정보를 JSON 형식으로 추출해줘:
    {
        "pid": "ID가 있으면 추출, 없으면 'NEW'",
        "name": "환자 이름 (실명)",
        "age": "나이 (숫자만)",
        "gender": "성별 (남/여)",
        "hospital": "병원 이름",
        "disease_main": "주진료 병명",
        "disease_sub": "부진료 병명"
    }
    """
    
    # Map screenshots to P031, P032, P033
    new_id_start = 31
    for f in files:
        pid = f"P{new_id_start:03d}"
        print(f"Vision Extracting {pid} from Screenshot {f}...")
        path = os.path.join(RX_DIR, f)
        with open(path, "rb") as img_file:
            img_bytes = img_file.read()
            
        try:
            res = call_gemini_vision(img_bytes, "image/png", prompt)
            json_str = re.search(r'\{.*\}', res, re.DOTALL).group(0)
            data = json.loads(json_str)
            
            data["pid"] = pid
            all_data[pid] = data
            new_id_start += 1
            
            print(f"  Result: {data.get('name')} / {data.get('disease_main')}")
        except Exception as e:
            print(f"  Error processing {pid}: {e}")
            
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        json.dump(all_data, out, ensure_ascii=False, indent=4)
    print("\nScreenshots Extracted. Registry updated to P033.")

if __name__ == "__main__":
    extract_screenshots()
