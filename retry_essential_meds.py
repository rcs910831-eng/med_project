import os
import requests
import time

# 저장 경로
os.makedirs('data/images', exist_ok=True)

# 식약처 이미지 다운로드를 위한 더 정밀한 헤더 설정
# 실제 브라우저에서 검색 후 들어가는 것과 동일한 컨텍스트 재현
def smart_download(name, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://nedrug.mfds.go.kr/searchDoc', # 필수 Referer
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin'
    }
    
    try:
        # 세션을 유지하며 다운로드
        with requests.Session() as session:
            # 먼저 메인 검색 페이지를 방문하여 쿠키 확보
            session.get("https://nedrug.mfds.go.kr/searchDoc", headers=headers, timeout=10)
            time.sleep(1)
            
            response = session.get(url, headers=headers, timeout=20, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type or len(response.content) > 1000:
                    with open(f"data/images/{name}.jpg", 'wb') as f:
                        f.write(response.content)
                    print(f" -> 성공: {name}")
                    return True
            print(f" -> 실패: {name} (HTTP {response.status_code}, Type: {response.headers.get('Content-Type')})")
    except Exception as e:
        print(f" -> 에러: {name} - {e}")
    return False

med_list = [
    ("Champ_Red", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426399432600115"),
    ("Coldaewon_Blue", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/151028303004300067"),
    ("Brufen", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402287800040"),
    ("Panpyrin_Q", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398327800032"),
    ("Pancol_S", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426403816600055"),
    ("Geworin", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426425121400030"),
    ("Festal_Plus", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402120000078"),
    ("Dr_Bearse", "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398188100140")
]

if __name__ == "__main__":
    for name, url in med_list:
        smart_download(name, url)
        time.sleep(2)
