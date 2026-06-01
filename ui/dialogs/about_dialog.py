from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 ExcelTools")
        self.setMinimumSize(350, 250)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ExcelTools")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("版本 1.0.0")
        version.setStyleSheet("font-size: 14px; color: #666;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        description = QLabel("Excel多功能工具集\n基于 Python + PyQt6 开发")
        description.setStyleSheet("font-size: 12px; padding: 20px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        features = QLabel(
            "支持功能:\n"
            "- 文件合并\n"
            "- 文件拆分\n"
            "- 数据清洗\n"
            "- 格式转换\n"
            "- 数据分析\n"
            "- 批量处理"
        )
        features.setStyleSheet("font-size: 11px; padding: 10px;")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
