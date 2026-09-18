from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TerminalPanel(QWidget):
    """A minimal command runner: an output area plus a command input box."""

    def __init__(self):
        super().__init__()

        self._working_dir = str(Path.home())

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        self._output.setFont(font)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command and press Enter (e.g. python --version)")
        self._input.returnPressed.connect(self._run_command)

        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addWidget(QLabel("Terminal"))
        title_bar_layout.addStretch()

        minimize_button = QPushButton("—")
        maximize_button = QPushButton("□")
        minimize_button.setToolTip("Minimize terminal")
        maximize_button.setToolTip("Maximize terminal")
        minimize_button.setFixedWidth(32)
        maximize_button.setFixedWidth(32)
        minimize_button.clicked.connect(self._minimize_terminal)
        maximize_button.clicked.connect(self._maximize_terminal)
        title_bar_layout.addWidget(minimize_button)
        title_bar_layout.addWidget(maximize_button)
        self.setStyleSheet("QPushButton { min-height: 24px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(title_bar)
        layout.addWidget(self._output)
        layout.addWidget(self._input)

        self._process = None
        self._is_minimized = False

    def set_working_directory(self, folder_path: str) -> None:
        self._working_dir = folder_path

    def _run_command(self) -> None:
        command = self._input.text().strip()
        if not command:
            return
        self._input.clear()
        self._output.appendPlainText(f"$ {command}")

        if self._process is not None and self._process.state() != QProcess.NotRunning:
            self._output.appendPlainText("(A command is already running, please wait.)")
            return

        self._process = QProcess()
        self._process.setWorkingDirectory(self._working_dir)
        # Merge stdout and stderr so error output shows up too.
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)

        # Running through the system shell (bash) means pipes, quotes,
        # and things like `pip --version` behave as the user expects.
        self._process.start("bash", ["-c", command])

    def _minimize_terminal(self) -> None:
        if self._is_minimized:
            self._output.setVisible(True)
            self._input.setVisible(True)
            self._is_minimized = False
            return

        self._output.setVisible(False)
        self._input.setVisible(False)
        self._is_minimized = True

    def _maximize_terminal(self) -> None:
        self._output.setVisible(True)
        self._input.setVisible(True)
        self._is_minimized = False
        self._input.setFocus()

    def _handle_output(self) -> None:
        data = self._process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)

    def _handle_finished(self, _exit_code: int, _exit_status) -> None:
        self._output.appendPlainText("")
