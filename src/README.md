# Empathetic Chatbot - 공감형 음성 챗봇

음성 감정 인식과 공감적 대화를 결합한 AI 챗봇 시스템입니다.

## 프로젝트 구성

- **Backend**: FastAPI 기반 AI 서버 (STT, 감정 인식, LLM, TTS)
- **Mobile**: React Native (Expo) 모바일 앱

## 주요 기능

### 음성 감정 인식 (Speech Emotion Recognition)
- Whisper 인코더 기반 감정 분류
- 8가지 감정 클래스: neutral, calm, happy, sad, angry, fearful, disgust, surprised
- Top-3 감정 확률 제공

### 음성-텍스트 변환 (STT)
- OpenAI Whisper 모델 (whisper-base)
- 한국어 음성 인식 최적화

### 공감적 대화 생성 (LLM)
- **파인튜닝된 Qwen3-14B 모델** 사용 (공감 대화 특화)
- 감정을 고려한 공감적 응답
- Toxic Positivity 방지 (피상적 위로 차단)
- 자연스러운 한국어 구어체

### 음성 합성 (TTS)
- Facebook MMS-TTS Korean 모델
- 자연스러운 한국어 음성 합성

### 대화 이력 관리
- **SQLite**: 로컬 대화 저장 및 이력 조회 (기본)
- **Vertex AI Memory Bank**: 클라우드 대화 저장 (선택사항)

## 프로젝트 구조

```
empathetic_chatbot_project/
├── backend/                          # FastAPI 백엔드
│   ├── main.py                      # 서버 진입점
│   ├── config.py                    # 설정 파일
│   ├── requirements.txt             # Python 의존성
│   ├── controller/                  # API 라우터
│   │   ├── chat_controller.py      # 채팅 API
│   │   └── history_controller.py   # 대화 이력 API
│   ├── service/                     # 비즈니스 로직
│   │   ├── stt_service.py          # Whisper STT
│   │   ├── emotion_service.py      # 감정 분류
│   │   ├── llm_service.py          # LLM 응답 생성
│   │   ├── tts_service.py          # TTS
│   │   └── vertex_memory_service.py # Vertex AI (선택)
│   ├── models/                      # AI 모델 & DB
│   │   ├── emotion_model.py        # 감정 모델
│   │   ├── llm_model.py            # LLM 래퍼
│   │   ├── database.py             # SQLite DB
│   │   └── schemas.py              # API 스키마
│   └── utils/                       # 유틸리티
│       └── audio_utils.py
└── mobile/                           # React Native 앱
    ├── App.js                       # 앱 진입점
    ├── src/
    │   ├── screens/                 # 화면 컴포넌트
    │   │   ├── ChatScreen.js       # 채팅 화면
    │   │   └── HistoryScreen.js    # 이력 화면
    │   ├── components/              # UI 컴포넌트
    │   │   ├── MessageBubble.js    # 메시지 버블
    │   │   └── VoiceRecorder.js    # 음성 녹음
    │   ├── services/                # API 서비스
    │   │   └── api.js              # API 클라이언트
    │   └── constants/               # 설정
    │       └── config.js            # API 주소 설정
    └── package.json
```

## 설치 및 실행

### Backend 설정

#### Python 환경 설정
```bash
# Python 3.10+ 권장
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 의존성 설치
cd backend
pip install -r requirements.txt
```

#### 모델 다운로드

**자동 다운로드 모델** (서버 첫 실행 시):
- **Whisper (STT)**: openai/whisper-base (~290MB)
- **Facebook MMS-TTS**: facebook/mms-tts-kor (~400MB)
- **Qwen3-14B**: Qwen/Qwen3-14B (~28GB) - 파인튜닝 모델이 없을 때만

**참고**: 모델 다운로드에 시간이 소요됩니다 (인터넷 속도 및 디스크 공간 필요).

**수동 배치 모델** (선택사항):

1. **파인튜닝된 LLM 모델 (강력 권장)**
   ```
   backend/models/finetuned-model/
   ```
   - 공감 대화에 최적화된 파인튜닝 Qwen3-14B 모델
   - **모델 우선순위**:
     1. `finetuned-model/` 존재 → 파인튜닝 모델 사용
     2. 없는 경우 → 기본 Qwen3-14B 자동 다운로드

2. **감정 분류 모델**
   ```
   backend/models/emotionExtract.pth
   ```
   - Whisper 기반 감정 분류 모델
   - 없으면 감정 분석 없이 일반 대화만 가능

#### 백엔드 서버 실행
```bash
cd backend
python main.py
```

서버 주소:
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/chat/health

### Mobile 앱 설정

```bash
cd mobile
npm install
npm start
```

