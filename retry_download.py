import os
import requests
import time

# 저장 디렉토리
save_dir = 'data/images'
os.makedirs(save_dir, exist_ok=True)

# 식약처 공식 이미지 주소 (재검증된 고유 ID)
med_targets = {
    "Diabex_500mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398221100144",
    "Plavix_75mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402446300130",
    "Votrient_200mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/152342371457100063",
    "Tylenol_500mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426425530100070"
}

# 브라우저와 동일한 환경을 시뮬레이션하는 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://nedrug.mfds.go.kr/searchDoc',
    'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-origin'
}

def download_pills():
    with requests.Session() as session:
        # 첫 번째 요청으로 세션 쿠키 활성화
        session.get("https://nedrug.mfds.go.kr/searchDoc", headers=headers)
        
        for name, url in med_targets.items():
            file_path = os.path.join(save_dir, name)
            print(f"다운로드 중: {name}...")
            
            try:
                # 0바이트 파일이 있으면 미리 삭제
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                response = session.get(url, headers=headers, timeout=20)
                if response.status_code == 200 and len(response.content) > 1000:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f" -> [성공] {len(response.content)} 바이트 저장됨.")
                else:
                    print(f" -> [실패] 상태 코드: {response.status_code}, 데이터 크기: {len(response.content)}")
                
                time.sleep(2) # 서버 부하 방지 및 차단 회피
            except Exception as e:
                print(f" -> [에러] {e}")

if __name__ == "__main__":
    download_pills()
