import sys
import os
import time

# 시스템 인코딩 설정
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 경로 추가
sys.path.append(os.getcwd())

from pharma_timeline_core import PatientTimelineManager
from pharma_v19_performance import monitor

def test_performance():
    print("🚀 PHARMA-HYBRID v19.1 성능 검증 시작...")
    
    # 1. 매니저 초기화
    manager = PatientTimelineManager(db_path=r'C:\PharmaProject\database\test_performance.db')
    
    # 2. 대량 데이터 삽입 테스트 (성능 측정)
    print("📊 10명 환자 병렬 등록 시뮬레이션...")
    start_total = time.time()
    for i in range(10):
        manager.add_patient(f"테스트환자_{i}", 40+i, "M")
    
    # 3. 처방 추가 테스트
    for i in range(10):
        p_id = manager.add_patient(f"테스트환자_{i}", 40+i, "M")
        manager.add_prescription(p_id, "고혈압", ["노바스크"], 30)
    
    total_duration = time.time() - start_total
    print(f"✅ 총 소요 시간: {total_duration:.3f}초")
    
    # 4. 성능 통계 확인
    print("\n📈 [PERFORMANCE METRICS]")
    for func in ['add_patient', 'add_prescription']:
        stats = monitor.get_stats(func)
        if stats:
            print(f"🔹 {func}: 평균 {stats['avg']:.4f}초 (총 {stats['count']}회 호출)")

if __name__ == "__main__":
    try:
        test_performance()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
