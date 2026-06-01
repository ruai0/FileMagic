import os
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """文件重命名插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "文件重命名"
        self.description = "批量重命名Excel文件"
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
        
        dir_group = QGroupBox("选择目录")
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("未选择目录")
        self.dir_label.setStyleSheet("padding: 10px; color: #666;")
        dir_layout.addWidget(self.dir_label)
        select_btn = QPushButton("选择目录")
        select_btn.clicked.connect(self._on_select_dir)
        dir_layout.addWidget(select_btn)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        file_group = QGroupBox("文件预览")
        file_layout = QVBoxLayout()
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["原文件名", "新文件名"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh)
        file_layout.addWidget(refresh_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("重命名规则")
        opts_layout = QVBoxLayout()
        
        rule_layout = QHBoxLayout()
        rule_layout.addWidget(QLabel("规则:"))
        self.rule_combo = QComboBox()
        self.rule_combo.addItems(["添加前缀", "添加后缀", "替换文本", "删除文本", "序号命名", "日期前缀"])
        self.rule_combo.currentIndexChanged.connect(self._on_rule_changed)
        rule_layout.addWidget(self.rule_combo)
        opts_layout.addLayout(rule_layout)
        
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("参数:"))
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("输入参数")
        param_layout.addWidget(self.param_input)
        opts_layout.addLayout(param_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        exec_layout = QHBoxLayout()
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self._on_preview)
        exec_layout.addWidget(preview_btn)
        exec_btn = QPushButton("执行重命名")
        exec_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        exec_btn.clicked.connect(self._on_execute)
        exec_layout.addWidget(exec_btn)
        layout.addLayout(exec_layout)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_select_dir(self):
        d = FileDialog.select_directory(self._widget, "选择目录")
        if d:
            self.dir_label.setText(d)
            self._refresh()
    
    def _refresh(self):
        d = self.dir_label.text()
        if d == "未选择目录":
            return
        self.files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith((".xlsx", ".xls", ".csv"))]
        self.file_table.setRowCount(len(self.files))
        for row, fp in enumerate(self.files):
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(fp)))
        self.log_panel.info(f"找到 {len(self.files)} 个文件")
    
    def _on_rule_changed(self, idx):
        hints = ["输入前缀", "输入后缀", "格式: 旧:新", "输入要删除的文本", "格式: 前缀_起始数字", "无需参数"]
        self.param_input.setPlaceholderText(hints[idx])
    
    def _generate_names(self):
        rule = self.rule_combo.currentIndex()
        param = self.param_input.text().strip()
        names = []
        for i, fp in enumerate(self.files):
            name = os.path.basename(fp)
            name_no_ext, ext = os.path.splitext(name)
            if rule == 0:
                names.append(f"{param}{name}")
            elif rule == 1:
                names.append(f"{name_no_ext}{param}{ext}")
            elif rule == 2:
                parts = param.split(":")
                names.append(name.replace(parts[0], parts[1]) if len(parts) == 2 else name)
            elif rule == 3:
                names.append(name.replace(param, ""))
            elif rule == 4:
                parts = param.split("_")
                names.append(f"{parts[0]}_{int(parts[1]) + i:03d}{ext}" if len(parts) == 2 else name)
            else:
                from datetime import datetime
                names.append(f"{datetime.now().strftime('%Y%m%d_')}{name}")
        return names
    
    def _on_preview(self):
        if not self.files:
            return
        new_names = self._generate_names()
        for row, nn in enumerate(new_names):
            self.file_table.setItem(row, 1, QTableWidgetItem(nn))
    
    def _on_execute(self):
        if not self.files:
            QMessageBox.warning(self._widget, "警告", "请先选择目录")
            return
        
        reply = QMessageBox.question(self._widget, "确认", f"确定重命名 {len(self.files)} 个文件？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        new_names = self._generate_names()
        ok = 0
        for old, new in zip(self.files, new_names):
            try:
                os.rename(old, os.path.join(os.path.dirname(old), new))
                ok += 1
                self.log_panel.info(f"✓ {os.path.basename(old)} → {new}")
            except Exception as e:
                self.log_panel.error(f"✗ {os.path.basename(old)}: {e}")
        
        QMessageBox.information(self._widget, "成功", f"已重命名 {ok} 个文件")
        self._refresh()
