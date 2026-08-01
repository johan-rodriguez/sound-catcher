"""
mac_audio_sender.py - Stream macOS Audio over LAN to Sound Catcher on Windows.

Run this script on your Mac while on a call. It captures BlackHole 2ch audio
and streams raw PCM chunks over TCP or UDP directly to the Windows machine running Sound Catcher.
"""

import sys
import time
import socket
import struct
import argparse
import numpy as np
import sounddevice as sd

# Configuration defaults
DEFAULT_PORT = 50005
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SEC = 0.05  # 50 ms audio chunks (800 samples = 3,200 bytes)


def get_blackhole_device_id() -> int:
    """Finds the index of the BlackHole audio device on macOS."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if "blackhole" in dev.get("name", "").lower() and dev.get("max_input_channels", 0) > 0:
            return idx
    return -1


def test_connectivity(win_ip: str, port: int, protocol: str = "tcp") -> bool:
    """Performs pre-flight connectivity test to Windows receiver."""
    print(f"\n🧪 Running Network Connectivity Test ({protocol.upper()})...")
    
    if protocol == "tcp":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect((win_ip, port))
            ping_payload = f"PING_HANDSHAKE:{socket.gethostname()}".encode("utf-8")
            header = struct.pack(">I", len(ping_payload))
            sock.sendall(header + ping_payload)
            print(f"  [✓] 🟢 Successfully connected over TCP to {win_ip}:{port}!")
            sock.close()
            return True
        except ConnectionRefusedError:
            print(f"  [❌] Connection Refused by {win_ip}:{port}")
            print("      -> Make sure Sound Catcher is open on Windows and set to '🌐 Network Stream'!")
            return False
        except socket.timeout:
            print(f"  [❌] Connection Timed Out to {win_ip}:{port}")
            print("      -> Windows Firewall is likely blocking incoming TCP port 50005, or IP is incorrect.")
            return False
        except Exception as e:
            print(f"  [❌] TCP Test Error: {e}")
            return False
        finally:
            sock.close()
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ping_payload = f"PING_HANDSHAKE:{socket.gethostname()}".encode("utf-8")
            for _ in range(3):
                sock.sendto(ping_payload, (win_ip, port))
                time.sleep(0.05)
            print(f"  [✓] Sent UDP Handshake Ping to {win_ip}:{port}")
            return True
        except Exception as e:
            print(f"  [❌] Error sending UDP packets: {e}")
            return False
        finally:
            sock.close()


def main():
    parser = argparse.ArgumentParser(description="Stream macOS BlackHole Audio over LAN to Sound Catcher on Windows.")
    parser.add_argument("--ip", type=str, required=True, help="IP address of the Windows laptop (e.g., 192.168.1.50)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port number (Default: {DEFAULT_PORT})")
    parser.add_argument("--protocol", type=str, choices=["tcp", "udp"], default="tcp", help="Streaming protocol: tcp (default) or udp")
    parser.add_argument("--device", type=int, default=None, help="Audio input device ID (Auto-detects BlackHole if omitted)")
    parser.add_argument("--test", action="store_true", help="Run connection diagnostic test only without streaming audio")
    args = parser.parse_args()

    win_ip = args.ip
    port = args.port
    protocol = args.protocol.lower()

    if args.test:
        test_connectivity(win_ip, port, protocol)
        sys.exit(0)

    # Run pre-flight test before streaming
    test_ok = test_connectivity(win_ip, port, protocol)
    if not test_ok and protocol == "tcp":
        print("\n⚠️ Pre-flight connection test failed! Please verify Windows IP & Firewall settings before streaming.")

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
    print(f"  - Destination Windows:  {win_ip}:{port} ({protocol.upper()})")
    print(f"  - Sample Rate:          {SAMPLE_RATE} Hz")
    print(f"==================================================")

    block_size = int(SAMPLE_RATE * CHUNK_SEC)

    if protocol == "tcp":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to Windows at {win_ip}:{port} over TCP...")
            sock.connect((win_ip, port))
            print("🟢 Connected to Sound Catcher on Windows!")
        except Exception as e:
            print(f"\n❌ Error connecting over TCP to {win_ip}:{port}: {e}")
            print("Make sure Sound Catcher is running on Windows and port 50005 is allowed in Firewall.")
            sys.exit(1)

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"[Warning] Audio status: {status}", file=sys.stderr)
            samples = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            
            rms = float(np.sqrt(np.mean(np.square(samples))))
            bars = int(min(1.0, rms * 10.0) * 20)
            meter = "█" * bars + "░" * (20 - bars)
            print(f"\r📡 Streaming Audio (TCP)... [{meter}]", end="", flush=True)

            raw_bytes = samples.tobytes()
            header = struct.pack(">I", len(raw_bytes))
            try:
                sock.sendall(header + raw_bytes)
            except Exception as err:
                print(f"\n❌ Socket send error: {err}", file=sys.stderr)

    else:  # UDP mode
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"[Warning] Audio status: {status}", file=sys.stderr)
            samples = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            
            rms = float(np.sqrt(np.mean(np.square(samples))))
            bars = int(min(1.0, rms * 10.0) * 20)
            meter = "█" * bars + "░" * (20 - bars)
            print(f"\r📡 Streaming Audio (UDP)... [{meter}]", end="", flush=True)

            raw_bytes = samples.tobytes()
            MAX_PACKET = 4096
            for i in range(0, len(raw_bytes), MAX_PACKET):
                chunk = raw_bytes[i : i + MAX_PACKET]
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
        print(f"\n❌ Error during audio capture: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
