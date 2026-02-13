"""
轻量级DCC工具管理器打包脚本
只打包GUI前端，不包含后端脚本代码
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil

def check_requirements():
    """检查打包所需条件"""
    print("=== 轻量级DCC工具管理器打包工具 ===\n")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("✗ PyInstaller未安装")
        print("正在安装PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller安装成功")
        except subprocess.CalledProcessError:
            print("✗ PyInstaller安装失败")
            return False
    
    # 检查Git仓库
    git_path = Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
    if git_path.exists() and (git_path / ".git").exists():
        print("✓ Git仓库路径确认")
    else:
        print("✗ 未找到有效的Git仓库")
        return False
    
    return True

def create_lightweight_spec():
    """创建轻量级spec文件（不包含脚本代码）"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/gui/lightweight_manager.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 只包含必要的配置文件，不包含脚本代码
        ('src/plugins/**/config.json', 'plugin_configs'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'subprocess',
        'threading',
        'json',
        'pathlib',
        'datetime',
        'tempfile'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除大型库以减小exe体积
        'numpy',
        'scipy',
        'matplotlib',
        'pandas',
        'PIL',
        'OpenGL'
    ],
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
    name='DCC_Tool_Manager_Lite',
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
)
'''
    
    spec_file = Path("lightweight_manager.spec")
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ 轻量级spec文件已创建: {spec_file}")
    return spec_file

def build_lightweight_exe():
    """构建轻量级exe程序"""
    print("开始构建轻量级可执行文件...")
    
    try:
        # 清理之前的构建
        if Path("build").exists():
            shutil.rmtree("build")
        if Path("dist").exists():
            shutil.rmtree("dist")
        
        # 使用spec文件构建
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean",
            "lightweight_manager.spec"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 轻量级构建成功完成")
            return True
        else:
            print("✗ 构建失败")
            print("错误信息:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ 构建过程中出错: {e}")
        return False

def create_distribution_package():
    """创建分发包"""
    print("正在创建分发包...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("✗ 未找到构建输出目录")
        return False
    
    package_name = "DCC_Tool_Manager_Lite_v1.0"
    package_dir = Path(package_name)
    
    # 清理旧包
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # 复制exe文件
    exe_source = dist_dir / "DCC_Tool_Manager_Lite.exe"
    if exe_source.exists():
        shutil.copy2(exe_source, package_dir / "DCC_Tool_Manager.exe")
        print("✓ 已复制主程序")
    else:
        print("✗ 未找到主程序exe文件")
        return False
    
    # 创建配置文件
    create_config_files(package_dir)
    
    # 创建启动脚本
    create_launch_scripts(package_dir)
    
    # 创建说明文档
    create_documentation(package_dir)
    
    print(f"✓ 分发包已创建: {package_name}")
    return True

def create_config_files(package_dir):
    """创建必要的配置文件"""
    # Git仓库配置
    config_content = {
        "git_repository": "C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV",
        "auto_check_updates": True,
        "default_dcc": "Maya",
        "ui_theme": "light"
    }
    
    config_file = package_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(config_content, f, indent=2, ensure_ascii=False)
    
    print("✓ 配置文件已创建")

def create_launch_scripts(package_dir):
    """创建启动脚本"""
    # 批处理启动脚本
    bat_content = '''@echo off
cd /d "%~dp0"
echo 正在启动DCC工具管理器...
"DCC_Tool_Manager.exe"
if errorlevel 1 (
    echo 程序启动失败，请检查系统环境
    pause
)
'''
    
    bat_file = package_dir / "启动DCC工具管理器.bat"
    with open(bat_file, 'w', encoding='gbk') as f:  # 使用gbk编码确保中文正常显示
        f.write(bat_content)
    
    # PowerShell启动脚本
    ps_content = '''# DCC工具管理器启动脚本
Write-Host "正在启动DCC工具管理器..." -ForegroundColor Green
Start-Process ".\\DCC_Tool_Manager.exe"
'''
    
    ps_file = package_dir / "启动DCC工具管理器.ps1"
    with open(ps_file, 'w', encoding='utf-8') as f:
        f.write(ps_content)
    
    print("✓ 启动脚本已创建")

def create_documentation(package_dir):
    """创建说明文档"""
    readme_content = '''DCC工具管理器 精简版 v1.0
============================

简介:
这是一个轻量级的DCC工具管理前端程序，通过Git管理后端脚本代码，
为美术人员提供友好的图形界面来使用各种DCC工具。

主要功能:
• Git版本管理 - 自动更新和同步工具代码
• DCC软件连接 - 支持Maya、3ds Max、Blender、Unreal Engine
• 可视化参数配置 - 直观的工具参数设置界面
• 脚本生成 - 生成可在DCC中直接运行的脚本文件
• 日志记录 - 完整的操作过程记录

使用方法:
1. 双击"启动DCC工具管理器.bat"启动程序
2. 程序会自动检查Git更新（如有需要请更新）
3. 选择要使用的DCC软件并连接
4. 在工具列表中选择需要的工具
5. 配置相关参数
6. 选择执行方式：
   - "在DCC中执行"：直接发送到已连接的DCC软件
   - "生成脚本文件"：生成脚本文件供手动执行

系统要求:
• Windows 7及以上版本
• 网络连接（用于Git更新）
• 对应的DCC软件（如Maya、3ds Max等）

注意事项:
• 首次使用需要确保Git仓库路径正确
• 程序不会包含实际的工具脚本代码
• 所有工具代码通过Git仓库进行管理
• 建议定期更新以获取最新功能

技术支持:
如有问题请联系开发团队

版本信息:
版本: 1.0.0
发布日期: 2024年2月
'''
    
    with open(package_dir / "README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建快速开始指南
    quick_start = '''快速开始指南
============

第一步：启动程序
双击"启动DCC工具管理器.bat"文件

第二步：检查更新
如果提示有新版本，请点击"更新到最新版本"

第三步：连接DCC软件
1. 在下拉菜单中选择你的DCC软件
2. 点击"连接"按钮

第四步：使用工具
1. 在左侧选择需要的工具类别
2. 选择具体工具
3. 配置参数
4. 点击执行按钮

就这么简单！
'''
    
    with open(package_dir / "快速开始.txt", 'w', encoding='utf-8') as f:
        f.write(quick_start)
    
    print("✓ 文档文件已创建")

def main():
    """主打包流程"""
    if not check_requirements():
        print("\n❌ 环境检查失败，打包终止")
        return False
    
    # 创建spec文件
    spec_file = create_lightweight_spec()
    if not spec_file:
        print("\n❌ 创建spec文件失败")
        return False
    
    # 构建exe
    if not build_lightweight_exe():
        print("\n❌ 构建exe文件失败")
        return False
    
    # 创建分发包
    if not create_distribution_package():
        print("\n❌ 创建分发包失败")
        return False
    
    print("\n🎉 轻量级打包完成！")
    print("分发包位于:", Path("DCC_Tool_Manager_Lite_v1.0").absolute())
    print("主要特点:")
    print("• 文件体积小（仅包含前端界面）")
    print("• 通过Git管理后端脚本")
    print("• 支持自动更新检查")
    print("• 美术人员友好界面")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)