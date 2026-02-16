"""
任务链触发器

多个任务依次执行
"""

import time
# 解决导入问题
try:
    from src.gui.trigger_manager import BaseTrigger
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.gui.trigger_manager import BaseTrigger


class TaskChainTrigger(BaseTrigger):
    """任务链触发器"""
    
    TRIGGER_NAME = "task_chain"
    TRIGGER_DISPLAY_NAME = "🔗 任务链"
    TRIGGER_DESCRIPTION = "多个任务依次执行"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "tasks": {
            "type": "string",
            "default": "",
            "description": "任务ID列表 (用分号分隔)"
        },
        "delay_between": {
            "type": "int",
            "default": 2,
            "description": "任务间隔时间(秒)",
            "min": 0,
            "max": 300
        },
        "stop_on_error": {
            "type": "bool",
            "default": True,
            "description": "出错时停止后续任务"
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._current_task_index = 0
        self._chain_started = False
        self._last_execution = None
    
    def _get_task_list(self) -> list:
        """获取任务ID列表"""
        tasks_str = self.config.get("tasks", "")
        if not tasks_str:
            return []
        
        return [t.strip() for t in tasks_str.split(";") if t.strip()]
    
    def should_trigger(self) -> bool:
        # 任务链触发器通常由其他触发器或手动启动
        # 这里实现一个简单的一次性触发逻辑
        tasks = self._get_task_list()
        if not tasks:
            return False
        
        if not self._chain_started:
            self._chain_started = True
            self._current_task_index = 0
            self._last_execution = time.time()
            return True
        
        # 检查是否需要执行下一个任务
        if self._current_task_index < len(tasks):
            delay = self.config.get("delay_between", 2)
            if time.time() - self._last_execution >= delay:
                self._current_task_index += 1
                self._last_execution = time.time()
                return self._current_task_index <= len(tasks)
        
        return False
    
    def get_next_trigger_info(self) -> str:
        tasks = self._get_task_list()
        if not tasks:
            return "无任务配置"
        
        if not self._chain_started:
            return f"等待启动 ({len(tasks)} 个任务)"
        
        if self._current_task_index < len(tasks):
            delay = self.config.get("delay_between", 2)
            elapsed = time.time() - self._last_execution
            remaining = max(0, delay - elapsed)
            current_task = tasks[self._current_task_index]
            return f"下个任务: {current_task} ({int(remaining)}秒后)"
        
        return "任务链已完成"
    
    def reset_chain(self):
        """重置任务链"""
        self._chain_started = False
        self._current_task_index = 0
        self._last_execution = None


# 导出触发器类
TriggerClass = TaskChainTrigger

# 独立运行测试
if __name__ == "__main__":
    def test_callback():
        print("🔗 任务链触发器触发！")
    
    trigger = TaskChainTrigger({
        "tasks": "task_001;task_002;task_003",
        "delay_between": 5,
        "stop_on_error": True
    }, test_callback)
    
    print(f"触发器信息: {trigger.get_info()}")
    print(f"任务链状态: {trigger.get_next_trigger_info()}")
