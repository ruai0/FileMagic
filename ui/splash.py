import sys
from PyQt6.QtWidgets import QSplashScreen, QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QRect


class SplashScreen(QSplashScreen):
    """启动画面"""
    
    def __init__(self):
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor("#1a1a2e"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QColor("#ffffff"))
        font = QFont("Microsoft YaHei", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, 80, 400, 50), Qt.AlignmentFlag.AlignCenter, "ExcelTools")
        
        painter.setPen(QColor("#888888"))
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.drawText(QRect(0, 140, 400, 30), Qt.AlignmentFlag.AlignCenter, "Excel多功能工具集")
        
        painter.setPen(QColor("#00d4aa"))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.drawText(QRect(0, 200, 400, 20), Qt.AlignmentFlag.AlignCenter, "正在加载...")
        
        painter.setPen(QColor("#444444"))
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        painter.drawText(QRect(0, 270, 400, 20), Qt.AlignmentFlag.AlignCenter, "v1.0.0 | 基于 Python + PyQt6")
        
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        
        self.message_label = QLabel(self)
        self.message_label.setStyleSheet("color: #888; font-size: 10px;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setGeometry(0, 240, 400, 20)
    
    def show_message(self, message: str):
        """显示加载信息"""
        self.message_label.setText(message)
        self.repaint()
    
    def finish(self):
        """关闭启动画面"""
        super().close()
