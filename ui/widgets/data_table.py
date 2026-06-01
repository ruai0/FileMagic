from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from typing import List, Any, Optional


class DataTable(QTableWidget):
    """数据表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
    
    def load_data(self, headers: List[str], data: List[List[Any]]):
        """加载数据"""
        self.setColumnCount(len(headers))
        self.setRowCount(len(data))
        self.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, col_idx, item)
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def clear_data(self):
        """清除数据"""
        self.clearContents()
        self.setRowCount(0)
        self.setColumnCount(0)
    
    def get_selected_row(self) -> Optional[int]:
        """获取选中的行索引"""
        selected = self.currentRow()
        return selected if selected >= 0 else None
    
    def get_row_data(self, row: int) -> List[str]:
        """获取指定行的数据"""
        data = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            data.append(item.text() if item else "")
        return data
