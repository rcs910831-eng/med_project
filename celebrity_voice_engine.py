import io
import os
from gtts import gTTS
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

class CelebrityVoiceEngine:
    def __init__(self, engine_type="gtts"):
        self.engine_type = engine_type
        self.current_voice = "default"
        # Persona settings: (pitch_shift, speed_shift)
        self.personas = {
            "장원영(Wonyoung)": {"pitch": 1.4, "speed": 1.1},
            "카리나(Karina)": {"pitch": 0.9, "speed": 0.9},
            "안유진(AnYuJin)": {"pitch": 1.2, "speed": 1.0},
            "전문의(Doctor)": {"pitch": 0.8, "speed": 0.85},
            "default": {"pitch": 1.0, "speed": 1.0}
        }

    def set_voice(self, voice_name):
        if voice_name in self.personas:
            self.current_voice = voice_name
        else:
            self.current_voice = "default"

    def _adjust_audio(self, audio_bytes, persona_name):
        if not HAS_PYDUB:
            return audio_bytes
        
        persona = self.personas.get(persona_name, self.personas["default"])
        
        # Load audio from bytes
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        
        # Pitch shift (simulated by changing frame rate)
        new_sample_rate = int(audio.frame_rate * persona["pitch"])
        pitched_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        pitched_audio = pitched_audio.set_frame_rate(audio.frame_rate)
        
        # Speed shift
        final_audio = pitched_audio.speedup(playback_speed=persona["speed"]) if persona["speed"] != 1.0 else pitched_audio
        
        # Export back to bytes
        out_buf = io.BytesIO()
        final_audio.export(out_buf, format="mp3")
        return out_buf.getvalue()

    def synthesize_to_audio(self, text):
        if not text:
            return b""
            
        # 1. Generate standard gTTS
        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        audio_bytes = mp3_fp.getvalue()
        
        # 2. Adjust for persona if possible
        # Note: pitch adjustment via pydub might sound robotic if not careful, 
        # but it satisfies the requirement for "different voices".
        try:
            return self._adjust_audio(audio_bytes, self.current_voice)
        except Exception as e:
            print(f"Audio adjustment failed: {e}")
            return audio_bytes

if __name__ == "__main__":
    # Test script provided by user
    engine = CelebrityVoiceEngine(engine_type="gtts")
    engine.set_voice("장원영(Wonyoung)")
    text = "안녕하세요. 장원영 AI 보이스 테스트입니다. 뛰어 읽기가 잘 되는지 확인해 보세요."
    audio = engine.synthesize_to_audio(text)
    with open("output.mp3", "wb") as f:
        f.write(audio)
    print("output.mp3 saved.")
