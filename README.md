# 감정 기반 멀티모달 AI 대화 서비스

음성 감정 인식과 공감적 대화를 결합한 AI 대화 서비스입니다.

## 프로젝트 개요

사용자의 음성에서 감정을 인식하고, 이를 기반으로 공감적인 대화를 제공하는 AI 대화 서비스입니다.
- **음성 감정 인식**: 8가지 감정 분류
- **공감적 대화**: Qwen3-14B 모델을 미세조정하여 감정 기반 응답 생성
- **음성 대화**: STT(Whisper) → 감정 분석 → LLM 응답 → TTS(Facebook MMS-TTS)

## 시스템 구성

### Backend (FastAPI)
- **STT**: OpenAI Whisper 기반 음성 인식
- **감정 분석**: Whisper 인코더 기반 감정 분류
- **LLM**: 파인튜닝된 Qwen3-14B (공감 대화 특화)
- **TTS**: Facebook MMS-TTS Korean

### Mobile (React Native + Expo)
- 음성 녹음 및 채팅 인터페이스
- 대화 이력 조회
- 실시간 음성 재생

## 폴더 구조

```
empathetic_chatbot_project/
├── src/                    # 소스 코드
│   ├── backend/           # FastAPI 백엔드 서버
│   ├── mobile/            # React Native 모바일 앱
│   └── README.md          # 소스 코드 상세 문서 및 설치 가이드
└── video/                  # 데모 영상
    ├── 금전문제.mp4
    ├── 동료와의 불화.mp4
    ├── 어머님께 혼남.mp4
    └── 인생고민.mp4
```

## 데모 영상

`video/` 폴더에 다양한 상황에서의 공감적 대화 데모 영상이 포함되어 있습니다:
- **금전문제.mp4** - 금전적 고민 상담 예시
- **동료와의 불화.mp4** - 직장 내 인간관계 고민 예시
- **어머님께 혼남.mp4** - 가족 관계 고민 예시
- **인생고민.mp4** - 진로 및 인생 고민 예시

## 시작하기

소스 코드 설치 및 실행 방법은 [`src/README.md`](src/README.md)를 참고하세요.

## 라이선스

MIT License
