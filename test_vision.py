from gemini_ai_engine import call_gemini_vision
import os

img_path = r"C:\Users\rcs91\github\med_project\prescription_images\RX_P001.png"
with open(img_path, "rb") as f:
    img_bytes = f.read()

prompt = "이 처방전에서 약품 이름만 추출해줘."
print("Calling Gemini Vision...")
res = call_gemini_vision(img_bytes, "image/png", prompt)
print(f"Response: {res}")
