import os
import requests
import time
from PIL import Image
import io

# 디렉토리 생성
os.makedirs('data/images', exist_ok=True)

# 30년 약사가 선정한 필수 상비약 및 어린이 약 목록 (식약처 이미지 ID 기반)
med_download_list = [
    # 1. 어린이 약
    {"name": "Champ_Red_Syrup", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426399432600115"}, # 챔프시럽 (아세트아미노펜)
    {"name": "Coldaewon_Kids_Blue", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/151028303004300067"}, # 콜대원키즈 코감기
    {"name": "Brufen_Syrup", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402287800040"}, # 부루펜시럽
    {"name": "Citus_Tab", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426399228800160"}, # 씨투스정
    
    # 2. 일반 성인 상비약
    {"name": "Panpyrin_Q", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398327800032"}, # 판피린큐액
    {"name": "Pancol_S", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426403816600055"}, # 판콜에스내복액
    {"name": "Modecol_S", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/148782333647100063"}, # 모드콜에스
    {"name": "Geworin_Tab", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426425121400030"}, # 게보린정
    
    # 3. 소화계 및 기타
    {"name": "Festal_Plus", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402120000078"}, # 훼스탈플러스
    {"name": "Dr_Bearse", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426398188100140"}, # 닥터베아제
    {"name": "Buscopan_Plus", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426403063800094"}, # 부스코판당의정
    {"name": "Norumo_Tab", "url": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/147426402324300122"}  # 노루모정
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Referer': 'https://nedrug.mfds.go.kr/searchDoc',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
}

def download_and_save():
    session = requests.Session()
    # 세션 활성화
    try:
        session.get("https://nedrug.mfds.go.kr/searchDoc", headers=headers, timeout=10)
    except:
        pass

    for med in med_download_list:
        file_path = f"data/images/{med['name']}.jpg"
        print(f"[{med['name']}] 다운로드 시도 중...")
        
        try:
            response = session.get(med['url'], headers=headers, timeout=20)
            if response.status_code == 200 and len(response.content) > 1000:
                # 이미지 무결성 확인 및 저장
                img = Image.open(io.BytesIO(response.content))
                img = img.convert('RGB')
                img.save(file_path, "JPEG", quality=90)
                print(f" -> 완료: {file_path}")
            else:
                print(f" -> 실패: 상태코드 {response.status_code}, 크기 {len(response.content)}")
            
            time.sleep(1.5) # 서버 부하 방지
        except Exception as e:
            print(f" -> 에러: {e}")

if __name__ == "__main__":
    download_and_save()
