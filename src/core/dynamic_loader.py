"""
动态加载引擎 - 负责插件的安全加载和执行环境管理
"""

import os
import sys
import importlib
import importlib.util
import traceback
import logging
import signal
from typing import Any, Dict, Optional, Callable
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Thread, Event
import time

# Windows兼容性处理
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    # 创建虚拟的resource模块用于Windows
    class DummyResource:
        RLIMIT_AS = 1
        RLIMIT_CPU = 2
        RLIM_INFINITY = float('inf')
        
        @staticmethod
        def getrlimit(*args):
            return (float('inf'), float('inf'))
        
        @staticmethod
        def setrlimit(*args):
            pass
    
    resource = DummyResource()

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """资源限制配置"""
    memory_limit_mb: int = 512
    cpu_time_limit_sec: int = 30
    timeout_sec: int = 60


class SandboxEnvironment:
    """
    沙箱执行环境
    提供隔离的执行空间和资源限制
    """
    
    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.original_limits = None
    
    def __enter__(self):
        """进入沙箱环境"""
        self._setup_resource_limits()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出沙箱环境"""
        self._restore_resource_limits()
    
    def _setup_resource_limits(self):
        """设置资源限制"""
        try:
            # 设置内存限制（Linux/Mac）
            if HAS_RESOURCE and hasattr(resource, 'RLIMIT_AS'):
                self.original_limits = resource.getrlimit(resource.RLIMIT_AS)
                resource.setrlimit(
                    resource.RLIMIT_AS, 
                    (self.limits.memory_limit_mb * 1024 * 1024, resource.RLIM_INFINITY)
                )
            
            # 设置CPU时间限制
            if HAS_RESOURCE and hasattr(resource, 'RLIMIT_CPU'):
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.limits.cpu_time_limit_sec, resource.RLIM_INFINITY)
                )
                
        except Exception as e:
            logger.warning(f"无法设置资源限制: {e}")
    
    def _restore_resource_limits(self):
        """恢复原始资源限制"""
        try:
            if HAS_RESOURCE and self.original_limits and hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, self.original_limits)
        except Exception as e:
            logger.warning(f"无法恢复资源限制: {e}")


class TimeoutException(Exception):
    """超时异常"""
    pass


class DynamicLoader:
    """
    动态加载引擎
    
    负责：
    - 安全的插件加载
    - 沙箱环境执行
    - 资源限制控制
    - 错误恢复机制
    - 代码签名验证
    """
    
    def __init__(self, sandbox_enabled: bool = True):
        """
        初始化动态加载器
        
        Args:
            sandbox_enabled: 是否启用沙箱环境
        """
        self.sandbox_enabled = sandbox_enabled
        self._setup_logging()
        self._loaded_modules: Dict[str, Any] = {}
    
    def _setup_logging(self):
        """设置日志"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    @contextmanager
    def timeout_context(self, seconds: int):
        """
        超时上下文管理器
        
        Args:
            seconds: 超时秒数
        """
        def timeout_handler(signum, frame):
            raise TimeoutException(f"执行超时 ({seconds}秒)")
        
        # Windows不支持signal.SIGALRM
        if os.name != 'nt':
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
        
        try:
            yield
        finally:
            if os.name != 'nt':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
    
    def load_module_safely(self, module_path: str, module_name: str = None) -> Optional[Any]:
        """
        安全加载模块
        
        Args:
            module_path: 模块文件路径
            module_name: 模块名称
            
        Returns:
            加载的模块对象或None
        """
        module_name = module_name or Path(module_path).stem
        
        try:
            # 检查模块是否已加载
            if module_name in self._loaded_modules:
                logger.info(f"模块已加载: {module_name}")
                return self._loaded_modules[module_name]
            
            # 验证文件存在
            if not os.path.exists(module_path):
                logger.error(f"模块文件不存在: {module_path}")
                return None
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                logger.error(f"无法创建模块规范: {module_path}")
                return None
            
            # 在沙箱环境中加载模块
            with self._safe_execution_environment():
                module = importlib.util.module_from_spec(spec)
                
                # 设置超时保护
                with self.timeout_context(30):  # 30秒加载超时
                    spec.loader.exec_module(module)
                
                # 存储已加载模块
                self._loaded_modules[module_name] = module
                logger.info(f"模块加载成功: {module_name}")
                return module
                
        except TimeoutException as e:
            logger.error(f"模块加载超时: {module_name} - {e}")
            return None
        except Exception as e:
            logger.error(f"模块加载失败: {module_name} - {e}")
            logger.debug(traceback.format_exc())
            return None
    
    @contextmanager
    def _safe_execution_environment(self):
        """安全执行环境上下文"""
        if self.sandbox_enabled:
            with SandboxEnvironment() as sandbox:
                yield sandbox
        else:
            yield None
    
    def execute_function_safely(self, func: Callable, *args, **kwargs) -> Any:
        """
        安全执行函数
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
        """
        try:
            with self._safe_execution_environment():
                # 设置执行超时
                timeout = kwargs.pop('_timeout', 30)
                
                def target():
                    try:
                        result['value'] = func(*args, **kwargs)
                    except Exception as e:
                        result['exception'] = e
                
                result = {'value': None, 'exception': None}
                thread = Thread(target=target)
                thread.daemon = True
                thread.start()
                
                thread.join(timeout)
                
                if thread.is_alive():
                    raise TimeoutException(f"函数执行超时 ({timeout}秒)")
                
                if result['exception']:
                    raise result['exception']
                
                return result['value']
                
        except TimeoutException:
            logger.error(f"函数执行超时: {func.__name__}")
            raise
        except Exception as e:
            logger.error(f"函数执行失败: {func.__name__} - {e}")
            raise
    
    def unload_module(self, module_name: str) -> bool:
        """
        卸载模块
        
        Args:
            module_name: 模块名称
            
        Returns:
            是否卸载成功
        """
        try:
            if module_name in self._loaded_modules:
                del self._loaded_modules[module_name]
            
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            logger.info(f"模块卸载成功: {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"模块卸载失败: {module_name} - {e}")
            return False
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """
        获取所有已加载的模块
        
        Returns:
            已加载模块字典
        """
        return self._loaded_modules.copy()
    
    def verify_module_signature(self, module_path: str) -> bool:
        """
        验证模块代码签名（简化实现）
        
        Args:
            module_path: 模块文件路径
            
        Returns:
            签名是否有效
        """
        # 简化实现，实际项目中应使用数字签名
        try:
            with open(module_path, 'rb') as f:
                content = f.read()
                # 这里可以实现哈希校验或其他签名验证逻辑
                return True
        except Exception:
            return False
    
    def cleanup_resources(self):
        """清理资源"""
        self._loaded_modules.clear()
        logger.info("动态加载器资源清理完成")


# 使用示例
if __name__ == "__main__":
    loader = DynamicLoader(sandbox_enabled=True)
    
    # 安全加载模块
    module = loader.load_module_safely("./example_plugin.py")
    if module:
        # 安全执行函数
        try:
            result = loader.execute_function_safely(
                getattr(module, 'main', lambda: "No main function"),
                _timeout=10
            )
            print(f"执行结果: {result}")
        except Exception as e:
            print(f"执行失败: {e}")