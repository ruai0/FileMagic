import os
import subprocess
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """Word转PDF插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "Word转PDF"
        self.description = "将Word文档转为PDF"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.files = []
    
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
        
        file_group = QGroupBox("Word文件列表")
        file_layout = QVBoxLayout()
        
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["文件名", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加文件")
        add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(add_btn)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(clear_btn)
        file_layout.addLayout(btn_row)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(convert_btn)
        
        note_label = QLabel("注意：需要安装Microsoft Word或LibreOffice才能使用此功能")
        note_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(note_label)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_files_dropped(self, filepaths):
        for fp in filepaths:
            if fp.lower().endswith((".docx", ".doc")) and fp not in self.files:
                self.files.append(fp)
        self._update_table()
    
    def _on_add(self):
        filepaths = FileDialog.open_files(self._widget, "选择Word文件", "Word文件 (*.docx *.doc)")
        if filepaths:
            for fp in filepaths:
                if fp not in self.files:
                    self.files.append(fp)
            self._update_table()
    
    def _update_table(self):
        self.file_table.setRowCount(len(self.files))
        for row, fp in enumerate(self.files):
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(fp)))
            self.file_table.setItem(row, 1, QTableWidgetItem("就绪"))
    
    def _on_clear(self):
        self.files.clear()
        self.file_table.setRowCount(0)
    
    def _on_convert(self):
        if not self.files:
            QMessageBox.warning(self._widget, "警告", "请先添加Word文件")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("转换中...")
        progress.show()
        
        try:
            import docx2pdf
            total = len(self.files)
            
            for idx, fp in enumerate(self.files):
                progress.set_status(f"转换 {idx+1}/{total}: {os.path.basename(fp)}")
                progress.set_progress(int((idx / total) * 100))
                
                output_path = os.path.join(output_dir, os.path.splitext(os.path.basename(fp))[0] + ".pdf")
                docx2pdf.convert(fp, output_path)
                
                self.file_table.setItem(idx, 1, QTableWidgetItem("完成"))
                progress.add_log(f"已转换: {os.path.basename(fp)}")
            
            progress.complete("转换完成!")
            QMessageBox.information(self._widget, "成功", f"已转换 {total} 个文件")
        except ImportError:
            progress.close()
            QMessageBox.warning(self._widget, "提示", "请先安装docx2pdf:\npip install docx2pdf")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"转换失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"转换失败:\n{str(e)}")
