# ExcelTools 插件模板

## 目录结构

```
my_plugin/
├── __init__.py        # 必需
├── plugin.py          # 必需 - 插件主逻辑
├── plugin.json        # 必需 - 插件配置
├── ui.py              # 可选 - 插件UI界面
└── README.md          # 可选 - 插件说明
```

## plugin.json 示例

```json
{
    "name": "我的插件",
    "description": "这是一个示例插件",
    "version": "1.0.0",
    "author": "作者名",
    "category": "Excel处理",
    "icon": "plugin",
    "enabled": true,
    "has_ui": true
}
```

## plugin.py 示例（带UI）

```python
import os
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt
from core.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """带UI的插件示例"""
    
    def __init__(self):
        super().__init__()
        self.name = "我的插件"
        self.description = "这是一个带UI的示例插件"
        self.version = "1.0.0"
        self.author = "作者名"
        self.category = "Excel处理"
        self._widget = None
        self._context = None
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        super().initialize(context)
        self._context = context
    
    def get_widget(self):
        """返回插件界面"""
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget
    
    def _create_widget(self):
        """创建插件界面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title = QLabel("📁 我的插件")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 说明
        desc = QLabel("这是一个带完整UI的插件示例")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)
        
        # 文件选择组
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择文件...")
        path_layout.addWidget(self.path_input)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(browse_btn)
        file_layout.addLayout(path_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 选项组
        options_group = QGroupBox("处理选项")
        options_layout = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("处理模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["模式A", "模式B", "模式C"])
        mode_layout.addWidget(self.mode_combo)
        options_layout.addLayout(mode_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        start_btn = QPushButton("开始处理")
        start_btn.setStyleSheet("background-color: #00d4aa; color: white; padding: 8px 16px;")
        start_btn.clicked.connect(self._start_process)
        btn_layout.addWidget(start_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(reset_btn)
        
        layout.addLayout(btn_layout)
        
        # 结果表格
        result_group = QGroupBox("处理结果")
        result_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["文件", "状态", "说明"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def _browse_file(self):
        """浏览文件"""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self._widget, "选择文件", "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        if filepath:
            self.path_input.setText(filepath)
    
    def _start_process(self):
        """开始处理"""
        filepath = self.path_input.text()
        if not filepath:
            QMessageBox.warning(self._widget, "警告", "请先选择文件")
            return
        
        self.progress_bar.setValue(50)
        QMessageBox.information(self._widget, "完成", "处理完成！")
        self.progress_bar.setValue(100)
    
    def _reset(self):
        """重置"""
        self.path_input.clear()
        self.progress_bar.setValue(0)
        self.result_table.setRowCount(0)
