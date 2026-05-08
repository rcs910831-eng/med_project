#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHARMA-MOBILE Voice Handler
Google Cloud Speech-to-Text & Text-to-Speech Integration
"""

import os
import io
import logging
from typing import Optional, Tuple
from google.cloud import speech_v1 as speech
from google.cloud import texttospeech_v1 as texttospeech

# 로깅 설정
logger = logging.getLogger(__name__)


class VoiceHandler:
    """Google Cloud 음성 처리 (STT/TTS)"""

    def __init__(self):
        """Google Cloud 클라이언트 초기화"""
        # google-cloud-key.json 파일 경로 설정
        credentials_path = os.path.join(os.path.dirname(__file__), "google-cloud-key.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        try:
            logger.info(f"🔍 Google Cloud 인증 파일 확인: {credentials_path}")
            logger.info(f"📂 파일 존재 여부: {os.path.exists(credentials_path)}")

            self.speech_client = speech.SpeechClient()
            self.tts_client = texttospeech_v1.TextToSpeechClient()
            logger.info("✅ Google Cloud 클라이언트 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Google Cloud 클라이언트 초기화 실패: {str(e)}")
            logger.warning(f"📝 상세 정보: {type(e).__name__}")
            self.speech_client = None
            self.tts_client = None

    def speech_to_text(self, audio_content: bytes, language_code: str = "ko-KR") -> Tuple[str, float]:
        """
        음성을 텍스트로 변환 (Speech-to-Text)

        Args:
            audio_content: 오디오 바이너리 데이터 (WAV/MP3)
            language_code: 언어 코드 ("ko-KR", "en-US" 등)

        Returns:
            (변환된 텍스트, 신뢰도)
        """
        if not self.speech_client:
            logger.error("❌ Speech Client가 초기화되지 않음")
            raise RuntimeError("Google Cloud Speech API를 사용할 수 없습니다")

        try:
            # 오디오 요청 생성
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_long"  # 더 정확한 모델
            )

            # Speech-to-Text 요청
            response = self.speech_client.recognize(config=config, audio=audio)

            # 결과 처리
            if not response.results:
                logger.warning("⚠️ 음성 인식 결과 없음")
                return "", 0.0

            # 신뢰도가 가장 높은 결과 선택
            best_result = response.results[0]

            if not best_result.alternatives:
                return "", 0.0

            best_alternative = best_result.alternatives[0]
            transcript = best_alternative.transcript
            confidence = best_alternative.confidence

            logger.info(f"✅ 음성 인식 완료: {transcript} (신뢰도: {confidence:.2%})")
            return transcript, confidence

        except Exception as e:
            logger.error(f"❌ Speech-to-Text 오류: {str(e)}")
            raise

    def text_to_speech(self, text: str, language_code: str = "ko-KR",
                      speaking_rate: float = 1.0) -> bytes:
        """
        텍스트를 음성으로 변환 (Text-to-Speech)

        Args:
            text: 변환할 텍스트
            language_code: 언어 코드 ("ko-KR", "en-US" 등)
            speaking_rate: 음성 속도 (0.25 ~ 4.0, 기본 1.0)

        Returns:
            MP3 오디오 바이너리 데이터
        """
        if not self.tts_client:
            logger.error("❌ TTS Client가 초기화되지 않음")
            raise RuntimeError("Google Cloud Text-to-Speech API를 사용할 수 없습니다")

        try:
            # TTS 요청 생성
            synthesis_input = texttospeech_v1.SynthesisInput(text=text)

            # 음성 설정 (한국어 여성 목소리)
            voice = texttospeech_v1.VoiceSelectionParams(
                language_code=language_code,
                name="ko-KR-Neural2-A",  # 자연스러운 신경망 음성
                ssml_gender=texttospeech_v1.SsmlVoiceGender.FEMALE
            )

            # 오디오 설정
            audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )

            # Text-to-Speech 요청
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            logger.info(f"✅ 음성 생성 완료: {len(response.audio_content)} bytes")
            return response.audio_content

        except Exception as e:
            logger.error(f"❌ Text-to-Speech 오류: {str(e)}")
            raise

    @staticmethod
    def create_health_explanation(medication_info: dict) -> str:
        """
        약물 정보를 음성 설명으로 변환

        Args:
            medication_info: 약물 정보 딕셔너리
                {
                    "patient_name": "김철수",
                    "medications": [
                        {"name": "노바스크정", "dose": "1회 1정", "frequency": "1일 1회"},
                        ...
                    ],
                    "warnings": ["자몽주스 금지", "저혈압 주의"]
                }

        Returns:
            음성 설명 스크립트 (한글)
        """
        script = f"{medication_info.get('patient_name', '사용자')}님의 복약 정보를 알려드립니다.\n\n"

        # 약물 정보
        medications = medication_info.get("medications", [])
        if medications:
            script += "【약물 정보】\n"
            for i, med in enumerate(medications, 1):
                script += f"{i}. {med.get('name', '약물명')} - "
                script += f"1회 {med.get('dose', '용량')}, "
                script += f"{med.get('frequency', '1일 1회')} 복용하세요.\n"
            script += "\n"

        # 주의사항
        warnings = medication_info.get("warnings", [])
        if warnings:
            script += "【주의사항】\n"
            for warning in warnings:
                script += f"• {warning}\n"
            script += "\n"

        script += "이상으로 약물 정보 설명을 마쳤습니다."
        return script


# 싱글톤 인스턴스
_voice_handler_instance = None


def get_voice_handler() -> VoiceHandler:
    """VoiceHandler 싱글톤 인스턴스 반환"""
    global _voice_handler_instance
    if _voice_handler_instance is None:
        _voice_handler_instance = VoiceHandler()
    return _voice_handler_instance
