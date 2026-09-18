import sys

from PySide6.QtCore import QObject, QProcess, Signal


class PythonRunner(QObject):
    """
    Runs a Python file using QProcess and reports its output via signals.

    We inherit from QObject (not a widget) because this class has no
    visual part — it just manages a background process. Any QObject
    can define custom signals like the ones below.
    """

    # emitted whenever the running program produces output (stdout or
    # stderr, merged together). Carries the new text as a string.
    output_ready = Signal(str)

    # emitted when the process finishes, carrying its exit code.
    finished = Signal(int)

    def __init__(self):
        super().__init__()
        self._process = None

    def run_file(self, file_path: str, working_dir: str) -> None:
        """Start running the given Python file."""
        if self.is_running():
            return  # a run is already in progress; ignore extra clicks

        self._process = QProcess()
        self._process.setWorkingDirectory(working_dir)

        # merge stdout and stderr into one stream, so tracebacks show
        # up in the output panel right alongside normal print() output.
        self._process.setProcessChannelMode(QProcess.MergedChannels)

        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)

        # sys.executable is the interpreter currently running PyDE
        # itself — using it means "run with the same Python PyDE uses".
        self._process.start(sys.executable, [file_path])

    def stop(self) -> None:
        """Stop the currently running process, if any."""
        if self.is_running():
            self._process.kill()

    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.NotRunning

    def _handle_output(self) -> None:
        data = self._process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self.output_ready.emit(text)

    def _handle_finished(self, exit_code: int, _exit_status) -> None:
        self.finished.emit(exit_code)
