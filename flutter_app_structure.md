# PHARMA-MOBILE Flutter App 구조

## 📁 폴더 구성

```
pharma_mobile/
├── lib/
│   ├── main.dart                 # 앱 진입점
│   ├── screens/
│   │   ├── home_screen.dart      # 홈 화면 (오늘 건강 상태)
│   │   ├── medication_screen.dart # 약물 목록 & 알림
│   │   ├── adherence_screen.dart  # 복약 순응도 (그래프)
│   │   └── settings_screen.dart   # 설정
│   ├── widgets/
│   │   ├── medication_card.dart   # 약물 카드 위젯
│   │   ├── reminder_widget.dart   # 알림 위젯
│   │   └── health_input_widget.dart # 건강 입력 위젯
│   ├── services/
│   │   ├── api_service.dart       # FastAPI 통신
│   │   ├── speech_service.dart    # 음성 입출력
│   │   └── notification_service.dart # 푸시 알림
│   ├── models/
│   │   ├── user.dart
│   │   ├── medication.dart
│   │   └── health_input.dart
│   └── providers/
│       ├── user_provider.dart     # 사용자 상태 관리 (Provider)
│       └── medication_provider.dart
├── pubspec.yaml                  # 의존성 정의
└── README.md
```

---

## 🛠️ pubspec.yaml (의존성)

```yaml
name: pharma_mobile
description: 의료 복약 관리 앱

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # API 통신
  dio: ^5.3.0                    # HTTP 클라이언트
  retrofit: ^4.0.0

  # 상태 관리
  provider: ^6.0.0
  riverpod: ^2.3.0

  # 음성
  speech_to_text: ^6.1.0         # STT (음성 → 텍스트)
  flutter_tts: ^0.13.0           # TTS (텍스트 → 음성)

  # 알림
  flutter_local_notifications: ^16.0.0
  firebase_messaging: ^14.0.0

  # UI
  flutter_spinkit: ^5.2.0        # 로딩 애니메이션
  charts_flutter: ^0.12.0        # 차트 (복약률)
  intl: ^0.19.0                  # 국제화/날짜 포맷

  # 데이터 저장
  sqflite: ^2.3.0                # 로컬 DB
  shared_preferences: ^2.2.0     # 설정 저장

  # 유틸
  http: ^1.1.0
  json_serializable: ^6.7.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  build_runner: ^2.4.0
  json_serializable: ^6.7.0

flutter:
  uses-material-design: true
  assets:
    - assets/images/
    - assets/sounds/
```

---

## 📱 주요 화면 설계

### 1️⃣ **홈 화면 (Home Screen)**

```
┌─────────────────────────────────┐
│  👤 김철수 (68세, 남성)          │  (헤더)
├─────────────────────────────────┤
│                                  │
│  오늘 몸 상태는 어떤가요?        │
│  ┌──────────────────────────┐   │
│  │ 📝 텍스트 입력            │   │
│  │ [어제보다 다리가 붓는 느낌] │   │
│  └──────────────────────────┘   │
│                                  │
│  ┌──────────────────────────┐   │
│  │ 🎤 음성 입력 (START)     │   │  (음성 버튼)
│  └──────────────────────────┘   │
│                                  │
│  ┌──────────────────────────┐   │
│  │ 📷 처방전 사진           │   │  (OCR)
│  └──────────────────────────┘   │
│                                  │
│           [분석 시작]             │
│                                  │
├─────────────────────────────────┤
│ 📊 AI 분석 결과                  │
│ • 아침: 혈압약 먼저             │
│ • 점심: 이뇨제 피하기           │
│ • 저녁: 영양제 + 마그네슘       │
│ • 운동: 부종 완화 요가 (10분)   │
│ • 식단: 염분 제한 중요           │
└─────────────────────────────────┘
```

### 2️⃣ **약물 알림 화면**

```
┌─────────────────────────────────┐
│ 💊 오늘 약물 스케줄             │
├─────────────────────────────────┤
│                                  │
│ 🌅 아침 8:00                     │
│ ┌──────────────────────────┐    │
│ │ ☑️  노바스크정 5mg      │    │ (먹음 표시)
│ │ 용량: 1회 1정, 매일     │    │
│ │ 주의: 자몽주스 금지     │    │
│ └──────────────────────────┘    │
│                                  │
│ 🌤️  점심 12:00                  │
│ ┌──────────────────────────┐    │
│ │ ⬜ 다이아벡스정 500mg   │    │ (아직 안 먹음)
│ │ 용량: 1회 1정, 2일 2회  │    │
│ │ 주의: 식사 직후 복용     │    │
│ └──────────────────────────┘    │
│                                  │
│ 🌙 저녁 19:00                    │
│ ┌──────────────────────────┐    │
│ │ ☑️  마그네슘 400mg      │    │
│ │ 용량: 1캡슐             │    │
│ │ 시너지: 혈압 안정화     │    │
│ └──────────────────────────┘    │
│                                  │
│ 📊 오늘 복약률: 66% (2/3)       │
└─────────────────────────────────┘
```

### 3️⃣ **복약 순응도 (그래프)**

