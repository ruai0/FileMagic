import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt


@dataclass
class Operation:
    """操作记录"""
    id: str
    name: str
    plugin: str
    params: Dict[str, Any]
    timestamp: str
    status: str = "pending"
    result: Optional[str] = None


class OperationHistory:
    """操作历史管理器"""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.history_file = os.path.join(config_dir, "operation_history.json")
        self.operations: List[Operation] = []
        self.undos: List[Operation] = []
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.operations = [Operation(**op) for op in data.get("operations", [])]
            except:
                self.operations = []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump({"operations": [asdict(op) for op in self.operations]}, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_operation(self, name: str, plugin: str, params: Dict[str, Any] = None):
        """添加操作记录"""
        op = Operation(
            id=f"op_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            name=name,
            plugin=plugin,
            params=params or {},
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.operations.insert(0, op)
        if len(self.operations) > 100:
            self.operations = self.operations[:100]
        self._save_history()
        return op.id
    
    def complete_operation(self, op_id: str, result: str = "成功"):
        """完成操作"""
        for op in self.operations:
            if op.id == op_id:
                op.status = "completed"
                op.result = result
                self._save_history()
                break
    
    def fail_operation(self, op_id: str, error: str):
        """操作失败"""
        for op in self.operations:
            if op.id == op_id:
                op.status = "failed"
                op.result = error
                self._save_history()
                break
    
    def add_undo(self, operation: Operation):
        """添加撤销记录"""
        self.undos.append(operation)
        if len(self.undos) > 20:
            self.undos = self.undos[20:]
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return len(self.undos) > 0
    
    def undo(self) -> Optional[Operation]:
        """撤销操作"""
        if self.undos:
            return self.undos.pop()
        return None
    
    def get_history(self, limit: int = 50) -> List[Operation]:
        """获取历史记录"""
        return self.operations[:limit]
    
    def clear_history(self):
        """清空历史记录"""
        self.operations.clear()
        self.undos.clear()
        self._save_history()


class HistoryWidget(QWidget):
    """历史记录组件"""
    
    def __init__(self, history: OperationHistory, parent=None):
        super().__init__(parent)
        self.history = history
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("操作历史")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        
        clear_btn = QPushButton("清空历史")
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["操作名称", "插件", "时间", "状态", "结果"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        history = self.history.get_history()
        self.table.setRowCount(len(history))
        
        for i, op in enumerate(history):
            self.table.setItem(i, 0, QTableWidgetItem(op.name))
            self.table.setItem(i, 1, QTableWidgetItem(op.plugin))
            self.table.setItem(i, 2, QTableWidgetItem(op.timestamp))
            
            status_item = QTableWidgetItem(op.status)
            if op.status == "completed":
                status_item.setForeground(Qt.GlobalColor.green)
            elif op.status == "failed":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(i, 3, status_item)
            
            self.table.setItem(i, 4, QTableWidgetItem(op.result or ""))
    
    def _clear_history(self):
        """清空历史"""
        self.history.clear_history()
        self._update_table()
    
    def refresh(self):
        """刷新表格"""
        self._update_table()
