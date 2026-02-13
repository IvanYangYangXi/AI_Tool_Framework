"""
AI模型接口 - 支持多种大语言模型提供商
"""

import logging
import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseModelInterface(ABC):
    """AI模型接口基类"""
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        pass


class OpenAIInterface(BaseModelInterface):
    """OpenAI模型接口"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            logger.warning("OpenAI库未安装，使用模拟响应")
            self.client = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """使用OpenAI生成响应"""
        if not self.client:
            return self._mock_response(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "你是一个专业的工具开发专家，专门帮助生成符合SDD规范的配置和代码。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI调用失败: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """模拟响应（用于测试）"""
        # 基于提示词关键词返回相应的模拟配置
        if "网格清理" in prompt or "mesh cleanup" in prompt.lower():
            return '''tool:
  name: "MeshCleaner"
  version: "1.0.0"
  type: "dcc"
  description: "Maya网格清理工具，删除重复顶点，合并接近顶点，优化拓扑"

metadata:
  author: "AI Generated"
  created_date: "2024-01-01"
  compatibility:
    - platform: "dcc"
      name: "maya"
      min_version: "2022"

configuration:
  parameters:
    - name: "tolerance"
      type: "number"
      required: false
      default: 0.001
      description: "顶点合并容差"
    - name: "delete_duplicates"
      type: "boolean"
      required: false
      default: true
      description: "是否删除重复顶点"
    - name: "optimize_topology"
      type: "boolean"
      required: false
      default: true
      description: "是否优化网格拓扑"

execution:
  entry_point: "main.py::execute"
  dependencies:
    - "pymel"
    - "numpy"
  resources:
    memory_limit: "1GB"
    timeout: "60s"

integration:
  interfaces:
    - name: "Maya Interface"
      type: "qt"'''

        elif "材质转换" in prompt or "material conversion" in prompt.lower():
            return '''tool:
  name: "MaterialConverter"
  version: "1.0.0"
  type: "ue_engine"
  description: "Unreal Engine材质转换工具，支持不同格式间转换"

metadata:
  author: "AI Generated"
  created_date: "2024-01-01"
  compatibility:
    - platform: "engine"
      name: "unreal"
      min_version: "5.0"

configuration:
  parameters:
    - name: "source_format"
      type: "string"
      required: true
      default: "obj"
      description: "源材质格式"
    - name: "target_format"
      type: "string"
      required: true
      default: "mtl"
      description: "目标材质格式"
    - name: "preserve_textures"
      type: "boolean"
      required: false
      default: true
      description: "是否保留纹理贴图"

execution:
  entry_point: "main.py::execute"
  dependencies:
    - "unrealengine"
  resources:
    memory_limit: "512MB"
    timeout: "30s"

integration:
  interfaces:
    - name: "UE Interface"
      type: "api"'''

        else:
            return '''tool:
  name: "GeneratedTool"
  version: "1.0.0"
  type: "utility"
  description: "根据描述生成的通用工具"

metadata:
  author: "AI Generated"
  created_date: "2024-01-01"
  compatibility: []

configuration:
  parameters:
    - name: "input_data"
      type: "string"
      required: false
      default: ""
      description: "输入数据"

execution:
  entry_point: "main.py::execute"
  dependencies: []
  resources:
    memory_limit: "256MB"
    timeout: "30s"

integration:
  interfaces:
    - name: "Console Interface"
      type: "console"'''


class AnthropicInterface(BaseModelInterface):
    """Anthropic Claude模型接口"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化Anthropic客户端"""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            logger.warning("Anthropic库未安装，使用模拟响应")
            self.client = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """使用Claude生成响应"""
        if not self.client:
            return self._mock_response(prompt)
        
        try:
            response = self.client.messages.create(
                model=kwargs.get('model', 'claude-3-haiku-20240307'),
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.7),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude调用失败: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """模拟响应"""
        return OpenAIInterface._mock_response(self, prompt)


