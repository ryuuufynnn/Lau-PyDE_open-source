import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


app = QApplication.instance() or QApplication(sys.argv)


def test_prompt_without_trailing_space_still_activates_inline_input():
    win = MainWindow()

    class Runner:
        def __init__(self):
            self.running = True

        def is_running(self):
            return self.running

        def stop(self):
            self.running = False

    win._runner = Runner()
    win.output_panel.clear()
    win._output_line_tail = ""
    win._active_prompt = ""

    win._append_output("Name: ")

    assert win.output_panel.isReadOnly() is False
    assert win.output_panel._input_start == len("Name: ")
    assert win._active_prompt == "Name:"

    win.output_panel.close()
    win.close()
