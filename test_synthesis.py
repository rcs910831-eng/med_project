from med_agent import MedicalAgent

def test_realtime_logic():
    print("=== [실시간 약물 식별 & 생활 수칙 합성 시스템 테스트] ===")
    agent = MedicalAgent()
    
    # 시뮬레이션: 사용자가 지르텍정 사진을 찍음
    test_pill_image = "pill_photo.jpg"
    
    # 로직 수행
    result = agent.analyze_pill_realtime(test_pill_image)
    
    print(f"\n[최종 합성 리포트 출력]:\n")
    print(result["report"])

if __name__ == "__main__":
    test_realtime_logic()
