from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def test_live_diagnostics_updates_explorer_badge():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()

    # simulate opening a file
    w._current_file_path = "/tmp/test_live.py"

    # set content with a syntax error
    w.editor.setPlainText("x = 1\nprint(\n")

    # directly trigger diagnostic handler (bypass timer)
    w.editor._on_diagnostic_timer()

    # the explorer should have an entry for the file with count > 0
    count = w.explorer._error_counts.get(w._current_file_path, 0)
    assert count >= 1
