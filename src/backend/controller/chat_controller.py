"""
Chat Controller - API endpoints for chat functionality
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
import uuid
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models.schemas import (
    ChatRequest,
    ChatResponse,
    VoiceChatResponse,
    HealthResponse,
    EmotionPrediction
)
from models.database import get_db, Conversation, Message
from sqlalchemy.orm import Session
from datetime import datetime
from service.stt_service import STTService
from service.emotion_service import EmotionService
from service.llm_service import LLMService
from service.tts_service import TTSService
import config


router = APIRouter(prefix="/api/chat", tags=["chat"])

# Global service instances (will be initialized in main.py)
stt_service: STTService = None
emotion_service: EmotionService = None
llm_service: LLMService = None
tts_service: TTSService = None


def set_services(stt: STTService, emotion: EmotionService, llm: LLMService, tts: TTSService):
    """Set service instances (called from main.py)"""
    global stt_service, emotion_service, llm_service, tts_service
    stt_service = stt
    emotion_service = emotion
    llm_service = llm
    tts_service = tts


@router.post("/voice", response_model=VoiceChatResponse)
async def chat_with_voice(
    audio: UploadFile = File(...),
    conversation_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Voice-based chat endpoint

    Process flow:
    1. Receive audio file
    2. Transcribe with Whisper (STT)
    3. Extract emotion from audio
    4. Generate empathetic response with LLM
    5. Return all results
    """
    if not all([stt_service, emotion_service, llm_service]):
        raise HTTPException(status_code=500, detail="Services not initialized")

    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Save uploaded file temporarily
    audio_path = config.UPLOAD_DIR / f"{uuid.uuid4()}_{audio.filename}"

    try:
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)

        # Step 1: Transcribe audio (STT)
        print(f"[API] Transcribing audio...")
        transcribed_text = stt_service.transcribe(audio_path)
        print(f"[API] Transcription: {transcribed_text}")

        # Step 2: Extract emotion
        print(f"[API] Analyzing emotion...")
        emotion_result = emotion_service.predict(audio_path, topk=3)
        detected_emotion = emotion_result["top_emotion"]
        emotion_probability = emotion_result["top_probability"]
        top_predictions = [
            EmotionPrediction(**pred)
            for pred in emotion_result["top_predictions"]
        ]
        print(f"[API] Detected emotion: {detected_emotion} ({emotion_probability:.3f})")

        # Step 3: Generate LLM response
        print(f"[API] Generating empathetic response...")
        llm_response = llm_service.chat(
            message=transcribed_text,
            conversation_id=conversation_id,
            emotion=detected_emotion
        )
        print(f"[API] Response: {llm_response}")

        # Step 4: Save to database
        try:
            # Check if conversation exists
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                # Create new conversation with title from first message
                conversation = Conversation(
                    id=conversation_id,
                    title=transcribed_text[:50] + ("..." if len(transcribed_text) > 50 else "")
                )
                db.add(conversation)

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=transcribed_text,
                emotion=detected_emotion,
                emotion_probability=emotion_probability
            )
            db.add(user_message)

            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=llm_response
            )
            db.add(assistant_message)

            db.commit()
            print(f"[API] Saved conversation to database")
        except Exception as e:
            print(f"[API] Error saving to database: {e}")
            db.rollback()

        return VoiceChatResponse(
            transcribed_text=transcribed_text,
            detected_emotion=detected_emotion,
            emotion_probability=emotion_probability,
            emotion_top3=top_predictions,
            llm_response=llm_response,
            conversation_id=conversation_id
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[API ERROR] Voice processing failed: {str(e)}")
        print(f"[API ERROR] Traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

    finally:
        # Clean up temporary file
        if audio_path.exists():
            audio_path.unlink()


@router.post("/text", response_model=ChatResponse)
async def chat_with_text(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Text-based chat endpoint

    Process flow:
    1. Receive text message
    2. Generate empathetic response with LLM (no emotion analysis)
    3. Save to database
    4. Return response
    """
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        # Generate LLM response
        print(f"[API] Text message: {request.message}")
        llm_response = llm_service.chat(
            message=request.message,
            conversation_id=conversation_id,
            emotion=None
        )
        print(f"[API] Response: {llm_response}")

        # Save to database
        try:
            # Check if conversation exists
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                # Create new conversation with title from first message
                conversation = Conversation(
                    id=conversation_id,
                    title=request.message[:50] + ("..." if len(request.message) > 50 else "")
                )
                db.add(conversation)

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=request.message
            )
            db.add(user_message)

            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=llm_response
            )
            db.add(assistant_message)

            db.commit()
            print(f"[API] Saved text conversation to database")
        except Exception as e:
            print(f"[API] Error saving to database: {e}")
            db.rollback()

        return ChatResponse(
            response=llm_response,
            emotion=None,
            emotion_probability=None,
            conversation_id=conversation_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.post("/tts")
async def text_to_speech(request: dict):
    """
    Text-to-Speech endpoint
    Convert text to speech audio file

    Args:
        request: JSON body with 'text' field

    Returns:
        Audio file (WAV format)
    """
    from fastapi.responses import FileResponse

    if not tts_service:
        raise HTTPException(status_code=500, detail="TTS service not initialized")

    # Extract text from request body
    text = request.get('text', '')
    if not text:
        raise HTTPException(status_code=422, detail="Missing 'text' field in request body")

    # Generate output path
    audio_filename = f"tts_{uuid.uuid4()}.wav"
    audio_path = config.UPLOAD_DIR / audio_filename

    try:
        # Generate speech
        print(f"[API] TTS request: {text[:50]}...")
        output_path = tts_service.synthesize(
            text=text,
            output_path=audio_path,
            speed=config.TTS_SPEED
        )

        # Return audio file
        return FileResponse(
            path=str(output_path),
            media_type="audio/wav",
            filename=audio_filename,
            headers={
                "Content-Disposition": f"attachment; filename={audio_filename}"
            }
        )

    except Exception as e:
        # Clean up on error
        if audio_path.exists():
            audio_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a given ID"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    try:
        llm_service.clear_conversation(conversation_id)
        return {"status": "success", "message": f"Conversation {conversation_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    models_loaded = {
        "stt": stt_service is not None,
        "emotion": emotion_service is not None,
        "llm": llm_service is not None,
        "tts": tts_service is not None
    }

    all_loaded = all(models_loaded.values())

    # Add Memory Bank status if LLM service is available
    memory_status = None
    if llm_service:
        memory_status = llm_service.get_memory_status()

    return HealthResponse(
        status="healthy" if all_loaded else "unhealthy",
        message="All services running" if all_loaded else "Some services not initialized",
        models_loaded=models_loaded,
        memory_bank_status=memory_status
    )


@router.get("/memory/status")
async def get_memory_status():
    """Get detailed Memory Bank status"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    try:
        status = llm_service.get_memory_status()
        return {
            "status": "success",
            "memory_bank": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting memory status: {str(e)}")
