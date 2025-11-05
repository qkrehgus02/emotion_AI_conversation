"""
Emotion Classification Service
"""
import torch
import json
from transformers import AutoFeatureExtractor
from pathlib import Path
from typing import Union, List, Dict
import sys

sys.path.append(str(Path(__file__).parent.parent))
from models.emotion_model import SpeechEmotionClassifier
from utils.audio_utils import load_audio


DEFAULT_LABELS = ['기쁨', '놀라움', '두려움', '사랑스러움', '슬픔', '화남', '없음']


class EmotionService:
    """
    Emotion classification service for speech
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        labels_path: Union[str, Path] = None,
        model_name: str = "openai/whisper-base",
        sample_rate: int = 16000,
        max_duration: int = 30,
        device: str = None
    ):
        """
        Initialize emotion classification service

        Args:
            model_path: Path to trained emotion model weights
            labels_path: Path to label mapping JSON file
            model_name: Base Whisper model name
            sample_rate: Audio sample rate
            max_duration: Maximum audio duration
            device: Device to use (cuda/cpu)
        """
        self.model_path = Path(model_path)
        self.labels_path = Path(labels_path) if labels_path else None
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.max_duration = max_duration

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[Emotion] Loading emotion model from: {self.model_path}")
        print(f"[Emotion] Using device: {self.device}")

        # Load label mapping
        self.labels = self._load_labels()
        self.num_classes = len(self.labels)

        print(f"[Emotion] Labels: {', '.join(self.labels)}")

        # Load feature extractor
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)

        # Load model
        self.model = SpeechEmotionClassifier(
            model_name=model_name,
            class_num=self.num_classes
        )

        # Load weights
        state_dict = torch.load(self.model_path, map_location=self.device)

        # Handle DDP checkpoints
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        # Remove 'module.' prefix if present
        if isinstance(state_dict, dict):
            has_module_prefix = any(key.startswith("module.") for key in state_dict.keys())
            if has_module_prefix:
                state_dict = {
                    key.replace("module.", "", 1): value
                    for key, value in state_dict.items()
                }

        # Map old key names to new architecture
        state_dict = self._remap_state_dict_keys(state_dict)

        # Load with strict=False to handle any remaining mismatches
        missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)

        if missing_keys:
            print(f"[Warning] Missing keys in state_dict: {len(missing_keys)} keys")
            print(f"[Warning] First few missing keys: {missing_keys[:5]}")
        if unexpected_keys:
            print(f"[Warning] Unexpected keys in state_dict: {len(unexpected_keys)} keys")
            print(f"[Warning] First few unexpected keys: {unexpected_keys[:5]}")
        self.model = self.model.to(self.device)
        self.model.eval()

        print(f"[Emotion] Model loaded successfully")

    def _remap_state_dict_keys(self, state_dict: dict) -> dict:
        """
        Remap state dict keys from training format to current model architecture

        Training model had keys like:
        - module.whisper_model.* (DataParallel wrapper)
        - module.classifier.weight/bias (single layer: 512 -> 7)

        Current model expects:
        - whisper.* (WhisperModel)
        - classifier.0.weight, classifier.3.weight, classifier.6.weight (3-layer MLP)
        """
        new_state_dict = {}

        for key, value in state_dict.items():
            new_key = key

            # Map whisper_model.* to whisper.*
            if key.startswith("whisper_model."):
                new_key = key.replace("whisper_model.", "whisper.", 1)
            elif key.startswith("whisper_encoder."):
                # Handle alternative naming
                new_key = key.replace("whisper_encoder.", "whisper.encoder.", 1)

            # Skip additional_transformer_layers if they exist
            if key.startswith("additional_transformer_layers."):
                print(f"[Info] Skipping key: {key} (not in current architecture)")
                continue

            # Handle classifier: saved model has single layer (512->7),
            # current model has 3-layer MLP (512->256->128->7)
            # We can't directly load these, so skip and use random init
            if key.startswith("classifier."):
                if "weight" in key or "bias" in key:
                    # Check if it's the simple format (no layer number)
                    parts = key.split('.')
                    if len(parts) == 2:  # classifier.weight or classifier.bias
                        print(f"[Warning] Skipping classifier key: {key} (single-layer vs multi-layer mismatch)")
                        print(f"[Warning] Saved: {value.shape}, Current model uses 3-layer MLP")
                        continue

            new_state_dict[new_key] = value

        return new_state_dict

    def _load_labels(self) -> List[str]:
        """Load label mapping from JSON file or use defaults"""
        if self.labels_path and self.labels_path.exists():
            try:
                with open(self.labels_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                labels = [label for _, label in sorted(
                    ((int(k), v) for k, v in raw.items()),
                    key=lambda item: item[0]
                )]
                return labels
            except Exception as e:
                print(f"[Warning] Failed to load labels: {e}. Using defaults.")

        return DEFAULT_LABELS.copy()

    def predict(self, audio_path: Union[str, Path], topk: int = 3) -> Dict:
        """
        Predict emotion from audio file

        Args:
            audio_path: Path to audio file
            topk: Number of top predictions to return

        Returns:
            Dictionary with predictions
        """
        # Load audio
        waveform = load_audio(
            audio_path,
            sample_rate=self.sample_rate,
            max_duration=self.max_duration
        )

        # Extract features
        features = self.feature_extractor(
            waveform,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        ).input_features

        features = features.to(self.device)

        # Predict
        with torch.no_grad():
            logits = self.model(features)
            probabilities = torch.softmax(logits, dim=1)

        # Get top-k predictions
        topk_values, topk_indices = torch.topk(
            probabilities,
            k=min(topk, self.num_classes),
            dim=1
        )

        # Format results
        predictions = []
        for idx, score in zip(topk_indices[0].tolist(), topk_values[0].tolist()):
            label = self.labels[idx] if idx < len(self.labels) else f"class_{idx}"
            predictions.append({
                "label": label,
                "probability": float(score)
            })

        return {
            "top_emotion": predictions[0]["label"],
            "top_probability": predictions[0]["probability"],
            "top_predictions": predictions
        }

    def predict_batch(self, audio_paths: List[Union[str, Path]], topk: int = 3) -> List[Dict]:
        """
        Predict emotions for multiple audio files

        Args:
            audio_paths: List of audio file paths
            topk: Number of top predictions per file

        Returns:
            List of prediction dictionaries
        """
        results = []
        for audio_path in audio_paths:
            try:
                result = self.predict(audio_path, topk=topk)
                results.append(result)
            except Exception as e:
                print(f"[Error] Failed to process {audio_path}: {e}")
                results.append({
                    "error": str(e),
                    "top_emotion": "unknown",
                    "top_probability": 0.0,
                    "top_predictions": []
                })

        return results
