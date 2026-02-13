"""
DCC工具插件标准接口规范
定义所有DCC工具插件必须实现的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class DCCSoftware(Enum):
    """支持的DCC软件枚举"""
    MAYA = "maya"
    MAX = "3ds_max" 
    BLENDER = "blender"
    HOUDINI = "houdini"
    CINEMA4D = "cinema4d"
    NUKE = "nuke"


class PluginInterface(ABC):
    """插件接口基类"""
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行插件主功能
        
        Args:
            **kwargs: 执行参数
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入参数
        
        Args:
            params: 输入参数字典
            
        Returns:
            验证后的参数字典
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        获取插件信息
        
        Returns:
            插件信息字典
        """
        pass


class DCCPluginInterface(PluginInterface):
    """DCC插件接口"""
    
    # 必须的类属性
    PLUGIN_NAME: str
    PLUGIN_VERSION: str
    PLUGIN_TYPE: str = "dcc"
    PLUGIN_DESCRIPTION: str
    PLUGIN_AUTHOR: str
    
    # DCC特定属性
    TARGET_DCC: DCCSoftware
    MIN_VERSION: str
    MAX_VERSION: str = ""
    
    @abstractmethod
    def connect_to_dcc(self) -> bool:
        """
        连接到目标DCC软件
        
        Returns:
            连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect_from_dcc(self):
        """断开DCC连接"""
        pass
    
    @abstractmethod
    def get_selection(self) -> List[str]:
        """
        获取当前选择的对象
        
        Returns:
            选择对象ID列表
        """
        pass
    
    @abstractmethod
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """
        获取场景中的对象信息
        
        Returns:
            对象信息列表
        """
        pass


class MayaPluginMixin:
    """Maya插件混入类"""
    
    def maya_eval(self, mel_command: str) -> Any:
        """
        执行MEL命令
        
        Args:
            mel_command: MEL命令字符串
            
        Returns:
            命令执行结果
        """
        try:
            import maya.cmds as cmds
            return eval(f"cmds.{mel_command}")
        except ImportError:
            raise RuntimeError("Maya环境未找到")
        except Exception as e:
            raise RuntimeError(f"MEL命令执行失败: {e}")
    
    def maya_python(self, python_code: str) -> Any:
        """
        执行Maya Python代码
        
        Args:
            python_code: Python代码字符串
            
        Returns:
            代码执行结果
        """
        try:
            import maya.cmds as cmds
            import maya.mel as mel
            # 这里可以执行更复杂的Maya操作
            return exec(python_code)
        except ImportError:
            raise RuntimeError("Maya环境未找到")


class MaxPluginMixin:
    """3ds Max插件混入类"""
    
    def max_execute(self, maxscript: str) -> Any:
        """
        执行MaxScript
        
        Args:
            maxscript: MaxScript代码
            
        Returns:
            执行结果
        """
        try:
            import pymxs
            runtime = pymxs.runtime
            return runtime.execute(maxscript)
        except ImportError:
            raise RuntimeError("3ds Max环境未找到")


class BlenderPluginMixin:
    """Blender插件混入类"""
    
    def blender_context(self) -> Any:
        """
        获取Blender上下文
        
        Returns:
            Blender上下文对象
        """
        try:
            import bpy
            return bpy.context
        except ImportError:
            raise RuntimeError("Blender环境未找到")
    
    def blender_data(self) -> Any:
        """
        获取Blender数据
        
        Returns:
            Blender数据对象
        """
        try:
            import bpy
            return bpy.data
        except ImportError:
            raise RuntimeError("Blender环境未找到")


# 标准的插件元数据装饰器
def dcc_plugin(name: str, version: str, dcc: DCCSoftware, 
               min_version: str, max_version: str = ""):
    """
    DCC插件装饰器
    
    Args:
        name: 插件名称
        version: 插件版本
        dcc: 目标DCC软件
        min_version: 最小支持版本
        max_version: 最大支持版本
    """
    def decorator(cls):
        cls.PLUGIN_NAME = name
        cls.PLUGIN_VERSION = version
        cls.PLUGIN_TYPE = "dcc"
        cls.TARGET_DCC = dcc
        cls.MIN_VERSION = min_version
        cls.MAX_VERSION = max_version
        return cls
    return decorator


# 标准参数验证装饰器
def validate_params(**param_specs):
    """
    参数验证装饰器
    
    Args:
        **param_specs: 参数规格定义
    """
    def decorator(func):
        def wrapper(self, **kwargs):
            # 验证参数
            validated_params = {}
            for param_name, spec in param_specs.items():
                value = kwargs.get(param_name, spec.get('default'))
                
                # 类型检查
                if 'type' in spec and value is not None:
                    expected_type = spec['type']
                    if not isinstance(value, expected_type):
                        raise TypeError(f"参数 {param_name} 类型错误，期望 {expected_type}")
                
                # 范围检查
                if 'min' in spec and value is not None:
                    if value < spec['min']:
                        raise ValueError(f"参数 {param_name} 不能小于 {spec['min']}")
                
                if 'max' in spec and value is not None:
                    if value > spec['max']:
                        raise ValueError(f"参数 {param_name} 不能大于 {spec['max']}")
                
                # 必需参数检查
                if spec.get('required', False) and value is None:
                    raise ValueError(f"参数 {param_name} 是必需的")
                
                validated_params[param_name] = value
            
            return func(self, **validated_params)
        return wrapper
    return decorator


# 使用示例
@dcc_plugin(
    name="ExampleMeshTool",
    version="1.0.0",
    dcc=DCCSoftware.MAYA,
    min_version="2022",
    max_version="2025"
)
class ExampleMeshTool(DCCPluginInterface, MayaPluginMixin):
    """示例网格工具"""
    
    PLUGIN_DESCRIPTION = "示例网格处理工具"
    PLUGIN_AUTHOR = "Example Developer"
    
    def connect_to_dcc(self) -> bool:
        """连接到Maya"""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            return False
    
    def disconnect_from_dcc(self):
        """断开Maya连接"""
        pass
    
    @validate_params(
        tolerance={'type': float, 'min': 0.001, 'max': 1.0, 'default': 0.01},
        delete_duplicates={'type': bool, 'default': True}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行网格清理"""
        try:
            # 连接DCC
            if not self.connect_to_dcc():
                return {"status": "error", "message": "无法连接到Maya"}
            
            # 获取选择
            selection = self.get_selection()
            if not selection:
                return {"status": "error", "message": "没有选择对象"}
            
            # 执行清理操作
            result = self._perform_cleanup(selection, kwargs)
            
            return {
                "status": "success",
                "processed_objects": selection,
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        return params  # 装饰器已处理验证
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.PLUGIN_NAME,
            "version": self.PLUGIN_VERSION,
            "type": self.PLUGIN_TYPE,
            "target_dcc": self.TARGET_DCC.value,
            "min_version": self.MIN_VERSION,
            "max_version": self.MAX_VERSION,
            "description": self.PLUGIN_DESCRIPTION,
            "author": self.PLUGIN_AUTHOR
        }
    
    def get_selection(self) -> List[str]:
        """获取Maya选择"""
        try:
            objects = self.maya_eval("ls(selection=True)")
            return objects if objects else []
        except:
            return []
    
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """获取场景对象信息"""
        try:
            all_objects = self.maya_eval("ls(type='mesh')")
            return [{"name": obj, "type": "mesh"} for obj in all_objects]
        except:
            return []
    
    def _perform_cleanup(self, objects: List[str], params: Dict[str, Any]) -> Dict[str, Any]:
        """执行清理操作"""
        # 这里实现具体的网格清理逻辑
        return {
            "deleted_vertices": 100,
            "merged_vertices": 50,
            "optimized_meshes": len(objects)
        }


