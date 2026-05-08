#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kakao_token_helper.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
카카오 OAuth 액세스 토큰 발급 도우미

[사용법]
  python kakao_token_helper.py

[흐름]
  1. 브라우저에서 Kakao 로그인 URL 자동 열기
  2. 로그인 후 리다이렉트 URL에서 code 값 복사
  3. 이 스크립트에 붙여넣기 → access_token 자동 발급
  4. 발급된 토큰 → .env / secrets.toml 에 자동 저장

[카카오 개발자 콘솔 설정 필요]
  https://developers.kakao.com
  → 내 애플리케이션 → [앱 선택]
  → 제품 설정 → 카카오 로그인 → 활성화
  → Redirect URI 추가: http://localhost:5000/callback
  → 동의항목 → 카카오톡 메시지 전송 → 선택 동의 설정
"""

import os
import json
import urllib.request
import urllib.parse
import webbrowser

# ── REST API 키 로드 ─────────────────────────────────────────────────────────
def _load_key():
    # .env 에서 직접 읽기
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("KAKAO_REST_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("KAKAO_REST_API_KEY", "")


REST_API_KEY  = _load_key()
REDIRECT_URI  = "https://localhost"          # 개발자 콘솔에 등록한 URI와 동일하게
SCOPE         = "talk_message"               # 카카오톡 메시지 발송 권한


def get_auth_url() -> str:
    params = urllib.parse.urlencode({
        "client_id":     REST_API_KEY,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
    })
    return f"https://kauth.kakao.com/oauth/authorize?{params}"


def exchange_code_for_token(auth_code: str) -> dict:
    """인가 코드 → 액세스 토큰 교환."""
    data = urllib.parse.urlencode({
        "grant_type":   "authorization_code",
        "client_id":    REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code":         auth_code,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def save_tokens(access_token: str, refresh_token: str):
    """발급된 토큰을 .env 와 secrets.toml 에 저장."""
    # .env 업데이트
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    if os.path.exists(env_path):
        lines = open(env_path, encoding="utf-8").readlines()

    updated = {"KAKAO_ACCESS_TOKEN": False, "KAKAO_REFRESH_TOKEN": False}
    new_lines = []
    for line in lines:
        for k in updated:
            if line.startswith(f"{k}="):
                val = access_token if k == "KAKAO_ACCESS_TOKEN" else refresh_token
                line = f"{k}={val}\n"
                updated[k] = True
                break
        new_lines.append(line)
    for k, done in updated.items():
        if not done:
            val = access_token if k == "KAKAO_ACCESS_TOKEN" else refresh_token
            new_lines.append(f"{k}={val}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ .env 저장 완료")

    # secrets.toml 업데이트
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if os.path.exists(toml_path):
        content = open(toml_path, encoding="utf-8").read()
        import re
        content = re.sub(
            r'KAKAO_ACCESS_TOKEN\s*=\s*"[^"]*"',
            f'KAKAO_ACCESS_TOKEN   = "{access_token}"',
            content
        )
        content = re.sub(
            r'KAKAO_REFRESH_TOKEN\s*=\s*"[^"]*"',
            f'KAKAO_REFRESH_TOKEN  = "{refresh_token}"',
            content
        )
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ secrets.toml 저장 완료")


def main():
    print("=" * 60)
    print("  PHARMA-HYBRID 카카오톡 토큰 발급 도우미")
    print("=" * 60)

    if not REST_API_KEY:
        print("❌ KAKAO_REST_API_KEY 가 설정되지 않았습니다.")
        print("   .env 파일에 KAKAO_REST_API_KEY=<키> 를 추가하세요.")
        return

    print(f"\n🔑 REST API 키: {REST_API_KEY[:8]}{'*' * 20}")
    print(f"\n📋 카카오 개발자 콘솔에서 아래 URI를 Redirect URI로 등록하세요:")
    print(f"   {REDIRECT_URI}")
    print(f"\n[Step 1] 브라우저에서 아래 URL을 열고 카카오 로그인 후")
    print(f"         리다이렉트된 URL의 'code=' 값을 복사하세요.\n")

    auth_url = get_auth_url()
    print(f"  {auth_url}\n")

    try:
        webbrowser.open(auth_url)
        print("  (브라우저 자동 오픈 시도...)")
    except Exception:
        print("  (브라우저 자동 오픈 실패 — 위 URL을 직접 열어주세요)")

    print("\n[Step 2] 리다이렉트 URL 예시:")
    print(f"  https://localhost/?code=XXXXXXXXXXXX&state=...")
    print(f"           ^^^^^^^^^^^^^^^^^^^^ 이 부분 복사\n")

    auth_code = input("👉 code 값 붙여넣기: ").strip()
    if not auth_code:
        print("❌ 인가 코드가 비어있습니다.")
        return

    print("\n🔄 액세스 토큰 발급 중...")
    try:
        result = exchange_code_for_token(auth_code)
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return

    access_token  = result.get("access_token", "")
    refresh_token = result.get("refresh_token", "")

    if not access_token:
        print(f"❌ 토큰 발급 실패: {result}")
        return

    print(f"\n✅ 액세스 토큰 발급 성공!")
    print(f"   access_token  : {access_token[:12]}...")
    print(f"   refresh_token : {refresh_token[:12] if refresh_token else '없음'}...")
    print(f"   expires_in    : {result.get('expires_in', '?')}초\n")

    save_tokens(access_token, refresh_token)

    print("\n🎉 완료! 이제 보호자 알림 카카오톡 발송이 작동합니다.")
    print("   앱을 재시작하면 새 토큰이 자동으로 적용됩니다.")


if __name__ == "__main__":
    main()
