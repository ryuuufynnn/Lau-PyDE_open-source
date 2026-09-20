import ast
import difflib
import tokenize
from io import StringIO
from PySide6.QtCore import QRect, QRegularExpression, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

PYTHON_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
]

PYTHON_BUILTINS = [
    "print", "len", "range", "str", "int", "float", "bool", "list",
    "dict", "set", "tuple", "open", "input", "type", "isinstance",
    "enumerate", "zip", "map", "filter", "sorted", "sum", "min", "max",
    "abs", "super", "self",
]


class PythonHighlighter(QSyntaxHighlighter):
    """
    Colors Python source code as the user types.

    A QSyntaxHighlighter works by checking each line of text against a
    list of (regular expression, text format) rules and applying the
    matching color. Qt calls our `highlightBlock` method automatically
    whenever a line of text changes — we never call it ourselves.
    """

    def __init__(self, document):
        super().__init__(document)
        self._rules = []

        def make_format(color: str, bold: bool = False) -> QTextCharFormat:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Bold)
            return fmt

        keyword_format = make_format("#c586c0", bold=True)
        for word in PYTHON_KEYWORDS:
            self._rules.append((QRegularExpression(rf"\b{word}\b"), keyword_format))

        builtin_format = make_format("#4ec9b0")
        for word in PYTHON_BUILTINS:
            self._rules.append((QRegularExpression(rf"\b{word}\b"), builtin_format))

        # def/class NAME — highlight just the captured name (group 1),
        # not the keyword itself (the keyword already gets colored above).
        function_name_format = make_format("#dcdcaa")
        self._rules.append((QRegularExpression(r"\bdef\s+(\w+)"), function_name_format))

        class_name_format = make_format("#4ec9b0", bold=True)
        self._rules.append((QRegularExpression(r"\bclass\s+(\w+)"), class_name_format))

        number_format = make_format("#b5cea8")
        self._rules.append((QRegularExpression(r"\b[0-9]+\.?[0-9]*\b"), number_format))

        string_format = make_format("#ce9178")
        f_string_variable_format = make_format("#9CDCFE")

        self._rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        self._rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self._rules.append(
            (
                QRegularExpression(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"),
                    f_string_variable_format,
            )
        )

        self._comment_format = make_format("#6a9955")
        self._comment_pattern = QRegularExpression(r"#[^\n]*")

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                # Patterns with a capture group (def/class names) should
                # only color the captured name, not the whole match.
                if match.lastCapturedIndex() >= 1:
                    start, length = match.capturedStart(1), match.capturedLength(1)
                else:
                    start, length = match.capturedStart(), match.capturedLength()
                self.setFormat(start, length, fmt)

        # comments are applied last so "#" inside a comment always wins,
        # even if part of the comment text matched an earlier rule.
        comment_iterator = self._comment_pattern.globalMatch(text)
        while comment_iterator.hasNext():
            match = comment_iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self._comment_format)


