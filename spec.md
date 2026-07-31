# PROMPT: Real-Time Call Assistant (AI Copilot) for macOS

Build a desktop software application for macOS that intercepts system output audio in real time during a call, transcribes it, detects when the caller asks a question, and uses the Google Gemini API to generate fast, concise answers in a floating window.

---

### Required Tech Stack
- **Operating System:** macOS (Must support output audio redirection).
- **Primary Language:** Python 3.10+
- **Audio Capture:** `soundcard` or `sounddevice` / `pyaudio` library configured to capture from virtual audio device (e.g., BlackHole).
- **Transcription (STT):** `faster-whisper` (local) or `google-cloud-speech` / real-time low-latency WebSocket transcription.
- **AI Engine:** Google Gemini API (`google-genai` SDK) using `gemini-2.5-flash` model for ultra-low latency responses.
- **Graphical Interface (GUI):** `PyQt6` or `PySide6` supporting "*Always on Top*" floating window and sleek dark mode style.

---

### Project Architecture & Data Flow

1. **Audio Module (`audio_capture.py`):**
   - Continuously listen to input stream from configured system audio device (e.g., BlackHole 2ch).
   - Maintain a low-latency continuous audio buffer.

2. **Transcription Module (`transcriber.py`):**
   - Process audio buffer blocks and convert them to text in real time.
   - Detect pauses/silence to determine when a complete sentence or question was finished.

3. **AI Assistant Module with Gemini (`ai_assistant.py`):**
   - Receive transcribed text.
   - Use Gemini API to evaluate if text corresponds to a question or prompt.
   - Configure Gemini System Instruction prompt:
     > *"You are a real-time interview and call copilot. Your job is to provide direct, professional, brief, and bullet-pointed answers so the user can skim them at a quick glance during the call. Avoid unnecessary introductions."*
   - Return generated Gemini response to the graphical interface.

4. **Graphical Interface (`gui.py`):**
   - Compact floating window, styled in sleek dark mode.
   - Retains `Qt.WindowStaysOnTopHint` property.
   - Displays two main sections:
     1. **Live Transcription** (What the caller is saying).
     2. **Gemini Suggestions** (Key bullet-point responses).
   - Includes a clear history button and visual audio level indicator.

---

### Code Structure Instructions

Generate the complete project structure with the following files:
1. `requirements.txt` (With all necessary libraries).
2. `README.md` (Step-by-step instructions to install BlackHole on macOS and configure Multi-Output device in 'Audio MIDI Setup').
3. `config.py` (Environment variables handling like `GEMINI_API_KEY` and audio parameters).
4. `src/audio_capture.py`
5. `src/transcriber.py`
6. `src/ai_assistant.py`
7. `src/gui.py`
8. `main.py` (Application entrypoint).

Ensure proper error handling for missing audio devices and missing API keys.