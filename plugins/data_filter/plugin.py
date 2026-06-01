import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from ui.widgets.data_table import DataTable
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """数据筛选插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "数据筛选"
        self.description = "多条件筛选导出"
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
        
        filter_group = QGroupBox("筛选条件（每行一个条件）")
        filter_layout = QVBoxLayout()
        
        self.filter_table = QTableWidget()
        self.filter_table.setColumnCount(4)
        self.filter_table.setHorizontalHeaderLabels(["列名", "运算符", "值", "逻辑"])
        self.filter_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.filter_table.setMaximumHeight(120)
        filter_layout.addWidget(self.filter_table)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加条件")
        add_btn.clicked.connect(self._add_condition)
        btn_row.addWidget(add_btn)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._del_condition)
        btn_row.addWidget(del_btn)
        filter_layout.addLayout(btn_row)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        preview_group = QGroupBox("筛选结果")
        preview_layout = QVBoxLayout()
        self.data_table = DataTable()
        preview_layout.addWidget(self.data_table)
        self.result_label = QLabel("共 0 行")
        self.result_label.setStyleSheet("padding: 5px; color: #666;")
        preview_layout.addWidget(self.result_label)
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
        
        self._init_filter_table()
        return widget
    
    def _init_filter_table(self):
        self.filter_table.setRowCount(5)
        ops = ["等于", "不等于", "包含", "大于", "小于", "为空", "不为空"]
        for row in range(5):
            combo = QComboBox()
            combo.addItems(ops)
            self.filter_table.setCellWidget(row, 1, combo)
            logic = QComboBox()
            logic.addItems(["AND", "OR"])
            logic.setEnabled(row > 0)
            self.filter_table.setCellWidget(row, 3, logic)
    
    def _add_condition(self):
        row = self.filter_table.rowCount()
        self.filter_table.insertRow(row)
        ops = ["等于", "不等于", "包含", "大于", "小于", "为空", "不为空"]
        combo = QComboBox()
        combo.addItems(ops)
        self.filter_table.setCellWidget(row, 1, combo)
        logic = QComboBox()
        logic.addItems(["AND", "OR"])
        self.filter_table.setCellWidget(row, 3, logic)
    
    def _del_condition(self):
        row = self.filter_table.currentRow()
        if row >= 0:
            self.filter_table.removeRow(row)
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self._load_data()
    
    def _load_data(self):
        try:
            if self.source_file.endswith(".csv"):
                self.source_df = pd.read_csv(self.source_file)
            else:
                self.source_df = pd.read_excel(self.source_file)
            
            for row in range(self.filter_table.rowCount()):
                col_combo = QComboBox()
                col_combo.addItems([""] + list(self.source_df.columns))
                self.filter_table.setCellWidget(row, 0, col_combo)
            
            self.log_panel.info(f"已加载: {len(self.source_df)} 行, {len(self.source_df.columns)} 列")
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _build_conditions(self):
        conditions = []
        for row in range(self.filter_table.rowCount()):
            col_combo = self.filter_table.cellWidget(row, 0)
            op_combo = self.filter_table.cellWidget(row, 1)
            val_item = self.filter_table.item(row, 2)
            logic_combo = self.filter_table.cellWidget(row, 3)
            
            if col_combo and col_combo.currentText() and val_item and val_item.text():
                conditions.append({
                    "col": col_combo.currentText(),
                    "op": op_combo.currentText(),
                    "val": val_item.text(),
                    "logic": logic_combo.currentText() if row > 0 else "AND"
                })
        return conditions
    
    def _apply_conditions(self, df, conditions):
        if not conditions:
            return df
        
        mask = pd.Series([True] * len(df), index=df.index)
        
        for i, c in enumerate(conditions):
            col, op, val = c["col"], c["op"], c["val"]
            if col not in df.columns:
                continue
            
            series = df[col]
            col_mask = pd.Series([False] * len(df), index=df.index)
            
            if op == "等于":
                col_mask = series.astype(str) == val
            elif op == "不等于":
                col_mask = series.astype(str) != val
            elif op == "包含":
                col_mask = series.astype(str).str.contains(val, na=False)
            elif op == "大于":
                col_mask = pd.to_numeric(series, errors="coerce") > float(val)
            elif op == "小于":
                col_mask = pd.to_numeric(series, errors="coerce") < float(val)
            elif op == "为空":
                col_mask = series.isna()
            elif op == "不为空":
                col_mask = series.notna()
            
            if i == 0:
                mask = col_mask
            elif c["logic"] == "AND":
                mask = mask & col_mask
            else:
                mask = mask | col_mask
        
        return df[mask]
    
    def _on_preview(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        conditions = self._build_conditions()
        result = self._apply_conditions(self.source_df, conditions)
        
        headers = list(result.columns)
        data = result.head(100).values.tolist()
        self.data_table.load_data(headers, data)
        self.result_label.setText(f"共 {len(result)} 行")
        self.log_panel.info(f"筛选完成: {len(result)} 行")
    
    def _on_export(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        output_path = FileDialog.save_excel(self._widget, "导出筛选结果")
        if not output_path:
            return
        
        conditions = self._build_conditions()
        result = self._apply_conditions(self.source_df, conditions)
        result.to_excel(output_path, index=False)
        
        self.log_panel.info(f"已导出 {len(result)} 行")
        QMessageBox.information(self._widget, "成功", f"已导出 {len(result)} 行")
