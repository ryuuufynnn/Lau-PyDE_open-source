from pathlib import Path
import json
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
)

from core.file_manager import read_file, write_file
from core.runner import PythonRunner
from ui.editor import CodeEditor
from ui.explorer import FileExplorer
from ui.inline_output import InlineInputOutput
from ui.terminal import TerminalPanel

APP_NAME = "Lau-PyDE"
APP_VERSION = "0.0.1"

RECENT_PROJECT_FILE = Path.home() / ".lau_pyde_recent.json"

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
        self._maximized_pane: Optional[str] = None
        self._explorer_minimized = False
        self._bottom_minimized = False

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

        # starting code for the welcome message
        # Welcome screen
        self._editor_stack = QStackedWidget()

        self._welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self._welcome_widget)
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(8)

        # Title
        welcome_title = QLabel("Welcome to Lau-PyDE")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setStyleSheet(
            "font-size: 24px;"
            "font-weight: bold;"
        )

        # Subtitle
        welcome_subtitle = QLabel(
            "A simple and lightweight Python Development Environment"
        )
        welcome_subtitle.setAlignment(Qt.AlignCenter)
        welcome_subtitle.setStyleSheet(
            "font-size: 12px;"
        )

        # Get Started title
        welcome_get_started_title = QLabel("Get Started with these commands")
        welcome_get_started_title.setAlignment(Qt.AlignCenter)
        welcome_get_started_title.setStyleSheet(
            "font-size: 14px;"
            "font-weight: bold;"
        )

        # Commands
        welcome_new_file = QLabel("Ctrl+N    |    New File")
        welcome_open_file = QLabel("Ctrl+O    |    Open File")
        welcome_open_folder = QLabel("Ctrl+L    |    Open Folder")

        for label in (
            welcome_new_file,
            welcome_open_file,
            welcome_open_folder,
        ):
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 13px;")

        # Ending message
        welcome_footer = QLabel("Enjoy using Lau-PyDE. Happy coding!")
        welcome_footer.setAlignment(Qt.AlignCenter)
        welcome_footer.setStyleSheet("font-size: 13px;")

        # Add everything
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)

        welcome_layout.addSpacing(24)

        welcome_layout.addWidget(welcome_get_started_title)
        welcome_layout.addWidget(welcome_new_file)
        welcome_layout.addWidget(welcome_open_file)
        welcome_layout.addWidget(welcome_open_folder)

        welcome_layout.addSpacing(24)

        welcome_layout.addWidget(welcome_footer)
        self._editor_stack.addWidget(self._welcome_widget)
        self._editor_stack.addWidget(self.editor)
        self._editor_stack.setCurrentWidget(self._welcome_widget)

        # self.explorer = FileExplorer()
        # self.load_recent_project()
        # self.explorer.file_double_clicked.connect(self.open_file)
        self.explorer = FileExplorer()
        self.explorer.set_root_folder(None)

        self.load_recent_project()
        self.explorer.file_double_clicked.connect(self.open_file)

        self.output_panel = InlineInputOutput()
        self.output_panel.input_submitted.connect(self.send_input)
        self._active_prompt = ""
        self._output_line_tail = ""

        self.terminal_panel = TerminalPanel()
        self.terminal_panel.minimize_requested.connect(self._minimize_bottom_panel)
        self.terminal_panel.maximize_requested.connect(
            lambda: self._maximize_pane("terminal")
        )

        self.explorer.minimize_requested.connect(self._minimize_explorer)
        self.explorer.maximize_requested.connect(lambda: self._maximize_pane("explorer"))

        self._runner = PythonRunner()
        self._runner.output_ready.connect(self._append_output)
        self._runner.finished.connect(self._on_run_finished)

    def send_input(self, text: str) -> None:
        if not self._runner.is_running():
            return
            
        # self.output_panel.insertPlainText(text)
        self.output_panel.stop_input()
        self._active_prompt = ""

        self._runner.write_input(text + "\n")

    def _build_layout(self) -> None:
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(4, 4, 4, 4)

        output_title = QWidget()
        output_title_layout = QHBoxLayout(output_title)
        output_title_layout.setContentsMargins(0, 0, 0, 0)
        output_title_layout.addWidget(QLabel("Output"))
        output_title_layout.addStretch()

        # replace textual Stop with a compact stop icon button
        self._stop_running_button = QPushButton("⏹")
        self._stop_running_button.setToolTip("Stop the running Python program")
        self._stop_running_button.setEnabled(False)
        self._stop_running_button.clicked.connect(self.stop_running)
        self._stop_running_button.setStyleSheet("border: none; min-height: 24px;")
        output_title_layout.addWidget(self._stop_running_button)

        output_minimize_button = QPushButton("▁")
        output_maximize_button = QPushButton("▢")
        output_minimize_button.setToolTip("Minimize output and terminal")
        output_maximize_button.setToolTip("Maximize or restore output")
        output_minimize_button.setFixedWidth(32)
        output_maximize_button.setFixedWidth(32)
        output_minimize_button.clicked.connect(self._minimize_bottom_panel)
        output_maximize_button.clicked.connect(lambda: self._maximize_pane("output"))
        # remove button borders for a sleeker look
        output_minimize_button.setStyleSheet("border: none; min-height: 24px;")
        output_maximize_button.setStyleSheet("border: none; min-height: 24px;")
        output_title_layout.addWidget(output_minimize_button)
        output_title_layout.addWidget(output_maximize_button)

        output_layout.addWidget(output_title)
        output_layout.addWidget(self.output_panel)

        bottom_tabs = QTabWidget()
        bottom_tabs.addTab(output_container, "Output")
        bottom_tabs.addTab(self.terminal_panel, "Terminal")
        self._bottom_tabs = bottom_tabs
        self._output_container = output_container

        # vertical splitter: editor on top, Output/Terminal tabs below.
        editor_and_output = QSplitter(Qt.Vertical)
        editor_and_output.addWidget(self._editor_stack) # pinalitan ko from self.editor to self.editor_stack
        editor_and_output.addWidget(bottom_tabs)
        editor_and_output.setStretchFactor(0, 3)
        editor_and_output.setStretchFactor(1, 1)
        self._editor_and_output = editor_and_output

        # horizontal splitter: explorer sidebar on the left, everything
        # else on the right. QSplitter lets the user drag to resize.
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.explorer)
        main_splitter.addWidget(editor_and_output)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([220, 980])
        self._main_splitter = main_splitter

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
        open_folder_action.setShortcut(QKeySequence("Ctrl+L"))
        open_folder_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_folder_action)

        close_project_action = QAction("Close Project", self)
        close_project_action.setShortcut(QKeySequence("Ctrl+P"))
        close_project_action.triggered.connect(self.close_project)
        file_menu.addAction(close_project_action)

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
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
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

        # run menu
        run_menu = menu_bar.addMenu("&Run")

        run_action = QAction("Run File", self)
        run_action.setShortcut(QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.run_file)
        run_menu.addAction(run_action)

        self._stop_running_action = QAction("Stop Running", self)
        self._stop_running_action.setShortcut(QKeySequence("Ctrl+."))
        self._stop_running_action.setEnabled(False)
        self._stop_running_action.triggered.connect(self.stop_running)
        run_menu.addAction(self._stop_running_action)

        # view menu
        view_menu = menu_bar.addMenu("&View")

        show_explorer_action = QAction("Show Explorer", self)
        show_explorer_action.triggered.connect(self._show_explorer)
        view_menu.addAction(show_explorer_action)

        show_output_action = QAction("Show Output", self)
        show_output_action.triggered.connect(lambda: self._show_bottom_panel("output"))
        view_menu.addAction(show_output_action)

        show_terminal_action = QAction("Show Terminal", self)
        show_terminal_action.setShortcut(QKeySequence("Ctrl+T"))
        show_terminal_action.triggered.connect(lambda: self._show_bottom_panel("terminal"))
        view_menu.addAction(show_terminal_action)

        restore_layout_action = QAction("Restore Layout", self)
        restore_layout_action.triggered.connect(self._restore_layout)
        view_menu.addAction(restore_layout_action)

        # termnal layout
        terminal_menu = menu_bar.addMenu("&Terminal")

        focus_terminal_action = QAction("Focus Terminal", self)
        focus_terminal_action.triggered.connect(self._focus_terminal)
        terminal_menu.addAction(focus_terminal_action)

    # file operations
    def new_file(self) -> None:
        if not self._confirm_discard_changes():
            return

        self.editor.clear()
        self._show_editor()
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

        self._show_editor()
        self.editor.setPlainText(content)
        self._current_file_path = path
        self.editor.document().setModified(False)
        self._update_title()
        self.statusBar().showMessage(f"Opened {path}")

    def open_folder_dialog(self) -> None:
        start_dir = self._current_folder or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", start_dir)

        if folder:
            # self._current_folder = folder
            # # self.explorer.set_root_folder(folder)
            self.terminal_panel.set_working_directory(folder)
            # self.statusBar().showMessage(f"Workspace: {folder}")
            self._current_folder = folder
            self.explorer.set_root_folder(folder)
            self.terminal_panel.set_working_directory(folder)

            RECENT_PROJECT_FILE.write_text(
                json.dumps({"project": folder})
            )
            self.statusBar().showMessage(f"Workspace: {folder}")
        self._show_editor()

    def close_project(self) -> None:
        """Close the current project workspace."""
        self._current_folder = None
        self._current_file_path = None

        

        # remove the current project folder from the IDE and set to None
        self.explorer.set_root_folder(None)

        if RECENT_PROJECT_FILE.exists():
            try:
                RECENT_PROJECT_FILE.unlink()
            except OSError:
                pass

        self._show_welcome()
        self.editor.clear()
        self.explorer.hide()

        self._update_title()
        self.statusBar().showMessage("Project closed")

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

    def load_recent_project(self) -> None:
        if not RECENT_PROJECT_FILE.exists():
            return
        try:
            data = json.loads(RECENT_PROJECT_FILE.read_text())
            folder = data.get("project")

            if folder and Path(folder).is_dir():
                self._current_folder = folder
                self.explorer.set_root_folder(folder)
                
        except (json.JSONDecodeError, OSError):
            pass

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

    # run
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

        self._output_line_tail = ""
        self.output_panel.clear()
        self.output_panel.stop_input()
        self._show_bottom_panel("output")
        self._append_output(f"Running at {self._current_file_path}\n")

        self._runner.run_file(self._current_file_path, working_dir)
        self._set_running_controls(True)
        self.statusBar().showMessage("status: running...")

    def stop_running(self) -> None:
        """Kill the program currently being run from the editor."""
        if not self._runner.is_running():
            return

        self.output_panel.stop_input()
        self._active_prompt = ""
        self._runner.stop()
        self._append_output("\nCode stop running successfully.")
        self.statusBar().showMessage("Killed")

    def _set_running_controls(self, running: bool) -> None:
        self._stop_running_button.setEnabled(running)
        self._stop_running_action.setEnabled(running)

    def _append_output(self, text: str) -> None:
        self.output_panel.moveCursor(QTextCursor.End)
        self.output_panel.insertPlainText(text)

        # keep the unfinished line so a prompt split across process output
        # chunks (for example, "Enter your" + " name: ") is still detected.
        self._output_line_tail = (self._output_line_tail + text).rsplit("\n", 1)[-1]

        if not text or self._runner is None or not self._runner.is_running():
            return

        last_line = self._output_line_tail.rstrip()
        if not last_line:
            return

        prompt = last_line.strip()
        if prompt.endswith(":") or prompt.endswith("?") or prompt.endswith(">"):
            if prompt != self._active_prompt:
                self._active_prompt = prompt
                self.output_panel.start_input()

    def _on_run_finished(self, exit_code: int) -> None:
        self._active_prompt = ""
        self._output_line_tail = ""
        self.output_panel.stop_input()
        self._append_output(f"Process finished with exit code {exit_code}. Thank You for using Lau-PyDE!\n")
        self._set_running_controls(False)
        self.statusBar().showMessage("status: ready")

    # pane layout
    def _minimize_bottom_panel(self) -> None:
        self._restore_layout()
        self._bottom_minimized = True
        self._bottom_tabs.hide()
        self.statusBar().showMessage("Output and terminal minimized. Use View to show them.")

    def _minimize_explorer(self) -> None:
        self._restore_layout()
        self._explorer_minimized = True
        self.explorer.hide()
        self.statusBar().showMessage("Explorer minimized. Use View to show it.")

    def _maximize_pane(self, pane: str) -> None:
        if self._maximized_pane == pane:
            self._restore_layout()
            return

        if pane == "explorer":
            self._explorer_minimized = False
        else:
            self._bottom_minimized = False

        self._restore_layout()
        self._maximized_pane = pane
        self._bottom_tabs.tabBar().hide()

        if pane == "explorer":
            self.explorer.show()
            self._editor_and_output.hide()
            self._main_splitter.setSizes([self.width(), 0])
        else:
            self.explorer.hide()
            self.editor.hide()
            self._bottom_tabs.show()
            self._bottom_tabs.setCurrentWidget(
                self._output_container if pane == "output" else self.terminal_panel
            )
            self._editor_and_output.setSizes([0, self.height()])
            self._main_splitter.setSizes([0, self.width()])
            if pane == "terminal":
                self.terminal_panel.focus_input()

    def _restore_layout(self) -> None:
        self._maximized_pane = None
        self._editor_and_output.show()
        self.editor.show()
        self.explorer.setVisible(not self._explorer_minimized)
        self._bottom_tabs.setVisible(not self._bottom_minimized)
        self._bottom_tabs.tabBar().show()
        self._main_splitter.setSizes([220, max(1, self.width() - 220)])
        if not self._bottom_minimized:
            self._editor_and_output.setSizes([max(1, self.height() - 260), 260])

    def _show_explorer(self) -> None:
        self._restore_layout()
        self._explorer_minimized = False
        self.explorer.show()

    # shwow welcome message method
    def _show_welcome(self) -> None:
       self._editor_stack.setCurrentWidget(self._welcome_widget)   

    def _show_editor(self) -> None:
        self._editor_stack.setCurrentWidget(self.editor)

    def _show_bottom_panel(self, pane: str) -> None:
        self._restore_layout()
        self._bottom_minimized = False
        self._bottom_tabs.show()
        self._bottom_tabs.setCurrentWidget(
            self._output_container if pane == "output" else self.terminal_panel
        )
        if pane == "terminal":
            self.terminal_panel.focus_input()

    def _focus_terminal(self) -> None:
        self._show_bottom_panel("terminal")

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
