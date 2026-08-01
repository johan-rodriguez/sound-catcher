"""
Main configuration for Sound Catcher.
Manages environment variables, audio parameters, models, and AI prompts.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass
class AppConfig:
    """Global application configuration."""

    # API Key and AI Models
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # AI Copilot System Instruction Prompt
    system_prompt: str = (
        "You are a real-time interview and call copilot. Your job "
        "is to provide direct, professional, brief, and bullet-pointed answers "
        "so the user can skim them at a quick glance during the call. "
        "Avoid unnecessary introductions."
    )

    # Speech-To-Text (STT) Parameters
    stt_model_size: str = os.getenv("STT_MODEL_SIZE", "base")
    stt_language: Optional[str] = os.getenv("STT_LANGUAGE", None)  # None for auto-detection, or 'en', 'es'
    stt_device: str = os.getenv("STT_DEVICE", "cpu")  # 'cpu' or 'cuda'
    stt_compute_type: str = os.getenv("STT_COMPUTE_TYPE", "float32")  # 'float32', 'int8'

    # Audio Parameters
    sample_rate: int = 16000  # 16 kHz optimal for STT
    channels: int = 1  # Mono
    chunk_duration_sec: float = 0.5  # Audio chunk capture size in seconds
    default_device_keywords: tuple = (
        "BlackHole",
        "CABLE Output",
        "VB-Audio",
        "Stereo Mix",
        "Virtual Cable",
    )
    default_device_keyword: str = os.getenv("AUDIO_DEVICE_KEYWORD", "BlackHole")

    # Voice Activity Detection (VAD) & Silence Thresholds
    vad_silence_threshold: float = 0.015  # RMS energy threshold for silence
    vad_silence_duration_sec: float = 0.8  # Seconds of silence to finalize phrase

    def is_api_key_valid(self) -> bool:
        """Checks if the Gemini API Key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    def update_api_key(self, new_key: str) -> bool:
        """Saves the new API Key in memory and persists it to the .env file."""
        cleaned_key = new_key.strip()
        if not cleaned_key:
            return False

        self.gemini_api_key = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key

        # Save to .env file
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        lines = []
        found = False

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        lines.append(f"GEMINI_API_KEY={cleaned_key}\n")
                        found = True
                    else:
                        lines.append(line)

        if not found:
            lines.append(f"GEMINI_API_KEY={cleaned_key}\n")

        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        except Exception as e:
            print(f"Error writing to .env: {e}")
            return False


# Global config instance
config = AppConfig()
