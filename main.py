import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.app import FileMagicApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FileMagic")
    app.setOrganizationName("FileMagic")
    app.setApplicationVersion("1.0.0")
    
    window = FileMagicApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
