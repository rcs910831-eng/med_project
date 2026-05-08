#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
음성 감정 인식 엔진
사령관(의료진) 음성 + 환자 컨디션(톤·속도·에너지) 이중 분석
Whisper STT 이후 단계에서 호출되는 파이프라인
"""

import numpy as np
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger("EmotionVoiceAnalyzer")

# ── 선택적 의존성 ─────────────────────────────────────────────────────────
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from scipy.io.wavfile import read as wav_read
    from scipy.signal import butter, filtfilt
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ════════════════════════════════════════════════════════════════════════════
# 감정 상태 열거형
# ════════════════════════════════════════════════════════════════════════════

class PatientEmotion(Enum):
    CALM        = "안정"
    ANXIOUS     = "불안"
    DEPRESSED   = "우울"
    FATIGUED    = "피로"
    AGITATED    = "흥분"
    IN_PAIN     = "통증호소"
    CONFUSED    = "혼란"
    COOPERATIVE = "협조적"
    UNKNOWN     = "분석불가"


class CommanderTone(Enum):
    INSTRUCTIVE = "지시적"
    EMPATHETIC  = "공감적"
    URGENT      = "긴급"
    CALM        = "침착"
    ENCOURAGING = "격려"
    UNKNOWN     = "분석불가"


# ════════════════════════════════════════════════════════════════════════════
# 데이터 클래스
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class AudioFeatures:
    """오디오 신호에서 추출한 음향학적 특징"""
    duration_sec: float = 0.0
    mean_pitch_hz: float = 0.0
    pitch_variability: float = 0.0   # 피치 표준편차
    mean_energy: float = 0.0
    energy_variability: float = 0.0
    speaking_rate_syl_per_sec: float = 0.0  # 음절/초 (속도)
    pause_ratio: float = 0.0         # 무음 구간 비율
    spectral_centroid_mean: float = 0.0
    mfcc_features: list = field(default_factory=list)  # MFCC 평균 13차
    zcr_mean: float = 0.0            # 영점교차율 (거칠기 지표)
    rms_mean: float = 0.0            # 실효치 (음량)


@dataclass
class EmotionAnalysisResult:
    """감정 분석 최종 결과"""
    speaker_role: str = "unknown"    # "commander" | "patient"
    emotion: str = PatientEmotion.UNKNOWN.value
    confidence: float = 0.0         # 0.0 ~ 1.0
    features: Optional[AudioFeatures] = None

    # 세부 지표
    stress_index: float = 0.0       # 0~100 스트레스 지수
    fatigue_index: float = 0.0      # 0~100 피로도
    pain_index: float = 0.0         # 0~100 통증 가능성
    cooperation_score: float = 0.0  # 0~100 협조도

    # 임상 해석 및 권고
    clinical_note: str = ""
    recommended_action: str = ""
    alert_level: str = "normal"     # "normal" | "watch" | "alert" | "critical"
    analysis_method: str = "rule_based"
    timestamp: str = ""


# ════════════════════════════════════════════════════════════════════════════
# 저수준 오디오 특징 추출
# ════════════════════════════════════════════════════════════════════════════

def _extract_features_librosa(audio_array: np.ndarray, sr: int) -> AudioFeatures:
    f = AudioFeatures()
    f.duration_sec = len(audio_array) / sr

    # 피치 (F0)
    f0, voiced_flag, _ = librosa.pyin(
        audio_array.astype(np.float32),
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
    )
    voiced = f0[voiced_flag]
    if len(voiced) > 0:
        f.mean_pitch_hz   = float(np.nanmean(voiced))
        f.pitch_variability = float(np.nanstd(voiced))

    # 에너지 (RMS)
    rms = librosa.feature.rms(y=audio_array)[0]
    f.rms_mean          = float(np.mean(rms))
    f.mean_energy       = float(np.mean(rms ** 2))
    f.energy_variability = float(np.std(rms))

    # 스펙트럼 중심
    sc = librosa.feature.spectral_centroid(y=audio_array, sr=sr)[0]
    f.spectral_centroid_mean = float(np.mean(sc))

    # MFCC
    mfcc = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=13)
    f.mfcc_features = [float(np.mean(c)) for c in mfcc]

    # 영점교차율
    zcr = librosa.feature.zero_crossing_rate(audio_array)[0]
    f.zcr_mean = float(np.mean(zcr))

    # 묵음 비율 (음량 < 5% 구간)
    threshold = 0.05 * np.max(np.abs(audio_array))
    silence_frames = np.sum(np.abs(audio_array) < threshold)
    f.pause_ratio = float(silence_frames / len(audio_array))

    # 발화 속도 추정 (에너지 돌출 수 / duration)
    onset_frames = librosa.onset.onset_detect(y=audio_array, sr=sr)
    f.speaking_rate_syl_per_sec = len(onset_frames) / max(f.duration_sec, 0.1)

    return f


def _extract_features_numpy(audio_array: np.ndarray, sr: int) -> AudioFeatures:
    """librosa 없을 때 순수 NumPy 폴백"""
    f = AudioFeatures()
    f.duration_sec = len(audio_array) / sr

    # RMS 에너지 (프레임 단위)
    frame_len = int(0.025 * sr)
    hop = int(0.010 * sr)
    rms_list = []
    for start in range(0, len(audio_array) - frame_len, hop):
        frame = audio_array[start:start + frame_len].astype(np.float64)
        rms_list.append(np.sqrt(np.mean(frame ** 2)))
    if rms_list:
        rms = np.array(rms_list)
        f.rms_mean = float(np.mean(rms))
        f.mean_energy = float(np.mean(rms ** 2))
        f.energy_variability = float(np.std(rms))

    # 영점교차율
    signs = np.sign(audio_array.astype(np.float64))
    zcr = np.mean(np.abs(np.diff(signs)) / 2)
    f.zcr_mean = float(zcr)

    # 묵음 비율
    threshold = 0.05 * (np.max(np.abs(audio_array)) + 1e-10)
    f.pause_ratio = float(np.mean(np.abs(audio_array) < threshold))

    # 피치 추정 (자기상관 기반 단순 추정)
    try:
        segment = audio_array[:min(len(audio_array), sr)].astype(np.float64)
        corr = np.correlate(segment, segment, mode='full')
        corr = corr[len(corr) // 2:]
        min_lag = int(sr / 500)  # 500Hz 최대
        max_lag = int(sr / 50)   # 50Hz 최소
        if max_lag < len(corr):
            peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
            f.mean_pitch_hz = float(sr / peak_lag) if peak_lag > 0 else 0.0
    except Exception:
        pass

    return f


def extract_audio_features(audio_array: np.ndarray, sr: int = 16000) -> AudioFeatures:
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)
    audio_array = audio_array.astype(np.float32)
    peak = np.max(np.abs(audio_array))
    if peak > 0:
        audio_array = audio_array / peak

    if LIBROSA_AVAILABLE:
        try:
            return _extract_features_librosa(audio_array, sr)
        except Exception as e:
            logger.warning(f"librosa 추출 실패, 폴백: {e}")
    return _extract_features_numpy(audio_array, sr)


# ════════════════════════════════════════════════════════════════════════════
# 감정 분류 규칙 엔진
# ════════════════════════════════════════════════════════════════════════════

class EmotionClassifier:
    """
    음향 특징 → 감정 상태 매핑 규칙 기반 분류기
    임상 관찰에 기반한 임계값 설정
    """

    # 정상 범위 기준 (한국어 성인 기준)
    NORMAL_PITCH_FEMALE = (180, 280)   # Hz
    NORMAL_PITCH_MALE   = (80, 160)    # Hz
    HIGH_ENERGY_THRESH  = 0.08
    LOW_ENERGY_THRESH   = 0.02
    FAST_SPEECH_THRESH  = 5.0          # 음절/초
    SLOW_SPEECH_THRESH  = 2.0
    HIGH_PAUSE_THRESH   = 0.55         # 55% 이상 묵음
    HIGH_ZCR_THRESH     = 0.15         # 음성 거칠기

    def classify_patient(self, f: AudioFeatures, gender_hint: str = "unknown") -> Tuple[str, float, dict]:
        """환자 감정 분류 → (emotion_value, confidence, scores_dict)"""
        scores = {
            PatientEmotion.CALM.value:        0.0,
            PatientEmotion.ANXIOUS.value:     0.0,
            PatientEmotion.DEPRESSED.value:   0.0,
            PatientEmotion.FATIGUED.value:    0.0,
            PatientEmotion.AGITATED.value:    0.0,
            PatientEmotion.IN_PAIN.value:     0.0,
            PatientEmotion.CONFUSED.value:    0.0,
            PatientEmotion.COOPERATIVE.value: 0.0,
        }

        # 에너지 패턴
        if f.mean_energy < self.LOW_ENERGY_THRESH:
            scores[PatientEmotion.FATIGUED.value]  += 2.5
            scores[PatientEmotion.DEPRESSED.value] += 1.5
        elif f.mean_energy > self.HIGH_ENERGY_THRESH:
            scores[PatientEmotion.AGITATED.value]  += 2.0
            scores[PatientEmotion.ANXIOUS.value]   += 1.0

        # 발화 속도
        if f.speaking_rate_syl_per_sec > self.FAST_SPEECH_THRESH:
            scores[PatientEmotion.ANXIOUS.value]   += 2.0
            scores[PatientEmotion.AGITATED.value]  += 1.5
        elif f.speaking_rate_syl_per_sec < self.SLOW_SPEECH_THRESH and f.speaking_rate_syl_per_sec > 0.1:
            scores[PatientEmotion.FATIGUED.value]  += 2.0
            scores[PatientEmotion.DEPRESSED.value] += 1.0
            scores[PatientEmotion.IN_PAIN.value]   += 1.0

        # 묵음 비율 (말이 느리거나 중단 많음)
        if f.pause_ratio > self.HIGH_PAUSE_THRESH:
            scores[PatientEmotion.FATIGUED.value]  += 1.5
            scores[PatientEmotion.CONFUSED.value]  += 1.0
            scores[PatientEmotion.IN_PAIN.value]   += 1.0

        # 피치 변동성 (높으면 불안·통증, 낮으면 우울·피로)
        if f.pitch_variability > 60:
            scores[PatientEmotion.ANXIOUS.value]   += 1.5
            scores[PatientEmotion.IN_PAIN.value]   += 2.0
        elif f.pitch_variability < 20 and f.mean_pitch_hz > 0:
            scores[PatientEmotion.DEPRESSED.value] += 1.5
            scores[PatientEmotion.FATIGUED.value]  += 1.0

        # 음성 거칠기 (ZCR 높으면 통증·흥분)
        if f.zcr_mean > self.HIGH_ZCR_THRESH:
            scores[PatientEmotion.IN_PAIN.value]   += 2.0
            scores[PatientEmotion.AGITATED.value]  += 1.0

        # 에너지 변동성 (불규칙 → 불안·통증)
        if f.energy_variability > 0.04:
            scores[PatientEmotion.ANXIOUS.value]   += 1.0
            scores[PatientEmotion.IN_PAIN.value]   += 0.5

        # 협조·안정 기준 (중간 속도 + 중간 에너지 + 낮은 묵음)
        if (self.SLOW_SPEECH_THRESH < f.speaking_rate_syl_per_sec < self.FAST_SPEECH_THRESH
                and self.LOW_ENERGY_THRESH < f.mean_energy < self.HIGH_ENERGY_THRESH
                and f.pause_ratio < 0.4):
            scores[PatientEmotion.CALM.value]        += 2.0
            scores[PatientEmotion.COOPERATIVE.value] += 1.5

        top_emotion = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[top_emotion] / total if total > 0 else 0.0
        return top_emotion, min(confidence, 0.99), scores

    def classify_commander(self, f: AudioFeatures) -> Tuple[str, float]:
        """의료진(사령관) 발화 톤 분류"""
        if f.mean_energy > self.HIGH_ENERGY_THRESH * 1.2 and f.speaking_rate_syl_per_sec > self.FAST_SPEECH_THRESH:
            return CommanderTone.URGENT.value, 0.82
        if f.pitch_variability > 50 and f.mean_energy > self.LOW_ENERGY_THRESH * 1.5:
            return CommanderTone.ENCOURAGING.value, 0.75
        if f.speaking_rate_syl_per_sec < self.SLOW_SPEECH_THRESH * 1.2 and f.pause_ratio > 0.3:
            return CommanderTone.EMPATHETIC.value, 0.78
        if f.mean_energy < self.LOW_ENERGY_THRESH * 1.5 and f.pitch_variability < 30:
            return CommanderTone.CALM.value, 0.80
        return CommanderTone.INSTRUCTIVE.value, 0.70


# ════════════════════════════════════════════════════════════════════════════
# 임상 지표 계산
# ════════════════════════════════════════════════════════════════════════════

def _compute_clinical_indices(f: AudioFeatures, emotion_scores: dict) -> Tuple[float, float, float, float]:
    """(stress, fatigue, pain, cooperation) 0–100 지수 반환"""
    stress = min(100, (
        emotion_scores.get(PatientEmotion.ANXIOUS.value, 0) * 15
        + emotion_scores.get(PatientEmotion.AGITATED.value, 0) * 12
        + emotion_scores.get(PatientEmotion.IN_PAIN.value, 0) * 10
        + f.energy_variability * 200
    ))
    fatigue = min(100, (
        emotion_scores.get(PatientEmotion.FATIGUED.value, 0) * 18
        + emotion_scores.get(PatientEmotion.DEPRESSED.value, 0) * 12
        + f.pause_ratio * 80
        + max(0, (3.0 - f.speaking_rate_syl_per_sec)) * 10
    ))
    pain = min(100, (
        emotion_scores.get(PatientEmotion.IN_PAIN.value, 0) * 20
        + f.zcr_mean * 300
        + f.pitch_variability * 0.5
    ))
    coop = min(100, max(0, (
        emotion_scores.get(PatientEmotion.COOPERATIVE.value, 0) * 20
        + emotion_scores.get(PatientEmotion.CALM.value, 0) * 15
        - emotion_scores.get(PatientEmotion.AGITATED.value, 0) * 10
        - emotion_scores.get(PatientEmotion.CONFUSED.value, 0) * 8
        + 30  # 베이스라인
    )))
    return round(stress, 1), round(fatigue, 1), round(pain, 1), round(coop, 1)


def _get_alert_level(stress: float, pain: float, fatigue: float) -> str:
    max_index = max(stress, pain, fatigue)
    if max_index >= 75:  return "critical"
    if max_index >= 55:  return "alert"
    if max_index >= 35:  return "watch"
    return "normal"


def _generate_clinical_note(emotion: str, stress: float, pain: float,
                             fatigue: float, coop: float, f: AudioFeatures) -> Tuple[str, str]:
    note_parts = []
    action_parts = []

    if emotion == PatientEmotion.IN_PAIN.value:
        note_parts.append("환자 음성에서 통증 신호 감지 (피치 변동·ZCR 상승)")
        action_parts.append("통증 척도(NRS) 재평가 · 진통제 처방 검토")
    elif emotion == PatientEmotion.ANXIOUS.value:
        note_parts.append("발화 속도 및 에너지 상승 — 불안 패턴")
        action_parts.append("심호흡 안내 · 항불안 중재 고려 · 정보 제공 강화")
    elif emotion == PatientEmotion.FATIGUED.value:
        note_parts.append("저에너지·느린 발화 — 심각한 피로 패턴")
        action_parts.append("활력징후 재측정 · 수면 질 평가 · 빈혈 여부 확인")
    elif emotion == PatientEmotion.DEPRESSED.value:
        note_parts.append("단조로운 피치·낮은 에너지 — 우울 가능성")
        action_parts.append("PHQ-9 우울 선별 평가 · 정신건강의학과 협진 고려")
    elif emotion == PatientEmotion.AGITATED.value:
        note_parts.append("고에너지·빠른 발화 — 흥분 또는 급성 혼란 패턴")
        action_parts.append("안전 환경 확보 · 인지 평가 · 원인 질환 확인")
    elif emotion == PatientEmotion.CONFUSED.value:
        note_parts.append("긴 묵음 구간 + 불규칙 발화 — 혼란·지남력 저하")
        action_parts.append("간이정신상태검사(MMSE) 시행 · 전해질·혈당 확인")
    elif emotion in (PatientEmotion.CALM.value, PatientEmotion.COOPERATIVE.value):
        note_parts.append("안정적 발화 패턴 — 협조적 상태")
        action_parts.append("현 치료 계획 유지 · 정기 모니터링 지속")

    if pain >= 60:
        note_parts.append(f"통증 지수 {pain:.0f}/100 — 임계 수준")
        action_parts.append("통증 전문 간호사 즉시 호출")
    if fatigue >= 60:
        note_parts.append(f"피로 지수 {fatigue:.0f}/100 — 검사 필요")
    if coop < 40:
        action_parts.append("치료 동기 면담 실시 권장")

    clinical_note = " | ".join(note_parts) if note_parts else "특이 소견 없음"
    recommended_action = " → ".join(action_parts) if action_parts else "현재 프로토콜 유지"
    return clinical_note, recommended_action


# ════════════════════════════════════════════════════════════════════════════
# 메인 분석 클래스
# ════════════════════════════════════════════════════════════════════════════

class EmotionVoiceAnalyzer:
    """
    사령관 + 환자 이중 화자 감정 분석 엔진

    사용법:
        analyzer = EmotionVoiceAnalyzer()

        # 오디오 배열로 직접 분석
        result = analyzer.analyze(audio_array, sr=16000, speaker_role="patient")

        # WAV 파일 경로로 분석
        result = analyzer.analyze_file("patient_voice.wav", speaker_role="patient")

        # Streamlit UploadedFile 객체로 분석
        result = analyzer.analyze_streamlit_file(uploaded_file, speaker_role="patient")
    """

    def __init__(self):
        self.classifier = EmotionClassifier()

    def analyze(self, audio_array: np.ndarray, sr: int = 16000,
                speaker_role: str = "patient",
                gender_hint: str = "unknown") -> EmotionAnalysisResult:

        result = EmotionAnalysisResult(speaker_role=speaker_role)
        result.timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result.analysis_method = "librosa_based" if LIBROSA_AVAILABLE else "numpy_fallback"

        try:
            features = extract_audio_features(audio_array, sr)
            result.features = features

            if speaker_role == "commander":
                tone, conf = self.classifier.classify_commander(features)
                result.emotion = tone
                result.confidence = conf
                result.clinical_note = f"사령관 발화 톤: {tone} (신뢰도 {conf:.0%})"
                result.recommended_action = "발화 톤 로그 기록 완료"
                result.alert_level = "normal"
            else:
                emotion, conf, scores = self.classifier.classify_patient(features, gender_hint)
                result.emotion = emotion
                result.confidence = conf

                s_idx, f_idx, p_idx, c_score = _compute_clinical_indices(features, scores)
                result.stress_index    = s_idx
                result.fatigue_index   = f_idx
                result.pain_index      = p_idx
                result.cooperation_score = c_score
                result.alert_level = _get_alert_level(s_idx, p_idx, f_idx)

                note, action = _generate_clinical_note(
                    emotion, s_idx, p_idx, f_idx, c_score, features)
                result.clinical_note      = note
                result.recommended_action = action

        except Exception as e:
            logger.error(f"감정 분석 오류: {e}")
            result.emotion = PatientEmotion.UNKNOWN.value
            result.clinical_note = f"분석 중 오류 발생: {e}"

        return result

    def analyze_file(self, wav_path: str, speaker_role: str = "patient",
                     gender_hint: str = "unknown") -> EmotionAnalysisResult:
        if not SCIPY_AVAILABLE:
            r = EmotionAnalysisResult(speaker_role=speaker_role)
            r.clinical_note = "scipy 미설치 — pip install scipy 필요"
            return r
        try:
            sr, data = wav_read(wav_path)
            if data.dtype != np.float32:
                data = data.astype(np.float32) / np.iinfo(data.dtype).max
            return self.analyze(data, sr, speaker_role, gender_hint)
        except Exception as e:
            r = EmotionAnalysisResult(speaker_role=speaker_role)
            r.clinical_note = f"파일 읽기 오류: {e}"
            return r

    def analyze_streamlit_file(self, uploaded_file,
                                speaker_role: str = "patient",
                                gender_hint: str = "unknown") -> EmotionAnalysisResult:
        """Streamlit st.file_uploader() 결과를 직접 받아 분석"""
        import tempfile, os
        suffix = ".wav"
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            result = self.analyze_file(tmp_path, speaker_role, gender_hint)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return result

    def analyze_dual_speakers(self,
                               commander_audio: np.ndarray,
                               patient_audio: np.ndarray,
                               sr: int = 16000) -> dict:
        """사령관 + 환자 동시 분석 — 세션 요약 반환"""
        cmd_result = self.analyze(commander_audio, sr, "commander")
        pat_result = self.analyze(patient_audio,   sr, "patient")
        return {
            "commander": cmd_result,
            "patient":   pat_result,
            "session_summary": _generate_session_summary(cmd_result, pat_result),
        }


def _generate_session_summary(cmd: EmotionAnalysisResult, pat: EmotionAnalysisResult) -> dict:
    """사령관·환자 상호작용 기반 세션 종합 평가"""
    risk_level = pat.alert_level
    interaction_quality = "양호"

    if pat.emotion in (PatientEmotion.AGITATED.value, PatientEmotion.CONFUSED.value):
        if cmd.emotion == CommanderTone.URGENT.value:
            interaction_quality = "주의 필요 (환자 불안정 + 사령관 긴급 톤)"
            risk_level = "alert"
    elif pat.emotion in (PatientEmotion.CALM.value, PatientEmotion.COOPERATIVE.value):
        if cmd.emotion in (CommanderTone.CALM.value, CommanderTone.EMPATHETIC.value):
            interaction_quality = "최적 (상호 안정)"
    elif pat.emotion == PatientEmotion.IN_PAIN.value:
        interaction_quality = "즉각 조치 필요 — 통증 관리 우선"
        risk_level = "critical" if pat.pain_index >= 70 else "alert"

    return {
        "commander_tone":      cmd.emotion,
        "patient_emotion":     pat.emotion,
        "interaction_quality": interaction_quality,
        "session_risk":        risk_level,
        "patient_stress":      pat.stress_index,
        "patient_fatigue":     pat.fatigue_index,
        "patient_pain":        pat.pain_index,
        "cooperation_score":   pat.cooperation_score,
        "priority_action":     pat.recommended_action,
    }


# ════════════════════════════════════════════════════════════════════════════
# Streamlit UI 렌더링 헬퍼
# ════════════════════════════════════════════════════════════════════════════

ALERT_COLORS = {
    "normal":   "#00ff88",
    "watch":    "#ffcc00",
    "alert":    "#ff9800",
    "critical": "#ff4b4b",
}
ALERT_LABELS = {
    "normal":   "정상",
    "watch":    "주의",
    "alert":    "경고",
    "critical": "위급",
}


def render_emotion_result_html(result: EmotionAnalysisResult) -> str:
    """분석 결과 HTML 카드 반환"""
    ac = ALERT_COLORS.get(result.alert_level, "#aaa")
    al = ALERT_LABELS.get(result.alert_level, result.alert_level)
    conf_pct = f"{result.confidence:.0%}"

    if result.speaker_role == "commander":
        return f'<div style="background:rgba(0,20,60,0.7);border:1px solid rgba(0,200,255,0.25);border-radius:8px;padding:12px;font-family:\'Noto Sans KR\',sans-serif;"><div style="color:rgba(0,200,255,0.7);font-size:0.65rem;font-weight:700;margin-bottom:4px;">🎖️ 사령관 발화 분석</div><div style="display:flex;gap:10px;align-items:center;"><span style="color:#fff;font-size:1rem;font-weight:700;">{result.emotion}</span><span style="color:rgba(255,255,255,0.4);font-size:0.65rem;">신뢰도 {conf_pct}</span></div><div style="color:rgba(255,255,255,0.5);font-size:0.62rem;margin-top:4px;">{result.clinical_note}</div></div>'

    # 환자 카드
    def bar(val, color="#00f2ff"):
        w = min(int(val), 100)
        return f'<div style="background:rgba(255,255,255,0.08);border-radius:3px;height:6px;margin-top:2px;"><div style="width:{w}%;background:{color};height:6px;border-radius:3px;transition:width 0.4s;"></div></div>'

    return f'<div style="background:rgba(0,20,40,0.75);border:1px solid {ac}44;border-radius:8px;padding:12px;font-family:\'Noto Sans KR\',sans-serif;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><span style="color:rgba(0,200,255,0.7);font-size:0.65rem;font-weight:700;">🧠 환자 감정·컨디션 분석</span><span style="background:{ac}22;color:{ac};font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:4px;border:1px solid {ac}55;">{al}</span></div><div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px;"><span style="color:#fff;font-size:1.1rem;font-weight:700;">{result.emotion}</span><span style="color:rgba(255,255,255,0.35);font-size:0.62rem;">신뢰도 {conf_pct}</span></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;"><div><div style="color:rgba(255,255,255,0.4);font-size:0.58rem;">스트레스 지수</div><div style="color:#ff9800;font-size:0.75rem;font-weight:700;">{result.stress_index:.0f}/100</div>{bar(result.stress_index, "#ff9800")}</div><div><div style="color:rgba(255,255,255,0.4);font-size:0.58rem;">피로도</div><div style="color:#ffcc00;font-size:0.75rem;font-weight:700;">{result.fatigue_index:.0f}/100</div>{bar(result.fatigue_index, "#ffcc00")}</div><div><div style="color:rgba(255,255,255,0.4);font-size:0.58rem;">통증 가능성</div><div style="color:#ff4b4b;font-size:0.75rem;font-weight:700;">{result.pain_index:.0f}/100</div>{bar(result.pain_index, "#ff4b4b")}</div><div><div style="color:rgba(255,255,255,0.4);font-size:0.58rem;">협조도</div><div style="color:#00ff88;font-size:0.75rem;font-weight:700;">{result.cooperation_score:.0f}/100</div>{bar(result.cooperation_score, "#00ff88")}</div></div><div style="border-top:1px solid rgba(0,200,255,0.1);padding-top:6px;"><div style="color:rgba(0,200,255,0.6);font-size:0.6rem;font-weight:700;margin-bottom:2px;">📋 임상 소견</div><div style="color:rgba(255,255,255,0.75);font-size:0.65rem;line-height:1.5;">{result.clinical_note}</div></div><div style="border-top:1px solid rgba(0,200,255,0.1);padding-top:6px;margin-top:6px;"><div style="color:#00ff88;font-size:0.6rem;font-weight:700;margin-bottom:2px;">⚡ 권고 조치</div><div style="color:rgba(255,255,255,0.7);font-size:0.65rem;">{result.recommended_action}</div></div><div style="color:rgba(255,255,255,0.2);font-size:0.55rem;margin-top:4px;">분석 시각: {result.timestamp} | 방법: {result.analysis_method}</div></div>'


def render_demo_result(scenario: str = "pain") -> EmotionAnalysisResult:
    """
    라이브러리 없이 시나리오 기반 데모 결과 반환
    Streamlit 데모용 — 실제 오디오 없이 UI 확인 가능
    """
    import datetime
    scenarios = {
        "pain": EmotionAnalysisResult(
            speaker_role="patient", emotion=PatientEmotion.IN_PAIN.value,
            confidence=0.84, stress_index=72, fatigue_index=55,
            pain_index=80, cooperation_score=45,
            clinical_note="환자 음성에서 통증 신호 감지 (피치 변동·ZCR 상승)",
            recommended_action="통증 척도(NRS) 재평가 · 진통제 처방 검토",
            alert_level="alert", analysis_method="demo_scenario",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
        "calm": EmotionAnalysisResult(
            speaker_role="patient", emotion=PatientEmotion.COOPERATIVE.value,
            confidence=0.79, stress_index=18, fatigue_index=22,
            pain_index=10, cooperation_score=85,
            clinical_note="안정적 발화 패턴 — 협조적 상태",
            recommended_action="현재 치료 계획 유지 · 정기 모니터링 지속",
            alert_level="normal", analysis_method="demo_scenario",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
        "anxious": EmotionAnalysisResult(
            speaker_role="patient", emotion=PatientEmotion.ANXIOUS.value,
            confidence=0.76, stress_index=65, fatigue_index=30,
            pain_index=25, cooperation_score=55,
            clinical_note="발화 속도 및 에너지 상승 — 불안 패턴",
            recommended_action="심호흡 안내 · 항불안 중재 고려 · 정보 제공 강화",
            alert_level="watch", analysis_method="demo_scenario",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
        "fatigued": EmotionAnalysisResult(
            speaker_role="patient", emotion=PatientEmotion.FATIGUED.value,
            confidence=0.81, stress_index=30, fatigue_index=78,
            pain_index=20, cooperation_score=50,
            clinical_note="저에너지·느린 발화 — 심각한 피로 패턴",
            recommended_action="활력징후 재측정 · 수면 질 평가 · 빈혈 여부 확인",
            alert_level="watch", analysis_method="demo_scenario",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    }
    return scenarios.get(scenario, scenarios["calm"])
