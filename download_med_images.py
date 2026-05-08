import os
import requests
import re
import time

# 디렉토리 생성
os.makedirs('data/images', exist_ok=True)

def download_images():
    try:
        # UTF-8로 파일 읽기
        with open('target_image_urls.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or ': ' not in line:
                continue
            
            drug_name, url = line.split(': ', 1)
            
            # 파일명 정제 (한글 유지)
            safe_name = re.sub(r'[^\w\s-]', '', drug_name).strip().replace(' ', '_')
            file_path = f'data/images/{safe_name}.jpg'
            
            # 도메인에 따른 Referer 설정
            domain = "https://www.health.kr/"
            if "mfds.go.kr" in url:
                domain = "https://nedrug.mfds.go.kr/"
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Referer': domain,
                'Connection': 'keep-alive'
            }
            
            print(f"Downloading: {drug_name}...")
            
            try:
                # 3번의 재시도 로직
                for attempt in range(3):
                    try:
                        response = requests.get(url, headers=headers, stream=True, timeout=15)
                        if response.status_code == 200:
                            with open(file_path, 'wb') as img_file:
                                for chunk in response.iter_content(4096):
                                    img_file.write(chunk)
                            print(f" -> SUCCESS: {file_path}")
                            break
                        else:
                            print(f" -> ATTEMPT {attempt+1} FAILED (HTTP {response.status_code})")
                            time.sleep(2)
                    except Exception as e:
                        print(f" -> ATTEMPT {attempt+1} ERROR: {e}")
                        time.sleep(2)
                else:
                    print(f" -> FINAL FAILURE: {drug_name}")
                
                time.sleep(1) # 서버 매너
                
            except Exception as e:
                print(f" -> ERROR for {drug_name}: {e}")
                
    except Exception as e:
        print(f"Global error: {e}")

if __name__ == "__main__":
    download_images()
