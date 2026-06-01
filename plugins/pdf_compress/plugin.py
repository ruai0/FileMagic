import os
import fitz
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """PDF压缩插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF压缩"
        self.description = "压缩PDF文件大小"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context = None
        self.source_file = None
    
    def initialize(self, context):
        super().initialize(context)
        self._context = context
    
    def get_widget(self):
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget
    
    def _create_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        file_group = QGroupBox("源PDF文件")
        file_layout = QVBoxLayout()
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_file_dropped)
        file_layout.addWidget(self.drop_zone)
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("padding: 10px; color: #666;")
        file_layout.addWidget(self.file_label)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("压缩选项")
        opts_layout = QVBoxLayout()
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("压缩质量:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["低（更小文件）", "中（平衡）", "高（更清晰）"])
        self.quality_combo.setCurrentIndex(1)
        quality_layout.addWidget(self.quality_combo)
        opts_layout.addLayout(quality_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        compress_btn = QPushButton("开始压缩")
        compress_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        compress_btn.clicked.connect(self._on_compress)
        layout.addWidget(compress_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            size = os.path.getsize(self.source_file) / 1024 / 1024
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)} ({size:.2f} MB)")
    
    def _on_compress(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        output_path = FileDialog.save_file(self._widget, "保存压缩PDF", "PDF文件 (*.pdf)", ".pdf")
        if not output_path:
            return
        
        try:
            original_size = os.path.getsize(self.source_file)
            
            quality = self.quality_combo.currentIndex()
            garbage = [4, 3, 2][quality]
            deflate = [True, True, False][quality]
            
            doc = fitz.open(self.source_file)
            
            for page in doc:
                pix = page.get_pixmap()
                page.set_pixmap(pix)
            
            doc.save(output_path, garbage=garbage, deflate=deflate)
            doc.close()
            
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / original_size) * 100
            
            self.log_panel.info(f"原始大小: {original_size / 1024:.2f} KB")
            self.log_panel.info(f"压缩后: {compressed_size / 1024:.2f} KB")
            self.log_panel.info(f"压缩率: {reduction:.1f}%")
            
            QMessageBox.information(self._widget, "成功", 
                f"压缩完成!\n\n"
                f"原始大小: {original_size / 1024:.2f} KB\n"
                f"压缩后: {compressed_size / 1024:.2f} KB\n"
                f"减小: {reduction:.1f}%")
        except Exception as e:
            self.log_panel.error(f"压缩失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"压缩失败:\n{str(e)}")
