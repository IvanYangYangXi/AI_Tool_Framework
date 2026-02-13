"""
DCC工具框架简易启动器
为DCC艺术家提供最简单的使用方式
"""

import sys
import os
from pathlib import Path

def main():
    print("DCC工具框架启动器")
    print("=" * 30)
    
    # 获取框架路径
    framework_path = Path(__file__).parent
    print(f"框架路径: {framework_path}")
    
    # 添加必要的路径
    sys.path.insert(0, str(framework_path))
    sys.path.insert(0, str(framework_path / "src" / "core"))
    
    print("\n可用的工具:")
    print("1. Maya网格清理工具")
    print("2. 3ds Max材质转换工具") 
    print("3. Blender网格优化工具")
    print("4. UE资产优化工具")
    print("5. 启动图形界面")
    
    while True:
        try:
            choice = input("\n请选择要使用的工具 (1-5, q退出): ").strip()
            
            if choice.lower() == 'q':
                break
            elif choice == '1':
                run_maya_tool(framework_path)
            elif choice == '2':
                run_max_tool(framework_path)
            elif choice == '3':
                run_blender_tool(framework_path)
            elif choice == '4':
                run_ue_tool(framework_path)
            elif choice == '5':
                launch_gui(framework_path)
            else:
                print("无效选择，请输入1-5或q")
                
        except KeyboardInterrupt:
            print("\n\n程序被中断")
            break
        except Exception as e:
            print(f"错误: {e}")

def run_maya_tool(framework_path):
    """运行Maya工具"""
    print("\n--- Maya网格清理工具 ---")
    try:
        plugin_path = framework_path / "src" / "plugins" / "dcc" / "maya" / "mesh_cleaner"
        sys.path.insert(0, str(plugin_path))
        
        from plugin import MayaMeshCleaner
        cleaner = MayaMeshCleaner()
        
        info = cleaner.get_info()
        print(f"插件名称: {info['name']}")
        print(f"版本: {info['version']}")
        print(f"描述: {info['description']}")
        
        print("\n使用方法:")
        print("1. 在Maya中选择要清理的网格对象")
        print("2. 运行以下代码:")
        print(f"""
import sys
sys.path.append(r"{plugin_path}")
from plugin import MayaMeshCleaner
cleaner = MayaMeshCleaner()
result = cleaner.execute(
    tolerance=0.001,
    delete_duplicates=True,
    merge_vertices=True,
    optimize_normals=True
)
print(result)
        """)
        
    except Exception as e:
        print(f"加载Maya工具失败: {e}")

def run_max_tool(framework_path):
    """运行3ds Max工具"""
    print("\n--- 3ds Max材质转换工具 ---")
    try:
        plugin_path = framework_path / "src" / "plugins" / "dcc" / "max" / "material_converter"
        sys.path.insert(0, str(plugin_path))
        
        from plugin import MaxMaterialConverter
        converter = MaxMaterialConverter()
        
        info = converter.get_info()
        print(f"插件名称: {info['name']}")
        print(f"版本: {info['version']}")
        print("这是一个3ds Max材质转换工具")
        
    except Exception as e:
        print(f"加载3ds Max工具失败: {e}")

def run_blender_tool(framework_path):
    """运行Blender工具"""
    print("\n--- Blender网格优化工具 ---")
    try:
        plugin_path = framework_path / "src" / "plugins" / "dcc" / "blender" / "mesh_optimizer"
        sys.path.insert(0, str(plugin_path))
        
        from plugin import BlenderMeshOptimizer
        optimizer = BlenderMeshOptimizer()
        
        info = optimizer.get_info()
        print(f"插件名称: {info['name']}")
        print(f"支持版本: {info['min_version']}-{info['max_version']}")
        print("这是一个Blender网格优化工具")
        
    except Exception as e:
        print(f"加载Blender工具失败: {e}")

def run_ue_tool(framework_path):
    """运行UE工具"""
    print("\n--- UE资产优化工具 ---")
    try:
        plugin_path = framework_path / "src" / "plugins" / "ue" / "asset_optimizer"
        sys.path.insert(0, str(plugin_path))
        
        from plugin import UEAssetOptimizer
        optimizer = UEAssetOptimizer()
        
        info = optimizer.get_info()
        print(f"插件名称: {info['name']}")
        print(f"UE版本: {info['target_ue_version']}")
        print("这是一个UE资产优化工具")
        
    except Exception as e:
        print(f"加载UE工具失败: {e}")

def launch_gui(framework_path):
    """启动图形界面"""
    print("\n--- 启动图形界面 ---")
    try:
        gui_path = framework_path / "src" / "gui" / "main_window.py"
        if gui_path.exists():
            print("正在启动图形界面...")
            # 这里可以添加实际的GUI启动代码
            print("图形界面功能正在开发中...")
        else:
            print("图形界面文件不存在")
    except Exception as e:
        print(f"启动GUI失败: {e}")

if __name__ == "__main__":
    main()