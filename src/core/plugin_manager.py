"""
插件管理器 - 负责插件的生命周期管理、发现和注册
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """插件类型枚举"""
    DCC = "dcc"
    UE_ENGINE = "ue_engine"
    UTILITY = "utility"


class PluginStatus(Enum):
    """插件状态枚举"""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """插件信息数据类"""
    name: str
    version: str
    plugin_type: PluginType
    description: str
    author: str
    file_path: str
    module_name: str
    status: PluginStatus = PluginStatus.UNLOADED
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginManager:
    """
    插件管理器
    
    负责：
    - 插件发现与扫描
    - 插件加载与卸载
    - 插件生命周期管理
    - 依赖关系解析
    - 版本冲突检测
    """
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        初始化插件管理器
        
        Args:
            plugin_dirs: 插件目录列表，默认为['./plugins']
        """
        self.plugin_dirs = plugin_dirs or ['./plugins']
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, Any] = {}
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
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        发现所有可用插件
        
        Returns:
            发现的插件信息列表
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"插件目录不存在: {plugin_dir}")
                continue
                
            plugin_path = Path(plugin_dir)
            for plugin_file in plugin_path.rglob("plugin.py"):
                try:
                    plugin_info = self._extract_plugin_info(plugin_file)
                    if plugin_info:
                        discovered_plugins.append(plugin_info)
                        self.plugins[plugin_info.name] = plugin_info
                        logger.info(f"发现插件: {plugin_info.name} v{plugin_info.version}")
                except Exception as e:
                    logger.error(f"解析插件文件失败 {plugin_file}: {e}")
        
        return discovered_plugins
    
    def _extract_plugin_info(self, plugin_file: Path) -> Optional[PluginInfo]:
        """
        从插件文件中提取插件信息
        
        Args:
            plugin_file: 插件文件路径
            
        Returns:
            插件信息对象或None
        """
        try:
            # 动态导入插件模块来获取元数据
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_file.parent.name}", 
                plugin_file
            )
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            
            # 只导入必要的属性，避免执行插件代码
            plugin_attrs = {}
            with open(plugin_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单的属性提取（实际项目中可能需要更复杂的解析）
            for attr in ['PLUGIN_NAME', 'PLUGIN_VERSION', 'PLUGIN_TYPE', 
                        'PLUGIN_DESCRIPTION', 'PLUGIN_AUTHOR']:
                if attr in content:
                    # 这里简化处理，实际应该用AST解析
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip().startswith(attr):
                            try:
                                value = line.split('=', 1)[1].strip().strip('"\'')
                                plugin_attrs[attr.replace('PLUGIN_', '').lower()] = value
                            except:
                                pass
            
            if 'name' not in plugin_attrs:
                return None
                
            return PluginInfo(
                name=plugin_attrs.get('name', ''),
                version=plugin_attrs.get('version', '1.0.0'),
                plugin_type=PluginType(plugin_attrs.get('type', 'utility')),
                description=plugin_attrs.get('description', ''),
                author=plugin_attrs.get('author', 'Unknown'),
                file_path=str(plugin_file),
                module_name=f"plugin_{plugin_file.parent.name}"
            )
            
        except Exception as e:
            logger.error(f"提取插件信息失败: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否加载成功
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件未找到: {plugin_name}")
            return False
            
        plugin_info = self.plugins[plugin_name]
        if plugin_info.status == PluginStatus.LOADED:
            logger.info(f"插件已加载: {plugin_name}")
            return True
            
        try:
            # 检查依赖
            if not self._check_dependencies(plugin_info):
                logger.error(f"插件依赖不满足: {plugin_name}")
                return False
            
            # 加载插件模块
            spec = importlib.util.spec_from_file_location(
                plugin_info.module_name,
                plugin_info.file_path
            )
            if not spec or not spec.loader:
                raise ImportError(f"无法加载插件模块: {plugin_info.module_name}")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_info.module_name] = module
            spec.loader.exec_module(module)
            
            # 存储加载的插件
            self.loaded_plugins[plugin_name] = module
            plugin_info.status = PluginStatus.LOADED
            
            logger.info(f"插件加载成功: {plugin_name}")
            return True
            
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            logger.error(f"插件加载失败 {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否卸载成功
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"插件未加载: {plugin_name}")
            return False
            
        try:
            # 从已加载插件中移除
            del self.loaded_plugins[plugin_name]
            self.plugins[plugin_name].status = PluginStatus.UNLOADED
            
            # 清理模块缓存
            if self.plugins[plugin_name].module_name in sys.modules:
                del sys.modules[self.plugins[plugin_name].module_name]
            
            logger.info(f"插件卸载成功: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"插件卸载失败 {plugin_name}: {e}")
            return False
    
    def _check_dependencies(self, plugin_info: PluginInfo) -> bool:
        """
        检查插件依赖
        
        Args:
            plugin_info: 插件信息
            
        Returns:
            依赖是否满足
        """
        # 简化实现，实际项目中需要更复杂的依赖解析
        try:
            for dep in plugin_info.dependencies:
                # 检查Python包依赖
                if dep.startswith('python:'):
                    pkg_name = dep.replace('python:', '')
                    importlib.import_module(pkg_name)
            return True
        except ImportError:
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """
        获取已加载的插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例或None
        """
        return self.loaded_plugins.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginInfo]:
        """
        列出所有插件
        
        Args:
            plugin_type: 插件类型过滤器
            
        Returns:
            插件信息列表
        """
        plugins = list(self.plugins.values())
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        return plugins
    
    def get_loaded_plugins(self) -> Dict[str, Any]:
        """
        获取所有已加载的插件
        
        Returns:
            已加载插件字典
        """
        return self.loaded_plugins.copy()


# 使用示例
if __name__ == "__main__":
    # 创建插件管理器
    pm = PluginManager(['./src/plugins'])
    
    # 发现插件
    plugins = pm.discover_plugins()
    print(f"发现 {len(plugins)} 个插件")
    
    # 加载所有插件
    for plugin in plugins:
        pm.load_plugin(plugin.name)