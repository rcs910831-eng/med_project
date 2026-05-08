import os
import json
import base64
from gemini_ai_engine import call_gemini_vision

RX_DIR = r"C:\Users\rcs91\github\med_project\prescription_images"
OUT_FILE = r"C:\Users\rcs91\github\med_project\real_patient_data.json"

def extract_all_data():
    files = [f for f in os.listdir(RX_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    all_data = {}
    
    prompt = """
    이 처방전 이미지에서 다음 정보를 JSON 형식으로 추출해줘:
    {
        "pid": "파일명에서 추출한 ID (예: P001)",
        "name": "환자 이름",
        "age": "나이 (숫자만)",
        "gender": "성별",
        "hospital": "병원 이름",
        "disease_main": "주진료 병명",
        "disease_sub": "부진료 병명 (없으면 빈문자열)",
        "meds": [
            {
                "type": "주진료 또는 부진료",
                "name": "약물 이름",
                "dosage": "1회 투약량",
                "frequency": "1일 투약횟수",
                "duration": "총 투약일수",
                "note": "주의사항"
            }
        ]
    }
    """
    
    for f in files:
        pid_match = re.search(r'P(\d+)', f)
        if not pid_match: continue
        pid = f"P{pid_match.group(1)}"
        
        print(f"Processing {f}...")
        path = os.path.join(RX_DIR, f)
        with open(path, "rb") as img_file:
            img_bytes = img_file.read()
            
        try:
            res = call_gemini_vision(img_bytes, "image/png", prompt)
            # JSON parsing (robust)
            json_str = re.search(r'\{.*\}', res, re.DOTALL).group(0)
            data = json.loads(json_str)
            all_data[pid] = data
        except Exception as e:
            print(f"Error processing {pid}: {e}")
            
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        json.dump(all_data, out, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    import re
    extract_all_data()
