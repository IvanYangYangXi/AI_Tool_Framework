"""
DCC工具框架一键安装脚本
为DCC艺术家提供简单易用的安装体验
"""

import os
import sys
import subprocess
from pathlib import Path
import json

def check_maya_installed():
    """检查Maya是否已安装"""
    try:
        import maya.cmds as cmds
        print("✓ 检测到Maya环境")
        return True
    except ImportError:
        print("⚠ 未检测到Maya环境")
        return False

def install_framework():
    """安装框架到Maya"""
    print("=== DCC工具框架一键安装 ===\n")
    
    # 获取当前目录
    current_dir = Path.cwd()
    print(f"当前目录: {current_dir}")
    
    # 检查框架结构
    required_paths = [
        "src/core",
        "src/plugins/dcc/maya",
        "src/plugins/dcc/max", 
        "src/plugins/dcc/blender",
        "src/plugins/ue"
    ]
    
    print("检查框架结构...")
    missing_paths = []
    for path in required_paths:
        if not (current_dir / path).exists():
            missing_paths.append(path)
    
    if missing_paths:
        print("框架结构不完整，缺少以下目录:")
        for path in missing_paths:
            print(f"  - {path}")
        return False
    
    print("框架结构完整")
    
    # 检查Maya环境
    maya_available = check_maya_installed()
    
    if maya_available:
        # 在Maya环境中运行安装
        print("\n在Maya环境中执行安装...")
        run_maya_installation(current_dir)
    else:
        # 创建桌面快捷方式和说明
        print("\n创建使用说明...")
        create_user_guide(current_dir)
    
    return True

def run_maya_installation(framework_path):
    """在Maya环境中运行安装"""
    try:
        # 导入安装器
        installer_path = framework_path / "installers" / "maya_installer.py"
        if installer_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("maya_installer", installer_path)
            installer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(installer_module)
            
            # 运行安装
            installer = installer_module.MayaPluginInstaller(str(framework_path))
            installer.install_all_dcc_plugins()
            installer.create_launcher_script()
            installer.create_shelf_button()
            
            print("✓ Maya插件安装完成")
            print("✓ 启动器脚本已创建")
            print("✓ 工具架按钮已添加")
            
        else:
            print("❌ 未找到Maya安装器")
            
    except Exception as e:
        print(f"❌ Maya安装失败: {e}")

def create_user_guide(framework_path):
    """创建用户使用指南"""
    guide_content = f"""
DCC工具框架使用指南
==================

框架已成功部署到: {framework_path}

使用方法:

1. Maya中使用:
   - 打开Maya
   - 在脚本编辑器中运行以下代码:
   
   import sys
   sys.path.append(r"{framework_path}")
   from installers.maya_installer import MayaPluginInstaller
   installer = MayaPluginInstaller(r"{framework_path}")
   installer.install_all_dcc_plugins()

2. 图形界面使用:
   - 运行: python "{framework_path}/src/gui/main_window.py"
   - 或者双击桌面快捷方式(如果已创建)

3. 直接调用插件:
   import sys
   sys.path.append(r"{framework_path}/src/plugins/dcc/maya/mesh_cleaner")
   from plugin import MayaMeshCleaner
   cleaner = MayaMeshCleaner()

支持的工具:
- Maya网格清理工具
- 3ds Max材质转换工具
- Blender网格优化工具
- UE资产优化工具

技术要求:
- Python 3.7+
- 支持的DCC软件版本请查看各插件的README文件

如需帮助，请查看各插件目录下的README.md文件。
"""
    
    # 保存指南
    guide_path = framework_path / "USER_GUIDE.txt"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✓ 用户指南已创建: {guide_path}")
    
    # 创建桌面快捷方式(Windows)
    if sys.platform == "win32":
        create_desktop_shortcut(framework_path)

def create_desktop_shortcut(framework_path):
    """创建桌面快捷方式"""
    try:
        import win32com.client
        
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "DCC工具框架.lnk"
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{framework_path}/src/gui/main_window.py"'
        shortcut.WorkingDirectory = str(framework_path)
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        print(f"✓ 桌面快捷方式已创建: {shortcut_path}")
        
    except ImportError:
        print("⚠ 未安装pywin32，无法创建桌面快捷方式")
    except Exception as e:
        print(f"⚠ 创建桌面快捷方式失败: {e}")

def create_startup_script(framework_path):
    """创建启动脚本"""
    startup_content = f'''#!/usr/bin/env python3
"""
DCC工具框架启动脚本
双击此文件即可启动图形界面
"""

import sys
import os
from pathlib import Path

# 添加框架路径
framework_path = Path(r"{framework_path}")
sys.path.insert(0, str(framework_path))
sys.path.insert(0, str(framework_path / "src" / "core"))

try:
    # 启动GUI
    from gui.main_window import DCCFrameworkGUI
    gui = DCCFrameworkGUI()
    gui.show()
    
except Exception as e:
    print(f"启动失败: {{e}}")
    
    # 备用方案：显示简单的命令行界面
    print("\\n=== DCC工具框架 ===")
    print("可用的工具:")
    
    plugins_dir = framework_path / "src" / "plugins"
    for plugin_type in plugins_dir.iterdir():
        if plugin_type.is_dir():
            print(f"\\n{{plugin_type.name.upper()}}工具:")
            for software_dir in plugin_type.iterdir():
                if software_dir.is_dir():
                    for plugin_dir in software_dir.iterdir():
                        if plugin_dir.is_dir():
                            config_file = plugin_dir / "config.json"
                            if config_file.exists():
                                try:
                                    import json
                                    with open(config_file, 'r', encoding='utf-8') as f:
                                        config = json.load(f)
                                        print(f"  - {{config['plugin']['name']}}")
                                except:
                                    print(f"  - {{plugin_dir.name}}")
    
    input("\\n按回车键退出...")
'''

    startup_path = framework_path / "launch_framework.py"
    with open(startup_path, 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    print(f"✓ 启动脚本已创建: {startup_path}")

def main():
    """主函数"""
    try:
        success = install_framework()
        
        if success:
            framework_path = Path.cwd()
            create_startup_script(framework_path)
            print(f"\n🎉 安装完成!")
            print(f"框架位置: {framework_path}")
            print(f"使用方法: 双击 launch_framework.py 启动图形界面")
        else:
            print("\n❌ 安装失败，请检查错误信息")
            
    except KeyboardInterrupt:
        print("\n\n安装被用户取消")
    except Exception as e:
        print(f"\n❌ 安装过程中出现错误: {e}")

if __name__ == "__main__":
    main()