import os
from PIL import Image
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")


class Plugin(BasePlugin):
    """图片批量处理插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "图片批量处理"
        self.description = "批量压缩、格式转换、调整尺寸"
        self.version = "1.0.0"
        self.author = "ExcelTools"
        self._widget = None
        self._context = None
        self.files: List[str] = []
    
    def initialize(self, context):
        super().initialize(context)
        self._context = context
    
    def get_widget(self):
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget
    
    def _create_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        file_group = QGroupBox("图片文件列表")
        file_layout = QVBoxLayout()
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["文件名", "尺寸", "格式"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加图片")
        add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(add_btn)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(clear_btn)
        file_layout.addLayout(btn_row)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("处理选项")
        opts_layout = QVBoxLayout()
        
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("输出格式:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["保持原格式", "PNG", "JPG", "BMP", "WEBP"])
        fmt_layout.addWidget(self.fmt_combo)
        opts_layout.addLayout(fmt_layout)
        
        resize_layout = QHBoxLayout()
        self.resize_check = QCheckBox("调整尺寸")
        resize_layout.addWidget(self.resize_check)
        resize_layout.addWidget(QLabel("宽度:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 5000)
        self.width_spin.setValue(800)
        self.width_spin.setEnabled(False)
        resize_layout.addWidget(self.width_spin)
        resize_layout.addWidget(QLabel("高度:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 5000)
        self.height_spin.setValue(600)
        self.height_spin.setEnabled(False)
        resize_layout.addWidget(self.height_spin)
        opts_layout.addLayout(resize_layout)
        
        self.resize_check.stateChanged.connect(self._on_resize_changed)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("压缩质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(85)
        self.quality_spin.setSuffix("%")
        quality_layout.addWidget(self.quality_spin)
        opts_layout.addLayout(quality_layout)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        exec_btn = QPushButton("开始处理")
        exec_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        exec_btn.clicked.connect(self._on_process)
        layout.addWidget(exec_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_resize_changed(self, state):
        self.width_spin.setEnabled(state == Qt.CheckState.Checked.value)
        self.height_spin.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _on_files_dropped(self, filepaths):
        for fp in filepaths:
            if fp.lower().endswith(IMG_EXTS) and fp not in self.files:
                self.files.append(fp)
        self._update_table()
    
    def _on_add(self):
        filepaths = FileDialog.open_files(self._widget, "选择图片", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)")
        if filepaths:
            for fp in filepaths:
                if fp not in self.files:
                    self.files.append(fp)
            self._update_table()
    
    def _update_table(self):
        self.file_table.setRowCount(len(self.files))
        for row, fp in enumerate(self.files):
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(fp)))
            try:
                img = Image.open(fp)
                self.file_table.setItem(row, 1, QTableWidgetItem(f"{img.width}x{img.height}"))
                self.file_table.setItem(row, 2, QTableWidgetItem(img.format or "N/A"))
            except:
                self.file_table.setItem(row, 1, QTableWidgetItem("N/A"))
                self.file_table.setItem(row, 2, QTableWidgetItem("N/A"))
    
    def _on_clear(self):
        self.files.clear()
        self.file_table.setRowCount(0)
    
    def _on_process(self):
        if not self.files:
            QMessageBox.warning(self._widget, "警告", "请先添加图片")
            return
        
        output_dir = FileDialog.select_directory(self._widget, "选择输出目录")
        if not output_dir:
            return
        
        progress = ProgressDialog("处理中...")
        progress.show()
        
        try:
            fmt_idx = self.fmt_combo.currentIndex()
            fmt_map = {0: None, 1: "PNG", 2: "JPEG", 3: "BMP", 4: "WEBP"}
            target_fmt = fmt_map[fmt_idx]
            
            resize = self.resize_check.isChecked()
            width = self.width_spin.value()
            height = self.height_spin.value()
            quality = self.quality_spin.value()
            
            for idx, fp in enumerate(self.files):
                progress.set_status(f"处理 {idx + 1}/{len(self.files)}: {os.path.basename(fp)}")
                progress.set_progress(int((idx / len(self.files)) * 100))
                
                img = Image.open(fp)
                
                if resize:
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                name = os.path.splitext(os.path.basename(fp))[0]
                out_fmt = target_fmt or img.format or "PNG"
                ext = out_fmt.lower()
                output_path = os.path.join(output_dir, f"{name}.{ext}")
                
                save_kwargs = {}
                if out_fmt in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                
                img.save(output_path, out_fmt, **save_kwargs)
                progress.add_log(f"已处理: {name}.{ext}")
            
            progress.complete("处理完成!")
            self.log_panel.info(f"已处理 {len(self.files)} 张图片")
            QMessageBox.information(self._widget, "成功", f"已处理 {len(self.files)} 张图片")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"处理失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"处理失败:\n{str(e)}")
