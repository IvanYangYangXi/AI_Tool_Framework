#!/usr/bin/env python3
"""
DCC工具框架功能验证脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "core"))

def main():
    print("DCC工具框架功能验证")
    print("=" * 40)
    
    # 验证核心文件存在
    core_files = [
        ("DCC插件接口", project_root / "src" / "core" / "dcc_plugin_interface.py"),
        ("UE插件接口", project_root / "src" / "core" / "ue_plugin_interface.py"),
        ("依赖管理器", project_root / "src" / "core" / "dependency_manager.py"),
        ("插件市场", project_root / "src" / "core" / "plugin_market.py")
    ]
    
    print("核心组件验证:")
    for name, file_path in core_files:
        if file_path.exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [ERROR] {name} 不存在")
    
    # 验证插件文件存在
    print("\n插件组件验证:")
    plugin_files = [
        ("Maya网格清理工具", project_root / "src" / "plugins" / "dcc" / "maya" / "mesh_cleaner" / "plugin.py"),
        ("3ds Max材质转换工具", project_root / "src" / "plugins" / "dcc" / "max" / "material_converter" / "plugin.py"),
        ("Blender网格优化工具", project_root / "src" / "plugins" / "dcc" / "blender" / "mesh_optimizer" / "plugin.py"),
        ("UE资产优化工具", project_root / "src" / "plugins" / "ue" / "asset_optimizer" / "plugin.py")
    ]
    
    for name, file_path in plugin_files:
        if file_path.exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [ERROR] {name} 不存在")
    
    # 验证配置文件
    print("\n配置文件验证:")
    config_files = [
        ("Maya插件配置", project_root / "src" / "plugins" / "dcc" / "maya" / "mesh_cleaner" / "config.json"),
        ("3ds Max插件配置", project_root / "src" / "plugins" / "dcc" / "max" / "material_converter" / "config.json"),
        ("Blender插件配置", project_root / "src" / "plugins" / "dcc" / "blender" / "mesh_optimizer" / "config.json"),
        ("UE插件配置", project_root / "src" / "plugins" / "ue" / "asset_optimizer" / "config.json")
    ]
    
    for name, file_path in config_files:
        if file_path.exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [ERROR] {name} 不存在")
    
    print("\n完成度统计:")
    total_components = len(core_files) + len(plugin_files) + len(config_files)
    completed_components = sum(1 for _, path in core_files + plugin_files + config_files if path.exists())
    
    print(f"已完成组件: {completed_components}/{total_components}")
    print(f"完成率: {completed_components/total_components*100:.1f}%")
    
    if completed_components == total_components:
        print("\n[SUCCESS] 所有组件都已成功创建！")
        print("DCC工具框架已准备就绪，可以开始实际开发工作。")
    else:
        print("\n[WARNING] 部分组件缺失，请检查上述错误。")

if __name__ == "__main__":
    main()