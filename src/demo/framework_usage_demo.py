#!/usr/bin/env python3
"""
DCC工具框架实际使用演示
展示如何在实际项目中使用框架的各种功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "core"))

def demo_plugin_usage():
    """演示插件使用方法"""
    print("=== 插件使用演示 ===\n")
    
    # 1. 使用Maya网格清理插件
    print("1. Maya网格清理插件使用示例:")
    try:
        # 导入插件
        sys.path.insert(0, str(project_root / "src" / "plugins" / "dcc" / "maya" / "mesh_cleaner"))
        from plugin import MayaMeshCleaner
        
        # 创建插件实例
        maya_cleaner = MayaMeshCleaner()
        
        # 获取插件信息
        info = maya_cleaner.get_info()
        print(f"   插件名称: {info['name']}")
        print(f"   版本: {info['version']}")
        print(f"   描述: {info['description']}")
        
        # 验证参数示例
        test_params = {
            "tolerance": 0.001,
            "delete_duplicates": True,
            "merge_vertices": True
        }
        validated = maya_cleaner.validate_parameters(test_params)
        print(f"   参数验证: {validated}")
        
        print("   ✓ Maya插件基础功能正常\n")
        
    except Exception as e:
        print(f"   ✗ Maya插件演示失败: {e}\n")
    
    # 2. 使用Blender网格优化插件
    print("2. Blender网格优化插件使用示例:")
    try:
        # 导入插件
        sys.path.insert(0, str(project_root / "src" / "plugins" / "dcc" / "blender" / "mesh_optimizer"))
        from plugin import BlenderMeshOptimizer
        
        # 创建插件实例
        blender_optimizer = BlenderMeshOptimizer()
        
        # 获取插件信息
        info = blender_optimizer.get_info()
        print(f"   插件名称: {info['name']}")
        print(f"   支持版本: {info['min_version']} - {info['max_version']}")
        print(f"   功能特性: {', '.join(info['capabilities'][:3])}...")
        
        print("   ✓ Blender插件基础功能正常\n")
        
    except Exception as e:
        print(f"   ✗ Blender插件演示失败: {e}\n")
    
    # 3. 使用UE资产优化插件
    print("3. UE资产优化插件使用示例:")
    try:
        # 导入插件
        sys.path.insert(0, str(project_root / "src" / "plugins" / "ue" / "asset_optimizer"))
        from plugin import UEAssetOptimizer
        
        # 创建插件实例
        ue_optimizer = UEAssetOptimizer()
        
        # 获取插件信息
        info = ue_optimizer.get_info()
        print(f"   插件名称: {info['name']}")
        print(f"   UE版本支持: {info['target_ue_version']}")
        print(f"   项目类型: {info['project_type']}")
        
        print("   ✓ UE插件基础功能正常\n")
        
    except Exception as e:
        print(f"   ✗ UE插件演示失败: {e}\n")

def demo_dependency_management():
    """演示依赖管理功能"""
    print("=== 依赖管理演示 ===\n")
    
    try:
        from dependency_manager import PluginDependencyManager
        
        # 创建依赖管理器
        manager = PluginDependencyManager(str(project_root / "src" / "plugins"))
        
        # 分析依赖关系
        print("1. 依赖关系分析:")
        dependencies = manager.analyze_dependencies()
        print(f"   分析了 {len(dependencies)} 个插件的依赖关系")
        
        # 检测冲突
        print("\n2. 依赖冲突检测:")
        conflicts = manager.detect_conflicts()
        if conflicts:
            print(f"   发现 {len(conflicts)} 个潜在冲突:")
            for plugin_a, plugin_b, reason in conflicts:
                print(f"   - {plugin_a} 与 {plugin_b}: {reason}")
        else:
            print("   ✓ 未发现依赖冲突")
        
        # 获取安装顺序
        print("\n3. 推荐安装顺序:")
        install_order = manager.get_installation_order()
        for i, plugin_name in enumerate(install_order[:5], 1):  # 显示前5个
            print(f"   {i}. {plugin_name}")
        if len(install_order) > 5:
            print(f"   ... 还有 {len(install_order) - 5} 个插件")
        
        print("\n   ✓ 依赖管理功能正常\n")
        
    except Exception as e:
        print(f"   ✗ 依赖管理演示失败: {e}\n")

def demo_plugin_market():
    """演示插件市场功能"""
    print("=== 插件市场演示 ===\n")
    
    try:
        from plugin_market import PluginMarketplace
        
        # 创建市场实例
        marketplace = PluginMarketplace()
        
        # 获取市场统计
        print("1. 市场统计信息:")
        stats = marketplace.get_statistics()
        print(f"   总插件数: {stats['total_plugins']}")
        print(f"   总下载量: {stats['total_downloads']}")
        print(f"   平均评分: {stats['average_rating']}")
        print(f"   免费插件: {stats['free_plugins']} 个")
        
        # 搜索功能演示
        print("\n2. 插件搜索演示:")
        
        # 按评分搜索
        print("   高评分插件:")
        top_rated = marketplace.search_plugins(sort_by="rating")[:3]
        for plugin in top_rated:
            print(f"   - {plugin.name} (评分: {plugin.rating})")
        
        # 按下载量搜索
        print("\n   热门插件:")
        popular = marketplace.get_popular_plugins(3)
        for plugin in popular:
            print(f"   - {plugin.name} (下载: {plugin.download_count})")
        
        # 关键词搜索
        print("\n   搜索'Maya'相关插件:")
        maya_plugins = marketplace.search_plugins(query="maya")
        for plugin in maya_plugins:
            print(f"   - {plugin.name}")
        
        print("\n   ✓ 插件市场功能正常\n")
        
    except Exception as e:
        print(f"   ✗ 插件市场演示失败: {e}\n")

def demo_creating_new_plugin():
    """演示如何创建新插件"""
    print("=== 新插件创建演示 ===\n")
    
    print("创建新插件的基本步骤:")
    print("1. 选择目标平台 (Maya/Max/Blender/UE)")
    print("2. 基于相应标准接口创建插件类")
    print("3. 实现核心功能方法")
    print("4. 编写配置文件")
    print("5. 添加使用文档")
    print("6. 通过依赖管理器验证")
    print("7. 发布到插件市场")
    
    print("\n示例插件结构:")
    print("""
src/plugins/dcc/maya/my_new_tool/
├── plugin.py          # 主插件代码
├── config.json        # 配置文件
└── README.md          # 使用文档
    """)
    
    print("   ✓ 新插件创建指南完成\n")

def main():
    """主演示函数"""
    print("DCC工具框架实际使用演示")
    print("=" * 50)
    print("当前工作目录:", project_root)
    print()
    
    # 执行各项演示
    demo_plugin_usage()
    demo_dependency_management() 
    demo_plugin_market()
    demo_creating_new_plugin()
    
    # 总结
    print("=" * 50)
    print("演示完成！")
    print("\n现在您可以:")
    print("1. 直接使用现有的插件工具")
    print("2. 基于框架标准开发新插件")
    print("3. 通过插件市场管理和分发工具")
    print("4. 利用依赖管理系统确保兼容性")
    
    print("\n📚 建议下一步:")
    print("- 查看各插件目录下的README.md了解详细使用方法")
    print("- 参考现有插件代码学习开发模式")
    print("- 使用verification.py定期验证框架完整性")

if __name__ == "__main__":
    main()