# 插件工厂类
class DCCPluginFactory:
    """DCC插件工厂"""
    
    _plugin_registry: Dict[str, type] = {}
    
    @classmethod
    def register_plugin(cls, plugin_class: type):
        """注册插件类"""
        plugin_name = getattr(plugin_class, 'PLUGIN_NAME', plugin_class.__name__)
        cls._plugin_registry[plugin_name] = plugin_class
        print(f"注册插件: {plugin_name}")
    
    @classmethod
    def create_plugin(cls, plugin_name: str, **kwargs) -> Optional[DCCPluginInterface]:
        """创建插件实例"""
        if plugin_name in cls._plugin_registry:
            plugin_class = cls._plugin_registry[plugin_name]
            return plugin_class(**kwargs)
        return None
    
    @classmethod
    def list_plugins(cls) -> List[str]:
        """列出所有注册的插件"""
        return list(cls._plugin_registry.keys())
    
    @classmethod
    def get_plugin_info(cls, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        if plugin_name in cls._plugin_registry:
            plugin_class = cls._plugin_registry[plugin_name]
            return {
                "name": getattr(plugin_class, 'PLUGIN_NAME', plugin_name),
                "version": getattr(plugin_class, 'PLUGIN_VERSION', '1.0.0'),
                "target_dcc": getattr(plugin_class, 'TARGET_DCC', None),
                "description": getattr(plugin_class, 'PLUGIN_DESCRIPTION', '')
            }
        return None


# 自动注册装饰器
def auto_register(cls):
    """自动注册插件装饰器"""
    DCCPluginFactory.register_plugin(cls)
    return cls