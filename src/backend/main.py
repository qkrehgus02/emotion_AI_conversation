"""
FastAPI Main Application
Empathetic Chatbot Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import services
from service.stt_service import STTService
from service.emotion_service import EmotionService
from service.llm_service import LLMService
from service.tts_service import TTSService

# Import controllers
from controller import chat_controller, history_controller

# Import database
from models.database import init_db

# Import config
import config


# Global service instances
stt_service = None
emotion_service = None
llm_service = None
tts_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    global stt_service, emotion_service, llm_service, tts_service

    print("\n" + "="*70)
    print("🚀 Empathetic Chatbot Backend Starting...")
    print("="*70)

    # Initialize database
    print("\n[0/4] Initializing database...")
    init_db()

    try:
        # Initialize STT service
        print("\n[1/4] Initializing STT service...")
        stt_service = STTService(
            model_name=config.WHISPER_MODEL_NAME,
            sample_rate=config.WHISPER_SAMPLE_RATE,
            max_duration=config.WHISPER_MAX_DURATION
        )

        # Initialize Emotion service
        print("\n[2/4] Initializing Emotion service...")
        emotion_service = EmotionService(
            model_path=config.EMOTION_MODEL_PATH,
            labels_path=config.EMOTION_LABELS_PATH,
            model_name=config.EMOTION_MODEL_NAME,
            sample_rate=config.WHISPER_SAMPLE_RATE,
            max_duration=config.WHISPER_MAX_DURATION
        )

        # Initialize LLM service
        print("\n[3/4] Initializing LLM service...")
        llm_service = LLMService()

        # Initialize TTS service
        print("\n[4/4] Initializing TTS service...")
        tts_service = TTSService(
            model_tag=config.TTS_MODEL_TAG,
            vocoder_tag=config.TTS_VOCODER_TAG
        )

        # Set services in controller
        chat_controller.set_services(stt_service, emotion_service, llm_service, tts_service)

        print("\n" + "="*70)
        print("✅ All services initialized successfully!")
        print("="*70)
        print(f"\n🌐 Server running at: http://{config.API_HOST}:{config.API_PORT}")
        print(f"📚 API docs: http://{config.API_HOST}:{config.API_PORT}/docs")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error during startup: {e}")
        raise

    yield

    # Shutdown
    print("\n🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Empathetic Chatbot API",
    description="Voice and text-based empathetic chatbot using Whisper, Emotion Recognition, and Qwen3 LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_controller.router)
app.include_router(history_controller.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Empathetic Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/chat/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.API_PORT,
        reload=False  # Set to True for development
    )
