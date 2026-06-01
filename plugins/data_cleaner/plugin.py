import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """数据清洗插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "数据清洗"
        self.description = "清洗Excel数据，去重、处理空值等"
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
        
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout()
        self.data_table = DataTable()
        preview_layout.addWidget(self.data_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        options_group = QGroupBox("清洗选项")
        options_layout = QVBoxLayout()
        
        duplicate_layout = QHBoxLayout()
        self.remove_duplicates = QCheckBox("删除完全重复行")
        self.remove_duplicates.setChecked(True)
        duplicate_layout.addWidget(self.remove_duplicates)
        self.mark_duplicates = QCheckBox("标记重复行")
        duplicate_layout.addWidget(self.mark_duplicates)
        options_layout.addLayout(duplicate_layout)
        
        null_layout = QHBoxLayout()
        null_layout.addWidget(QLabel("空值处理:"))
        self.null_combo = QComboBox()
        self.null_combo.addItems(["保留", "删除含空值行", "用0填充", "用前值填充"])
        null_layout.addWidget(self.null_combo)
        options_layout.addLayout(null_layout)
        
        trim_layout = QHBoxLayout()
        self.trim_spaces = QCheckBox("去除文本前后空格")
        self.trim_spaces.setChecked(True)
        trim_layout.addWidget(self.trim_spaces)
        options_layout.addLayout(trim_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        clean_btn = QPushButton("开始清洗")
        clean_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        clean_btn.clicked.connect(self._on_clean)
        layout.addWidget(clean_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths: List[str]):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self._load_preview()
    
    def _load_preview(self):
        try:
            if self.source_file.endswith(".csv"):
                self.source_df = pd.read_csv(self.source_file)
            else:
                self.source_df = pd.read_excel(self.source_file)
            headers = list(self.source_df.columns)
            data = self.source_df.head(100).values.tolist()
            self.data_table.load_data(headers, data)
            self.log_panel.info(f"已加载数据: {len(self.source_df)} 行, {len(headers)} 列")
        except Exception as e:
            self.log_panel.error(f"加载数据失败: {str(e)}")
    
    def _on_clean(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        output_path = FileDialog.save_excel(self._widget, "保存清洗结果")
        if not output_path:
            return
        
        progress = ProgressDialog("清洗数据中...")
        progress.show()
        
        try:
            df = self.source_df.copy()
            original_rows = len(df)
            
            progress.set_status("处理重复数据...")
            progress.set_progress(10)
            
            if self.remove_duplicates.isChecked():
                before = len(df)
                df = df.drop_duplicates()
                self.log_panel.info(f"删除了 {before - len(df)} 行重复数据")
            elif self.mark_duplicates.isChecked():
                df["_is_duplicate"] = df.duplicated(keep="first")
                self.log_panel.info("已标记重复行")
            
            progress.set_status("处理空值...")
            progress.set_progress(30)
            
            null_option = self.null_combo.currentIndex()
            if null_option == 1:
                before = len(df)
                df = df.dropna()
                self.log_panel.info(f"删除了 {before - len(df)} 行含空值数据")
            elif null_option == 2:
                df = df.fillna(0)
                self.log_panel.info("已用0填充空值")
            elif null_option == 3:
                df = df.fillna(method="ffill")
                self.log_panel.info("已用前值填充空值")
            
            progress.set_status("处理文本...")
            progress.set_progress(60)
            
            if self.trim_spaces.isChecked():
                for col in df.select_dtypes(include=["object"]).columns:
                    df[col] = df[col].astype(str).str.strip()
                self.log_panel.info("已去除文本空格")
            
            progress.set_status("保存文件...")
            progress.set_progress(80)
            
            df.to_excel(output_path, index=False)
            
            progress.set_progress(100)
            progress.complete("清洗完成!")
            
            self.log_panel.info(f"原始行数: {original_rows}, 清洗后行数: {len(df)}")
            QMessageBox.information(self._widget, "成功", f"清洗完成!\n原始: {original_rows} 行\n清洗后: {len(df)} 行")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"清洗失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"清洗失败:\n{str(e)}")
