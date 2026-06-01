import os
from typing import Dict, Any, List, Optional
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """文件合并插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "文件合并"
        self.description = "将多个Excel文件合并为一个文件"
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
        
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout()
        
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["文件名", "大小", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("添加文件")
        add_btn.clicked.connect(self._on_add_files)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(self._on_remove_files)
        buttons_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self._on_clear_files)
        buttons_layout.addWidget(clear_btn)
        
        file_layout.addLayout(buttons_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        options_group = QGroupBox("合并选项")
        options_layout = QVBoxLayout()
        
        merge_type_layout = QHBoxLayout()
        merge_type_layout.addWidget(QLabel("合并方式:"))
        self.merge_type_combo = QComboBox()
        self.merge_type_combo.addItems(["按工作表合并", "按行合并(追加)", "按列合并"])
        merge_type_layout.addWidget(self.merge_type_combo)
        options_layout.addLayout(merge_type_layout)
        
        duplicate_layout = QHBoxLayout()
        duplicate_layout.addWidget(QLabel("重复数据:"))
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["保留所有", "删除重复", "标记重复"])
        duplicate_layout.addWidget(self.duplicate_combo)
        options_layout.addLayout(duplicate_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        merge_btn = QPushButton("开始合并")
        merge_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        merge_btn.clicked.connect(self._on_merge)
        layout.addWidget(merge_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_files_dropped(self, filepaths: List[str]):
        for filepath in filepaths:
            if filepath not in self.files and self._is_valid_file(filepath):
                self.files.append(filepath)
                self._update_file_table()
                self.log_panel.info(f"添加文件: {os.path.basename(filepath)}")
    
    def _on_add_files(self):
        filepaths = FileDialog.open_files(
            self._widget, "选择Excel文件",
            "Excel文件 (*.xlsx *.xls *.xlsm *.xlsb);;CSV文件 (*.csv)"
        )
        if filepaths:
            for filepath in filepaths:
                if filepath not in self.files:
                    self.files.append(filepath)
            self._update_file_table()
            self.log_panel.info(f"添加了 {len(filepaths)} 个文件")
    
    def _on_remove_files(self):
        selected_rows = set()
        for item in self.file_table.selectedItems():
            selected_rows.add(item.row())
        for row in sorted(selected_rows, reverse=True):
            if row < len(self.files):
                self.files.pop(row)
        self._update_file_table()
    
    def _on_clear_files(self):
        self.files.clear()
        self._update_file_table()
    
    def _update_file_table(self):
        self.file_table.setRowCount(len(self.files))
        for row, filepath in enumerate(self.files):
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(filepath)))
            size = os.path.getsize(filepath)
            self.file_table.setItem(row, 1, QTableWidgetItem(self._format_size(size)))
            self.file_table.setItem(row, 2, QTableWidgetItem("就绪"))
    
    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def _is_valid_file(self, filepath: str) -> bool:
        return os.path.splitext(filepath)[1].lower() in [".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"]
    
    def _on_merge(self):
        if not self.files:
            QMessageBox.warning(self._widget, "警告", "请先添加要合并的文件")
            return
        
        output_path = FileDialog.save_excel(self._widget, "保存合并结果")
        if not output_path:
            return
        
        progress = ProgressDialog("合并文件中...")
        progress.show()
        
        try:
            merge_type = self.merge_type_combo.currentIndex()
            if merge_type == 0:
                self._merge_by_sheet(output_path, progress)
            elif merge_type == 1:
                self._merge_by_row(output_path, progress)
            else:
                self._merge_by_column(output_path, progress)
            
            progress.complete("合并完成!")
            self.log_panel.info(f"合并完成: {output_path}")
            QMessageBox.information(self._widget, "成功", f"文件已保存到:\n{output_path}")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"合并失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"合并失败:\n{str(e)}")
    
    def _merge_by_sheet(self, output_path: str, progress):
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            total = len(self.files)
            for idx, filepath in enumerate(self.files):
                progress.set_status(f"处理文件 {idx + 1}/{total}: {os.path.basename(filepath)}")
                progress.set_progress(int((idx / total) * 100))
                try:
                    if filepath.endswith(".csv"):
                        df = pd.read_csv(filepath)
                        sheet_name = os.path.splitext(os.path.basename(filepath))[0][:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        xls = pd.ExcelFile(filepath)
                        for sheet_name in xls.sheet_names:
                            df = pd.read_excel(filepath, sheet_name=sheet_name)
                            new_name = f"{sheet_name[:20]}_{idx}"
                            df.to_excel(writer, sheet_name=new_name, index=False)
                    progress.add_log(f"已处理: {os.path.basename(filepath)}")
                except Exception as e:
                    progress.add_log(f"处理失败 {os.path.basename(filepath)}: {str(e)}")
    
    def _merge_by_row(self, output_path: str, progress):
        all_dfs = []
        total = len(self.files)
        for idx, filepath in enumerate(self.files):
            progress.set_status(f"读取文件 {idx + 1}/{total}: {os.path.basename(filepath)}")
            progress.set_progress(int((idx / total) * 50))
            try:
                df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_excel(filepath)
                all_dfs.append(df)
                progress.add_log(f"已读取: {os.path.basename(filepath)}")
            except Exception as e:
                progress.add_log(f"读取失败 {os.path.basename(filepath)}: {str(e)}")
        
        if all_dfs:
            progress.set_status("合并数据...")
            progress.set_progress(75)
            merged_df = pd.concat(all_dfs, ignore_index=True)
            if self.duplicate_combo.currentIndex() == 1:
                merged_df = merged_df.drop_duplicates()
            elif self.duplicate_combo.currentIndex() == 2:
                merged_df["_is_duplicate"] = merged_df.duplicated(keep="first")
            progress.set_status("保存文件...")
            progress.set_progress(90)
            merged_df.to_excel(output_path, index=False)
            progress.set_progress(100)
    
    def _merge_by_column(self, output_path: str, progress):
        all_dfs = []
        total = len(self.files)
        for idx, filepath in enumerate(self.files):
            progress.set_status(f"读取文件 {idx + 1}/{total}: {os.path.basename(filepath)}")
            progress.set_progress(int((idx / total) * 50))
            try:
                df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_excel(filepath)
                all_dfs.append(df)
                progress.add_log(f"已读取: {os.path.basename(filepath)}")
            except Exception as e:
                progress.add_log(f"读取失败 {os.path.basename(filepath)}: {str(e)}")
        
        if all_dfs:
            progress.set_status("合并数据...")
            progress.set_progress(75)
            merged_df = pd.concat(all_dfs, axis=1)
            progress.set_status("保存文件...")
            progress.set_progress(90)
            merged_df.to_excel(output_path, index=False)
            progress.set_progress(100)
