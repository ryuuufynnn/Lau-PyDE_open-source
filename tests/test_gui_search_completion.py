from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor

# Create QApplication before importing widgets to avoid Qt errors on some
# platforms where importing widget classes triggers Qt internals.
app = QApplication.instance() or QApplication([])

from ui.editor import CodeEditor


def test_search_and_completion():
    editor = CodeEditor()

    sample = """def foo():
    print('needle')
# needle in a comment
x = 'needle'
"""

    editor.setPlainText(sample)

    # Verify there are multiple occurrences of 'needle' via the document find API
    doc = editor.document()
    cursor = doc.find("needle")
    hits = 0
    while not cursor.isNull():
        hits += 1
        cursor = doc.find("needle", cursor)

    assert hits >= 3, f"expected >=3 'needle' hits, got {hits}"

    # Trigger completion by inserting a partial builtin name and forcing the completer
    # Place cursor at end, type 'pri', and check that 'print' is among possible completions
    c = editor.textCursor()
    c.movePosition(QTextCursor.End)
    editor.setTextCursor(c)
    editor.insertPlainText('\npri')

    # ensure internal completion model is up-to-date
    editor._check_errors()

    # select the current word under cursor manually (avoid relying on private helpers)
    cur = editor.textCursor()
    cur.select(QTextCursor.WordUnderCursor)
    prefix = cur.selectedText()
    assert prefix == 'pri', f"expected prefix 'pri', got '{prefix}'"

    candidates = [s for s in editor._completion_model.stringList() if s.startswith(prefix)]
    assert 'print' in candidates, f"'print' not found in completion candidates starting with {prefix}: {candidates}"


if __name__ == '__main__':
    # allow running this file directly for quick checks
    try:
        test_search_and_completion()
        print('TEST_OK')
    except AssertionError as e:
        print('TEST_FAIL', e)
    except Exception as e:
        print('TEST_ERROR', e)