class LineNumberArea(QWidget):
    """
    A thin widget drawn to the left of the editor that shows line numbers.

    It doesn't do any work itself — it just asks its parent CodeEditor
    to paint into it. This "delegate the painting back to the editor"
    pattern is the standard Qt approach for line-number gutters.
    """

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    """
    The main code-editing widget.

    Inherits from QPlainTextEdit, which already gives us text editing,
    copy/paste/cut/undo/redo, and keyboard navigation for free — we
    only add what's specific to a code editor: line numbers, syntax
    highlighting, and auto-indentation.
    """

    def __init__(self):
        super().__init__()

        # A monospace font is essential for code so columns line up.
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(11)
        self.setFont(font)

        # self._error_line = None
        # self._error_start = None
        # self._error_end = None
        self._syntax_errors = []
        self._keyword_errors = []
        self._name_errors = []

        # Code editors traditionally scroll sideways rather than wrap.
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

        self._line_number_area = LineNumberArea(self)

        # blockCountChanged/updateRequest/cursorPositionChanged already
        # exist on QPlainTextEdit — we connect to them ("signals and
        # slots") to keep the line-number gutter in sync as the user types.
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        self._highlighter = PythonHighlighter(self.document())
        self.textChanged.connect(self._check_errors)

    def get_error_messages(self) -> list[str]:
        """Return human-readable error messages for all current issues."""
        self._check_errors()

        messages: list[str] = []

        for line, start, end in self._syntax_errors:
            block = self.document().findBlockByLineNumber(line - 1)
            if not block.isValid():
                messages.append(f"Line {line}: Syntax error.")
                continue
            text = block.text().strip()
            if not text:
                messages.append(f"Line {line}: Syntax error.")
                continue
            messages.append(f"Line {line}: Syntax error near '{text}'.")

        for line, start, end in self._keyword_errors:
            block = self.document().findBlockByLineNumber(line - 1)
            if not block.isValid():
                messages.append(f"Line {line}: Possible keyword typo.")
                continue
            text = block.text()
            token_text = text[start:end].strip()
            if not token_text:
                messages.append(f"Line {line}: Possible keyword typo.")
                continue
            messages.append(f"Line {line}: '{token_text}' is not valid Python. Did you mean '{text[start:end].strip()}'?")

        for line, start, end in self._name_errors:
            block = self.document().findBlockByLineNumber(line - 1)
            if not block.isValid():
                messages.append(f"Line {line}: Name error.")
                continue
            text = block.text()
            token_text = text[start:end].strip()
            if not token_text:
                messages.append(f"Line {line}: Name error.")
                continue
            messages.append(f"Line {line}: '{token_text}' is not recognized. Check the spelling or name.")

        return messages

    def _collect_defined_names(self, tree: ast.AST) -> set[str]:
        """Collect names that are actually defined in the code so we do not
        flag valid variables as misspellings or undefined names."""
        defined: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.arg):
                defined.add(node.arg)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    defined.add(alias.asname or alias.name.split(".")[0])

        return defined

    def _check_errors(self) -> None:
        code = self.toPlainText()

        # self._error_line = None
        # self._error_start = None
        # self._error_end = None
        self._syntax_errors = []
        self._keyword_errors = []
        self._name_errors = []
        seen_syntax = set()
        seen_keyword = set()
        seen_name = set()

        try:
            list(tokenize.generate_tokens(StringIO(code).readline))
        except tokenize.TokenError as error:
            message, location = error.args

            if location:
                line, column = location
                item = (line, column + 1, column + 2)
                if item not in seen_syntax:
                    self._syntax_errors.append(item)
                    seen_syntax.add(item)

        tokens = []

        try:
            tokens = list(tokenize.generate_tokens(StringIO(code).readline))
        except tokenize.TokenError:
            pass

        at_statement_start = True

        for token in tokens:
            if token.type == tokenize.NEWLINE:
                at_statement_start = True
                continue

            if token.type in (tokenize.INDENT, tokenize.DEDENT):
                continue

            if at_statement_start and token.type == tokenize.NAME:
                if token.string not in PYTHON_KEYWORDS:
                    matches = difflib.get_close_matches(
                        token.string,
                        PYTHON_KEYWORDS,
                        n=1,
                        cutoff=0.75,
                    )

                    if matches:
                        item = (
                            token.start[0],
                            token.start[1],
                            token.end[1],
                        )
                        if item not in seen_keyword:
                            self._keyword_errors.append(item)
                            seen_keyword.add(item)

                at_statement_start = False

        self._name_errors = []

        defined_names: set[str] = set()

        try:
            tree = ast.parse(code)
            defined_names = self._collect_defined_names(tree)
        except SyntaxError as error:
            if error.lineno is not None and error.offset is not None:
                start = error.offset
                end = getattr(error, "end_offset", None)

                self._syntax_errors.append(
                    (
                        error.lineno,
                        start,
                        end,
                    )
                )

            self._highlight_current_line()
            return

        for token in tokens:
            if token.type != tokenize.NAME:
                continue

            if token.string in PYTHON_KEYWORDS:
                continue

            if token.string in PYTHON_BUILTINS:
                continue

            if token.string in defined_names:
                continue

            matches = difflib.get_close_matches(
                token.string,
                PYTHON_BUILTINS,
                n=1,
                cutoff=0.75,
            )

            if not matches:
                continue

            item = (
                token.start[0],
                token.start[1],
                token.end[1],
            )
            if item not in seen_name:
                self._name_errors.append(item)
                seen_name.add(item)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Name):
                continue

            if not isinstance(node.ctx, ast.Load):
                continue

            if node.id in PYTHON_KEYWORDS:
                continue

            if node.id in PYTHON_BUILTINS:
                continue

            if node.id in defined_names:
                continue

            matches = difflib.get_close_matches(
                node.id,
                PYTHON_BUILTINS,
                n=1,
                cutoff=0.75,
            )

            if matches:
                item = (
                    node.lineno,
                    node.col_offset,
                    node.end_col_offset,
                )
                if item not in seen_name:
                    self._name_errors.append(item)
                    seen_name.add(item)
        self._highlight_current_line()

    # line number gutter
    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _new_block_count: int) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        rect = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(rect.left(), rect.top(), self.line_number_area_width(), rect.height())
        )

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0, int(top), self._line_number_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignRight, str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def _highlight_current_line(self) -> None:
        """Highlight the current line and any syntax error."""

        selections = []

        # current line
        current_selection = QTextEdit.ExtraSelection()
        current_selection.format.setBackground(QColor("#2a2d2e"))
        current_selection.format.setProperty(
            QTextFormat.FullWidthSelection,
            True,
        )

        current_selection.cursor = self.textCursor()
        current_selection.cursor.clearSelection()

        selections.append(current_selection)

        # syntax errors
        for line, start, end in self._syntax_errors:
            block = self.document().findBlockByLineNumber(line - 1)

            if not block.isValid():
                continue

            error_selection = QTextEdit.ExtraSelection()

            error_selection.format.setUnderlineColor(
                QColor("#f44747")
            )
            error_selection.format.setUnderlineStyle(
                QTextCharFormat.WaveUnderline
            )

            start = max(0, start - 1)

            if end is not None:
                end = max(start + 1, end - 1)
            else:
                end = min(start + 1, len(block.text()))

            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + start)
            cursor.setPosition(
                block.position() + end,
                QTextCursor.KeepAnchor,
            )

            error_selection.cursor = cursor
            selections.append(error_selection)

        # keyword errors
        for line, start, end in self._keyword_errors:
            block = self.document().findBlockByLineNumber(line - 1)

            if not block.isValid():
                continue

            error_selection = QTextEdit.ExtraSelection()

            error_selection.format.setUnderlineColor(
                QColor("#f44747")
            )
            error_selection.format.setUnderlineStyle(
                QTextCharFormat.WaveUnderline
            )

            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + start)
            cursor.setPosition(
                block.position() + end,
                QTextCursor.KeepAnchor,
            )

            error_selection.cursor = cursor
            selections.append(error_selection)

        # name errors
        for line, start, end in self._name_errors:
            block = self.document().findBlockByLineNumber(line - 1)

            if not block.isValid():
                continue

            error_selection = QTextEdit.ExtraSelection()

            error_selection.format.setUnderlineColor(
                QColor("#f44747")
            )
            error_selection.format.setUnderlineStyle(
                QTextCharFormat.WaveUnderline
            )

            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + start)
            cursor.setPosition(
                block.position() + end,
                QTextCursor.KeepAnchor,
            )

            error_selection.cursor = cursor
            selections.append(error_selection)

        self.setExtraSelections(selections)

    # auto indentation
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_auto_indent()
            return

        if event.key() == Qt.Key_Backspace:
            if self._handle_backspace():
                return
        
        super().keyPressEvent(event)

    def _handle_backspace(self) -> bool:
        cursor = self.textCursor()

        if cursor.hasSelection():
            return False

        position = cursor.positionInBlock()
        line = cursor.block().text()

        # only handle backspace inside indentation shish
        if position == 0:
            return False

        before_cursor = line[:position]

        if not before_cursor.isspace():
            return False

        spaces = 3

        # remove up to one indentation level.
        remove_count = min(position, spaces)

        cursor.deletePreviousChar()

        for _ in range(remove_count):
            cursor.deletePreviousChar()

        self.setTextCursor(cursor)

        return True
    def _handle_auto_indent(self) -> None:
        """
        When the user presses Enter, keep the same indentation as the
        current line, and add one extra indent level if the line ends
        with a colon (e.g. `if x:`, `def foo():`).

        This is intentionally simple — it looks only at the current
        line's text, not the whole file's structure, on purpose.
        """
        cursor = self.textCursor()
        current_line = cursor.block().text()

        stripped = current_line.lstrip(" ")
        indent = current_line[: len(current_line) - len(stripped)]

        if stripped.rstrip().endswith(":"):
            indent += "    "

        cursor.insertText("\n" + indent)
        self.setTextCursor(cursor)