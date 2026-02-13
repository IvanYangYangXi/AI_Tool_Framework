"""
插件管理器测试用例
"""

import unittest
import tempfile
import os
from pathlib import Path
from src.core.plugin_manager import PluginManager, PluginType, PluginStatus


class TestPluginManager(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_manager = PluginManager([self.temp_dir])
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plugin_discovery(self):
        """测试插件发现功能"""
        # 创建测试插件文件
        plugin_dir = Path(self.temp_dir) / "test_plugin"
        plugin_dir.mkdir()
        
        plugin_content = '''
PLUGIN_NAME = "TestPlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "dcc"
PLUGIN_DESCRIPTION = "测试插件"
PLUGIN_AUTHOR = "Test Author"
'''
        
        plugin_file = plugin_dir / "plugin.py"
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 测试插件发现
        plugins = self.plugin_manager.discover_plugins()
        
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]
        self.assertEqual(plugin.name, "TestPlugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.plugin_type, PluginType.DCC)
        self.assertEqual(plugin.status, PluginStatus.UNLOADED)
    
    def test_plugin_loading(self):
        """测试插件加载功能"""
        # 创建带执行函数的测试插件
        plugin_dir = Path(self.temp_dir) / "executable_plugin"
        plugin_dir.mkdir()
        
        plugin_content = '''
PLUGIN_NAME = "ExecutablePlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "utility"
PLUGIN_DESCRIPTION = "可执行测试插件"
PLUGIN_AUTHOR = "Test Author"

def execute(test_param="default"):
    return f"执行结果: {test_param}"

def register():
    return {"execute": execute}
'''
        
        plugin_file = plugin_dir / "plugin.py"
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 发现并加载插件
        self.plugin_manager.discover_plugins()
        result = self.plugin_manager.load_plugin("ExecutablePlugin")
        
        self.assertTrue(result)
        
        # 验证插件状态
        plugin_info = self.plugin_manager.plugins["ExecutablePlugin"]
        self.assertEqual(plugin_info.status, PluginStatus.LOADED)
        
        # 获取并执行插件
        plugin_module = self.plugin_manager.get_plugin("ExecutablePlugin")
        self.assertIsNotNone(plugin_module)
        self.assertTrue(hasattr(plugin_module, 'execute'))
        
        result = plugin_module.execute("测试参数")
        self.assertEqual(result, "执行结果: 测试参数")
    
    def test_plugin_unloading(self):
        """测试插件卸载功能"""
        # 创建测试插件
        plugin_dir = Path(self.temp_dir) / "unloadable_plugin"
        plugin_dir.mkdir()
        
        plugin_content = '''
PLUGIN_NAME = "UnloadablePlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "utility"
PLUGIN_DESCRIPTION = "可卸载测试插件"
PLUGIN_AUTHOR = "Test Author"

def execute():
    return "插件执行"
'''
        
        plugin_file = plugin_dir / "plugin.py"
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 加载插件
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("UnloadablePlugin")
        
        # 验证加载状态
        self.assertIn("UnloadablePlugin", self.plugin_manager.loaded_plugins)
        
        # 卸载插件
        result = self.plugin_manager.unload_plugin("UnloadablePlugin")
        self.assertTrue(result)
        
        # 验证卸载状态
        self.assertNotIn("UnloadablePlugin", self.plugin_manager.loaded_plugins)
        plugin_info = self.plugin_manager.plugins["UnloadablePlugin"]
        self.assertEqual(plugin_info.status, PluginStatus.UNLOADED)
    
    def test_list_plugins_by_type(self):
        """测试按类型列出插件"""
        # 创建不同类型插件
        plugins_data = [
            ("DCCPlugin", "dcc"),
            ("UEPlugin", "ue_engine"),
            ("UtilityPlugin", "utility")
        ]
        
        for name, plugin_type in plugins_data:
            plugin_dir = Path(self.temp_dir) / f"{name.lower()}_plugin"
            plugin_dir.mkdir()
            
            plugin_content = f'''
PLUGIN_NAME = "{name}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "{plugin_type}"
PLUGIN_DESCRIPTION = "测试{plugin_type}插件"
PLUGIN_AUTHOR = "Test Author"
'''
            
            plugin_file = plugin_dir / "plugin.py"
            with open(plugin_file, 'w', encoding='utf-8') as f:
                f.write(plugin_content)
        
        # 发现所有插件
        all_plugins = self.plugin_manager.discover_plugins()
        self.assertEqual(len(all_plugins), 3)
        
        # 按类型筛选
        dcc_plugins = self.plugin_manager.list_plugins(PluginType.DCC)
        ue_plugins = self.plugin_manager.list_plugins(PluginType.UE_ENGINE)
        utility_plugins = self.plugin_manager.list_plugins(PluginType.UTILITY)
        
        self.assertEqual(len(dcc_plugins), 1)
        self.assertEqual(len(ue_plugins), 1)
        self.assertEqual(len(utility_plugins), 1)
        
        self.assertEqual(dcc_plugins[0].name, "DCCPlugin")
        self.assertEqual(ue_plugins[0].name, "UEPlugin")
        self.assertEqual(utility_plugins[0].name, "UtilityPlugin")


if __name__ == '__main__':
    unittest.main()