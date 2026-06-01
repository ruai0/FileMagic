import os
from typing import Dict, Any, List, Optional
import fitz
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QSpinBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """PDF转图片插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF转图片"
        self.description = "将PDF页面转为PNG/JPG图片"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
        self.total_pages = 0
    
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
        
        opts_group = QGroupBox("转换选项")
        opts_layout = QVBoxLayout()
        
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("图片格式:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PNG", "JPG"])
        fmt_layout.addWidget(self.fmt_combo)
        opts_layout.addLayout(fmt_layout)
        
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI(清晰度):"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 300)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSingleStep(25)
        dpi_layout.addWidget(self.dpi_spin)
        opts_layout.addLayout(dpi_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(convert_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self._load_info()
    
    def _load_info(self):
        try:
            doc = fitz.open(self.source_file)
            self.total_pages = doc.page_count
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)} ({self.total_pages} 页)")
            doc.close()
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _on_convert(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("转换中...")
        progress.show()
        
        try:
            doc = fitz.open(self.source_file)
            fmt = self.fmt_combo.currentText().lower()
            dpi = self.dpi_spin.value()
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            base_name = os.path.splitext(os.path.basename(self.source_file))[0]
            
            for i in range(doc.page_count):
                progress.set_status(f"转换页 {i+1}/{doc.page_count}")
                progress.set_progress(int((i / doc.page_count) * 100))
                
                page = doc[i]
                pix = page.get_pixmap(matrix=mat)
                
                output_path = os.path.join(output_dir, f"{base_name}_page{i+1:03d}.{fmt}")
                pix.save(output_path)
                progress.add_log(f"已保存: {output_path}")
            
            doc.close()
            progress.complete("转换完成!")
            self.log_panel.info(f"已转换 {doc.page_count} 页为图片")
            QMessageBox.information(self._widget, "成功", f"已转换 {doc.page_count} 页为图片")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"转换失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"转换失败:\n{str(e)}")
