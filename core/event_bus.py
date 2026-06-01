from typing import Callable, Dict, List, Any
from collections import defaultdict


class EventBus:
    """事件总线 - 插件间通信机制"""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, event: str, callback: Callable) -> None:
        """订阅事件"""
        self._listeners[event].append(callback)
    
    def unsubscribe(self, event: str, callback: Callable) -> None:
        """取消订阅"""
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)
    
    def publish(self, event: str, data: Any = None) -> None:
        """发布事件"""
        for callback in self._listeners[event]:
            try:
                callback(data)
            except Exception as e:
                print(f"Event callback error for {event}: {e}")
    
    def clear(self) -> None:
        """清除所有监听器"""
        self._listeners.clear()
