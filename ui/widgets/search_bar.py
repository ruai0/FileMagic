from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class SearchBar(QWidget):
    """搜索栏"""
    
    search_changed = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        self._setup_ui(placeholder)
    
    def _setup_ui(self, placeholder: str):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)
    
    def get_text(self) -> str:
        """获取搜索文本"""
        return self.search_input.text()
    
    def set_text(self, text: str):
        """设置搜索文本"""
        self.search_input.setText(text)
    
    def clear(self):
        """清除搜索文本"""
        self.search_input.clear()
