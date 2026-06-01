from PyQt6.QtWidgets import QFileDialog, QWidget
from typing import List, Tuple, Optional


class FileDialog:
    """文件选择对话框"""
    
    EXCEL_FILTER = "Excel文件 (*.xlsx *.xls *.xlsm *.xlsb)"
    CSV_FILTER = "CSV文件 (*.csv)"
    ALL_FILES = "所有文件 (*)"
    
    @staticmethod
    def open_file(
        parent: Optional[QWidget] = None,
        title: str = "打开文件",
        filter: str = "所有文件 (*)"
    ) -> Optional[str]:
        """打开单个文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            parent, title, "", filter
        )
        return filepath if filepath else None
    
    @staticmethod
    def open_files(
        parent: Optional[QWidget] = None,
        title: str = "打开文件",
        filter: str = "所有文件 (*)"
    ) -> List[str]:
        """打开多个文件"""
        filepaths, _ = QFileDialog.getOpenFileNames(
            parent, title, "", filter
        )
        return filepaths
    
    @staticmethod
    def open_excel(
        parent: Optional[QWidget] = None,
        title: str = "打开Excel文件"
    ) -> Optional[str]:
        """打开Excel文件"""
        return FileDialog.open_file(
            parent,
            title,
            f"{FileDialog.EXCEL_FILTER};;{FileDialog.CSV_FILTER};;{FileDialog.ALL_FILES}"
        )
    
    @staticmethod
    def open_csv(
        parent: Optional[QWidget] = None,
        title: str = "打开CSV文件"
    ) -> Optional[str]:
        """打开CSV文件"""
        return FileDialog.open_file(
            parent,
            title,
            f"{FileDialog.CSV_FILTER};;{FileDialog.ALL_FILES}"
        )
    
    @staticmethod
    def save_file(
        parent: Optional[QWidget] = None,
        title: str = "保存文件",
        filter: str = "所有文件 (*)",
        default_suffix: str = ""
    ) -> Optional[str]:
        """保存文件"""
        filepath, _ = QFileDialog.getSaveFileName(
            parent, title, "", filter, None,
            QFileDialog.Option.DontUseNativeDialog
        )
        return filepath if filepath else None
    
    @staticmethod
    def save_excel(
        parent: Optional[QWidget] = None,
        title: str = "保存Excel文件"
    ) -> Optional[str]:
        """保存Excel文件"""
        return FileDialog.save_file(
            parent,
            title,
            FileDialog.EXCEL_FILTER,
            ".xlsx"
        )
    
    @staticmethod
    def save_csv(
        parent: Optional[QWidget] = None,
        title: str = "保存CSV文件"
    ) -> Optional[str]:
        """保存CSV文件"""
        return FileDialog.save_file(
            parent,
            title,
            FileDialog.CSV_FILTER,
            ".csv"
        )
    
    @staticmethod
    def select_directory(
        parent: Optional[QWidget] = None,
        title: str = "选择目录"
    ) -> Optional[str]:
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(
            parent, title, "",
            QFileDialog.Option.DontUseNativeDialog
        )
        return directory if directory else None
