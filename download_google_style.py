import os
import requests
import time

# 저장 경로 설정
os.makedirs('data/images', exist_ok=True)

# 30년 약사가 엄선한 상비약 이미지 소스 (안정적인 일반 웹 이미지 및 공공 데이터 활용)
# 식약처 서버가 아닌 일반 이미지 서버나 위키미디어 등을 활용하여 차단 방지
med_image_sources = [
    # 1. 어린이 상비약
    {"name": "Champ_Red", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Acetaminophen_syrup_bottles.jpg/800px-Acetaminophen_syrup_bottles.jpg"}, # 챔프 대용 (아세트아미노펜 시럽)
    {"name": "Brufen_Kids", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Ibuprofen_syrup.jpg/800px-Ibuprofen_syrup.jpg"}, # 부루펜 대용
    
    # 2. 성인 상비약 (구글 검색 등을 통해 접근 가능한 이미지 예시)
    {"name": "Tylenol_500mg", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Tylenol_500_mg_capsules.jpg/800px-Tylenol_500_mg_capsules.jpg"},
    {"name": "Aspirin_100mg", "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Aspirin_tablets.jpg/800px-Aspirin_tablets.jpg"},
    
    # 실제 한국 약품들은 직접적인 고정 URL 확보가 어려울 경우 
    # 위와 같이 성분이 동일한 글로벌 표준 이미지로 먼저 학습 데이터를 구축하고,
    # 사용자님의 실물 사진을 추가로 받는 것이 AI 학습에 더 효과적입니다.
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def download_meds():
    for med in med_image_sources:
        print(f"[{med['name']}] 이미지 다운로드 중...")
        try:
            response = requests.get(med['url'], headers=headers, timeout=20)
            if response.status_code == 200:
                with open(f"data/images/{med['name']}.jpg", 'wb') as f:
                    f.write(response.content)
                print(f" -> 완료: {med['name']}.jpg")
            else:
                print(f" -> 실패: HTTP {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f" -> 에러: {e}")

if __name__ == "__main__":
    download_meds()
