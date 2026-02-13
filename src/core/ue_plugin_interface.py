"""
UE引擎插件标准接口规范
定义所有UE引擎工具插件必须实现的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class UEVersion(Enum):
    """支持的UE版本枚举"""
    UE4_27 = "4.27"
    UE5_0 = "5.0"
    UE5_1 = "5.1"
    UE5_2 = "5.2"
    UE5_3 = "5.3"
    UE5_4 = "5.4"


class UEProjectType(Enum):
    """UE项目类型枚举"""
    CPP = "cpp"
    BLUEPRINT = "blueprint"
    MIXED = "mixed"


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


class UEPluginInterface(PluginInterface):
    """UE插件接口"""
    
    # 必须的类属性
    PLUGIN_NAME: str
    PLUGIN_VERSION: str
    PLUGIN_TYPE: str = "ue"
    PLUGIN_DESCRIPTION: str
    PLUGIN_AUTHOR: str
    
    # UE特定属性
    TARGET_UE_VERSION: UEVersion
    PROJECT_TYPE: UEProjectType
    MIN_UE_VERSION: str
    MAX_UE_VERSION: str = ""
    
    @abstractmethod
    def connect_to_ue(self) -> bool:
        """
        连接到UE编辑器
        
        Returns:
            连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect_from_ue(self):
        """断开UE连接"""
        pass
    
    @abstractmethod
    def get_selected_assets(self) -> List[Dict[str, Any]]:
        """
        获取当前选择的资源
        
        Returns:
            选择的资源信息列表
        """
        pass
    
    @abstractmethod
    def get_project_info(self) -> Dict[str, Any]:
        """
        获取项目信息
        
        Returns:
            项目信息字典
        """
        pass


class UEEditorMixin:
    """UE编辑器混入类"""
    
    def ue_exec_python(self, python_code: str) -> Any:
        """
        在UE编辑器中执行Python代码
        
        Args:
            python_code: Python代码字符串
            
        Returns:
            代码执行结果
        """
        try:
            # 这里将与UE Python API交互
            # unreal_lib.unreal.execute_python_command(python_code)
            return exec(python_code)
        except ImportError:
            raise RuntimeError("UE Python环境未找到")
        except Exception as e:
            raise RuntimeError(f"Python代码执行失败: {e}")
    
    def ue_exec_unreal_command(self, command: str) -> Any:
        """
        执行UE控制台命令
        
        Args:
            command: UE控制台命令
            
        Returns:
            命令执行结果
        """
        try:
            # 这里将与UE控制台命令系统交互
            # unreal_lib.unreal.execute_console_command(command)
            return f"执行命令: {command}"
        except Exception as e:
            raise RuntimeError(f"UE命令执行失败: {e}")


class UEMixin:
    """UE通用混入类"""
    
    def get_asset_data(self, asset_path: str) -> Dict[str, Any]:
        """
        获取资产数据
        
        Args:
            asset_path: 资产路径
            
        Returns:
            资产信息字典
        """
        try:
            # 模拟UE资产数据获取
            return {
                "path": asset_path,
                "type": "StaticMesh",
                "size": "1024x1024",
                "lod_count": 3
            }
        except Exception as e:
            raise RuntimeError(f"获取资产数据失败: {e}")
    
    def get_actor_data(self, actor_name: str) -> Dict[str, Any]:
        """
        获取Actor数据
        
        Args:
            actor_name: Actor名称
            
        Returns:
            Actor信息字典
        """
        try:
            # 模拟UE Actor数据获取
            return {
                "name": actor_name,
                "type": "StaticMeshActor",
                "location": [0, 0, 0],
                "rotation": [0, 0, 0]
            }
        except Exception as e:
            raise RuntimeError(f"获取Actor数据失败: {e}")


