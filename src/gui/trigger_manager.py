"""
自定义触发器脚本管理器

支持动态加载触发器脚本，每个触发器脚本遵循标准接口：
- 参数定义 (TRIGGER_PARAMETERS)
- 触发条件检测 (should_trigger)
- 状态计算 (get_next_trigger_info)
"""

import importlib.util
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type

logger = logging.getLogger(__name__)


# ============================================
# 触发器基类接口
# ============================================

class BaseTrigger(ABC):
    """
    触发器基类
    
    所有自定义触发器必须继承此类并实现抽象方法
    """
    
    # 触发器元信息 - 子类必须定义
    TRIGGER_NAME: str = "base_trigger"
    TRIGGER_DISPLAY_NAME: str = "基础触发器"
    TRIGGER_DESCRIPTION: str = "触发器描述"
    TRIGGER_VERSION: str = "1.0.0"
    TRIGGER_AUTHOR: str = "Unknown"
    
    # 触发器参数定义
    # 格式: {"param_name": {"type": "string|int|float|bool|list", "default": value, "description": "说明"}}
    TRIGGER_PARAMETERS: Dict[str, Dict] = {}
    
    def __init__(self, config: Dict[str, Any] = None, 
                 execute_callback: Callable = None,
                 log_callback: Callable = None):
        """
        初始化触发器
        
        Args:
            config: 触发器配置参数
            execute_callback: 触发时执行的回调函数
            log_callback: 日志回调函数
        """
        self.config = config or {}
        self.execute_callback = execute_callback
        self.log_callback = log_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_trigger_time: Optional[datetime] = None
        self._trigger_count = 0
        
        # 应用默认值
        for param_name, param_def in self.TRIGGER_PARAMETERS.items():
            if param_name not in self.config:
                self.config[param_name] = param_def.get('default')
    
    def log(self, message: str, level: str = "info"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(f"[{self.TRIGGER_NAME}] {message}", level)
        else:
            getattr(logger, level, logger.info)(f"[{self.TRIGGER_NAME}] {message}")
    
    @abstractmethod
    def should_trigger(self) -> bool:
        """
        检查是否应该触发
        
        Returns:
            True 如果应该触发，False 否则
        """
        pass
    
    @abstractmethod
    def get_next_trigger_info(self) -> str:
        """
        获取下次触发的信息描述
        
        Returns:
            下次触发的描述字符串，如 "2分钟后" 或 "当条件满足时"
        """
        pass
    
    def on_trigger(self):
        """
        触发时执行的操作
        可以在子类中重写以添加自定义逻辑
        """
        self._last_trigger_time = datetime.now()
        self._trigger_count += 1
        self.log(f"触发器触发 (第 {self._trigger_count} 次)")
        
        if self.execute_callback:
            try:
                self.execute_callback()
            except Exception as e:
                self.log(f"执行回调失败: {e}", "error")
    
    def start(self):
        """启动触发器监控"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.log("触发器已启动")
    
    def stop(self):
        """停止触发器监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.log("触发器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        check_interval = self.config.get('check_interval', 1)  # 默认1秒检查一次
        
        while self._running:
            try:
                if self.should_trigger():
                    self.on_trigger()
                time.sleep(check_interval)
            except Exception as e:
                self.log(f"监控循环错误: {e}", "error")
                time.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """获取触发器状态"""
        return {
            "name": self.TRIGGER_NAME,
            "display_name": self.TRIGGER_DISPLAY_NAME,
            "running": self._running,
            "last_trigger": self._last_trigger_time.isoformat() if self._last_trigger_time else None,
            "trigger_count": self._trigger_count,
            "next_trigger_info": self.get_next_trigger_info(),
            "config": self.config
        }
    
    def get_info(self) -> Dict[str, Any]:
        """获取触发器信息"""
        return {
            "name": self.TRIGGER_NAME,
            "display_name": self.TRIGGER_DISPLAY_NAME,
            "description": self.TRIGGER_DESCRIPTION,
            "version": self.TRIGGER_VERSION,
            "author": self.TRIGGER_AUTHOR,
            "parameters": self.TRIGGER_PARAMETERS
        }


# ============================================
# 触发器脚本信息
# ============================================

@dataclass
class TriggerScriptInfo:
    """触发器脚本信息"""
    id: str                          # 唯一ID
    name: str                        # 脚本名称
    display_name: str                # 显示名称
    description: str                 # 描述
    version: str                     # 版本
    author: str                      # 作者
    file_path: str                   # 脚本文件路径
    parameters: Dict[str, Dict] = field(default_factory=dict)  # 参数定义
    enabled: bool = True             # 是否启用
    source: str = "unknown"          # 脚本来源 (shared/local)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TriggerScriptInfo':
        return cls(**data)


# ============================================
# 触发器管理器
# ============================================

class TriggerManager:
    """
    自定义触发器脚本管理器
    
    负责发现、加载和管理触发器脚本
    """
    
    def __init__(self, triggers_dir: Path = None, config_dir: Path = None):
        """
        初始化触发器管理器
        
        Args:
            triggers_dir: 触发器脚本目录
            config_dir: 配置文件目录
        """
        # 默认目录：我的文档/DCC_Tool_Manager/triggers
        if triggers_dir is None:
            docs_dir = Path.home() / "Documents" / "DCC_Tool_Manager"
            triggers_dir = docs_dir / "triggers"
        
        self.triggers_dir = Path(triggers_dir)
        self.triggers_dir.mkdir(parents=True, exist_ok=True)
        
        # 共享触发器目录（仓库内的）
        self.shared_triggers_dir = Path(__file__).parent.parent / "plugins" / "triggers"
        self.shared_triggers_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置目录
        if config_dir is None:
            config_dir = Path.home() / "Documents" / "DCC_Tool_Manager" / "config"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 已发现的触发器脚本
        self.discovered_triggers: Dict[str, TriggerScriptInfo] = {}
        
        # 已加载的触发器类
        self._trigger_classes: Dict[str, Type[BaseTrigger]] = {}
        
        # 活动的触发器实例
        self._active_triggers: Dict[str, BaseTrigger] = {}
        
        self._lock = threading.RLock()
        
        # 创建内置触发器脚本（在本地目录）
        self._create_builtin_triggers()
        
        # 创建示例触发器
        self._create_example_triggers()
        
        # 发现触发器
        self.discover_triggers()
    
    def _create_builtin_triggers(self):
        """创建内置触发器脚本（作为共享脚本）"""
        # 间隔触发器脚本 - 放在共享目录
        interval_trigger_path = self.shared_triggers_dir / "interval_trigger.py"
        if not interval_trigger_path.exists():
            interval_code = '''"""
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
'''
            try:
                with open(interval_trigger_path, 'w', encoding='utf-8') as f:
                    f.write(interval_code)
                logger.info("创建间隔触发器脚本")
            except Exception as e:
                logger.error(f"创建间隔触发器脚本失败: {e}")
        
        # 定时触发器脚本 - 放在共享目录
        scheduled_trigger_path = self.shared_triggers_dir / "scheduled_trigger.py"
        if not scheduled_trigger_path.exists():
            scheduled_code = '''"""
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
'''
            try:
                with open(scheduled_trigger_path, 'w', encoding='utf-8') as f:
                    f.write(scheduled_code)
                logger.info("创建定时触发器脚本")
            except Exception as e:
                logger.error(f"创建定时触发器脚本失败: {e}")
        
        # 文件监控触发器脚本 - 放在共享目录
        file_watch_trigger_path = self.shared_triggers_dir / "file_watch_trigger.py"
        if not file_watch_trigger_path.exists():
            file_watch_code = '''"""
文件监控触发器

当文件变化时执行
"""

import time
from pathlib import Path
# 解决导入问题
try:
    from src.gui.trigger_manager import BaseTrigger
except ImportError:
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent.parent))
    from src.gui.trigger_manager import BaseTrigger


class FileWatchTrigger(BaseTrigger):
    """文件监控触发器"""
    
    TRIGGER_NAME = "file_watch"
    TRIGGER_DISPLAY_NAME = "📁 文件监控"
    TRIGGER_DESCRIPTION = "当文件变化时执行"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "watch_paths": {
            "type": "string",
            "default": "",
            "description": "监控路径 (用分号分隔多个路径)"
        },
        "debounce_seconds": {
            "type": "int",
            "default": 5,
            "description": "防抖时间(秒) - 文件变化后等待时间",
            "min": 1,
            "max": 300
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._file_timestamps = {}
        self._last_change_time = None
    
    def _get_watch_paths(self) -> list:
        """获取监控路径列表"""
        paths_str = self.config.get("watch_paths", "")
        if not paths_str:
            return []
        
        paths = []
        for path_str in paths_str.split(";"):
            path_str = path_str.strip()
            if path_str:
                path = Path(path_str)
                if path.exists():
                    paths.append(path)
        
        return paths
    
    def _check_file_changes(self) -> bool:
        """检查文件是否有变化"""
        paths = self._get_watch_paths()
        if not paths:
            return False
        
        current_time = time.time()
        has_changes = False
        
        for path in paths:
            try:
                if path.is_file():
                    # 检查单个文件
                    mtime = path.stat().st_mtime
                    if str(path) not in self._file_timestamps:
                        self._file_timestamps[str(path)] = mtime
                    elif self._file_timestamps[str(path)] != mtime:
                        self._file_timestamps[str(path)] = mtime
                        self._last_change_time = current_time
                        has_changes = True
                
                elif path.is_dir():
                    # 检查目录下的所有文件
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            mtime = file_path.stat().st_mtime
                            key = str(file_path)
                            if key not in self._file_timestamps:
                                self._file_timestamps[key] = mtime
                            elif self._file_timestamps[key] != mtime:
                                self._file_timestamps[key] = mtime
                                self._last_change_time = current_time
                                has_changes = True
            except Exception as e:
                self.log(f"检查文件失败 {path}: {e}", "warning")
        
        return has_changes
    
    def should_trigger(self) -> bool:
        # 检查文件变化
        self._check_file_changes()
        
        # 如果没有变化，不触发
        if self._last_change_time is None:
            return False
        
        # 检查防抖时间
        debounce = self.config.get("debounce_seconds", 5)
        elapsed = time.time() - self._last_change_time
        
        if elapsed >= debounce:
            self._last_change_time = None  # 重置
            return True
        
        return False
    
    def get_next_trigger_info(self) -> str:
        paths = self._get_watch_paths()
        if not paths:
            return "无监控路径"
        
        if self._last_change_time:
            debounce = self.config.get("debounce_seconds", 5)
            elapsed = time.time() - self._last_change_time
            remaining = max(0, debounce - elapsed)
            return f"{int(remaining)}秒后触发"
        
        return f"监控 {len(paths)} 个路径"


# 导出触发器类
TriggerClass = FileWatchTrigger

# 独立运行测试
if __name__ == "__main__":
    def test_callback():
        print("📁 文件监控触发器触发！")
    
    trigger = FileWatchTrigger({
        "watch_paths": r"C:\\temp;D:\\projects",
        "debounce_seconds": 3
    }, test_callback)
    
    print(f"触发器信息: {trigger.get_info()}")
    print(f"监控状态: {trigger.get_next_trigger_info()}")
'''
            try:
                with open(file_watch_trigger_path, 'w', encoding='utf-8') as f:
                    f.write(file_watch_code)
                logger.info("创建文件监控触发器脚本")
            except Exception as e:
                logger.error(f"创建文件监控触发器脚本失败: {e}")
        
        # 任务链触发器脚本 - 放在共享目录
        task_chain_trigger_path = self.shared_triggers_dir / "task_chain_trigger.py"
        if not task_chain_trigger_path.exists():
            task_chain_code = '''"""
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
'''
            try:
                with open(task_chain_trigger_path, 'w', encoding='utf-8') as f:
                    f.write(task_chain_code)
                logger.info("创建任务链触发器脚本")
            except Exception as e:
                logger.error(f"创建任务链触发器脚本失败: {e}")
    
    def _create_example_triggers(self):
        """创建示例触发器脚本"""
        examples_dir = self.triggers_dir / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        # 示例1: CPU使用率触发器
        cpu_trigger_path = examples_dir / "cpu_usage_trigger.py"
        if not cpu_trigger_path.exists():
            cpu_trigger_code = '''"""
CPU使用率触发器

当CPU使用率超过指定阈值时触发
"""

import psutil
from src.gui.trigger_manager import BaseTrigger


class CPUUsageTrigger(BaseTrigger):
    """CPU使用率触发器"""
    
    TRIGGER_NAME = "cpu_usage"
    TRIGGER_DISPLAY_NAME = "CPU使用率触发器"
    TRIGGER_DESCRIPTION = "当CPU使用率超过指定阈值时触发工具执行"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "threshold": {
            "type": "int",
            "default": 80,
            "description": "CPU使用率阈值(%)",
            "min": 1,
            "max": 100
        },
        "duration": {
            "type": "int", 
            "default": 5,
            "description": "持续时间(秒) - CPU需持续超过阈值的时间"
        },
        "cooldown": {
            "type": "int",
            "default": 60,
            "description": "冷却时间(秒) - 触发后多久才能再次触发"
        },
        "check_interval": {
            "type": "float",
            "default": 1.0,
            "description": "检查间隔(秒)"
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._high_cpu_start = None
        self._last_trigger = None
    
    def should_trigger(self) -> bool:
        import time
        
        threshold = self.config.get("threshold", 80)
        duration = self.config.get("duration", 5)
        cooldown = self.config.get("cooldown", 60)
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            return False
        
        now = time.time()
        
        # 检查冷却时间
        if self._last_trigger and (now - self._last_trigger) < cooldown:
            return False
        
        # 检查是否超过阈值
        if cpu_percent >= threshold:
            if self._high_cpu_start is None:
                self._high_cpu_start = now
            elif (now - self._high_cpu_start) >= duration:
                self._high_cpu_start = None
                self._last_trigger = now
                return True
        else:
            self._high_cpu_start = None
        
        return False
    
    def get_next_trigger_info(self) -> str:
        threshold = self.config.get("threshold", 80)
        return f"当CPU使用率>{threshold}%时触发"


# 导出触发器类
TriggerClass = CPUUsageTrigger
'''
            try:
                with open(cpu_trigger_path, 'w', encoding='utf-8') as f:
                    f.write(cpu_trigger_code)
            except Exception as e:
                logger.error(f"创建示例触发器失败: {e}")
        
        # 示例2: 时间窗口触发器
        time_window_path = examples_dir / "time_window_trigger.py"
        if not time_window_path.exists():
            time_window_code = '''"""
时间窗口触发器

在指定的时间窗口内触发
"""

from datetime import datetime, time as dt_time
from src.gui.trigger_manager import BaseTrigger


class TimeWindowTrigger(BaseTrigger):
    """时间窗口触发器"""
    
    TRIGGER_NAME = "time_window"
    TRIGGER_DISPLAY_NAME = "时间窗口触发器"
    TRIGGER_DESCRIPTION = "在指定的时间窗口内（如工作时间9:00-18:00）每隔一定时间触发"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "start_time": {
            "type": "string",
            "default": "09:00",
            "description": "开始时间 (HH:MM格式)"
        },
        "end_time": {
            "type": "string",
            "default": "18:00",
            "description": "结束时间 (HH:MM格式)"
        },
        "interval_minutes": {
            "type": "int",
            "default": 30,
            "description": "窗口内触发间隔(分钟)"
        },
        "weekdays_only": {
            "type": "bool",
            "default": True,
            "description": "是否仅工作日触发"
        },
        "check_interval": {
            "type": "float",
            "default": 60.0,
            "description": "检查间隔(秒)"
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._last_trigger_time = None
    
    def _parse_time(self, time_str: str) -> dt_time:
        """解析时间字符串"""
        parts = time_str.split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    
    def _is_in_window(self) -> bool:
        """检查当前是否在时间窗口内"""
        now = datetime.now()
        current_time = now.time()
        
        # 检查是否是工作日
        if self.config.get("weekdays_only", True):
            if now.weekday() >= 5:  # 周六=5, 周日=6
                return False
        
        start = self._parse_time(self.config.get("start_time", "09:00"))
        end = self._parse_time(self.config.get("end_time", "18:00"))
        
        return start <= current_time <= end
    
    def should_trigger(self) -> bool:
        if not self._is_in_window():
            return False
        
        now = datetime.now()
        interval = self.config.get("interval_minutes", 30) * 60  # 转换为秒
        
        if self._last_trigger_time is None:
            self._last_trigger_time = now
            return True
        
        elapsed = (now - self._last_trigger_time).total_seconds()
        if elapsed >= interval:
            self._last_trigger_time = now
            return True
        
        return False
    
    def get_next_trigger_info(self) -> str:
        if not self._is_in_window():
            start = self.config.get("start_time", "09:00")
            return f"等待时间窗口 ({start})"
        
        interval = self.config.get("interval_minutes", 30)
        if self._last_trigger_time:
            elapsed = (datetime.now() - self._last_trigger_time).total_seconds()
            remaining = max(0, interval * 60 - elapsed)
            if remaining < 60:
                return f"{int(remaining)}秒后"
            return f"{int(remaining/60)}分钟后"
        return f"即将触发"


# 导出触发器类
TriggerClass = TimeWindowTrigger
'''
            try:
                with open(time_window_path, 'w', encoding='utf-8') as f:
                    f.write(time_window_code)
            except Exception as e:
                logger.error(f"创建示例触发器失败: {e}")
    
    def discover_triggers(self) -> List[TriggerScriptInfo]:
        """发现所有触发器脚本"""
        print(f"[DEBUG] TriggerManager.discover_triggers() 开始")
        print(f"[DEBUG] 共享目录: {self.shared_triggers_dir}")
        print(f"[DEBUG] 本地目录: {self.triggers_dir}")
        
        self.discovered_triggers.clear()
        self._trigger_classes.clear()
        
        # 扫描本地触发器目录
        print(f"[DEBUG] 扫描本地目录...")
        local_count = 0
        for trigger_file in self.triggers_dir.rglob("*_trigger.py"):
            print(f"[DEBUG] 找到本地触发器文件: {trigger_file}")
            try:
                info = self._load_trigger_info(trigger_file, source="local")
                if info:
                    self.discovered_triggers[info.id] = info
                    logger.info(f"发现本地触发器: {info.display_name}")
                    local_count += 1
                else:
                    print(f"[DEBUG] 本地触发器加载失败: {trigger_file}")
            except Exception as e:
                logger.error(f"解析触发器失败 {trigger_file}: {e}")
                print(f"[DEBUG] 本地触发器异常: {e}")
        
        print(f"[DEBUG] 本地触发器加载完成，共 {local_count} 个")
        
        # 扫描共享触发器目录
        print(f"[DEBUG] 扫描共享目录...")
        shared_count = 0
        for trigger_file in self.shared_triggers_dir.rglob("*_trigger.py"):
            print(f"[DEBUG] 找到共享触发器文件: {trigger_file}")
            try:
                # 检查是否已存在同名触发器（本地优先）
                trigger_id = f"trigger_{trigger_file.stem}"
                if trigger_id not in self.discovered_triggers:
                    info = self._load_trigger_info(trigger_file, source="shared")
                    if info:
                        self.discovered_triggers[info.id] = info
                        logger.info(f"发现共享触发器: {info.display_name}")
                        shared_count += 1
                    else:
                        print(f"[DEBUG] 共享触发器加载失败: {trigger_file}")
                else:
                    print(f"[DEBUG] 跳过重复触发器: {trigger_id}")
            except Exception as e:
                logger.error(f"解析触发器失败 {trigger_file}: {e}")
                print(f"[DEBUG] 共享触发器异常: {e}")
        
        print(f"[DEBUG] 共享触发器加载完成，共 {shared_count} 个")
        print(f"[DEBUG] 总计发现 {len(self.discovered_triggers)} 个触发器")
        
        result = list(self.discovered_triggers.values())
        for trigger in result:
            print(f"[DEBUG] 返回触发器: {trigger.display_name} (ID: {trigger.id})")
        
        return result
    
    def _load_trigger_info(self, file_path: Path, source: str = "unknown") -> Optional[TriggerScriptInfo]:
        """加载触发器脚本信息"""
        try:
            # 确保项目根路径在 sys.path 中（为了让触发器脚本能导入 src 模块）
            import sys
            import os
            
            # 尝试多种方式获取项目根路径
            current_working_dir = Path(os.getcwd())
            trigger_manager_file = Path(__file__).resolve()
            
            # 方式1: 从 trigger_manager.py 文件路径推算
            project_root_1 = trigger_manager_file.parent.parent.parent  # src/gui/trigger_manager.py -> 项目根
            
            # 方式2: 从当前工作目录推算（假设在项目根运行）
            project_root_2 = current_working_dir
            
            # 方式3: 硬编码已知路径
            project_root_3 = Path("d:/MyProject_D/AI_Tool_Framework")
            
            # 选择一个存在且包含 src 目录的路径
            for project_root in [project_root_1, project_root_2, project_root_3]:
                if project_root.exists() and (project_root / "src").exists():
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))
                        print(f"[DEBUG] 添加项目根路径到 sys.path: {project_root}")
                    break
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                f"trigger_{file_path.stem}", 
                str(file_path)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取触发器类
            trigger_class = getattr(module, 'TriggerClass', None)
            if trigger_class is None:
                # 尝试查找 BaseTrigger 的子类
                for name, obj in vars(module).items():
                    if (isinstance(obj, type) and 
                        hasattr(obj, 'TRIGGER_NAME') and
                        name != 'BaseTrigger'):
                        # 检查是否是 BaseTrigger 的子类（通过名称）
                        try:
                            if any(base.__name__ == 'BaseTrigger' for base in obj.__mro__):
                                trigger_class = obj
                                break
                        except:
                            continue
            
            if trigger_class is None:
                # 调试信息：列出模块中的所有类
                module_classes = []
                for name, obj in vars(module).items():
                    if isinstance(obj, type):
                        module_classes.append(f"{name} (bases: {[base.__name__ for base in obj.__bases__]})")
                
                logger.warning(f"未找到触发器类: {file_path}")
                logger.warning(f"模块中的类: {module_classes}")
                
                # 检查 BaseTrigger 是否可用
                try:
                    from src.gui.trigger_manager import BaseTrigger as TestBase
                    logger.warning(f"BaseTrigger 可用: {TestBase}")
                except ImportError as ie:
                    logger.warning(f"BaseTrigger 不可用: {ie}")
                
                return None
            
            # 提取信息
            trigger_id = f"trigger_{file_path.stem}"
            info = TriggerScriptInfo(
                id=trigger_id,
                name=getattr(trigger_class, 'TRIGGER_NAME', file_path.stem),
                display_name=getattr(trigger_class, 'TRIGGER_DISPLAY_NAME', file_path.stem),
                description=getattr(trigger_class, 'TRIGGER_DESCRIPTION', ''),
                version=getattr(trigger_class, 'TRIGGER_VERSION', '1.0.0'),
                author=getattr(trigger_class, 'TRIGGER_AUTHOR', 'Unknown'),
                file_path=str(file_path),
                parameters=getattr(trigger_class, 'TRIGGER_PARAMETERS', {}),
                source=source
            )
            
            # 缓存类
            self._trigger_classes[trigger_id] = trigger_class
            
            return info
            
        except Exception as e:
            logger.error(f"解析触发器失败 {file_path}: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def get_trigger_class(self, trigger_id: str) -> Optional[Type[BaseTrigger]]:
        """获取触发器类"""
        return self._trigger_classes.get(trigger_id)
    
    def create_trigger_instance(self, trigger_id: str, config: Dict = None,
                                execute_callback: Callable = None,
                                log_callback: Callable = None) -> Optional[BaseTrigger]:
        """
        创建触发器实例
        
        Args:
            trigger_id: 触发器ID
            config: 配置参数
            execute_callback: 执行回调
            log_callback: 日志回调
        
        Returns:
            触发器实例
        """
        trigger_class = self._trigger_classes.get(trigger_id)
        if trigger_class is None:
            logger.error(f"未找到触发器: {trigger_id}")
            return None
        
        try:
            return trigger_class(
                config=config,
                execute_callback=execute_callback,
                log_callback=log_callback
            )
        except Exception as e:
            logger.error(f"创建触发器实例失败: {e}")
            return None
    
    def start_trigger(self, instance_id: str, trigger_id: str, config: Dict = None,
                     execute_callback: Callable = None,
                     log_callback: Callable = None) -> bool:
        """
        启动触发器
        
        Args:
            instance_id: 实例ID（用于追踪）
            trigger_id: 触发器ID
            config: 配置参数
            execute_callback: 执行回调
            log_callback: 日志回调
        
        Returns:
            是否成功启动
        """
        with self._lock:
            if instance_id in self._active_triggers:
                logger.warning(f"触发器实例已存在: {instance_id}")
                return False
            
            instance = self.create_trigger_instance(
                trigger_id, config, execute_callback, log_callback
            )
            
            if instance is None:
                return False
            
            instance.start()
            self._active_triggers[instance_id] = instance
            return True
    
    def stop_trigger(self, instance_id: str) -> bool:
        """停止触发器"""
        with self._lock:
            if instance_id not in self._active_triggers:
                return False
            
            instance = self._active_triggers.pop(instance_id)
            instance.stop()
            return True
    
    def stop_all_triggers(self):
        """停止所有触发器"""
        with self._lock:
            for instance_id in list(self._active_triggers.keys()):
                self.stop_trigger(instance_id)
    
    def get_active_triggers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活动触发器的状态"""
        with self._lock:
            return {
                instance_id: instance.get_status()
                for instance_id, instance in self._active_triggers.items()
            }
    
    def get_all_trigger_info(self) -> List[Dict[str, Any]]:
        """获取所有已发现触发器的信息"""
        return [info.to_dict() for info in self.discovered_triggers.values()]


# ============================================
# 内置触发器
# ============================================

class IntervalTrigger(BaseTrigger):
    """间隔触发器 - 内置"""
    
    TRIGGER_NAME = "interval"
    TRIGGER_DISPLAY_NAME = "间隔触发器"
    TRIGGER_DESCRIPTION = "每隔固定时间触发一次"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "interval_value": {
            "type": "int",
            "default": 30,
            "description": "间隔值"
        },
        "interval_unit": {
            "type": "string",
            "default": "minutes",
            "description": "间隔单位 (seconds/minutes/hours)",
            "choices": ["seconds", "minutes", "hours"]
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._next_trigger = None
        self._calculate_next()
    
    def _calculate_next(self):
        """计算下次触发时间"""
        from datetime import timedelta
        
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


class ScheduledTrigger(BaseTrigger):
    """定时触发器 - 内置"""
    
    TRIGGER_NAME = "scheduled"
    TRIGGER_DISPLAY_NAME = "定时触发器"
    TRIGGER_DESCRIPTION = "在指定时间触发"
    TRIGGER_VERSION = "1.0.0"
    TRIGGER_AUTHOR = "System"
    
    TRIGGER_PARAMETERS = {
        "time": {
            "type": "string",
            "default": "09:00",
            "description": "触发时间 (HH:MM格式)"
        },
        "days": {
            "type": "list",
            "default": ["mon", "tue", "wed", "thu", "fri"],
            "description": "触发日期 (mon/tue/wed/thu/fri/sat/sun/everyday)"
        }
    }
    
    def __init__(self, config=None, execute_callback=None, log_callback=None):
        super().__init__(config, execute_callback, log_callback)
        self._triggered_today = False
        self._last_check_date = None
    
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
        days = self.config.get("days", ["everyday"])
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
        days = self.config.get("days", ["everyday"])
        
        if "everyday" in days:
            return f"每天 {time_str}"
        else:
            days_str = ",".join(days)
            return f"{time_str} ({days_str})"
