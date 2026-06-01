import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """工作表管理插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "工作表管理"
        self.description = "批量导出/删除/重命名工作表"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
        self.sheets = []
    
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
        
        sheet_group = QGroupBox("工作表列表（Ctrl多选）")
        sheet_layout = QVBoxLayout()
        self.sheet_list = QListWidget()
        self.sheet_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        sheet_layout.addWidget(self.sheet_list)
        sheet_group.setLayout(sheet_layout)
        layout.addWidget(sheet_group)
        
        ops_layout = QHBoxLayout()
        ops_layout.addWidget(QLabel("操作:"))
        self.op_combo = QComboBox()
        self.op_combo.addItems(["导出选中工作表", "删除选中工作表", "重命名工作表"])
        ops_layout.addWidget(self.op_combo)
        
        ops_layout.addWidget(QLabel("新名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("重命名时输入")
        ops_layout.addWidget(self.name_input)
        layout.addLayout(ops_layout)
        
        exec_btn = QPushButton("执行")
        exec_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        exec_btn.clicked.connect(self._on_execute)
        layout.addWidget(exec_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self._load_sheets()
    
    def _load_sheets(self):
        try:
            xls = pd.ExcelFile(self.source_file)
            self.sheets = xls.sheet_names
            self.sheet_list.clear()
            for s in self.sheets:
                df = pd.read_excel(self.source_file, sheet_name=s)
                self.sheet_list.addItem(f"{s} ({len(df)} 行)")
            self.log_panel.info(f"已加载 {len(self.sheets)} 个工作表")
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _get_selected(self):
        return [item.text().split(" (")[0] for item in self.sheet_list.selectedItems()]
    
    def _on_execute(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择文件")
            return
        
        selected = self._get_selected()
        if not selected:
            QMessageBox.warning(self._widget, "警告", "请先选择工作表")
            return
        
        op = self.op_combo.currentIndex()
        
        try:
            if op == 0:
                self._export_sheets(selected)
            elif op == 1:
                self._delete_sheets(selected)
            else:
                self._rename_sheet(selected)
        except Exception as e:
            self.log_panel.error(f"操作失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", str(e))
    
    def _export_sheets(self, sheets):
        out_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not out_dir:
            return
        for s in sheets:
            df = pd.read_excel(self.source_file, sheet_name=s)
            df.to_excel(os.path.join(out_dir, f"{s}.xlsx"), index=False)
            self.log_panel.info(f"已导出: {s}")
        QMessageBox.information(self._widget, "成功", f"已导出 {len(sheets)} 个工作表")
    
    def _delete_sheets(self, sheets):
        out_path = FileDialog.save_excel(self._widget, "保存删除后文件")
        if not out_path:
            return
        xls = pd.ExcelFile(self.source_file)
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for s in xls.sheet_names:
                if s not in sheets:
                    df = pd.read_excel(self.source_file, sheet_name=s)
                    df.to_excel(writer, sheet_name=s, index=False)
                    self.log_panel.info(f"保留: {s}")
        QMessageBox.information(self._widget, "成功", f"已删除 {len(sheets)} 个工作表")
    
    def _rename_sheet(self, sheets):
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self._widget, "警告", "请输入新名称")
            return
        out_path = FileDialog.save_excel(self._widget, "保存重命名后文件")
        if not out_path:
            return
        xls = pd.ExcelFile(self.source_file)
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for s in xls.sheet_names:
                df = pd.read_excel(self.source_file, sheet_name=s)
                name = new_name if s == sheets[0] else s
                df.to_excel(writer, sheet_name=name, index=False)
        QMessageBox.information(self._widget, "成功", f"已重命名: {sheets[0]} → {new_name}")
