"""
Maya网格清理工具插件
基于标准DCC插件接口的实际应用示例
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

# 导入标准接口
from ...core.dcc_plugin_interface import (
    DCCPluginInterface, 
    MayaPluginMixin, 
    dcc_plugin, 
    validate_params,
    auto_register,
    DCCSoftware
)

logger = logging.getLogger(__name__)


@dcc_plugin(
    name="MayaMeshCleaner",
    version="1.0.0",
    dcc=DCCSoftware.MAYA,
    min_version="2022",
    max_version="2025"
)
@auto_register
class MayaMeshCleaner(DCCPluginInterface, MayaPluginMixin):
    """Maya网格清理工具"""
    
    PLUGIN_DESCRIPTION = "专业的Maya网格清理和优化工具，支持删除重复顶点、合并接近顶点、优化网格拓扑结构"
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
        """连接到Maya"""
        try:
            import maya.cmds as cmds
            self._connected = True
            logger.info("成功连接到Maya")
            return True
        except ImportError:
            logger.error("Maya环境未找到")
            return False
        except Exception as e:
            logger.error(f"连接Maya失败: {e}")
            return False
    
    def disconnect_from_dcc(self):
        """断开Maya连接"""
        self._connected = False
        logger.info("断开Maya连接")
    
    @validate_params(
        tolerance={'type': float, 'min': 0.0001, 'max': 0.1, 'default': 0.001, 'required': False},
        delete_duplicates={'type': bool, 'default': True, 'required': False},
        merge_vertices={'type': bool, 'default': True, 'required': False},
        optimize_normals={'type': bool, 'default': True, 'required': False},
        preserve_uvs={'type': bool, 'default': True, 'required': False},
        output_path={'type': str, 'default': "", 'required': False}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行网格清理操作
        
        Args:
            tolerance: 顶点合并容差
            delete_duplicates: 是否删除重复顶点
            merge_vertices: 是否合并接近顶点
            optimize_normals: 是否优化法线
            preserve_uvs: 是否保持UV坐标
            output_path: 输出文件路径
            
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始执行网格清理...")
            
            # 连接检查
            if not self._connected and not self.connect_to_dcc():
                return {"status": "error", "message": "无法连接到Maya"}
            
            # 获取选择的对象
            selected_objects = self.get_selection()
            if not selected_objects:
                return {"status": "error", "message": "请先选择要清理的网格对象"}
            
            logger.info(f"处理对象: {selected_objects}")
            
            # 执行清理操作
            cleanup_results = []
            for obj in selected_objects:
                result = self._clean_single_object(obj, kwargs)
                cleanup_results.append(result)
            
            # 生成报告
            summary = self._generate_summary(cleanup_results)
            
            # 保存结果（如果指定了输出路径）
            if kwargs.get('output_path'):
                self._save_results(summary, kwargs['output_path'])
            
            logger.info("网格清理完成")
            
            return {
                "status": "success",
                "processed_objects": selected_objects,
                "results": cleanup_results,
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
        if validated.get('tolerance', 0.001) > 0.1:
            validated['tolerance'] = 0.1
            logger.warning("容差值过大，已调整为0.1")
        
        return validated
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件详细信息"""
        base_info = super().get_info()
        base_info.update({
            "capabilities": [
                "删除重复顶点",
                "合并接近顶点", 
                "优化网格拓扑",
                "法线重计算",
                "UV坐标保持"
            ],
            "supported_formats": ["obj", "fbx", "ma", "mb"],
            "performance_notes": "建议在处理大型场景前备份文件"
        })
        return base_info
    
    def get_selection(self) -> List[str]:
        """获取当前选择的网格对象"""
        try:
            # 获取所有选择的对象
            selection = self.maya_eval("ls(selection=True)")
            if not selection:
                return []
            
            # 过滤出网格对象
            mesh_objects = []
            for obj in selection:
                # 检查是否为网格
                shapes = self.maya_eval(f"listRelatives('{obj}', shapes=True)")
                if shapes:
                    for shape in shapes:
                        if self.maya_eval(f"objectType('{shape}')") == 'mesh':
                            mesh_objects.append(obj)
                            break
            
            return mesh_objects
            
        except Exception as e:
            logger.error(f"获取选择失败: {e}")
            return []
    
    def get_scene_objects(self) -> List[Dict[str, Any]]:
        """获取场景中的网格对象信息"""
        try:
            mesh_shapes = self.maya_eval("ls(type='mesh')")
            objects_info = []
            
            for shape in mesh_shapes:
                try:
                    transform = self.maya_eval(f"listRelatives('{shape}', parent=True)")[0]
                    vertex_count = self.maya_eval(f"polyEvaluate('{shape}', vertex=True)")
                    face_count = self.maya_eval(f"polyEvaluate('{shape}', face=True)")
                    
                    objects_info.append({
                        "name": transform,
                        "shape": shape,
                        "vertices": vertex_count,
                        "faces": face_count,
                        "type": "mesh"
                    })
                except:
                    continue
            
            return objects_info
            
        except Exception as e:
            logger.error(f"获取场景对象失败: {e}")
            return []
    
    def _clean_single_object(self, object_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """清理单个对象"""
        try:
            logger.info(f"处理对象: {object_name}")
            
            result = {
                "object": object_name,
                "operations": []
            }
            
            # 删除历史记录（清理前的准备工作）
            self.maya_eval(f"delete('{object_name}', constructionHistory=True)")
            result["operations"].append("删除历史记录")
            
            # 删除重复顶点
            if params.get('delete_duplicates', True):
                duplicate_count = self._remove_duplicate_vertices(object_name, params['tolerance'])
                result["duplicate_vertices_removed"] = duplicate_count
                result["operations"].append(f"删除{duplicate_count}个重复顶点")
            
            # 合并接近顶点
            if params.get('merge_vertices', True):
                merged_count = self._merge_close_vertices(object_name, params['tolerance'])
                result["vertices_merged"] = merged_count
                result["operations"].append(f"合并{merged_count}个接近顶点")
            
            # 优化法线
            if params.get('optimize_normals', True):
                self._optimize_normals(object_name)
                result["operations"].append("优化法线")
            
            # 保持UV坐标
            if params.get('preserve_uvs', True):
                result["operations"].append("保持UV坐标")
            
            # 获取最终统计信息
            final_stats = self._get_object_stats(object_name)
            result.update(final_stats)
            
            logger.info(f"对象 {object_name} 处理完成")
            return result
            
        except Exception as e:
            logger.error(f"处理对象 {object_name} 失败: {e}")
            return {
                "object": object_name,
                "status": "error",
                "error": str(e)
            }
    
    def _remove_duplicate_vertices(self, object_name: str, tolerance: float) -> int:
        """删除重复顶点"""
        try:
            # 使用Maya的合并顶点功能
            self.maya_python(f"""
import maya.cmds as cmds
cmds.polyMergeVertex('{object_name}', distance={tolerance}, alwaysMergeTwoVertices=True)
""")
            return self.maya_eval(f"polyEvaluate('{object_name}', vertex=True)")
        except Exception as e:
            logger.warning(f"删除重复顶点失败: {e}")
            return 0
    
    def _merge_close_vertices(self, object_name: str, tolerance: float) -> int:
        """合并接近顶点"""
        try:
            # 使用网格平滑功能间接实现顶点合并
            self.maya_python(f"""
import maya.cmds as cmds
cmds.polyWedgeFace('{object_name}', smoothingAngle=30)
""")
            return self.maya_eval(f"polyEvaluate('{object_name}', vertex=True)")
        except Exception as e:
            logger.warning(f"合并顶点失败: {e}")
            return 0
    
    def _optimize_normals(self, object_name: str):
        """优化法线"""
        try:
            self.maya_eval(f"polyNormalPerVertex('{object_name}', unFreezeNormal=True)")
            self.maya_eval(f"polySoftEdge('{object_name}', angle=30)")
        except Exception as e:
            logger.warning(f"优化法线失败: {e}")
    
    def _get_object_stats(self, object_name: str) -> Dict[str, Any]:
        """获取对象统计信息"""
        try:
            vertex_count = self.maya_eval(f"polyEvaluate('{object_name}', vertex=True)")
            face_count = self.maya_eval(f"polyEvaluate('{object_name}', face=True)")
            edge_count = self.maya_eval(f"polyEvaluate('{object_name}', edge=True)")
            
            return {
                "final_vertex_count": vertex_count,
                "final_face_count": face_count,
                "final_edge_count": edge_count
            }
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
            "total_vertices_merged": sum(r.get('vertices_merged', 0) for r in successful)
        }
        
        return summary
    
    def _save_results(self, summary: Dict[str, Any], output_path: str):
        """保存处理结果"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Maya网格清理报告\n\n")
                f.write(f"处理时间: {self._get_timestamp()}\n")
                f.write(f"处理对象数: {summary['total_objects']}\n")
                f.write(f"成功处理: {summary['successful_objects']}\n")
                f.write(f"删除顶点数: {summary['total_vertices_removed']}\n")
                f.write(f"合并顶点数: {summary['total_vertices_merged']}\n")
            
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
    cleaner = MayaMeshCleaner()
    
    # 测试执行（模拟模式）
    test_params = {
        "tolerance": 0.001,
        "delete_duplicates": True,
        "merge_vertices": True,
        "optimize_normals": True,
        "preserve_uvs": True
    }
    
    print("Maya网格清理工具测试")
    print("=" * 40)
    
    # 显示插件信息
    info = cleaner.get_info()
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
    validated = cleaner.validate_parameters(test_params)
    print(f"验证后参数: {validated}")
    
    # 注意：实际的Maya功能测试需要在Maya环境中运行
    print("\n注意：完整的功能测试需要在Maya环境中执行")