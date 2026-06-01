import os
from typing import Dict, Any, List, Optional
from pypdf import PdfReader, PdfWriter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QSpinBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


class Plugin(BasePlugin):
    """PDF拆分插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF拆分"
        self.description = "按页码拆分PDF文件"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context: Optional[Dict[str, Any]] = None
        self.source_file = None
        self.total_pages = 0
    
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
        
        file_group = QGroupBox("源PDF文件")
        file_layout = QVBoxLayout()
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_file_dropped)
        file_layout.addWidget(self.drop_zone)
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("padding: 10px; color: #666;")
        file_layout.addWidget(self.file_label)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("拆分方式")
        opts_layout = QVBoxLayout()
        
        self.mode_group = QButtonGroup()
        
        mode1 = QRadioButton("按页码范围拆分")
        mode1.setChecked(True)
        self.mode_group.addButton(mode1, 0)
        opts_layout.addWidget(mode1)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("页码范围:"))
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("如: 1-3,5,7-10")
        range_layout.addWidget(self.range_input)
        opts_layout.addLayout(range_layout)
        
        mode2 = QRadioButton("每N页拆分一个文件")
        self.mode_group.addButton(mode2, 1)
        opts_layout.addWidget(mode2)
        
        n_layout = QHBoxLayout()
        n_layout.addWidget(QLabel("每文件页数:"))
        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 1000)
        self.n_spin.setValue(10)
        self.n_spin.setEnabled(False)
        n_layout.addWidget(self.n_spin)
        opts_layout.addLayout(n_layout)
        
        mode3 = QRadioButton("逐页拆分")
        self.mode_group.addButton(mode3, 2)
        opts_layout.addWidget(mode3)
        
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        split_btn = QPushButton("开始拆分")
        split_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        split_btn.clicked.connect(self._on_split)
        layout.addWidget(split_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_mode_changed(self, button):
        id = self.mode_group.checkedId()
        self.range_input.setEnabled(id == 0)
        self.n_spin.setEnabled(id == 1)
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self._load_info()
    
    def _load_info(self):
        try:
            reader = PdfReader(self.source_file)
            self.total_pages = len(reader.pages)
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)} ({self.total_pages} 页)")
            self.log_panel.info(f"已加载: {self.total_pages} 页")
        except Exception as e:
            self.log_panel.error(f"加载失败: {str(e)}")
    
    def _parse_pages(self, range_str: str) -> List[int]:
        pages = []
        for part in range_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                pages.extend(range(int(start), int(end) + 1))
            else:
                pages.append(int(part))
        return [p for p in pages if 1 <= p <= self.total_pages]
    
    def _on_split(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("拆分PDF中...")
        progress.show()
        
        try:
            reader = PdfReader(self.source_file)
            mode = self.mode_group.checkedId()
            base_name = os.path.splitext(os.path.basename(self.source_file))[0]
            
            if mode == 0:
                pages = self._parse_pages(self.range_input.text())
                if not pages:
                    raise ValueError("请输入有效的页码范围")
                
                writer = PdfWriter()
                for p in pages:
                    writer.add_page(reader.pages[p - 1])
                
                output_path = os.path.join(output_dir, f"{base_name}_拆分.pdf")
                with open(output_path, "wb") as f:
                    writer.write(f)
                self.log_panel.info(f"已导出: {output_path}")
            
            elif mode == 1:
                n = self.n_spin.value()
                total_files = (self.total_pages + n - 1) // n
                
                for i in range(total_files):
                    progress.set_status(f"处理文件 {i+1}/{total_files}")
                    progress.set_progress(int((i / total_files) * 100))
                    
                    writer = PdfWriter()
                    start = i * n
                    end = min(start + n, self.total_pages)
                    
                    for p in range(start, end):
                        writer.add_page(reader.pages[p])
                    
                    output_path = os.path.join(output_dir, f"{base_name}_part{i+1:03d}.pdf")
                    with open(output_path, "wb") as f:
                        writer.write(f)
                    self.log_panel.info(f"已导出: {output_path}")
            
            else:
                for i in range(self.total_pages):
                    progress.set_status(f"处理页 {i+1}/{self.total_pages}")
                    progress.set_progress(int((i / self.total_pages) * 100))
                    
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    
                    output_path = os.path.join(output_dir, f"{base_name}_page{i+1:03d}.pdf")
                    with open(output_path, "wb") as f:
                        writer.write(f)
                
                self.log_panel.info(f"已拆分为 {self.total_pages} 个文件")
            
            progress.complete("拆分完成!")
            QMessageBox.information(self._widget, "成功", "PDF拆分完成")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"拆分失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"拆分失败:\n{str(e)}")
