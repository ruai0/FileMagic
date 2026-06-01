from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Dict, Any


class TaskManager(QWidget):
    """任务管理器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title = QLabel("任务管理器")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        clear_btn = QPushButton("清除已完成任务")
        clear_btn.clicked.connect(self._clear_completed)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(["任务名称", "状态", "进度", "开始时间", "操作"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.task_table.setColumnWidth(2, 200)
        layout.addWidget(self.task_table)
        
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总任务: 0")
        stats_layout.addWidget(self.total_label)
        self.running_label = QLabel("运行中: 0")
        stats_layout.addWidget(self.running_label)
        self.completed_label = QLabel("已完成: 0")
        stats_layout.addWidget(self.completed_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def add_task(self, task_id: str, name: str):
        """添加任务"""
        from datetime import datetime
        self.tasks[task_id] = {
            "name": name,
            "status": "运行中",
            "progress": 0,
            "start_time": datetime.now().strftime("%H:%M:%S"),
            "widget": None
        }
        self._update_table()
    
    def update_task(self, task_id: str, progress: int, status: str = None):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            if status:
                self.tasks[task_id]["status"] = status
            self._update_table()
    
    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "已完成"
            self.tasks[task_id]["progress"] = 100
            self._update_table()
    
    def fail_task(self, task_id: str, error: str = ""):
        """任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = f"失败: {error}" if error else "失败"
            self._update_table()
    
    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._update_table()
    
    def _clear_completed(self):
        """清除已完成的任务"""
        completed = [tid for tid, task in self.tasks.items() if task["status"] == "已完成"]
        for tid in completed:
            del self.tasks[tid]
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        self.task_table.setRowCount(len(self.tasks))
        
        for i, (task_id, task) in enumerate(self.tasks.items()):
            self.task_table.setItem(i, 0, QTableWidgetItem(task["name"]))
            
            status_item = QTableWidgetItem(task["status"])
            if task["status"] == "运行中":
                status_item.setForeground(Qt.GlobalColor.yellow)
            elif task["status"] == "已完成":
                status_item.setForeground(Qt.GlobalColor.green)
            elif "失败" in task["status"]:
                status_item.setForeground(Qt.GlobalColor.red)
            self.task_table.setItem(i, 1, status_item)
            
            progress_bar = QProgressBar()
            progress_bar.setValue(task["progress"])
            self.task_table.setCellWidget(i, 2, progress_bar)
            
            self.task_table.setItem(i, 3, QTableWidgetItem(task["start_time"]))
            
            if task["status"] == "运行中":
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(lambda checked, tid=task_id: self._cancel_task(tid))
                self.task_table.setCellWidget(i, 4, cancel_btn)
            else:
                remove_btn = QPushButton("移除")
                remove_btn.clicked.connect(lambda checked, tid=task_id: self.remove_task(tid))
                self.task_table.setCellWidget(i, 4, remove_btn)
        
        self.total_label.setText(f"总任务: {len(self.tasks)}")
        running = sum(1 for t in self.tasks.values() if t["status"] == "运行中")
        self.running_label.setText(f"运行中: {running}")
        completed = sum(1 for t in self.tasks.values() if t["status"] == "已完成")
        self.completed_label.setText(f"已完成: {completed}")
    
    def _cancel_task(self, task_id: str):
        """取消任务"""
        self.fail_task(task_id, "已取消")
