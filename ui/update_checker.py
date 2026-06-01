import json
import urllib.request
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class UpdateChecker(QThread):
    """更新检查线程"""
    
    update_found = pyqtSignal(str, str)
    check_complete = pyqtSignal(bool, str)
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            url = "https://api.github.com/repos/your-repo/ExcelTools/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "ExcelTools"})
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "").lstrip("v")
                    
                    if self._version_compare(latest_version, self.current_version) > 0:
                        self.update_found.emit(latest_version, data.get("body", ""))
                    else:
                        self.check_complete.emit(True, "已是最新版本")
            except urllib.error.URLError:
                self.check_complete.emit(False, "无法连接到更新服务器")
            except Exception as e:
                self.check_complete.emit(False, f"检查失败: {str(e)}")
        
        except Exception as e:
            self.check_complete.emit(False, f"检查失败: {str(e)}")
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """比较版本号"""
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0


class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.setWindowTitle("检查更新")
        self.setMinimumSize(400, 300)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        version_label = QLabel(f"当前版本: v{self.current_version}")
        version_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(version_label)
        
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setStyleSheet("padding: 20px; color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.close_btn)
        
        self.update_btn = QPushButton("下载更新")
        self.update_btn.setStyleSheet("background-color: #00d4aa; color: white;")
        self.update_btn.setVisible(False)
        buttons_layout.addWidget(self.update_btn)
        
        layout.addLayout(buttons_layout)
        
        self.checker = UpdateChecker(self.current_version)
        self.checker.update_found.connect(self._on_update_found)
        self.checker.check_complete.connect(self._on_check_complete)
        self.checker.start()
    
    def _on_update_found(self, version: str, notes: str):
        """发现新版本"""
        self.status_label.setText(f"发现新版本: v{version}")
        self.status_label.setStyleSheet("padding: 20px; color: #00d4aa; font-weight: bold;")
        
        if notes:
            self.progress_label.setText(f"更新内容:\n{notes[:200]}...")
        
        self.update_btn.setVisible(True)
    
    def _on_check_complete(self, success: bool, message: str):
        """检查完成"""
        self.status_label.setText(message)
        if success:
            self.status_label.setStyleSheet("padding: 20px; color: #00d4aa;")
        else:
            self.status_label.setStyleSheet("padding: 20px; color: #ff6b6b;")
        
        self.close_btn.setFocus()
