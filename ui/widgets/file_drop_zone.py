from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class FileDropZone(QWidget):
    """文件拖放区域"""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            FileDropZone {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            FileDropZone:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 40px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        text_label = QLabel("拖放文件到这里\n或点击选择文件")
        text_label.setStyleSheet("font-size: 14px; color: #666;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                FileDropZone {
                    border: 2px dashed #0078d4;
                    border-radius: 10px;
                    background-color: #e6f2ff;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """拖离事件"""
        self._reset_style()
    
    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        self._reset_style()
        
        filepaths = []
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            filepaths.append(filepath)
        
        if filepaths:
            self.files_dropped.emit(filepaths)
    
    def _reset_style(self):
        """重置样式"""
        self.setStyleSheet("""
            FileDropZone {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            FileDropZone:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
