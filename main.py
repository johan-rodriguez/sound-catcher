"""
Main Application Entrypoint for Sound Catcher.
Initializes QApplication, builds main window, and orchestrates worker threads
for audio capture, Speech-To-Text (STT) transcription, and AI Copilot (Gemini).
"""

import sys
import logging
import signal
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config import config
from src.audio_capture import AudioCaptureWorker
from src.transcriber import TranscriberWorker
from src.ai_assistant import AIAssistantWorker
from src.gui import MainWindow

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sound_catcher")


def main():
    """Main application startup function."""
    logger.info("Starting Sound Catcher - Real-time AI Call Copilot...")

    # 1. Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Sound Catcher")
    app.setOrganizationName("SoundCatcher")

    # Allow SIGINT (Ctrl+C) graceful exit
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    signal.signal(signal.SIGINT, lambda *args: app.quit())

    # 2. Initialize Main Window (GUI)
    window = MainWindow()

    # 3. Initialize Worker Threads
    audio_worker = AudioCaptureWorker()
    transcriber_worker = TranscriberWorker()
    ai_worker = AIAssistantWorker()

    # 4. Populate audio devices list in GUI
    available_devices = AudioCaptureWorker.get_available_input_devices()
    window.update_audio_devices(available_devices)

    # 5. Connect Qt Signals & Slots

    # --- Audio Capture -> Transcriber & GUI ---
    audio_worker.audio_chunk_ready.connect(transcriber_worker.add_audio_chunk)
    audio_worker.audio_level_changed.connect(window.update_audio_level)
    audio_worker.status_changed.connect(window.update_status)
    audio_worker.error_occurred.connect(window.show_error)

    # --- STT Transcriber -> AI Assistant & GUI ---
    transcriber_worker.transcription_updated.connect(window.append_transcription)
    transcriber_worker.question_detected.connect(ai_worker.request_suggestion)
    transcriber_worker.status_changed.connect(window.update_status)
    transcriber_worker.error_occurred.connect(window.show_error)

    # --- Gemini AI Assistant -> GUI ---
    ai_worker.ai_response_ready.connect(window.append_ai_suggestion)
    ai_worker.status_changed.connect(window.update_status)
    ai_worker.error_occurred.connect(window.show_error)

    # --- User Interaction GUI -> Workers ---
    window.device_selected.connect(audio_worker.set_device)

    # 6. Start Worker Threads
    transcriber_worker.start()
    ai_worker.start()
    audio_worker.start_capture()

    # 7. Clean Shutdown Handler
    def cleanup():
        logger.info("Closing application and freeing resources...")
        audio_worker.stop_capture()
        transcriber_worker.stop_transcriber()
        ai_worker.stop_assistant()

        audio_worker.wait(1000)
        transcriber_worker.wait(1000)
        ai_worker.wait(1000)
        logger.info("Resources released successfully.")

    app.aboutToQuit.connect(cleanup)

    # 8. Show Window & Run Qt Event Loop
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
