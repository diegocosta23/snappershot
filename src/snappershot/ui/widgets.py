from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class SearchBox(QLineEdit):
    """
    Sökfält för bolag.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setPlaceholderText("Sök företag...")
        self.setMinimumHeight(38)


class CompanyList(QListWidget):
    """
    Lista med sökträffar.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setMinimumHeight(220)


class TimeframePanel(QGroupBox):
    """
    Val av timeframes.
    """

    def __init__(self) -> None:

        super().__init__("Timeframes")

        layout = QHBoxLayout(self)

        self.week = QCheckBox("1W")
        self.day = QCheckBox("1D")
        self.h4 = QCheckBox("4H")
        self.m45 = QCheckBox("45M")

        self.week.setChecked(True)
        self.day.setChecked(True)
        self.h4.setChecked(True)
        self.m45.setChecked(True)

        layout.addWidget(self.week)
        layout.addWidget(self.day)
        layout.addWidget(self.h4)
        layout.addWidget(self.m45)


class CaptureButton(QPushButton):
    """
    Start Capture.
    """

    def __init__(self) -> None:

        super().__init__("Capture Screenshots")

        self.setMinimumHeight(42)


class StatusPanel(QFrame):
    """
    Nedersta statusraden.
    """

    def __init__(self) -> None:

        super().__init__()

        layout = QVBoxLayout(self)

        self.status = QLabel("Ready")
        self.progress = QProgressBar()

        self.progress.setValue(0)

        layout.addWidget(self.status)
        layout.addWidget(self.progress)


class LogPanel(QTextEdit):
    """
    Programlogg.
    """

    def __init__(self) -> None:

        super().__init__()

        self.setReadOnly(True)
        self.setMinimumHeight(170)

    def log(self, text: str):

        self.append(text)
