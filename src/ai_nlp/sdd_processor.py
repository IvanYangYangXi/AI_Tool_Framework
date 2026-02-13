"""
SDD处理器 - 处理AI生成的SDD配置响应
"""

import yaml
import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SDDProcessor:
    """
    SDD配置处理器
    负责解析、验证和处理AI生成的SDD配置
    """
    
    def __init__(self):
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
    
    def parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析AI响应中的SDD配置
        
        Args:
            response: AI生成的响应文本
            
        Returns:
            解析后的SDD配置字典或None
        """
        try:
            # 方法1: 直接尝试YAML解析
            config = self._parse_yaml_directly(response)
            if config:
                logger.info("直接YAML解析成功")
                return config
            
            # 方法2: 提取YAML块
            config = self._extract_yaml_block(response)
            if config:
                logger.info("YAML块提取成功")
                return config
            
            # 方法3: 提取JSON格式
            config = self._extract_json_block(response)
            if config:
                logger.info("JSON块提取成功")
                return config
            
            # 方法4: 模式匹配提取
            config = self._pattern_extract_config(response)
            if config:
                logger.info("模式匹配提取成功")
                return config
            
            logger.warning("无法从响应中提取有效的SDD配置")
            return None
            
        except Exception as e:
            logger.error(f"SDD解析失败: {e}")
            return None
    
    def _parse_yaml_directly(self, response: str) -> Optional[Dict[str, Any]]:
        """直接解析YAML"""
        try:
            # 清理响应文本
            cleaned_response = self._clean_response(response)
            config = yaml.safe_load(cleaned_response)
            
            # 验证基本结构
            if self._validate_sdd_structure(config):
                return config
            return None
        except Exception:
            return None
    
    def _extract_yaml_block(self, response: str) -> Optional[Dict[str, Any]]:
        """提取YAML代码块"""
        # 匹配 ```yaml ... ``` 或 ``` ... ``` 格式的代码块
        yaml_patterns = [
            r'```yaml\s*(.*?)\s*```',
            r'```yml\s*(.*?)\s*```',
            r'```(?:\s*)(tool:.*?)\s*```',
            r'(tool:\s*.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in yaml_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    config = yaml.safe_load(match.strip())
                    if self._validate_sdd_structure(config):
                        return config
                except Exception:
                    continue
        return None
    
    def _extract_json_block(self, response: str) -> Optional[Dict[str, Any]]:
        """提取JSON格式"""
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'(\{.*?"tool".*?\})'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    config = json.loads(match.strip())
                    # 转换为YAML格式
                    if self._validate_sdd_structure(config):
                        return config
                except Exception:
                    continue
        return None
    
    def _pattern_extract_config(self, response: str) -> Optional[Dict[str, Any]]:
        """使用模式匹配提取配置"""
        try:
            config = {
                'tool': {},
                'metadata': {},
                'configuration': {'parameters': []},
                'execution': {'dependencies': [], 'resources': {}},
                'integration': {'interfaces': []}
            }
            
            # 提取工具基本信息
            tool_name = self._extract_pattern(response, r'[工具名称|name][:：]\s*([^\n]+)')
            if tool_name:
                config['tool']['name'] = tool_name.strip()
            
            tool_type = self._extract_pattern(response, r'[类型|type][:：]\s*([^\n]+)')
            if tool_type:
                config['tool']['type'] = tool_type.strip().lower()
            
            description = self._extract_pattern(response, r'[描述|description][:：]\s*([^\n]+)')
            if description:
                config['tool']['description'] = description.strip()
            
            # 如果没有提取到必要信息，返回None
            if not config['tool'].get('name'):
                return None
                
            # 设置默认值
            config['tool'].setdefault('version', '1.0.0')
            config['tool'].setdefault('type', 'utility')
            config['tool'].setdefault('description', 'Generated tool')
            
            config['metadata']['author'] = 'AI Generated'
            config['metadata']['created_date'] = '2024-01-01'
            
            return config
            
        except Exception as e:
            logger.error(f"模式匹配提取失败: {e}")
            return None
    
    def _extract_pattern(self, text: str, pattern: str) -> Optional[str]:
        """提取正则表达式匹配的内容"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _clean_response(self, response: str) -> str:
        """清理响应文本"""
        # 移除常见的前缀说明
        lines = response.split('\n')
        cleaned_lines = []
        
        skip_prefixes = [
            '以下是', '下面是一个', '这里是一个', '根据要求',
            'Here is', 'Below is', 'Here\'s', 'Based on'
        ]
        
        for line in lines:
            line = line.strip()
            # 跳过说明性文字
            if any(line.startswith(prefix) for prefix in skip_prefixes):
                continue
            # 跳过空行
            if not line:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _validate_sdd_structure(self, config: Dict[str, Any]) -> bool:
        """验证SDD配置结构"""
        if not isinstance(config, dict):
            return False
        
        # 检查必需的顶层键
        required_keys = ['tool']
        if not all(key in config for key in required_keys):
            return False
        
        # 检查tool部分的必需字段
        tool_section = config['tool']
        if not isinstance(tool_section, dict):
            return False
        
        required_tool_fields = ['name', 'version', 'type', 'description']
        if not all(field in tool_section for field in required_tool_fields):
            return False
        
        # 验证工具类型
        valid_types = ['dcc', 'ue_engine', 'utility']
        if tool_section['type'] not in valid_types:
            return False
        
        return True
    
    def validate_and_enhance_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并增强SDD配置
        
        Args:
            config: 原始SDD配置
            
        Returns:
            增强后的配置
        """
        # 确保所有必需的部分都存在
        enhanced_config = config.copy()
        
        # 补充缺失的元数据
        if 'metadata' not in enhanced_config:
            enhanced_config['metadata'] = {}
        
        enhanced_config['metadata'].setdefault('author', 'AI Generated')
        enhanced_config['metadata'].setdefault('created_date', '2024-01-01')
        
        # 补充配置部分
        if 'configuration' not in enhanced_config:
            enhanced_config['configuration'] = {'parameters': []}
        
        if 'parameters' not in enhanced_config['configuration']:
            enhanced_config['configuration']['parameters'] = []
        
        # 补充执行部分
        if 'execution' not in enhanced_config:
            enhanced_config['execution'] = {
                'entry_point': 'main.py::execute',
                'dependencies': [],
                'resources': {
                    'memory_limit': '512MB',
                    'timeout': '30s'
                }
            }
        
        # 补充集成部分
        if 'integration' not in enhanced_config:
            enhanced_config['integration'] = {
                'interfaces': [
                    {
                        'name': 'Console Interface',
                        'type': 'console'
                    }
                ]
            }
        
        # 验证和标准化参数
        self._standardize_parameters(enhanced_config)
        
        # 验证依赖项
        self._validate_dependencies(enhanced_config)
        
        logger.info("SDD配置验证和增强完成")
        return enhanced_config
    
    def _standardize_parameters(self, config: Dict[str, Any]):
        """标准化参数定义"""
        parameters = config['configuration']['parameters']
        
        for param in parameters:
            if isinstance(param, dict):
                # 确保必需字段存在
                param.setdefault('type', 'string')
                param.setdefault('required', False)
                param.setdefault('description', '')
                
                # 标准化类型
                type_mapping = {
                    'str': 'string',
                    'int': 'number',
                    'float': 'number',
                    'bool': 'boolean',
                    'list': 'list',
                    'dict': 'dict'
                }
                
                if param['type'] in type_mapping:
                    param['type'] = type_mapping[param['type']]
                
                # 确保布尔值正确
                if isinstance(param.get('required'), str):
                    param['required'] = param['required'].lower() in ['true', 'yes', '1']
    
    def _validate_dependencies(self, config: Dict[str, Any]):
        """验证依赖项"""
        dependencies = config['execution'].get('dependencies', [])
        
        # 移除重复依赖
        unique_deps = list(set(dependencies))
        config['execution']['dependencies'] = unique_deps
        
        # 验证依赖格式
        valid_deps = []
        for dep in unique_deps:
            if isinstance(dep, str) and dep.strip():
                valid_deps.append(dep.strip())
        
        config['execution']['dependencies'] = valid_deps
    
    def save_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """
        保存SDD配置到文件
        
        Args:
            config: SDD配置
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"SDD配置保存成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"SDD配置保存失败: {e}")
            return False
    
    def load_config(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载SDD配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            SDD配置字典或None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if self._validate_sdd_structure(config):
                logger.info(f"SDD配置加载成功: {file_path}")
                return config
            else:
                logger.warning(f"SDD配置结构无效: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"SDD配置加载失败: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    processor = SDDProcessor()
    
    # 测试各种格式的响应
    test_responses = [
        # YAML格式
        '''tool:
  name: "MeshCleaner"
  version: "1.0.0"
  type: "dcc"
  description: "网格清理工具"''',
        
        # 带代码块的YAML
        '''```yaml
tool:
  name: "Exporter"
  version: "1.0.0"
  type: "utility"
  description: "数据导出工具"
```''',
        
        # 自然语言描述
        '''根据您的需求，我为您创建一个网格清理工具：
工具名称：VertexCleaner
类型：dcc
描述：清理重复顶点的工具''',
        
        # JSON格式
        '''{
  "tool": {
    "name": "MaterialConverter",
    "version": "1.0.0",
    "type": "ue_engine",
    "description": "材质转换工具"
  }
}'''
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n=== 测试响应 {i} ===")
        config = processor.parse_ai_response(response)
        if config:
            print("解析成功:")
            print(yaml.dump(config, default_flow_style=False, allow_unicode=True))
        else:
            print("解析失败")