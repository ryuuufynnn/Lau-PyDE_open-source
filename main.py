from curses import window
import sys
from pathlib import Path
from PySide6.QtGui import QIcon

from PySide6.QtWidgets import QApplication

from ui.main_window import DARK_STYLESHEET, MainWindow

PENGUIN_NAME = "Sissa"

def main():
    app = QApplication(sys.argv)
    BASE_DIR = Path(__file__).resolve().parent
    ICON_PATH = BASE_DIR / "assets" / "lau-pyde_logo.jpg"

    app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()