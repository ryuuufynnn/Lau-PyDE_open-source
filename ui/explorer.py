"""
explorer.py

A simple file explorer sidebar. Shows the folder the user opened as a
tree, and lets them double-click a file to open it in the editor.

We use QFileSystemModel + QTreeView, Qt's built-in widgets for showing
a folder as a tree — we don't write any folder-scanning code ourselves,
and nothing outside the opened folder is ever touched.
"""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QVBoxLayout, QWidget

class FileExplorer(QWidget):
    """
    Sidebar showing the currently opened folder as a file tree.

    Emits `file_double_clicked` with the full path when the user
    double-clicks a file, so MainWindow can open it in the editor.
    Using a signal here (instead of, say, FileExplorer importing and
    calling MainWindow directly) keeps this widget independent — it
    doesn't need to know anything about the rest of the app.
    """

    file_double_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        self._model = QFileSystemModel()
        self._model.setNameFilters(["*.py", "*.txt", "*.md", "*.json", "*.cfg", "*.toml"])
        self._model.setNameFilterDisables(False)  # hide non-matching files entirely

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        # Only the "name" column matters here; hide size/type/date columns.
        for column in (1, 2, 3):
            self._tree.hideColumn(column)

        self._tree.doubleClicked.connect(self._on_double_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

    def set_root_folder(self, folder_path: str) -> None:
        """Point the explorer at a new project folder."""
        root_index = self._model.setRootPath(folder_path)
        self._tree.setRootIndex(root_index)

    def _on_double_clicked(self, index) -> None:
        path = self._model.filePath(index)
        if Path(path).is_file():
            self.file_double_clicked.emit(path)

