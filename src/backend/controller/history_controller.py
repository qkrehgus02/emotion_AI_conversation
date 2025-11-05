"""
Conversation History Controller - API endpoints for managing conversation history
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models.database import get_db, Conversation, Message
from pydantic import BaseModel


router = APIRouter(prefix="/api/history", tags=["history"])


# Pydantic models for API
class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    emotion: Optional[str] = None
    emotion_probability: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class CreateConversationRequest(BaseModel):
    conversation_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None


class AddMessageRequest(BaseModel):
    conversation_id: str
    role: str
    content: str
    emotion: Optional[str] = None
    emotion_probability: Optional[float] = None


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of conversations

    Args:
        user_id: Filter by user ID (optional)
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
    """
    query = db.query(Conversation)

    if user_id:
        query = query.filter(Conversation.user_id == user_id)

    conversations = query.order_by(desc(Conversation.updated_at)).offset(offset).limit(limit).all()

    # Add message count and last message for each conversation
    result = []
    for conv in conversations:
        message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        last_message_obj = db.query(Message).filter(Message.conversation_id == conv.id).order_by(desc(Message.created_at)).first()
        last_message = last_message_obj.content[:100] if last_message_obj else None

        result.append(ConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count,
            last_message=last_message
        ))

    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed conversation with all messages

    Args:
        conversation_id: Conversation ID
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.model_validate(msg) for msg in messages]
    )


@router.post("/conversations")
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation

    Args:
        request: Conversation creation request
    """
    # Check if conversation already exists
    existing = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    if existing:
        return {"status": "exists", "conversation_id": request.conversation_id}

    conversation = Conversation(
        id=request.conversation_id,
        user_id=request.user_id,
        title=request.title or "새 대화"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {"status": "created", "conversation_id": conversation.id}


@router.post("/messages")
async def add_message(
    request: AddMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Add a message to a conversation

    Args:
        request: Message addition request
    """
    # Check if conversation exists, create if not
    conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    if not conversation:
        conversation = Conversation(
            id=request.conversation_id,
            title="새 대화"
        )
        db.add(conversation)

    # Update conversation title from first user message if not set
    if not conversation.title or conversation.title == "새 대화":
        if request.role == "user":
            conversation.title = request.content[:50] + ("..." if len(request.content) > 50 else "")

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    # Create message
    message = Message(
        conversation_id=request.conversation_id,
        role=request.role,
        content=request.content,
        emotion=request.emotion,
        emotion_probability=request.emotion_probability
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "status": "success",
        "message_id": message.id,
        "conversation_id": message.conversation_id
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages

    Args:
        conversation_id: Conversation ID
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete all messages
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()

    # Delete conversation
    db.delete(conversation)
    db.commit()

    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get messages for a specific conversation

    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages
        offset: Number of messages to skip
    """
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).offset(offset).limit(limit).all()

    return [MessageResponse.model_validate(msg) for msg in messages]
