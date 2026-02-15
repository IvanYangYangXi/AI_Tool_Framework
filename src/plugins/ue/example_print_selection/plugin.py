
"""
Unreal Engine打印选择资产 - 示例脚本

获取UE编辑器中当前选择的资产并打印其名称
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# 插件元数据常量
PLUGIN_NAME = "[示例] UE打印选择"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "ue_engine"
PLUGIN_DESCRIPTION = "获取Unreal Engine中选择的资产并打印其名称 - 示例脚本"
PLUGIN_AUTHOR = "DCC Tool Framework Team"


class PrintSelection:
    """Unreal Engine打印选择资产工具"""
    
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
        """连接到Unreal Engine"""
        try:
            import unreal
            self._connected = True
            logger.info("成功连接到Unreal Engine")
            return True
        except ImportError:
            logger.warning("Unreal Engine环境未找到，使用模拟模式")
            return False
        except Exception as e:
            logger.error(f"连接Unreal Engine失败: {e}")
            return False
    
    def disconnect_from_dcc(self):
        """断开UE连接"""
        self._connected = False
        logger.info("断开Unreal Engine连接")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行主功能：获取选择的资产并打印名称
        
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始获取选择的资产...")
            
            # 尝试连接UE
            if not self._connected:
                self.connect_to_dcc()
            
            # 获取选择的资产
            selected_assets = self.get_selection()
            
            # 打印结果
            if selected_assets:
                print("\n" + "=" * 50)
                print("【选择的资产】")
                print("=" * 50)
                for i, asset_name in enumerate(selected_assets, 1):
                    print(f"  {i}. {asset_name}")
                print("=" * 50)
                print(f"总计: {len(selected_assets)} 个资产")
                print("=" * 50 + "\n")
                
                return {
                    "status": "success",
                    "selected_assets": selected_assets,
                    "count": len(selected_assets),
                    "message": f"成功获取 {len(selected_assets)} 个资产"
                }
            else:
                print("\n【提示】没有选择任何资产\n")
                
                return {
                    "status": "success",
                    "selected_assets": [],
                    "count": 0,
                    "message": "没有选择任何资产"
                }
                
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "selected_assets": [],
                "count": 0,
                "message": str(e)
            }
    
    def get_selection(self) -> List[str]:
        """获取当前选择的资产"""
        try:
            if self._connected:
                import unreal
                # 获取内容浏览器选择的资产
                # EditorUtilityLibrary 是静态类，直接调用方法
                selected = unreal.EditorUtilityLibrary.get_selected_assets()
                return [asset.get_name() for asset in selected]
            else:
                # 模拟模式
                logger.info("模拟模式：返回测试数据")
                return ["SM_Chair", "M_Wood", "T_Wood_D"]
                
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


def run_in_unreal():
    """Unreal Engine直接执行入口"""
    plugin = PrintSelection()
    result = plugin.execute()
    return result


# 检测是否在UE环境中
def _is_in_unreal():
    try:
        import unreal
        return True
    except ImportError:
        return False


# 自动执行逻辑
if _is_in_unreal():
    # 在UE环境中，直接执行
    run_in_unreal()
else:
    # 本地测试模式（不在UE环境中）
    if __name__ == "__main__":
        print("\n" + "=" * 60)
        print("Unreal Engine 打印选择资产工具 - 本地测试模式")
        print("=" * 60)
        
        plugin = PrintSelection()
        info = plugin.get_info()
        print(f"\n插件名称: {info['name']}")
        print(f"版本: {info['version']}")
        print(f"描述: {info['description']}")
        
        print("\n执行测试（模拟模式）:")
        result = plugin.execute()
        print(f"\n返回结果: {result}")
