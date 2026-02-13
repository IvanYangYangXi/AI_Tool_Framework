"""
Unreal Engine资产优化工具插件
基于标准UE插件接口的实际应用示例
"""

import logging
from typing import Dict, Any, List
from pathlib import Path
import json

# 导入标准接口
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.join(current_dir, '..', '..', 'core')
sys.path.insert(0, core_path)

from ue_plugin_interface import (
    UEPluginInterface, 
    UEEditorMixin, 
    UEMixin,
    ue_plugin, 
    validate_params,
    auto_register,
    UEVersion,
    UEProjectType
)

logger = logging.getLogger(__name__)


@ue_plugin(
    name="UEAssetOptimizer",
    version="1.0.0",
    ue_version=UEVersion.UE5_1,
    project_type=UEProjectType.CPP,
    min_version="5.0",
    max_version="5.4"
)
@auto_register
class UEAssetOptimizer(UEPluginInterface, UEEditorMixin, UEMixin):
    """Unreal Engine资产优化工具"""
    
    PLUGIN_DESCRIPTION = "专业的UE资产优化工具，支持纹理压缩、网格LOD生成、材质实例化等功能"
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
    
    def connect_to_ue(self) -> bool:
        """连接到UE编辑器"""
        try:
            # 模拟连接到UE
            self._connected = True
            logger.info("成功连接到UE编辑器")
            return True
        except Exception as e:
            logger.error(f"连接UE失败: {e}")
            return False
    
    def disconnect_from_ue(self):
        """断开UE连接"""
        self._connected = False
        logger.info("断开UE连接")
    
    @validate_params(
        texture_quality={'type': int, 'min': 1, 'max': 100, 'default': 75, 'required': False},
        generate_lods={'type': bool, 'default': True, 'required': False},
        create_material_instances={'type': bool, 'default': True, 'required': False},
        compress_textures={'type': bool, 'default': True, 'required': False},
        optimize_collision={'type': bool, 'default': True, 'required': False},
        output_report={'type': bool, 'default': True, 'required': False}
    )
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行资产优化操作
        
        Args:
            texture_quality: 纹理质量 (1-100)
            generate_lods: 是否生成LOD
            create_material_instances: 是否创建材质实例
            compress_textures: 是否压缩纹理
            optimize_collision: 是否优化碰撞
            output_report: 是否输出报告
            
        Returns:
            执行结果字典
        """
        try:
            logger.info("开始执行资产优化...")
            
            # 连接检查
            if not self._connected and not self.connect_to_ue():
                return {"status": "error", "message": "无法连接到UE编辑器"}
            
            # 获取选择的资产
            selected_assets = self.get_selected_assets()
            if not selected_assets:
                return {"status": "error", "message": "请先选择要优化的资产"}
            
            logger.info(f"处理资产: {[asset['path'] for asset in selected_assets]}")
            
            # 执行优化操作
            optimization_results = []
            for asset in selected_assets:
                result = self._optimize_single_asset(asset, kwargs)
                optimization_results.append(result)
            
            # 生成报告
            summary = self._generate_summary(optimization_results)
            
            # 保存报告（如果启用）
            if kwargs.get('output_report', True):
                self._save_report(summary)
            
            logger.info("资产优化完成")
            
            return {
                "status": "success",
                "processed_assets": [asset['path'] for asset in selected_assets],
                "results": optimization_results,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数"""
        # 基本验证已在装饰器中完成
        validated = params.copy()
        
        # 额外的业务逻辑验证
        if validated.get('texture_quality', 75) < 10:
            validated['texture_quality'] = 10
            logger.warning("纹理质量过低，已调整为10")
        
        return validated
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件详细信息"""
        base_info = super().get_info()
        base_info.update({
            "capabilities": [
                "纹理压缩优化",
                "网格LOD自动生成",
                "材质实例化",
                "碰撞体优化",
                "资产大小分析",
                "性能报告生成"
            ],
            "supported_asset_types": ["StaticMesh", "Texture2D", "Material", "SkeletalMesh"],
            "performance_notes": "大规模资产优化可能需要较长时间，请耐心等待"
        })
        return base_info
    
    def get_selected_assets(self) -> List[Dict[str, Any]]:
        """获取当前选择的资产"""
        try:
            # 模拟获取UE中选择的资产
            # 在实际实现中，这里会调用UE的Python API
            selected_assets = [
                {
                    "path": "/Game/Meshes/SM_Character",
                    "type": "SkeletalMesh",
                    "size": "2048x2048"
                },
                {
                    "path": "/Game/Textures/T_Character_Diffuse", 
                    "type": "Texture2D",
                    "size": "4096x4096"
                },
                {
                    "path": "/Game/Materials/M_Character",
                    "type": "Material",
                    "complexity": "High"
                }
            ]
            
            return selected_assets
            
        except Exception as e:
            logger.error(f"获取选择资产失败: {e}")
            return []
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        try:
            # 模拟获取UE项目信息
            return {
                "project_name": "MyGameProject",
                "engine_version": "5.1.1",
                "project_type": "CPP",
                "platforms": ["Windows", "PS5", "Xbox"],
                "build_target": "Development"
            }
        except Exception as e:
            logger.error(f"获取项目信息失败: {e}")
            return {}
    
    def _optimize_single_asset(self, asset: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """优化单个资产"""
        try:
            logger.info(f"处理资产: {asset['path']}")
            
            result = {
                "asset_path": asset['path'],
                "asset_type": asset['type'],
                "operations": [],
                "before_stats": {},
                "after_stats": {}
            }
            
            # 根据资产类型执行不同的优化操作
            if asset['type'] == "Texture2D":
                texture_result = self._optimize_texture(asset, params)
                result.update(texture_result)
                result["operations"].append("纹理压缩优化")
                
            elif asset['type'] == "StaticMesh":
                mesh_result = self._optimize_static_mesh(asset, params)
                result.update(mesh_result)
                result["operations"].append("网格LOD生成")
                
            elif asset['type'] == "Material":
                material_result = self._optimize_material(asset, params)
                result.update(material_result)
                result["operations"].append("材质实例化")
            
            logger.info(f"资产 {asset['path']} 处理完成")
            return result
            
        except Exception as e:
            logger.error(f"处理资产 {asset['path']} 失败: {e}")
            return {
                "asset_path": asset['path'],
                "status": "error",
                "error": str(e)
            }
    
    def _optimize_texture(self, texture_asset: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """优化纹理资产"""
        try:
            quality = params.get('texture_quality', 75)
            
            # 模拟纹理压缩操作
            original_size = texture_asset.get('size', '4096x4096')
            compressed_size = self._calculate_compressed_size(original_size, quality)
            
            return {
                "original_resolution": original_size,
                "compressed_resolution": compressed_size,
                "quality_setting": quality,
                "compression_ratio": self._calculate_compression_ratio(original_size, compressed_size)
            }
        except Exception as e:
            logger.warning(f"纹理优化失败: {e}")
            return {}
    
    def _optimize_static_mesh(self, mesh_asset: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """优化静态网格资产"""
        try:
            lod_count = 0
            
            if params.get('generate_lods', True):
                # 模拟LOD生成
                lod_count = 3  # 生成3个LOD级别
            
            collision_optimized = params.get('optimize_collision', False)
            
            return {
                "generated_lod_count": lod_count,
                "collision_optimized": collision_optimized,
                "vertex_count_reduction": 45  # 模拟顶点数减少百分比
            }
        except Exception as e:
            logger.warning(f"网格优化失败: {e}")
            return {}
    
    def _optimize_material(self, material_asset: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """优化材质资产"""
        try:
            instance_created = False
            
            if params.get('create_material_instances', True):
                # 模拟材质实例创建
                instance_created = True
            
            return {
                "instance_created": instance_created,
                "parameter_count": 12,  # 模拟参数数量
                "shader_complexity": "Medium"
            }
        except Exception as e:
            logger.warning(f"材质优化失败: {e}")
            return {}
    
    def _calculate_compressed_size(self, original_size: str, quality: int) -> str:
        """计算压缩后的尺寸"""
        # 简化的尺寸计算逻辑
        width, height = map(int, original_size.split('x'))
        scale_factor = quality / 100.0
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        return f"{new_width}x{new_height}"
    
    def _calculate_compression_ratio(self, original: str, compressed: str) -> float:
        """计算压缩比率"""
        orig_w, orig_h = map(int, original.split('x'))
        comp_w, comp_h = map(int, compressed.split('x'))
        orig_pixels = orig_w * orig_h
        comp_pixels = comp_w * comp_h
        return round((orig_pixels - comp_pixels) / orig_pixels * 100, 2)
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成处理摘要"""
        successful = [r for r in results if r.get('status') != 'error']
        
        summary = {
            "total_assets": len(results),
            "successful_assets": len(successful),
            "failed_assets": len(results) - len(successful),
            "texture_assets_processed": len([r for r in successful if r.get('asset_type') == 'Texture2D']),
            "mesh_assets_processed": len([r for r in successful if r.get('asset_type') == 'StaticMesh']),
            "material_assets_processed": len([r for r in successful if r.get('asset_type') == 'Material']),
            "average_compression_ratio": self._calculate_average_compression(successful)
        }
        
        return summary
    
    def _calculate_average_compression(self, results: List[Dict[str, Any]]) -> float:
        """计算平均压缩比率"""
        compression_ratios = [r.get('compression_ratio', 0) for r in results if 'compression_ratio' in r]
        if compression_ratios:
            return round(sum(compression_ratios) / len(compression_ratios), 2)
        return 0.0
    
    def _save_report(self, summary: Dict[str, Any]):
        """保存优化报告"""
        try:
            report_path = Path("ue_asset_optimization_report.json")
            
            report_data = {
                "timestamp": self._get_timestamp(),
                "summary": summary,
                "plugin_info": self.get_info()
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"优化报告已保存到: {report_path}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 独立运行测试
if __name__ == "__main__":
    # 创建插件实例
    optimizer = UEAssetOptimizer()
    
    # 测试执行（模拟模式）
    test_params = {
        "texture_quality": 75,
        "generate_lods": True,
        "create_material_instances": True,
        "compress_textures": True,
        "optimize_collision": True
    }
    
    print("Unreal Engine资产优化工具测试")
    print("=" * 50)
    
    # 显示插件信息
    info = optimizer.get_info()
    print(f"插件名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    print(f"支持的UE版本: {info['target_ue_version']}")
    print(f"项目类型: {info['project_type']}")
    print(f"版本范围: {info['min_version']} - {info['max_version']}")
    
    print("\n功能特性:")
    for capability in info['capabilities']:
        print(f"  • {capability}")
    
    # 测试参数验证
    print("\n参数验证测试:")
    validated = optimizer.validate_parameters(test_params)
    print(f"验证后参数: {validated}")
    
    # 模拟执行测试
    print("\n模拟执行测试:")
    mock_assets = [
        {"path": "/Game/Test/SM_TestMesh", "type": "StaticMesh"},
        {"path": "/Game/Test/T_TestTexture", "type": "Texture2D"}
    ]
    
    # 注意：实际的UE功能测试需要在UE编辑器环境中运行
    print("\n注意：完整的功能测试需要在UE编辑器环境中执行")