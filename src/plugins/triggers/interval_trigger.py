"""
间隔触发器

每隔固定时间执行一次
"""

from datetime import datetime, timedelta
# 解决导入问题
try:
    from src.gui.trigger_manager import BaseTrigger
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.gui.trigger_manager import BaseTrigger


class IntervalTrigger(BaseTrigger):
    """间隔触发器"""
    
    TRIGGER_NAME = "interval"
    TRIGGER_DISPLAY_NAME = "🔄 间隔执行"
    TRIGGER_DESCRIPTION = "每隔固定时间执行一次"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "interval_value": {
            "type": "int",
            "default": 30,
            "description": "间隔值",
            "min": 1,
            "max": 9999
        },
        "interval_unit": {
            "type": "choice",
            "default": "minutes",
            "description": "间隔单位",
            "choices": ["seconds", "minutes", "hours"]
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._next_trigger = None
        self._calculate_next()
    
    def _calculate_next(self):
        """计算下次触发时间"""
        value = self.config.get("interval_value", 30)
        unit = self.config.get("interval_unit", "minutes")
        
        if unit == "seconds":
            delta = timedelta(seconds=value)
        elif unit == "hours":
            delta = timedelta(hours=value)
        else:
            delta = timedelta(minutes=value)
        
        self._next_trigger = datetime.now() + delta
    
    def should_trigger(self) -> bool:
        if self._next_trigger and datetime.now() >= self._next_trigger:
            self._calculate_next()
            return True
        return False
    
    def get_next_trigger_info(self) -> str:
        if self._next_trigger:
            remaining = (self._next_trigger - datetime.now()).total_seconds()
            if remaining < 0:
                return "即将触发"
            elif remaining < 60:
                return f"{int(remaining)}秒后"
            elif remaining < 3600:
                return f"{int(remaining/60)}分钟后"
            else:
                return f"{int(remaining/3600)}小时后"
        return "未知"


# 导出触发器类
TriggerClass = IntervalTrigger

# 独立运行测试
if __name__ == "__main__":
    def test_callback():
        print("✅ 间隔触发器触发！")
    
    trigger = IntervalTrigger({
        "interval_value": 5,
        "interval_unit": "seconds"
    }, test_callback)
    
    print(f"触发器信息: {trigger.get_info()}")
    print(f"下次触发: {trigger.get_next_trigger_info()}")
