#!/usr/bin/env python3
"""
DCC/UE工具开发调试工具套件
提供完整的开发、测试、调试一体化环境
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dev_tools.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DevToolSuite:
    """开发工具套件主类"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.framework_path = self.project_root / "src"
        self.tools_path = self.project_root / "generated_tools"
        self.tests_path = self.project_root / "tests"
        
    def setup_development_environment(self) -> bool:
        """设置开发环境"""
        try:
            logger.info("设置开发环境...")
            
            # 创建必要的目录
            directories = [
                self.tools_path,
                self.tests_path,
                self.project_root / "debug_sessions",
                self.project_root / "logs"
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True)
            
            # 安装开发依赖
            self.install_dev_dependencies()
            
            # 创建开发配置文件
            self.create_dev_configs()
            
            logger.info("开发环境设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置开发环境失败: {e}")
            return False
    
    def install_dev_dependencies(self):
        """安装开发依赖"""
        dev_requirements = [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "debugpy>=1.6.0",
            "setuptools>=67.0"
        ]
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + dev_requirements, check=True)
            logger.info("开发依赖安装完成")
        except subprocess.CalledProcessError as e:
            logger.warning(f"依赖安装警告: {e}")
    
    def create_dev_configs(self):
        """创建开发配置文件"""
        # VSCode配置
        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # launch.json - 调试配置
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "justMyCode": True
                },
                {
                    "name": "DCC/UE Tool Debug",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/src/main.py",
                    "console": "integratedTerminal",
                    "args": [],
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                },
                {
                    "name": "Generated Tool Debug",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "cwd": "${fileDirname}",
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                }
            ]
        }
        
        with open(vscode_dir / "launch.json", "w") as f:
            json.dump(launch_config, f, indent=2)
        
        # settings.json - 工作区设置
        workspace_settings = {
            "python.defaultInterpreterPath": sys.executable,
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True
            }
        }
        
        with open(vscode_dir / "settings.json", "w") as f:
            json.dump(workspace_settings, f, indent=2)
        
        logger.info("开发配置文件创建完成")
    
    def create_tool_template(self, tool_name: str, tool_type: str = "utility") -> Path:
        """创建工具开发模板"""
        template_dir = self.tools_path / f"{tool_name}_dev"
        template_dir.mkdir(exist_ok=True)
        
        # 创建基本的工具结构
        files_to_create = {
            "plugin.py": self._generate_plugin_template(tool_name, tool_type),
            "main.py": self._generate_main_template(tool_name),
            f"{tool_name.lower()}_tool.py": self._generate_tool_class_template(tool_name),
            "test_tool.py": self._generate_test_template(tool_name),
            "requirements.txt": "# 工具依赖\n",
            "README.md": self._generate_readme_template(tool_name, tool_type),
            ".vscode/launch.json": self._generate_tool_debug_config(tool_name)
        }
        
        for file_path, content in files_to_create.items():
            full_path = template_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        logger.info(f"工具开发模板创建完成: {template_dir}")
        return template_dir
    
    def _generate_plugin_template(self, tool_name: str, tool_type: str) -> str:
        """生成插件模板"""
        return f'''"""
{tool_name} - 开发模板
"""

PLUGIN_NAME = "{tool_name}"
PLUGIN_VERSION = "0.1.0"
PLUGIN_TYPE = "{tool_type}"
PLUGIN_DESCRIPTION = "{tool_name}工具开发模板"
PLUGIN_AUTHOR = "Developer"

import logging
logger = logging.getLogger(__name__)

def validate_parameters(params: dict) -> dict:
    """验证参数"""
    # TODO: 实现参数验证逻辑
    return params

def execute_main_logic(params: dict) -> dict:
    """执行主逻辑"""
    # TODO: 实现工具核心功能
    logger.info(f"执行{{PLUGIN_NAME}} v{{PLUGIN_VERSION}}")
    return {{"status": "success", "result": "功能待实现"}}

def execute(**kwargs) -> dict:
    """插件主执行函数"""
    try:
        # 参数验证
        validated_params = validate_parameters(kwargs)
        
        # 执行主逻辑
        result = execute_main_logic(validated_params)
        
        return {{
            "status": "success",
            "tool": PLUGIN_NAME,
            "version": PLUGIN_VERSION,
            "result": result
        }}
        
    except Exception as e:
        logger.error(f"执行失败: {{e}}")
        return {{
            "status": "error",
            "tool": PLUGIN_NAME,
            "error": str(e)
        }}

def register() -> dict:
    """插件注册函数"""
    return {{
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "type": PLUGIN_TYPE,
        "description": PLUGIN_DESCRIPTION,
        "execute": execute
    }}

if __name__ == "__main__":
    # 测试执行
    test_result = execute(test_param="test_value")
    print(f"测试结果: {{test_result}}")
'''
    
    def _generate_main_template(self, tool_name: str) -> str:
        """生成主执行文件模板"""
        return f'''"""
{tool_name} 主执行文件
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from plugin import execute, register
    print("插件导入成功")
except ImportError as e:
    print(f"插件导入失败: {{e}}")
    sys.exit(1)

def main():
    """主函数"""
    try:
        # 获取插件信息
        registration = register()
        print(f"插件信息: {{registration}}")
        
        # 执行插件
        result = execute(debug=True)
        print(f"执行结果: {{result}}")
        
        return result
        
    except Exception as e:
        print(f"执行出错: {{e}}")
        return {{"status": "error", "error": str(e)}}

if __name__ == "__main__":
    main()
'''
    
    def _generate_tool_class_template(self, tool_name: str) -> str:
        """生成工具类模板"""
        return f'''"""
{tool_name} 工具类封装
"""

class {tool_name}Tool:
    """{tool_name}工具类"""
    
    def __init__(self):
        self.name = "{tool_name}"
        self.initialized = False
    
    def initialize(self):
        """初始化工具"""
        # TODO: 实现初始化逻辑
        self.initialized = True
        print(f"{{self.name}} 初始化完成")
    
    def execute(self, **kwargs):
        """执行工具"""
        if not self.initialized:
            self.initialize()
        
        # 导入并执行插件
        try:
            from .plugin import execute
            return execute(**kwargs)
        except Exception as e:
            return {{"status": "error", "error": str(e)}}
    
    def get_info(self):
        """获取工具信息"""
        try:
            from .plugin import register
            return register()
        except Exception as e:
            return {{"error": str(e)}}

# 便捷函数
def create_tool():
    """创建工具实例"""
    return {tool_name}Tool()

def run_tool(**kwargs):
    """运行工具"""
    tool = create_tool()
    return tool.execute(**kwargs)
'''
    
    def _generate_test_template(self, tool_name: str) -> str:
        """生成测试文件模板"""
        return f'''"""
{tool_name} 测试用例
"""

import unittest
import sys
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, str(Path(__file__).parent))

class Test{tool_name}(unittest.TestCase):
    
    def setUp(self):
        """测试前置条件"""
        pass
    
    def tearDown(self):
        """测试后置条件"""
        pass
    
    def test_plugin_import(self):
        """测试插件导入"""
        try:
            from plugin import execute, register
            self.assertTrue(callable(execute))
            self.assertTrue(callable(register))
        except ImportError:
            self.fail("插件导入失败")
    
    def test_registration(self):
        """测试插件注册"""
        try:
            from plugin import register
            info = register()
            self.assertIsInstance(info, dict)
            self.assertIn("name", info)
            self.assertIn("version", info)
        except Exception as e:
            self.fail(f"注册测试失败: {{e}}")
    
    def test_execution(self):
        """测试执行功能"""
        try:
            from plugin import execute
            result = execute(test_mode=True)
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"执行测试失败: {{e}}")
    
    def test_parameter_validation(self):
        """测试参数验证"""
        try:
            from plugin import execute
            # 测试各种参数情况
            result1 = execute()
            result2 = execute(test_param="value")
            
            self.assertIsInstance(result1, dict)
            self.assertIsInstance(result2, dict)
            
        except Exception as e:
            self.fail(f"参数验证测试失败: {{e}}")

if __name__ == "__main__":
    unittest.main()
'''
    
    def _generate_readme_template(self, tool_name: str, tool_type: str) -> str:
        """生成README模板"""
        return f'''# {tool_name}

## 描述
{tool_name}工具开发模板

## 类型
{tool_type.upper()}

## 开发状态
🛠️ 开发中

## 使用方法

### 开发调试
```bash
# 运行测试
python test_{tool_name.lower()}.py

# 直接执行
python main.py

# 调试模式
python -m debugpy --listen 5678 --wait-for-client main.py
```

### 集成到框架
```python
from {tool_name.lower()}_tool import run_tool

result = run_tool(
    # 传入参数
)
```

## 开发指南

1. 实现 `validate_parameters` 函数处理参数验证
2. 在 `execute_main_logic` 中实现核心功能
3. 完善测试用例
4. 更新文档说明

## 目录结构
```
{tool_name}_dev/
├── plugin.py              # 主插件文件
├── main.py                # 执行入口
├── {tool_name.lower()}_tool.py    # 工具类封装
├── test_{tool_name.lower()}.py    # 测试用例
├── requirements.txt       # 依赖列表
└── README.md             # 说明文档
```
'''
    
    def _generate_tool_debug_config(self, tool_name: str) -> str:
        """生成工具调试配置"""
        config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": f"{tool_name} Debug",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/generated_tools/" + f"{tool_name}_dev/main.py",
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}/generated_tools/" + f"{tool_name}_dev",
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                }
            ]
        }
        return json.dumps(config, indent=2)
    
    def run_tests(self, tool_path: Optional[str] = None) -> Dict[str, Any]:
        """运行测试"""
        try:
            test_command = [sys.executable, "-m", "pytest"]
            
            if tool_path:
                test_command.extend([tool_path, "-v"])
            else:
                test_command.extend([str(self.tests_path), "-v"])
            
            # 添加覆盖率报告
            test_command.extend(["--cov", str(self.framework_path), "--cov-report", "html"])
            
            result = subprocess.run(
                test_command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def debug_tool(self, tool_path: str, debug_port: int = 5678) -> bool:
        """启动工具调试会话"""
        try:
            tool_dir = Path(tool_path).parent
            main_file = tool_dir / "main.py"
            
            if not main_file.exists():
                logger.error(f"找不到main.py文件: {main_file}")
                return False
            
            debug_command = [
                sys.executable, "-m", "debugpy",
                "--listen", str(debug_port),
                "--wait-for-client",
                str(main_file)
            ]
            
            logger.info(f"启动调试会话，端口: {debug_port}")
            logger.info(f"调试命令: {' '.join(debug_command)}")
            
            # 在新进程中启动调试器
            process = subprocess.Popen(
                debug_command,
                cwd=tool_dir,
                env={**os.environ, "PYTHONPATH": str(self.framework_path)}
            )
            
            logger.info(f"调试进程已启动，PID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动调试失败: {e}")
            return False
    
    def analyze_code_quality(self, path: str) -> Dict[str, Any]:
        """分析代码质量"""
        results = {}
        
        try:
            # 运行flake8检查
            flake8_result = subprocess.run(
                [sys.executable, "-m", "flake8", path],
                capture_output=True,
                text=True
            )
            results["flake8"] = {
                "success": flake8_result.returncode == 0,
                "output": flake8_result.stdout,
                "errors": flake8_result.stderr
            }
            
            # 运行black格式检查
            black_result = subprocess.run(
                [sys.executable, "-m", "black", "--check", path],
                capture_output=True,
                text=True
            )
            results["black"] = {
                "success": black_result.returncode == 0,
                "output": black_result.stdout,
                "errors": black_result.stderr
            }
            
            # 运行mypy类型检查
            mypy_result = subprocess.run(
                [sys.executable, "-m", "mypy", path],
                capture_output=True,
                text=True
            )
            results["mypy"] = {
                "success": mypy_result.returncode == 0,
                "output": mypy_result.stdout,
                "errors": mypy_result.stderr
            }
            
        except Exception as e:
            results["error"] = str(e)
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="DCC/UE工具开发调试工具套件")
    parser.add_argument("command", choices=["setup", "create-template", "test", "debug", "analyze"])
    parser.add_argument("--name", help="工具名称")
    parser.add_argument("--type", help="工具类型", default="utility")
    parser.add_argument("--path", help="工具路径")
    parser.add_argument("--port", type=int, default=5678, help="调试端口")
    
    args = parser.parse_args()
    
    dev_suite = DevToolSuite()
    
    if args.command == "setup":
        success = dev_suite.setup_development_environment()
        sys.exit(0 if success else 1)
        
    elif args.command == "create-template":
        if not args.name:
            print("请提供工具名称: --name <tool_name>")
            sys.exit(1)
        template_path = dev_suite.create_tool_template(args.name, args.type)
        print(f"模板创建完成: {template_path}")
        
    elif args.command == "test":
        result = dev_suite.run_tests(args.path)
        print("测试结果:")
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)
        
    elif args.command == "debug":
        if not args.path:
            print("请提供工具路径: --path <tool_path>")
            sys.exit(1)
        success = dev_suite.debug_tool(args.path, args.port)
        sys.exit(0 if success else 1)
        
    elif args.command == "analyze":
        if not args.path:
            print("请提供分析路径: --path <analysis_path>")
            sys.exit(1)
        results = dev_suite.analyze_code_quality(args.path)
        print("代码质量分析:")
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()