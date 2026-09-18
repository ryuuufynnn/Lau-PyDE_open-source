import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import DARK_STYLESHEET, MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    window - MainWindow
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()