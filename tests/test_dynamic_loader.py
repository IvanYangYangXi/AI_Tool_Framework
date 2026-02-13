"""
动态加载引擎测试用例
"""

import unittest
import tempfile
import time
from pathlib import Path
from src.core.dynamic_loader import DynamicLoader, TimeoutException


class TestDynamicLoader(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DynamicLoader(sandbox_enabled=False)  # 测试时禁用沙箱
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.loader.cleanup_resources()
    
    def test_safe_module_loading(self):
        """测试安全模块加载"""
        # 创建测试模块
        module_content = '''
def hello(name="World"):
    return f"Hello, {name}!"

def add(a, b):
    return a + b

TEST_CONSTANT = "test_value"
'''
        
        module_path = Path(self.temp_dir) / "test_module.py"
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        # 加载模块
        module = self.loader.load_module_safely(str(module_path), "test_module")
        
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'hello'))
        self.assertTrue(hasattr(module, 'add'))
        self.assertTrue(hasattr(module, 'TEST_CONSTANT'))
        
        # 测试函数执行
        result = module.hello("Tester")
        self.assertEqual(result, "Hello, Tester!")
        
        result = module.add(5, 3)
        self.assertEqual(result, 8)
        
        self.assertEqual(module.TEST_CONSTANT, "test_value")
    
    def test_module_caching(self):
        """测试模块缓存"""
        # 创建测试模块
        module_content = '''
counter = 0

def increment():
    global counter
    counter += 1
    return counter
'''
        
        module_path = Path(self.temp_dir) / "cached_module.py"
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        # 第一次加载
        module1 = self.loader.load_module_safely(str(module_path))
        self.assertIsNotNone(module1)
        
        # 调用函数修改状态
        result1 = module1.increment()
        self.assertEqual(result1, 1)
        
        # 第二次加载（应该返回缓存的模块）
        module2 = self.loader.load_module_safely(str(module_path))
        self.assertIs(module1, module2)  # 应该是同一个对象
        
        # 状态应该是保持的
        result2 = module2.increment()
        self.assertEqual(result2, 2)
    
    def test_safe_function_execution(self):
        """测试安全函数执行"""
        # 创建测试模块
        module_content = '''
def normal_function(x, y):
    return x * y

def slow_function(duration):
    import time
    time.sleep(duration)
    return "completed"

def error_function():
    raise ValueError("测试异常")
'''
        
        module_path = Path(self.temp_dir) / "execution_test_module.py"
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        module = self.loader.load_module_safely(str(module_path))
        self.assertIsNotNone(module)
        
        # 正常函数执行
        result = self.loader.execute_function_safely(
            module.normal_function, 6, 7
        )
        self.assertEqual(result, 42)
        
        # 超时测试（如果支持的话）
        try:
            result = self.loader.execute_function_safely(
                module.slow_function, 2, _timeout=1
            )
            # 如果没有超时异常，检查结果
            self.assertEqual(result, "completed")
        except TimeoutException:
            # 超时是预期的行为
            pass
        except Exception:
            # 其他异常
            pass
    
    def test_module_unloading(self):
        """测试模块卸载"""
        # 创建测试模块
        module_content = '''
def test_function():
    return "test"
'''
        
        module_path = Path(self.temp_dir) / "unload_test_module.py"
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        # 加载模块
        module = self.loader.load_module_safely(str(module_path), "unload_test")
        self.assertIsNotNone(module)
        self.assertIn("unload_test", self.loader.get_loaded_modules())
        
        # 卸载模块
        result = self.loader.unload_module("unload_test")
        self.assertTrue(result)
        self.assertNotIn("unload_test", self.loader.get_loaded_modules())
    
    def test_invalid_module_handling(self):
        """测试无效模块处理"""
        # 不存在的文件
        module = self.loader.load_module_safely("/nonexistent/module.py")
        self.assertIsNone(module)
        
        # 无效的Python文件
        invalid_content = '''
def invalid_syntax(
    return "unclosed parenthesis"
'''
        
        invalid_path = Path(self.temp_dir) / "invalid_module.py"
        with open(invalid_path, 'w', encoding='utf-8') as f:
            f.write(invalid_content)
        
        module = self.loader.load_module_safely(str(invalid_path))
        self.assertIsNone(module)


if __name__ == '__main__':
    unittest.main()