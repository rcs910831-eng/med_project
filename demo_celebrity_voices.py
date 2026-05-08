#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연예인 음성 TTS - 실제 사용 예제
Celebrity Voice TTS - Practical Usage Examples
"""

import os
import sys
from celebrity_voice_engine import CelebrityVoiceEngine, VoiceSessionManager


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 1: 기본 사용법 (Basic Usage)
# ═══════════════════════════════════════════════════════════════════════════════

def example_1_basic_usage():
    """기본 음성 합성 예제"""
    print("\n" + "="*70)
    print("예제 1️⃣ : 기본 사용법 (Basic Usage)")
    print("="*70)

    # 음성 엔진 생성
    engine = CelebrityVoiceEngine(engine_type="gtts")
    print("✅ 음성 엔진 생성 완료\n")

    # 의료 정보 텍스트
    medical_text = "타세바정은 표피 성장 인자 수용체 억제제입니다. 폐암 치료에 주로 사용됩니다."

    # 다양한 음성으로 합성
    for voice_name in ["기본(로봇)", "장원영(Wonyoung)", "카리나(Karina)"]:
        print(f"\n📢 {voice_name} 음성으로 합성 중...")
        engine.set_voice(voice_name)

        # 오디오 바이트 생성
        audio = engine.synthesize_to_audio(medical_text)

        if audio:
            # 파일로 저장
            filename = f"output_{voice_name.replace('(', '').replace(')', '')}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio)
            print(f"   ✅ 저장 완료: {filename} ({len(audio)} bytes)")
        else:
            print(f"   ❌ 합성 실패")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 2: HTML5 오디오 플레이어 생성 (HTML Audio Player)
# ═══════════════════════════════════════════════════════════════════════════════

def example_2_html_player():
    """HTML5 오디오 플레이어 생성 예제"""
    print("\n" + "="*70)
    print("예제 2️⃣ : HTML5 오디오 플레이어 생성 (HTML Audio Player)")
    print("="*70)

    engine = CelebrityVoiceEngine(engine_type="gtts")

    # 암 치료 정보
    cancer_info = "자궁육종암은 자궁 근육층에서 발생하는 악성 종양입니다. 1차 치료는 수술과 항암 화학요법입니다."

    # 각 음성으로 HTML 생성
    for voice_name in ["장원영(Wonyoung)", "카리나(Karina)", "안유진(Yujin)"]:
        print(f"\n🎤 {voice_name} 음성 - HTML 플레이어 생성 중...")

        html = engine.create_audio_html_player(cancer_info, voice_name)

        if html:
            # HTML 파일로 저장
            filename = f"player_{voice_name.replace('(', '').replace(')', '')}.html"
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{voice_name} - 암 치료 정보</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; margin: 20px; background: #0a1628; color: white; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #00f2ff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 {voice_name} 음성</h1>
        <p><strong>텍스트:</strong> {cancer_info}</p>
        <hr>
        {html}
    </div>
</body>
</html>
"""
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   ✅ 저장 완료: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 3: 세션 관리자 사용 (Session Manager)
# ═══════════════════════════════════════════════════════════════════════════════

def example_3_session_manager():
    """세션 관리자 사용 예제"""
    print("\n" + "="*70)
    print("예제 3️⃣ : 세션 관리자 사용 (Session Manager)")
    print("="*70)

    # 간단한 세션 상태 시뮬레이션
    class SimpleSession:
        def __init__(self):
            self.data = {}

        def __setitem__(self, key, value):
            self.data[key] = value

        def __getitem__(self, key):
            return self.data.get(key)

        def __contains__(self, key):
            return key in self.data

        def get(self, key, default=None):
            return self.data.get(key, default)

    # 세션 생성 및 관리자 초기화
    session = SimpleSession()
    voice_mgr = VoiceSessionManager(session)

    print("\n📋 초기 상태:")
    print(f"   - 선택된 음성: {voice_mgr.get_selected_voice()}")
    print(f"   - 음성 활성화: {voice_mgr.is_enabled()}")

    # 음성 변경
    print("\n🎤 음성 변경:")
    for voice in ["장원영(Wonyoung)", "카리나(Karina)", "안유진(Yujin)"]:
        voice_mgr.set_voice(voice)
        print(f"   ✓ {voice_mgr.get_selected_voice()}")

    # 음성 토글
    print("\n🔊 음성 토글:")
    print(f"   - 활성 전: {voice_mgr.is_enabled()}")
    voice_mgr.toggle_voice()
    print(f"   - 활성 후: {voice_mgr.is_enabled()}")

    voice_mgr.toggle_voice()
    print(f"   - 비활성 후: {voice_mgr.is_enabled()}")

    # 음성으로 합성
    print("\n🎵 텍스트 합성:")
    text = "당뇨병 환자는 단백질을 충분히 섭취하세요."
    audio_b64 = voice_mgr.synthesize(text)
    if audio_b64:
        print(f"   ✅ Base64 인코딩 완료 ({len(audio_b64)} chars)")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 4: 의료 정보 음성화 (Medical Info to Voice)
