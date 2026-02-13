#!/usr/bin/env python3
"""
简单Blender插件功能测试
"""

import sys
import os
from pathlib import Path

# 添加核心模块路径
project_root = Path(__file__).parent
core_path = project_root / "src" / "core"
sys.path.insert(0, str(core_path))

try:
    # 测试导入核心接口
    from dcc_plugin_interface import DCCSoftware, dcc_plugin, validate_params
    
    print("核心接口导入成功")
    print("支持的DCC软件:", [sw.value for sw in DCCSoftware])
    
    # 测试装饰器功能
    @dcc_plugin(
        name="TestPlugin",
        version="1.0.0", 
        dcc=DCCSoftware.BLENDER,
        min_version="3.0"
    )
    class TestPlugin:
        PLUGIN_DESCRIPTION = "测试插件"
        PLUGIN_AUTHOR = "Test Author"
        
        @validate_params(tolerance={'type': float, 'min': 0.001, 'max': 1.0, 'default': 0.01})
        def test_method(self, **kwargs):
            return kwargs
    
    plugin = TestPlugin()
    result = plugin.test_method(tolerance=0.05)
    print("参数验证测试通过:", result)
    
    print("Blender插件基础功能测试完成")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()