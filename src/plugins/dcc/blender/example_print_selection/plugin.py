
"""
Blender打印选择对象 - 示例脚本

获取Blender中当前选择的对象并打印其名称
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# 插件元数据常量
PLUGIN_NAME = "[示例] Blender打印选择"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "dcc"
PLUGIN_DESCRIPTION = "获取Blender中选择的对象并打印其名称 - 示例脚本"
PLUGIN_AUTHOR = "DCC Tool Framework Team"


class PrintSelection:
    """Blender打印选择对象工具"""
    
    PLUGIN_NAME = PLUGIN_NAME
    PLUGIN_VERSION = PLUGIN_VERSION
    PLUGIN_TYPE = PLUGIN_TYPE
    PLUGIN_DESCRIPTION = PLUGIN_DESCRIPTION
    PLUGIN_AUTHOR = PLUGIN_AUTHOR
    
    def __init__(self):
        self._connected = False
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
    
    def connect_to_dcc(self) -> bool:
        """连接到Blender"""
        try:
            import bpy
            self._connected = True
            logger.info("成功连接到Blender")
            return True
        except ImportError:
            logger.warning("Blender环境未找到，使用模拟模式")
            return False
        except Exception as e:
            logger.error(f"连接Blender失败: {e}")
            return False
    
    def disconnect_from_dcc(self):
        """断开Blender连接"""
        self._connected = False
        logger.info("断开Blender连接")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行主功能：获取选择的对象并打印名称
        
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始获取选择的对象...")
            
            # 尝试连接Blender
            if not self._connected:
                self.connect_to_dcc()
            
            # 获取选择的对象
            selected_objects = self.get_selection()
            
            # 打印结果
            if selected_objects:
                print("\n" + "=" * 50)
                print("【选择的对象】")
                print("=" * 50)
                for i, obj_name in enumerate(selected_objects, 1):
                    print(f"  {i}. {obj_name}")
                print("=" * 50)
                print(f"总计: {len(selected_objects)} 个对象")
                print("=" * 50 + "\n")
                
                return {
                    "status": "success",
                    "selected_objects": selected_objects,
                    "count": len(selected_objects),
                    "message": f"成功获取 {len(selected_objects)} 个对象"
                }
            else:
                print("\n【提示】没有选择任何对象\n")
                
                return {
                    "status": "success",
                    "selected_objects": [],
                    "count": 0,
                    "message": "没有选择任何对象"
                }
                
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "selected_objects": [],
                "count": 0,
                "message": str(e)
            }
    
    def get_selection(self) -> List[str]:
        """获取当前选择的对象"""
        try:
            if self._connected:
                import bpy
                selection = [obj.name for obj in bpy.context.selected_objects]
                return selection
            else:
                # 模拟模式
                logger.info("模拟模式：返回测试数据")
                return ["Cube", "Sphere", "Cylinder"]
                
        except Exception as e:
            logger.error(f"获取选择失败: {e}")
            return []
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.PLUGIN_NAME,
            "version": self.PLUGIN_VERSION,
            "type": self.PLUGIN_TYPE,
            "description": self.PLUGIN_DESCRIPTION,
            "author": self.PLUGIN_AUTHOR
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        return params
    
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """获取场景对象"""
        return []


def run_in_blender():
    """Blender直接执行入口"""
    plugin = PrintSelection()
    result = plugin.execute()
    return result


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Blender 打印选择对象工具 - 测试模式")
    print("=" * 60)
    
    plugin = PrintSelection()
    info = plugin.get_info()
    print(f"\n插件名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    
    print("\n执行测试（模拟模式）:")
    result = plugin.execute()
    print(f"\n返回结果: {result}")
