from pathlib import Path

from PySide6.QtCore import QProcess, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.inline_output import InlineInputOutput


class TerminalPanel(QWidget):
    """A command runner whose editable command line lives in the terminal."""

    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self):
        super().__init__()

        self._working_dir = str(Path.home())

        self._output = InlineInputOutput()
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        self._output.setFont(font)
        self._output.input_submitted.connect(self._run_command)

        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addWidget(QLabel("Terminal"))
        title_bar_layout.addStretch()

        self._stop_button = QPushButton("Stop")
        self._stop_button.setToolTip("Stop the running terminal command")
        self._stop_button.setEnabled(False)
        self._stop_button.clicked.connect(self.stop)

        minimize_button = QPushButton("—")
        maximize_button = QPushButton("□")
        minimize_button.setToolTip("Minimize terminal")
        maximize_button.setToolTip("Maximize or restore terminal")
        minimize_button.setFixedWidth(32)
        maximize_button.setFixedWidth(32)
        minimize_button.clicked.connect(self.minimize_requested)
        maximize_button.clicked.connect(self.maximize_requested)
        title_bar_layout.addWidget(self._stop_button)
        title_bar_layout.addWidget(minimize_button)
        title_bar_layout.addWidget(maximize_button)
        self.setStyleSheet("QPushButton { min-height: 24px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(title_bar)
        layout.addWidget(self._output)

        self._process = None
        self._show_prompt()

    def set_working_directory(self, folder_path: str) -> None:
        self._working_dir = folder_path

    def _run_command(self, command: str) -> None:
        command = command.strip()
        self._output.stop_input()
        self._output.moveCursor(QTextCursor.End)
        # self._output.insertPlainText("\n")
        if not command:
            self._show_prompt()
            return

        if self._process is not None and self._process.state() != QProcess.NotRunning:
            self._output.appendPlainText("(A command is already running, please wait.)")
            self._show_prompt()
            return

        self._process = QProcess()
        self._process.setWorkingDirectory(self._working_dir)
        # Merge stdout and stderr so error output shows up too.
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)
        self._stop_button.setEnabled(True)

        # Running through the system shell (bash) means pipes, quotes,
        # and things like `pip --version` behave as the user expects.
        self._process.start("bash", ["-c", command])

    def stop(self) -> None:
        """Kill the current shell command, if one is still running."""
        if self._process is not None and self._process.state() != QProcess.NotRunning:
            self._process.kill()

    def focus_input(self) -> None:
        """Focus the current inline terminal prompt."""
        self._output.setFocus()
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output.setTextCursor(cursor)

    def _handle_output(self) -> None:
        data = self._process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self._output.moveCursor(QTextCursor.End)
        self._output.insertPlainText(text)

    def _handle_finished(self, _exit_code: int, _exit_status) -> None:
        self._output.appendPlainText("")
        self._process = None
        self._stop_button.setEnabled(False)
        self._show_prompt()

    # def colors(self):
    #     # ANSI escape codes for colors
    #     RED = "\033[91m"
    #     GREEN = "\033[92m"
    #     YELLOW = "\033[93m"
    #     BLUE = "\033[94m"
    #     MAGENTA = "\033[95m"
    #     CYAN = "\033[96m"
    #     RESET = "\033[0m"

    #     return RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, RESET


    def _show_prompt(self) -> None:
        current_path = Path.cwd()
        cursor = self._output.textCursor()
        green_format = QTextCharFormat()
        green_format.setForeground(QColor("#00ff00"))

        cursor.setCharFormat(green_format)
        cursor.insertText(f"{current_path}\n")
        cursor.insertText("$ ")

        self._output.setTextCursor(cursor)
        self._output.start_input()
