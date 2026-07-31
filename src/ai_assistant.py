"""
AI Assistant Module with Gemini.
Uses official `google-genai` SDK to evaluate transcribed questions and generate
fast, concise, bullet-pointed response suggestions for the user.
"""

import logging
import queue
from typing import Optional
from PySide6.QtCore import QThread, Signal

from config import config

logger = logging.getLogger(__name__)


class AIAssistantWorker(QThread):
    """
    Worker thread to process queries sent to the Google Gemini API.
    """

    # Qt Signals
    ai_response_ready = Signal(str, str)  # (original_question, markdown_answer)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self._request_queue = queue.Queue()
        self._is_running = False
        self._client = None

    def request_suggestion(self, question: str, full_context: Optional[str] = None) -> None:
        """Enqueues a new question for Gemini to process."""
        if self._is_running:
            self._request_queue.put((question, full_context))

    def stop_assistant(self) -> None:
        """Stops the assistant thread."""
        self._is_running = False
        self._request_queue.put(None)

    def _init_client(self) -> bool:
        """Initializes the official Gemini client (google-genai)."""
        if not config.is_api_key_valid():
            msg = "Missing environment variable `GEMINI_API_KEY`."
            logger.warning(msg)
            self.error_occurred.emit(msg)
            return False

        try:
            from google import genai

            logger.info(f"Initializing Gemini client with model {config.gemini_model}")
            self._client = genai.Client(api_key=config.gemini_api_key)
            return True
        except Exception as e:
            error_msg = f"Error initializing Gemini SDK (`google-genai`): {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def run(self) -> None:
        """AI assistant request processing loop."""
        self._is_running = True

        if not self._init_client():
            self.status_changed.emit("Waiting for Gemini API Key...")

        while self._is_running:
            try:
                item = self._request_queue.get(timeout=0.5)
                if item is None:
                    break

                question, context = item

                if self._client is None and not self._init_client():
                    continue

                self._process_question(question, context)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in AI assistant thread loop: {e}")

    def _process_question(self, question: str, context: Optional[str] = None) -> None:
        """Sends query to Gemini and emits response."""
        if self._client is None:
            return

        try:
            self.status_changed.emit("Gemini generating suggestion...")
            logger.info(f"Sending to Gemini: '{question}'")

            # Prompt construction
            prompt_content = f"Caller says: \"{question}\"\n\nGenerate key bullet-point response notes:"
            if context:
                prompt_content = f"Call context:\n{context}\n\n{prompt_content}"

            from google import genai
            from google.genai import types

            response = self._client.models.generate_content(
                model=config.gemini_model,
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=config.system_prompt,
                    temperature=0.3,
                    max_output_tokens=350,
                )
            )

            answer = response.text.strip() if response.text else "*(No response generated)*"
            logger.info("Gemini response received successfully.")
            self.status_changed.emit("Gemini suggestion ready.")
            self.ai_response_ready.emit(question, answer)

        except Exception as e:
            error_msg = f"Error querying Gemini API: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("Error in Gemini response.")
