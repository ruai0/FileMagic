import os
from typing import Dict, Any, Optional
from pypdf import PdfReader, PdfWriter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox,
    QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from ui.widgets.file_drop_zone import FileDropZone
from ui.widgets.log_panel import LogPanel
from core.plugin_manager import BasePlugin
from ui.dialogs.file_dialog import FileDialog


class Plugin(BasePlugin):
    """PDF加密插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "PDF加密"
        self.description = "给PDF设置密码保护"
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
        
        file_group = QGroupBox("PDF文件")
        file_layout = QVBoxLayout()
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._on_file_dropped)
        file_layout.addWidget(self.drop_zone)
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("padding: 10px; color: #666;")
        file_layout.addWidget(self.file_label)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        opts_group = QGroupBox("密码设置")
        opts_layout = QVBoxLayout()
        
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("打开密码:"))
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("输入打开密码")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_layout.addWidget(self.pwd_input)
        opts_layout.addLayout(pwd_layout)
        
        owner_layout = QHBoxLayout()
        owner_layout.addWidget(QLabel("权限密码:"))
        self.owner_input = QLineEdit()
        self.owner_input.setPlaceholderText("输入权限密码（可选）")
        self.owner_input.setEchoMode(QLineEdit.EchoMode.Password)
        owner_layout.addWidget(self.owner_input)
        opts_layout.addLayout(owner_layout)
        
        self.no_print_check = QCheckBox("禁止打印")
        opts_layout.addWidget(self.no_print_check)
        
        self.no_copy_check = QCheckBox("禁止复制内容")
        opts_layout.addWidget(self.no_copy_check)
        
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)
        
        encrypt_btn = QPushButton("开始加密")
        encrypt_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 10px; font-size: 14px;")
        encrypt_btn.clicked.connect(self._on_encrypt)
        layout.addWidget(encrypt_btn)
        
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        
        return widget
    
    def _on_file_dropped(self, filepaths):
        if filepaths:
            self.source_file = filepaths[0]
            self.file_label.setText(f"已选择: {os.path.basename(self.source_file)}")
    
    def _on_encrypt(self):
        if not self.source_file:
            QMessageBox.warning(self._widget, "警告", "请先选择PDF文件")
            return
        
        pwd = self.pwd_input.text()
        if not pwd:
            QMessageBox.warning(self._widget, "警告", "请输入密码")
            return
        
        output_path = FileDialog.save_file(self._widget, "保存加密PDF", "PDF文件 (*.pdf)", ".pdf")
        if not output_path:
            return
        
        try:
            reader = PdfReader(self.source_file)
            writer = PdfWriter()
            
            for page in reader.pages:
                writer.add_page(page)
            
            owner_pwd = self.owner_input.text() or None
            
            permissions = 0
            if self.no_print_check.isChecked():
                permissions |= 0b000000000001
            if self.no_copy_check.isChecked():
                permissions |= 0b000000001000
            
            writer.encrypt(
                user_password=pwd,
                owner_password=owner_pwd,
                permissions_flag=permissions
            )
            
            with open(output_path, "wb") as f:
                writer.write(f)
            
            self.log_panel.info(f"已加密: {output_path}")
            QMessageBox.information(self._widget, "成功", "PDF加密完成")
        except Exception as e:
            self.log_panel.error(f"加密失败: {str(e)}")
            QMessageBox.critical(self._widget, "错误", f"加密失败:\n{str(e)}")
