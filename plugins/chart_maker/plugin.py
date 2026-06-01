import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QSpinBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """图表生成插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "图表生成"
        self.description = "生成柱状图、折线图、饼图"
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
        
        chart_group = QGroupBox("图表设置")
        chart_layout = QVBoxLayout()
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("图表类型:"))
        self.chart_combo = QComboBox()
        self.chart_combo.addItems(["柱状图", "折线图", "饼图", "散点图"])
        type_layout.addWidget(self.chart_combo)
        chart_layout.addLayout(type_layout)
        
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X轴(分类):"))
        self.x_combo = QComboBox()
        x_layout.addWidget(self.x_combo)
        chart_layout.addLayout(x_layout)
        
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y轴(数值):"))
        self.y_combo = QComboBox()
        y_layout.addWidget(self.y_combo)
        chart_layout.addLayout(y_layout)
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("图表标题:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入图表标题")
        title_layout.addWidget(self.title_input)
        chart_layout.addLayout(title_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("宽度:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(400, 2000)
        self.width_spin.setValue(800)
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("高度:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(300, 1500)
        self.height_spin.setValue(500)
        size_layout.addWidget(self.height_spin)
        chart_layout.addLayout(size_layout)
        
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
        
        gen_btn = QPushButton("生成图表")
        gen_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        gen_btn.clicked.connect(self._on_generate)
        layout.addWidget(gen_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths: List[str]):
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
            
            self.x_combo.clear()
            self.y_combo.clear()
            self.x_combo.addItems(list(self.source_df.columns))
            self.y_combo.addItems(list(self.source_df.columns))
            
            self.log_panel.info(f"已加载: {len(self.source_df)} 行, {len(self.source_df.columns)} 列")
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _on_generate(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        output_path = FileDialog.save_file(
            self._widget, "保存图表",
            "PNG图片 (*.png);;JPG图片 (*.jpg);;SVG图片 (*.svg)",
            ".png"
        )
        if not output_path:
            return
        
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            
            plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
            plt.rcParams["axes.unicode_minus"] = False
            
            chart_type = self.chart_combo.currentIndex()
            x_col = self.x_combo.currentText()
            y_col = self.y_combo.currentText()
            title = self.title_input.text() or f"{y_col} vs {x_col}"
            width = self.width_spin.value() / 100
            height = self.height_spin.value() / 100
            
            fig, ax = plt.subplots(figsize=(width, height))
            
            x_data = self.source_df[x_col].astype(str)
            y_data = pd.to_numeric(self.source_df[y_col], errors="coerce")
            
            if chart_type == 0:
                ax.bar(x_data, y_data, color="#4472C4")
                ax.set_ylabel(y_col)
            elif chart_type == 1:
                ax.plot(x_data, y_data, marker="o", color="#4472C4")
                ax.set_ylabel(y_col)
            elif chart_type == 2:
                ax.pie(y_data, labels=x_data, autopct="%1.1f%%")
            elif chart_type == 3:
                ax.scatter(x_data, y_data, color="#4472C4")
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            
            ax.set_title(title)
            
            if chart_type != 2:
                plt.xticks(rotation=45, ha="right")
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
            
            self.log_panel.info(f"图表已保存: {output_path}")
            QMessageBox.information(self._widget, "成功", f"图表已保存到:\n{output_path}")
        
        except ImportError:
            QMessageBox.warning(self._widget, "警告", "请先安装 matplotlib:\npip install matplotlib")
        except Exception as e:
            self.log_panel.error(f"生成图表失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"生成图表失败:\n{str(e)}")
