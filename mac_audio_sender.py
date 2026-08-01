"""
mac_audio_sender.py - Stream macOS Audio over LAN to Sound Catcher on Windows.

Run this script on your Mac while on a call. It captures BlackHole 2ch audio
and streams raw PCM chunks over UDP directly to the Windows machine running Sound Catcher.
"""

import sys
import time
import socket
import argparse
import numpy as np
import sounddevice as sd

# Configuration defaults
DEFAULT_PORT = 50005
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SEC = 0.05  # 50 ms audio chunks (800 samples = 3,200 bytes)
MAX_PACKET_SIZE = 4096  # Max bytes per UDP datagram to comply with OS UDP MTU limits


def get_blackhole_device_id() -> int:
    """Finds the index of the BlackHole audio device on macOS."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if "blackhole" in dev.get("name", "").lower() and dev.get("max_input_channels", 0) > 0:
            return idx
    return -1


def main():
    parser = argparse.ArgumentParser(description="Stream macOS BlackHole Audio over LAN to Sound Catcher on Windows.")
    parser.add_argument("--ip", type=str, required=True, help="IP address of the Windows laptop (e.g., 192.168.1.50)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"UDP Port (Default: {DEFAULT_PORT})")
    parser.add_argument("--device", type=int, default=None, help="Audio input device ID (Auto-detects BlackHole if omitted)")
    args = parser.parse_args()

    win_ip = args.ip
    port = args.port

    device_id = args.device
    if device_id is None:
        device_id = get_blackhole_device_id()

    if device_id < 0:
        print("\n❌ Error: BlackHole 2ch audio device not found!")
        print("Please ensure BlackHole 2ch is installed via Homebrew (`brew install blackhole-2ch`)")
        print("Or pass an explicit device ID using `--device <ID>`.\n")
        print("Available input devices:")
        for idx, dev in enumerate(sd.query_devices()):
            if dev.get("max_input_channels", 0) > 0:
                print(f"  [{idx}] {dev.get('name')}")
        sys.exit(1)

    dev_info = sd.query_devices(device_id)
    dev_name = dev_info.get("name", f"ID {device_id}")

    print(f"==================================================")
    print(f"🎙️  macOS Remote Audio Streamer for Sound Catcher")
    print(f"==================================================")
    print(f"  - Source Audio Device:  {dev_name} (ID: {device_id})")
    print(f"  - Destination Windows:  {win_ip}:{port}")
    print(f"  - Sample Rate:          {SAMPLE_RATE} Hz")
    print(f"==================================================")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    block_size = int(SAMPLE_RATE * CHUNK_SEC)

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"[Warning] Audio status: {status}", file=sys.stderr)
        samples = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
        
        # Calculate audio energy meter
        rms = float(np.sqrt(np.mean(np.square(samples))))
        bars = int(min(1.0, rms * 10.0) * 20)
        meter = "█" * bars + "░" * (20 - bars)
        print(f"\r📡 Streaming Audio... [{meter}]", end="", flush=True)

        # Send raw float32 PCM bytes via UDP socket in safe packet sizes
        raw_bytes = samples.tobytes()
        for i in range(0, len(raw_bytes), MAX_PACKET_SIZE):
            chunk = raw_bytes[i : i + MAX_PACKET_SIZE]
            sock.sendto(chunk, (win_ip, port))

    try:
        with sd.InputStream(
            device=device_id,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            blocksize=block_size,
            dtype="float32",
            callback=audio_callback,
        ):
            print("\n🚀 Streaming started! Speak or play call audio on your Mac...")
            print("Press Ctrl+C to stop streaming.\n")
            while True:
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n🛑 Audio streaming stopped cleanly.")
    except Exception as e:
        print(f"\n❌ Error starting stream: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