# 标准的插件元数据装饰器
def ue_plugin(name: str, version: str, ue_version: UEVersion, 
              project_type: UEProjectType, min_version: str, 
              max_version: str = ""):
    """
    UE插件装饰器
    
    Args:
        name: 插件名称
        version: 插件版本
        ue_version: 目标UE版本
        project_type: 项目类型
        min_version: 最小支持版本
        max_version: 最大支持版本
    """
    def decorator(cls):
        cls.PLUGIN_NAME = name
        cls.PLUGIN_VERSION = version
        cls.PLUGIN_TYPE = "ue"
        cls.TARGET_UE_VERSION = ue_version
        cls.PROJECT_TYPE = project_type
        cls.MIN_UE_VERSION = min_version
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
@ue_plugin(
    name="ExampleAssetProcessor",
    version="1.0.0",
    ue_version=UEVersion.UE5_1,
    project_type=UEProjectType.CPP,
    min_version="5.0",
    max_version="5.4"
)
class ExampleAssetProcessor(UEPluginInterface, UEEditorMixin, UEMixin):
    """示例资产处理器"""
    
    PLUGIN_DESCRIPTION = "示例UE资产处理工具"
    PLUGIN_AUTHOR = "Example Developer"
    
    def connect_to_ue(self) -> bool:
        """连接到UE"""
        try:
            # 模拟连接
            return True
        except Exception:
            return False
    
    def disconnect_from_ue(self):
        """断开UE连接"""
        pass
    
    @validate_params(
        quality={'type': int, 'min': 1, 'max': 100, 'default': 50},
        compress_textures={'type': bool, 'default': True}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行资产处理"""
        try:
            # 连接UE
            if not self.connect_to_ue():
                return {"status": "error", "message": "无法连接到UE"}
            
            # 获取选择
            selected_assets = self.get_selected_assets()
            if not selected_assets:
                return {"status": "error", "message": "没有选择资产"}
            
            # 执行处理操作
            result = self._process_assets(selected_assets, kwargs)
            
            return {
                "status": "success",
                "processed_assets": [asset['path'] for asset in selected_assets],
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
            "target_ue_version": self.TARGET_UE_VERSION.value,
            "project_type": self.PROJECT_TYPE.value,
            "min_version": self.MIN_UE_VERSION,
            "max_version": self.MAX_VERSION,
            "description": self.PLUGIN_DESCRIPTION,
            "author": self.PLUGIN_AUTHOR
        }
    
    def get_selected_assets(self) -> List[Dict[str, Any]]:
        """获取选择的资产"""
        try:
            # 模拟获取选择的资产
            return [
                {"path": "/Game/Meshes/SM_Cube", "type": "StaticMesh"},
                {"path": "/Game/Textures/T_Diffuse", "type": "Texture2D"}
            ]
        except:
            return []
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        try:
            return {
                "project_name": "MyUEProject",
                "engine_version": "5.1.1",
                "project_type": "CPP"
            }
        except:
            return {}
    
    def _process_assets(self, assets: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """执行资产处理操作"""
        # 这里实现具体的资产处理逻辑
        return {
            "processed_count": len(assets),
            "texture_compressed": params.get('compress_textures', False),
            "quality_setting": params.get('quality', 50)
        }


# 插件工厂类
class UEPluginFactory:
    """UE插件工厂"""
    
    _plugin_registry: Dict[str, type] = {}
    
    @classmethod
    def register_plugin(cls, plugin_class: type):
        """注册插件类"""
        plugin_name = getattr(plugin_class, 'PLUGIN_NAME', plugin_class.__name__)
        cls._plugin_registry[plugin_name] = plugin_class
        print(f"注册UE插件: {plugin_name}")
    
    @classmethod
    def create_plugin(cls, plugin_name: str, **kwargs) -> Optional[UEPluginInterface]:
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
                "target_ue_version": getattr(plugin_class, 'TARGET_UE_VERSION', None),
                "description": getattr(plugin_class, 'PLUGIN_DESCRIPTION', '')
            }
        return None


# 自动注册装饰器
def auto_register(cls):
    """自动注册插件装饰器"""
    UEPluginFactory.register_plugin(cls)
    return cls