"""
Vertex AI Conversation Memory Service
Uses Vertex AI Discovery Engine Conversational Search for persistent memory storage
"""
import os
from typing import List, Dict, Optional
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import NotFound


class VertexMemoryService:
    """
    Memory Bank service using Vertex AI Conversational Search
    Provides cloud-based persistent conversation memory

    NO LOCAL MEMORY - All conversations stored in Vertex AI only
    """

    def __init__(
        self,
        project_id: str,
        location: str = "global",
        data_store_id: str = None,
        enabled: bool = True
    ):
        """
        Initialize Vertex AI Memory Service

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud location (e.g., "global", "us-central1")
            data_store_id: Vertex AI Data Store ID
            enabled: Enable Memory Bank
        """
        self.enabled = enabled
        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id

        if not self.enabled:
            print("[VertexMemory] Memory Bank disabled")
            return

        if not data_store_id:
            print("[VertexMemory] No data_store_id provided, Memory Bank disabled")
            self.enabled = False
            return

        try:
            # Set up client options for the specific location
            client_options_instance = ClientOptions(
                api_endpoint=f"{location}-discoveryengine.googleapis.com"
            )

            # Initialize Conversational Search client
            self.client = discoveryengine.ConversationalSearchServiceClient(
                client_options=client_options_instance
            )

            # Build serving config path
            # Format: projects/{project}/locations/{location}/dataStores/{data_store}/servingConfigs/default_config
            self.serving_config = self.client.serving_config_path(
                project=project_id,
                location=location,
                data_store=data_store_id,
                serving_config="default_config"
            )

            print(f"[VertexMemory] ✓ Initialized successfully")
            print(f"[VertexMemory]   Project: {project_id}")
            print(f"[VertexMemory]   Location: {location}")
            print(f"[VertexMemory]   Data Store: {data_store_id}")
            print(f"[VertexMemory]   NO LOCAL MEMORY - Vertex AI only")

            self.vertex_available = True

        except Exception as e:
            print(f"[VertexMemory] ✗ Failed to initialize: {e}")
            self.enabled = False
            self.vertex_available = False

    def is_enabled(self) -> bool:
        """Check if Memory Bank is enabled"""
        return self.enabled

    def _get_conversation_name(self, user_id: str) -> str:
        """
        Build conversation resource name

        Format: projects/{project}/locations/{location}/dataStores/{data_store}/conversations/{conversation_id}
        """
        return self.client.conversation_path(
            project=self.project_id,
            location=self.location,
            data_store=self.data_store_id,
            conversation=user_id
        )

    def add_message(
        self,
        user_id: str,
        message: str,
        role: str,
        emotion: Optional[str] = None
    ) -> bool:
        """
        Add a message to Vertex AI conversation history

        This stores the message in Vertex AI's persistent storage.

        Args:
            user_id: Unique conversation/user identifier
            message: Message content
            role: Message role ("user" or "assistant")
            emotion: Detected emotion (optional)

        Returns:
            True if successfully stored, False otherwise
        """
        if not self.enabled:
            print(f"[VertexMemory] ! Memory Bank disabled, message not stored")
            return False

        try:
            # Prepare message content
            message_content = message
            if emotion:
                message_content = f"[감정: {emotion}] {message}"

            # Build conversation name
            conversation_name = self._get_conversation_name(user_id)

            # Create text input
            text_input = discoveryengine.TextInput(input=message_content)

            # Build converse conversation request
            request = discoveryengine.ConverseConversationRequest(
                name=conversation_name,
                query=text_input,
                serving_config=self.serving_config
            )

            # Call Vertex AI API to store message
            response = self.client.converse_conversation(request=request)

            print(f"[VertexMemory] ✓ Stored {role} message for user: {user_id}")

            return True

        except NotFound as e:
            # Conversation doesn't exist yet - this is normal for first message
            print(f"[VertexMemory] Creating new conversation for user: {user_id}")
            # Retry - the API will create it automatically
            try:
                request = discoveryengine.ConverseConversationRequest(
                    name=self._get_conversation_name(user_id),
                    query=discoveryengine.TextInput(input=message_content),
                    serving_config=self.serving_config
                )
                self.client.converse_conversation(request=request)
                print(f"[VertexMemory] ✓ Created conversation and stored message")
                return True
            except Exception as retry_error:
                print(f"[VertexMemory] ✗ Failed to create conversation: {retry_error}")
                return False

        except Exception as e:
            print(f"[VertexMemory] ✗ Error storing message: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_conversation_history(
        self,
        user_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Retrieve conversation history from Vertex AI

        Args:
            user_id: Unique conversation/user identifier
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with 'role' and 'content' keys
            Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        if not self.enabled:
            print(f"[VertexMemory] ! Memory Bank disabled, returning empty history")
            return []

        try:
            # Build conversation name
            conversation_name = self._get_conversation_name(user_id)

            # Get conversation
            request = discoveryengine.GetConversationRequest(
                name=conversation_name
            )

            conversation = self.client.get_conversation(request=request)

            messages = []

            # Extract messages from conversation
            if hasattr(conversation, 'messages') and conversation.messages:
                for msg in conversation.messages:
                    # User message
                    if hasattr(msg, 'user_input') and msg.user_input:
                        messages.append({
                            "role": "user",
                            "content": msg.user_input.input,
                            "timestamp": msg.create_time.isoformat() if hasattr(msg, 'create_time') else ""
                        })

                    # Assistant reply
                    if hasattr(msg, 'reply') and msg.reply and hasattr(msg.reply, 'summary') and msg.reply.summary:
                        messages.append({
                            "role": "assistant",
                            "content": msg.reply.summary.summary_text,
                            "timestamp": msg.create_time.isoformat() if hasattr(msg, 'create_time') else ""
                        })

            # Sort by timestamp (oldest to newest)
            messages.sort(key=lambda x: x.get("timestamp", ""))

            # Return most recent N messages
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

            print(f"[VertexMemory] ✓ Retrieved {len(recent_messages)} messages for user: {user_id}")

            return recent_messages

        except NotFound:
            # No conversation exists yet - this is normal for first chat
            print(f"[VertexMemory] ○ No conversation found for user: {user_id} (first chat)")
            return []

        except Exception as e:
            print(f"[VertexMemory] ✗ Error retrieving history: {e}")
            import traceback
            traceback.print_exc()
            return []

    def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all conversation memory for a user

        Args:
            user_id: Unique conversation/user identifier

        Returns:
            True if successfully cleared, False otherwise
        """
        if not self.enabled:
            print(f"[VertexMemory] ! Memory Bank disabled")
            return False

        try:
            conversation_name = self._get_conversation_name(user_id)

            # Delete conversation
            request = discoveryengine.DeleteConversationRequest(
                name=conversation_name
            )

            self.client.delete_conversation(request=request)

            print(f"[VertexMemory] ✓ Cleared all memory for user: {user_id}")
            return True

        except NotFound:
            print(f"[VertexMemory] ○ No conversation to delete for user: {user_id}")
            return True

        except Exception as e:
            print(f"[VertexMemory] ✗ Error clearing memory: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_status(self) -> dict:
        """Get Memory Bank status"""
        return {
            "enabled": self.enabled,
            "vertex_ai_available": getattr(self, 'vertex_available', False),
            "service": "Vertex AI Conversational Search",
            "project_id": self.project_id,
            "location": self.location,
            "data_store_id": self.data_store_id,
            "storage": "Vertex AI only (NO local memory)"
        }
