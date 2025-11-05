"""
Audio preprocessing utilities
"""
import librosa
import numpy as np
from pathlib import Path
from typing import Union
import subprocess
import tempfile


def pad_or_trim(waveform: np.ndarray, target_length: int) -> np.ndarray:
    """
    Pad or trim waveform to the target length

    Args:
        waveform: Input waveform array
        target_length: Target length in samples

    Returns:
        Padded or trimmed waveform
    """
    if len(waveform) > target_length:
        return waveform[:target_length]
    return np.pad(waveform, (0, target_length - len(waveform)), "constant")


def convert_webm_to_wav(webm_path: Union[str, Path]) -> Path:
    """
    Convert WebM audio to WAV using FFmpeg

    Args:
        webm_path: Path to WebM file

    Returns:
        Path to converted WAV file
    """
    import shutil
    import os

    webm_path = Path(webm_path)
    wav_path = webm_path.with_suffix('.wav')

    # Find FFmpeg executable
    ffmpeg_cmd = shutil.which('ffmpeg')
    if ffmpeg_cmd is None:
        # Try conda environment path
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            ffmpeg_cmd = os.path.join(conda_prefix, 'bin', 'ffmpeg')
            if not os.path.exists(ffmpeg_cmd):
                ffmpeg_cmd = 'ffmpeg'
        else:
            ffmpeg_cmd = 'ffmpeg'

    try:
        # Use FFmpeg to convert WebM to WAV
        subprocess.run([
            ffmpeg_cmd, '-y', '-i', str(webm_path),
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            str(wav_path)
        ], check=True, capture_output=True, timeout=30)

        return wav_path
    except subprocess.CalledProcessError as e:
        print(f"[Error] FFmpeg conversion failed: {e.stderr.decode()}")
        raise
    except FileNotFoundError:
        print(f"[Error] FFmpeg not found at: {ffmpeg_cmd}")
        print(f"[Error] CONDA_PREFIX: {os.environ.get('CONDA_PREFIX')}")
        print(f"[Error] PATH: {os.environ.get('PATH')}")
        raise


def load_audio(
    audio_path: Union[str, Path],
    sample_rate: int = 16000,
    max_duration: int = 30
) -> np.ndarray:
    """
    Load audio file and resample to target sample rate
    Automatically converts WebM to WAV if needed

    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate (default: 16000 Hz for Whisper)
        max_duration: Maximum duration in seconds

    Returns:
        Waveform array
    """
    audio_path = Path(audio_path)

    # Convert WebM to WAV if needed
    if audio_path.suffix.lower() == '.webm':
        print(f"[Audio] Converting WebM to WAV: {audio_path.name}")
        try:
            wav_path = convert_webm_to_wav(audio_path)
            audio_path = wav_path
        except Exception as e:
            print(f"[Audio] WebM conversion failed: {e}")
            raise ValueError(f"Failed to convert WebM audio: {e}")

    # Load audio
    try:
        waveform, _ = librosa.load(str(audio_path), sr=sample_rate)
    except Exception as e:
        print(f"[Audio] Failed to load {audio_path}: {e}")
        raise

    # Trim or pad to max duration
    max_length = sample_rate * max_duration
    waveform = pad_or_trim(waveform, max_length)

    return waveform


def validate_audio_file(audio_path: Union[str, Path]) -> bool:
    """
    Validate if file is a valid audio file

    Args:
        audio_path: Path to audio file

    Returns:
        True if valid, False otherwise
    """
    path = Path(audio_path)

    if not path.exists():
        return False

    # Check file extension
    valid_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.webm']
    if path.suffix.lower() not in valid_extensions:
        return False

    # Try loading the file
    try:
        librosa.load(str(path), sr=None, duration=1)
        return True
    except Exception:
        return False


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """
    Get duration of audio file in seconds

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds
    """
    try:
        duration = librosa.get_duration(path=str(audio_path))
        return duration
    except Exception:
        return 0.0


def convert_audio_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    sample_rate: int = 16000
) -> bool:
    """
    Convert audio file to WAV format with target sample rate

    Args:
        input_path: Input audio file path
        output_path: Output WAV file path
        sample_rate: Target sample rate

    Returns:
        True if successful, False otherwise
    """
    try:
        import soundfile as sf

        waveform, _ = librosa.load(str(input_path), sr=sample_rate)
        sf.write(str(output_path), waveform, sample_rate)
        return True
    except Exception as e:
        print(f"[Error] Failed to convert audio: {e}")
        return False
