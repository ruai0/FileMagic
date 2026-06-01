from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel
from PyQt6.QtCore import Qt


class PluginPanel(QWidget):
    """插件导航面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("功能列表")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        self.plugin_list = QListWidget()
        layout.addWidget(self.plugin_list)
