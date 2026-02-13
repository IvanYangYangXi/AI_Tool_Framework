# 插件系统核心技术实现示例

## 1. 插件接口标准化设计

### 1.1 基础插件接口定义

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class PluginType(Enum):
    """插件类型枚举"""
    DCC_TOOL = "dcc_tool"          # DCC工具插件
    UE_PLUGIN = "ue_plugin"        # UE引擎插件
    GENERAL_TOOL = "general_tool"  # 通用工具插件
    EXTENSION = "extension"        # 扩展插件

@dataclass
class PluginMetadata:
    """插件元数据"""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: list
    compatibility: Dict[str, str]

class PluginInterface(ABC):
    """插件基础接口 - 定义所有插件必须实现的方法"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """执行插件功能"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取插件能力描述"""
        pass
```

### 1.2 DCC软件插件适配器

```python
class DCCPluginAdapter(PluginInterface):
    """DCC软件插件适配器基类"""
    
    def __init__(self, dcc_software: str):
        self.dcc_software = dcc_software
        self.is_connected = False
        
    @abstractmethod
    def connect_to_dcc(self) -> bool:
        """连接到DCC软件"""
        pass
    
    @abstractmethod
    def disconnect_from_dcc(self) -> None:
        """断开DCC软件连接"""
        pass
    
    @abstractmethod
    def execute_dcc_command(self, command: str, args: Dict[str, Any]) -> Any:
        """执行DCC命令"""
        pass

class MayaPluginAdapter(DCCPluginAdapter):
    """Maya插件适配器"""
    
    def __init__(self):
        super().__init__("maya")
        
    def connect_to_dcc(self) -> bool:
        try:
            import maya.cmds as cmds
            self.is_connected = True
            return True
        except ImportError:
            return False
    
    def execute_dcc_command(self, command: str, args: Dict[str, Any]) -> Any:
        if not self.is_connected:
            raise RuntimeError("未连接到Maya")
            
        import maya.cmds as cmds
        cmd_func = getattr(cmds, command, None)
        if cmd_func:
            return cmd_func(**args)
        else:
            raise ValueError(f"不支持的Maya命令: {command}")
```

## 2. 插件发现与加载机制

### 2.1 插件发现器实现

```python
import os
import importlib.util
import json
from pathlib import Path
from typing import List, Dict, Type

