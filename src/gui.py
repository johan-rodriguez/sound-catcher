"""
Modern PySide6 GUI for Sound Catcher.
Minimalist dark theme with Always-on-Top floating window support,
audio level meter, live transcription, and Gemini Markdown suggestions.
"""

import datetime
import logging
from typing import List, Tuple, Optional
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QCheckBox, QProgressBar, QTextBrowser,
    QTextEdit, QSplitter, QFrame, QMessageBox, QApplication, QStyle, QInputDialog
)

from config import config

logger = logging.getLogger(__name__)

# Premium Dark Mode QSS Stylesheet
DARK_THEME_QSS = """
QMainWindow {
    background-color: #12131C;
    color: #E0E2EC;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #C5C6D0;
}

QFrame.card {
    background-color: #1B1C28;
    border: 1px solid #2B2C3D;
    border-radius: 10px;
    padding: 8px;
}

QLabel.header-title {
    font-size: 15px;
    font-weight: bold;
    color: #8EACCD;
}

QLabel.panel-title {
    font-size: 13px;
    font-weight: 600;
    color: #D6E3FF;
    padding-bottom: 4px;
}

QComboBox {
    background-color: #262738;
    border: 1px solid #3B3C54;
    border-radius: 6px;
    padding: 4px 8px;
    color: #E0E2EC;
}

QComboBox::drop-down {
    border: 0px;
}

QPushButton {
    background-color: #2B2C3D;
    border: 1px solid #3F4056;
    border-radius: 6px;
    padding: 5px 12px;
    color: #E0E2EC;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3B3C54;
    border-color: #585A78;
}

QPushButton:pressed {
    background-color: #1F2030;
}

QPushButton.primary {
    background-color: #005AC1;
    color: #FFFFFF;
    border: none;
}

QPushButton.primary:hover {
    background-color: #0066DC;
}

QCheckBox {
    color: #C5C6D0;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #585A78;
    background-color: #262738;
}

QCheckBox::indicator:checked {
    background-color: #4C8EFF;
    border-color: #4C8EFF;
}

QProgressBar {
    background-color: #262738;
    border: 1px solid #3B3C54;
    border-radius: 4px;
    text-align: center;
    height: 8px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4C8EFF, stop:1 #80B5FF);
    border-radius: 3px;
}

QTextEdit, QTextBrowser {
    background-color: #151622;
    border: 1px solid #28293B;
    border-radius: 8px;
    padding: 8px;
    color: #E0E2EC;
    selection-background-color: #00458E;
}

QSplitter::handle {
    background-color: #2B2C3D;
    height: 2px;
}

QStatusBar {
    background-color: #12131C;
    color: #8C8E9E;
    border-top: 1px solid #232433;
}
"""