# ═══════════════════════════════════════════════════════════════════════════════

def example_4_medical_info():
    """의료 정보를 음성으로 변환하는 예제"""
    print("\n" + "="*70)
    print("예제 4️⃣ : 의료 정보 음성화 (Medical Information)")
    print("="*70)

    engine = CelebrityVoiceEngine(engine_type="gtts")

    # 의료 정보 샘플들
    medical_samples = {
        "FDA 약품 정보": "아바스틴은 혈관 내피 성장 인자 억제제입니다. 대장암, 폐암, 유방암 등의 치료에 사용됩니다. 주의사항으로는 고혈압과 단백뇨가 있습니다.",

        "암 프로토콜": "자궁육종암은 자궁 근육층에서 발생하는 악성 종양입니다. ICD10 코드는 C54.3입니다. 바이오마커는 TP53 변이입니다. 1차 치료는 자궁 전절제술과 보조 항암화학요법입니다.",

        "식단 가이드": "대장암 환자는 식이섬유를 충분히 섭취해야 합니다. 권장 식품으로는 보리, 현미, 시금치, 브로콜리가 있습니다. 제한해야 할 음식은 자극적이고 기름진 음식입니다."
    }

    voice = "장원영(Wonyoung)"
    engine.set_voice(voice)

    print(f"\n🎤 선택 음성: {voice}")
    print("-" * 70)

    for info_type, text in medical_samples.items():
        print(f"\n📌 {info_type}")
        print(f"   텍스트: {text[:60]}...")

        # 음성 합성
        audio = engine.synthesize_to_audio(text)
        if audio:
            print(f"   ✅ 합성 성공 ({len(audio)} bytes)")

            # 파일 저장
            safe_name = info_type.replace(" ", "_")
            filename = f"medical_{safe_name}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio)
            print(f"   💾 저장: {filename}")
        else:
            print(f"   ❌ 합성 실패")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 5: 모든 음성 비교 (Voice Comparison)
# ═══════════════════════════════════════════════════════════════════════════════