class PluginDiscoveryService:
    """插件发现服务"""
    
    def __init__(self, plugin_dirs: List[str]):
        self.plugin_dirs = plugin_dirs
        self.discovered_plugins: Dict[str, Type[PluginInterface]] = {}
        
    def discover_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """发现所有可用插件"""
        for plugin_dir in self.plugin_dirs:
            self._scan_directory(plugin_dir)
        return self.discovered_plugins
    
    def _scan_directory(self, directory: str):
        """扫描目录中的插件"""
        plugin_path = Path(directory)
        if not plugin_path.exists():
            return
            
        # 扫描Python文件
        for py_file in plugin_path.glob("**/*.py"):
            self._load_plugin_from_file(py_file)
            
        # 扫描插件包
        for plugin_pkg in plugin_path.glob("**/plugin.json"):
            self._load_plugin_from_package(plugin_pkg.parent)
    
    def _load_plugin_from_file(self, file_path: Path):
        """从Python文件加载插件"""
        try:
            spec = importlib.util.spec_from_file_location(
                file_path.stem, file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginInterface) and 
                    attr != PluginInterface):
                    plugin_id = f"{file_path.parent.name}.{attr_name}"
                    self.discovered_plugins[plugin_id] = attr
                    break
                    
        except Exception as e:
            print(f"加载插件失败 {file_path}: {e}")
    
    def _load_plugin_from_package(self, package_path: Path):
        """从插件包加载插件"""
        try:
            config_file = package_path / "plugin.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            plugin_id = config.get('id')
            entry_module = config.get('entry_module')
            
            if plugin_id and entry_module:
                module_path = package_path / f"{entry_module}.py"
                spec = importlib.util.spec_from_file_location(
                    entry_module, module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 获取插件类
                plugin_class = getattr(module, config.get('plugin_class'), None)
                if plugin_class and issubclass(plugin_class, PluginInterface):
                    self.discovered_plugins[plugin_id] = plugin_class
                    
        except Exception as e:
            print(f"加载插件包失败 {package_path}: {e}")
```

### 2.2 动态加载器实现

```python
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable

class PluginLoader:
    """插件动态加载器"""
    
    def __init__(self):
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.loading_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def load_plugin(self, plugin_id: str, 
                   plugin_class: Type[PluginInterface],
                   config: Dict[str, Any] = None) -> Optional[PluginInterface]:
        """加载指定插件"""
        with self.loading_lock:
            if plugin_id in self.loaded_plugins:
                return self.loaded_plugins[plugin_id]
            
            try:
                # 创建插件实例
                plugin_instance = plugin_class()
                
                # 初始化插件
                if plugin_instance.initialize(config or {}):
                    self.loaded_plugins[plugin_id] = plugin_instance
                    return plugin_instance
                else:
                    print(f"插件初始化失败: {plugin_id}")
                    return None
                    
            except Exception as e:
                print(f"加载插件异常 {plugin_id}: {e}")
                return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        with self.loading_lock:
            if plugin_id in self.loaded_plugins:
                try:
                    self.loaded_plugins[plugin_id].cleanup()
                    del self.loaded_plugins[plugin_id]
                    return True
                except Exception as e:
                    print(f"卸载插件异常 {plugin_id}: {e}")
                    return False
            return False
    
    def async_load_plugin(self, plugin_id: str,
                         plugin_class: Type[PluginInterface],
                         callback: Callable[[Optional[PluginInterface]], None],
                         config: Dict[str, Any] = None):
        """异步加载插件"""
        future = self.executor.submit(
            self.load_plugin, plugin_id, plugin_class, config
        )
        future.add_done_callback(
            lambda f: callback(f.result())
        )
```

## 3. 配置管理系统

### 3.1 分层配置管理

```python
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigurationManager:
    """分层配置管理器"""
    
    def __init__(self, config_base_path: str):
        self.base_path = Path(config_base_path)
        self.system_config = {}
        self.user_config = {}
        self.plugin_configs = {}
        
    def load_all_configs(self):
        """加载所有层级配置"""
        self.system_config = self._load_system_config()
        self.user_config = self._load_user_config()
        self.plugin_configs = self._load_plugin_configs()
    
    def _load_system_config(self) -> Dict[str, Any]:
        """加载系统配置"""
        system_config_file = self.base_path / "system.yaml"
        if system_config_file.exists():
            with open(system_config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_user_config(self) -> Dict[str, Any]:
        """加载用户配置"""
        user_config_file = self.base_path / "user.yaml"
        if user_config_file.exists():
            with open(user_config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载插件配置"""
        plugin_configs = {}
        plugins_config_dir = self.base_path / "plugins"
        
        if plugins_config_dir.exists():
            for config_file in plugins_config_dir.glob("*.yaml"):
                plugin_id = config_file.stem
                with open(config_file, 'r', encoding='utf-8') as f:
                    plugin_configs[plugin_id] = yaml.safe_load(f)
        
        return plugin_configs
    
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件配置（合并优先级：用户 > 插件 > 系统）"""
        config = {}
        
        # 系统配置为基础
        config.update(self.system_config.get('default_plugin_config', {}))
        
        # 插件默认配置覆盖
        if plugin_id in self.plugin_configs:
            config.update(self.plugin_configs[plugin_id])
        
        # 用户配置最终覆盖
        user_plugin_config = self.user_config.get('plugins', {}).get(plugin_id, {})
        config.update(user_plugin_config)
        
        return config
```

### 3.2 SDD格式解析器

```python
import jsonschema
from typing import Dict, Any

class SDDParser:
    """SDD (Software Design Document) 解析器"""
    
    # SDD JSON Schema定义
    SDD_SCHEMA = {
        "type": "object",
        "properties": {
            "tool_info": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "type": {"type": "string", "enum": ["dcc", "ue_engine", "general"]},
                    "category": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "version", "type"]
            },
            "dependencies": {
                "type": "object",
                "properties": {
                    "required_tools": {"type": "array", "items": {"type": "string"}},
                    "compatible_versions": {"type": "array", "items": {"type": "string"}}
                }
            },
            "configuration": {
                "type": "object",
                "properties": {
                    "input_params": {"type": "array"},
                    "output_params": {"type": "array"}
                }
            },
            "execution": {
                "type": "object",
                "properties": {
                    "entry_point": {"type": "string"},
                    "command_line": {"type": "string"},
                    "timeout": {"type": "integer"},
                    "memory_limit": {"type": "string"}
                }
            }
        },
        "required": ["tool_info"]
    }
    
    @classmethod
    def validate_sdd(cls, sdd_content: Dict[str, Any]) -> bool:
        """验证SDD格式"""
        try:
            jsonschema.validate(sdd_content, cls.SDD_SCHEMA)
            return True
        except jsonschema.ValidationError as e:
            print(f"SDD验证失败: {e.message}")
            return False
    
    @classmethod
    def parse_sdd_to_config(cls, sdd_content: Dict[str, Any]) -> Dict[str, Any]:
        """将SDD转换为插件配置"""
        if not cls.validate_sdd(sdd_content):
            raise ValueError("无效的SDD格式")
        
        config = {
            "plugin_metadata": {
                "name": sdd_content["tool_info"]["name"],
                "version": sdd_content["tool_info"]["version"],
                "description": sdd_content["tool_info"].get("description", ""),
                "type": sdd_content["tool_info"]["type"]
            },
            "dependencies": sdd_content.get("dependencies", {}),
            "parameters": {
                "input": sdd_content.get("configuration", {}).get("input_params", []),
                "output": sdd_content.get("configuration", {}).get("output_params", [])
            },
            "execution": sdd_content.get("execution", {})
        }
        
        return config
```

## 4. 权限控制系统

### 4.1 权限管理器

```python
from enum import Enum
from dataclasses import dataclass
from typing import Set, List

class PermissionLevel(Enum):
    """权限等级"""
    READ_ONLY = "read_only"
    BASIC = "basic" 
    ADVANCED = "advanced"
    ADMIN = "admin"

@dataclass
class Permission:
    """权限定义"""
    name: str
    level: PermissionLevel
    description: str

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.user_permissions: Dict[str, Set[str]] = {}
        self.role_permissions: Dict[str, Set[str]] = {}
        
    def register_permission(self, permission: Permission):
        """注册权限"""
        self.permissions[permission.name] = permission
    
    def assign_permission_to_user(self, user_id: str, permission_name: str):
        """为用户分配权限"""
        if permission_name in self.permissions:
            if user_id not in self.user_permissions:
                self.user_permissions[user_id] = set()
            self.user_permissions[user_id].add(permission_name)
    
    def check_permission(self, user_id: str, permission_name: str) -> bool:
        """检查用户是否具有指定权限"""
        user_perms = self.user_permissions.get(user_id, set())
        return permission_name in user_perms
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """获取用户所有权限"""
        user_perm_names = self.user_permissions.get(user_id, set())
        return [self.permissions[name] for name in user_perm_names 
                if name in self.permissions]

# 预定义权限
DEFAULT_PERMISSIONS = [
    Permission("plugin.install", PermissionLevel.ADMIN, "安装插件"),
    Permission("plugin.uninstall", PermissionLevel.ADMIN, "卸载插件"),
    Permission("plugin.execute", PermissionLevel.BASIC, "执行插件"),
    Permission("config.modify", PermissionLevel.ADVANCED, "修改配置"),
    Permission("system.monitor", PermissionLevel.READ_ONLY, "监控系统状态")
]
```

### 4.2 沙箱执行环境

```python
import sys
from contextlib import contextmanager
from typing import Any, Dict

class SandboxEnvironment:
    """沙箱执行环境"""
    
    def __init__(self, resource_limits: Dict[str, Any] = None):
        self.resource_limits = resource_limits or {}
        self.original_modules = sys.modules.copy()
        
    @contextmanager
    def isolated_execution(self):
        """隔离执行上下文"""
        # 保存当前状态
        original_path = sys.path[:]
        original_modules = sys.modules.copy()
        
        try:
            # 设置资源限制
            self._apply_resource_limits()
            
            # 创建隔离的模块空间
            restricted_modules = self._create_restricted_modules()
            sys.modules.update(restricted_modules)
            
            yield
            
        finally:
            # 恢复原始状态
            sys.path[:] = original_path
            sys.modules.clear()
            sys.modules.update(original_modules)
            self._release_resource_limits()
    
    def _apply_resource_limits(self):
        """应用资源限制"""
        import resource
        
        if 'memory' in self.resource_limits:
            memory_limit = self.resource_limits['memory']
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        
        if 'cpu_time' in self.resource_limits:
            cpu_limit = self.resource_limits['cpu_time']
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    
    def _release_resource_limits(self):
        """释放资源限制"""
        import resource
        # 恢复默认限制
        resource.setrlimit(resource.RLIMIT_AS, resource.RLIM_INFINITY)
        resource.setrlimit(resource.RLIMIT_CPU, resource.RLIM_INFINITY)
    
    def _create_restricted_modules(self) -> Dict[str, Any]:
        """创建受限的模块环境"""
        restricted = {}
        
        # 只允许安全的内置模块
        safe_modules = ['sys', 'os', 'json', 'math']
        for module_name in safe_modules:
            if module_name in sys.modules:
                restricted[module_name] = sys.modules[module_name]
        
        return restricted
```

## 5. 事件总线实现

### 5.1 事件系统核心

```python
from typing import Dict, List, Callable, Any
import asyncio
import threading
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """事件类型枚举"""
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_EXECUTED = "plugin_executed"
    CONFIG_CHANGED = "config_changed"
    SYSTEM_ERROR = "system_error"

@dataclass
class Event:
    """事件数据结构"""
    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float

class EventBus:
    """事件总线实现"""
    
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.event_queue = asyncio.Queue()
        self.running = False
        self.event_loop = None
        
    def subscribe(self, event_type: EventType, listener: Callable):
        """订阅事件"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def unsubscribe(self, event_type: EventType, listener: Callable):
        """取消订阅事件"""
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)
    
    def publish(self, event: Event):
        """发布事件"""
        if self.event_loop and self.running:
            asyncio.run_coroutine_threadsafe(
                self._handle_event(event), self.event_loop
            )
        else:
            # 同步处理
            self._dispatch_event(event)
    
    async def _handle_event(self, event: Event):
        """异步处理事件"""
        await self.event_queue.put(event)
        self._dispatch_event(event)
    
    def _dispatch_event(self, event: Event):
        """分发事件给监听器"""
        if event.event_type in self.listeners:
            for listener in self.listeners[event.event_type]:
                try:
                    listener(event)
                except Exception as e:
                    print(f"事件处理异常: {e}")
    
    def start_event_loop(self):
        """启动事件循环"""
        self.running = True
        self.event_loop = asyncio.new_event_loop()
        
        def run_loop():
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_forever()
            
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def stop_event_loop(self):
        """停止事件循环"""
        self.running = False
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
```

这些实现示例展示了插件系统的核心技术要点，包括标准化接口设计、动态发现加载、分层配置管理、权限控制和事件通信等关键功能。每个组件都遵循了良好的软件工程原则，可以作为实际开发的参考基础。