class MainWindow(QMainWindow):
    """
    Main application window for Sound Catcher.
    """

    # Signals emitted from GUI to background workers
    device_selected = Signal(int)
    clear_history_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sound Catcher - AI Call Copilot")
        self.resize(850, 650)
        self.setMinimumSize(600, 450)

        # Apply dark stylesheet
        self.setStyleSheet(DARK_THEME_QSS)

        # Initialize visual components
        self._init_ui()

        # Always-on-Top floating window by default
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

    def _init_ui(self) -> None:
        """Constructs all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Top Control Header Bar
        control_card = QFrame()
        control_card.setProperty("class", "card")
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(10, 6, 10, 6)

        # Title Brand
        title_label = QLabel("🎙️ Sound Catcher")
        title_label.setProperty("class", "header-title")
        control_layout.addWidget(title_label)

        control_layout.addSpacing(10)

        # Audio Device Selector
        dev_label = QLabel("Audio:")
        control_layout.addWidget(dev_label)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        control_layout.addWidget(self.device_combo)

        # Network Info / Diagnostics Button
        self.net_info_btn = QPushButton("📡 IP Info")
        self.net_info_btn.setToolTip("Show Windows IP address & Mac connection test helper")
        self.net_info_btn.clicked.connect(self._show_network_diagnostics)
        control_layout.addWidget(self.net_info_btn)

        # RMS Audio Level Meter
        self.audio_meter = QProgressBar()
        self.audio_meter.setRange(0, 100)
        self.audio_meter.setValue(0)
        self.audio_meter.setTextVisible(False)
        self.audio_meter.setFixedWidth(70)
        self.audio_meter.setToolTip("Captured audio signal strength")
        control_layout.addWidget(self.audio_meter)

        control_layout.addStretch()

        # "Always on Top" Checkbox
        self.always_top_checkbox = QCheckBox("Always on Top")
        self.always_top_checkbox.setChecked(True)
        self.always_top_checkbox.toggled.connect(self._set_always_on_top)
        control_layout.addWidget(self.always_top_checkbox)

        # Clear History Button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setToolTip("Clear transcription and AI suggestions history")
        self.clear_btn.clicked.connect(self._clear_history)
        control_layout.addWidget(self.clear_btn)

        main_layout.addWidget(control_card)

        # API Key Status & Alert Banner
        self.alert_banner = QFrame()
        self.alert_banner.setStyleSheet(
            "QFrame { background-color: #3D2914; border: 1px solid #7F4D18; border-radius: 6px; padding: 4px; }"
            "QLabel { color: #FFDCC3; font-weight: 500; }"
        )
        alert_layout = QHBoxLayout(self.alert_banner)
        alert_layout.setContentsMargins(10, 4, 10, 4)
        self.alert_label = QLabel("⚠️ `GEMINI_API_KEY` is not set. Set it in `.env` file or click:")
        alert_layout.addWidget(self.alert_label)

        self.key_btn = QPushButton("🔑 Set API Key")
        self.key_btn.setFixedSize(130, 26)
        self.key_btn.setStyleSheet("QPushButton { background-color: #7F4D18; color: #FFFFFF; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #9C5F1F; }")
        self.key_btn.clicked.connect(self._prompt_api_key)
        alert_layout.addWidget(self.key_btn)

        self.alert_banner.setVisible(not config.is_api_key_valid())
        main_layout.addWidget(self.alert_banner)

        # 2. Main Splitter (Transcription & AI Suggestions)
        splitter = QSplitter(Qt.Vertical)

        # Top Panel: Live Transcription
        transcript_card = QFrame()
        transcript_card.setProperty("class", "card")
        transcript_layout = QVBoxLayout(transcript_card)
        transcript_layout.setContentsMargins(8, 8, 8, 8)

        t_title = QLabel("🗣️ Live Transcription (Caller)")
        t_title.setProperty("class", "panel-title")
        transcript_layout.addWidget(t_title)

        self.transcript_area = QTextEdit()
        self.transcript_area.setReadOnly(True)
        self.transcript_area.setPlaceholderText("Listening for call audio...")
        transcript_layout.addWidget(self.transcript_area)

        splitter.addWidget(transcript_card)

        # Bottom Panel: Gemini AI Suggestions
        suggestions_card = QFrame()
        suggestions_card.setProperty("class", "card")
        suggestions_layout = QVBoxLayout(suggestions_card)
        suggestions_layout.setContentsMargins(8, 8, 8, 8)

        s_header_layout = QHBoxLayout()
        s_title = QLabel("✨ Gemini Suggestions (Key Bullet Points)")
        s_title.setProperty("class", "panel-title")
        s_header_layout.addWidget(s_title)
        s_header_layout.addStretch()

        self.copy_btn = QPushButton("📋 Copy Last Response")
        self.copy_btn.setFixedHeight(24)
        self.copy_btn.clicked.connect(self._copy_last_suggestion)
        s_header_layout.addWidget(self.copy_btn)

        suggestions_layout.addLayout(s_header_layout)

        self.suggestions_area = QTextBrowser()
        self.suggestions_area.setOpenExternalLinks(True)
        self.suggestions_area.setPlaceholderText("Automatic AI response bullet points will appear here...")
        suggestions_layout.addWidget(self.suggestions_area)

        splitter.addWidget(suggestions_card)

        # Initial splitter ratio (40% transcript, 60% suggestions)
        splitter.setSizes([220, 330])
        main_layout.addWidget(splitter, stretch=1)

        # 3. Bottom Status Bar
        self.statusBar().showMessage("Initializing application...")
        self.last_ai_suggestion = ""

    # --- UI Update Slots ---

    @Slot(list)
    def update_audio_devices(self, devices: List[Tuple[int, str]]) -> None:
        """Populates the Audio Device ComboBox."""
        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        selected_idx = 0
        for i, (dev_id, dev_name) in enumerate(devices):
            self.device_combo.addItem(dev_name, dev_id)
            if config.default_device_keyword.lower() in dev_name.lower():
                selected_idx = i

        if devices:
            self.device_combo.setCurrentIndex(selected_idx)

        self.device_combo.blockSignals(False)

    @Slot(float)
    def update_audio_level(self, level: float) -> None:
        """Updates RMS volume meter progress bar (0.0 to 1.0)."""
        val = int(level * 100)
        self.audio_meter.setValue(val)

    @Slot(str, bool)
    def append_transcription(self, text: str, is_final: bool) -> None:
        """Appends new timestamped transcription text to top panel."""
        if not text.strip():
            return

        now = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"<div style='margin-bottom: 6px;'><span style='color: #797B8E; font-size: 11px;'>[{now}]</span> <b>Caller:</b> {text}</div>"

        self.transcript_area.append(formatted)

        sb = self.transcript_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str, str)
    def append_ai_suggestion(self, question: str, markdown_answer: str) -> None:
        """Appends Gemini response suggestion to bottom panel."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_ai_suggestion = markdown_answer

        html_body = self._markdown_to_html(markdown_answer)

        formatted = (
            f"<div style='background-color: #1E2030; border-left: 4px solid #4C8EFF; "
            f"border-radius: 6px; padding: 10px; margin-bottom: 12px;'>"
            f"<div style='color: #82A5FF; font-size: 11px; font-weight: bold;'>[{now}] 💡 DETECTED QUESTION:</div>"
            f"<div style='color: #E0E2EC; font-style: italic; margin-bottom: 8px;'>\"{question}\"</div>"
            f"<hr style='border: 0; border-top: 1px solid #2B2C3D; margin: 6px 0;'>"
            f"<div style='color: #F0F2FC;'>{html_body}</div>"
            f"</div>"
        )

        self.suggestions_area.append(formatted)

        sb = self.suggestions_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def update_status(self, message: str) -> None:
        """Updates status bar message."""
        self.statusBar().showMessage(message)

    @Slot(str)
    def show_error(self, message: str) -> None:
        """Displays error notifications in status bar."""
        self.statusBar().showMessage(f"Error: {message}")
        logger.error(f"Error emitted to UI: {message}")

    # --- User Interaction Methods ---

    def _on_device_changed(self, index: int) -> None:
        """Handles audio device change from ComboBox."""
        dev_id = self.device_combo.itemData(index)
        if dev_id is not None:
            self.device_selected.emit(dev_id)

    def _set_always_on_top(self, enabled: bool) -> None:
        """Toggles Always-on-Top mode for window."""
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        if self.isVisible():
            self.show()

    def _clear_history(self) -> None:
        """Clears transcript and suggestions areas."""
        self.transcript_area.clear()
        self.suggestions_area.clear()
        self.last_ai_suggestion = ""
        self.statusBar().showMessage("History cleared.")

    def _copy_last_suggestion(self) -> None:
        """Copies last Gemini suggestion plain text to clipboard."""
        if not self.last_ai_suggestion:
            self.statusBar().showMessage("No suggestion available to copy.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(self.last_ai_suggestion)
        self.statusBar().showMessage("Suggestion copied to clipboard!")

    def _prompt_api_key(self) -> None:
        """Opens input dialog asking for Gemini API Key and saves to .env."""
        key, ok = QInputDialog.getText(
            self,
            "Set Gemini API Key",
            "Enter your Google Gemini API Key (AI Studio):",
            text=config.gemini_api_key or ""
        )

        if ok and key.strip():
            if config.update_api_key(key):
                self.alert_banner.setVisible(False)
                self.statusBar().showMessage("Gemini API Key saved successfully to .env!")
                QMessageBox.information(
                    self,
                    "API Key Saved",
                    "Your API key was saved successfully to the `.env` file."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error Saving",
                    "Could not save key to `.env` file."
                )

    @staticmethod
    def _markdown_to_html(md_text: str) -> str:
        """Converts Markdown bullet points and formatting to HTML for Qt."""
        lines = md_text.splitlines()
        html_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    html_lines.append("<ul style='margin-top: 4px; margin-bottom: 4px; padding-left: 18px;'>")
                    in_list = True
                content = stripped[2:]
                html_lines.append(f"<li style='margin-bottom: 3px;'>{content}</li>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                if stripped:
                    html_lines.append(f"<p style='margin: 4px 0;'>{stripped}</p>")

        if in_list:
            html_lines.append("</ul>")

        result = "".join(html_lines)
        result = result.replace("**", "<b>", 1)
        while "**" in result:
            result = result.replace("**", "</b>", 1)
            if "**" in result:
                result = result.replace("**", "<b>", 1)

        return result if result else md_text

    @Slot()
    def _show_network_diagnostics(self) -> None:
        """Displays network connection diagnostics and local IP addresses."""
        import socket
        ips = []
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass

        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbynameex(hostname)[2]:
                if ip not in ips and not ip.startswith("127."):
                    ips.append(ip)
        except Exception:
            pass

        ip_list_str = "<br>".join([f"&nbsp;&nbsp;• <b>{ip}</b>" for ip in ips]) if ips else "&nbsp;&nbsp;• 127.0.0.1"
        primary_ip = ips[0] if ips else "192.168.x.x"

        msg = (
            f"<b>💻 Windows Laptop IP Address(es):</b><br>"
            f"{ip_list_str}<br><br>"
            f"<b>1. Run this command on your Mac to test connection:</b><br>"
            f"<code>python3 mac_audio_sender.py --ip {primary_ip} --test</code><br><br>"
            f"<b>2. Run this command on your Mac to stream call audio:</b><br>"
            f"<code>python3 mac_audio_sender.py --ip {primary_ip}</code><br><br>"
            f"<i>Listening on UDP Port 50005. Make sure Windows Firewall permits incoming UDP packets.</i>"
        )
        QMessageBox.information(self, "📡 Network Stream Helper & Diagnostics", msg)
