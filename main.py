import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.app import ExcelToolsApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("办公工具箱")
    app.setOrganizationName("办公工具箱")
    app.setApplicationVersion("1.0.0")
    
    window = ExcelToolsApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
