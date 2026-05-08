from med_agent import agent
from privacy_guard import privacy_guard
import time
import sys
import io

# Windows 터미널 한글 깨짐 방지
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_scenario():
    print("="*60)
    print("   [med] 30년 경력 베테랑 하이브리드 AI 의료 에이전트 데모")
    print("="*60)
    time.sleep(1)

    # 1. 환자 기본 정보 (DNA)
    user_dna = {"vulnerabilities": "kidney"}
    morning_scan_data = {"edema_value": 0.08, "timestamp": "07:30 AM"}
    
    print("\n--- [STAGE 1] 기상 바이오 스캐닝 ---")
    stage1_res = agent.bio_scanning(user_dna, morning_scan_data)
    print(f"결과: {stage1_res['analysis']}")

    # 2. 처방전 판독 (충돌 시나리오)
    print("\n--- [STAGE 2] 처방전 & 알약 대조 (충돌 발생 시뮬레이션) ---")
    prescription_raw = "처방전: 환자 홍길동(900101-1234567) 리리카캡슐 75mg"
    pill_img_data = {"detected_drug": "아토젯정"} # 충돌 상황: 처방은 리리카, 실제는 아토젯
    
    stage2_res = agent.analyze_prescription(prescription_raw, pill_img_data)
    print(f"마스킹된 텍스트: {stage2_res['masked_text']}")
    print(f"충돌 해결 로직: {stage2_res['resolution']['message']}")

    # 3. 심화 데이터 분석 (RAG)
    print("\n--- [STAGE 3] CT/MRI 연동 심화 분석 ---")
    ct_report = "환자의 저번 주 CT상 간 수치가 경계선에 있음 확인."
    # 앞서 OCR에서 추출된 것으로 가정한 약 이름 사용
    stage3_res = agent.deep_analysis("리리카캡슐", ct_report)
    for insight in stage3_res['expert_insights']:
        print(f"베테랑 인사이트: {insight}")

    # 4. 생활 관리 코칭
    print("\n--- [STAGE 4] 맞춤형 식단 및 운동 제안 ---")
    stage4_res = agent.generate_lifestyle_coaching("S병원", "kidney", "리리카캡슐")
    print(f"오늘의 식단: {stage4_res['diet_reco']}")
    print(f"오늘의 운동: {stage4_res['exercise_reco']}")

    # 5. 응급 상황 (시뮬레이션)
    print("\n--- [STAGE 5] 안전망 (응급 메시지 생성) ---")
    location = {"lat": 37.5665, "lng": 126.9780, "landmark": "서울시청 인근 자택"}
    emergency_msg = agent.trigger_emergency_alert(location, "호흡 곤란 및 어지러움", ["리리카캡슐", "혈압약"])
    print(emergency_msg)

    print("\n" + "="*60)
    print("데모가 성공적으로 완료되었습니다.")
    print("="*60)

if __name__ == "__main__":
    run_scenario()
