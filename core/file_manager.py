import os
import json
from typing import List, Optional
from .exceptions import FileOperationError


class FileManager:
    """文件管理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.recent_files: List[str] = []
        self._max_recent = 10
        self._load_recent_files()
    
    def _load_recent_files(self) -> None:
        """加载最近文件列表"""
        if self.config_manager:
            self.recent_files = self.config_manager.get("recent_files", [])
    
    def _save_recent_files(self) -> None:
        """保存最近文件列表"""
        if self.config_manager:
            self.config_manager.set("recent_files", self.recent_files)
            self.config_manager.save("app_config")
    
    def add_recent_file(self, filepath: str) -> None:
        """添加最近文件"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:self._max_recent]
        self._save_recent_files()
    
    def get_recent_files(self) -> List[str]:
        """获取最近文件列表"""
        return self.recent_files.copy()
    
    def clear_recent_files(self) -> None:
        """清除最近文件列表"""
        self.recent_files.clear()
        self._save_recent_files()
    
    def validate_file(self, filepath: str) -> bool:
        """验证文件是否存在且可读"""
        if not os.path.exists(filepath):
            return False
        if not os.path.isfile(filepath):
            return False
        if not os.access(filepath, os.R_OK):
            return False
        return True
    
    def get_file_extension(self, filepath: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(filepath)[1].lower()
    
    def is_excel_file(self, filepath: str) -> bool:
        """检查是否为Excel文件"""
        excel_extensions = [".xlsx", ".xls", ".xlsm", ".xlsb"]
        return self.get_file_extension(filepath) in excel_extensions
    
    def is_csv_file(self, filepath: str) -> bool:
        """检查是否为CSV文件"""
        return self.get_file_extension(filepath) == ".csv"
    
    def get_file_size(self, filepath: str) -> int:
        """获取文件大小（字节）"""
        return os.path.getsize(filepath)
    
    def format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
