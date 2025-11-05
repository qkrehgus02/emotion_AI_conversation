"""
LLM Service - Wrapper for EmpatheticLLM with Vertex AI Memory Bank integration
NO LOCAL MEMORY - All conversations stored in Vertex AI only
"""
from pathlib import Path
import sys
from typing import Optional, List, Dict

sys.path.append(str(Path(__file__).parent.parent))
from models.llm_model import EmpatheticLLM
from service.vertex_memory_service import VertexMemoryService
import config


class LLMService:
    """
    Service layer for LLM operations with Vertex AI Memory Bank integration

    NO LOCAL MEMORY - All conversation history managed by Vertex AI
    """

    def __init__(
        self,
        model_name: str = None,
        system_prompt: str = None,
        use_memory_bank: bool = None,
        **kwargs
    ):
        """
        Initialize LLM service

        Args:
            model_name: HuggingFace model name (default from config)
            system_prompt: System prompt (default from config)
            use_memory_bank: Enable Vertex AI Memory Bank (default from config)
            **kwargs: Additional parameters for EmpatheticLLM
        """
        # Check if fine-tuned model exists, otherwise use base model
        if config.LLM_MODEL_PATH.exists():
            model_name = str(config.LLM_MODEL_PATH)
            print(f"[LLMService] Using fine-tuned model from: {model_name}")
        else:
            model_name = model_name or config.LLM_MODEL_NAME
            print(f"[LLMService] Fine-tuned model not found, using base model: {model_name}")

        self.system_prompt = system_prompt or config.SYSTEM_PROMPT

        # Determine if Memory Bank should be used
        if use_memory_bank is None:
            use_memory_bank = config.MEMORY_BANK_ENABLED

        print(f"[LLMService] Memory Bank enabled: {use_memory_bank}")
        print(f"[LLMService] NO LOCAL MEMORY - Vertex AI only")

        # Initialize Vertex AI Memory Bank service
        self.memory_service = VertexMemoryService(
            project_id=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
            data_store_id=config.VERTEX_AI_AGENT_ENGINE_ID,
            enabled=use_memory_bank
        )

        # Initialize LLM (for response generation only, no storage)
        self.llm = EmpatheticLLM(
            model_name=model_name,
            system_prompt=self.system_prompt,
            max_new_tokens=kwargs.get('max_new_tokens', config.LLM_MAX_NEW_TOKENS),
            temperature=kwargs.get('temperature', config.LLM_TEMPERATURE),
            top_p=kwargs.get('top_p', config.LLM_TOP_P),
            top_k=kwargs.get('top_k', config.LLM_TOP_K),
            repetition_penalty=kwargs.get('repetition_penalty', config.LLM_REPETITION_PENALTY),
            no_repeat_ngram_size=kwargs.get('no_repeat_ngram_size', config.LLM_NO_REPEAT_NGRAM_SIZE)
        )

        print(f"[LLMService] ✓ LLM service initialized successfully")
        memory_status = self.memory_service.get_status()
        print(f"[LLMService] Memory Bank status: {memory_status}")

    def chat(
        self,
        message: str,
        conversation_id: str,
        emotion: str = None
    ) -> str:
        """
        Generate response for user message

        Process flow:
        1. Retrieve conversation history from Vertex AI
        2. Build prompt with system + history + current message
        3. Generate response with LLM (no local storage)
        4. Store user message + response in Vertex AI
        5. Return response

        Args:
            message: User's message
            conversation_id: Unique conversation ID
            emotion: Detected emotion (optional)

        Returns:
            Generated response
        """
        print(f"\n[LLMService] ========== Processing Chat ==========")
        print(f"[LLMService] User: {message[:50]}...")
        print(f"[LLMService] Conversation ID: {conversation_id}")
        print(f"[LLMService] Emotion: {emotion if emotion else 'None'}")

        # ========================================
        # STEP 1: Retrieve history from Vertex AI
        # ========================================

        conversation_history = []

        if self.memory_service.is_enabled():
            print(f"\n[LLMService] → Fetching history from Vertex AI...")

            conversation_history = self.memory_service.get_conversation_history(
                user_id=conversation_id,
                max_messages=10
            )

            if len(conversation_history) > 0:
                print(f"[LLMService] ✓ Loaded {len(conversation_history)} previous messages")
            else:
                print(f"[LLMService] ○ No previous conversation (first chat)")
        else:
            print(f"\n[LLMService] ! Memory Bank disabled, no history available")

        # ========================================
        # STEP 2: Build prompt messages
        # ========================================

        print(f"\n[LLMService] → Building prompt...")

        # Start with system prompt
        prompt_messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation history
        for msg in conversation_history:
            prompt_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message with emotion info
        if emotion:
            current_message = f"[감지된 감정: {emotion}] {message}"
        else:
            current_message = message

        prompt_messages.append({
            "role": "user",
            "content": current_message
        })

        print(f"[LLMService] ✓ Prompt built with {len(prompt_messages)} messages")
        print(f"[LLMService]   - System: 1")
        print(f"[LLMService]   - History: {len(conversation_history)}")
        print(f"[LLMService]   - Current: 1")

        # ========================================
        # STEP 3: Generate response (no storage)
        # ========================================

        print(f"\n[LLMService] → Generating response...")

        response = self.llm.generate_response(prompt_messages)

        print(f"[LLMService] ✓ Response: {response[:50]}...")

        # ========================================
        # STEP 4: Store in Vertex AI (NO local storage)
        # ========================================

        if self.memory_service.is_enabled():
            print(f"\n[LLMService] → Storing in Vertex AI...")

            # Store user message
            success_user = self.memory_service.add_message(
                user_id=conversation_id,
                message=message,
                role="user",
                emotion=emotion
            )

            # Store assistant response
            success_assistant = self.memory_service.add_message(
                user_id=conversation_id,
                message=response,
                role="assistant",
                emotion=None
            )

            if success_user and success_assistant:
                print(f"[LLMService] ✓✓ Both messages saved to Vertex AI")
            else:
                print(f"[LLMService] ✗ Warning: Failed to save some messages")
        else:
            print(f"\n[LLMService] ! Memory Bank disabled, messages NOT saved")
            print(f"[LLMService] ! WARNING: Conversations will NOT persist!")

        print(f"[LLMService] ========== Chat Complete ==========\n")

        return response

    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear conversation history

        Deletes conversation from Vertex AI (no local storage to clear)
        """
        print(f"[LLMService] Clearing conversation: {conversation_id}")

        if self.memory_service.is_enabled():
            self.memory_service.clear_user_memory(conversation_id)
            print(f"[LLMService] ✓ Conversation cleared from Vertex AI")
        else:
            print(f"[LLMService] ! Memory Bank disabled, nothing to clear")

    def get_conversation_history(self, conversation_id: str) -> list:
        """
        Get conversation history

        Returns history from Vertex AI (no local storage)
        """
        if self.memory_service.is_enabled():
            return self.memory_service.get_conversation_history(conversation_id)
        else:
            return []

    def get_memory_status(self) -> dict:
        """Get Memory Bank status"""
        return self.memory_service.get_status()
