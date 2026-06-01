import os
from typing import Dict, Any, List, Optional
import pdfplumber
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """PDF提取插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF提取"
        self.description = "提取PDF中的文字和表格"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
    
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
        
        opts_group = QGroupBox("提取选项")
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("提取类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["提取文字", "提取表格", "提取全部"])
        opts_layout.addWidget(self.type_combo)
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        extract_btn = QPushButton("开始提取")
        extract_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        extract_btn.clicked.connect(self._on_extract)
        layout.addWidget(extract_btn)
        
        self.result_tabs = QTabWidget()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.result_tabs.addTab(self.text_edit, "提取结果")
        self.table_widget = DataTable()
        self.result_tabs.addTab(self.table_widget, "表格数据")
        layout.addWidget(self.result_tabs)
        
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
            extract_type = self.type_combo.currentIndex()
            
            with pdfplumber.open(self.source_file) as pdf:
                if extract_type == 0 or extract_type == 2:
                    self._extract_text(pdf)
                
                if extract_type == 1 or extract_type == 2:
                    self._extract_tables(pdf)
            
            self.log_panel.info("提取完成")
        except Exception as e:
            self.log_panel.error(f"提取失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"提取失败:\n{str(e)}")
    
    def _extract_text(self, pdf):
        text = []
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text.append(f"=== 第 {i+1} 页 ===\n{page_text}\n")
        
        self.text_edit.setText("\n".join(text) if text else "未提取到文字")
    
    def _extract_tables(self, pdf):
        all_tables = []
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table:
                    all_tables.extend(table)
        
        if all_tables:
            headers = all_tables[0] if all_tables[0] else ["列1"]
            data = all_tables[1:] if len(all_tables) > 1 else []
            self.table_widget.load_data(headers, data)
            self.log_panel.info(f"提取到 {len(data)} 行表格数据")
        else:
            self.table_widget.load_data(["提示"], [["未提取到表格"]])
    
    def _on_export(self):
        if not self.source_file:
            return
        
        output_path = FileDialog.save_file(self._widget, "导出结果", "文本文件 (*.txt);;CSV文件 (*.csv)")
        if not output_path:
            return
        
        content = self.text_edit.toPlainText()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.log_panel.info(f"已导出: {output_path}")
        QMessageBox.information(self._widget, "成功", f"已导出到:\n{output_path}")
