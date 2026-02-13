"""
DCC工具和UE引擎工具管理框架主入口
"""

import sys
import os
import logging
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core import PluginManager, DynamicLoader, ConfigManager, PermissionSystem
from src.core.permission_system import ResourceType, PermissionLevel
from src.ai_nlp import AIToolGenerator

def setup_logging():
    """设置日志配置"""
    # 处理Windows中文编码问题
    import locale
    try:
        # 尝试设置为UTF-8编码
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('framework.log', encoding='utf-8')
        ]
    )

def demo_basic_usage():
    """演示基本使用"""
    print("=" * 50)
    print("DCC工具和UE引擎工具管理框架演示")
    print("=" * 50)
    
    # 初始化各个组件
    print("\n1. 初始化框架组件...")
    
    # 插件管理器
    plugin_manager = PluginManager([
        './src/plugins/dcc',
        './src/plugins/ue_engine'
    ])
    
    # 动态加载器
    dynamic_loader = DynamicLoader(sandbox_enabled=True)
    
    # 配置管理器
    config_manager = ConfigManager(['./configs'])
    
    # 权限系统
    permission_system = PermissionSystem()
    
    print("[OK] 框架组件初始化完成")
    
    # 用户认证
    print("\n2. 用户认证...")
    token = permission_system.authenticate_user("admin")
    if token:
        print("[OK] 管理员认证成功")
        user_payload = permission_system.verify_token(token)
        print(f"  用户信息: {user_payload}")
    else:
        print("[ERROR] 认证失败")
        return
    
    # 权限检查
    print("\n3. 权限检查...")
    has_plugin_permission = permission_system.check_permission(
        "admin", 
        ResourceType.PLUGIN, 
        PermissionLevel.EXECUTE
    )
    
    has_config_permission = permission_system.check_permission(
        "admin",
        ResourceType.CONFIG,
        PermissionLevel.WRITE
    )
    
    print(f"  插件执行权限: {'[OK]' if has_plugin_permission else '[ERROR]'}")
    print(f"  配置写入权限: {'[OK]' if has_config_permission else '[ERROR]'}")
    
    # 发现插件
    print("\n4. 发现插件...")
    discovered_plugins = plugin_manager.discover_plugins()
    print(f"  发现 {len(discovered_plugins)} 个插件:")
    for plugin in discovered_plugins:
        print(f"    - {plugin.name} v{plugin.version} ({plugin.plugin_type.value})")
    
    # 加载并执行插件
    print("\n5. 加载并执行插件...")
    for plugin_info in discovered_plugins:
        if permission_system.check_permission(
            "admin",
            ResourceType.PLUGIN,
            PermissionLevel.EXECUTE
        ):
            print(f"\n  执行插件: {plugin_info.name}")
            
            # 加载插件
            if plugin_manager.load_plugin(plugin_info.name):
                plugin_module = plugin_manager.get_plugin(plugin_info.name)
                
                if plugin_module and hasattr(plugin_module, 'execute'):
                    try:
                        # 安全执行插件
                        result = dynamic_loader.execute_function_safely(
                            plugin_module.execute,
                            output_path=f"./output/{plugin_info.name.lower()}_result.txt",
                            _timeout=30
                        )
                        print(f"    执行结果: {result}")
                    except Exception as e:
                        print(f"    执行失败: {e}")
                else:
                    print(f"    插件缺少execute函数")
            else:
                print(f"    插件加载失败")
        else:
            print(f"  权限不足，跳过插件: {plugin_info.name}")
    
    # 展示用户权限
    print("\n6. 用户权限概览...")
    user_permissions = permission_system.get_user_permissions("admin")
    print("  管理员权限:")
    for resource_type, level in user_permissions.items():
        print(f"    {resource_type.value}: {level.value}")
    
    # 显示审计日志
    print("\n7. 审计日志...")
    audit_logs = permission_system.get_audit_log(limit=5)
    for log in audit_logs:
        timestamp = log['timestamp']
        event_type = log['event_type']
        username = log['username']
        message = log['message']
        print(f"  [{timestamp:.0f}] {event_type} - {username}: {message}")
    
    print("\n" + "=" * 50)
    print("基础功能演示完成!")
    print("=" * 50)

def demo_ai_tool_generation():
    """演示AI工具生成功能"""
    print("\n" + "=" * 50)
    print("AI驱动工具生成演示")
    print("=" * 50)
    
    print("\n1. 初始化AI工具生成器...")
    # 使用模拟模式避免API调用
    ai_generator = AIToolGenerator(model_provider="openai")
    print("[OK] AI工具生成器初始化完成")
    
    print("\n2. 生成示例工具...")
    
    # 生成一个简单的工具
    description = "创建一个文件批量重命名工具，支持添加前缀、后缀，替换特定字符"
    
    result = ai_generator.generate_tool_from_description(
        description,
        output_dir="./generated_tools"
    )
    
    print(f"生成结果: {'[OK] 成功' if result.success else '[ERROR] 失败'}")
    
    if result.success:
        print(f"  工具名称: {result.tool_name}")
        print(f"  生成文件: {len(result.generated_files)} 个")
        print(f"  配置文件: {result.config_file}")
        print("\n  生成的文件:")
        for file_path in result.generated_files:
            print(f"    - {file_path}")
        
        print("\n  执行说明预览:")
        instructions_preview = result.execution_instructions.split('\n')[:8]
        for line in instructions_preview:
            if line.strip():
                print(f"    {line}")
        if len(result.execution_instructions.split('\n')) > 8:
            print("    ...")
    
    print("\n" + "=" * 50)
    print("AI工具生成功能演示完成!")
    print("=" * 50)

def main():
    """主函数"""
    setup_logging()
    
    try:
        # 运行基础功能演示
        demo_basic_usage()
        
        # 运行AI功能演示
        demo_ai_tool_generation()
        
        print("\n所有演示完成!")
        print("\n生成的AI工具可在 ./generated_tools/ 目录中找到")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        logging.exception("程序异常")

if __name__ == "__main__":
    main()