"""
DCC插件管理器打包脚本
将Python GUI应用打包为独立的exe程序
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
        return True
    except ImportError:
        print("✗ PyInstaller未安装")
        return False

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError:
        print("✗ PyInstaller安装失败")
        return False

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/gui/simple_artistic_manager.py'],
    pathex=[],
    binaries=[],
    datas=[('src/plugins', 'plugins'), ('src/core', 'core')],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'json',
        'pathlib',
        'datetime'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DCCPluginManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app_icon.ico'  # 如果有图标文件的话
)
'''
    
    spec_file = Path("plugin_manager.spec")
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ spec文件已创建: {spec_file}")
    return spec_file

def create_resources():
    """创建资源文件"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    # 创建简单的图标文件占位符（实际使用时需要真正的ico文件）
    icon_placeholder = resources_dir / "app_icon.ico"
    if not icon_placeholder.exists():
        # 创建一个简单的文本文件作为占位符
        with open(icon_placeholder, 'w') as f:
            f.write("Icon file placeholder")
        print("✓ 资源文件夹和图标占位符已创建")
    
    return resources_dir

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 使用spec文件构建
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean",  # 清理之前的构建
            "plugin_manager.spec"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 构建成功完成")
            return True
        else:
            print("✗ 构建失败")
            print("错误信息:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ 构建过程中出错: {e}")
        return False

def copy_additional_files():
    """复制额外需要的文件"""
    dist_dir = Path("dist")
    if not dist_dir.exists():
        dist_dir.mkdir()
    
    # 复制配置文件和文档
    files_to_copy = [
        "COMPLETE_USER_MANUAL.md",
        "HOW_TO_USE.md",
        "verification.py"
    ]
    
    for file_name in files_to_copy:
        source_file = Path(file_name)
        if source_file.exists():
            dest_file = dist_dir / file_name
            shutil.copy2(source_file, dest_file)
            print(f"✓ 已复制: {file_name}")
    
    # 创建启动批处理文件
    bat_content = '''@echo off
cd /d "%~dp0"
"DCCPluginManager.exe"
pause
'''
    
    bat_file = dist_dir / "启动插件管理器.bat"
    with open(bat_file, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("✓ 已创建启动批处理文件")

def create_distribution_package():
    """创建分发包"""
    dist_dir = Path("dist")
    package_name = "DCC_Plugin_Manager_v1.0"
    package_dir = Path(package_name)
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # 复制可执行文件和相关文件
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, package_dir / item.name)
    
    # 创建说明文档
    readme_content = '''DCC插件管理器 v1.0
==================

简介:
这是一个专为美术人员设计的DCC插件管理工具，支持Maya、Blender、3ds Max等软件的插件统一管理。

功能特点:
• 美术友好的图形界面
• 插件一键安装和管理
• 参数可视化配置
• 执行日志记录
• 支持定时任务设置

使用方法:
1. 双击"DCCPluginManager.exe"启动程序
2. 在左侧选择需要的插件
3. 在右侧配置参数
4. 点击"运行插件"按钮执行

系统要求:
• Windows 7及以上版本
• .NET Framework 4.0或更高版本

技术支持:
如有问题请联系开发团队

版本信息:
版本: 1.0.0
发布日期: 2024年2月
'''
    
    with open(package_dir / "README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ 分发包已创建: {package_name}")

def main():
    """主打包流程"""
    print("=== DCC插件管理器打包工具 ===\n")
    
    # 检查和安装PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("无法安装PyInstaller，打包终止")
            return False
    
    # 创建必要文件
    create_spec_file()
    create_resources()
    
    # 构建可执行文件
    if build_executable():
        # 后续处理
        copy_additional_files()
        create_distribution_package()
        print("\n🎉 打包完成！")
        print("可执行文件位于 dist/ 目录中")
        print("分发包位于 DCC_Plugin_Manager_v1.0/ 目录中")
        return True
    else:
        print("\n❌ 打包失败")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)