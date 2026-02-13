#!/usr/bin/env python3
"""
DCC工具框架实际使用演示
展示如何在日常工作中使用这个框架
"""

import sys
import os
from pathlib import Path

def demo_framework_usage():
    """演示框架的实际使用方法"""
    print("DCC工具框架实际使用演示")
    print("=" * 50)
    
    # 1. 直接使用现有插件
    print("\n1. 直接使用现有插件")
    print("-" * 30)
    
    # Maya插件使用示例
    print("Maya网格清理工具使用:")
    print("""
import sys
sys.path.append("src/plugins/dcc/maya/mesh_cleaner")
from plugin import MayaMeshCleaner

# 创建实例
cleaner = MayaMeshCleaner()

# 查看信息
info = cleaner.get_info()
print(f"插件: {info['name']} v{info['version']}")

# 执行清理（在Maya环境中）
# result = cleaner.execute(
#     tolerance=0.001,
#     delete_duplicates=True,
#     merge_vertices=True
# )
""")
    
    # Blender插件使用示例
    print("\nBlender网格优化工具使用:")
    print("""
import sys
sys.path.append("src/plugins/dcc/blender/mesh_optimizer")
from plugin import BlenderMeshOptimizer

optimizer = BlenderMeshOptimizer()
info = optimizer.get_info()
print(f"支持版本: {info['min_version']}-{info['max_version']}")
""")
    
    # 2. 依赖管理使用
    print("\n2. 依赖管理功能")
    print("-" * 30)
    print("""
from src.core.dependency_manager import PluginDependencyManager

# 创建管理器
manager = PluginDependencyManager("src/plugins")

# 分析依赖
dependencies = manager.analyze_dependencies()
print(f"分析了 {len(dependencies)} 个插件")

# 检测冲突
conflicts = manager.detect_conflicts()
if not conflicts:
    print("✓ 无依赖冲突")

# 获取安装顺序
install_order = manager.get_installation_order()
print("推荐安装顺序:", install_order[:3])
""")
    
    # 3. 插件市场使用
    print("\n3. 插件市场功能")
    print("-" * 30)
    print("""
from src.core.plugin_market import PluginMarketplace

# 创建市场实例
market = PluginMarketplace()

# 搜索插件
maya_plugins = market.search_plugins(query="maya")
print(f"找到 {len(maya_plugins)} 个Maya相关插件")

# 获取热门插件
popular = market.get_popular_plugins(3)
for plugin in popular:
    print(f"- {plugin.name} (下载: {plugin.download_count})")
""")
    
    # 4. 开发新插件
    print("\n4. 开发新插件模板")
    print("-" * 30)
    print("创建新插件的步骤:")
    print("1. 复制现有插件目录作为模板")
    print("2. 修改 config.json 配置文件")
    print("3. 在 plugin.py 中实现具体功能")
    print("4. 使用依赖管理器验证兼容性")
    print("5. 发布到插件市场")
    
    template_example = """
# 插件目录结构模板:
my_new_tool/
├── plugin.py          # 主要代码文件
├── config.json        # 配置文件
└── README.md          # 使用说明
"""
    print(template_example)

def demo_daily_workflow():
    """演示日常使用工作流"""
    print("\n" + "=" * 50)
    print("日常工作流程示例")
    print("=" * 50)
    
    workflow_steps = [
        "1. 项目启动时验证框架完整性",
        "2. 根据需求在插件市场搜索合适工具",
        "3. 安装并配置所需的插件",
        "4. 使用依赖管理器确保兼容性",
        "5. 在DCC软件中运行插件",
        "6. 查看生成的报告和日志"
    ]
    
    for step in workflow_steps:
        print(step)
    
    print("\n具体命令示例:")
    print("# 验证框架")
    print("python verification.py")
    print()
    print("# 查看可用插件")
    print("python -c \"from src.core.plugin_market import PluginMarketplace; m=PluginMarketplace(); print([p.name for p in m.get_popular_plugins(5)])\"")

def demo_troubleshooting():
    """演示常见问题解决"""
    print("\n" + "=" * 50)
    print("常见问题解决方法")
    print("=" * 50)
    
    problems = {
        "插件导入失败": "检查Python路径设置，确保src目录在sys.path中",
        "依赖冲突": "使用dependency_manager.py分析和解决冲突",
        "版本不兼容": "查看插件的min_version和max_version要求",
        "功能异常": "检查插件的日志输出和错误信息"
    }
    
    for problem, solution in problems.items():
        print(f"问题: {problem}")
        print(f"解决: {solution}")
        print()

def main():
    """主函数"""
    demo_framework_usage()
    demo_daily_workflow()
    demo_troubleshooting()
    
    print("\n" + "=" * 50)
    print("💡 实用建议")
    print("=" * 50)
    print("• 定期运行 verification.py 检查框架状态")
    print("• 参考现有插件学习开发模式")
    print("• 使用配置文件管理插件参数")
    print("• 查看README文档了解详细功能")
    print("• 通过插件市场获取最新工具")
    
    print("\n现在您可以开始使用DCC工具框架了！")

if __name__ == "__main__":
    main()