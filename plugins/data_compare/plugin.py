import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QTabWidget, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """数据对比插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "数据对比"
        self.description = "对比两个Excel文件的差异"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.df_a = None
        self.df_b = None
    
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
        
        file_group = QGroupBox("文件对比")
        file_layout = QVBoxLayout()
        
        row = QHBoxLayout()
        self.drop_a = FileDropZone()
        self.drop_a.files_dropped.connect(lambda f: self._on_file_a(f))
        self.drop_a.setMaximumHeight(80)
        row.addWidget(self.drop_a)
        self.drop_b = FileDropZone()
        self.drop_b.files_dropped.connect(lambda f: self._on_file_b(f))
        self.drop_b.setMaximumHeight(80)
        row.addWidget(self.drop_b)
        file_layout.addLayout(row)
        
        self.label_a = QLabel("文件A: 未选择")
        self.label_b = QLabel("文件B: 未选择")
        labels = QHBoxLayout()
        labels.addWidget(self.label_a)
        labels.addWidget(self.label_b)
        file_layout.addLayout(labels)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("对比选项")
        opts_layout = QVBoxLayout()
        
        self.compare_structure = QCheckBox("对比结构（列名、列数）")
        self.compare_structure.setChecked(True)
        opts_layout.addWidget(self.compare_structure)
        
        self.compare_data = QCheckBox("对比数据内容")
        self.compare_data.setChecked(True)
        opts_layout.addWidget(self.compare_data)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("主键列:"))
        self.key_combo = QComboBox()
        self.key_combo.addItem("(按行号)")
        key_layout.addWidget(self.key_combo)
        opts_layout.addLayout(key_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        compare_btn = QPushButton("开始对比")
        compare_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        compare_btn.clicked.connect(self._on_compare)
        layout.addWidget(compare_btn)
        
        self.result_tabs = QTabWidget()
        self.data_table = DataTable()
        self.result_tabs.addTab(self.data_table, "差异数据")
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.result_tabs.addTab(self.stats_text, "对比报告")
        layout.addWidget(self.result_tabs)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_a(self, filepaths):
        if filepaths:
            try:
                self.df_a = pd.read_csv(filepaths[0]) if filepaths[0].endswith(".csv") else pd.read_excel(filepaths[0])
                self.label_a.setText(f"文件A: {os.path.basename(filepaths[0])} ({len(self.df_a)} 行)")
                self._update_key_combo()
            except Exception as e:
                self.log_panel.error(f"加载文件A失败: {e}")
    
    def _on_file_b(self, filepaths):
        if filepaths:
            try:
                self.df_b = pd.read_csv(filepaths[0]) if filepaths[0].endswith(".csv") else pd.read_excel(filepaths[0])
                self.label_b.setText(f"文件B: {os.path.basename(filepaths[0])} ({len(self.df_b)} 行)")
                self._update_key_combo()
            except Exception as e:
                self.log_panel.error(f"加载文件B失败: {e}")
    
    def _update_key_combo(self):
        self.key_combo.clear()
        self.key_combo.addItem("(按行号)")
        if self.df_a is not None:
            self.key_combo.addItems(list(self.df_a.columns))
    
    def _on_compare(self):
        if self.df_a is None or self.df_b is None:
            QMessageBox.warning(self._widget, "警告", "请先选择两个文件")
            return
        
        try:
            report = ["=" * 50, "数据对比报告", "=" * 50]
            
            if self.compare_structure.isChecked():
                report.extend([
                    f"\n文件A: {len(self.df_a)} 行 x {len(self.df_a.columns)} 列",
                    f"文件B: {len(self.df_b)} 行 x {len(self.df_b.columns)} 列",
                    f"\n共同列: {len(set(self.df_a.columns) & set(self.df_b.columns))}",
                    f"文件A独有列: {set(self.df_a.columns) - set(self.df_b.columns)}",
                    f"文件B独有列: {set(self.df_b.columns) - set(self.df_a.columns)}"
                ])
            
            if self.compare_data.isChecked():
                diff_data = self._compare_data()
                if diff_data is not None:
                    self.data_table.load_data(list(diff_data.columns), diff_data.values.tolist())
                    report.append(f"\n数据差异: {len(diff_data)} 处")
            
            self.stats_text.setText("\n".join(report))
            self.result_tabs.setCurrentIndex(0)
            self.log_panel.info("对比完成")
        except Exception as e:
            self.log_panel.error(f"对比失败: {e}")
    
    def _compare_data(self):
        key = self.key_combo.currentText()
        diffs = []
        
        if key == "(按行号)":
            min_len = min(len(self.df_a), len(self.df_b))
            for idx in range(min_len):
                for col in set(self.df_a.columns) & set(self.df_b.columns):
                    va = str(self.df_a.at[idx, col])
                    vb = str(self.df_b.at[idx, col])
                    if va != vb:
                        diffs.append([idx + 1, col, va[:30], vb[:30]])
        else:
            merged = pd.merge(self.df_a, self.df_b, on=key, how="outer", suffixes=("_A", "_B"), indicator=True)
            for _, row in merged.head(500).iterrows():
                if row["_merge"] != "both":
                    diffs.append([row.get(key, ""), "仅在一侧", "", ""])
                else:
                    for col in self.df_a.columns:
                        if col != key and f"{col}_B" in merged.columns:
                            va, vb = str(row.get(f"{col}_A", "")), str(row.get(f"{col}_B", ""))
                            if va != vb:
                                diffs.append([row[key], col, va[:30], vb[:30]])
        
        return pd.DataFrame(diffs[:200], columns=["主键/行号", "列名", "文件A", "文件B"]) if diffs else None
