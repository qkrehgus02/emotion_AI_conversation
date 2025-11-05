"""
Speech Emotion Classification Model
Based on Whisper encoder + classification head
"""
import torch
import torch.nn as nn
from transformers import WhisperModel


class SpeechEmotionClassifier(nn.Module):
    """
    Speech emotion classifier using Whisper encoder as feature extractor
    """

    def __init__(self, model_name: str = "openai/whisper-base", class_num: int = 8):
        super().__init__()
        self.model_name = model_name
        self.class_num = class_num

        # Load pretrained Whisper model
        self.whisper = WhisperModel.from_pretrained(model_name)

        # Freeze Whisper encoder (optional - can be unfrozen for fine-tuning)
        for param in self.whisper.parameters():
            param.requires_grad = False

        # Get hidden size from Whisper config
        hidden_size = self.whisper.config.d_model

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, class_num)
        )

    def forward(self, input_features):
        """
        Forward pass

        Args:
            input_features: Whisper input features [batch_size, n_mels, seq_len]

        Returns:
            logits: Classification logits [batch_size, class_num]
        """
        # Extract features using Whisper encoder
        encoder_outputs = self.whisper.encoder(input_features)

        # Use mean pooling over sequence dimension
        # encoder_outputs.last_hidden_state: [batch_size, seq_len, hidden_size]
        pooled = torch.mean(encoder_outputs.last_hidden_state, dim=1)

        # Classification
        logits = self.classifier(pooled)

        return logits
