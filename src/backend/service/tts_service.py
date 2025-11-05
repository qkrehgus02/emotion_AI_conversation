"""
Text-to-Speech Service using Facebook MMS-TTS
Converts text responses to speech audio with high-quality Korean TTS
"""
from pathlib import Path
from typing import Union
import torch
import soundfile as sf
import sys

sys.path.append(str(Path(__file__).parent.parent))


class TTSService:
    """
    Text-to-Speech service using Facebook MMS-TTS Korean model
    Provides high-quality Korean TTS
    """

    def __init__(
        self,
        model_tag: str = None,
        vocoder_tag: str = None,
        device: str = None
    ):
        """
        Initialize TTS service with Facebook MMS-TTS

        Args:
            model_tag: Not used (kept for compatibility)
            vocoder_tag: Not used (kept for compatibility)
            device: Device to use (cuda/cpu)
        """
        try:
            from transformers import VitsModel, VitsTokenizer
        except ImportError:
            raise ImportError(
                "Please install transformers: pip install transformers"
            )

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Use local model path
        model_path = str(Path(__file__).parent.parent / "models" / "tts_models" /
                        "models--facebook--mms-tts-kor" / "snapshots" /
                        "1b6491366d2ed6ea8e4e735607155d9f0110df29")

        print(f"[TTS] Initializing Facebook MMS-TTS Korean")
        print(f"[TTS] Model path: {model_path}")
        print(f"[TTS] Device: {self.device}")

        try:
            # Load tokenizer and model from local path
            # Note: VitsTokenizer for Korean needs uroman for romanization
            self.tokenizer = VitsTokenizer.from_pretrained(model_path)
            self.model = VitsModel.from_pretrained(model_path).to(self.device)

            # Check if uroman is available
            try:
                import uroman as ur
                self.uroman_available = True
                print(f"[TTS] uroman romanizer is available")
            except ImportError:
                self.uroman_available = False
                print(f"[TTS] Warning: uroman not available. Install with: pip install uroman")

            print(f"[TTS] MMS-TTS initialized successfully")

        except Exception as e:
            print(f"[TTS] Failed to load MMS-TTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        speed: float = 1.0
    ) -> Path:
        """
        Synthesize speech from text using Facebook MMS-TTS

        Args:
            text: Text to synthesize (Korean)
            output_path: Output audio file path (.wav)
            speed: Speech speed multiplier (default: 1.0)

        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)

        # Validate input text
        if not text or not text.strip():
            raise ValueError("Input text is empty or contains only whitespace")

        text = text.strip()

        # Ensure output path has .wav extension
        if output_path.suffix.lower() != '.wav':
            output_path = output_path.with_suffix('.wav')

        try:
            print(f"[TTS] Synthesizing text (length={len(text)}): {text[:50]}...")

            # Tokenize input text with uroman preprocessing for Korean
            # The tokenizer should automatically apply uroman if available
            inputs = self.tokenizer(text, return_tensors="pt", add_special_tokens=True).to(self.device)

            # Check if tokenization produced valid input
            if inputs.input_ids.size(1) == 0:
                print(f"[TTS] Warning: Tokenization produced empty input")
                print(f"[TTS] Input text: {text}")
                print(f"[TTS] input_ids shape: {inputs.input_ids.shape}")
                raise ValueError(f"Tokenization resulted in empty input for text: {text}")

            # Generate speech
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Extract waveform
            waveform = outputs.waveform[0].cpu().numpy()

            # MMS-TTS uses 16kHz sample rate
            sample_rate = self.model.config.sampling_rate

            # Apply speed adjustment if needed
            if speed != 1.0:
                import scipy.signal as signal
                # Resample to adjust speed
                num_samples = int(len(waveform) / speed)
                waveform = signal.resample(waveform, num_samples)

            # Write to file
            sf.write(
                str(output_path),
                waveform,
                sample_rate,
                subtype='PCM_16'
            )

            print(f"[TTS] Generated audio: {output_path}")
            return output_path

        except Exception as e:
            print(f"[TTS] Error during synthesis: {e}")
            raise

    def batch_synthesize(
        self,
        texts: list,
        output_dir: Union[str, Path],
        speed: float = 1.0
    ) -> list:
        """
        Synthesize multiple texts to audio files

        Args:
            texts: List of texts to synthesize
            output_dir: Output directory
            speed: Speech speed multiplier

        Returns:
            List of output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []

        for idx, text in enumerate(texts):
            output_path = output_dir / f"tts_output_{idx:03d}.wav"
            try:
                path = self.synthesize(text, output_path, speed)
                output_paths.append(path)
            except Exception as e:
                print(f"[TTS] Failed to synthesize text {idx}: {e}")
                output_paths.append(None)

        return output_paths


# Simplified TTS Service (fallback option)
class SimpleTTSService:
    """
    Simplified TTS using gTTS as fallback
    Use when ESPnet2 is not available or for quick testing
    """

    def __init__(self, language: str = "ko"):
        """
        Initialize simple TTS with gTTS

        Args:
            language: Language code (default: Korean)
        """
        try:
            from gtts import gTTS
            self.gTTS = gTTS
            self.language = language
            print(f"[TTS] Simple TTS (gTTS) initialized")
        except ImportError:
            raise ImportError("Please install gTTS: pip install gtts")

    def synthesize(
        self,
        text: str,
        output_path: Union[str, Path],
        speed: float = 1.0
    ) -> Path:
        """
        Convert text to speech using gTTS

        Args:
            text: Text to convert
            output_path: Output file path (.mp3)
            speed: Speech speed (slow=True if < 1.0)

        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)

        # Generate speech
        tts = self.gTTS(text=text, lang=self.language, slow=(speed < 1.0))
        tts.save(str(output_path))

        print(f"[TTS] Generated audio (gTTS): {output_path}")
        return output_path