class LocalModelInterface(BaseModelInterface):
    """本地模型接口（使用transformers）"""
    
    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化本地模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        except ImportError:
            logger.warning("Transformers库未安装，使用简单模板响应")
            self.model = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """使用本地模型生成响应"""
        if not self.model:
            return self._template_response(prompt)
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            outputs = self.model.generate(
                inputs,
                max_length=kwargs.get('max_length', 500),
                temperature=kwargs.get('temperature', 0.7),
                do_sample=True
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response[len(prompt):]  # 移除输入部分
        except Exception as e:
            logger.error(f"本地模型调用失败: {e}")
            return self._template_response(prompt)
    
    def _template_response(self, prompt: str) -> str:
        """基于模板的响应"""
        # 简单的关键词匹配模板系统
        if "导出" in prompt:
            return '''tool:
  name: "Exporter"
  version: "1.0.0"
  type: "utility"
  description: "数据导出工具"'''
        elif "导入" in prompt:
            return '''tool:
  name: "Importer"
  version: "1.0.0"
  type: "utility"
  description: "数据导入工具"'''
        else:
            return '''tool:
  name: "GenericTool"
  version: "1.0.0"
  type: "utility"
  description: "通用工具"'''


class ModelInterface:
    """
    AI模型接口包装器
    支持多种AI模型提供商的统一接口
    """
    
    def __init__(self, provider: str = "openai", api_key: str = None):
        """
        初始化模型接口
        
        Args:
            provider: 模型提供商 ("openai", "anthropic", "local")
            api_key: API密钥
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.interface = self._create_interface()
        self.last_prompt = ""
        self.last_response = ""
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
    
    def _create_interface(self) -> BaseModelInterface:
        """创建对应的模型接口"""
        if self.provider == "openai":
            return OpenAIInterface(self.api_key)
        elif self.provider == "anthropic":
            return AnthropicInterface(self.api_key)
        elif self.provider == "local":
            return LocalModelInterface()
        else:
            logger.warning(f"未知的提供商: {self.provider}，使用OpenAI接口")
            return OpenAIInterface(self.api_key)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        生成AI响应
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            AI生成的响应
        """
        self.last_prompt = prompt
        
        try:
            response = self.interface.generate_response(prompt, **kwargs)
            self.last_response = response
            
            logger.info(f"AI响应生成成功 (提供商: {self.provider})")
            logger.debug(f"响应长度: {len(response)} 字符")
            
            return response
            
        except Exception as e:
            logger.error(f"AI响应生成失败: {e}")
            # 返回默认响应
            default_response = self._get_default_response(prompt)
            self.last_response = default_response
            return default_response
    
    def _get_default_response(self, prompt: str) -> str:
        """获取默认响应"""
        return f"""tool:
  name: "DefaultTool"
  version: "1.0.0"
  type: "utility"
  description: "基于'{prompt[:50]}...'生成的默认工具"

metadata:
  author: "System Generated"
  created_date: "2024-01-01"

configuration:
  parameters: []

execution:
  entry_point: "main.py::execute"
  dependencies: []

integration:
  interfaces:
    - name: "Console"
      type: "console" """
    
    def get_last_interaction(self) -> Dict[str, str]:
        """获取最后一次交互记录"""
        return {
            "provider": self.provider,
            "prompt": self.last_prompt,
            "response": self.last_response
        }


# 使用示例和测试
if __name__ == "__main__":
    # 测试不同提供商的接口
    
    # 测试OpenAI接口（模拟）
    print("=== 测试OpenAI接口 ===")
    openai_interface = ModelInterface("openai", "test-key")
    response = openai_interface.generate_response("创建一个网格清理工具")
    print("响应:", response[:200] + "..." if len(response) > 200 else response)
    
    print("\n=== 测试Anthropic接口 ===")
    anthropic_interface = ModelInterface("anthropic", "test-key")
    response = anthropic_interface.generate_response("创建一个材质转换工具")
    print("响应:", response[:200] + "..." if len(response) > 200 else response)
    
    print("\n=== 测试本地模型接口 ===")
    local_interface = ModelInterface("local")
    response = local_interface.generate_response("创建一个导出工具")
    print("响应:", response[:200] + "..." if len(response) > 200 else response)