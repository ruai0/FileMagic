import os
from typing import Dict, Any, Optional
import fitz
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
    QLineEdit, QSpinBox, QColorDialog
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """PDF水印插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF水印"
        self.description = "给PDF添加文字水印"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
        self.watermark_color = (0.8, 0.8, 0.8)
    
    def initialize(self, context: Dict[str, Any]) -> None:
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
        
        opts_group = QGroupBox("水印设置")
        opts_layout = QVBoxLayout()
        
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("水印文字:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入水印文字")
        self.text_input.setText("机密文件")
        text_layout.addWidget(self.text_input)
        opts_layout.addLayout(text_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字体大小:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 100)
        self.size_spin.setValue(50)
        size_layout.addWidget(self.size_spin)
        
        size_layout.addWidget(QLabel("透明度:"))
        self.alpha_spin = QSpinBox()
        self.alpha_spin.setRange(10, 100)
        self.alpha_spin.setValue(30)
        self.alpha_spin.setSuffix("%")
        size_layout.addWidget(self.alpha_spin)
        opts_layout.addLayout(size_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        add_btn = QPushButton("添加水印")
        add_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        add_btn.clicked.connect(self._on_add_watermark)
        layout.addWidget(add_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
    
    def _on_add_watermark(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        output_path = FileDialog.save_file(self._widget, "保存水印PDF", "PDF文件 (*.pdf)", ".pdf")
        if not output_path:
            return
        
        progress = ProgressDialog("添加水印中...")
        progress.show()
        
        try:
            text = self.text_input.text()
            size = self.size_spin.value()
            alpha = self.alpha_spin.value() / 100
            
            doc = fitz.open(self.source_file)
            
            for i in range(doc.page_count):
                progress.set_status(f"处理页 {i+1}/{doc.page_count}")
                progress.set_progress(int((i / doc.page_count) * 100))
                
                page = doc[i]
                rect = page.rect
                
                tw = fitz.TextWriter(page.rect)
                font = fitz.Font("helv")
                
                x = rect.width / 2 - size * len(text) / 4
                y = rect.height / 2
                
                tw.append((x, y), text, font=font, fontsize=size)
                
                page.draw_text(
                    (x, y),
                    text,
                    fontsize=size,
                    fontname="helv",
                    color=(0.5, 0.5, 0.5),
                    rotate=45,
                    overlay=True,
                    fill_opacity=alpha
                )
            
            doc.save(output_path)
            doc.close()
            
            progress.complete("水印添加完成!")
            self.log_panel.info(f"已添加水印: {output_path}")
            QMessageBox.information(self._widget, "成功", "水印添加完成")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"添加水印失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"添加水印失败:\n{str(e)}")
