"""
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
        "watch_paths": r"C:\temp;D:\projects",
        "debounce_seconds": 3
    }, test_callback)
    
    print(f"触发器信息: {trigger.get_info()}")
    print(f"监控状态: {trigger.get_next_trigger_info()}")
