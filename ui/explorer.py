"""
explorer.py

A simple file explorer sidebar. Shows the folder the user opened as a
tree, and lets them double-click a file to open it in the editor.

We use QFileSystemModel + QTreeView, Qt's built-in widgets for showing
a folder as a tree — we don't write any folder-scanning code ourselves,
and nothing outside the opened folder is ever touched.
"""

from pathlib import Path

from PySide6.QtCore import Signal, Qt, QModelIndex, QDir
from PySide6.QtGui import QColor, QPainter 
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QStyledItemDelegate,
)

class ErrorCountDelegate(QStyledItemDelegate):
    """Draws the file name and its code-issue count."""

    def __init__(self, explorer, parent=None):
        super().__init__(parent)
        self.explorer = explorer

    def paint(self, painter: QPainter, option, index) -> None:
        super().paint(painter, option, index)

        path = self.explorer._model.filePath(index)
        count = self.explorer._error_counts.get(path)

        if not count:
            return

        painter.save()

        badge_width = 20
        badge_height = 18

        badge_x = option.rect.right() - badge_width - 6
        badge_y = option.rect.center().y() - badge_height // 2

        badge_rect = option.rect.__class__(
            badge_x,
            badge_y,
            badge_width,
            badge_height,
        )

        painter.setPen(Qt.NoPen)

        painter.setPen(QColor("#ffd500"))
        painter.drawText(
            badge_rect,
            Qt.AlignCenter,
            str(count),
        )

        painter.restore()

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
    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self):
        super().__init__()

        self._model = QFileSystemModel()
        # show both directories and matching files; do not hide folders
        self._model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        self._model.setNameFilters(["*.py", "*.txt", "*.md", "*.json", "*.cfg", "*.toml"])
        self._model.setNameFilterDisables(False)  # hide non-matching files entirely

        self._error_counts = {}

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setItemDelegate(ErrorCountDelegate(self, self._tree))
        self._tree.setHeaderHidden(True)

        # Only the "name" column matters here; hide size/type/date columns.
        for column in (1, 2, 3):
            self._tree.hideColumn(column)

        self._tree.doubleClicked.connect(self._on_double_clicked)

        # title_bar = QWidget()
        # title_layout = QHBoxLayout(title_bar)
        # title_layout.setContentsMargins(4, 4, 4, 0)
        title_bar = QWidget()
        title_bar.setFixedHeight(32)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(4, 0, 4, 0)

        title_layout.addWidget(QLabel("Explorer"))
        title_layout.addStretch()

        minimize_button = QPushButton("▁")
        maximize_button = QPushButton("▢")
        minimize_button.setToolTip("Minimize explorer")
        maximize_button.setToolTip("Maximize or restore explorer")
        minimize_button.setFixedWidth(32)
        maximize_button.setFixedWidth(32)
        minimize_button.clicked.connect(self.minimize_requested)
        maximize_button.clicked.connect(self.maximize_requested)
        # remove button borders to match other panels
        minimize_button.setStyleSheet("border: none; min-height: 24px;")
        maximize_button.setStyleSheet("border: none; min-height: 24px;")
        title_layout.addWidget(minimize_button)
        title_layout.addWidget(maximize_button)

        for pointer in maximize_button, minimize_button:
            pointer.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)
        layout.addWidget(self._tree)
        layout.addStretch()

    def set_root_folder(self, folder_path: str | None) -> None:
        """Point the explorer at a new project folder."""

        # if walang naka open na folder dapat walang path
        if not folder_path:
            self._tree.hide()
            return
        
        root_index = self._model.setRootPath(folder_path)
        self._tree.setRootIndex(root_index)
        self._tree.show()

    def _on_double_clicked(self, index) -> None:
        path = self._model.filePath(index)
        if Path(path).is_file():
            self.file_double_clicked.emit(path)

    def set_error_count(self, file_path: str, count: int) -> None:
        """Set the number of code issues for a file."""
        if count <= 0:
            self._error_counts.pop(file_path, None)
        else:
            self._error_counts[file_path] = count

        self._tree.viewport().update()