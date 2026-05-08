"""
TTS Handler - Text-to-Speech Integration
Generates voice explanations for medication information
"""

import os
import logging
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VoiceConfig:
    """Voice configuration for TTS"""
    language_code: str = "ko-KR"
    voice_name: str = "ko-KR-Standard-A"
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain: float = 0.0


class TTSHandler:
    """Handles text-to-speech synthesis"""

    SUPPORTED_LANGUAGES = {
        "ko-KR": {
            "name": "Korean (Korea)",
            "voices": [
                "ko-KR-Standard-A",
                "ko-KR-Standard-B",
                "ko-KR-Standard-C",
                "ko-KR-Standard-D"
            ]
        },
        "en-US": {
            "name": "English (US)",
            "voices": [
                "en-US-Standard-A",
                "en-US-Standard-C",
                "en-US-Standard-E",
                "en-US-Standard-G"
            ]
        }
    }

    def __init__(self, output_dir: str = "./pharma_voice_comp"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._init_google_tts()

        logger.info(f"TTSHandler initialized with output dir: {output_dir}")

    def _init_google_tts(self):
        """Initialize Google Cloud Text-to-Speech"""
        try:
            from google.cloud import texttospeech
            self.texttospeech = texttospeech
            self.tts_available = True
            logger.info("Google Cloud TTS initialized")
        except ImportError:
            logger.warning("google-cloud-texttospeech not installed")
            self.tts_available = False

    def generate_medication_explanation(
        self,
        medication_info: dict,
        patient_name: str = "환자님",
        language_code: str = "ko-KR",
        output_file: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate voice explanation for medication

        Args:
            medication_info: Dictionary with medication details
            patient_name: Patient name for personalization
            language_code: Language code
            output_file: Optional output file path

        Returns:
            Audio bytes or None
        """
        try:
            # Generate script
            script = self._generate_medication_script(
                medication_info,
                patient_name,
                language_code
            )

            # Synthesize speech
            audio_content = self.synthesize_text(
                script,
                language_code=language_code,
                output_file=output_file
            )

            return audio_content

        except Exception as e:
            logger.error(f"Error generating medication explanation: {e}")
            return None

    def generate_prescription_summary(
        self,
        patient_info: dict,
        medications: List[dict],
        language_code: str = "ko-KR",
        output_file: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate comprehensive voice summary of prescription

        Args:
            patient_info: Patient information
            medications: List of medications
            language_code: Language code
            output_file: Optional output file path

        Returns:
            Audio bytes or None
        """
        try:
            script = self._generate_prescription_script(
                patient_info,
                medications,
                language_code
            )

            audio_content = self.synthesize_text(
                script,
                language_code=language_code,
                output_file=output_file
            )

            return audio_content

        except Exception as e:
            logger.error(f"Error generating prescription summary: {e}")
            return None

    def synthesize_text(
        self,
        text: str,
        language_code: str = "ko-KR",
        voice_name: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Synthesize text to speech using Google Cloud TTS

        Args:
            text: Text to synthesize
            language_code: Language code
            voice_name: Optional specific voice
            output_file: Optional output file path

        Returns:
            Audio bytes or None
        """
        if not self.tts_available:
            logger.error("Google Cloud TTS not available")
            return None

        try:
            # Use default voice if not specified
            if not voice_name:
                voice_name = self.SUPPORTED_LANGUAGES.get(
                    language_code, {}
                ).get("voices", ["ko-KR-Standard-A"])[0]

            client = self.texttospeech.TextToSpeechClient()

            synthesis_input = self.texttospeech.SynthesisInput(text=text)
            voice = self.texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            audio_config = self.texttospeech.AudioConfig(
                audio_encoding=self.texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            audio_content = response.audio_content

            # Save to file if specified
            if output_file:
                os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
                with open(output_file, "wb") as f:
                    f.write(audio_content)
                logger.info(f"Audio saved to {output_file}")

            return audio_content

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None

    def _generate_medication_script(
        self,
        med_info: dict,
        patient_name: str,
        language_code: str
    ) -> str:
        """Generate medication explanation script"""
        if language_code == "ko-KR":
            return self._generate_korean_medication_script(med_info, patient_name)
        else:
            return self._generate_english_medication_script(med_info, patient_name)

    def _generate_korean_medication_script(self, med_info: dict, patient_name: str) -> str:
        """Generate Korean medication script"""
        script = f"""
        {patient_name}님의 처방약 정보를 알려드립니다.

        약물명: {med_info.get('name', '약물')} {med_info.get('strength', '')}입니다.

        1일 권장량: {med_info.get('daily_dose', '의사의 지시에 따름')}입니다.

        투여 횟수: {med_info.get('frequency', '매일')}복용해주시기 바랍니다.

        투약 기간: {med_info.get('duration', '의사의 지시에 따름')}동안 복용합니다.
        """

        if med_info.get('warnings'):
            script += f"\n        주의사항: {med_info.get('warnings', '')}"

        script += """

        더 자세한 정보는 전문가와 상담해주시기 바랍니다.
        """

        return script

    def _generate_english_medication_script(self, med_info: dict, patient_name: str) -> str:
        """Generate English medication script"""
        script = f"""
        Here is the medication information for {patient_name}.

        Medication: {med_info.get('name', 'medication')} {med_info.get('strength', '')}.

        Daily recommended dose: {med_info.get('daily_dose', 'as directed by physician')}.

        Frequency: {med_info.get('frequency', 'daily')}.

        Duration: {med_info.get('duration', 'as prescribed')}.
        """

        if med_info.get('warnings'):
            script += f"\n\n        Warnings: {med_info.get('warnings', '')}"

        script += "\n\n        Please consult with a healthcare professional for more information."

        return script

    def _generate_prescription_script(
        self,
        patient_info: dict,
        medications: List[dict],
        language_code: str
    ) -> str:
        """Generate comprehensive prescription script"""
        if language_code == "ko-KR":
            return self._generate_korean_prescription_script(patient_info, medications)
        else:
            return self._generate_english_prescription_script(patient_info, medications)

    def _generate_korean_prescription_script(
        self,
        patient_info: dict,
        medications: List[dict]
    ) -> str:
        """Generate Korean prescription script"""
        script = f"""
        {patient_info.get('name', '환자님')}님의 처방약 정보를 종합적으로 설명드리겠습니다.

        환자 정보:
        나이는 {patient_info.get('age', '미상')}세이고, 성별은 {patient_info.get('sex', '미상')}입니다.
        """

        if patient_info.get('primary_diagnosis'):
            script += f"\n        주된 진료 질환: {patient_info.get('primary_diagnosis')}"

        if patient_info.get('secondary_diagnosis'):
            script += f"\n        부가적 진료 질환: {patient_info.get('secondary_diagnosis')}"

        script += "\n\n        처방 약물 정보:\n"

        for idx, med in enumerate(medications, 1):
            script += f"""
            {idx}번 약물: {med.get('name', '')} {med.get('strength', '')}입니다.
            1일 권장량은 {med.get('daily_dose', '의사 지시에 따름')}이고,
            {med.get('frequency', '매일')} 복용하시면 됩니다.
            """

        script += """

        정기적으로 병원에 방문하여 상담받으시기 바랍니다.
        더 자세한 정보는 의료전문가와 상담해주세요.
        """

        return script

    def _generate_english_prescription_script(
        self,
        patient_info: dict,
        medications: List[dict]
    ) -> str:
        """Generate English prescription script"""
        script = f"""
        Comprehensive medication information for {patient_info.get('name', 'the patient')}.

        Patient information:
        Age: {patient_info.get('age', 'unknown')} years old.
        Gender: {patient_info.get('sex', 'unknown')}.
        """

        if patient_info.get('primary_diagnosis'):
            script += f"\n        Primary diagnosis: {patient_info.get('primary_diagnosis')}."

        if patient_info.get('secondary_diagnosis'):
            script += f"\n        Secondary diagnosis: {patient_info.get('secondary_diagnosis')}."

        script += "\n\n        Prescribed medications:\n"

        for idx, med in enumerate(medications, 1):
            script += f"""
            Medication {idx}: {med.get('name', '')} {med.get('strength', '')}.
            Daily recommended dose: {med.get('daily_dose', 'as directed')}.
            Frequency: {med.get('frequency', 'daily')}.
            """

        script += """

        Please visit your healthcare provider regularly for follow-up consultation.
        Contact a medical professional for more detailed information.
        """

        return script

    def batch_synthesize(
        self,
        texts: List[str],
        language_code: str = "ko-KR",
        output_dir: Optional[str] = None
    ) -> List[Optional[bytes]]:
        """
        Synthesize multiple texts

        Args:
            texts: List of texts to synthesize
            language_code: Language code
            output_dir: Optional directory to save files

        Returns:
            List of audio bytes
        """
        results = []

        for idx, text in enumerate(texts):
            output_file = None
            if output_dir:
                output_file = os.path.join(output_dir, f"audio_{idx:03d}.mp3")

            audio = self.synthesize_text(text, language_code, output_file=output_file)
            results.append(audio)

        logger.info(f"Batch synthesized {len(results)} items")
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    handler = TTSHandler()

    # Example: Generate medication explanation
    med_info = {
        "name": "노바스크정",
        "strength": "5mg",
        "daily_dose": "1회 1정 (5mg)",
        "frequency": "1일 1회 (아침)",
        "duration": "30일",
        "warnings": "자몽 주스와 함께 섭취 금지"
    }

    audio = handler.generate_medication_explanation(
        med_info,
        patient_name="김철수님",
        output_file="./pharma_voice_comp/example_medication.mp3"
    )

    if audio:
        print(f"Audio generated successfully: {len(audio)} bytes")
    else:
        print("Failed to generate audio")
