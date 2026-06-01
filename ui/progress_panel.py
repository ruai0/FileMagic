from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QGroupBox, QListWidget,
    QListWidgetItem, QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from typing import Dict, Optional
from datetime import datetime


class ProgressPanel(QWidget):
    """进度显示面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: Dict[str, dict] = {}
        self._setup_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_ui)
        self.timer.start(500)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        title = QLabel("📊 任务进度")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        
        self.clear_btn = QPushButton("清除完成")
        self.clear_btn.clicked.connect(self._clear_completed)
        header.addWidget(self.clear_btn)
        
        layout.addLayout(header)
        
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 5px;
                background: rgba(255,255,255,0.03);
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
        """)
        layout.addWidget(self.task_list)
        
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总任务: 0")
        self.running_label = QLabel("运行中: 0")
        self.completed_label = QLabel("已完成: 0")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.running_label)
        stats_layout.addWidget(self.completed_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def add_task(self, task_id: str, name: str, total: int = 100):
        """添加任务"""
        self.tasks[task_id] = {
            "name": name,
            "current": 0,
            "total": total,
            "status": "running",
            "start_time": datetime.now(),
            "message": ""
        }
        self._update_list()
    
    def update_progress(self, task_id: str, current: int, message: str = ""):
        """更新进度"""
        if task_id in self.tasks:
            self.tasks[task_id]["current"] = current
            if message:
                self.tasks[task_id]["message"] = message
            self._update_list()
    
    def complete_task(self, task_id: str, message: str = "完成"):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["current"] = self.tasks[task_id]["total"]
            self.tasks[task_id]["message"] = message
            self._update_list()
    
    def fail_task(self, task_id: str, error: str = "失败"):
        """任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["message"] = error
            self._update_list()
    
    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._update_list()
    
    def _clear_completed(self):
        """清除已完成的任务"""
        completed = [tid for tid, t in self.tasks.items() if t["status"] in ["completed", "failed"]]
        for tid in completed:
            del self.tasks[tid]
        self._update_list()
    
    def _update_list(self):
        """更新列表"""
        self.task_list.clear()
        
        for task_id, task in self.tasks.items():
            progress = int(task["current"] / task["total"] * 100) if task["total"] > 0 else 0
            
            status_icon = "⏳" if task["status"] == "running" else "✅" if task["status"] == "completed" else "❌"
            
            item_text = f"{status_icon} {task['name']}"
            if task["message"]:
                item_text += f" - {task['message']}"
            item_text += f" [{progress}%]"
            
            item = QListWidgetItem(item_text)
            if task["status"] == "completed":
                item.setForeground(Qt.GlobalColor.green)
            elif task["status"] == "failed":
                item.setForeground(Qt.GlobalColor.red)
            
            self.task_list.addItem(item)
        
        total = len(self.tasks)
        running = sum(1 for t in self.tasks.values() if t["status"] == "running")
        completed = sum(1 for t in self.tasks.values() if t["status"] == "completed")
        
        self.total_label.setText(f"总任务: {total}")
        self.running_label.setText(f"运行中: {running}")
        self.completed_label.setText(f"已完成: {completed}")
    
    def _update_ui(self):
        """定时更新UI"""
        pass
