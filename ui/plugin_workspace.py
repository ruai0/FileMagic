from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt


class PluginWorkspace(QWidget):
    """插件工作区"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
    
    def add_widget(self, widget):
        """添加组件到工作区"""
        return self.stack.addWidget(widget)
    
    def set_current_index(self, index):
        """设置当前显示的组件"""
        self.stack.setCurrentIndex(index)
