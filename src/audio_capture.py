"""
Real-time Audio Capture Module.
Uses sounddevice and numpy to continuously listen to system output/input audio stream.
"""

import logging
import time
import socket
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

    NETWORK_DEVICE_ID: int = -99
    UDP_PORT: int = 50005

    @staticmethod
    def get_available_input_devices() -> List[Tuple[int, str]]:
        """
        Returns a list of available input audio devices including Network Stream option.
        Format: [(device_index, device_name), ...]
        """
        devices = [(AudioCaptureWorker.NETWORK_DEVICE_ID, "🌐 Network Stream (UDP Port 50005)")]
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
    def find_default_device_id(keywords: Optional[Tuple[str, ...]] = None) -> Optional[int]:
        """
        Searches for the device ID matching specified keywords (e.g., BlackHole on macOS, CABLE Output on Windows).
        """
        if keywords is None:
            keywords = config.default_device_keywords

        devices = AudioCaptureWorker.get_available_input_devices()
        # First check explicit keyword if set via env
        env_keyword = config.default_device_keyword.lower()
        for idx, name in devices:
            if env_keyword in name.lower():
                return idx

        # Then check cross-platform fallback keywords
        for kw in keywords:
            for idx, name in devices:
                if kw.lower() in name.lower():
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

    def _run_network_stream(self) -> None:
        """UDP Socket listener for remote audio streaming (e.g. from macOS sender)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        try:
            sock.bind(("0.0.0.0", self.UDP_PORT))
            msg = f"Listening for Network Stream on UDP Port {self.UDP_PORT}..."
            logger.info(msg)
            print(f"\n[Network Receiver] {msg}")
            print(f"[Network Receiver] Make sure Windows Firewall allows UDP traffic on port {self.UDP_PORT}\n")
            self.status_changed.emit(msg)

            packet_count = 0
            first_packet_logged = False

            while self._is_running:
                try:
                    data, addr = sock.recvfrom(65536)
                    if not data or not self._is_running:
                        continue
                    samples = np.frombuffer(data, dtype=np.float32)
                    if len(samples) > 0:
                        packet_count += 1
                        if not first_packet_logged:
                            first_packet_logged = True
                            conn_msg = f"Connected! Receiving audio from Mac ({addr[0]}:{addr[1]})"
                            logger.info(conn_msg)
                            print(f"[Network Receiver] 📡 {conn_msg}")
                            self.status_changed.emit(f"Receiving audio from {addr[0]}")
                        elif packet_count % 100 == 0:
                            logger.debug(f"Received {packet_count} UDP audio packets from {addr[0]}")

                        rms = float(np.sqrt(np.mean(np.square(samples))))
                        normalized_level = min(1.0, rms * 10.0)
                        self.audio_level_changed.emit(normalized_level)
                        self.audio_chunk_ready.emit(samples)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"UDP Audio Recv Error: {e}")

        except Exception as e:
            error_msg = f"Error binding UDP port {self.UDP_PORT}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            sock.close()

    def run(self) -> None:
        """Main thread execution method."""
        self._is_running = True

        # Handle Network Audio Stream mode
        if self.device_id == self.NETWORK_DEVICE_ID:
            self._run_network_stream()
            return

        # If device_id not specified, search for virtual audio device (BlackHole, VB-Cable, etc.)
        if self.device_id is None:
            self.device_id = self.find_default_device_id()

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
