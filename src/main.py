from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    root_folder = sys.argv[1] if len(sys.argv) > 1 else None
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    window = MainWindow(root_folder)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
