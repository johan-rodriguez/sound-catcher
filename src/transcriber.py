"""
Real-time Speech-To-Text (STT) Transcriber Module.
Uses `faster-whisper` in a worker thread to process audio chunks
and emit transcribed text alongside question detection signals.
"""

import logging
import queue
import re
import time
from typing import Optional, List
import numpy as np
from PySide6.QtCore import QThread, Signal

from config import config

logger = logging.getLogger(__name__)

# Keywords and patterns indicating a question or query in English or Spanish
QUESTION_INDICATORS = [
    r"\?",
    # English question starters & keywords
    r"\bwhat\b", r"\bhow\b", r"\bwhy\b", r"\bwhen\b", r"\bwhere\b", r"\bwho\b", r"\bwhich\b",
    r"\bcan you\b", r"\bcould you\b", r"\bwould you\b", r"\bplease explain\b", r"\btell me\b",
    r"\bdo you know\b", r"\bwhat is\b", r"\bwhat are\b", r"\bhow do\b", r"\bhow does\b",
    r"\badvantages\b", r"\bdisadvantages\b", r"\bdifference\b", r"\bopinion\b",
    # Spanish question starters & keywords
    r"\bqué\b", r"\bque\b", r"\bcómo\b", r"\bcomo\b", r"\bcuál\b", r"\bcual\b",
    r"\bpor qué\b", r"\bporque\b", r"\bcuándo\b", r"\bcuando\b", r"\bdónde\b", r"\bdonde\b",
    r"\bpuedes\b", r"\bpodrías\b", r"\bexplica\b", r"\bdime\b", r"\bcuéntame\b"
]


class TranscriberWorker(QThread):
    """
    STT worker thread powered by `faster-whisper`.
    Processes audio queue, performs Voice Activity Detection (VAD),
    and emits transcription & question detection signals.
    """

    # Qt Signals
    transcription_updated = Signal(str, bool)  # (text, is_final)
    question_detected = Signal(str)            # (detected_question)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self._audio_queue = queue.Queue()
        self._is_running = False
        self._model = None
        self._audio_buffer: List[np.ndarray] = []
        self._silence_duration = 0.0

    def add_audio_chunk(self, samples: np.ndarray) -> None:
        """Enqueues an audio chunk for processing."""
        if self._is_running:
            self._audio_queue.put(samples)

    def stop_transcriber(self) -> None:
        """Stops transcriber execution."""
        self._is_running = False
        self._audio_queue.put(None)  # Sentinel to unblock queue

    def run(self) -> None:
        """Loads STT model and continuously processes audio queue."""
        self._is_running = True

        # 1. Load `faster-whisper` model
        try:
            self.status_changed.emit(f"Loading transcription model ({config.stt_model_size})...")
            from faster_whisper import WhisperModel

            logger.info(f"Loading WhisperModel: size={config.stt_model_size}, device={config.stt_device}")
            self._model = WhisperModel(
                config.stt_model_size,
                device=config.stt_device,
                compute_type=config.stt_compute_type
            )
            self.status_changed.emit("Transcription ready. Listening for voice...")
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            error_msg = (
                f"Error loading transcription model `faster-whisper`: {e}.\n"
                "Please make sure `faster-whisper` is installed."
            )
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("Error loading STT.")
            self._is_running = False
            return

        # 2. Main transcription loop
        while self._is_running:
            try:
                chunk = self._audio_queue.get(timeout=0.2)
                if chunk is None:
                    break

                # Calculate RMS energy for VAD
                rms = float(np.sqrt(np.mean(np.square(chunk))))

                if rms < config.vad_silence_threshold:
                    self._silence_duration += config.chunk_duration_sec
                else:
                    self._silence_duration = 0.0
                    self._audio_buffer.append(chunk)

                # Process condition: prolonged silence OR buffer duration >= 6 sec
                buffer_duration = len(self._audio_buffer) * config.chunk_duration_sec

                should_process = (
                    (self._silence_duration >= config.vad_silence_duration_sec and len(self._audio_buffer) > 0)
                    or buffer_duration >= 6.0
                )

                if should_process and len(self._audio_buffer) > 0:
                    self._process_accumulated_audio()

            except queue.Empty:
                if len(self._audio_buffer) > 0 and self._silence_duration >= config.vad_silence_duration_sec:
                    self._process_accumulated_audio()

    def _process_accumulated_audio(self) -> None:
        """Concatenates accumulated audio buffer and runs Whisper transcription."""
        if not self._audio_buffer or self._model is None:
            return

        try:
            full_audio = np.concatenate(self._audio_buffer)
            self._audio_buffer.clear()
            self._silence_duration = 0.0

            # Skip if audio length is too short (< 0.4s)
            if len(full_audio) < config.sample_rate * 0.4:
                return

            segments, info = self._model.transcribe(
                full_audio,
                beam_size=3,
                language=config.stt_language,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            text_segments = []
            for segment in segments:
                cleaned = segment.text.strip()
                if cleaned:
                    text_segments.append(cleaned)

            if not text_segments:
                return

            full_text = " ".join(text_segments)

            # Filter common Whisper silence hallucinations
            if self._is_hallucination(full_text):
                logger.debug(f"Hallucination filtered: '{full_text}'")
                return

            logger.info(f"Transcription finished: '{full_text}'")
            self.transcription_updated.emit(full_text, True)

            # Evaluate if text contains a question or relevant query
            if self._is_question_or_request(full_text):
                logger.info(f"Question detected: '{full_text}'")
                self.question_detected.emit(full_text)

        except Exception as e:
            logger.error(f"Error during transcription process: {e}")
            self.error_occurred.emit(f"Transcription error: {e}")

    @staticmethod
    def _is_hallucination(text: str) -> bool:
        """Detects common ghost phrases produced by Whisper on silence."""
        lowered = text.lower().strip()
        hallucinations = [
            "thank you.", "thanks for watching.", "[blank_audio]",
            "subtitles by", "amara.org", "subscribe",
            "gracias.", "gracias por ver.", "subtítulos por", "bye."
        ]
        return any(h in lowered for h in hallucinations) or len(lowered) < 2

    @staticmethod
    def _is_question_or_request(text: str) -> bool:
        """Determines if transcribed text represents a question or prompt."""
        lowered = text.lower()
        if "?" in text:
            return True

        for pattern in QUESTION_INDICATORS:
            if re.search(pattern, lowered):
                return True

        words = text.split()
        if len(words) >= 6:
            return True

        return False
