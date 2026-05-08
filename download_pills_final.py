import os
import requests
import time

# 저장 디렉토리 설정
image_dir = 'data/images'
os.makedirs(image_dir, exist_ok=True)

# 다운로드 대상 정보 (식약처 공식 이미지 ID 기반)
med_data = [
    {"name": "Diabex_500mg.jpg", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398221100144"},
    {"name": "Plavix_75mg.jpg", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402446300130"},
    {"name": "Votrient_200mg.jpg", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/152342371457100063"},
    {"name": "Tylenol_500mg.jpg", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426425530100070"}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Referer': 'https://nedrug.mfds.go.kr/searchDoc',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

def download_pills():
    session = requests.Session()
    # 메인 페이지 접속으로 세션 활성화
    session.get("https://nedrug.mfds.go.kr/searchDoc", headers=headers)
    
    for item in med_data:
        file_path = os.path.join(image_dir, item['name'])
        print(f"다운로드 중: {item['name']}...")
        
        try:
            # 스트림 방식으로 다운로드 시도
            response = session.get(item['url'], headers=headers, stream=True, timeout=20)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 파일 크기 확인 (비정상적인 404 안내 페이지 다운로드 방지)
                if os.path.getsize(file_path) > 1000:
                    print(f" -> 완료: {item['name']} ({os.path.getsize(file_path)} bytes)")
                else:
                    print(f" -> 경고: 데이터가 너무 작습니다. (404 가능성)")
                    os.remove(file_path)
            else:
                print(f" -> 실패: HTTP {response.status_code}")
                
            time.sleep(1.5) # 서버 부하 방지
            
        except Exception as e:
            print(f" -> 에러: {e}")

if __name__ == "__main__":
    download_pills()
