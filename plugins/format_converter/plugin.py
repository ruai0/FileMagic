import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """格式转换插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "格式转换"
        self.description = "Excel与其他格式互相转换"
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
        
        options_group = QGroupBox("转换选项")
        options_layout = QVBoxLayout()
        
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("转换方向:"))
        self.direction_group = QButtonGroup()
        self.to_csv_radio = QRadioButton("Excel → CSV")
        self.to_csv_radio.setChecked(True)
        self.direction_group.addButton(self.to_csv_radio, 0)
        direction_layout.addWidget(self.to_csv_radio)
        self.to_json_radio = QRadioButton("Excel → JSON")
        self.direction_group.addButton(self.to_json_radio, 1)
        direction_layout.addWidget(self.to_json_radio)
        self.to_excel_radio = QRadioButton("CSV → Excel")
        self.direction_group.addButton(self.to_excel_radio, 2)
        direction_layout.addWidget(self.to_excel_radio)
        options_layout.addLayout(direction_layout)
        
        encoding_layout = QHBoxLayout()
        encoding_layout.addWidget(QLabel("编码:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8", "GBK", "GB2312", "ISO-8859-1"])
        encoding_layout.addWidget(self.encoding_combo)
        options_layout.addLayout(encoding_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(convert_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths: List[str]):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
            self.log_panel.info(f"源文件: {os.path.basename(self.source_file)}")
    
    def _on_convert(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        progress = ProgressDialog("转换中...")
        progress.show()
        
        try:
            direction = self.direction_group.checkedId()
            if direction == 0:
                self._convert_to_csv(progress)
            elif direction == 1:
                self._convert_to_json(progress)
            else:
                self._convert_to_excel(progress)
            progress.complete("转换完成!")
            QMessageBox.information(self._widget, "成功", "文件转换完成!")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"转换失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"转换失败:\n{str(e)}")
    
    def _convert_to_csv(self, progress):
        output_path = FileDialog.save_csv(self._widget, "保存CSV文件")
        if not output_path:
            return
        progress.set_status("读取Excel文件...")
        progress.set_progress(20)
        df = pd.read_excel(self.source_file)
        progress.set_status("写入CSV文件...")
        progress.set_progress(60)
        encoding = self.encoding_combo.currentText()
        df.to_csv(output_path, index=False, encoding=encoding)
        progress.set_progress(100)
        self.log_panel.info(f"已转换为CSV: {output_path}")
    
    def _convert_to_json(self, progress):
        output_path = FileDialog.save_file(self._widget, "保存JSON文件", "JSON文件 (*.json)", ".json")
        if not output_path:
            return
        progress.set_status("读取Excel文件...")
        progress.set_progress(20)
        df = pd.read_excel(self.source_file)
        progress.set_status("写入JSON文件...")
        progress.set_progress(60)
        data = df.to_dict(orient="records")
        encoding = self.encoding_combo.currentText()
        with open(output_path, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        progress.set_progress(100)
        self.log_panel.info(f"已转换为JSON: {output_path}")
    
    def _convert_to_excel(self, progress):
        output_path = FileDialog.save_excel(self._widget, "保存Excel文件")
        if not output_path:
            return
        progress.set_status("读取CSV文件...")
        progress.set_progress(20)
        encoding = self.encoding_combo.currentText()
        df = pd.read_csv(self.source_file, encoding=encoding)
        progress.set_status("写入Excel文件...")
        progress.set_progress(60)
        df.to_excel(output_path, index=False)
        progress.set_progress(100)
        self.log_panel.info(f"已转换为Excel: {output_path}")
