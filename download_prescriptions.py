import os
import requests
import time

os.makedirs('data/images/prescriptions', exist_ok=True)

# 30년 약사가 엄선한 처방전 양식 및 샘플 이미지 소스
# (접근 가능한 공개된 이미지 주소 위주로 구성)
prescription_sources = [
    {"name": "prescription_sample_1", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Prescription_Sample.jpg/800px-Prescription_Sample.jpg"},
    {"name": "prescription_sample_2", "url": "https://cdn.pixabay.com/photo/2014/12/10/20/56/medical-563427_1280.jpg"},
    {"name": "prescription_sample_3", "url": "https://cdn.pixabay.com/photo/2017/02/01/13/52/analysis-2030261_1280.jpg"},
    {"name": "prescription_sample_4", "url": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Standard_Prescription_Form.png"},
    {"name": "prescription_sample_5", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Medical_Prescription.jpg/800px-Medical_Prescription.jpg"},
    # 한국 처방전 양식은 직접 URL 확보가 어려울 수 있어, 공공데이터/블로그 등에서 대중적으로 노출된 안정적인 링크 시도
    {"name": "kr_prescription_template", "url": "https://www.docdocdoc.co.kr/news/photo/202103/2008881_2011116_462.jpg"},
    {"name": "kr_prescription_sample_1", "url": "https://t1.daumcdn.net/cfile/tistory/2219803C586F158F2C"},
    {"name": "kr_prescription_sample_2", "url": "https://upload.wikimedia.org/wikipedia/ko/a/a2/%EC%B2%B2%EB%B0%A9%EC%A0%84_%EC%83%98%ED%94%8C.jpg"}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def download_prescriptions():
    for item in prescription_sources:
        print(f"[{item['name']}] 다운로드 중...")
        try:
            response = requests.get(item['url'], headers=headers, timeout=15)
            if response.status_code == 200:
                ext = "jpg" if "jpg" in item['url'].lower() else "png"
                file_path = f"data/images/prescriptions/{item['name']}.{ext}"
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f" -> 완료: {file_path}")
            else:
                print(f" -> 실패: HTTP {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f" -> 에러: {e}")

if __name__ == "__main__":
    download_prescriptions()
