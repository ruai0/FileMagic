from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class ProgressDialog(QDialog):
    """进度对话框"""
    
    def __init__(self, title: str = "处理中", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        self.setModal(True)
        self._setup_ui()
        self._cancelled = False
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("准备中...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        buttons_layout = QVBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def set_status(self, text: str):
        """设置状态文本"""
        self.status_label.setText(text)
    
    def set_progress(self, value: int):
        """设置进度值"""
        self.progress_bar.setValue(value)
    
    def add_log(self, message: str):
        """添加日志信息"""
        self.log_text.append(message)
    
    def _on_cancel(self):
        """取消操作"""
        self._cancelled = True
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("正在取消...")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled
    
    def complete(self, message: str = "完成"):
        """完成操作"""
        self.progress_bar.setValue(100)
        self.status_label.setText(message)
        self.cancel_btn.setText("关闭")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)
