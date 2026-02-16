"""
自动化任务管理器

支持的触发器类型：
1. 定时执行 - 在指定时间运行工具
2. 间隔执行 - 每隔一段时间运行
3. 文件监控 - 当特定文件/目录变化时触发
4. 任务链 - 多个工具依次执行
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import hashlib
import os

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """触发器类型"""
    SCHEDULED = "scheduled"      # 定时执行（每天/每周特定时间）
    INTERVAL = "interval"        # 间隔执行（每隔N分钟/小时）
    FILE_WATCH = "file_watch"    # 文件监控
    TASK_CHAIN = "task_chain"    # 任务链
    CUSTOM = "custom"            # 自定义触发器脚本


class TaskStatus(Enum):
    """任务状态"""
    IDLE = "idle"                # 空闲
    WAITING = "waiting"          # 等待触发
    RUNNING = "running"          # 运行中
    PAUSED = "paused"            # 已暂停
    ERROR = "error"              # 错误
    COMPLETED = "completed"      # 已完成


@dataclass
class ScheduledConfig:
    """定时执行配置"""
    time: str = "09:00"          # 执行时间 HH:MM
    days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"])
    # 支持: mon, tue, wed, thu, fri, sat, sun, everyday


@dataclass
class IntervalConfig:
    """间隔执行配置"""
    value: int = 30              # 间隔值
    unit: str = "minutes"        # 单位: seconds, minutes, hours


@dataclass
class FileWatchConfig:
    """文件监控配置"""
    watch_paths: List[str] = field(default_factory=list)   # 监控路径
    patterns: List[str] = field(default_factory=lambda: ["*"])  # 文件模式
    events: List[str] = field(default_factory=lambda: ["modified", "created"])
    debounce_seconds: int = 5    # 防抖时间


@dataclass
class TaskChainConfig:
    """任务链配置"""
    tasks: List[str] = field(default_factory=list)  # 任务ID列表
    stop_on_error: bool = True   # 出错时停止
    delay_between: int = 2       # 任务间延迟（秒）


@dataclass
class CustomTriggerConfig:
    """自定义触发器配置"""
    trigger_script_id: str = ""      # 触发器脚本ID
    trigger_parameters: Dict[str, Any] = field(default_factory=dict)  # 触发器参数


@dataclass
class AutomationTask:
    """自动化任务"""
    id: str                      # 任务唯一ID
    name: str                    # 任务名称
    enabled: bool = True         # 是否启用
    trigger_type: str = "interval"  # 触发类型
    
    # 工具信息
    tool_id: str = ""            # 工具ID
    tool_category: str = ""      # 工具分类 (maya, max, blender, ue, other)
    execution_mode: str = "standalone"  # 执行模式 (standalone, dcc)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 触发器配置
    scheduled_config: Optional[Dict] = None
    interval_config: Optional[Dict] = None
    file_watch_config: Optional[Dict] = None
    task_chain_config: Optional[Dict] = None
    custom_trigger_config: Optional[Dict] = None  # 自定义触发器配置
    
    # 运行时状态
    status: str = "idle"
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    last_error: Optional[str] = None
    
    # 创建/修改时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AutomationTask':
        """从字典创建"""
        # 过滤掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class AutomationManager:
    """自动化任务管理器"""
    
    def __init__(self, config_dir: Path, execute_callback: Callable = None):
        """
        初始化自动化管理器
        
        Args:
            config_dir: 配置文件目录
            execute_callback: 执行工具的回调函数 (tool_id, category, mode, params) -> result
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "automation_tasks.json"
        self.execute_callback = execute_callback
        
        self.tasks: Dict[str, AutomationTask] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._file_watchers: Dict[str, threading.Thread] = {}
        self._file_hashes: Dict[str, str] = {}  # 文件监控用的哈希缓存
        self._lock = threading.RLock()
        
        # 状态变更回调
        self.on_task_status_change: Optional[Callable] = None
        self.on_task_executed: Optional[Callable] = None
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载任务
        self._load_tasks()
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def _load_tasks(self):
        """加载任务配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = AutomationTask.from_dict(task_data)
                        # 根据 enabled 状态修正 status
                        if task.enabled:
                            # 如果任务启用，状态应该是 waiting（除非正在运行或出错）
                            if task.status not in ['running', 'error']:
                                task.status = 'waiting'
                        else:
                            task.status = 'paused'
                        self.tasks[task.id] = task
                logger.info(f"加载了 {len(self.tasks)} 个自动化任务")
            except Exception as e:
                logger.error(f"加载任务配置失败: {e}")
    
    def _save_tasks(self):
        """保存任务配置"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "tasks": [task.to_dict() for task in self.tasks.values()]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"保存了 {len(self.tasks)} 个自动化任务")
        except Exception as e:
            logger.error(f"保存任务配置失败: {e}")
    
    def create_task(self, name: str, trigger_type: TriggerType, 
                   tool_id: str, tool_category: str,
                   execution_mode: str = "standalone",
                   parameters: Dict = None,
                   trigger_config: Dict = None) -> AutomationTask:
        """
        创建新任务
        
        Args:
            name: 任务名称
            trigger_type: 触发类型
            tool_id: 工具ID
            tool_category: 工具分类
            execution_mode: 执行模式
            parameters: 工具参数
            trigger_config: 触发器配置
        
        Returns:
            创建的任务对象
        """
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = AutomationTask(
            id=task_id,
            name=name,
            trigger_type=trigger_type.value,
            tool_id=tool_id,
            tool_category=tool_category,
            execution_mode=execution_mode,
            parameters=parameters or {},
            status="waiting"  # 新建任务默认为等待状态
        )
        
        # 设置触发器配置
        if trigger_config:
            if trigger_type == TriggerType.SCHEDULED:
                task.scheduled_config = trigger_config
            elif trigger_type == TriggerType.INTERVAL:
                task.interval_config = trigger_config
            elif trigger_type == TriggerType.FILE_WATCH:
                task.file_watch_config = trigger_config
            elif trigger_type == TriggerType.TASK_CHAIN:
                task.task_chain_config = trigger_config
            elif trigger_type == TriggerType.CUSTOM:
                task.custom_trigger_config = trigger_config
        
        # 计算下次运行时间
        task.next_run = self._calculate_next_run(task)
        
        with self._lock:
            self.tasks[task_id] = task
            self._save_tasks()
        
        logger.info(f"创建任务: {name} ({task_id})")
        return task
    
    def update_task(self, task_id: str, **kwargs) -> Optional[AutomationTask]:
        """更新任务"""
        with self._lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            task.updated_at = datetime.now().isoformat()
            task.next_run = self._calculate_next_run(task)
            
            self._save_tasks()
            return task
    
    def update_task_full(self, task_id: str, name: str = None, trigger_type: TriggerType = None,
                        enabled: bool = None, trigger_config: Dict[str, Any] = None) -> Optional[AutomationTask]:
        """完整更新任务（包括触发器配置）"""
        with self._lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            
            # 更新基本信息
            if name is not None:
                task.name = name
            if enabled is not None:
                task.enabled = enabled
            
            # 更新触发器类型和配置
            if trigger_type is not None:
                task.trigger_type = trigger_type.value
                
                # 清除旧的配置
                task.interval_config = None
                task.scheduled_config = None  
                task.file_watch_config = None
                task.task_chain_config = None
                task.custom_trigger_config = None
                
                # 设置新配置
                if trigger_config:
                    if trigger_type == TriggerType.INTERVAL:
                        task.interval_config = trigger_config
                    elif trigger_type == TriggerType.SCHEDULED:
                        task.scheduled_config = trigger_config
                    elif trigger_type == TriggerType.FILE_WATCH:
                        task.file_watch_config = trigger_config
                    elif trigger_type == TriggerType.TASK_CHAIN:
                        task.task_chain_config = trigger_config
                    elif trigger_type == TriggerType.CUSTOM:
                        task.custom_trigger_config = trigger_config
            
            # 重新计算下次运行时间
            task.updated_at = datetime.now().isoformat()
            task.next_run = self._calculate_next_run(task)
            
            self._save_tasks()
            return task
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self._save_tasks()
                logger.info(f"删除任务: {task_id}")
                return True
            return False
    
    def get_task(self, task_id: str) -> Optional[AutomationTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[AutomationTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def set_task_enabled(self, task_id: str, enabled: bool):
        """启用/禁用任务"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = enabled
                self.tasks[task_id].status = "waiting" if enabled else "paused"
                if enabled:
                    self.tasks[task_id].next_run = self._calculate_next_run(self.tasks[task_id])
                self._save_tasks()
                self._notify_status_change(task_id)
    
    def _calculate_next_run(self, task: AutomationTask) -> Optional[str]:
        """计算下次运行时间"""
        if not task.enabled:
            return None
        
        now = datetime.now()
        
        if task.trigger_type == TriggerType.SCHEDULED.value:
            config = task.scheduled_config or {}
            time_str = config.get("time", "09:00")
            days = config.get("days", ["everyday"])
            
            hour, minute = map(int, time_str.split(":"))
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_time <= now:
                next_time += timedelta(days=1)
            
            # 检查是否在指定日期
            if "everyday" not in days:
                day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
                while next_time.strftime("%a").lower()[:3] not in days:
                    next_time += timedelta(days=1)
            
            return next_time.isoformat()
        
        elif task.trigger_type == TriggerType.INTERVAL.value:
            config = task.interval_config or {}
            # 兼容两种键名格式: interval_value/interval_unit 和 value/unit
            value = config.get("interval_value", config.get("value", 30))
            unit = config.get("interval_unit", config.get("unit", "minutes"))
            
            if unit == "seconds":
                delta = timedelta(seconds=value)
            elif unit == "hours":
                delta = timedelta(hours=value)
            else:  # minutes
                delta = timedelta(minutes=value)
            
            if task.last_run:
                last = datetime.fromisoformat(task.last_run)
                next_time = last + delta
                if next_time <= now:
                    next_time = now + delta
            else:
                next_time = now + delta
            
            return next_time.isoformat()
        
        elif task.trigger_type == TriggerType.FILE_WATCH.value:
            return "文件变更时"
        
        elif task.trigger_type == TriggerType.TASK_CHAIN.value:
            return "手动触发"
        
        return None
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        # 启动文件监控
        self._start_file_watchers()
        
        logger.info("自动化调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        
        # 停止文件监控
        for thread in self._file_watchers.values():
            thread.join(timeout=1)
        self._file_watchers.clear()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
        
        logger.info("自动化调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                now = datetime.now()
                tasks_to_execute = []
                
                # 快速扫描需要执行的任务（持有锁时间短）
                with self._lock:
                    for task in list(self.tasks.values()):
                        if not task.enabled:
                            continue
                        
                        if task.trigger_type in [TriggerType.SCHEDULED.value, TriggerType.INTERVAL.value]:
                            if task.next_run:
                                try:
                                    next_run = datetime.fromisoformat(task.next_run)
                                    if now >= next_run:
                                        tasks_to_execute.append(task)
                                except (ValueError, TypeError):
                                    # 无效的 next_run 格式，跳过
                                    pass
                
                # 在锁外执行任务（避免阻塞调度器）
                for task in tasks_to_execute:
                    try:
                        self._execute_task(task)
                    except Exception as e:
                        logger.error(f"执行任务 {task.id} 时出错: {e}")
                
                # 每秒检查一次
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"调度器错误: {e}")
                time.sleep(5)
    
    def _start_file_watchers(self):
        """启动文件监控"""
        for task in self.tasks.values():
            if task.enabled and task.trigger_type == TriggerType.FILE_WATCH.value:
                self._start_file_watcher(task)
    
    def _start_file_watcher(self, task: AutomationTask):
        """启动单个任务的文件监控"""
        config = task.file_watch_config or {}
        watch_paths = config.get("watch_paths", [])
        
        if not watch_paths:
            return
        
        def watch_loop():
            debounce = config.get("debounce_seconds", 5)
            last_trigger = 0
            
            while self._running and task.enabled:
                try:
                    for path in watch_paths:
                        if self._check_file_changed(path, task.id):
                            now = time.time()
                            if now - last_trigger >= debounce:
                                last_trigger = now
                                self._execute_task(task)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"文件监控错误 ({task.id}): {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=watch_loop, daemon=True)
        thread.start()
        self._file_watchers[task.id] = thread
    
    def _check_file_changed(self, path: str, task_id: str) -> bool:
        """检查文件是否变化"""
        try:
            p = Path(path)
            if not p.exists():
                return False
            
            if p.is_file():
                current_hash = self._get_file_hash(p)
            else:
                # 目录：计算所有文件的组合哈希
                current_hash = self._get_dir_hash(p)
            
            cache_key = f"{task_id}:{path}"
            old_hash = self._file_hashes.get(cache_key)
            self._file_hashes[cache_key] = current_hash
            
            if old_hash is None:
                return False  # 第一次不触发
            
            return old_hash != current_hash
            
        except Exception as e:
            logger.error(f"检查文件变化失败: {e}")
            return False
    
    def _get_file_hash(self, path: Path) -> str:
        """获取文件哈希"""
        stat = path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
    
    def _get_dir_hash(self, path: Path) -> str:
        """获取目录哈希"""
        hashes = []
        for f in path.rglob("*"):
            if f.is_file():
                hashes.append(f"{f}:{f.stat().st_mtime}")
        return hashlib.md5(":".join(sorted(hashes)).encode()).hexdigest()
    
    def _execute_task(self, task: AutomationTask):
        """执行任务"""
        logger.info(f"执行任务: {task.name}")
        
        task.status = TaskStatus.RUNNING.value
        self._notify_status_change(task.id)
        
        try:
            if task.trigger_type == TriggerType.TASK_CHAIN.value:
                self._execute_task_chain(task)
            else:
                self._execute_single_tool(task)
            
            task.status = TaskStatus.WAITING.value
            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            task.last_error = None
            task.next_run = self._calculate_next_run(task)
            
        except Exception as e:
            logger.error(f"任务执行失败 ({task.id}): {e}")
            task.status = TaskStatus.ERROR.value
            task.last_error = str(e)
        
        self._save_tasks()
        self._notify_status_change(task.id)
        
        if self.on_task_executed:
            self.on_task_executed(task)
    
    def _execute_single_tool(self, task: AutomationTask):
        """执行单个工具"""
        if self.execute_callback:
            result = self.execute_callback(
                task.tool_id,
                task.tool_category,
                task.execution_mode,
                task.parameters
            )
            logger.info(f"任务 {task.name} 执行结果: {result}")
        else:
            logger.warning(f"任务 {task.name}: 未设置执行回调")
    
    def _execute_task_chain(self, task: AutomationTask):
        """执行任务链"""
        config = task.task_chain_config or {}
        chain_task_ids = config.get("tasks", [])
        stop_on_error = config.get("stop_on_error", True)
        delay = config.get("delay_between", 2)
        
        for task_id in chain_task_ids:
            if task_id in self.tasks:
                sub_task = self.tasks[task_id]
                try:
                    self._execute_single_tool(sub_task)
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"任务链中的 {task_id} 执行失败: {e}")
                    if stop_on_error:
                        raise
    
    def run_task_now(self, task_id: str) -> bool:
        """立即运行任务"""
        task = self.tasks.get(task_id)
        if task:
            threading.Thread(target=self._execute_task, args=(task,), daemon=True).start()
            return True
        return False
    
    def _notify_status_change(self, task_id: str):
        """通知状态变更"""
        if self.on_task_status_change:
            task = self.tasks.get(task_id)
            if task:
                self.on_task_status_change(task)


# ============================================
# 预设任务模板
# ============================================

class TaskTemplates:
    """预设任务模板"""
    
    @staticmethod
    def daily_scheduled(name: str, time: str = "09:00", 
                       days: List[str] = None) -> Dict:
        """每日定时执行模板"""
        return {
            "trigger_type": TriggerType.SCHEDULED,
            "trigger_config": {
                "time": time,
                "days": days or ["mon", "tue", "wed", "thu", "fri"]
            }
        }
    
    @staticmethod
    def interval_minutes(name: str, minutes: int = 30) -> Dict:
        """间隔执行模板（分钟）"""
        return {
            "trigger_type": TriggerType.INTERVAL,
            "trigger_config": {
                "value": minutes,
                "unit": "minutes"
            }
        }
    
    @staticmethod
    def interval_hours(name: str, hours: int = 1) -> Dict:
        """间隔执行模板（小时）"""
        return {
            "trigger_type": TriggerType.INTERVAL,
            "trigger_config": {
                "value": hours,
                "unit": "hours"
            }
        }
    
    @staticmethod
    def file_watch(name: str, paths: List[str], 
                  patterns: List[str] = None) -> Dict:
        """文件监控模板"""
        return {
            "trigger_type": TriggerType.FILE_WATCH,
            "trigger_config": {
                "watch_paths": paths,
                "patterns": patterns or ["*"],
                "events": ["modified", "created"],
                "debounce_seconds": 5
            }
        }
    
    @staticmethod
    def task_chain(name: str, task_ids: List[str], 
                  stop_on_error: bool = True) -> Dict:
        """任务链模板"""
        return {
            "trigger_type": TriggerType.TASK_CHAIN,
            "trigger_config": {
                "tasks": task_ids,
                "stop_on_error": stop_on_error,
                "delay_between": 2
            }
        }
