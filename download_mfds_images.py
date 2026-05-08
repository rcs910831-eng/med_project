import os
import requests
import time

# 저장 폴더 생성
os.makedirs('data/images', exist_ok=True)

# 식약처 공식 이미지 주소 리스트
med_images = {
    "Norvasc_5mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426403087300104",
    "Diabex_500mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398221100144",
    "Plavix_75mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402446300130",
    "Votrient_200mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/152342371457100063",
    "Tylenol_500mg.jpg": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426425530100070"
}

# 브라우저와 동일한 환경 설정을 위한 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://nedrug.mfds.go.kr/searchDoc',
    'Connection': 'keep-alive'
}

def download_images():
    session = requests.Session()
    # 첫 접속을 통해 세션 쿠키 확보 시도
    session.get("https://nedrug.mfds.go.kr/searchDoc", headers=headers)
    
    for filename, url in med_images.items():
        print(f"진행 중: {filename} 다운로드 시도...")
        try:
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(f"data/images/{filename}", 'wb') as f:
                    f.write(response.content)
                print(f" -> 성공: {filename} ({len(response.content)} bytes)")
            else:
                print(f" -> 실패: {filename} (상태 코드: {response.status_code}, 데이터 크기: {len(response.content)})")
            
            time.sleep(2) # 서버 과부하 및 차단 방지
        except Exception as e:
            print(f" -> 에러 발생: {filename} - {e}")

if __name__ == "__main__":
    download_images()
