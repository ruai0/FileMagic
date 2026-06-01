from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExcelTools")
        self.setMinimumSize(1200, 800)
