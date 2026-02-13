"""
SDD配置规范和解析器 - 处理工具描述文档的解析和验证
"""

import yaml
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from jsonschema import validate

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """工具类型枚举"""
    DCC = "dcc"
    UE_ENGINE = "ue_engine"
    UTILITY = "utility"


@dataclass
class Parameter:
    """参数定义"""
    name: str
    type: str
    required: bool = False
    default: Any = None
    description: str = ""


@dataclass
class Compatibility:
    """兼容性信息"""
    platform: str  # dcc 或 engine
    name: str      # 软件名称
    min_version: str = ""
    max_version: str = ""


@dataclass
class ToolConfig:
    """工具配置数据类"""
    # 基本信息
    name: str
    version: str
    tool_type: ToolType
    description: str
    
    # 元数据
    author: str = ""
    created_date: str = ""
    compatibility: List[Compatibility] = field(default_factory=list)
    
    # 配置参数
    parameters: List[Parameter] = field(default_factory=list)
    
    # 执行配置
    entry_point: str = ""
    dependencies: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    
    # 集成接口
    interfaces: List[Dict[str, str]] = field(default_factory=list)
    
    # 原始配置
    raw_config: Dict[str, Any] = field(default_factory=dict)


class ConfigSchemaValidator:
    """配置模式验证器"""
    
    # SDD配置JSON Schema
    SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["tool"],
        "properties": {
            "tool": {
                "type": "object",
                "required": ["name", "version", "type", "description"],
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
                    "type": {"type": "string", "enum": ["dcc", "ue_engine", "utility"]},
                    "description": {"type": "string"}
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "created_date": {"type": "string", "format": "date"},
                    "compatibility": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "platform": {"type": "string"},
                                "name": {"type": "string"},
                                "min_version": {"type": "string"},
                                "max_version": {"type": "string"}
                            },
                            "required": ["platform", "name"]
                        }
                    }
                }
            },
            "configuration": {
                "type": "object",
                "properties": {
                    "parameters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "enum": ["string", "number", "boolean", "list", "dict"]},
                                "required": {"type": "boolean"},
                                "default": {},
                                "description": {"type": "string"}
                            },
                            "required": ["name", "type"]
                        }
                    }
                }
            },
            "execution": {
                "type": "object",
                "properties": {
                    "entry_point": {"type": "string"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "resources": {
                        "type": "object",
                        "properties": {
                            "memory_limit": {"type": "string"},
                            "timeout": {"type": "string"},
                            "cpu_limit": {"type": "string"}
                        }
                    }
                }
            },
            "integration": {
                "type": "object",
                "properties": {
                    "interfaces": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "enum": ["qt", "web", "console", "api"]}
                            },
                            "required": ["name", "type"]
                        }
                    }
                }
            }
        }
    }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        验证配置是否符合SDD规范
        
        Args:
            config: 配置字典
            
        Returns:
            是否验证通过
        """
        try:
            validate(instance=config, schema=cls.SCHEMA)
            return True
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"配置验证失败: {e.message}")
            return False


class ConfigManager:
    """
    配置管理器
    
    负责：
    - SDD配置文件的解析和验证
    - 配置模板管理
    - 自然语言到配置的转换
    - 运行时配置更新
    """
    
    def __init__(self, config_dirs: List[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dirs: 配置目录列表
        """
        self.config_dirs = config_dirs or ['./configs']
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._setup_logging()
        self._load_templates()
    
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
    
    def _load_templates(self):
        """加载配置模板"""
        template_dir = Path('./configs/templates')
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_templates()
            return
        
        for template_file in template_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    self.templates[template_file.stem] = template
                    logger.info(f"加载模板: {template_file.stem}")
            except Exception as e:
                logger.error(f"加载模板失败 {template_file}: {e}")
    
    def _create_default_templates(self):
        """创建默认模板"""
        default_templates = {
            'basic_dcc_tool': {
                'tool': {
                    'name': '{{tool_name}}',
                    'version': '1.0.0',
                    'type': 'dcc',
                    'description': '{{description}}'
                },
                'metadata': {
                    'author': '{{author}}',
                    'created_date': '{{date}}'
                },
                'execution': {
                    'entry_point': 'main.py::execute',
                    'dependencies': []
                }
            },
            'ue_engine_tool': {
                'tool': {
                    'name': '{{tool_name}}',
                    'version': '1.0.0',
                    'type': 'ue_engine',
                    'description': '{{description}}'
                },
                'metadata': {
                    'author': '{{author}}',
                    'created_date': '{{date}}'
                },
                'execution': {
                    'entry_point': 'main.py::execute',
                    'dependencies': ['unrealengine']
                }
            }
        }
        
        template_dir = Path('./configs/templates')
        for name, template in default_templates.items():
            template_file = template_dir / f"{name}.yaml"
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
    
    def parse_sdd_config(self, config_path: str) -> Optional[ToolConfig]:
        """
        解析SDD配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            工具配置对象或None
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 验证配置
            if not ConfigSchemaValidator.validate_config(config_data):
                return None
            
            # 转换为ToolConfig对象
            return self._convert_to_tool_config(config_data)
            
        except Exception as e:
            logger.error(f"解析配置文件失败 {config_path}: {e}")
            return None
    
    def _convert_to_tool_config(self, config_data: Dict[str, Any]) -> ToolConfig:
        """将配置数据转换为ToolConfig对象"""
        tool_section = config_data.get('tool', {})
        metadata_section = config_data.get('metadata', {})
        config_section = config_data.get('configuration', {})
        execution_section = config_data.get('execution', {})
        integration_section = config_data.get('integration', {})
        
        # 解析参数
        parameters = []
        for param_data in config_section.get('parameters', []):
            parameters.append(Parameter(
                name=param_data['name'],
                type=param_data['type'],
                required=param_data.get('required', False),
                default=param_data.get('default'),
                description=param_data.get('description', '')
            ))
        
        # 解析兼容性
        compatibility = []
        for compat_data in metadata_section.get('compatibility', []):
            compatibility.append(Compatibility(
                platform=compat_data['platform'],
                name=compat_data['name'],
                min_version=compat_data.get('min_version', ''),
                max_version=compat_data.get('max_version', '')
            ))
        
        return ToolConfig(
            name=tool_section['name'],
            version=tool_section['version'],
            tool_type=ToolType(tool_section['type']),
            description=tool_section['description'],
            author=metadata_section.get('author', ''),
            created_date=metadata_section.get('created_date', ''),
            compatibility=compatibility,
            parameters=parameters,
            entry_point=execution_section.get('entry_point', ''),
            dependencies=execution_section.get('dependencies', []),
            resources=execution_section.get('resources', {}),
            interfaces=integration_section.get('interfaces', []),
            raw_config=config_data
        )
    
    def generate_config_from_template(self, template_name: str, 
                                    variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        基于模板生成配置
        
        Args:
            template_name: 模板名称
            variables: 变量替换字典
            
        Returns:
            生成的配置字典或None
        """
        if template_name not in self.templates:
            logger.error(f"模板不存在: {template_name}")
            return None
        
        template = self.templates[template_name]
        return self._fill_template(template, variables)
    
    def _fill_template(self, template: Dict[str, Any], 
                      variables: Dict[str, Any]) -> Dict[str, Any]:
        """填充模板变量"""
        result = {}
        for key, value in template.items():
            if isinstance(value, dict):
                result[key] = self._fill_template(value, variables)
            elif isinstance(value, list):
                result[key] = [self._fill_template(item, variables) if isinstance(item, dict) 
                             else self._replace_variables(str(item), variables) 
                             for item in value]
            else:
                result[key] = self._replace_variables(str(value), variables)
        return result
    
    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """替换文本中的变量"""
        for var_name, var_value in variables.items():
            placeholder = f'{{{{{var_name}}}}}'
            text = text.replace(placeholder, str(var_value))
        return text
    
    def save_config(self, config: ToolConfig, output_path: str):
        """
        保存配置到文件
        
        Args:
            config: 工具配置对象
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config.raw_config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置保存成功: {output_path}")
        except Exception as e:
            logger.error(f"保存配置失败 {output_path}: {e}")


# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    cm = ConfigManager()
    
    # 基于模板生成配置
    config_data = cm.generate_config_from_template('basic_dcc_tool', {
        'tool_name': 'Mesh Exporter',
        'description': '导出网格数据的工具',
        'author': 'John Doe',
        'date': '2024-01-01'
    })
    
    if config_data:
        print("生成的配置:")
        print(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))