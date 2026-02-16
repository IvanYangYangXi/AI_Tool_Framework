"""
定时触发器

在指定时间执行
"""

from datetime import datetime
# 解决导入问题
try:
    from src.gui.trigger_manager import BaseTrigger
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.gui.trigger_manager import BaseTrigger


class ScheduledTrigger(BaseTrigger):
    """定时触发器"""
    
    TRIGGER_NAME = "scheduled"
    TRIGGER_DISPLAY_NAME = "⏰ 定时执行"
    TRIGGER_DESCRIPTION = "在指定时间执行"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "time": {
            "type": "string",
            "default": "09:00",
            "description": "触发时间 (HH:MM格式)"
        },
        "days": {
            "type": "string",
            "default": "周一,周二,周三,周四,周五",
            "description": "执行日期 (用逗号分隔，如: 周一,周三,周五 或 每天)"
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._triggered_today = False
        self._last_check_date = None
    
    def _parse_days(self, days_str: str) -> list:
        """解析日期字符串"""
        if not days_str or days_str.strip() == "每天":
            return ["everyday"]
        
        # 中文到英文映射
        day_map = {
            "周一": "mon", "周二": "tue", "周三": "wed", "周四": "thu", 
            "周五": "fri", "周六": "sat", "周日": "sun"
        }
        
        days = []
        for day in days_str.split(","):
            day = day.strip()
            if day in day_map:
                days.append(day_map[day])
            elif day in day_map.values():
                days.append(day)
        
        return days or ["everyday"]
    
    def should_trigger(self) -> bool:
        now = datetime.now()
        today = now.date()
        
        # 新的一天重置标志
        if self._last_check_date != today:
            self._last_check_date = today
            self._triggered_today = False
        
        if self._triggered_today:
            return False
        
        # 检查是否是指定日期
        days_str = self.config.get("days", "周一,周二,周三,周四,周五")
        days = self._parse_days(days_str)
        
        if "everyday" not in days:
            day_abbr = now.strftime("%a").lower()[:3]
            if day_abbr not in days:
                return False
        
        # 检查时间
        time_str = self.config.get("time", "09:00")
        try:
            hour, minute = map(int, time_str.split(":"))
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 在目标时间后1分钟内触发
            if target_time <= now <= target_time.replace(second=59):
                self._triggered_today = True
                return True
        except:
            pass
        
        return False
    
    def get_next_trigger_info(self) -> str:
        time_str = self.config.get("time", "09:00")
        days_str = self.config.get("days", "周一,周二,周三,周四,周五")
        
        if days_str.strip() == "每天":
            return f"每天 {time_str}"
        else:
            return f"{time_str} ({days_str})"


# 导出触发器类
TriggerClass = ScheduledTrigger

# 独立运行测试
if __name__ == "__main__":
    def test_callback():
        print("⏰ 定时触发器触发！")
    
    trigger = ScheduledTrigger({
        "time": "14:30",
        "days": "周一,周三,周五"
    }, test_callback)
    
    print(f"触发器信息: {trigger.get_info()}")
    print(f"下次触发: {trigger.get_next_trigger_info()}")
