from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._output)
        layout.addWidget(self._input)

        self._process = None

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

    def _handle_output(self) -> None:
        data = self._process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)

    def _handle_finished(self, _exit_code: int, _exit_status) -> None:
        self._output.appendPlainText("")
