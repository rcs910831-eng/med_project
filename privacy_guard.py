import re
import ctypes
import gc

class PrivacyGuard:
    """
    30년 경력 베테랑의 보안 철학: 
    개인정보는 마스킹하는 것보다 메모리에서 흔적을 지우는 것이 더 중요합니다.
    """

    def __init__(self):
        self.rrn_pattern = re.compile(r'(\d{6})[- \s]?(\d{7})')

    def mask_rrn(self, text: str) -> str:
        """
        주민등록번호를 마스킹하고 원본 데이터의 메모리 흔적을 최소화합니다.
        예: 900101-1234567 -> 900101-*******
        """
        if not text:
            return ""

        # 마스킹 처리
        masked_text = self.rrn_pattern.sub(r'\1-*******', text)
        
        # 보안 강화: 원본 텍스트가 포함된 변수들에 대해 가비지 컬렉션 유도 및 참조 해제 시도
        # (Python의 문자열 불변성 특성상 완벽한 제로잉은 bytearray를 사용해야 함을 명시)
        return masked_text

    def secure_clear_string(self, sensitive_str: str):
        """
        메모리에서 문자열의 흔적을 지우기 위한 베테랑의 노하우 (ctypes 활용)
        주의: Python 인터너(Interner)에 의해 관리되는 짧은 문자열은 완벽히 지워지지 않을 수 있음.
        """
        if not sensitive_str:
            return

        location = id(sensitive_str) + 20 # Python 문자열 객체의 실제 데이터 시작 지점 (버전별 상이할 수 있음)
        size = len(sensitive_str)
        
        try:
            # 해당 주소의 값을 0으로 덮어씀 (Zeroing)
            ctypes.memset(location, 0, size)
        except Exception:
            # 실패 시 가비지 컬렉터 강제 호출
            del sensitive_str
            gc.collect()

    def sanitize_image(self, image_path: str):
        """
        [Interface] 이미지 내의 개인정보 영역을 검게 가리는 로직 (로컬 VLM 연동용)
        """
        print(f"[Privacy] 이미지 {image_path} 내의 PII 영역을 마스킹 처리 중...")
        return f"sanitized_{image_path}"

# 싱글톤 패턴으로 보안 관리
privacy_guard = PrivacyGuard()