```
┌─────────────────────────────────┐
│ 📈 복약 순응도 (최근 7일)       │
├─────────────────────────────────┤
│                                  │
│  100%│     ●                     │
│       │    ╱ ╲                   │
│   80%│   ╱   ●─●                │  (꺾은선 그래프)
│       │  ╱                       │
│   60%│ ●                         │
│       │                          │
│   40%│                           │
│                                  │
│   월 화 수 목 금 토 일          │
│                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ 약물별 순응도:                  │
│ • 노바스크: 100% (7/7)         │
│ • 당뇨약: 85% (6/7)            │  (성공/실패 통계)
│ • 영양제: 57% (4/7)            │
│                                  │
│ 전체 평균: 81%                   │
└─────────────────────────────────┘
```

### 4️⃣ **AI 조언 상세**

```
┌─────────────────────────────────┐
│ 🧠 AI 건강 상담                  │
├─────────────────────────────────┤
│                                  │
│ 📌 현재 상태: 다리 부종          │
│                                  │
│ 💡 약물 순서 (중요!)            │
│    1. 노바스크 (혈관 확장)      │
│    2. 라식스 (이뇨)             │
│    3. 30분 후 마그네슘          │
│    ⚠️  NOTE: 이 순서로 먹어야  │
│        효과가 최고!             │
│                                  │
│ 🍎 추천 식단                     │
│    • 저염 고단백                │
│    • 칼륨 풍부 (바나나, 고구마) │
│    • 부종 완화 (팥, 옥수수)     │
│                                  │
│ 💪 운동                          │
│    • 저강도 요가 (10분)         │
│    • 다리 마사지 (5분)          │
│    ⏰ 식후 30분 시작            │
│                                  │
│ 🌿 영양제 시너지                 │
│    + 마그네슘: 혈압 안정        │
│    + 칼슘: 뼈 건강              │
│    + Omega-3: 염증 완화         │
│                                  │
│ ⚠️  주의사항                     │
│    • 찬 음료 피하기             │
│    • 자몽주스 금지              │
│    • 염분 섭취 제한             │
│                                  │
└─────────────────────────────────┘
```

---

## 🔔 **알림 시스템 (Notification)**

```
┌────────────────────────────┐
│  🔔 약 복용 시간입니다!   │
├────────────────────────────┤
│                            │
│  💊 노바스크정 5mg        │
│  시간: 아침 8:00           │
│  용량: 1회 1정            │
│                            │
│  [지금 복용]  [나중에]    │
│                            │
└────────────────────────────┘

타이밍: 지정된 시간에 알림 (로컬 + FCM)
```

---

## 🚀 **구현 로드맵**

### Phase 1: 기본 틀 (1주)
- [ ] Flutter 프로젝트 설정
- [ ] 기본 화면 UI
- [ ] API 통신 구현

### Phase 2: 핵심 기능 (2주)
- [ ] 음성 입력/STT
- [ ] 약물 알림 시스템
- [ ] 복약 기록

### Phase 3: AI 통합 (1주)
- [ ] Gemini API 연동
- [ ] 건강 상태 분석
- [ ] 추천 생성

### Phase 4: 고급 기능 (1주)
- [ ] 복약률 그래프
- [ ] 푸시 알림
- [ ] 약물 상호작용 경고

---

## 📝 **핵심 Dart 코드 예시**

### main.dart
```dart
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => UserProvider()),
        ChangeNotifierProvider(create: (_) => MedicationProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PHARMA-MOBILE',
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: Colors.cyan,
      ),
      home: const HomeScreen(),
    );
  }
}
```

### api_service.dart
```dart
class ApiService {
  static const String baseUrl = "http://192.168.x.x:8000"; // 백엔드 IP

  Future<Map> analyzeHealth(String userId, String input) async {
    final response = await dio.post(
      "$baseUrl/api/health/analyze",
      data: {
        "user_id": userId,
        "input_type": "text",
        "content": input,
      },
    );
    return response.data;
  }

  Future<Map> logMedication(String userId, String medName, bool taken) async {
    final response = await dio.post(
      "$baseUrl/api/medication/log",
      data: {
        "user_id": userId,
        "medication_name": medName,
        "taken": taken,
      },
    );
    return response.data;
  }
}
```

### speech_service.dart
```dart
class SpeechService {
  final SpeechToText _speechToText = SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();

  Future<String> startListening() async {
    if (!_speechToText.isAvailable) return "";
    
    await _speechToText.listen(
      onResult: (result) {
        print("인식된 텍스트: ${result.recognizedWords}");
      },
      localeId: "ko_KR", // 한국어
    );
    
    return "listening";
  }

  Future<void> speak(String text) async {
    await _flutterTts.setLanguage("ko-KR");
    await _flutterTts.speak(text);
  }
}
```

---

## 🌐 **배포**

### iOS
```bash
flutter pub get
flutter build ios --release
# Xcode에서 App Store 배포
```

### Android
```bash
flutter pub get
flutter build apk --release
# Google Play 배포
```

---

## 📊 **예상 개발 시간**

| 단계 | 소요 시간 |
|------|---------|
| 백엔드 API | 3일 |
| Flutter UI | 5일 |
| 기능 통합 | 3일 |
| 테스트 & QA | 4일 |
| **총합** | **~2주** |

---

## 💰 **비용 (클라우드 배포)**

| 서비스 | 비용/월 |
|-------|--------|
| Google Cloud (FastAPI) | $10-50 |
| Firebase (알림) | Free (무료) |
| Gemini API (한정) | $10-50 |
| **총합** | **$20-100/월** |
