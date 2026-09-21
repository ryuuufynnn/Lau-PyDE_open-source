from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

class InlineInputOutput(QPlainTextEdit):
    """Output view that accepts one answer directly after a program prompt."""

    input_submitted = Signal(str)
    interrupt_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._interrupt_enabled = False
        self._input_start: int | None = None
        self.setReadOnly(True)

    def start_input(self) -> None:
        """Make the text after the current output the editable answer area."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self._input_start = cursor.position()
        self.setReadOnly(False)
        self.setFocus(Qt.OtherFocusReason)

    def stop_input(self) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # conditional para if user input ang code ay magkakaroon ng \n 
        if self._input_start is not None:
            cursor.insertText("\n")

        self.setTextCursor(cursor)

        self._input_start = None
        self.setReadOnly(True)

    def _input_end(self) -> int:
        return self.document().characterCount() - 1

    def _move_to_input_end(self) -> None:
        cursor = self.textCursor()
        cursor.setPosition(self._input_end())
        self.setTextCursor(cursor)

    def _input_text(self) -> str:
        cursor = self.textCursor()
        cursor.setPosition(self._input_start)
        cursor.setPosition(self._input_end(), QTextCursor.KeepAnchor)
        return cursor.selectedText().replace("\u2029", "\n")

    def keyPressEvent(self, event) -> None:

        if (event.key() == Qt.Key_C
        and event.modifiers() & Qt.ControlModifier):
            
            if self._interrupt_enabled:
                self.interrupt_requested.emit()
                return

        if self._input_start is None:
            super().keyPressEvent(event)
            return

        key = event.key()
        cursor = self.textCursor()
        selection_start = cursor.selectionStart()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.input_submitted.emit(self._input_text())
            return

        if key == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            cursor.setPosition(self._input_start)
            cursor.setPosition(self._input_end(), QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
            return

        if key == Qt.Key_Backspace and cursor.position() <= self._input_start:
            return

        if key == Qt.Key_Delete and selection_start < self._input_start:
            return

        if key == Qt.Key_Left and cursor.position() <= self._input_start:
            return

        if key == Qt.Key_Home:
            cursor.setPosition(self._input_start)
            self.setTextCursor(cursor)
            return

        # if key == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
        #     self.interrupt_requested.emmit()
        #     return

        # The program's output is protected. If the user clicked in it,
        # continue editing at the active prompt instead.
        if selection_start < self._input_start:
            self._move_to_input_end()

        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        if self._input_start is None:
            super().mousePressEvent(event)
            return

        super().mousePressEvent(event)
        if self.textCursor().position() < self._input_start:
            self._move_to_input_end()

    def set_interrupt_enabled(self, enabled: bool) -> None:
        self._interrupt_enabled = enabled