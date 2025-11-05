"""
Pydantic schemas for API request/response models
"""
from typing import List, Optional
from pydantic import BaseModel


class EmotionPrediction(BaseModel):
    """Emotion prediction result"""
    label: str
    probability: float


class ChatRequest(BaseModel):
    """Request model for text-based chat"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat"""
    response: str
    emotion: Optional[str] = None
    emotion_probability: Optional[float] = None
    conversation_id: str


class VoiceChatResponse(BaseModel):
    """Response model for voice-based chat"""
    transcribed_text: str
    detected_emotion: str
    emotion_probability: float
    emotion_top3: List[EmotionPrediction]
    llm_response: str
    conversation_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    models_loaded: dict
    memory_bank_status: Optional[dict] = None
