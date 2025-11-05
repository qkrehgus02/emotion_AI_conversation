"""
Speech-to-Text Service using Whisper
"""
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pathlib import Path
from typing import Union
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils.audio_utils import load_audio


class STTService:
    """
    Speech-to-Text service using OpenAI Whisper
    """

    def __init__(
        self,
        model_name: str = "openai/whisper-base",
        sample_rate: int = 16000,
        max_duration: int = 30,
        device: str = None
    ):
        """
        Initialize STT service

        Args:
            model_name: Whisper model name
            sample_rate: Audio sample rate
            max_duration: Maximum audio duration in seconds
            device: Device to use (cuda/cpu)
        """
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.max_duration = max_duration

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[STT] Loading Whisper model: {model_name}")
        print(f"[STT] Using device: {self.device}")

        # Load processor and model
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
        self.model = self.model.to(self.device)
        self.model.eval()

        # Force Korean language
        self.forced_decoder_ids = self.processor.get_decoder_prompt_ids(
            language="korean",
            task="transcribe"
        )

        print(f"[STT] Model loaded successfully")

    def transcribe(self, audio_path: Union[str, Path]) -> str:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        # Load and preprocess audio
        waveform = load_audio(
            audio_path,
            sample_rate=self.sample_rate,
            max_duration=self.max_duration
        )

        # Extract features
        input_features = self.processor(
            waveform,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        ).input_features

        input_features = input_features.to(self.device)

        # Generate transcription
        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                forced_decoder_ids=self.forced_decoder_ids
            )

        # Decode
        transcription = self.processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0]

        return transcription.strip()

    def transcribe_with_timestamps(self, audio_path: Union[str, Path]) -> dict:
        """
        Transcribe audio with word-level timestamps

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with text and timestamps
        """
        # Load and preprocess audio
        waveform = load_audio(
            audio_path,
            sample_rate=self.sample_rate,
            max_duration=self.max_duration
        )

        # Extract features
        input_features = self.processor(
            waveform,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        ).input_features

        input_features = input_features.to(self.device)

        # Generate with timestamps
        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                forced_decoder_ids=self.forced_decoder_ids,
                return_timestamps=True
            )

        # Decode
        transcription = self.processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0]

        return {
            "text": transcription.strip(),
            "timestamps": []  # Whisper timestamps require additional processing
        }