def example_5_voice_comparison():
    """모든 음성을 비교하는 예제"""
    print("\n" + "="*70)
    print("예제 5️⃣ : 모든 음성 비교 (Voice Comparison)")
    print("="*70)

    engine = CelebrityVoiceEngine(engine_type="gtts")

    # 테스트 문장
    test_sentence = "안녕하세요. 약물 정보 시스템입니다."

    print(f"\n📢 테스트 문장: {test_sentence}\n")

    # 모든 음성 정보 표시
    voices = engine.get_available_voices()
    print(f"{'음성명':<20} | {'그룹':<10} | {'설명':<30} | {'음높이':<5} | {'속도':<5}")
    print("-" * 80)

    for voice_name, profile in voices.items():
        print(f"{voice_name:<20} | {profile['group']:<10} | {profile['description']:<30} | "
              f"{profile['pitch']:<5} | {profile['speed']:<5}")

        # 각 음성으로 합성
        engine.set_voice(voice_name)
        audio = engine.synthesize_to_audio(test_sentence)
        if audio:
            filename = f"compare_{voice_name.replace('(', '').replace(')', '')}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio)
            print(f"   └─ ✅ 저장: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 6: 커스텀 음성 추가 (Custom Voice)
# ═══════════════════════════════════════════════════════════════════════════════

def example_6_custom_voice():
    """새로운 음성을 추가하는 예제"""
    print("\n" + "="*70)
    print("예제 6️⃣ : 커스텀 음성 추가 (Custom Voice)")
    print("="*70)

    engine = CelebrityVoiceEngine(engine_type="gtts")

    # 새로운 음성 추가
    new_voice = {
        "name": "CustomVoice",
        "group": "Custom",
        "description": "커스텀 음성 - 개인 맞춤형",
        "pitch": 0.9,
        "speed": 0.88,
        "style": "professional",
        "color": "#9C27B0"
    }

    print("\n➕ 새로운 음성 추가:")
    engine.CELEBRITY_VOICES["커스텀음성"] = new_voice
    print("   ✅ '커스텀음성' 추가 완료\n")

    # 추가된 음성 확인
    voices = engine.get_available_voices()
    print(f"📋 현재 사용 가능한 음성 ({len(voices)}개):")
    for i, voice_name in enumerate(voices.keys(), 1):
        print(f"   {i}. {voice_name}")

    # 새 음성으로 합성
    print("\n🎤 커스텀 음성으로 합성:")
    text = "이것은 새로 추가된 커스텀 음성입니다."
    engine.set_voice("커스텀음성")
    audio = engine.synthesize_to_audio(text)
    if audio:
        with open("custom_voice_test.mp3", 'wb') as f:
            f.write(audio)
        print(f"   ✅ 저장: custom_voice_test.mp3")


# ═══════════════════════════════════════════════════════════════════════════════
# 예제 7: 배치 처리 (Batch Processing)
# ═══════════════════════════════════════════════════════════════════════════════

def example_7_batch_processing():
    """여러 텍스트를 한 번에 처리하는 예제"""
    print("\n" + "="*70)
    print("예제 7️⃣ : 배치 처리 (Batch Processing)")
    print("="*70)

    engine = CelebrityVoiceEngine(engine_type="gtts")

    # 처리할 항목들
    batch_items = [
        ("약물_타세바정", "타세바정"),
        ("약물_키트루다", "키트루다"),
        ("질환_폐암", "폐암"),
        ("질환_대장암", "대장암"),
        ("증상_피로", "피로"),
    ]

    voices_to_process = ["기본(로봇)", "장원영(Wonyoung)"]

    print(f"\n📊 배치 정보:")
    print(f"   - 처리할 항목: {len(batch_items)}개")
    print(f"   - 음성: {', '.join(voices_to_process)}")
    print(f"   - 총 생성 파일: {len(batch_items) * len(voices_to_process)}개\n")

    count = 0
    for item_id, item_text in batch_items:
        for voice_name in voices_to_process:
            engine.set_voice(voice_name)
            audio = engine.synthesize_to_audio(item_text)
            if audio:
                safe_voice = voice_name.replace("(", "").replace(")", "")
                filename = f"batch_{item_id}_{safe_voice}.mp3"
                with open(filename, 'wb') as f:
                    f.write(audio)
                count += 1
                print(f"   ✅ [{count:2d}] {filename}")

    print(f"\n✨ 배치 처리 완료: {count}개 파일 생성")


# ═══════════════════════════════════════════════════════════════════════════════
# 메인 함수
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """모든 예제 실행"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "연예인 음성 TTS - 파이썬 예제 모음" + " "*22 + "║")
    print("║" + " "*10 + "Celebrity Voice TTS - Python Examples" + " "*20 + "║")
    print("╚" + "="*68 + "╝")

    examples = [
        ("1. 기본 사용법", example_1_basic_usage),
        ("2. HTML5 오디오 플레이어", example_2_html_player),
        ("3. 세션 관리자", example_3_session_manager),
        ("4. 의료 정보 음성화", example_4_medical_info),
        ("5. 음성 비교", example_5_voice_comparison),
        ("6. 커스텀 음성 추가", example_6_custom_voice),
        ("7. 배치 처리", example_7_batch_processing),
    ]

    print("\n📋 사용 가능한 예제:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")

    print("\n" + "="*70)
    print("💡 팁: 특정 예제만 실행하려면 아래 코드를 사용하세요:")
    print("   example_1_basic_usage()")
    print("   example_2_html_player()")
    print("   ... 등등")
    print("="*70)

    # 모든 예제 실행
    try:
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\n⚠️  {name} 실행 중 오류: {e}")
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

    print("\n" + "="*70)
    print("✨ 모든 예제 실행 완료!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
