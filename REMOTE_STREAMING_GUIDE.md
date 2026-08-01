# 🌐 Remote Audio Streaming Guide: macOS Call to Windows Sound Catcher

This guide explains step-by-step how to **hold your voice call on your Mac** while **capturing the call audio and processing live AI copilot suggestions on a separate Windows laptop**.

---

## 🏗️ Architecture & Flow

```
+---------------------------------------------------+        LAN / Wi-Fi (UDP Port 50005)        +---------------------------------------------------+
|                     MAC LAPTOP                    | -----------------------------------------> |                   WINDOWS LAPTOP                  |
|  (Call: Zoom / Meet / Teams / Slack / Discord)    |                                            |              (Running Sound Catcher)               |
|                                                   |                                            |                                                   |
| 1. System Call Audio                              |                                            | 1. Receives UDP Audio Packets                     |
| 2. Redirected to BlackHole 2ch                    |                                            | 2. Local Whisper STT Transcription (CPU/CUDA)     |
| 3. mac_audio_sender.py streams PCM over UDP       |                                            | 3. Google Gemini API Answers in Floating GUI      |
+---------------------------------------------------+                                            +---------------------------------------------------+
```

---

## 📋 Prerequisites

1. Both laptops connected to the **same Wi-Fi or Local Network (LAN)**.
2. **On macOS:** Python 3.10+, `sounddevice`, `numpy`, and `blackhole-2ch`.
3. **On Windows:** Sound Catcher project installed (`requirements.txt`) and a valid `GEMINI_API_KEY`.

---

## 🚀 Step-by-Step Setup Tutorial

### Step 1: Find the Windows Laptop IP Address

On your **Windows Laptop**:
1. Open Command Prompt (`cmd`) or PowerShell.
2. Type:
   ```cmd
   ipconfig
   ```
3. Look for **IPv4 Address** under your Wi-Fi or Ethernet adapter (e.g., `192.168.1.85` or `10.0.0.15`).

---

### Step 2: Configure macOS Audio Routing (Mac Laptop)

1. **Install BlackHole 2ch** (if not already installed):
   ```bash
   brew install blackhole-2ch
   ```
2. **Create Multi-Output Device:**
   - Open **Audio MIDI Setup** on Mac (`open -a "Audio MIDI Setup"`).
   - Click the **`+`** icon at the bottom-left -> **Create Multi-Output Device**.
   - Check the box for your **Headphones/Speakers** AND **BlackHole 2ch**.
   - Set **System Sound Output** to **Multi-Output Device** in System Settings -> Sound.

---

### Step 3: Start Sound Catcher on Windows

On your **Windows Laptop**:

1. Open Command Prompt / PowerShell in the project directory:
   ```cmd
   venv\Scripts\activate
   python main.py
   ```
2. In the Sound Catcher floating window, click the **Audio** dropdown menu at the top.
3. Select **`🌐 Network Stream (UDP Port 50005)`**.
   - *Status bar will display: "Listening for Network Stream on UDP Port 50005"*

> 💡 **Note on Windows Firewall:** If Windows Firewall prompts you when running `python main.py`, check **Private Networks** and click **Allow Access** to allow incoming UDP packets on port 50005.

---

### Step 4: Run the Audio Sender on Mac

On your **macOS Laptop**:

1. Open Terminal in the project directory.
2. Run the `mac_audio_sender.py` script, pointing to your Windows laptop's IP address:
   ```bash
   python3 mac_audio_sender.py --ip 192.168.1.85
   ```
   *(Replace `192.168.1.85` with your actual Windows IPv4 address found in Step 1)*.

3. You will see live audio streaming status in Terminal:
   ```text
   ==================================================
   🎙️  macOS Remote Audio Streamer for Sound Catcher
   ==================================================
     - Source Audio Device:  BlackHole 2ch (ID: 2)
     - Destination Windows:  192.168.1.85:50005
     - Sample Rate:          16000 Hz
   ==================================================

   🚀 Streaming started! Speak or play call audio on your Mac...
   📡 Streaming Audio... [████████████░░░░░░░░]
   ```

---

### Step 5: Test & Verify

1. Start your call (Zoom, Google Meet, Teams, etc.) or play a YouTube video on your Mac.
2. Notice the live audio signal progress bar moving on both:
   - Mac terminal screen (`mac_audio_sender.py`)
   - Windows Sound Catcher GUI top progress bar.
3. Sound Catcher on Windows will transcribe the speech and display Gemini AI bullet-point responses in real time!

---

## 🛠️ Alternative Method: Hardware Aux Cable (No Wi-Fi Needed)

If you don't want to stream audio over Wi-Fi:

1. Plug a **3.5mm Aux Audio Cable** from Mac Headphone Jack -> Windows **Mic / Line-In** Port (or a $5 USB Audio Capture Dongle on Windows).
2. On Mac: Set sound output to Headphones.
3. On Windows: Open Sound Catcher and select **Microphone / Line In / USB Audio** from the Audio dropdown.

---

## ❓ Troubleshooting

### 1. Audio meter on Windows is not moving
- Verify both laptops are on the same Wi-Fi network (or router).
- Test connectivity from Mac terminal: `ping <WINDOWS_IP>`.
- Ensure Windows Firewall isn't blocking UDP port 50005. You can temporarily test by disabling Windows Defender Firewall for Private Networks or adding an inbound rule for UDP port 50005.

### 2. Can't hear the call on Mac
- Ensure **Multi-Output Device** is selected as your System Output on Mac, and that **both** your headphones and BlackHole 2ch are checked in Audio MIDI Setup.
