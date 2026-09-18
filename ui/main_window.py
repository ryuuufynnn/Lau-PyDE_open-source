from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit 
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.file_manager import read_file, write_file
from core.runner import PythonRunner
from ui.editor import CodeEditor
from ui.explorer import FileExplorer
from ui.terminal import TerminalPanel

APP_NAME = "Lau-PyDE"
APP_VERSION = "0.0.1"

DARK_STYLESHEET = """

QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-size: 13px
}

QPlainTextEdit, QLineEdit, QTreeView {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
}

QMenuBar {
    background-color: #2d2d2d;
}

QMenuBar::item:selected {
    background-color: #3c3c3c;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #3c3c3c;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
}

QTabBar::tab {
    background-color: #2d2d2d;
    padding: 6px 12px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
}

QStatusBar {
    background-color: #2d2d2d;
}

QSplitter::handle {
    background-color: #3c3c3c;
}

"""

class MainWindow(QMainWindow):
    """The PyDE main window: menu bar + explorer + editor + output/terminal."""

    def __init__(self):
        super().__init__()

        # which file is currently open, and which folder is the workspace
        # (used by the explorer, the terminal, and as the working
        # directory when running a file).
        self._current_file_path: Optional[str] = None
        self._current_folder: Optional[str] = None

        self.resize(1200, 800)

        self._build_widgets()
        self._build_layout()
        self._build_menu_and_shortcuts()

        self.statusBar().showMessage("Ready")
        self._update_title()

    # main setup
    def _build_widgets(self) -> None:
        self.editor = CodeEditor()
        self.editor.document().modificationChanged.connect(self._on_modification_changed)

        self.explorer = FileExplorer()
        self.explorer.file_double_clicked.connect(self.open_file)

        self.output_panel = QPlainTextEdit()
        self.output_panel.setReadOnly(True)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter input...")
        self.input_box.returnPressed.connect(self.send_input)

        self.terminal_panel = TerminalPanel()

        self._runner = PythonRunner()
        self._runner.output_ready.connect(self._append_output)
        self._runner.finished.connect(self._on_run_finished)

    def send_input(self):
        text = self.input_box.text()
        if not text:
            return
        self._runner.write_input(text + "\n")
        self.input_box.clear()

    def _build_layout(self) -> None:
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(self.output_panel)
        output_layout.addWidget(self.input_box)

        bottom_tabs = QTabWidget()
        bottom_tabs.addTab(output_container, "Output")
        bottom_tabs.addTab(self.terminal_panel, "Terminal")
        self._bottom_tabs = bottom_tabs

        # vertical splitter: editor on top, Output/Terminal tabs below.
        editor_and_output = QSplitter(Qt.Vertical)
        editor_and_output.addWidget(self.editor)
        editor_and_output.addWidget(bottom_tabs)
        editor_and_output.setStretchFactor(0, 3)
        editor_and_output.setStretchFactor(1, 1)

        # horizontal splitter: explorer sidebar on the left, everything
        # else on the right. QSplitter lets the user drag to resize.
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.explorer)
        main_splitter.addWidget(editor_and_output)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([220, 980])

        self.setCentralWidget(main_splitter)

    def _build_menu_and_shortcuts(self) -> None:
        """
        Build the menu bar.

        Each menu item is a QAction, which bundles together a label,
        a keyboard shortcut, and what happens when it's triggered (its
        `triggered` signal). The same QAction could also be reused on
        a toolbar, though v0.1 only uses menus.
        """
        menu_bar = self.menuBar()

        # file menu
        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("New File", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open File...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

        open_folder_action = QAction("Open Folder...", self)
        open_folder_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # edit menu
        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # --- Run menu ---
        run_menu = menu_bar.addMenu("&Run")

        run_action = QAction("Run File", self)
        run_action.setShortcut(QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.run_file)
        run_menu.addAction(run_action)

        # --- Terminal menu ---
        terminal_menu = menu_bar.addMenu("&Terminal")

        focus_terminal_action = QAction("Focus Terminal", self)
        focus_terminal_action.triggered.connect(self._focus_terminal)
        terminal_menu.addAction(focus_terminal_action)

    # ---- File operations ---------------------------------------------------

    def new_file(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.editor.clear()
        self._current_file_path = None
        self.editor.document().setModified(False)
        self._update_title()
        self.statusBar().showMessage("New file")

    def open_file_dialog(self) -> None:
        if not self._confirm_discard_changes():
            return
        start_dir = self._current_folder or str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", start_dir, "Python Files (*.py);;All Files (*)"
        )
        if path:
            self.open_file(path)

    def open_file(self, path: str) -> None:
        """Open a specific file path in the editor. Used both by the
        Open dialog and by double-clicking a file in the explorer."""
        try:
            content = read_file(path)
        except OSError as error:
            QMessageBox.critical(self, APP_NAME, f"Could not open file:\n{path}\n\n{error}")
            return

        self.editor.setPlainText(content)
        self._current_file_path = path
        self.editor.document().setModified(False)
        self._update_title()
        self.statusBar().showMessage(f"Opened {path}")

    def open_folder_dialog(self) -> None:
        start_dir = self._current_folder or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", start_dir)
        if folder:
            self._current_folder = folder
            self.explorer.set_root_folder(folder)
            self.terminal_panel.set_working_directory(folder)
            self.statusBar().showMessage(f"Workspace: {folder}")

    def save_file(self) -> bool:
        """Save to the current file path, prompting for one if there isn't one yet.
        Returns True if the file ended up saved, False if the user cancelled."""
        if self._current_file_path is None:
            return self.save_file_as()

        try:
            write_file(self._current_file_path, self.editor.toPlainText())
        except OSError as error:
            QMessageBox.critical(
                self, APP_NAME, f"Could not save file:\n{self._current_file_path}\n\n{error}"
            )
            return False

        self.editor.document().setModified(False)
        self._update_title()
        self.statusBar().showMessage(f"Saved {self._current_file_path}")
        return True

    def save_file_as(self) -> bool:
        start_dir = self._current_folder or str(Path.home())
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", start_dir, "Python Files (*.py);;All Files (*)"
        )
        if not path:
            return False
        self._current_file_path = path
        return self.save_file()

    def _confirm_discard_changes(self) -> bool:
        """If there are unsaved changes, ask what to do.
        Returns True if it's OK to proceed, False to cancel the action."""
        if not self.editor.document().isModified():
            return True

        choice = QMessageBox.question(
            self,
            APP_NAME,
            "This file has unsaved changes. Save before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if choice == QMessageBox.Save:
            return self.save_file()
        return choice == QMessageBox.Discard

    # ---- Run ----------------------------------------------------------------

    def run_file(self) -> None:
        if self._runner.is_running():
            QMessageBox.information(self, APP_NAME, "A program is already running.")
            return

        # the file has to exist on disk before we can run it as a file,
        # so save first (prompting for a location if it's a new file).
        if self._current_file_path is None or self.editor.document().isModified():
            if not self.save_file():
                return  # user cancelled the save

        working_dir = self._current_folder or str(Path(self._current_file_path).parent)

        self.output_panel.clear()
        self._bottom_tabs.setCurrentWidget(self.output_panel)
        self._append_output(f"Running {self._current_file_path}\n\n")

        self._runner.run_file(self._current_file_path, working_dir)
        self.statusBar().showMessage("Running...")

    def _append_output(self, text: str) -> None:
        self.output_panel.moveCursor(QTextCursor.End)
        self.output_panel.insertPlainText(text)

    def _on_run_finished(self, exit_code: int) -> None:
        self._append_output(f"\nProcess finished with exit code {exit_code}.\n")
        self.statusBar().showMessage("Ready")

    def _focus_terminal(self) -> None:
        self._bottom_tabs.setCurrentWidget(self.terminal_panel)

    # misc

    def _on_modification_changed(self, _modified: bool) -> None:
        self._update_title()

    def _update_title(self) -> None:
        name = Path(self._current_file_path).name if self._current_file_path else "Untitled"
        star = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{star}{name} — {APP_NAME}")

    def closeEvent(self, event) -> None:
        """Called automatically by Qt when the user tries to close the window."""
        if not self._confirm_discard_changes():
            event.ignore()
            return

        if self._runner.is_running():
            choice = QMessageBox.question(
                self,
                APP_NAME,
                "A program is still running. Stop it and quit?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if choice != QMessageBox.Yes:
                event.ignore()
                return
            self._runner.stop()

        event.accept()
