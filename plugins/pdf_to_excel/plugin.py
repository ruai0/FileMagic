import os
import pandas as pd
import pdfplumber
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """PDF转Excel插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF转Excel"
        self.description = "提取PDF表格数据到Excel"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context = None
        self.source_file = None
        self.tables = []
    
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
        
        preview_group = QGroupBox("提取预览")
        preview_layout = QVBoxLayout()
        self.data_table = DataTable()
        preview_layout.addWidget(self.data_table)
        self.result_label = QLabel("共 0 个表格")
        self.result_label.setStyleSheet("padding: 5px; color: #666;")
        preview_layout.addWidget(self.result_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        exec_layout = QHBoxLayout()
        extract_btn = QPushButton("提取表格")
        extract_btn.clicked.connect(self._on_extract)
        exec_layout.addWidget(extract_btn)
        export_btn = QPushButton("导出到Excel")
        export_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 8px;")
        export_btn.clicked.connect(self._on_export)
        exec_layout.addWidget(export_btn)
        layout.addLayout(exec_layout)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
    
    def _on_extract(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        try:
            self.tables = []
            with pdfplumber.open(self.source_file) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for j, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            self.tables.append({
                                "page": i + 1,
                                "data": table
                            })
            
            if self.tables:
                first_table = self.tables[0]["data"]
                headers = first_table[0] if first_table else []
                data = first_table[1:] if len(first_table) > 1 else []
                self.data_table.load_data(headers, data)
                self.result_label.setText(f"共 {len(self.tables)} 个表格")
                self.log_panel.info(f"提取到 {len(self.tables)} 个表格")
            else:
                self.data_table.load_data(["提示"], [["未找到表格"]])
                self.log_panel.info("未找到表格")
        except Exception as e:
            self.log_panel.error(f"提取失败: {str(e)}")
    
    def _on_export(self):
        if not self.tables:
            QMessageBox.warning(self._widget, "警告", "请先提取表格")
            return
        
        output_path = FileDialog.save_excel(self._widget, "保存Excel文件")
        if not output_path:
            return
        
        try:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for idx, table_info in enumerate(self.tables):
                    data = table_info["data"]
                    if data and len(data) > 0:
                        headers = data[0]
                        rows = data[1:]
                        df = pd.DataFrame(rows, columns=headers)
                        sheet_name = f"表格{idx + 1}_页{table_info['page']}"
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            
            self.log_panel.info(f"已导出: {output_path}")
            QMessageBox.information(self._widget, "成功", f"已导出 {len(self.tables)} 个表格到Excel")
        except Exception as e:
            self.log_panel.error(f"导出失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"导出失败:\n{str(e)}")
