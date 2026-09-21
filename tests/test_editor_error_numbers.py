from PySide6.QtWidgets import QApplication

from ui.editor import CodeEditor


def test_error_line_numbers_are_tracked_for_syntax_errors():
    app = QApplication.instance() or QApplication([])
    editor = CodeEditor()

    editor.setPlainText("x = 1\nprint(\n")
    editor._check_errors()

    assert editor._error_line_numbers() == {2}