Expo 앱에서 QR 코드를 스캔하거나 에뮬레이터에서 실행하세요.

**API 주소 설정** ([mobile/src/constants/config.js](mobile/src/constants/config.js)):
```javascript
export const API_BASE_URL = __DEV__
  ? 'http://localhost:8000'  // 개발: 로컬 서버
  : 'https://your-backend-url.com';  // 프로덕션: 실제 서버 주소
```

## API 엔드포인트

### 음성 채팅
```http
POST /api/chat/voice
Content-Type: multipart/form-data

Parameters:
  - audio: 음성 파일 (wav, mp3, flac)
  - conversation_id: (선택) 대화 ID

Response:
{
  "transcribed_text": "변환된 텍스트",
  "detected_emotion": "감지된 감정",
  "emotion_probability": 0.85,
  "emotion_top3": [...],
  "llm_response": "공감적 응답",
  "conversation_id": "uuid"
}
```

### 텍스트 채팅
```http
POST /api/chat/text
Content-Type: application/json

Body:
{
  "message": "사용자 메시지",
  "conversation_id": "uuid (선택)"
}
```

### TTS (음성 합성)
```http
POST /api/chat/tts
Content-Type: application/x-www-form-urlencoded

Parameters:
  - text: 텍스트 메시지

Response: audio/wav
```

### 대화 이력
```http
GET /api/history/conversations?limit=50
GET /api/history/conversations/{conversation_id}
DELETE /api/history/conversations/{conversation_id}
```

**API 문서**: http://localhost:8000/docs

## 기술 스택

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| **FastAPI** | 0.120.0 | 웹 프레임워크 |
| **PyTorch** | 2.5.1 | 딥러닝 프레임워크 |
| **Transformers** | 4.57.1 | Hugging Face 모델 |
| **Whisper** | openai/whisper-base | STT |
| **Qwen3-14B** | Qwen/Qwen3-14B | LLM (파인튜닝) |
| **MMS-TTS** | facebook/mms-tts-kor | TTS |
| **SQLite** | - | 대화 이력 저장 |
| **SQLAlchemy** | - | ORM |

### Mobile
| 기술 | 용도 |
|------|------|
| **React Native** | 모바일 앱 프레임워크 |
| **Expo** | 개발 환경 |
| **React Navigation** | 화면 네비게이션 |
| **Expo Audio** | 음성 녹음/재생 |

## 선택 기능: Vertex AI Memory Bank

SQLite 외에 Google Cloud Vertex AI Memory Bank를 사용하여 대화 이력을 클라우드에 저장할 수 있습니다.

### 설정 방법

1. `backend/.env` 파일 생성 (`.env.example` 복사):
   ```env
   MEMORY_BANK_ENABLED=true
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   VERTEX_AI_AGENT_ENGINE_ID=your-agent-engine-id
   ```

2. Google Cloud 인증:
   ```bash
   gcloud auth application-default login
   ```

자세한 내용: [Vertex AI 공식 문서](https://cloud.google.com/vertex-ai)

## 사용 예시

### cURL
```bash
# 음성 채팅
curl -X POST "http://localhost:8000/api/chat/voice" \
  -F "audio=@test_audio.wav"

# 텍스트 채팅
curl -X POST "http://localhost:8000/api/chat/text" \
  -H "Content-Type: application/json" \
  -d '{"message": "오늘 너무 힘들어요"}'
```

### Python
```python
import requests

# 음성 채팅
with open("test_audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/chat/voice",
        files={"audio": f}
    )
    print(response.json())

# 텍스트 채팅
response = requests.post(
    "http://localhost:8000/api/chat/text",
    json={"message": "오늘 면접에서 떨어졌어요"}
)
print(response.json())
```

## 문제 해결

### 모델 다운로드 실패
- 인터넷 연결 확인
- 디스크 공간 확인 (최소 30GB 필요)
- Hugging Face 접근 가능 여부 확인

### 메모리 부족
- LLM 모델이 큽니다 (~28GB)
- GPU 메모리 부족 시 CPU 모드로 자동 전환
- 더 작은 모델 고려 (config.py에서 변경)

### 음성 인식 오류
- 오디오 형식 확인 (wav, mp3, flac 지원)
- 샘플링 레이트 16kHz 권장
- 최대 30초 제한

### 모바일 앱 연결 오류
- 백엔드 서버가 실행 중인지 확인
- `config.js`의 API_BASE_URL 확인
- 방화벽 설정 확인

## 라이선스

MIT License

## 기여

이슈와 Pull Request는 언제나 환영합니다!

## 📧 문의

프로젝트 관련 문의사항은 GitHub Issues를 통해 남겨주세요.
