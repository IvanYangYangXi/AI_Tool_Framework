"""
AI工具生成器 - 基于自然语言描述和SDD规范自动生成工具代码
"""

import logging
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from ..core.config_manager import ConfigManager
from .sdd_processor import SDDProcessor
from .model_interface import ModelInterface
from .code_validator import CodeValidator

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """生成结果数据类"""
    success: bool
    tool_name: str
    generated_files: List[str]
    config_file: str
    validation_results: Dict[str, Any]
    ai_prompt_used: str
    execution_instructions: str


class AIToolGenerator:
    """
    AI驱动的工具生成器
    
    功能：
    - 将自然语言描述转换为SDD配置
    - 基于SDD配置生成完整的工具代码
    - 自动生成测试用例
    - 代码验证和质量检查
    - 一键部署集成
    """
    
    def __init__(self, model_provider: str = "openai", api_key: str = None):
        """
        初始化AI工具生成器
        
        Args:
            model_provider: AI模型提供商 ("openai", "anthropic", "local")
            api_key: API密钥
        """
        self.model_interface = ModelInterface(model_provider, api_key)
        self.sdd_processor = SDDProcessor()
        self.code_validator = CodeValidator()
        self.config_manager = ConfigManager()
        self._setup_logging()
        
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
    
    def generate_tool_from_description(self, description: str, 
                                     output_dir: str = "./generated_tools") -> GenerationResult:
        """
        基于自然语言描述生成完整工具
        
        Args:
            description: 工具功能描述
            output_dir: 输出目录
            
        Returns:
            生成结果对象
        """
        try:
            logger.info(f"开始生成工具: {description[:50]}...")
            
            # 1. 自然语言到SDD配置的转换
            sdd_config = self._nl_to_sdd(description)
            if not sdd_config:
                return GenerationResult(
                    success=False,
                    tool_name="unknown",
                    generated_files=[],
                    config_file="",
                    validation_results={"error": "SDD配置生成失败"},
                    ai_prompt_used="",
                    execution_instructions=""
                )
            
            tool_name = sdd_config.get('tool', {}).get('name', 'GeneratedTool')
            logger.info(f"生成的工具名称: {tool_name}")
            
            # 2. 基于SDD配置生成代码
            generated_files = self._generate_code_from_sdd(sdd_config, output_dir)
            
            # 3. 生成配置文件
            config_file = self._generate_config_file(sdd_config, output_dir)
            
            # 4. 代码验证
            validation_results = self._validate_generated_code(generated_files)
            
            # 5. 生成执行说明
            instructions = self._generate_execution_instructions(sdd_config)
            
            result = GenerationResult(
                success=True,
                tool_name=tool_name,
                generated_files=generated_files,
                config_file=config_file,
                validation_results=validation_results,
                ai_prompt_used=self.model_interface.last_prompt,
                execution_instructions=instructions
            )
            
            logger.info(f"工具生成成功: {tool_name}")
            return result
            
        except Exception as e:
            logger.error(f"工具生成失败: {e}")
            return GenerationResult(
                success=False,
                tool_name="unknown",
                generated_files=[],
                config_file="",
                validation_results={"error": str(e)},
                ai_prompt_used=getattr(self.model_interface, 'last_prompt', ''),
                execution_instructions=""
            )
    
    def _nl_to_sdd(self, description: str) -> Optional[Dict[str, Any]]:
        """
        自然语言转SDD配置
        
        Args:
            description: 自然语言描述
            
        Returns:
            SDD配置字典或None
        """
        prompt = self._create_sdd_generation_prompt(description)
        
        try:
            response = self.model_interface.generate_response(prompt)
            sdd_config = self.sdd_processor.parse_ai_response(response)
            return sdd_config
        except Exception as e:
            logger.error(f"SDD配置生成失败: {e}")
            return None
    
    def _create_sdd_generation_prompt(self, description: str) -> str:
        """
        创建SDD生成提示词
        
        Args:
            description: 工具描述
            
        Returns:
            格式化的提示词
        """
        template = """
你是一个专业的工具开发专家。请根据以下自然语言描述，生成符合SDD规范的工具配置。

工具描述: {description}

请严格按照以下YAML格式输出SDD配置：

tool:
  name: "[工具名称，使用驼峰命名法]"
  version: "1.0.0"
  type: "[dcc|ue_engine|utility]"
  description: "[详细的工具功能描述]"

metadata:
  author: "AI Generated"
  created_date: "{current_date}"
  compatibility:
    - platform: "[目标平台]"
      name: "[具体软件名称]"
      min_version: "[最低版本]"

configuration:
  parameters:
    - name: "[参数名]"
      type: "[string|number|boolean|list]"
      required: [true|false]
      default: [默认值]
      description: "[参数说明]"

execution:
  entry_point: "main.py::execute"
  dependencies:
    - "[依赖包1]"
    - "[依赖包2]"
  resources:
    memory_limit: "512MB"
    timeout: "30s"

integration:
  interfaces:
    - name: "Main Interface"
      type: "console"

要求：
1. 工具名称要简洁明确
2. 参数设计要考虑实用性
3. 依赖包要准确完整
4. 兼容性信息要真实可靠
5. 只输出YAML格式，不要添加其他说明文字

请直接输出YAML配置：
""".format(
    description=description,
    current_date="2024-01-01"  # 实际使用时应该用datetime
)
        
        return template
    
    def _generate_code_from_sdd(self, sdd_config: Dict[str, Any], 
                              output_dir: str) -> List[str]:
        """
        基于SDD配置生成代码文件
        
        Args:
            sdd_config: SDD配置
            output_dir: 输出目录
            
        Returns:
            生成的文件路径列表
        """
        generated_files = []
        tool_info = sdd_config.get('tool', {})
        tool_name = tool_info.get('name', 'GeneratedTool')
        tool_type = tool_info.get('type', 'utility')
        
        # 创建工具目录
        tool_dir = Path(output_dir) / tool_name.lower()
        tool_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成主插件文件
        main_plugin_content = self._generate_main_plugin(sdd_config)
        main_plugin_file = tool_dir / "plugin.py"
        with open(main_plugin_file, 'w', encoding='utf-8') as f:
            f.write(main_plugin_content)
        generated_files.append(str(main_plugin_file))
        
        # 生成主执行文件
        main_content = self._generate_main_file(sdd_config)
        main_file = tool_dir / "main.py"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        generated_files.append(str(main_file))
        
        # 生成工具类文件
        tool_class_content = self._generate_tool_class(sdd_config)
        tool_class_file = tool_dir / f"{tool_name.lower()}_tool.py"
        with open(tool_class_file, 'w', encoding='utf-8') as f:
            f.write(tool_class_content)
        generated_files.append(str(tool_class_file))
        
        # 生成README
        readme_content = self._generate_readme(sdd_config)
        readme_file = tool_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        generated_files.append(str(readme_file))
        
        return generated_files
    
    def _generate_main_plugin(self, sdd_config: Dict[str, Any]) -> str:
        """生成主插件文件"""
        tool_info = sdd_config.get('tool', {})
        tool_name = tool_info.get('name', 'GeneratedTool')
        tool_version = tool_info.get('version', '1.0.0')
        tool_type = tool_info.get('type', 'utility')
        description = tool_info.get('description', 'Generated tool')
        author = sdd_config.get('metadata', {}).get('author', 'AI Generated')
        
        # 获取参数信息
        parameters = sdd_config.get('configuration', {}).get('parameters', [])
        
        # 生成参数处理代码
        param_processing = self._generate_parameter_processing(parameters)
        
        template = f'''"""
{tool_name} - {description}
自动生成的{tool_type.upper()}工具插件
"""

PLUGIN_NAME = "{tool_name}"
PLUGIN_VERSION = "{tool_version}"
PLUGIN_TYPE = "{tool_type}"
PLUGIN_DESCRIPTION = "{description}"
PLUGIN_AUTHOR = "{author}"

{param_processing}

def execute(**kwargs):
    """
    插件主执行函数
    
    Args:
        **kwargs: 配置参数
        
    Returns:
        执行结果字典
    """
    try:
        print(f"执行 {{PLUGIN_NAME}} v{{PLUGIN_VERSION}}")
        print(f"参数: {{kwargs}}")
        
        # 参数验证和处理
        validated_params = validate_parameters(kwargs)
        
        # 执行核心逻辑
        result = main_execution(validated_params)
        
        return {{
            "status": "success",
            "tool": PLUGIN_NAME,
            "version": PLUGIN_VERSION,
            "result": result,
            "parameters_used": validated_params
        }}
        
    except Exception as e:
        print(f"执行失败: {{e}}")
        return {{
            "status": "error",
            "tool": PLUGIN_NAME,
            "error": str(e)
        }}

def register():
    """插件注册函数"""
    return {{
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "type": PLUGIN_TYPE,
        "description": PLUGIN_DESCRIPTION,
        "execute": execute
    }}

if __name__ == "__main__":
    # 直接运行测试
    test_params = {{{self._generate_test_params(parameters)}}}
    result = execute(**test_params)
    print(f"测试结果: {{result}}")
'''
        
        return template
    
    def _generate_parameter_processing(self, parameters: List[Dict]) -> str:
        """生成参数处理代码"""
        if not parameters:
            return '''def validate_parameters(params):
    """验证参数"""
    return params

def main_execution(params):
    """主执行逻辑"""
    return "工具执行完成"'''
        
        validation_code = "def validate_parameters(params):\n"
        validation_code += "    \"\"\"验证和处理参数\"\"\"\n"
        validation_code += "    validated = {}\n\n"
        
        for param in parameters:
            name = param['name']
            param_type = param['type']
            required = param.get('required', False)
            default = param.get('default', None)
            
            validation_code += f"    # 处理参数: {name}\n"
            if required:
                validation_code += f"    if '{name}' not in params:\n"
                validation_code += f"        raise ValueError('缺少必需参数: {name}')\n"
            
            if default is not None:
                validation_code += f"    {name} = params.get('{name}', {repr(default)})\n"
            else:
                validation_code += f"    {name} = params.get('{name}')\n"
            
            # 类型检查
            if param_type == 'string':
                validation_code += f"    if {name} is not None and not isinstance({name}, str):\n"
                validation_code += f"        raise TypeError('{name} 必须是字符串类型')\n"
            elif param_type == 'number':
                validation_code += f"    if {name} is not None and not isinstance({name}, (int, float)):\n"
                validation_code += f"        raise TypeError('{name} 必须是数字类型')\n"
            elif param_type == 'boolean':
                validation_code += f"    if {name} is not None and not isinstance({name}, bool):\n"
                validation_code += f"        raise TypeError('{name} 必须是布尔类型')\n"
            
            validation_code += f"    validated['{name}'] = {name}\n\n"
        
        validation_code += "    return validated\n\n"
        
        # 生成主执行逻辑占位符
        validation_code += "def main_execution(params):\n"
        validation_code += "    \"\"\"主执行逻辑 - 需要根据具体功能实现\"\"\"\n"
        validation_code += "    # 这里实现具体的工具功能\n"
        validation_code += "    print('执行工具核心逻辑...')\n"
        validation_code += "    return '功能执行完成'\n"
        
        return validation_code
    
    def _generate_test_params(self, parameters: List[Dict]) -> str:
        """生成测试参数"""
        if not parameters:
            return ""
        
        test_params = []
        for param in parameters:
            name = param['name']
            param_type = param['type']
            default = param.get('default')
            
            if default is not None:
                test_params.append(f"'{name}': {repr(default)}")
            elif param_type == 'string':
                test_params.append(f"'{name}': 'test_value'")
            elif param_type == 'number':
                test_params.append(f"'{name}': 123")
            elif param_type == 'boolean':
                test_params.append(f"'{name}': True")
            else:
                test_params.append(f"'{name}': None")
        
        return ", ".join(test_params)
    
    def _generate_main_file(self, sdd_config: Dict[str, Any]) -> str:
        """生成主执行文件"""
        tool_info = sdd_config.get('tool', {})
        tool_name = tool_info.get('name', 'GeneratedTool')
        
        template = f'''"""
{tool_name} 主执行文件
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from plugin import execute, register

def main():
    """主函数"""
    # 注册信息
    registration = register()
    print(f"工具信息: {{registration}}")
    
    # 执行工具
    result = execute()
    print(f"执行结果: {{result}}")
    
    return result

if __name__ == "__main__":
    main()
'''
        
        return template
    
    def _generate_tool_class(self, sdd_config: Dict[str, Any]) -> str:
        """生成工具类文件"""
        tool_info = sdd_config.get('tool', {})
        tool_name = tool_info.get('name', 'GeneratedTool')
        description = tool_info.get('description', 'Generated tool')
        
        template = f'''"""
{tool_name} 工具类
{description}
"""

class {tool_name}Tool:
    """{tool_name}工具类"""
    
    def __init__(self):
        self.name = "{tool_name}"
        self.description = "{description}"
    
    def execute(self, **kwargs):
        """执行工具功能"""
        # 导入并执行插件
        from .plugin import execute
        return execute(**kwargs)
    
    def get_info(self):
        """获取工具信息"""
        from .plugin import register
        return register()

# 便捷函数
def create_tool():
    """创建工具实例"""
    return {tool_name}Tool()

def run_tool(**kwargs):
    """运行工具"""
    tool = create_tool()
    return tool.execute(**kwargs)
'''
        
        return template
    
    def _generate_readme(self, sdd_config: Dict[str, Any]) -> str:
        """生成README文件"""
        tool_info = sdd_config.get('tool', {})
        tool_name = tool_info.get('name', 'GeneratedTool')
        description = tool_info.get('description', 'Generated tool')
        version = tool_info.get('version', '1.0.0')
        
        parameters = sdd_config.get('configuration', {}).get('parameters', [])
        dependencies = sdd_config.get('execution', {}).get('dependencies', [])
        
        param_table = "| 参数名 | 类型 | 必需 | 默认值 | 说明 |\n|--------|------|------|--------|------|\n"
        for param in parameters:
            name = param.get('name', '')
            ptype = param.get('type', '')
            required = '是' if param.get('required', False) else '否'
            default = str(param.get('default', '')) if param.get('default') is not None else ''
            desc = param.get('description', '')
            param_table += f"| {name} | {ptype} | {required} | {default} | {desc} |\n"
        
        deps_list = "\n".join([f"- {dep}" for dep in dependencies]) if dependencies else "无特殊依赖"
        
        template = f'''# {tool_name}

## 描述
{description}

## 版本
{version}

## 使用方法

### 基本使用
```python
from {tool_name.lower()}_tool import run_tool

result = run_tool(
    # 在这里传入参数
)
print(result)
```

### 作为插件使用
```python
from plugin import execute

result = execute(
    # 参数配置
)
```

## 参数说明
{param_table}

## 依赖项
{deps_list}

## 开发说明
- 主要逻辑在 `plugin.py` 中实现
- 工具类封装在 `{tool_name.lower()}_tool.py` 中
- 可直接运行 `main.py` 进行测试

## 注意事项
- 请确保满足所有依赖要求
- 建议在测试环境中先验证功能
'''
        
        return template
    
    def _generate_config_file(self, sdd_config: Dict[str, Any], output_dir: str) -> str:
        """生成配置文件"""
        import yaml
        
        tool_name = sdd_config.get('tool', {}).get('name', 'GeneratedTool')
        config_file = Path(output_dir) / tool_name.lower() / f"{tool_name.lower()}_config.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sdd_config, f, default_flow_style=False, allow_unicode=True)
        
        return str(config_file)
    
    def _validate_generated_code(self, generated_files: List[str]) -> Dict[str, Any]:
        """验证生成的代码"""
        results = {}
        
        for file_path in generated_files:
            try:
                validation_result = self.code_validator.validate_file(file_path)
                results[file_path] = validation_result
            except Exception as e:
                results[file_path] = {"valid": False, "error": str(e)}
        
        return results
    
    def _generate_execution_instructions(self, sdd_config: Dict[str, Any]) -> str:
        """生成执行说明"""
        tool_name = sdd_config.get('tool', {}).get('name', 'GeneratedTool')
        parameters = sdd_config.get('configuration', {}).get('parameters', [])
        
        instructions = f"""
# {tool_name} 使用说明

## 安装依赖
```bash
pip install -r requirements.txt
```

## 基本使用
```python
from {tool_name.lower()}.{tool_name.lower()}_tool import run_tool

# 带参数执行
result = run_tool(
"""

        # 添加参数示例
        for param in parameters[:3]:  # 只显示前3个参数作为示例
            name = param['name']
            ptype = param['type']
            default = param.get('default')
            instructions += f"    {name}="
            if default is not None:
                instructions += f"{repr(default)},\n"
            elif ptype == 'string':
                instructions += "'示例值',\n"
            elif ptype == 'number':
                instructions += "123,\n"
            elif ptype == 'boolean':
                instructions += "True,\n"
            else:
                instructions += "None,\n"
        
        instructions += """)
print(result)
```

## 作为插件使用
```python
import sys
sys.path.append('./generated_tools/{tool_name.lower()}')

from plugin import execute
result = execute()
print(result)
```

## 目录结构
```
{tool_name.lower()}/
├── plugin.py              # 主插件文件
├── main.py                # 执行入口
├── {tool_name.lower()}_tool.py    # 工具类封装
├── {tool_name.lower()}_config.yaml # 配置文件
└── README.md              # 说明文档
```
""".format(tool_name=tool_name.lower())
        
        return instructions


# 使用示例
if __name__ == "__main__":
    # 创建AI工具生成器
    generator = AIToolGenerator()
    
    # 基于自然语言描述生成工具
    description = "创建一个Maya的网格清理工具，能够删除重复顶点，合并接近的顶点，优化网格拓扑结构"
    
    result = generator.generate_tool_from_description(description)
    
    if result.success:
        print(f"工具生成成功: {result.tool_name}")
        print(f"生成的文件: {result.generated_files}")
        print(f"配置文件: {result.config_file}")
        print(f"执行说明: {result.execution_instructions}")
    else:
        print(f"工具生成失败: {result.validation_results}")