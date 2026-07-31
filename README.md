# 🎙️ Sound Catcher - Real-Time Call Copilot for macOS

**Sound Catcher** is an intelligent desktop assistant built with Python and PySide6 for macOS. It intercepts system output audio in real time during voice calls or video conferences (Zoom, Google Meet, Microsoft Teams, Slack, etc.), automatically transcribes the caller's speech, detects when they ask a question, and leverages the **Google Gemini API** (`gemini-2.5-flash`) to present clear, professional bullet-pointed answers in an **Always on Top** floating window.

---

## 📋 System Requirements

- **Operating System:** macOS 12+ (Monterey, Ventura, Sonoma, Sequoia or newer).
- **Python:** version 3.10 or higher.
- **Package Manager:** Homebrew (`brew`).
- **Virtual Audio Device:** BlackHole 2ch (to capture system output audio from callers).
- **Google Gemini API Key:** Obtainable at [Google AI Studio](https://aistudio.google.com/).

---

## 🎧 Step 1: Audio Setup on macOS

For the application to "listen" to the caller's voice without muting your own speakers or headphones, you must configure a **Multi-Output Device** in macOS using **BlackHole**.

### 1.1 Install BlackHole 2ch via Homebrew

Open your Terminal and run:

```bash
brew install blackhole-2ch
```

### 1.2 Configure Multi-Output Device in Audio MIDI Setup

1. Open the system app **Audio MIDI Setup** (search in Spotlight or run in Terminal: `open -a "Audio MIDI Setup"`).
2. Click the **`+`** icon at the bottom-left corner and select **"Create Multi-Output Device"**.
3. In the right panel, check the boxes for:
   - Your primary listening device (e.g., *Built-in Speakers*, *Headphones*, or *AirPods*).
   - **BlackHole 2ch**.
4. Ensure your primary listening device is set as the **Master Device** to retain volume control.
5. Open macOS **System Settings** -> **Sound** -> **Output** and select your newly created **Multi-Output Device** as the default system output.

Now, any audio played during a call will be routed to your headphones/speakers **and** sent simultaneously to BlackHole 2ch for **Sound Catcher** to transcribe.

---

## 🚀 Step 2: Application Setup

### 2.1 Navigate to Project Directory

```bash
cd /Users/johan/Development/sound-catcher
```

### 2.2 Create & Activate Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Step 3: Configure Gemini API Key

Create a `.env` file in the root directory with your API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.5-flash
STT_MODEL_SIZE=base
```

*Note: You can also launch the app and click the **"🔑 Set API Key"** button on the top banner to paste your key directly through the GUI.*

---

## 🏃‍♂️ Step 4: Running the App

With the virtual environment activated, run:

```bash
python3 main.py
```

### Application Features:
1. In the **Audio** dropdown, select **BlackHole 2ch** (auto-selected if detected).
2. Speak or play call audio:
   - The top panel **🗣️ Live Transcription** displays real-time speech-to-text.
   - The bottom panel **✨ Gemini Suggestions** automatically generates bullet-pointed response notes when a question is detected.
3. Click **📋 Copy Last Response** to instantly copy answers to your clipboard.
4. The window floats on top of all applications for easy reading. Toggle **Always on Top** via the checkbox anytime.

---

## 🛠️ Project Structure

```
sound-catcher/
├── spec.md                # Technical specification
├── requirements.txt       # Python dependencies
├── config.py              # Global configuration & .env reader
├── main.py                # App entrypoint and Qt orchestrator
├── README.md              # Installation & setup guide
├── .env                   # Environment file for GEMINI_API_KEY
├── .env.example           # Environment template
└── src/
    ├── audio_capture.py   # Real-time audio stream worker (sounddevice + QThread)
    ├── transcriber.py     # Local Speech-To-Text worker (faster-whisper + VAD)
    ├── ai_assistant.py    # Google Gemini API integration (google-genai SDK)
    └── gui.py             # Modern PySide6 dark mode floating GUI
```

---

## ❓ Troubleshooting

### 1. Microphone / Audio Recording Permissions
If the audio meter shows no signal, ensure Terminal / Python has audio recording permissions under **System Settings** -> **Privacy & Security** -> **Microphone**.

### 2. Cannot Hear Call Audio
Verify that **Multi-Output Device** is selected in macOS Sound Settings, and that both your headphones/speakers and BlackHole 2ch are checked in Audio MIDI Setup.
