import os
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None
    print("[Warning] pytesseract가 설치되어 있지 않습니다. OCR 기능이 제한됩니다.")

class VisionEngine:
    """
    30년 경력 약사 AI 프로젝트 - Phase 2 (시각 지능 모듈)
    처방전의 텍스트를 읽는 OCR과 약의 형태/시각 정보를 파악하는 VLM을 통합 처리합니다.
    """
    
    def __init__(self, llm_type="gemini"):
        self.llm_type = llm_type
        # Tesseract 실행 경로 지정이 필요한 경우 (Windows 예시)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self._initialize_vlm()

    def _initialize_vlm(self):
        """VLM (Vision-Language Model) 초기화"""
        print(f"[VisionEngine] {self.llm_type} 기반 VLM 초기화 중...")
        if self.llm_type.lower() == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.vlm = ChatGoogleGenerativeAI(model="gemini-1.5-flash") # Vision 지원 모델
                self.vlm_available = True
            except ImportError:
                print("[Warning] langchain-google-genai 패키지가 없어 VLM을 시뮬레이션 모드로 전환합니다.")
                self.vlm_available = False
        else:
            self.vlm_available = False

    def extract_text_from_prescription(self, image_path: str) -> str:
        """
        [OCR] 처방전이나 약 봉투 이미지에서 약품명 및 복약 지시 텍스트를 추출
        """
        print(f"[OCR] 분석 시작: {image_path}")
        if not os.path.exists(image_path):
            return f"오류: {image_path} 파일을 찾을 수 없습니다."

        if pytesseract:
            try:
                img = Image.open(image_path)
                # 한국어와 영어를 동시에 인식
                extracted_text = pytesseract.image_to_string(img, lang='kor+eng')
                return extracted_text.strip()
            except Exception as e:
                return f"[OCR 실패] {e}"
        else:
            # Tesseract가 없는 로컬 환경을 위한 모의(Mock) 응답
            print("[OCR - Mock Mode] 모의 텍스트를 반환합니다.")
            return "환자명: 김철수\n처방약: 리리카캡슐 75mg\n복약안내: 1일 2회 식후 복용"

    def analyze_pill_image(self, image_path: str) -> dict:
        """
        [VLM] 낱알 사진을 보고 모양, 색상, 식별 문자를 판독하여 JSON 형태로 추출
        """
        print(f"[VLM] 낱알 식별 분석 시작: {image_path}")
        if not os.path.exists(image_path):
            return {"error": f"{image_path} 파일을 찾을 수 없습니다."}

        if self.vlm_available:
            try:
                from langchain_core.messages import HumanMessage
                import base64

                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")

                message = HumanMessage(
                    content=[
                        {"type": "text", "text": "당신은 30년 경력의 약사입니다. 다음 약 낱알 이미지의 형태(정제/캡슐), 색상, 식별 코드를 분석하여 순수 JSON 포맷만 반환하세요. 예: {\"shape\": \"\", \"color\": \"\", \"mark\": \"\"}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                )
                response = self.vlm.invoke([message])
                import json
                raw_json = response.content.replace("```json", "").replace("```", "").strip()
                return json.loads(raw_json)
            except Exception as e:
                return {"error": str(e), "vlm_status": "failed"}
        else:
            # API 키나 모듈이 없는 환경을 위한 모의(Mock) 응답
            print("[VLM - Mock Mode] 모의 판독 결과를 반환합니다.")
            return {
                "shape": "캡슐",
                "color": "적갈색/흰색",
                "mark": "PGB 75",
                "detected_drug": "리리카캡슐" # 예측 약물
            }

    def process_hybrid_vision(self, prescription_img_path: str, pill_img_path: str) -> dict:
        """
        OCR 텍스트 추출과 VLM 알약 판별 기능을 병합하여,
        약사가 종합적으로 판단할 수 있는 비전 컨텍스트 객체를 생성합니다.
        """
        print("[VisionEngine] 복합 비전 파이프라인 (OCR + VLM) 구동 중...")
        ocr_text = self.extract_text_from_prescription(prescription_img_path)
        vlm_data = self.analyze_pill_image(pill_img_path)
        
        return {
            "ocr_text": ocr_text,
            "vlm_analysis": vlm_data,
            "status": "success"
        }

if __name__ == "__main__":
    engine = VisionEngine()
    # 개발 환경 테스트용 더미 파일 생성 로직 (실제로는 사용자의 진짜 이미지를 사용)
    dummy_prescription = "dummy_prescription.jpg"
    dummy_pill = "dummy_pill.jpg"
    
    # 껍데기 이미지 만들어서 에러 방지
    Image.new('RGB', (10, 10)).save(dummy_prescription)
    Image.new('RGB', (10, 10)).save(dummy_pill)
    
    result = engine.process_hybrid_vision(dummy_prescription, dummy_pill)
    print("=== 비전 엔진 복합 추출 결과 ===")
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 테스트 파일 정리
    os.remove(dummy_prescription)
    os.remove(dummy_pill)
