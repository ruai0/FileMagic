import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt
from typing import Optional


class FilePreview(QWidget):
    """文件预览组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self.file_label)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #888;")
        header.addWidget(self.info_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        self.tabs = QTabWidget()
        
        self.text_tab = QTextEdit()
        self.text_tab.setReadOnly(True)
        self.tabs.addTab(self.text_tab, "文本内容")
        
        self.table_tab = QTableWidget()
        self.table_tab.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.table_tab, "表格数据")
        
        self.info_tab = QTextEdit()
        self.info_tab.setReadOnly(True)
        self.tabs.addTab(self.info_tab, "文件信息")
        
        layout.addWidget(self.tabs)
    
    def preview_file(self, filepath: str):
        """预览文件"""
        if not os.path.exists(filepath):
            self.file_label.setText("文件不存在")
            return
        
        self.current_file = filepath
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        
        self.file_label.setText(filename)
        self.info_label.setText(self._format_size(size))
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in [".txt", ".py", ".js", ".html", ".css", ".json", ".xml", ".csv"]:
            self._preview_text(filepath)
            self.tabs.setCurrentIndex(0)
        elif ext in [".xlsx", ".xls"]:
            self._preview_excel(filepath)
            self.tabs.setCurrentIndex(1)
        elif ext in [".pdf"]:
            self._preview_pdf(filepath)
            self.tabs.setCurrentIndex(0)
        elif ext in [".docx", ".doc"]:
            self._preview_word(filepath)
            self.tabs.setCurrentIndex(0)
        else:
            self._preview_binary(filepath)
            self.tabs.setCurrentIndex(2)
        
        self._show_file_info(filepath)
    
    def _preview_text(self, filepath: str):
        """预览文本文件"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
            self.text_tab.setPlainText(content)
        except Exception as e:
            self.text_tab.setPlainText(f"读取失败: {str(e)}")
    
    def _preview_excel(self, filepath: str):
        """预览Excel文件"""
        try:
            import pandas as pd
            df = pd.read_excel(filepath, nrows=100)
            
            headers = list(df.columns)
            data = df.head(50).values.tolist()
            
            self.table_tab.setColumnCount(len(headers))
            self.table_tab.setRowCount(min(len(data), 50))
            self.table_tab.setHorizontalHeaderLabels(headers)
            
            for i, row in enumerate(data):
                for j, val in enumerate(row):
                    self.table_tab.setItem(i, j, QTableWidgetItem(str(val)[:50]))
            
            self.text_tab.setPlainText(f"共 {len(df)} 行, {len(headers)} 列\n\n列名: {', '.join(headers)}")
        except Exception as e:
            self.text_tab.setPlainText(f"读取失败: {str(e)}")
    
    def _preview_pdf(self, filepath: str):
        """预览PDF文件"""
        try:
            import fitz
            doc = fitz.open(filepath)
            
            text = f"共 {len(doc.page)} 页\n\n"
            for i in range(min(3, len(doc.page))):
                page = doc[i]
                text += f"--- 第 {i+1} 页 ---\n"
                text += page.get_text()[:2000] + "\n\n"
            
            self.text_tab.setPlainText(text)
            doc.close()
        except Exception as e:
            self.text_tab.setPlainText(f"读取失败: {str(e)}\n\n需要安装 PyMuPDF 库")
    
    def _preview_word(self, filepath: str):
        """预览Word文件"""
        try:
            from docx import Document
            doc = Document(filepath)
            
            text = ""
            for para in doc.paragraphs[:100]:
                if para.text.strip():
                    text += para.text + "\n"
            
            self.text_tab.setPlainText(text)
        except Exception as e:
            self.text_tab.setPlainText(f"读取失败: {str(e)}\n\n需要安装 python-docx 库")
    
    def _preview_binary(self, filepath: str):
        """预览二进制文件"""
        try:
            with open(filepath, "rb") as f:
                data = f.read(1000)
            
            hex_str = " ".join(f"{b:02x}" for b in data[:200])
            self.text_tab.setPlainText(f"二进制文件预览:\n\n{hex_str}...")
        except Exception as e:
            self.text_tab.setPlainText(f"读取失败: {str(e)}")
    
    def _show_file_info(self, filepath: str):
        """显示文件信息"""
        stat = os.stat(filepath)
        
        info = f"""文件信息:
        
文件名: {os.path.basename(filepath)}
完整路径: {filepath}
文件大小: {self._format_size(stat.st_size)}
创建时间: {self._format_time(stat.st_ctime)}
修改时间: {self._format_time(stat.st_mtime)}
访问时间: {self._format_time(stat.st_atime)}
文件扩展名: {os.path.splitext(filepath)[1]}"""
        
        self.info_tab.setPlainText(info)
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    def clear(self):
        """清空预览"""
        self.current_file = None
        self.file_label.setText("未选择文件")
        self.info_label.setText("")
        self.text_tab.clear()
        self.table_tab.clear()
        self.info_tab.clear()
