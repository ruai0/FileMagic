import os
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QGroupBox, QMessageBox,
    QLineEdit, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """数据脱敏插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "数据脱敏"
        self.description = "手机号、身份证、邮箱等敏感数据脱敏"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
        self.source_df = None
    
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
        
        opts_group = QGroupBox("脱敏选项")
        opts_layout = QVBoxLayout()
        
        self.phone_check = QCheckBox("手机号 (138****1234)")
        self.phone_check.setChecked(True)
        opts_layout.addWidget(self.phone_check)
        
        self.id_check = QCheckBox("身份证 (110***********1234)")
        self.id_check.setChecked(True)
        opts_layout.addWidget(self.id_check)
        
        self.email_check = QCheckBox("邮箱 (t***@example.com)")
        self.email_check.setChecked(True)
        opts_layout.addWidget(self.email_check)
        
        self.name_check = QCheckBox("姓名 (张*)")
        self.name_check.setChecked(True)
        opts_layout.addWidget(self.name_check)
        
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("自定义列:"))
        self.col_combo = QComboBox()
        self.col_combo.addItems(["(不使用)"])
        custom_layout.addWidget(self.col_combo)
        custom_layout.addWidget(QLabel("保留前N位:"))
        self.keep_spin = QSpinBox()
        self.keep_spin.setRange(1, 10)
        self.keep_spin.setValue(3)
        custom_layout.addWidget(self.keep_spin)
        opts_layout.addLayout(custom_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        self.data_table = DataTable()
        preview_layout.addWidget(self.data_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        exec_layout = QHBoxLayout()
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self._on_preview)
        exec_layout.addWidget(preview_btn)
        export_btn = QPushButton("导出")
        export_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 8px;")
        export_btn.clicked.connect(self._on_export)
        exec_layout.addWidget(export_btn)
        layout.addLayout(exec_layout)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _mask_phone(self, v):
        v = str(v)
        return v[:3] + "****" + v[7:] if len(v) == 11 and v.isdigit() else v
    
    def _mask_id(self, v):
        v = str(v)
        if len(v) == 18:
            return v[:3] + "***********" + v[14:]
        return v
    
    def _mask_email(self, v):
        v = str(v)
        if "@" in v:
            parts = v.split("@")
            return parts[0][0] + "***@" + parts[1] if len(parts[0]) > 1 else v
        return v
    
    def _mask_name(self, v):
        v = str(v)
        return v[0] + "*" * (len(v) - 1) if len(v) >= 2 and v.isalpha() else v
    
    def _mask_custom(self, v, keep):
        v = str(v)
        return v[:keep] + "*" * (len(v) - keep) if len(v) > keep else v
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self._load_data()
    
    def _load_data(self):
        try:
            if self.source_file.endswith(".csv"):
                self.source_df = pd.read_csv(self.source_file, dtype=str)
            else:
                self.source_df = pd.read_excel(self.source_file, dtype=str)
            self.source_df = self.source_df.fillna("")
            
            self.col_combo.clear()
            self.col_combo.addItems(["(不使用)"] + list(self.source_df.columns))
            
            headers = list(self.source_df.columns)
            data = self.source_df.head(20).values.tolist()
            self.data_table.load_data(headers, data)
            self.log_panel.info(f"已加载: {len(self.source_df)} 行")
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _mask_data(self, df):
        result = df.copy()
        for col in result.columns:
            if self.phone_check.isChecked():
                result[col] = result[col].apply(
                    lambda x: self._mask_phone(x) if re.match(r'^1[3-9]\d{9}$', str(x)) else x
                )
            if self.id_check.isChecked():
                result[col] = result[col].apply(
                    lambda x: self._mask_id(x) if re.match(r'^\d{17}[\dXx]$', str(x)) else x
                )
            if self.email_check.isChecked():
                result[col] = result[col].apply(
                    lambda x: self._mask_email(x) if "@" in str(x) else x
                )
            if self.name_check.isChecked():
                result[col] = result[col].apply(
                    lambda x: self._mask_name(x) if len(str(x)) >= 2 and str(x).isalpha() else x
                )
        
        custom_col = self.col_combo.currentText()
        if custom_col != "(不使用)" and custom_col in result.columns:
            keep = self.keep_spin.value()
            result[custom_col] = result[custom_col].apply(lambda x: self._mask_custom(x, keep))
        
        return result
    
    def _on_preview(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        result = self._mask_data(self.source_df.head(20))
        self.data_table.load_data(list(result.columns), result.values.tolist())
        self.log_panel.info("预览已更新")
    
    def _on_export(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        output_path = FileDialog.save_excel(self._widget, "导出脱敏数据")
        if not output_path:
            return
        result = self._mask_data(self.source_df)
        result.to_excel(output_path, index=False)
        self.log_panel.info(f"已导出: {output_path}")
        QMessageBox.information(self._widget, "成功", f"已导出脱敏数据")
