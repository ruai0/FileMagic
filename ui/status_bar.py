from PyQt6.QtWidgets import QStatusBar


class StatusBar(QStatusBar):
    """状态栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.showMessage("就绪")
