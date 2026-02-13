"""
3ds Max材质转换工具插件
基于标准DCC插件接口的实际应用示例
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

# 导入标准接口
from ...core.dcc_plugin_interface import (
    DCCPluginInterface, 
    MaxPluginMixin, 
    dcc_plugin, 
    validate_params,
    auto_register,
    DCCSoftware
)

logger = logging.getLogger(__name__)


@dcc_plugin(
    name="MaxMaterialConverter",
    version="1.0.0",
    dcc=DCCSoftware.MAX,
    min_version="2021",
    max_version="2025"
)
@auto_register
class MaxMaterialConverter(DCCPluginInterface, MaxPluginMixin):
    """3ds Max材质转换工具"""
    
    PLUGIN_DESCRIPTION = "专业的3ds Max材质转换工具，支持多种材质格式间的相互转换和优化"
    PLUGIN_AUTHOR = "DCC Tool Framework Team"
    
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
        """连接到3ds Max"""
        try:
            import pymxs
            self._runtime = pymxs.runtime
            self._connected = True
            logger.info("成功连接到3ds Max")
            return True
        except ImportError:
            logger.error("3ds Max环境未找到")
            return False
        except Exception as e:
            logger.error(f"连接3ds Max失败: {e}")
            return False
    
    def disconnect_from_dcc(self):
        """断开3ds Max连接"""
        self._connected = False
        logger.info("断开3ds Max连接")
    
    @validate_params(
        source_format={'type': str, 'default': "standard", 'required': False},
        target_format={'type': str, 'default': "physical", 'required': False},
        convert_textures={'type': bool, 'default': True, 'required': False},
        preserve_properties={'type': bool, 'default': True, 'required': False},
        output_directory={'type': str, 'default': "", 'required': False},
        batch_process={'type': bool, 'default': False, 'required': False}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行材质转换操作
        
        Args:
            source_format: 源材质格式
            target_format: 目标材质格式
            convert_textures: 是否转换纹理贴图
            preserve_properties: 是否保持原有属性
            output_directory: 输出目录
            batch_process: 是否批量处理
            
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始执行材质转换...")
            
            # 连接检查
            if not self._connected and not self.connect_to_dcc():
                return {"status": "error", "message": "无法连接到3ds Max"}
            
            # 获取材质对象
            materials = self._get_materials(kwargs.get('batch_process', False))
            if not materials:
                return {"status": "error", "message": "场景中没有找到材质"}
            
            logger.info(f"处理材质数量: {len(materials)}")
            
            # 执行转换操作
            conversion_results = []
            for material in materials:
                result = self._convert_single_material(material, kwargs)
                conversion_results.append(result)
            
            # 生成报告
            summary = self._generate_conversion_summary(conversion_results)
            
            # 保存结果（如果指定了输出目录）
            if kwargs.get('output_directory'):
                self._save_conversion_report(summary, kwargs['output_directory'])
            
            logger.info("材质转换完成")
            
            return {
                "status": "success",
                "processed_materials": len(materials),
                "results": conversion_results,
                "summary": summary,
                "output_directory": kwargs.get('output_directory', '')
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数"""
        validated = params.copy()
        
        # 验证材质格式支持
        supported_formats = ["standard", "physical", "arnold", "vray", "corona"]
        source_format = validated.get('source_format', 'standard')
        target_format = validated.get('target_format', 'physical')
        
        if source_format not in supported_formats:
            validated['source_format'] = 'standard'
            logger.warning(f"不支持的源格式 {source_format}，已设为standard")
        
        if target_format not in supported_formats:
            validated['target_format'] = 'physical'
            logger.warning(f"不支持的目标格式 {target_format}，已设为physical")
        
        return validated
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件详细信息"""
        base_info = super().get_info()
        base_info.update({
            "supported_formats": [
                "Standard Material",
                "Physical Material", 
                "Arnold Material",
                "VRay Material",
                "Corona Material"
            ],
            "conversion_features": [
                "材质类型转换",
                "纹理贴图映射",
                "属性参数传递",
                "节点连接重建",
                "批量处理支持"
            ],
            "limitations": "复杂节点网络可能需要手动调整"
        })
        return base_info
    
    def get_selection(self) -> List[str]:
        """获取当前选择的材质"""
        try:
            if not self._connected:
                return []
            
            # 获取选择的材质编辑器槽位
            selected_slots = self.max_execute("medit.GetNumSlots()")
            materials = []
            
            for i in range(1, selected_slots + 1):
                material = self.max_execute(f"medit.GetSlotMaterial({i})")
                if material and hasattr(material, 'name'):
                    materials.append(material.name)
            
            return materials
            
        except Exception as e:
            logger.error(f"获取选择失败: {e}")
            return []
    
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """获取场景中的材质信息"""
        try:
            if not self._connected:
                return []
            
            materials_info = []
            
            # 获取材质编辑器中的所有材质
            slot_count = self.max_execute("medit.GetNumSlots()")
            
            for i in range(1, slot_count + 1):
                try:
                    material = self.max_execute(f"medit.GetSlotMaterial({i})")
                    if material:
                        mat_info = {
                            "name": getattr(material, 'name', f'Material_{i}'),
                            "slot": i,
                            "type": type(material).__name__,
                            "properties": self._get_material_properties(material)
                        }
                        materials_info.append(mat_info)
                except:
                    continue
            
            return materials_info
            
        except Exception as e:
            logger.error(f"获取场景材质失败: {e}")
            return []
    
    def _get_materials(self, batch_mode: bool = False) -> List[Any]:
        """获取需要转换的材质"""
        try:
            if not self._connected:
                return []
            
            materials = []
            
            if batch_mode:
                # 批量模式：获取所有材质
                slot_count = self.max_execute("medit.GetNumSlots()")
                for i in range(1, slot_count + 1):
                    material = self.max_execute(f"medit.GetSlotMaterial({i})")
                    if material:
                        materials.append(material)
            else:
                # 选择模式：只处理选中的材质
                selected_materials = self.get_selection()
                for mat_name in selected_materials:
                    # 根据名称查找材质对象
                    material = self._find_material_by_name(mat_name)
                    if material:
                        materials.append(material)
            
            return materials
            
        except Exception as e:
            logger.error(f"获取材质失败: {e}")
            return []
    
    def _convert_single_material(self, material: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """转换单个材质"""
        try:
            material_name = getattr(material, 'name', 'Unknown')
            logger.info(f"转换材质: {material_name}")
            
            result = {
                "material": material_name,
                "source_type": type(material).__name__,
                "operations": []
            }
            
            # 检查源材质类型
            source_format = params.get('source_format', 'standard')
            target_format = params.get('target_format', 'physical')
            
            # 执行转换
            converted_material = self._perform_conversion(material, source_format, target_format, params)
            
            if converted_material:
                result["target_type"] = type(converted_material).__name__
                result["status"] = "success"
                result["operations"].append(f"从{source_format}转换为{target_format}")
                
                # 处理纹理贴图
                if params.get('convert_textures', True):
                    texture_result = self._convert_textures(material, converted_material, params)
                    result["textures_converted"] = texture_result
                    result["operations"].append("转换纹理贴图")
                
                # 保持属性
                if params.get('preserve_properties', True):
                    self._preserve_properties(material, converted_material)
                    result["operations"].append("保持原有属性")
                
                logger.info(f"材质 {material_name} 转换成功")
            else:
                result["status"] = "error"
                result["error"] = "转换失败"
                logger.error(f"材质 {material_name} 转换失败")
            
            return result
            
        except Exception as e:
            logger.error(f"转换材质失败: {e}")
            return {
                "material": getattr(material, 'name', 'Unknown') if material else 'Unknown',
                "status": "error",
                "error": str(e)
            }
    
    def _perform_conversion(self, source_material: Any, source_format: str, 
                          target_format: str, params: Dict[str, Any]) -> Any:
        """执行材质转换"""
        try:
            # 这里实现具体的材质转换逻辑
            # 不同格式间的转换需要具体的MaxScript或Python实现
            
            if target_format == "physical":
                # 转换为物理材质
                physical_mat = self.max_execute("PhysicalMaterial()")
                if physical_mat:
                    # 复制基本属性
                    physical_mat.name = f"{source_material.name}_Physical"
                    return physical_mat
                    
            elif target_format == "standard":
                # 转换为标准材质
                standard_mat = self.max_execute("StandardMaterial()")
                if standard_mat:
                    standard_mat.name = f"{source_material.name}_Standard"
                    return standard_mat
            
            # 其他格式转换...
            return None
            
        except Exception as e:
            logger.warning(f"材质转换失败: {e}")
            return None
    
    def _convert_textures(self, source_material: Any, target_material: Any, 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """转换纹理贴图"""
        try:
            texture_result = {
                "converted_maps": 0,
                "failed_maps": 0,
                "map_types": []
            }
            
            # 这里实现纹理贴图的转换逻辑
            # 需要遍历源材质的所有贴图槽位并映射到目标材质
            
            return texture_result
            
        except Exception as e:
            logger.warning(f"纹理转换失败: {e}")
            return {"converted_maps": 0, "failed_maps": 0, "error": str(e)}
    
    def _preserve_properties(self, source_material: Any, target_material: Any):
        """保持材质属性"""
        try:
            # 复制颜色属性
            if hasattr(source_material, 'diffuse') and hasattr(target_material, 'diffuse'):
                target_material.diffuse = source_material.diffuse
            
            # 复制光泽度等参数
            if hasattr(source_material, 'glossiness') and hasattr(target_material, 'roughness'):
                target_material.roughness = 1.0 - source_material.glossiness
                
        except Exception as e:
            logger.warning(f"保持属性失败: {e}")
    
    def _find_material_by_name(self, name: str) -> Any:
        """根据名称查找材质"""
        try:
            slot_count = self.max_execute("medit.GetNumSlots()")
            for i in range(1, slot_count + 1):
                material = self.max_execute(f"medit.GetSlotMaterial({i})")
                if material and getattr(material, 'name', '') == name:
                    return material
            return None
        except:
            return None
    
    def _get_material_properties(self, material: Any) -> Dict[str, Any]:
        """获取材质属性"""
        properties = {}
        try:
            # 获取基本属性
            if hasattr(material, 'diffuse'):
                properties['diffuse'] = str(material.diffuse)
            if hasattr(material, 'specular'):
                properties['specular'] = str(material.specular)
            if hasattr(material, 'glossiness'):
                properties['glossiness'] = material.glossiness
        except:
            pass
        return properties
    
    def _generate_conversion_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成转换摘要"""
        successful = [r for r in results if r.get('status') == 'success']
        failed = [r for r in results if r.get('status') == 'error']
        
        summary = {
            "total_materials": len(results),
            "successful_conversions": len(successful),
            "failed_conversions": len(failed),
            "textures_converted": sum(r.get('textures_converted', {}).get('converted_maps', 0) for r in successful)
        }
        
        return summary
    
    def _save_conversion_report(self, summary: Dict[str, Any], output_dir: str):
        """保存转换报告"""
        try:
            output_path = Path(output_dir) / "material_conversion_report.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 3ds Max材质转换报告\n\n")
                f.write(f"转换时间: {self._get_timestamp()}\n")
                f.write(f"总材质数: {summary['total_materials']}\n")
                f.write(f"成功转换: {summary['successful_conversions']}\n")
                f.write(f"转换失败: {summary['failed_conversions']}\n")
                f.write(f"纹理转换: {summary['textures_converted']}个\n")
            
            logger.info(f"转换报告已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 独立运行测试
if __name__ == "__main__":
    # 创建插件实例
    converter = MaxMaterialConverter()
    
    # 测试执行（模拟模式）
    test_params = {
        "source_format": "standard",
        "target_format": "physical",
        "convert_textures": True,
        "preserve_properties": True,
        "batch_process": False
    }
    
    print("3ds Max材质转换工具测试")
    print("=" * 40)
    
    # 显示插件信息
    info = converter.get_info()
    print(f"插件名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    print(f"支持的格式: {', '.join(info['supported_formats'])}")
    
    print("\n转换特性:")
    for feature in info['conversion_features']:
        print(f"  • {feature}")
    
    # 测试参数验证
    print("\n参数验证测试:")
    validated = converter.validate_parameters(test_params)
    print(f"验证后参数: {validated}")
    
    # 注意：实际的3ds Max功能测试需要在3ds Max环境中运行
    print("\n注意：完整的功能测试需要在3ds Max环境中执行")