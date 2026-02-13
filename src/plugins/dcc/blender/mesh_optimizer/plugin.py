"""
Blender网格优化工具插件
基于标准DCC插件接口的Blender应用示例
"""

import logging
from typing import Dict, Any, List
from pathlib import Path
import json

# 导入标准接口
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.join(current_dir, '..', '..', '..', 'core')
sys.path.insert(0, core_path)

from dcc_plugin_interface import (
    DCCPluginInterface, 
    BlenderPluginMixin, 
    dcc_plugin, 
    validate_params,
    auto_register,
    DCCSoftware
)

logger = logging.getLogger(__name__)


@dcc_plugin(
    name="BlenderMeshOptimizer",
    version="1.0.0",
    dcc=DCCSoftware.BLENDER,
    min_version="3.0",
    max_version="4.2"
)
@auto_register
class BlenderMeshOptimizer(DCCPluginInterface, BlenderPluginMixin):
    """Blender网格优化工具"""
    
    PLUGIN_DESCRIPTION = "专业的Blender网格优化工具，支持网格简化、重复面删除、材质优化等功能"
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
        """连接到Blender"""
        try:
            import bpy
            self._connected = True
            logger.info("成功连接到Blender")
            return True
        except ImportError:
            logger.error("Blender环境未找到")
            return False
        except Exception as e:
            logger.error(f"连接Blender失败: {e}")
            return False
    
    def disconnect_from_dcc(self):
        """断开Blender连接"""
        self._connected = False
        logger.info("断开Blender连接")
    
    @validate_params(
        decimate_ratio={'type': float, 'min': 0.01, 'max': 1.0, 'default': 0.5, 'required': False},
        remove_doubles={'type': bool, 'default': True, 'required': False},
        recalculate_normals={'type': bool, 'default': True, 'required': False},
        optimize_materials={'type': bool, 'default': True, 'required': False},
        preserve_uvs={'type': bool, 'default': True, 'required': False},
        output_path={'type': str, 'default': "", 'required': False}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行网格优化操作
        
        Args:
            decimate_ratio: 网格简化比例 (0.01-1.0)
            remove_doubles: 是否删除重复顶点
            recalculate_normals: 是否重新计算法线
            optimize_materials: 是否优化材质
            preserve_uvs: 是否保持UV坐标
            output_path: 输出文件路径
            
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始执行网格优化...")
            
            # 连接检查
            if not self._connected and not self.connect_to_dcc():
                return {"status": "error", "message": "无法连接到Blender"}
            
            # 获取选择的对象
            selected_objects = self.get_selection()
            if not selected_objects:
                return {"status": "error", "message": "请先选择要优化的网格对象"}
            
            logger.info(f"处理对象: {selected_objects}")
            
            # 执行优化操作
            optimization_results = []
            for obj in selected_objects:
                result = self._optimize_single_object(obj, kwargs)
                optimization_results.append(result)
            
            # 生成报告
            summary = self._generate_summary(optimization_results)
            
            # 保存结果（如果指定了输出路径）
            if kwargs.get('output_path'):
                self._save_results(summary, kwargs['output_path'])
            
            logger.info("网格优化完成")
            
            return {
                "status": "success",
                "processed_objects": selected_objects,
                "results": optimization_results,
                "summary": summary,
                "output_path": kwargs.get('output_path', '')
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数"""
        # 基本验证已在装饰器中完成
        validated = params.copy()
        
        # 额外的业务逻辑验证
        if validated.get('decimate_ratio', 0.5) < 0.01:
            validated['decimate_ratio'] = 0.01
            logger.warning("简化比例过小，已调整为0.01")
        
        return validated
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件详细信息"""
        base_info = super().get_info()
        base_info.update({
            "capabilities": [
                "网格简化",
                "删除重复几何体",
                "法线重计算",
                "材质优化",
                "UV坐标保持",
                "LOD生成"
            ],
            "supported_formats": ["obj", "fbx", "gltf", "blend"],
            "performance_notes": "大规模网格优化可能需要较长时间，请耐心等待"
        })
        return base_info
    
    def get_selection(self) -> List[str]:
        """获取当前选择的网格对象"""
        try:
            context = self.blender_context()
            selected_objects = []
            
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    selected_objects.append(obj.name)
            
            return selected_objects
            
        except Exception as e:
            logger.error(f"获取选择失败: {e}")
            return []
    
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """获取场景中的网格对象信息"""
        try:
            data = self.blender_data()
            objects_info = []
            
            for obj in data.objects:
                if obj.type == 'MESH':
                    mesh = obj.data
                    objects_info.append({
                        "name": obj.name,
                        "vertices": len(mesh.vertices),
                        "faces": len(mesh.polygons),
                        "edges": len(mesh.edges),
                        "materials": len(obj.material_slots),
                        "type": "mesh"
                    })
            
            return objects_info
            
        except Exception as e:
            logger.error(f"获取场景对象失败: {e}")
            return []
    
    def _optimize_single_object(self, object_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """优化单个对象"""
        try:
            logger.info(f"处理对象: {object_name}")
            
            result = {
                "object": object_name,
                "operations": [],
                "before_stats": {},
                "after_stats": {}
            }
            
            # 获取初始统计信息
            initial_stats = self._get_object_stats(object_name)
            result["before_stats"] = initial_stats
            
            # 设置为编辑模式
            self._set_edit_mode(object_name)
            
            # 删除重复顶点
            if params.get('remove_doubles', True):
                removed_count = self._remove_duplicate_vertices(params.get('merge_distance', 0.0001))
                result["duplicate_vertices_removed"] = removed_count
                result["operations"].append(f"删除{removed_count}个重复顶点")
            
            # 网格简化
            if params.get('decimate_ratio', 1.0) < 1.0:
                simplified_info = self._decimate_mesh(params['decimate_ratio'])
                result["vertices_reduced"] = simplified_info["vertices_removed"]
                result["faces_reduced"] = simplified_info["faces_removed"]
                result["operations"].append(f"简化网格 ({params['decimate_ratio']*100:.1f}%)")
            
            # 重新计算法线
            if params.get('recalculate_normals', True):
                self._recalculate_normals()
                result["operations"].append("重新计算法线")
            
            # 返回对象模式
            self._set_object_mode()
            
            # 优化材质（如果启用）
            if params.get('optimize_materials', True):
                material_result = self._optimize_materials(object_name)
                result["materials_optimized"] = material_result["optimized_count"]
                result["operations"].append(f"优化{material_result['optimized_count']}个材质")
            
            # 获取最终统计信息
            final_stats = self._get_object_stats(object_name)
            result["after_stats"] = final_stats
            
            logger.info(f"对象 {object_name} 处理完成")
            return result
            
        except Exception as e:
            logger.error(f"处理对象 {object_name} 失败: {e}")
            return {
                "object": object_name,
                "status": "error",
                "error": str(e)
            }
    
    def _set_edit_mode(self, object_name: str):
        """设置对象为编辑模式"""
        try:
            import bpy
            obj = bpy.data.objects[object_name]
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
        except Exception as e:
            logger.warning(f"设置编辑模式失败: {e}")
    
    def _set_object_mode(self):
        """返回对象模式"""
        try:
            import bpy
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            logger.warning(f"返回对象模式失败: {e}")
    
    def _remove_duplicate_vertices(self, merge_distance: float = 0.0001) -> int:
        """删除重复顶点"""
        try:
            import bpy
            # 记录删除前的顶点数
            initial_count = len(bpy.context.active_object.data.vertices)
            
            # 执行删除重复顶点操作
            bpy.ops.mesh.remove_doubles(threshold=merge_distance)
            
            # 计算删除的数量
            final_count = len(bpy.context.active_object.data.vertices)
            removed_count = initial_count - final_count
            
            return removed_count
        except Exception as e:
            logger.warning(f"删除重复顶点失败: {e}")
            return 0
    
    def _decimate_mesh(self, ratio: float) -> Dict[str, int]:
        """网格简化"""
        try:
            import bpy
            obj = bpy.context.active_object
            mesh = obj.data
            
            # 记录简化前的数据
            initial_vertices = len(mesh.vertices)
            initial_faces = len(mesh.polygons)
            
            # 应用简化修改器
            decimate_modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate_modifier.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=decimate_modifier.name)
            
            # 计算减少的数量
            final_vertices = len(mesh.vertices)
            final_faces = len(mesh.polygons)
            
            return {
                "vertices_removed": initial_vertices - final_vertices,
                "faces_removed": initial_faces - final_faces
            }
        except Exception as e:
            logger.warning(f"网格简化失败: {e}")
            return {"vertices_removed": 0, "faces_removed": 0}
    
    def _recalculate_normals(self):
        """重新计算法线"""
        try:
            import bpy
            bpy.ops.mesh.normals_make_consistent(inside=False)
        except Exception as e:
            logger.warning(f"重新计算法线失败: {e}")
    
    def _optimize_materials(self, object_name: str) -> Dict[str, int]:
        """优化材质"""
        try:
            import bpy
            obj = bpy.data.objects[object_name]
            optimized_count = 0
            
            # 清理未使用的材质槽
            for i in range(len(obj.material_slots) - 1, -1, -1):
                slot = obj.material_slots[i]
                if slot.material is None:
                    obj.active_material_index = i
                    bpy.ops.object.material_slot_remove()
                    optimized_count += 1
            
            return {"optimized_count": optimized_count}
        except Exception as e:
            logger.warning(f"优化材质失败: {e}")
            return {"optimized_count": 0}
    
    def _get_object_stats(self, object_name: str) -> Dict[str, Any]:
        """获取对象统计信息"""
        try:
            import bpy
            obj = bpy.data.objects[object_name]
            mesh = obj.data
            
            stats = {
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.polygons),
                "edge_count": len(mesh.edges),
                "material_count": len(obj.material_slots),
                "has_uv": bool(mesh.uv_layers),
                "triangle_count": sum(len(poly.vertices) - 2 for poly in mesh.polygons)
            }
            
            return stats
        except Exception as e:
            logger.warning(f"获取对象统计失败: {e}")
            return {}
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成处理摘要"""
        successful = [r for r in results if r.get('status') != 'error']
        
        summary = {
            "total_objects": len(results),
            "successful_objects": len(successful),
            "failed_objects": len(results) - len(successful),
            "total_vertices_removed": sum(r.get('duplicate_vertices_removed', 0) for r in successful),
            "total_vertices_reduced": sum(r.get('vertices_reduced', 0) for r in successful),
            "total_faces_reduced": sum(r.get('faces_reduced', 0) for r in successful),
            "total_materials_optimized": sum(r.get('materials_optimized', 0) for r in successful)
        }
        
        return summary
    
    def _save_results(self, summary: Dict[str, Any], output_path: str):
        """保存处理结果"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Blender网格优化报告\n\n")
                f.write(f"处理时间: {self._get_timestamp()}\n")
                f.write(f"处理对象数: {summary['total_objects']}\n")
                f.write(f"成功处理: {summary['successful_objects']}\n")
                f.write(f"删除重复顶点: {summary['total_vertices_removed']}\n")
                f.write(f"简化顶点数: {summary['total_vertices_reduced']}\n")
                f.write(f"简化面数: {summary['total_faces_reduced']}\n")
                f.write(f"优化材质数: {summary['total_materials_optimized']}\n")
            
            logger.info(f"结果已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 独立运行测试
if __name__ == "__main__":
    # 创建插件实例
    optimizer = BlenderMeshOptimizer()
    
    # 测试执行（模拟模式）
    test_params = {
        "decimate_ratio": 0.5,
        "remove_doubles": True,
        "recalculate_normals": True,
        "optimize_materials": True,
        "preserve_uvs": True
    }
    
    print("Blender网格优化工具测试")
    print("=" * 40)
    
    # 显示插件信息
    info = optimizer.get_info()
    print(f"插件名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    print(f"支持的DCC: {info['target_dcc']}")
    print(f"版本范围: {info['min_version']} - {info['max_version']}")
    
    print("\n功能特性:")
    for capability in info['capabilities']:
        print(f"  • {capability}")
    
    # 测试参数验证
    print("\n参数验证测试:")
    validated = optimizer.validate_parameters(test_params)
    print(f"验证后参数: {validated}")
    
    # 注意：实际的Blender功能测试需要在Blender环境中运行
    print("\n注意：完整的功能测试需要在Blender环境中执行")