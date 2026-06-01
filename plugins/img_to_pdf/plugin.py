import os
from typing import Dict, Any, List, Optional
from pypdf import PdfWriter
from PIL import Image
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog
from ui.dialogs.progress_dialog import ProgressDialog


IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")


class Plugin(BasePlugin):
    """图片转PDF插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "图片转PDF"
        self.description = "将多张图片合并为一个PDF"
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
        
        file_group = QGroupBox("图片文件列表")
        file_layout = QVBoxLayout()
        
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_zone)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["文件名", "尺寸"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加图片")
        add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(add_btn)
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(remove_btn)
        up_btn = QPushButton("上移")
        up_btn.clicked.connect(self._on_up)
        btn_row.addWidget(up_btn)
        down_btn = QPushButton("下移")
        down_btn.clicked.connect(self._on_down)
        btn_row.addWidget(down_btn)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(clear_btn)
        file_layout.addLayout(btn_row)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        convert_btn = QPushButton("开始转换")
        convert_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(convert_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_files_dropped(self, filepaths):
        for fp in filepaths:
            if fp.lower().endswith(IMG_EXTS) and fp not in self.files:
                self.files.append(fp)
        self._update_table()
    
    def _on_add(self):
        filepaths = FileDialog.open_files(self._widget, "选择图片", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)")
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
            except:
                self.file_table.setItem(row, 1, QTableWidgetItem("N/A"))
    
    def _on_remove(self):
        row = self.file_table.currentRow()
        if row >= 0 and row < len(self.files):
            self.files.pop(row)
            self._update_table()
    
    def _on_up(self):
        row = self.file_table.currentRow()
        if row > 0:
            self.files[row], self.files[row-1] = self.files[row-1], self.files[row]
            self._update_table()
            self.file_table.setCurrentCell(row-1, 0)
    
    def _on_down(self):
        row = self.file_table.currentRow()
        if row < len(self.files) - 1:
            self.files[row], self.files[row+1] = self.files[row+1], self.files[row]
            self._update_table()
            self.file_table.setCurrentCell(row+1, 0)
    
    def _on_clear(self):
        self.files.clear()
        self.file_table.setRowCount(0)
    
    def _on_convert(self):
        if len(self.files) < 1:
            QMessageBox.warning(self._widget, "警告", "请先添加图片文件")
            return
        
        output_path = FileDialog.save_file(self._widget, "保存PDF", "PDF文件 (*.pdf)", ".pdf")
        if not output_path:
            return
        
        progress = ProgressDialog("转换中...")
        progress.show()
        
        try:
            images = []
            for fp in self.files:
                img = Image.open(fp)
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                images.append(img)
            
            if len(images) == 1:
                images[0].save(output_path, "PDF")
            else:
                images[0].save(output_path, "PDF", save_all=True, append_images=images[1:])
            
            progress.complete("转换完成!")
            self.log_panel.info(f"已将 {len(self.files)} 张图片转为PDF: {output_path}")
            QMessageBox.information(self._widget, "成功", f"已将 {len(self.files)} 张图片转为PDF")
        except Exception as e:
            progress.close()
            self.log_panel.error(f"转换失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"转换失败:\n{str(e)}")
