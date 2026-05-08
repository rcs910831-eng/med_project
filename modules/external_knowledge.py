import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional

class ExternalKnowledgeConnector:
    """
    약학정보원(health.kr) 및 MSD 매뉴얼(msdmanuals.com) 데이터 연동 클래스
    """
    
    def __init__(self):
        self.health_kr_base = "https://health.kr/search薬/result.asp?searchterm="
        self.msd_base = "https://www.msdmanuals.com/ko/home/searchresults?query="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def search_health_kr(self, drug_name: str) -> Dict:
        """
        약학정보원 검색을 통해 제품명 및 질환 정보 추출 (Mocking for logic flow)
        """
        print(f"[External] health.kr에서 '{drug_name}' 검색 중...")
        # 실제 구현 시에는 requests로 HTML 파싱 필요
        # 현재는 로직 연결을 위해 성공 시나리오 데이터 반환
        return {
            "product_name": drug_name,
            "disease_name": "알레르기 비염",
            "dosage": "1일 1회 취침 전 1정 복용",
            "source": "health.kr"
        }

    def get_msd_lifestyle_guide(self, disease_name: str) -> List[str]:
        """
        MSD 매뉴얼에서 질환별 생활 수칙 추출 (Mocking for logic flow)
        """
        print(f"[External] MSD 매뉴얼에서 '{disease_name}' 생활 수칙 검색 중...")
        
        # 실제 구현 시에는 특정 질환 페이지의 '예방' 또는 '생활 방식' 섹션 크롤링
        guides = {
            "알레르기 비염": [
                "꽃가루가 심한 날은 야외 활동을 제한하고 창문을 닫으세요.",
                "실내 습도를 50% 이하로 유지하여 곰팡이 성장을 억제하세요.",
                "침구류는 주 1회 60도 이상의 뜨거운 물로 세탁하세요.",
                "반려동물은 침실에 들이지 않는 것이 좋습니다."
            ],
            "고혈압": [
                "하루 소금 섭취량을 5g 이하로 제한하세요.",
                "주 5회, 매회 30분 이상의 유산소 운동을 권장합니다.",
                "금연과 절주가 필수적입니다."
            ]
        }
        
        return guides.get(disease_name, ["관련 생활 수칙을 찾을 수 없습니다. 전문가와 상담하세요."])

    def synthesize_report(self, drug_data: Dict, msd_guides: List[str]) -> str:
        """
        정보 합성 (Synthesis)
        """
        report = f"### [약물 분석 리포트]\n"
        report += f"- **제품명:** {drug_data['product_name']}\n"
        report += f"- **주요 질환:** {drug_data['disease_name']}\n"
        report += f"- **복용 방법:** {drug_data['dosage']}\n\n"
        report += f"### [MSD 매뉴얼 추천 생활 수칙]\n"
        for i, guide in enumerate(msd_guides, 1):
            report += f"{i}. {guide}\n"
        
        return report
