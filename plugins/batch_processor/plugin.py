import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """批量处理插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "批量处理"
        self.description = "批量处理多个Excel文件"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.files: List[str] = []
    
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
        
        file_group = QGroupBox("源文件")
        file_layout = QVBoxLayout()
        
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["文件名", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        options_group = QGroupBox("批量操作")
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("操作类型:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["批量CSV转Excel", "批量Excel转CSV", "批量去除空行", "批量添加表头"])
        options_layout.addWidget(self.operation_combo)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        process_btn = QPushButton("开始处理")
        process_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        process_btn.clicked.connect(self._on_process)
        layout.addWidget(process_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_files_dropped(self, filepaths: List[str]):
        for filepath in filepaths:
            if filepath not in self.files:
                self.files.append(filepath)
        self._update_file_table()
        self.log_panel.info(f"添加了 {len(filepaths)} 个文件")
    
    def _update_file_table(self):
        self.file_table.setRowCount(len(self.files))
        for row, filepath in enumerate(self.files):
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
            self.file_table.setItem(row, 1, QTableWidgetItem("就绪"))
    
    def _on_process(self):
        if not self.files:
            QMessageBox.warning(self._widget, "警告", "请先添加要处理的文件")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("批量处理中...")
        progress.show()
        
        operation = self.operation_combo.currentIndex()
        total = len(self.files)
        success_count = 0
        
        try:
            for idx, filepath in enumerate(self.files):
                progress.set_status(f"处理文件 {idx + 1}/{total}: {os.path.basename(filepath)}")
                progress.set_progress(int((idx / total) * 100))
                
                try:
                    if operation == 0:
                        self._csv_to_excel(filepath, output_dir)
                    elif operation == 1:
                        self._excel_to_csv(filepath, output_dir)
                    elif operation == 2:
                        self._remove_empty_rows(filepath, output_dir)
                    else:
                        self._add_headers(filepath, output_dir)
                    self.file_table.setItem(idx, 1, QTableWidgetItem("完成"))
                    success_count += 1
                except Exception as e:
                    self.file_table.setItem(idx, 1, QTableWidgetItem(f"失败"))
                    self.log_panel.error(f"处理失败 {os.path.basename(filepath)}: {str(e)}")
            
            progress.set_progress(100)
            progress.complete("批量处理完成!")
            self.log_panel.info(f"处理完成: {success_count}/{total} 个文件成功")
            QMessageBox.information(self._widget, "完成", f"批量处理完成!\n成功: {success_count}/{total}")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"批量处理失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"批量处理失败:\n{str(e)}")
    
    def _csv_to_excel(self, filepath: str, output_dir: str):
        if not filepath.endswith(".csv"):
            raise ValueError("不是CSV文件")
        df = pd.read_csv(filepath)
        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(filepath))[0] + ".xlsx")
        df.to_excel(output_file, index=False)
    
    def _excel_to_csv(self, filepath: str, output_dir: str):
        if not filepath.endswith((".xlsx", ".xls")):
            raise ValueError("不是Excel文件")
        df = pd.read_excel(filepath)
        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(filepath))[0] + ".csv")
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    def _remove_empty_rows(self, filepath: str, output_dir: str):
        df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_excel(filepath)
        df = df.dropna(how="all")
        output_file = os.path.join(output_dir, os.path.basename(filepath))
        df.to_csv(output_file, index=False) if filepath.endswith(".csv") else df.to_excel(output_file, index=False)
    
    def _add_headers(self, filepath: str, output_dir: str):
        df = pd.read_csv(filepath, header=None) if filepath.endswith(".csv") else pd.read_excel(filepath, header=None)
        if df.iloc[0].apply(lambda x: isinstance(x, str)).all():
            df.columns = df.iloc[0]
            df = df[1:]
        output_file = os.path.join(output_dir, os.path.basename(filepath))
        df.to_csv(output_file, index=False) if filepath.endswith(".csv") else df.to_excel(output_file, index=False)
