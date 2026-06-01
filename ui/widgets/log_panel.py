from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from datetime import datetime


class LogPanel(QWidget):
    """日志面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setMaximumHeight(150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        
        title = QLabel("日志")
        title.setStyleSheet("font-weight: bold; padding: 5px;")
        header.addWidget(title)
        
        header.addStretch()
        
        clear_btn = QLabel("清除")
        clear_btn.setStyleSheet("color: #0078d4; padding: 5px; cursor: pointer;")
        clear_btn.mousePressEvent = lambda e: self.clear()
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.log_text)
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "DEBUG": "#666",
            "INFO": "#000",
            "WARNING": "#ff9900",
            "ERROR": "#ff0000",
            "CRITICAL": "#cc0000"
        }
        
        color = colors.get(level, "#000")
        
        html = f'<span style="color: #999;">[{timestamp}]</span> '
        html += f'<span style="color: {color};">[{level}]</span> '
        html += f'<span>{message}</span>'
        
        self.log_text.append(html)
    
    def debug(self, message: str):
        """添加调试日志"""
        self.add_log(message, "DEBUG")
    
    def info(self, message: str):
        """添加信息日志"""
        self.add_log(message, "INFO")
    
    def warning(self, message: str):
        """添加警告日志"""
        self.add_log(message, "WARNING")
    
    def error(self, message: str):
        """添加错误日志"""
        self.add_log(message, "ERROR")
    
    def critical(self, message: str):
        """添加严重错误日志"""
        self.add_log(message, "CRITICAL")
    
    def clear(self):
        """清除日志"""
        self.log_text.clear()
