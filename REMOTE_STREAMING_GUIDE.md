# 🌐 Remote Audio Streaming Guide: macOS Call to Windows Sound Catcher

This guide explains step-by-step how to **hold your voice call on your Mac** while **capturing the call audio and processing live AI copilot suggestions on a separate Windows laptop**.

---

## 🏗️ Architecture & Flow

```
+---------------------------------------------------+         LAN / Wi-Fi (TCP Port 50005)        +---------------------------------------------------+
|                     MAC LAPTOP                    | -----------------------------------------> |                   WINDOWS LAPTOP                  |
|  (Call: Zoom / Meet / Teams / Slack / Discord)    |                                            |              (Running Sound Catcher)               |
|                                                   |                                            |                                                   |
| 1. System Call Audio                              |                                            | 1. Accepts TCP Socket Stream                      |
| 2. Redirected to BlackHole 2ch                    |                                            | 2. Local Whisper STT Transcription (CPU/CUDA)     |
| 3. mac_audio_sender.py streams PCM over TCP       |                                            | 3. Google Gemini API Answers in Floating GUI      |
+---------------------------------------------------+                                            +---------------------------------------------------+
```

---

## 📋 Prerequisites

1. Both laptops connected to the **same Wi-Fi or Local Network (LAN)**.
2. **On macOS:** Python 3.10+, `sounddevice`, `numpy`, and `blackhole-2ch`.
3. **On Windows:** Sound Catcher project installed (`requirements.txt`) and a valid `GEMINI_API_KEY`.

---

## 🚀 Step-by-Step Setup Tutorial

### Step 1: Configure Windows Firewall (1-Click)

On your **Windows Laptop**:

1. Right-click **`setup_windows_firewall.bat`** in the project directory and select **Run as Administrator** (or run `setup_windows_firewall.ps1` in PowerShell as Admin).
2. This automatically configures Windows Defender Firewall rules for **Port 50005 TCP & UDP**.

---

### Step 2: Start Sound Catcher on Windows

On your **Windows Laptop**:

1. Open Command Prompt / PowerShell in the project directory:
   ```cmd
   venv\Scripts\activate
   python main.py
   ```
2. Sound Catcher automatically selects **`🌐 Network Stream (Port 50005)`** and starts listening on launch!
   - *Status bar will display: "Listening for Network Stream on Port 50005 (TCP & UDP)..."*
   - Click the **`📡 IP Info`** button next to the Audio dropdown to view your Windows IPv4 address (e.g. `192.168.100.108`).

---

### Step 3: Configure macOS Audio Routing (Mac Laptop)

1. **Install BlackHole 2ch** (if not already installed):
   ```bash
   brew install blackhole-2ch
   ```
2. **Create Multi-Output Device:**
   - Open **Audio MIDI Setup** on Mac (`open -a "Audio MIDI Setup"`).
   - Click the **`+`** icon at the bottom-left -> **Create Multi-Output Device**.
   - Check the box for your **Headphones/Speakers** AND **BlackHole 2ch**.
   - Set **System Sound Output** to **Multi-Output Device** in System Settings -> Sound.
   - *(Optional)* You can double-click **Multi-Output Device** in Audio MIDI Setup to rename it to any preferred display name.

---

### Step 4: Run the Audio Sender on Mac

On your **macOS Laptop**:

1. Open Terminal in the project directory.
2. **(Optional) Run a diagnostic connection test:**
   ```bash
   ./venv/bin/python3 mac_audio_sender.py --ip 192.168.100.108 --test
   ```
3. **Start live streaming:**
   ```bash
   ./venv/bin/python3 mac_audio_sender.py --ip 192.168.100.108
   ```
   *(Replace `192.168.100.108` with your actual Windows IPv4 address found in Step 2)*.

4. You will see live audio streaming status in Terminal:
   ```text
   ==================================================
   🎙️  macOS Remote Audio Streamer for Sound Catcher
   ==================================================
     - Source Audio Device:  BlackHole 2ch (ID: 2)
     - Destination Windows:  192.168.100.108:50005 (TCP)
     - Sample Rate:          16000 Hz
   ==================================================

   Connecting to Windows at 192.168.100.108:50005 over TCP...
   🟢 Connected to Sound Catcher on Windows!
   📡 Streaming Audio (TCP)... [████████████░░░░░░░░]
   ```

---

### Step 5: Test & Verify

1. Start your call (Zoom, Google Meet, Teams, etc.) or play a YouTube video on your Mac.
2. Notice the live audio signal progress bar moving on both:
   - Mac terminal screen (`mac_audio_sender.py`)
   - Windows Sound Catcher GUI top progress bar.
3. Sound Catcher on Windows will transcribe speech and display Gemini AI bullet-point responses in real time!

---

## 🛠️ Alternative Method: Hardware Aux Cable (No Wi-Fi Needed)

If you don't want to stream audio over Wi-Fi:

1. Plug a **3.5mm Aux Audio Cable** from Mac Headphone Jack -> Windows **Mic / Line-In** Port (or a USB Audio Capture Dongle on Windows).
2. On Mac: Set sound output to Headphones.
3. On Windows: Open Sound Catcher and select **Microphone / Line In / USB Audio** from the Audio dropdown.

---

## ❓ Troubleshooting

### 1. `[Errno 60] Operation timed out` on Mac
- **Cause:** Windows Defender Firewall is blocking incoming TCP connections on Port 50005.
- **Solution:** Right-click `setup_windows_firewall.bat` on Windows -> **Run as Administrator**.

### 2. `[Errno 61] Connection refused` on Mac
- **Cause:** Firewall is open, but Sound Catcher is not open on Windows or not listening.
- **Solution:** Make sure `python main.py` is running on Windows and the top dropdown is set to `🌐 Network Stream (Port 50005)`.

### 3. Can't hear call audio on Mac
- Ensure **Multi-Output Device** is selected as your System Output on Mac, and that **both** your headphones/speakers and BlackHole 2ch are checked in Audio MIDI Setup.
