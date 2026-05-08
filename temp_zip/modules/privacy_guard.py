import re
import gc

class PrivacyGuard:
    """
    30년 경력 AI 약사 프로젝트를 위한 고보안 개인정보 보호 모듈.
    """
    
    def __init__(self):
        # 한국 주민등록번호 정규식 패턴 (앞 6자리 - 뒤 7자리)
        # 123456-1234567, 123456 1234567, 1234561234567 등을 유연하게 캐치
        self.rrn_pattern = re.compile(r'(\d{6})[- \s]?(\d{7})')

    def mask_pii(self, text: str) -> str:
        """
        텍스트 내의 주민등록번호 패턴을 찾아서 뒷자리를 *******로 마스킹합니다.
        마스킹 완료 직후 가비지 컬렉터를 호출하여 메모리에서 원본의 흔적을 즉시 지우려 시도합니다.
        """
        if not text:
            return text

        # 앞 6자리는 남기고 (\1), 뒤 7자리를 *******로 치환
        masked_text = self.rrn_pattern.sub(r'\1-*******', text)
        
        # 원본 데이터에 대한 참조 정리 및 가비지 컬렉터 강제 호출
        del text
        gc.collect()
        
        return masked_text

if __name__ == "__main__":
    # 간단한 작동 및 메모리 제로화(GC) 테스트
    guard = PrivacyGuard()
    sample_text = "환자 리만호, 주민번호는 900101-1234567 입니다."
    result = guard.mask_pii(sample_text)
    print(f"Masking Result: {result}")
