#!/usr/bin/env python3
"""
DCC工具框架综合启动器
整合所有功能模块，提供一站式使用体验
"""

import sys
import os
from pathlib import Path
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "core"))
sys.path.insert(0, str(project_root / "src" / "gui"))

def show_main_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🎮 DCC工具框架综合管理平台")
    print("="*60)
    print("\n请选择要执行的操作:")
    print("1. 启动增强版图形界面")
    print("2. 使用命令行界面")
    print("3. 管理脚本和插件")
    print("4. 配置用户设置")
    print("5. 验证框架完整性")
    print("6. 查看系统信息")
    print("7. 退出程序")
    print()

def launch_enhanced_gui():
    """启动增强版GUI"""
    print("正在启动增强版图形界面...")
    try:
        from enhanced_gui import EnhancedDCCGUI
        app = EnhancedDCCGUI()
        app.show()
    except ImportError:
        print("❌ 无法导入GUI模块，请检查依赖")
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")

def launch_command_line_interface():
    """启动命令行界面"""
    print("正在启动命令行界面...")
    try:
        from simple_launcher import main as cli_main
        cli_main()
    except ImportError:
        print("❌ 无法导入命令行模块")
    except Exception as e:
        print(f"❌ 命令行界面启动失败: {e}")

def manage_scripts():
    """脚本管理功能"""
    print("\n=== 脚本管理 ===")
    try:
        from script_manager import ScriptManager
        manager = ScriptManager(str(project_root))
        
        while True:
            print("\n脚本管理选项:")
            print("1. 列出所有脚本")
            print("2. 部署脚本")
            print("3. 打包脚本")
            print("4. 查看部署状态")
            print("5. 返回主菜单")
            
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                scripts = manager.list_scripts()
                print(f"\n找到 {len(scripts)} 个脚本:")
                for i, script in enumerate(scripts, 1):
                    print(f"   {i}. {script['name']} ({script['software']}) v{script['version']}")
            
            elif choice == '2':
                scripts = manager.list_scripts()
                if scripts:
                    print("\n可用脚本:")
                    for i, script in enumerate(scripts, 1):
                        print(f"   {i}. {script['name']}")
                    
                    try:
                        idx = int(input("选择要部署的脚本编号: ")) - 1
                        if 0 <= idx < len(scripts):
                            result = manager.deploy_script(scripts[idx]['id'])
                            if result['success']:
                                print(f"✓ {result['message']}")
                            else:
                                print(f"✗ {result['error']}")
                    except (ValueError, IndexError):
                        print("无效的选择")
            
            elif choice == '3':
                scripts = manager.list_scripts()
                if scripts:
                    print("\n可用脚本:")
                    for i, script in enumerate(scripts, 1):
                        print(f"   {i}. {script['name']}")
                    
                    try:
                        idx = int(input("选择要打包的脚本编号: ")) - 1
                        if 0 <= idx < len(scripts):
                            result = manager.package_script(scripts[idx]['id'])
                            if result['success']:
                                print(f"✓ {result['message']}")
                            else:
                                print(f"✗ {result['error']}")
                    except (ValueError, IndexError):
                        print("无效的选择")
            
            elif choice == '4':
                scripts = manager.list_scripts()
                for script in scripts:
                    status = manager.get_deployment_status(script['id'])
                    deployed = "✓ 已部署" if status.get('is_deployed') else "○ 未部署"
                    print(f"   {script['name']}: {deployed}")
            
            elif choice == '5':
                break
            
            else:
                print("无效选择，请输入1-5")
                
    except ImportError:
        print("❌ 无法导入脚本管理模块")
    except Exception as e:
        print(f"❌ 脚本管理出错: {e}")

