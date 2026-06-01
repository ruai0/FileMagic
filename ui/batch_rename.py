import os
import re
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QCheckBox,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt


class BatchRenamer(QWidget):
    """批量重命名工具"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("📝 批量重命名")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout()
        
        btn_row = QHBoxLayout()
        add_files_btn = QPushButton("添加文件")
        add_files_btn.clicked.connect(self._add_files)
        btn_row.addWidget(add_files_btn)
        
        add_dir_btn = QPushButton("添加目录")
        add_dir_btn.clicked.connect(self._add_directory)
        btn_row.addWidget(add_dir_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(clear_btn)
        file_layout.addLayout(btn_row)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["原文件名", "新文件名", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        file_layout.addWidget(self.file_table)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        options_group = QGroupBox("重命名规则")
        options_layout = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "添加前缀",
            "添加后缀",
            "替换文本",
            "删除文本",
            "序号命名",
            "正则替换",
            "日期前缀"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        options_layout.addLayout(mode_layout)
        
        param1_layout = QHBoxLayout()
        param1_layout.addWidget(QLabel("参数1:"))
        self.param1_input = QLineEdit()
        self.param1_input.setPlaceholderText("输入参数")
        param1_layout.addWidget(self.param1_input)
        options_layout.addLayout(param1_layout)
        
        param2_layout = QHBoxLayout()
        param2_layout.addWidget(QLabel("参数2:"))
        self.param2_input = QLineEdit()
        self.param2_input.setPlaceholderText("输入参数（可选）")
        param2_layout.addWidget(self.param2_input)
        options_layout.addLayout(param2_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        preview_btn = QPushButton("预览结果")
        preview_btn.clicked.connect(self._preview)
        layout.addWidget(preview_btn)
        
        exec_layout = QHBoxLayout()
        exec_btn = QPushButton("执行重命名")
        exec_btn.setStyleSheet("background-color: #00d4aa; color: white; padding: 10px;")
        exec_btn.clicked.connect(self._execute)
        exec_layout.addWidget(exec_btn)
        layout.addLayout(exec_layout)
    
    def _add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "所有文件 (*);;Excel文件 (*.xlsx *.xls);;PDF文件 (*.pdf);;Word文件 (*.docx)"
        )
        if files:
            self.files.extend(files)
            self._update_table()
    
    def _add_directory(self):
        """添加目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            for f in os.listdir(dir_path):
                filepath = os.path.join(dir_path, f)
                if os.path.isfile(filepath):
                    self.files.append(filepath)
            self._update_table()
    
    def _clear_files(self):
        """清空文件"""
        self.files.clear()
        self.file_table.setRowCount(0)
    
    def _update_table(self):
        """更新表格"""
        self.file_table.setRowCount(len(self.files))
        for i, filepath in enumerate(self.files):
            self.file_table.setItem(i, 0, QTableWidgetItem(os.path.basename(filepath)))
            self.file_table.setItem(i, 2, QTableWidgetItem("待处理"))
    
    def _on_mode_changed(self, index):
        """模式改变"""
        hints = [
            "输入要添加的前缀",
            "输入要添加的后缀",
            "格式: 旧文本:新文本",
            "输入要删除的文本",
            "格式: 前缀_起始数字",
            "格式: 正则表达式:替换文本",
            "无需参数"
        ]
        self.param1_input.setPlaceholderText(hints[index])
    
    def _preview(self):
        """预览结果"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
        
        new_names = self._generate_names()
        
        for i, (old_path, new_name) in enumerate(zip(self.files, new_names)):
            self.file_table.setItem(i, 1, QTableWidgetItem(new_name))
            self.file_table.setItem(i, 2, QTableWidgetItem("就绪"))
    
    def _generate_names(self) -> List[str]:
        """生成新文件名"""
        mode = self.mode_combo.currentIndex()
        param1 = self.param1_input.text()
        param2 = self.param2_input.text()
        
        new_names = []
        for i, filepath in enumerate(self.files):
            name = os.path.basename(filepath)
            name_no_ext, ext = os.path.splitext(name)
            
            if mode == 0:
                new_name = f"{param1}{name}"
            elif mode == 1:
                new_name = f"{name_no_ext}{param1}{ext}"
            elif mode == 2:
                parts = param1.split(":")
                if len(parts) == 2:
                    new_name = name.replace(parts[0], parts[1])
                else:
                    new_name = name
            elif mode == 3:
                new_name = name.replace(param1, "")
            elif mode == 4:
                parts = param1.split("_")
                if len(parts) == 2:
                    prefix = parts[0]
                    start_num = int(parts[1])
                    new_name = f"{prefix}_{start_num + i:03d}{ext}"
                else:
                    new_name = name
            elif mode == 5:
                try:
                    new_name = re.sub(param1, param2, name)
                except:
                    new_name = name
            elif mode == 6:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y%m%d_")
                new_name = f"{date_str}{name}"
            else:
                new_name = name
            
            new_names.append(new_name)
        
        return new_names
    
    def _execute(self):
        """执行重命名"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
        
        reply = QMessageBox.question(
            self, "确认",
            f"确定要重命名 {len(self.files)} 个文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        new_names = self._generate_names()
        success = 0
        
        for i, (old_path, new_name) in enumerate(zip(self.files, new_names)):
            try:
                dir_path = os.path.dirname(old_path)
                new_path = os.path.join(dir_path, new_name)
                os.rename(old_path, new_path)
                self.file_table.setItem(i, 2, QTableWidgetItem("✅ 完成"))
                success += 1
            except Exception as e:
                self.file_table.setItem(i, 2, QTableWidgetItem(f"❌ {str(e)[:20]}"))
        
        QMessageBox.information(self, "完成", f"成功重命名 {success}/{len(self.files)} 个文件")
