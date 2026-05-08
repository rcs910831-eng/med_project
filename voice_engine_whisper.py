import os
import sys
import time
import threading
import queue
import numpy as np
import logging

# 중요: Whisper 및 오디오 관련 라이브러리 필요
# pip install openai-whisper sounddevice numpy scipy
try:
    import whisper
    import sounddevice as sd
    from scipy.io.wavfile import write
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [VOICE] - %(message)s')

class WhisperVoiceCommander:
    """OpenAI Whisper 기반 전략적 음성 명령 엔진"""
    
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
        self.is_listening = False
        self.command_queue = queue.Queue()
        
        # 명령어 매핑
        self.INTENT_MAP = {
            "분석": "START_ANALYSIS",
            "개시": "START_ANALYSIS",
            "검사": "START_ANALYSIS",
            "리포트": "GENERATE_REPORT",
            "보고서": "GENERATE_REPORT",
            "발행": "GENERATE_REPORT",
            "백업": "RUN_BACKUP",
            "저장": "RUN_BACKUP"
        }

    def load_model(self):
        """Whisper 모델 로드 (비차단 스레드 권장)"""
        if not WHISPER_AVAILABLE:
            logging.error("❌ Whisper 라이브러리가 설치되지 않았습니다.")
            return False
        
        logging.info(f"🛰️ Whisper {self.model_size} 모델 로딩 중...")
        start = time.time()
        self.model = whisper.load_model(self.model_size)
        logging.info(f"✅ 모델 로드 완료 (소요시간: {time.time()-start:.2f}초)")
        return True

    def transcribe_file(self, audio_file):
        """오디오 파일(Streamlit 업로드 등)을 Whisper로 변환"""
        if self.model is None:
            if not self.load_model(): return {"text": "ERROR: NO_MODEL", "intent": "NONE"}
        
        try:
            # 1. 파일 저장 (Streamlit 객체 대응)
            temp_path = "temp_st_voice.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_file.getvalue())
            
            # 2. Whisper 변환
            logging.info("🧠 Streamlit 음성 데이터 분석 중...")
            result = self.model.transcribe(temp_path, language='ko')
            text = result["text"].strip()
            
            logging.info(f"🗣️ 인식된 문구: {text}")
            return {"text": text, "intent": self.parse_intent(text)}
        except Exception as e:
            logging.error(f"❌ 음성 파일 처리 중 오류: {e}")
            return {"text": "", "intent": "NONE"}

    def record_and_transcribe(self, duration=3, fs=16000):
        """음성 녹음 및 Whisper 변환"""
        if self.model is None:
            if not self.load_model(): return "ERROR: NO_MODEL"

        logging.info(f"🎤 음성 대기 중... ({duration}초)")
        
        try:
            # 1. 오디오 녹음
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait() # 녹음 완료 대기
            
            # 2. 파일 저장 (임시)
            temp_wav = "temp_voice_cmd.wav"
            write(temp_wav, fs, (recording * 32767).astype(np.int16))
            
            # 3. Whisper 변환
            logging.info("🧠 음성 분석 중 (Whisper Processing)...")
            result = self.model.transcribe(temp_wav, language='ko')
            text = result["text"].strip()
            
            logging.info(f"🗣️ 인식된 문구: {text}")
            
            # 4. 의도 파악
            intent = self.parse_intent(text)
            return {"text": text, "intent": intent}
            
        except Exception as e:
            logging.error(f"❌ 음성 처리 중 오류: {e}")
            return {"text": "", "intent": "NONE"}

    def parse_intent(self, text):
        """텍스트에서 명령 의도 추출"""
        for keyword, intent in self.INTENT_MAP.items():
            if keyword in text:
                return intent
        return "NONE"

    def run_command_logic(self, intent):
        """의도에 따른 프로젝트 로직 실행"""
        if intent == "START_ANALYSIS":
            print("🚀 [ACTION] 분석을 개시합니다.")
            # 여기에 실제 분석 함수 연결
        elif intent == "GENERATE_REPORT":
            print("📜 [ACTION] 리포트 생성을 시작합니다.")
        elif intent == "RUN_BACKUP":
            print("💾 [ACTION] 시스템 전체 백업을 실행합니다.")
            import pharma_backup_system
            pharma_backup_system.run_strategic_backup()

if __name__ == "__main__":
    # 독립 실행 테스트용
    commander = WhisperVoiceCommander()
    if commander.load_model():
        res = commander.record_and_transcribe(duration=3)
        print(f"결과: {res}")
        commander.run_command_logic(res['intent'])
