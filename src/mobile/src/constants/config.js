// API Configuration
export const API_BASE_URL = __DEV__
  ? 'http://localhost:8000' // Development: Local backend
  : 'https://your-production-backend.com'; // Production: update this

export const API_ENDPOINTS = {
  CHAT_VOICE: `${API_BASE_URL}/api/chat/voice`,
  CHAT_TEXT: `${API_BASE_URL}/api/chat/text`,
  CHAT_TTS: `${API_BASE_URL}/api/chat/tts`,
  HISTORY_CONVERSATIONS: `${API_BASE_URL}/api/history/conversations`,
  HISTORY_CONVERSATION: (id) => `${API_BASE_URL}/api/history/conversations/${id}`,
};

export const EMOTION_CONFIG = {
  EMOJI_MAP: {
    'happy': '😊',
    'sad': '😢',
    'angry': '😠',
    'fear': '😨',
    'surprise': '😮',
    'disgust': '🤢',
    'neutral': '😐',
    'calm': '😌'
  },
  MESSAGE_MAP: {
    'happy': '기분이 좋으시군요!',
    'sad': '힘든 일이 있으신가봐요...',
    'angry': '많이 화가 나셨나봐요',
    'fear': '걱정되시는 게 있으신가요?',
    'surprise': '놀라셨나봐요!',
    'disgust': '불편하셨나봐요',
    'neutral': '차분하시네요',
    'calm': '평온해 보이세요'
  }
};