def configure_user_settings():
    """用户配置管理"""
    print("\n=== 用户配置管理 ===")
    try:
        from user_config import UserConfiguration
        config = UserConfiguration()
        
        while True:
            print("\n配置管理选项:")
            print("1. 查看当前配置")
            print("2. 修改偏好设置")
            print("3. 管理工作区")
            print("4. 导出配置")
            print("5. 返回主菜单")
            
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                info = config.get_system_info()
                print(f"\n用户ID: {info['user_id']}")
                print(f"平台: {info['platform']}")
                print(f"主题设置: {config.get_preference('theme')}")
                print(f"窗口大小: {config.get_workspace_setting('window_size')}")
                print(f"收藏插件数: {info['total_favorites']}")
            
            elif choice == '2':
                print("\n偏好设置选项:")
                print("1. 主题 (当前: {})".format(config.get_preference('theme')))
                print("2. 自动保存 (当前: {})".format(config.get_preference('auto_save')))
                print("3. 显示工具提示 (当前: {})".format(config.get_preference('show_tooltips')))
                
                pref_choice = input("选择要修改的设置 (1-3): ").strip()
                if pref_choice == '1':
                    theme = input("输入主题 (auto/light/dark): ").strip()
                    if theme in ['auto', 'light', 'dark']:
                        config.set_preference('theme', theme)
                        print(f"✓ 主题已设置为: {theme}")
                elif pref_choice == '2':
                    auto_save = input("启用自动保存? (y/n): ").strip().lower() == 'y'
                    config.set_preference('auto_save', auto_save)
                    print(f"✓ 自动保存已{'启用' if auto_save else '禁用'}")
                elif pref_choice == '3':
                    show_tips = input("显示工具提示? (y/n): ").strip().lower() == 'y'
                    config.set_preference('show_tooltips', show_tips)
                    print(f"✓ 工具提示已{'启用' if show_tips else '禁用'}")
            
            elif choice == '3':
                print("\n工作区管理:")
                print("1. 添加收藏插件")
                print("2. 查看最近项目")
                print("3. 修改窗口大小")
                
                ws_choice = input("选择操作 (1-3): ").strip()
                if ws_choice == '1':
                    plugin_id = input("输入插件ID: ").strip()
                    if plugin_id:
                        config.add_favorite_plugin(plugin_id)
                        print(f"✓ 已添加收藏: {plugin_id}")
                elif ws_choice == '3':
                    try:
                        width = int(input("输入窗口宽度: "))
                        height = int(input("输入窗口高度: "))
                        config.set_workspace_setting('window_size', [width, height])
                        print(f"✓ 窗口大小已更新为: {width}x{height}")
                    except ValueError:
                        print("❌ 请输入有效的数字")
            
            elif choice == '4':
                result = config.export_configuration()
                if result['success']:
                    print(f"✓ {result['message']}")
                else:
                    print(f"✗ {result['error']}")
            
            elif choice == '5':
                break
            
            else:
                print("无效选择，请输入1-5")
                
    except ImportError:
        print("❌ 无法导入用户配置模块")
    except Exception as e:
        print(f"❌ 配置管理出错: {e}")

def verify_framework():
    """验证框架完整性"""
    print("\n=== 框架完整性验证 ===")
    try:
        # 运行验证脚本
        import subprocess
        result = subprocess.run([sys.executable, str(project_root / "verification.py")], 
                              capture_output=True, text=True, cwd=str(project_root))
        
        if result.returncode == 0:
            print("✓ 框架验证通过")
            print(result.stdout)
        else:
            print("✗ 框架验证失败")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")

def show_system_info():
    """显示系统信息"""
    print("\n=== 系统信息 ===")
    try:
        import platform
        from user_config import UserConfiguration
        
        config = UserConfiguration()
        info = config.get_system_info()
        
        print(f"用户ID: {info['user_id']}")
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"Python版本: {platform.python_version()}")
        print(f"框架路径: {project_root}")
        print(f"配置文件: {info['config_path']}")
        print(f"最后更新: {info['last_updated']}")
        print(f"收藏插件: {info['total_favorites']} 个")
        print(f"最近项目: {info['recent_projects_count']} 个")
        
        # 显示可用插件数量
        try:
            from script_manager import ScriptManager
            manager = ScriptManager(str(project_root))
            scripts = manager.list_scripts()
            print(f"可用插件: {len(scripts)} 个")
        except:
            pass
            
    except Exception as e:
        print(f"❌ 获取系统信息失败: {e}")

def main():
    """主程序入口"""
    print("DCC工具框架综合管理平台")
    print(f"项目路径: {project_root}")
    
    while True:
        try:
            show_main_menu()
            choice = input("请输入选择 (1-7): ").strip()
            
            if choice == '1':
                launch_enhanced_gui()
            elif choice == '2':
                launch_command_line_interface()
            elif choice == '3':
                manage_scripts()
            elif choice == '4':
                configure_user_settings()
            elif choice == '5':
                verify_framework()
            elif choice == '6':
                show_system_info()
            elif choice == '7':
                print("\n感谢使用DCC工具框架！再见！👋")
                break
            else:
                print("❌ 无效选择，请输入1-7")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    main()