from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    capture_requested = Signal()
    search_text_changed = Signal(str)
    company_selected = Signal(str)
    copy_zip_requested = Signal()
    open_folder_requested = Signal()
    clear_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._zip_filename = ""
        self._zip_path = ""

        self.setObjectName("mainWindow")
        self.setWindowTitle("SnapperShot")
        self.resize(1220, 860)
        self.setMinimumSize(1100, 760)

        self._build_ui()
        self._connect_signals()

        self.set_company_results([])
        self.set_result(None, None)
        self.set_status("Redo")
        self.set_progress(0)
        self.append_log("SnapperShot startad.")

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(22, 22, 22, 22)
        root_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        scroll.setWidget(content)

        header_card = self._create_card()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(6)

        title = QLabel("SnapperShot")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("TradingView Desktop → snapshots → ZIP → ChatGPT")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.connection_label = QLabel("TradingView Desktop: väntar på anslutning")
        self.connection_label.setObjectName("statusValue")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(self.connection_label)

        search_card = self._create_card()
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(18, 18, 18, 18)
        search_layout.setSpacing(12)

        search_title = QLabel("Sök företag")
        search_title.setObjectName("sectionLabel")

        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Skriv exempelvis Investor...")
        self.company_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.results_hint = QLabel("Skriv minst två tecken för att se träffar.")
        self.results_hint.setObjectName("subtitleLabel")

        self.company_results = QListWidget()
        self.company_results.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.company_results.setMinimumHeight(170)
        self.company_results.itemClicked.connect(self._handle_result_clicked)
        self.company_results.hide()

        search_layout.addWidget(search_title)
        search_layout.addWidget(self.company_input)
        search_layout.addWidget(self.results_hint)
        search_layout.addWidget(self.company_results)

        timeframe_card = self._create_card()
        timeframe_layout = QVBoxLayout(timeframe_card)
        timeframe_layout.setContentsMargins(18, 18, 18, 18)
        timeframe_layout.setSpacing(10)

        timeframe_title = QLabel("Tidsramar")
        timeframe_title.setObjectName("sectionLabel")

        timeframe_note = QLabel("Välj vilka snapshots som ska tas. Standard är alla fyra.")
        timeframe_note.setObjectName("subtitleLabel")

        timeframe_row = QHBoxLayout()
        timeframe_row.setSpacing(14)

        self.timeframe_1w = QCheckBox("1W")
        self.timeframe_1d = QCheckBox("1D")
        self.timeframe_4h = QCheckBox("4H")
        self.timeframe_45m = QCheckBox("45M")

        for checkbox in (self.timeframe_1w, self.timeframe_1d, self.timeframe_4h, self.timeframe_45m):
            checkbox.setChecked(True)
            timeframe_row.addWidget(checkbox)

        timeframe_row.addStretch(1)

        timeframe_layout.addWidget(timeframe_title)
        timeframe_layout.addWidget(timeframe_note)
        timeframe_layout.addLayout(timeframe_row)

        integration_card = self._create_card()
        integration_layout = QVBoxLayout(integration_card)
        integration_layout.setContentsMargins(18, 18, 18, 18)
        integration_layout.setSpacing(10)

        integration_title = QLabel("Plats för framtida integrationer")
        integration_title.setObjectName("sectionLabel")

        integration_note = QLabel("Här finns utrymme för Finnhub, Yahoo Finance, nyheter och andra datakällor senare.")
        integration_note.setObjectName("subtitleLabel")
        integration_note.setWordWrap(True)

        integration_row = QHBoxLayout()
        integration_row.setSpacing(10)

        integration_row.addWidget(self._integration_card("TradingView", "Desktop automation"))
        integration_row.addWidget(self._integration_card("Finnhub", "Framtida API-källa"))
        integration_row.addWidget(self._integration_card("Yahoo Finance", "Framtida API-källa"))
        integration_row.addWidget(self._integration_card("Nyheter", "Framtida nyhetsflöde"))

        integration_layout.addWidget(integration_title)
        integration_layout.addWidget(integration_note)
        integration_layout.addLayout(integration_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.capture_button = QPushButton("📸 Capture")
        self.capture_button.setObjectName("primaryAction")
        self.capture_button.setMinimumHeight(48)
        self.capture_button.clicked.connect(self.capture_requested.emit)

        self.capture_note = QLabel("Programmet tar 1W, 1D, 4H och 45M när allt är klart.")
        self.capture_note.setObjectName("subtitleLabel")
        self.capture_note.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        action_row.addWidget(self.capture_button, 0)
        action_row.addWidget(self.capture_note, 1)

        progress_card = self._create_card()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(18, 18, 18, 18)
        progress_layout.setSpacing(10)

        progress_title = QLabel("Status")
        progress_title.setObjectName("sectionLabel")

        progress_row = QHBoxLayout()
        progress_row.setSpacing(12)

        self.status_value = QLabel("Redo")
        self.status_value.setObjectName("statusValue")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        progress_row.addWidget(self.status_value, 0)
        progress_row.addWidget(self.progress_bar, 1)

        progress_layout.addWidget(progress_title)
        progress_layout.addLayout(progress_row)

        result_card = self._create_card()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 18, 18, 18)
        result_layout.setSpacing(12)

        result_title = QLabel("Resultat")
        result_title.setObjectName("sectionLabel")

        self.result_value = QLabel("Ingen ZIP skapad ännu.")
        self.result_value.setObjectName("resultValue")
        self.result_value.setWordWrap(True)

        self.result_path_value = QLabel("Sparad plats visas här när ZIP är klar.")
        self.result_path_value.setObjectName("resultPathValue")
        self.result_path_value.setWordWrap(True)

        result_buttons = QHBoxLayout()
        result_buttons.setSpacing(10)

        self.copy_zip_button = QPushButton("📋 Kopiera ZIP")
        self.copy_zip_button.setObjectName("successAction")
        self.copy_zip_button.setEnabled(False)
        self.copy_zip_button.clicked.connect(self.copy_zip_requested.emit)

        self.open_folder_button = QPushButton("📂 Öppna mapp")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)

        self.clear_button = QPushButton("🗑 Rensa")
        self.clear_button.setObjectName("dangerAction")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_requested.emit)

        result_buttons.addWidget(self.copy_zip_button)
        result_buttons.addWidget(self.open_folder_button)
        result_buttons.addWidget(self.clear_button)

        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.result_path_value)
        result_layout.addLayout(result_buttons)

        log_card = self._create_card()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(18, 18, 18, 18)
        log_layout.setSpacing(10)

        log_title = QLabel("Logg")
        log_title.setObjectName("sectionLabel")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(200)

        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_box)

        content_layout.addWidget(header_card)
        content_layout.addWidget(search_card)
        content_layout.addWidget(timeframe_card)
        content_layout.addWidget(integration_card)
        content_layout.addLayout(action_row)
        content_layout.addWidget(progress_card)
        content_layout.addWidget(result_card)
        content_layout.addWidget(log_card, 1)

        root_layout.addWidget(scroll)

    def _create_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        return card

    def _integration_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setMinimumWidth(180)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("sectionLabel")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return card

    def _connect_signals(self) -> None:
        self.company_input.textEdited.connect(self.search_text_changed.emit)
        self.company_input.returnPressed.connect(self._emit_selected_company)

    def _emit_selected_company(self) -> None:
        company = self.current_company_text()
        if company:
            self.company_selected.emit(company)

    def _handle_result_clicked(self, item: QListWidgetItem) -> None:
        company = item.text().strip()
        if company:
            self.set_company_text(company)
            self.company_selected.emit(company)

    def set_company_text(self, text: str) -> None:
        previous = self.company_input.blockSignals(True)
        try:
            self.company_input.setText(text)
        finally:
            self.company_input.blockSignals(previous)

    def current_company_text(self) -> str:
        return self.company_input.text().strip()

    def set_company_results(self, results: list[str]) -> None:
        self.company_results.clear()

        if not results:
            self.company_results.hide()
            self.results_hint.setText("Inga träffar ännu. Skriv ett företagsnamn för att söka.")
            self.results_hint.show()
            return

        for result in results:
            self.company_results.addItem(QListWidgetItem(result))

        self.results_hint.hide()
        self.company_results.show()

    def set_result(self, filename: str | None, path: str | None) -> None:
        if not filename or not path:
            self._zip_filename = ""
            self._zip_path = ""
            self.result_value.setText("Ingen ZIP skapad ännu.")
            self.result_path_value.setText("Sparad plats visas här när ZIP är klar.")
            self.copy_zip_button.setEnabled(False)
            self.open_folder_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        self._zip_filename = filename
        self._zip_path = path
        self.result_value.setText(f"✔ {filename}")
        self.result_path_value.setText(f"Sparad i: {path}")
        self.copy_zip_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def set_status(self, text: str) -> None:
        self.status_value.setText(text)

    def set_connection_status(self, text: str) -> None:
        self.connection_label.setText(text)

    def set_busy(self, busy: bool) -> None:
        self.capture_button.setEnabled(not busy)
        self.company_input.setEnabled(not busy)
        self.company_results.setEnabled(not busy)
        for checkbox in (self.timeframe_1w, self.timeframe_1d, self.timeframe_4h, self.timeframe_45m):
            checkbox.setEnabled(not busy)

        if busy:
            self.capture_button.setText("Arbetar...")
            self.progress_bar.setRange(0, 0)
        else:
            self.capture_button.setText("📸 Capture")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(max(0, min(100, value)))

    def selected_timeframes(self) -> list[str]:
        timeframes = []
        if self.timeframe_1w.isChecked():
            timeframes.append("1W")
        if self.timeframe_1d.isChecked():
            timeframes.append("1D")
        if self.timeframe_4h.isChecked():
            timeframes.append("4H")
        if self.timeframe_45m.isChecked():
            timeframes.append("45M")
        return timeframes

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"{timestamp}  {message}")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def clear_log(self) -> None:
        self.log_box.clear()

    def show_error(self, message: str) -> None:
        self.set_status(message)
        self.append_log(f"❌ {message}")

    def show_success(self, message: str) -> None:
        self.set_status(message)
        self.append_log(f"✅ {message}")

    def selected_zip_path(self) -> str:
        return self._zip_path

    def selected_zip_filename(self) -> str:
        return self._zip_filename