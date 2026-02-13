"""
Maya插件自动安装脚本
将DCC工具框架的插件自动安装到Maya中
"""

import os
import sys
import shutil
import json
from pathlib import Path
import maya.cmds as cmds
import maya.mel as mel

class MayaPluginInstaller:
    """Maya插件自动安装器"""
    
    def __init__(self, framework_path=None):
        self.framework_path = framework_path or self._find_framework_path()
        self.maya_scripts_dir = self._get_maya_scripts_dir()
        self.installed_plugins = []
        
    def _find_framework_path(self):
        """自动寻找框架路径"""
        # 尝试几种常见的路径
        possible_paths = [
            Path.cwd(),
            Path(__file__).parent.parent.parent,
            Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
        ]
        
        for path in possible_paths:
            if (path / "src" / "plugins" / "dcc" / "maya").exists():
                return str(path)
        return str(Path.cwd())
    
    def _get_maya_scripts_dir(self):
        """获取Maya脚本目录"""
        try:
            # 获取Maya的脚本路径
            scripts_dir = cmds.internalVar(userScriptDir=True)
            return scripts_dir.rstrip('/')
        except:
            # 备用方案：使用环境变量
            home = os.path.expanduser("~")
            maya_version = "2024"  # 默认版本
            return f"{home}/Documents/maya/{maya_version}/scripts"
    
    def install_plugin(self, plugin_name="mesh_cleaner", target_dir=None):
        """
        安装指定的插件
        
        Args:
            plugin_name: 插件名称
            target_dir: 目标安装目录
        """
        try:
            print(f"开始安装插件: {plugin_name}")
            
            # 确定源路径
            source_path = Path(self.framework_path) / "src" / "plugins" / "dcc" / "maya" / plugin_name
            if not source_path.exists():
                raise FileNotFoundError(f"插件源目录不存在: {source_path}")
            
            # 确定目标路径
            if target_dir is None:
                target_dir = Path(self.maya_scripts_dir) / "dcc_tools" / plugin_name
            else:
                target_dir = Path(target_dir)
            
            # 创建目标目录
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            copied_files = []
            for file_path in source_path.iterdir():
                if file_path.is_file():
                    target_file = target_dir / file_path.name
                    shutil.copy2(file_path, target_file)
                    copied_files.append(str(target_file))
                    print(f"已复制: {file_path.name}")
            
            # 创建安装记录
            install_record = {
                "plugin_name": plugin_name,
                "source_path": str(source_path),
                "installed_path": str(target_dir),
                "files": copied_files,
                "install_time": self._get_current_time(),
                "framework_version": self._get_framework_version()
            }
            
            # 保存安装记录
            record_file = target_dir / "install_record.json"
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(install_record, f, indent=2, ensure_ascii=False)
            
            self.installed_plugins.append(install_record)
            print(f"插件 {plugin_name} 安装成功!")
            print(f"安装位置: {target_dir}")
            
            return True
            
        except Exception as e:
            print(f"安装失败: {e}")
            return False
    
    def create_launcher_script(self):
        """创建启动器脚本"""
        launcher_content = f'''
# DCC工具框架启动器
# 自动生成于: {self._get_current_time()}

import sys
import os
from pathlib import Path

# 添加框架路径
framework_path = r"{self.framework_path}"
if framework_path not in sys.path:
    sys.path.append(framework_path)

# 添加核心模块路径
core_path = Path(framework_path) / "src" / "core"
if str(core_path) not in sys.path:
    sys.path.append(str(core_path))

def launch_dcc_framework():
    """启动DCC工具框架GUI"""
    try:
        from gui.main_window import DCCFrameworkGUI
        gui = DCCFrameworkGUI()
        gui.show()
        return gui
    except Exception as e:
        print(f"启动GUI失败: {{e}}")
        # 备用方案：显示简单的工具菜单
        show_simple_menu()

def show_simple_menu():
    """显示简化版工具菜单"""
    tools = {{
        "网格清理工具": lambda: run_mesh_cleaner(),
        "材质转换工具": lambda: run_material_converter(),
        "插件管理器": lambda: run_plugin_manager()
    }}
    
    print("DCC工具框架 - 可用工具:")
    for i, (name, func) in enumerate(tools.items(), 1):
        print(f"{{i}}. {{name}}")
    
    return tools

def run_mesh_cleaner():
    """运行网格清理工具"""
    try:
        # 添加插件路径
        plugin_path = Path("{self.framework_path}") / "src" / "plugins" / "dcc" / "maya" / "mesh_cleaner"
        if str(plugin_path) not in sys.path:
            sys.path.append(str(plugin_path))
        
        from plugin import MayaMeshCleaner
        cleaner = MayaMeshCleaner()
        return cleaner
    except Exception as e:
        print(f"加载网格清理工具失败: {{e}}")
        return None

def run_material_converter():
    """运行材质转换工具"""
    try:
        plugin_path = Path("{self.framework_path}") / "src" / "plugins" / "dcc" / "max" / "material_converter"
        if str(plugin_path) not in sys.path:
            sys.path.append(str(plugin_path))
        
        from plugin import MaxMaterialConverter
        converter = MaxMaterialConverter()
        return converter
    except Exception as e:
        print(f"加载材质转换工具失败: {{e}}")
        return None

def run_plugin_manager():
    """运行插件管理器"""
    try:
        from dependency_manager import PluginDependencyManager
        manager = PluginDependencyManager(
            str(Path("{self.framework_path}") / "src" / "plugins")
        )
        return manager
    except Exception as e:
        print(f"加载插件管理器失败: {{e}}")
        return None

# 自动启动GUI（如果可能）
if __name__ == "__main__":
    launch_dcc_framework()
'''

        # 保存启动器脚本
        launcher_path = Path(self.maya_scripts_dir) / "dcc_tools" / "launcher.py"
        launcher_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        print(f"启动器脚本已创建: {launcher_path}")
        return str(launcher_path)
    
    def create_shelf_button(self):
        """在Maya工具架创建按钮"""
        try:
            # 创建工具架标签页（如果不存在）
            if not cmds.shelfLayout('DCC_Tools', exists=True):
                cmds.shelfLayout('DCC_Tools', parent='ShelfLayout')
            
            # 创建主按钮
            cmds.shelfButton(
                parent='DCC_Tools',
                command=f'exec(open(r"{self.maya_scripts_dir}/dcc_tools/launcher.py").read())',
                label='DCC工具',
                annotation='启动DCC工具框架',
                imageOverlayLabel='DCC',
                style='iconAndTextHorizontal'
            )
            
            print("已在Maya工具架创建DCC工具按钮")
            return True
            
        except Exception as e:
            print(f"创建工具架按钮失败: {e}")
            return False
    
    def install_all_dcc_plugins(self):
        """安装所有DCC插件"""
        dcc_plugins_dir = Path(self.framework_path) / "src" / "plugins" / "dcc" / "maya"
        if not dcc_plugins_dir.exists():
            print("未找到DCC插件目录")
            return False
        
        success_count = 0
        for plugin_dir in dcc_plugins_dir.iterdir():
            if plugin_dir.is_dir():
                if self.install_plugin(plugin_dir.name):
                    success_count += 1
        
        print(f"成功安装 {success_count} 个插件")
        return success_count > 0
    
    def _get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_framework_version(self):
        """获取框架版本"""
        try:
            version_file = Path(self.framework_path) / "VERSION"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    return f.read().strip()
            return "1.0.0"
        except:
            return "1.0.0"
    
    def get_installation_summary(self):
        """获取安装摘要"""
        return {
            "framework_path": self.framework_path,
            "maya_scripts_dir": self.maya_scripts_dir,
            "installed_plugins": self.installed_plugins,
            "total_installed": len(self.installed_plugins)
        }

def main():
    """主安装函数"""
    print("=== DCC工具框架 Maya自动安装程序 ===")
    
    installer = MayaPluginInstaller()
    
    print(f"框架路径: {installer.framework_path}")
    print(f"Maya脚本目录: {installer.maya_scripts_dir}")
    
    # 安装网格清理插件
    if installer.install_plugin("mesh_cleaner"):
        print("✓ 网格清理插件安装成功")
    
    # 创建启动器
    launcher_path = installer.create_launcher_script()
    if launcher_path:
        print("✓ 启动器脚本创建成功")
    
    # 创建工具架按钮
    if installer.create_shelf_button():
        print("✓ Maya工具架按钮创建成功")
    
    # 显示安装摘要
    summary = installer.get_installation_summary()
    print(f"\n安装完成! 总共安装了 {summary['total_installed']} 个插件")
    print("现在可以在Maya中点击'DCC工具'按钮启动框架")

if __name__ == "__main__":
    main()