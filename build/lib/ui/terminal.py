import re
from pathlib import Path

from PySide6.QtCore import QProcess, Signal, Qt
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
        self._working_directory = str(Path.cwd())

        self._output = InlineInputOutput()
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        self._output.setFont(font)
        self._output.input_submitted.connect(self._run_command)
        self._output.interrupt_requested.connect(self.stop)

        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addWidget(QLabel("Terminal"))
        title_bar_layout.addStretch()

        # terminal doesn't show a separate stop control (not useful here)
        minimize_button = QPushButton("▁")
        maximize_button = QPushButton("▢")
        minimize_button.setToolTip("Minimize terminal")
        maximize_button.setToolTip("Maximize or restore terminal")
        minimize_button.setFixedWidth(32)
        minimize_button.setCursor(Qt.PointingHandCursor)
        maximize_button.setFixedWidth(32)
        maximize_button.setCursor(Qt.PointingHandCursor)
        minimize_button.clicked.connect(self.minimize_requested)
        maximize_button.clicked.connect(self.maximize_requested)
        title_bar_layout.addWidget(minimize_button)
        title_bar_layout.addWidget(maximize_button)
        # remove button borders for a cleaner title bar
        minimize_button.setStyleSheet("border: none; min-height: 24px;")
        maximize_button.setStyleSheet("border: none; min-height: 24px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(title_bar)
        layout.addWidget(self._output)

        self._process = None
        self._show_prompt()

    def set_working_directory(self, path: str) -> None:
        self._working_dir = path
        self._working_directory = path
        self._show_prompt()

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

        if command == "lau c":
            self._output.clear()
            self._show_prompt()
            return

        self._process = QProcess()
        self._output.set_interrupt_enabled(True)
        self._process.setWorkingDirectory(self._working_dir)
        # Merge stdout and stderr so error output shows up too.
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)

        # running through the system shell (bash) means pipes, quotes,
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

        error_pattern = re.compile(
            r"(Traceback \(most recent call last\):|File \".*\"|\b(?:SyntaxError|NameError|ValueError|TypeError|IndexError|KeyError|AttributeError|IndentationError|TabError|AssertionError|RuntimeError|ModuleNotFoundError|ImportError)\b|Error:|Exception:)",
            re.IGNORECASE,
        )
        format_ = QTextCharFormat()
        format_.setForeground(QColor("#ff0000") if error_pattern.search(text) else QColor("#00ff00"))
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, format_)
        self._output.setTextCursor(cursor)

    def _handle_finished(self, _exit_code: int, _exit_status) -> None:
        self._output.set_interrupt_enabled(False)
        self._output.appendPlainText("")
        self._process = None
        self._show_prompt()

    def _show_prompt(self) -> None:
        current_path = self._working_dir

        cursor = self._output.textCursor()
        green_format = QTextCharFormat()
        green_format.setForeground(QColor("#00ff00"))

        cursor.setCharFormat(green_format)
        cursor.insertText(f"{current_path}\n")
        cursor.insertText("$ ")

        self._output.setTextCursor(cursor)
        self._output.start_input()