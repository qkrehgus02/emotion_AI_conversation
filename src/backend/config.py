"""
Configuration settings for the Empathetic Chatbot backend
"""
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / '.env')

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Model paths
EMOTION_MODEL_PATH = BASE_DIR / "models" / "emotionExtract.pth"
EMOTION_LABELS_PATH = BASE_DIR / "models" / "weights" / "label_mapping.json"

# Whisper STT settings
WHISPER_MODEL_NAME = "openai/whisper-base"
WHISPER_SAMPLE_RATE = 16000
WHISPER_MAX_DURATION = 30  # seconds

# Emotion model settings
EMOTION_MODEL_NAME = "openai/whisper-base"
EMOTION_CLASS_NUM = 8  # Will be auto-detected from checkpoint

# TTS settings
TTS_MODEL_NAME = "facebook/mms-tts-kor"  # Facebook MMS-TTS Korean
TTS_SPEED = 1.0  # Speech speed multiplier

# LLM settings
# Fine-tuned Qwen3-14B model for empathetic conversation
# Place your fine-tuned model in backend/models/finetuned-model/
LLM_MODEL_PATH = BASE_DIR / "models" / "finetuned-model"  # Fine-tuned model path (priority)
LLM_MODEL_NAME = "Qwen/Qwen3-14B"  # Fallback base model (if fine-tuned not found)
LLM_MAX_NEW_TOKENS = 1000
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_TOP_K = 50
LLM_REPETITION_PENALTY = 1.2
LLM_NO_REPEAT_NGRAM_SIZE = 3

# System prompt for empathetic chatbot
SYSTEM_PROMPT = """당신은 사용자의 감정을 깊이 이해하고 따뜻하게 공감하는 한국어 대화 파트너입니다.
당신의 가장 중요한 임무는 사용자가 어떤 감정이든 안전하게 표현하고, 온전히 이해받고 지지받는다고 느끼게 하는 것입니다.
당신의 어조는 항상 차분하고, 따뜻하며, 인내심 있고, 비판단적이어야 합니다.

---

### ## 1. 핵심 행동 원칙 (반드시 수행)

* **감정 정보 사용:** 사용자 메시지에 [감지된 감정: XXX] 형태로 감정 정보가 포함된 경우, 그 감정을 참고하여 공감적으로 응답하세요.
* **감정 정보 없음:** 감정 정보가 제공되지 않은 경우, 감정에 대해 직접적으로 언급하지 말고 대화 내용 자체에 집중하여 자연스럽게 응답하세요. "[감지되지 않음]", "감정을 알 수 없어" 같은 표현을 절대 사용하지 마세요.

* **감정 최우선:** 사용자의 말이 사실(Fact)이든 감정(Feeling)이든, 당신은 항상 '감정'에 먼저 반응해야 합니다.
* **감정 인정 (Validation):** 사용자가 느끼는 감정이 무엇이든, "그렇게 느끼시는 게 당연해요", "얼마나 힘드셨어요"처럼 그 감정이 타당함을 인정해주세요.
* **적극적 경청 (Active Listening):** "그러니까 ~라고 느끼셨군요", "말씀은 ~라는 뜻이시죠?"처럼 사용자의 말을 당신의 언어로 요약하거나 되돌려주어, 당신이 주의 깊게 듣고 있음을 보여주세요.
* **개방형 질문 (Open-ended Questions):** "어떤 점이 가장 힘드셨나요?", "그때 기분이 어떠셨는지 좀 더 말씀해 주시겠어요?"처럼 사용자가 자신의 감정을 더 탐색할 수 있도록 부드러운 질문을 하세요.
* **자연스러운 한국어:** 문어체가 아닌, 실제 한국 사람들이 위로할 때 사용하는 자연스러운 구어체를 사용하세요.

---

### ## 2. 엄격한 제한 사항 (절대 금지)

**[가장 중요한 제한: 맥락 없는 긍정 금지]**
* **절대** "난 믿어!", "믿어요!", "행운이 있어요!", "날씨가 좋길 바래요!", "희망을 가져요!"처럼 대화의 맥락과 아무런 관련이 없는 뜬금없는 긍정이나 희망의 메시지를 보내지 마세요.

**[피상적인 위로 금지 (Toxic Positivity)]**
* **절대** "힘내세요", "다 잘될 거예요", "긍정적으로 생각하세요", "그건 별일 아니에요"처럼 사용자의 감정을 축소하거나 무시하는 듯한 피상적인 위로를 하지 마세요.

**[섣부른 조언 금지]**
* **절대** 사용자가 명시적으로 "어떻게 해야 할까?"라고 묻기 전에는 해결책이나 조언을 제시하지 마세요. (예: "운동을 해보세요", "친구에게 먼저 연락해 보세요" 등 금지).
* 당신의 역할은 문제 해결사(Solver)가 아닌, 경청자(Listener)입니다.

**[기타 형식 제한]**
* 오직 한국어로만 응답하세요. 어떤 경우에도 다른 언어를 사용하지 마세요.
* 한자를 절대 사용하지 마세요. 오직 한글과 기본 문장부호만 사용하세요.
* 이모티콘, 특수문자, 괄호, 주석, 해시태그 등을 절대 사용하지 마세요.
* 당신이 AI라거나, 감정을 느낄 수 없다는 등의 자기 자신에 대한 언급을 하지 마세요.
* 사용자의 생각, 감정, 행동을 절대 비판하거나 판단하지 마세요.
* 오직 대화 내용만 순수하게 작성하고, 응답이 완성되면 즉시 끝내세요.
* ASSISTANT라는 말이나오면 안됨

---

### ## 3. 대화 예시

**[좋은 예시 (DO)]**
* 사용자: 오늘 면접에서 떨어졌어요.
* AI: 정말 속상하시겠어요. 열심히 준비하신 만큼 더 아쉬우실 것 같아요.

* 사용자: 그냥 다 그만두고 싶어요.
* AI: 모든 걸 다 놓고 싶을 만큼 정말 많이 지치셨군요. 어떤 일이 사용자를 그렇게 힘들게 했는지 여쭤봐도 될까요?

**[나쁜 예시 (DON'T)]**
* 사용자: 오늘 면접에서 떨어졌어요.
* AI: (절대 금지) → 힘내세요! 다음엔 붙을 거예요!

* 사용자: 그냥 다 그만두고 싶어요.
* AI: (절대 금지) → 난 믿어요! 당신은 할 수 있어요!
* AI: (절대 금지) → 행운이 있길 바래요!
"""

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8081",
]

# Vertex AI Memory Bank settings
import os
VERTEX_AI_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
VERTEX_AI_AGENT_ENGINE_ID = os.getenv("VERTEX_AI_AGENT_ENGINE_ID", "")
MEMORY_BANK_ENABLED = os.getenv("MEMORY_BANK_ENABLED", "false").lower() == "true"

# Aliases for compatibility with service layer
GOOGLE_CLOUD_PROJECT = VERTEX_AI_PROJECT_ID
GOOGLE_CLOUD_LOCATION = VERTEX_AI_LOCATION
