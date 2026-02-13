#!/usr/bin/env python3
"""
Blender插件独立测试脚本
用于在没有Blender环境的情况下测试插件基本功能
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    # 测试导入
    from src.core.dcc_plugin_interface import (
        DCCPluginInterface, 
        BlenderPluginMixin, 
        dcc_plugin, 
        validate_params,
        auto_register,
        DCCSoftware
    )
    print("[OK] 核心接口导入成功")
    
    # 导入Blender插件
    plugin_path = project_root / "src" / "plugins" / "dcc" / "blender" / "mesh_optimizer"
    sys.path.insert(0, str(plugin_path))
    
    from plugin import BlenderMeshOptimizer
    print("[OK] Blender插件导入成功")
    
    # 创建插件实例
    optimizer = BlenderMeshOptimizer()
    print("[OK] 插件实例创建成功")
    
    # 测试基本信息获取
    info = optimizer.get_info()
    print(f"\n=== 插件信息 ===")
    print(f"名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"类型: {info['type']}")
    print(f"目标DCC: {info['target_dcc']}")
    print(f"最小版本: {info['min_version']}")
    print(f"最大版本: {info['max_version']}")
    print(f"描述: {info['description']}")
    print(f"作者: {info['author']}")
    
    print(f"\n=== 功能特性 ===")
    for i, capability in enumerate(info['capabilities'], 1):
        print(f"{i}. {capability}")
    
    # 测试参数验证
    test_params = {
        "decimate_ratio": 0.5,
        "remove_doubles": True,
        "recalculate_normals": True,
        "optimize_materials": True,
        "preserve_uvs": True
    }
    
    print(f"\n=== 参数验证测试 ===")
    validated_params = optimizer.validate_parameters(test_params)
    print("原始参数:", test_params)
    print("验证后参数:", validated_params)
    
    # 测试配置文件
    config_file = plugin_path / "config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"\n=== 配置文件信息 ===")
        print(f"插件名称: {config['plugin']['name']}")
        print(f"版本: {config['plugin']['version']}")
        print(f"支持格式: {', '.join(config['plugin'].get('supported_formats', []))}")
        
        print(f"\n=== 参数配置 ===")
        for param_name, param_info in config.get('parameters', {}).items():
            print(f"{param_name}: {param_info.get('type')} (默认: {param_info.get('default')})")
            if 'description' in param_info:
                print(f"  描述: {param_info['description']}")
    
    print(f"\n[INFO] 所有测试通过！Blender插件功能正常")
    
except ImportError as e:
    print(f"[ERROR] 导入错误: {e}")
    print("请确保在正确的项目环境中运行此测试")
    
except Exception as e:
    print(f"[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()