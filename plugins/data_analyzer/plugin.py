import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.data_table import DataTable
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    """数据分析插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "数据分析"
        self.description = "Excel数据统计分析和图表生成"
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
        
        options_group = QGroupBox("分析选项")
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("分析类型:"))
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItems(["基本统计", "数据透视", "频率分布", "相关性分析"])
        options_layout.addWidget(self.analysis_combo)
        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self._on_analyze)
        options_layout.addWidget(analyze_btn)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        self.result_tabs = QTabWidget()
        self.data_table = DataTable()
        self.result_tabs.addTab(self.data_table, "数据预览")
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.result_tabs.addTab(self.stats_text, "统计结果")
        layout.addWidget(self.result_tabs)
        
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
            headers = list(self.source_df.columns)
            data = self.source_df.head(100).values.tolist()
            self.data_table.load_data(headers, data)
            self.log_panel.info(f"已加载数据: {len(self.source_df)} 行, {len(headers)} 列")
        except Exception as e:
            self.log_panel.error(f"加载数据失败: {str(e)}")
    
    def _on_analyze(self):
        if self.source_df is None:
            QMessageBox.warning(self._widget, "警告", "请先选择源文件")
            return
        
        try:
            analysis_type = self.analysis_combo.currentIndex()
            if analysis_type == 0:
                self._basic_statistics()
            elif analysis_type == 1:
                self._pivot_analysis()
            elif analysis_type == 2:
                self._frequency_distribution()
            else:
                self._correlation_analysis()
            self.result_tabs.setCurrentIndex(1)
        except Exception as e:
            self.log_panel.error(f"分析失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"分析失败:\n{str(e)}")
    
    def _basic_statistics(self):
        df = self.source_df
        stats = ["=" * 50, "基本统计信息", "=" * 50, f"\n总行数: {len(df)}", f"总列数: {len(df.columns)}"]
        
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            stats.append(f"\n数值列: {len(numeric_cols)} 个")
            stats.append("-" * 50)
            for col in numeric_cols:
                stats.extend([
                    f"\n【{col}】",
                    f"  均值: {df[col].mean():.4f}",
                    f"  中位数: {df[col].median():.4f}",
                    f"  标准差: {df[col].std():.4f}",
                    f"  最小值: {df[col].min()}",
                    f"  最大值: {df[col].max()}",
                    f"  总和: {df[col].sum():.4f}"
                ])
        
        text_cols = df.select_dtypes(include=["object"]).columns
        if len(text_cols) > 0:
            stats.append(f"\n文本列: {len(text_cols)} 个")
            stats.append("-" * 50)
            for col in text_cols:
                stats.extend([
                    f"\n【{col}】",
                    f"  唯一值数: {df[col].nunique()}",
                    f"  空值数: {df[col].isnull().sum()}"
                ])
        
        self.stats_text.setText("\n".join(stats))
        self.log_panel.info("基本统计分析完成")
    
    def _pivot_analysis(self):
        df = self.source_df
        stats = ["=" * 50, "数据透视分析", "=" * 50]
        
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        text_cols = df.select_dtypes(include=["object"]).columns.tolist()
        
        if text_cols and numeric_cols:
            pivot_col, value_col = text_cols[0], numeric_cols[0]
            stats.extend([f"\n按 [{pivot_col}] 分组统计 [{value_col}]:", "-" * 50])
            pivot = df.groupby(pivot_col)[value_col].agg(["count", "mean", "sum", "min", "max"])
            stats.append(pivot.to_string())
        else:
            stats.append("\n需要至少一个文本列和一个数值列进行透视分析")
        
        self.stats_text.setText("\n".join(stats))
        self.log_panel.info("数据透视分析完成")
    
    def _frequency_distribution(self):
        df = self.source_df
        stats = ["=" * 50, "频率分布", "=" * 50]
        text_cols = df.select_dtypes(include=["object"]).columns
        
        if len(text_cols) > 0:
            for col in text_cols[:3]:
                stats.extend([f"\n【{col}】频率分布:", "-" * 50])
                for value, count in df[col].value_counts().head(10).items():
                    stats.append(f"  {value}: {count} ({count / len(df) * 100:.1f}%)")
        else:
            stats.append("\n未找到文本列进行频率分布分析")
        
        self.stats_text.setText("\n".join(stats))
        self.log_panel.info("频率分布分析完成")
    
    def _correlation_analysis(self):
        df = self.source_df
        stats = ["=" * 50, "相关性分析", "=" * 50]
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            stats.extend(["\n相关系数矩阵:", "-" * 50, corr.to_string()])
        else:
            stats.append("\n需要至少两个数值列进行相关性分析")
        
        self.stats_text.setText("\n".join(stats))
        self.log_panel.info("相关性分析完成")
