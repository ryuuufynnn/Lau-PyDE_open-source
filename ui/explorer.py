"""
explorer.py

A simple file explorer sidebar. Shows the folder the user opened as a
tree, and lets them double-click a file to open it in the editor.

We use QFileSystemModel + QTreeView, Qt's built-in widgets for showing
a folder as a tree — we don't write any folder-scanning code ourselves,
and nothing outside the opened folder is ever touched.
"""

from pathlib import Path
import os
import sys
import shutil
import subprocess
import typing

from PySide6.QtCore import Signal, Qt, QModelIndex, QDir, QUrl
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QStyledItemDelegate,
    QMenu,
    QInputDialog,
    QMessageBox,
    QFileDialog,
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
        self._model.setNameFilters(["*.py", "*.txt", "*.md", "*.json", "*.cfg", "*.toml"])
        # Keep folders visible while filtering file names so the user can
        # browse the full directory hierarchy (expand/collapse folders).
        self._model.setNameFilterDisables(True)
        # Show directories and files; hide '.' and '..'
        self._model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)

        self._error_counts = {}
        self._project_root = None

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

        # context menu for file actions
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        # track last parent index we hid rows under so we can unhide later
        self._last_hidden_parent = None

    def set_root_folder(self, folder_path: str | None) -> None:
        """Point the explorer at a new project folder."""
        # store a normalized project root to make comparisons robust
        try:
            self._project_root = str(Path(folder_path).resolve()) if folder_path else None
        except Exception:
            # fallback to the raw string when resolve fails
            self._project_root = str(Path(folder_path)) if folder_path else None
        # if no folder is open, hide the tree
        if not folder_path:
            # unhide any previously hidden rows
            try:
                if self._last_hidden_parent is not None:
                    self._unhide_all_rows(self._last_hidden_parent)
            except Exception:
                pass
            self._tree.hide()
            return
        p = Path(folder_path)
        try:
            # If possible, set the view root to the folder's parent and
            # hide all siblings so the chosen folder is the only visible
            # child. This makes the explorer clearly show "the chosen
            # folder" rather than a list of siblings under its parent.
            parent = p.parent
            if parent.exists() and parent != p:
                # clear previously hidden rows
                if self._last_hidden_parent is not None:
                    try:
                        self._unhide_all_rows(self._last_hidden_parent)
                    except Exception:
                        pass

                self._model.setRootPath(str(parent))
                parent_idx = self._model.index(str(parent))
                self._tree.setRootIndex(parent_idx)

                # hide all rows except the chosen folder
                # compare paths using resolution and case-normalization so
                # Windows path variants (case/different separators) do not
                # cause the chosen folder to be hidden by accident.
                def _norm_path(x: str) -> str:
                    try:
                        return str(Path(x).resolve())
                    except Exception:
                        return os.path.normcase(os.path.normpath(str(x)))

                target_norm = _norm_path(p)
                for row in range(self._model.rowCount(parent_idx)):
                    child = self._model.index(row, 0, parent_idx)
                    child_path = self._model.filePath(child)
                    child_norm = _norm_path(child_path)
                    hide = child_norm != target_norm
                    try:
                        self._tree.setRowHidden(row, parent_idx, hide)
                    except Exception:
                        pass

                # remember which parent we hid rows under so we can unhide later
                self._last_hidden_parent = parent_idx

                # expand the chosen folder so its contents are visible
                try:
                    chosen_idx = self._model.index(str(p))
                    if chosen_idx.isValid():
                        self._tree.expand(chosen_idx)
                        self._tree.setCurrentIndex(chosen_idx)
                except Exception:
                    pass

                self._tree.show()
                return

            # fallback: set the model root directly to the folder
            self._model.setRootPath(str(p))
            idx = self._model.index(str(p))
            if idx.isValid():
                self._tree.setRootIndex(idx)
                try:
                    self._tree.expand(idx)
                except Exception:
                    pass
                self._tree.show()
        except Exception:
            # fallback: try setting the model root to the provided path
            try:
                root_index = self._model.setRootPath(folder_path)
                self._tree.setRootIndex(root_index)
                self._tree.show()
            except Exception:
                self._tree.hide()

    def _on_double_clicked(self, index) -> None:
        path = self._model.filePath(index)
        if Path(path).is_file():
            self.file_double_clicked.emit(path)

    def reveal_path(self, file_path: str) -> None:
        """Ensure the file is selected without collapsing the current project tree."""
        p = Path(file_path)
        if not p.exists():
            return

        root_folder = self._project_root
        project_root = Path(root_folder) if root_folder else None

        # Keep the active project root stable when a file inside that project is
        # opened. Resetting to the file's parent folder is what collapses the
        # visible hierarchy and hides the parent folders from the user.
        if project_root and p.is_relative_to(project_root):
            idx = self._model.index(str(p))
            if not idx.isValid():
                parent_idx = self._model.index(str(p.parent))
                if parent_idx.isValid():
                    name = p.name
                    for row in range(self._model.rowCount(parent_idx)):
                        child = self._model.index(row, 0, parent_idx)
                        if self._model.fileName(child) == name:
                            idx = child
                            break

            if idx.isValid():
                parent = idx.parent()
                parents = []
                while parent.isValid():
                    parents.append(parent)
                    parent = parent.parent()

                for pidx in reversed(parents):
                    try:
                        self._tree.expand(pidx)
                    except Exception:
                        pass

                self._tree.setCurrentIndex(idx)
                self._tree.scrollTo(idx)
            return

        # Only fall back to the file's parent when the selected file is outside
        # the currently opened project; keep the same folder-root pattern used in
        # `set_root_folder` for that case.
        folder = str(p.parent)
        try:
            root_index = self._model.setRootPath(folder)
            self._tree.setRootIndex(root_index)
        except Exception:
            try:
                self.set_root_folder(folder)
            except Exception:
                pass

        idx = self._model.index(str(p))
        if not idx.isValid():
            parent_idx = self._model.index(folder)
            if parent_idx.isValid():
                name = p.name
                for row in range(self._model.rowCount(parent_idx)):
                    child = self._model.index(row, 0, parent_idx)
                    if self._model.fileName(child) == name:
                        idx = child
                        break

        if idx.isValid():
            parent = idx.parent()
            parents = []
            while parent.isValid():
                parents.append(parent)
                parent = parent.parent()

            for pidx in reversed(parents):
                try:
                    self._tree.expand(pidx)
                except Exception:
                    pass

            self._tree.setCurrentIndex(idx)
            self._tree.scrollTo(idx)

    def _unhide_all_rows(self, parent_idx: QModelIndex) -> None:
        """Unhide all rows under the given parent index."""
        try:
            for row in range(self._model.rowCount(parent_idx)):
                try:
                    self._tree.setRowHidden(row, parent_idx, False)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_context_menu(self, pos) -> None:
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return

        path = self._model.filePath(index)

        menu = QMenu(self)

        if Path(path).is_dir():
            new_file = QAction('New File', self)
            new_file.triggered.connect(lambda: self._create_file(path))
            menu.addAction(new_file)

            new_folder = QAction('New Folder', self)
            new_folder.triggered.connect(lambda: self._create_folder(path))
            menu.addAction(new_folder)

        rename = QAction('Rename', self)
        rename.triggered.connect(lambda: self._rename(path))
        menu.addAction(rename)

        delete = QAction('Delete', self)
        delete.triggered.connect(lambda: self._delete(path))
        menu.addAction(delete)

        menu.addSeparator()

        copy_path = QAction('Copy Path', self)
        copy_path.triggered.connect(lambda: self._copy_path(path))
        menu.addAction(copy_path)

        reveal = QAction('Reveal in File Manager', self)
        reveal.triggered.connect(lambda: self._reveal(path))
        menu.addAction(reveal)

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _create_file(self, folder_path: str) -> None:
        name, ok = QInputDialog.getText(self, 'New File', 'File name:')
        if not ok or not name.strip():
            return
        target = Path(folder_path) / name
        try:
            target.write_text('', encoding='utf-8')
        except OSError as e:
            QMessageBox.critical(self, 'Error', f'Could not create file:\n{e}')
            return
        # refresh model for the folder so the new file appears
        try:
            self._model.setRootPath(str(folder_path))
        except Exception:
            try:
                self._model.directoryLoaded.emit(str(folder_path))
            except Exception:
                pass

    def _create_folder(self, folder_path: str) -> None:
        name, ok = QInputDialog.getText(self, 'New Folder', 'Folder name:')
        if not ok or not name.strip():
            return
        target = Path(folder_path) / name
        try:
            target.mkdir(parents=True, exist_ok=False)
        except OSError as e:
            QMessageBox.critical(self, 'Error', f'Could not create folder:\n{e}')
            return
        try:
            self._model.setRootPath(str(folder_path))
        except Exception:
            try:
                self._model.directoryLoaded.emit(str(folder_path))
            except Exception:
                pass

    def _rename(self, path: str) -> None:
        p = Path(path)
        new_name, ok = QInputDialog.getText(self, 'Rename', 'New name:', text=p.name)
        if not ok or not new_name.strip():
            return
        target = p.with_name(new_name)
        try:
            p.rename(target)
        except OSError as e:
            QMessageBox.critical(self, 'Error', f'Could not rename:\n{e}')
            return
        parent = str(p.parent)
        try:
            self._model.setRootPath(parent)
        except Exception:
            try:
                self._model.directoryLoaded.emit(parent)
            except Exception:
                pass

    def _delete(self, path: str) -> None:
        p = Path(path)
        choice = QMessageBox.question(self, 'Delete', f'Are you sure you want to delete {p}?', QMessageBox.Yes | QMessageBox.No)
        if choice != QMessageBox.Yes:
            return
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        except OSError as e:
            QMessageBox.critical(self, 'Error', f'Could not delete:\n{e}')
            return
        try:
            self._model.setRootPath(str(p.parent))
        except Exception:
            try:
                self._model.directoryLoaded.emit(str(p.parent))
            except Exception:
                pass

    def _copy_path(self, path: str) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(path)

    def _reveal(self, path: str) -> None:
        # Try platform-appropriate reveal
        try:
            if os.name == 'nt':
                subprocess.run(['explorer', '/select,', path])
            elif sys.platform == 'darwin':
                subprocess.run(['open', '-R', path])
            else:
                subprocess.run(['xdg-open', Path(path).parent])
        except Exception:
            QMessageBox.information(self, 'Reveal', f'Could not open file manager for {path}')

    def set_error_count(self, file_path: str, count: int) -> None:
        """Set the number of code issues for a file."""
        if count <= 0:
            self._error_counts.pop(file_path, None)
        else:
            self._error_counts[file_path] = count

        self._tree.viewport().update()