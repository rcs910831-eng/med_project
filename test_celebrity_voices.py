#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트: Celebrity Voice Engine
연예인 목소리 TTS 엔진 테스트 스크립트
"""

import sys
import os

print("=" * 70)
print("🎤 Celebrity Voice Engine 테스트")
print("=" * 70)

try:
    from celebrity_voice_engine import CelebrityVoiceEngine, VoiceSessionManager
    print("✅ celebrity_voice_engine 모듈 로드 성공\n")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    sys.exit(1)

# 1. 엔진 생성
print("1️⃣  음성 엔진 생성")
print("-" * 70)
try:
    engine = CelebrityVoiceEngine(engine_type="gtts")
    print("✅ gTTS 엔진 생성 성공\n")
except Exception as e:
    print(f"⚠️  gTTS 엔진 생성 실패: {e}")
    print("   pyttsx3 또는 다른 엔진으로 시도 중...\n")
    try:
        engine = CelebrityVoiceEngine(engine_type="pyttsx3")
        print("✅ pyttsx3 엔진 생성 성공\n")
    except Exception as e2:
        print(f"❌ 모든 엔진 생성 실패: {e2}")
        sys.exit(1)

# 2. 사용 가능한 음성 확인
print("2️⃣  사용 가능한 연예인 음성 목록")
print("-" * 70)
voices = engine.get_available_voices()
for i, (voice_name, profile) in enumerate(voices.items(), 1):
    print(f"   {i}. {voice_name}")
    print(f"      {profile['description']}")
    print(f"      - 그룹: {profile.get('group', 'N/A')}")
    print(f"      - 스타일: {profile.get('style', 'N/A')}")
    print()

# 3. 음성 선택 테스트
print("3️⃣  각 음성으로 텍스트 합성 테스트")
print("-" * 70)

test_texts = [
    ("기본 인사", "안녕하세요. 약물 정보 시스템입니다."),
    ("의료 정보", "타세바정은 표피 성장 인자 수용체 억제제입니다."),
    ("식단 가이드", "환자님께서는 단백질을 충분히 섭취하시고, 짜고 자극적인 음식은 피하세요."),
]

for voice_name in ["기본(로봇)", "장원영(Wonyoung)", "카리나(Karina)", "안유진(Yujin)"]:
    print(f"\n📢 {voice_name} 음성 테스트:")
    if not engine.set_voice(voice_name):
        print(f"   ❌ '{voice_name}' 음성 설정 실패")
        continue

    for text_type, text in test_texts[:1]:  # 첫 번째 텍스트만 테스트
        try:
            print(f"   [{text_type}] {text[:40]}...", end=" ")
            audio = engine.synthesize_to_audio(text)
            if audio:
                print(f"✅ ({len(audio)} bytes)")
            else:
                print("⚠️  오디오 생성 실패")
        except Exception as e:
            print(f"❌ 오류: {e}")

# 4. 세션 관리자 테스트
print("\n4️⃣  세션 관리자 테스트")
print("-" * 70)

class MockSessionState:
    """Streamlit 세션 상태 모킹"""
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

session = MockSessionState()
mgr = VoiceSessionManager(session)

print("✅ 세션 관리자 생성 성공")
print(f"   - 선택된 음성: {mgr.get_selected_voice()}")
print(f"   - 음성 활성화: {mgr.is_enabled()}")

# 음성 변경
mgr.set_voice("장원영(Wonyoung)")
print(f"   - 변경된 음성: {mgr.get_selected_voice()}")

# 음성 토글
mgr.toggle_voice()
print(f"   - 음성 토글 후: {mgr.is_enabled()}")

print("\n" + "=" * 70)
print("🎉 모든 테스트 완료!")
print("=" * 70)
print("\n💡 다음 단계:")
print("   1. requirements.txt 파일로 필요한 패키지 설치:")
print("      pip install -r requirements.txt")
print("   2. Streamlit 앱 실행:")
print("      streamlit run main_app.py")
print("   3. 웹 브라우저에서 앱 열기")
print("   4. 좌측 사이드바에서 '🎤 음성 낭독' 섹션에서 연예인 목소리 선택")
print("=" * 70)
