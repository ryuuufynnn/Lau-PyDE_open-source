from curses import window
import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from importlib import resources

from PySide6.QtWidgets import QApplication

from ui.main_window import DARK_STYLESHEET, MainWindow

PENGUIN_NAME = "Sissa"

def main():
    app = QApplication(sys.argv)
    # Prefer package resource lookup (works for installed package),
    # fall back to a filesystem path for source-tree runs.
    try:
        icon_path = None
        # resources.files requires a package; `assets` is packaged via
        # pyproject.toml and an __init__.py marker.
        logo_file = resources.files("assets").joinpath("logo.png")
        with resources.as_file(logo_file) as p:
            icon_path = p
        app.setWindowIcon(QIcon(str(icon_path)))
    except Exception:
        BASE_DIR = Path(__file__).resolve().parent
        ICON_PATH = BASE_DIR / "assets" / "logo.png"
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()