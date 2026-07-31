"""
Real-time Audio Capture Module.
Uses sounddevice and numpy to continuously listen to system output/input audio stream.
"""

import logging
import time
from typing import List, Tuple, Optional
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QThread, Signal

from config import config

logger = logging.getLogger(__name__)


class AudioCaptureWorker(QThread):
    """
    Worker thread responsible for capturing audio in real time.
    Emits Qt signals with captured audio blocks and RMS energy levels.
    """

    # Qt Signals
    audio_chunk_ready = Signal(np.ndarray)
    audio_level_changed = Signal(float)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, device_id: Optional[int] = None):
        super().__init__()
        self.device_id = device_id
        self._is_running = False
        self._stream: Optional[sd.InputStream] = None

    @staticmethod
    def get_available_input_devices() -> List[Tuple[int, str]]:
        """
        Returns a list of available input audio devices.
        Format: [(device_index, device_name), ...]
        """
        devices = []
        try:
            device_list = sd.query_devices()
            for idx, dev in enumerate(device_list):
                # Filter devices that support input channels
                if dev.get("max_input_channels", 0) > 0:
                    name = dev.get("name", f"Device {idx}")
                    devices.append((idx, name))
        except Exception as e:
            logger.error(f"Error listing audio devices: {e}")
        return devices

    @staticmethod
    def find_default_device_id(keyword: str = "BlackHole") -> Optional[int]:
        """
        Searches for the device ID matching the specified keyword (e.g., BlackHole).
        """
        devices = AudioCaptureWorker.get_available_input_devices()
        for idx, name in devices:
            if keyword.lower() in name.lower():
                return idx
        return None

    def set_device(self, device_id: Optional[int]) -> None:
        """Switches the audio capture device and restarts stream if running."""
        self.device_id = device_id
        if self._is_running:
            self.stop_capture()
            self.start_capture()

    def stop_capture(self) -> None:
        """Stops the audio capture loop."""
        self._is_running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Exception closing audio stream: {e}")
            self._stream = None
        self.status_changed.emit("Audio capture stopped.")

    def start_capture(self) -> None:
        """Starts audio capture on thread."""
        if not self.isRunning():
            self._is_running = True
            self.start()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
        """Callback executed by sounddevice for each processed audio block."""
        if status:
            logger.warning(f"Audio stream status: {status}")

        if not self._is_running:
            return

        # Convert to mono float32 numpy array
        samples = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()

        # Calculate Root Mean Square (RMS) level for visual meter
        rms = float(np.sqrt(np.mean(np.square(samples))))
        normalized_level = min(1.0, rms * 10.0)
        self.audio_level_changed.emit(normalized_level)

        # Emit audio chunk for transcriber module
        self.audio_chunk_ready.emit(samples)

    def run(self) -> None:
        """Main thread execution method."""
        self._is_running = True

        # If device_id not specified, search for BlackHole or fallback
        if self.device_id is None:
            self.device_id = self.find_default_device_id(config.default_device_keyword)

        device_name = "Default"
        if self.device_id is not None:
            try:
                info = sd.query_devices(self.device_id)
                device_name = info.get("name", f"ID {self.device_id}")
            except Exception:
                device_name = f"ID {self.device_id}"

        block_size = int(config.sample_rate * config.chunk_duration_sec)

        try:
            self.status_changed.emit(f"Listening on: {device_name}")
            logger.info(f"Starting audio capture on '{device_name}' (ID: {self.device_id})")

            self._stream = sd.InputStream(
                device=self.device_id,
                channels=config.channels,
                samplerate=config.sample_rate,
                blocksize=block_size,
                dtype="float32",
                callback=self._audio_callback,
            )

            with self._stream:
                while self._is_running:
                    self.msleep(100)

        except Exception as e:
            error_msg = f"Error opening audio device '{device_name}': {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("Error in audio capture.")
        finally:
            self._is_running = False
