import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QLineEdit,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """文件拆分插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "文件拆分"
        self.description = "将Excel文件拆分为多个文件"
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
        
        file_group = QGroupBox("源文件")
        file_layout = QVBoxLayout()
        
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_file_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("padding: 10px; color: #666;")
        file_layout.addWidget(self.file_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        options_group = QGroupBox("拆分选项")
        options_layout = QVBoxLayout()
        
        split_type_layout = QHBoxLayout()
        split_type_layout.addWidget(QLabel("拆分方式:"))
        self.split_type_combo = QComboBox()
        self.split_type_combo.addItems(["按工作表拆分", "按行数拆分", "按列值拆分"])
        self.split_type_combo.currentIndexChanged.connect(self._on_split_type_changed)
        split_type_layout.addWidget(self.split_type_combo)
        options_layout.addLayout(split_type_layout)
        
        rows_layout = QHBoxLayout()
        rows_layout.addWidget(QLabel("每文件行数:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100000)
        self.rows_spin.setValue(1000)
        self.rows_spin.setEnabled(False)
        rows_layout.addWidget(self.rows_spin)
        options_layout.addLayout(rows_layout)
        
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("分组列名:"))
        self.column_input = QLineEdit()
        self.column_input.setPlaceholderText("输入列名")
        self.column_input.setEnabled(False)
        column_layout.addWidget(self.column_input)
        options_layout.addLayout(column_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        split_btn = QPushButton("开始拆分")
        split_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        split_btn.clicked.connect(self._on_split)
        layout.addWidget(split_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths: List[str]):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self.log_panel.info(f"源文件: {os.path.basename(self.source_file)}")
    
    def _on_split_type_changed(self, index: int):
        self.rows_spin.setEnabled(index == 1)
        self.column_input.setEnabled(index == 2)
    
    def _on_split(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("拆分文件中...")
        progress.show()
        
        try:
            split_type = self.split_type_combo.currentIndex()
            if split_type == 0:
                self._split_by_sheet(output_dir, progress)
            elif split_type == 1:
                self._split_by_rows(output_dir, progress)
            else:
                self._split_by_column(output_dir, progress)
            
            progress.complete("拆分完成!")
            self.log_panel.info(f"拆分完成，输出目录: {output_dir}")
            QMessageBox.information(self._widget, "成功", f"文件已拆分到:\n{output_dir}")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"拆分失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"拆分失败:\n{str(e)}")
    
    def _split_by_sheet(self, output_dir: str, progress):
        xls = pd.ExcelFile(self.source_file)
        sheets = xls.sheet_names
        total = len(sheets)
        for idx, sheet_name in enumerate(sheets):
            progress.set_status(f"处理工作表 {idx + 1}/{total}: {sheet_name}")
            progress.set_progress(int((idx / total) * 100))
            df = pd.read_excel(self.source_file, sheet_name=sheet_name)
            output_file = os.path.join(output_dir, f"{sheet_name}.xlsx")
            df.to_excel(output_file, index=False, sheet_name=sheet_name)
            progress.add_log(f"已导出: {sheet_name}")
    
    def _split_by_rows(self, output_dir: str, progress):
        df = pd.read_excel(self.source_file)
        rows_per_file = self.rows_spin.value()
        total_rows = len(df)
        total_files = (total_rows + rows_per_file - 1) // rows_per_file
        for idx in range(total_files):
            progress.set_status(f"处理文件 {idx + 1}/{total_files}")
            progress.set_progress(int((idx / total_files) * 100))
            start = idx * rows_per_file
            end = min(start + rows_per_file, total_rows)
            chunk = df.iloc[start:end]
            output_file = os.path.join(output_dir, f"part_{idx + 1:03d}.xlsx")
            chunk.to_excel(output_file, index=False)
            progress.add_log(f"已导出: part_{idx + 1:03d}.xlsx (行 {start + 1}-{end})")
    
    def _split_by_column(self, output_dir: str, progress):
        column_name = self.column_input.text().strip()
        if not column_name:
            raise ValueError("请输入分组列名")
        df = pd.read_excel(self.source_file)
        if column_name not in df.columns:
            raise ValueError(f"列 '{column_name}' 不存在")
        groups = df.groupby(column_name)
        total = len(groups)
        for idx, (group_name, group_df) in enumerate(groups):
            progress.set_status(f"处理分组 {idx + 1}/{total}: {group_name}")
            progress.set_progress(int((idx / total) * 100))
            safe_name = str(group_name).replace("/", "_").replace("\\", "_")
            output_file = os.path.join(output_dir, f"{safe_name}.xlsx")
            group_df.to_excel(output_file, index=False)
            progress.add_log(f"已导出: {safe_name}.xlsx ({len(group_df)} 行)")
