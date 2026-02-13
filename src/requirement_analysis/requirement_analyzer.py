"""
智能需求分析器 - 分析和优化工具需求描述
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 修改导入路径
import sys
from pathlib import Path
# 添加src目录到路径
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from ai_nlp.model_interface import ModelInterface
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class RequirementQuality(Enum):
    """需求质量等级"""
    EXCELLENT = "excellent"    # 优秀 - 完整清晰的需求
    GOOD = "good"             # 良好 - 基本完整的需求
    FAIR = "fair"             # 一般 - 需要补充的需求
    POOR = "poor"             # 较差 - 需要大量完善的模糊需求


class AnalysisCategory(Enum):
    """分析类别"""
    FUNCTIONALITY = "functionality"     # 功能性需求
    TECHNICAL = "technical"             # 技术需求
    USABILITY = "usability"             # 可用性需求
    CONSTRAINTS = "constraints"         # 约束条件
    INTEGRATION = "integration"         # 集成需求


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    original_description: str
    quality_score: float  # 0-100分
    quality_level: RequirementQuality
    categories: List[AnalysisCategory] = field(default_factory=list)
    missing_elements: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    extracted_info: Dict[str, Any] = field(default_factory=dict)
    refined_description: str = ""
    estimated_complexity: str = "medium"  # low/medium/high
    estimated_timeline: str = "2-3 days"


class RequirementAnalyzer:
    """
    智能需求分析器
    
    功能：
    - 分析需求描述的完整性和清晰度
    - 识别缺失的关键要素
    - 检测模糊和歧义表述
    - 提供优化建议
    - 生成精炼的需求描述
    """
    
    def __init__(self, ai_provider: str = "openai", api_key: str = None):
        """
        初始化需求分析器
        
        Args:
            ai_provider: AI模型提供商
            api_key: API密钥
        """
        self.model_interface = ModelInterface(ai_provider, api_key)
        self.config_manager = ConfigManager()
        self._setup_logging()
        self._load_analysis_templates()
        
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
    
    def _load_analysis_templates(self):
        """加载分析模板"""
        self.analysis_prompts = {
            "completeness": self._create_completeness_prompt(),
            "clarity": self._create_clarity_prompt(),
            "extraction": self._create_extraction_prompt(),
            "refinement": self._create_refinement_prompt()
        }
    
    def analyze_requirement(self, description: str) -> RequirementAnalysis:
        """
        分析工具需求描述
        
        Args:
            description: 需求描述文本
            
        Returns:
            需求分析结果
        """
        logger.info(f"开始分析需求: {description[:50]}...")
        
        analysis = RequirementAnalysis(
            original_description=description,
            quality_score=0.0,
            quality_level=RequirementQuality.POOR
        )
        
        try:
            # 1. 完整性分析
            completeness_result = self._analyze_completeness(description)
            analysis.missing_elements = completeness_result.get('missing_elements', [])
            
            # 2. 清晰度分析
            clarity_result = self._analyze_clarity(description)
            analysis.ambiguities = clarity_result.get('ambiguities', [])
            
            # 3. 信息提取
            extraction_result = self._extract_information(description)
            analysis.extracted_info = extraction_result.get('info', {})
            analysis.categories = extraction_result.get('categories', [])
            
            # 4. 质量评分
            analysis.quality_score = self._calculate_quality_score(
                len(analysis.missing_elements),
                len(analysis.ambiguities),
                len(analysis.categories)
            )
            analysis.quality_level = self._determine_quality_level(analysis.quality_score)
            
            # 5. 生成建议
            analysis.recommendations = self._generate_recommendations(
                analysis.missing_elements,
                analysis.ambiguities,
                analysis.categories
            )
            
            # 6. 需求精炼
            analysis.refined_description = self._refine_requirement(description, analysis)
            
            # 7. 复杂度和时间估算
            analysis.estimated_complexity = self._estimate_complexity(analysis)
            analysis.estimated_timeline = self._estimate_timeline(analysis)
            
            logger.info(f"需求分析完成 - 质量等级: {analysis.quality_level.value}, 得分: {analysis.quality_score}")
            
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            analysis.quality_score = 0
            analysis.quality_level = RequirementQuality.POOR
            analysis.recommendations = ["需求分析过程中出现错误，请重新描述需求"]
        
        return analysis
    
    def _analyze_completeness(self, description: str) -> Dict[str, Any]:
        """分析需求完整性"""
        # 检查必需元素
        required_elements = {
            'tool_name': r'(?:工具|插件|功能).*?(?:名称|叫)',
            'purpose': r'(?:用来|用于|目的是|功能是)',
            'target_platform': r'(?:maya|3ds|max|blender|unreal|ue|虚幻|dcc)',
            'input_type': r'(?:输入|处理|操作|导入).*?(?:什么|哪些|类型)',
            'output_format': r'(?:输出|导出|生成|保存).*?(?:格式|类型|为什么)',
            'parameters': r'(?:参数|选项|设置|配置)',
            'constraints': r'(?:限制|要求|必须|不能)'
        }
        
        missing_elements = []
        found_elements = []
        
        for element, pattern in required_elements.items():
            if re.search(pattern, description, re.IGNORECASE):
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        # 使用AI进行深度分析
        ai_prompt = self.analysis_prompts["completeness"].format(
            description=description,
            found_elements=", ".join(found_elements)
        )
        
        try:
            ai_response = self.model_interface.generate_response(ai_prompt)
            # 解析AI响应中的额外缺失元素
            additional_missing = self._parse_missing_elements(ai_response)
            missing_elements.extend(additional_missing)
        except Exception as e:
            logger.warning(f"AI完整性分析失败: {e}")
        
        return {
            "missing_elements": list(set(missing_elements)),
            "found_elements": found_elements,
            "completeness_ratio": len(found_elements) / len(required_elements)
        }
    
    def _analyze_clarity(self, description: str) -> Dict[str, Any]:
        """分析需求清晰度"""
        ambiguities = []
        
        # 检查模糊表述
        ambiguity_patterns = [
            (r'等等|之类的|差不多|大概', '表述过于宽泛'),
            (r'优化|改进|增强', '缺乏具体指标'),
            (r'快速|高效|简单', '缺少量化标准'),
            (r'支持.*?功能', '功能范围不明确'),
            (r'可以.*?也可以', '逻辑关系不清')
        ]
        
        for pattern, description in ambiguity_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                ambiguities.append({
                    "text": match.group(),
                    "position": match.span(),
                    "issue": description
                })
        
        # 使用AI分析清晰度
        clarity_prompt = self.analysis_prompts["clarity"].format(description=description)
        
        try:
            ai_response = self.model_interface.generate_response(clarity_prompt)
            ai_ambiguities = self._parse_clarity_issues(ai_response)
            ambiguities.extend(ai_ambiguities)
        except Exception as e:
            logger.warning(f"AI清晰度分析失败: {e}")
        
        return {
            "ambiguities": ambiguities,
            "clarity_score": max(0, 100 - len(ambiguities) * 10)
        }
    
    def _extract_information(self, description: str) -> Dict[str, Any]:
        """提取需求关键信息"""
        extracted_info = {}
        categories = []
        
        # 提取工具类型
        if re.search(r'maya|玛雅', description, re.IGNORECASE):
            extracted_info['tool_type'] = 'dcc'
            extracted_info['platform'] = 'maya'
            categories.append(AnalysisCategory.TECHNICAL)
        elif re.search(r'3ds|3ds max', description, re.IGNORECASE):
            extracted_info['tool_type'] = 'dcc'
            extracted_info['platform'] = '3ds_max'
            categories.append(AnalysisCategory.TECHNICAL)
        elif re.search(r'blender', description, re.IGNORECASE):
            extracted_info['tool_type'] = 'dcc'
            extracted_info['platform'] = 'blender'
            categories.append(AnalysisCategory.TECHNICAL)
        elif re.search(r'unreal|ue|虚幻', description, re.IGNORECASE):
            extracted_info['tool_type'] = 'ue_engine'
            extracted_info['platform'] = 'unreal_engine'
            categories.append(AnalysisCategory.INTEGRATION)
        else:
            extracted_info['tool_type'] = 'utility'
            categories.append(AnalysisCategory.FUNCTIONALITY)
        
        # 提取功能关键词
        functionality_keywords = [
            ('export', '导出'), ('import', '导入'), ('convert', '转换'),
            ('optimize', '优化'), ('cleanup', '清理'), ('generate', '生成'),
            ('animate', '动画'), ('render', '渲染'), ('simulate', '模拟')
        ]
        
        found_functions = []
        for eng, chn in functionality_keywords:
            if re.search(f'{eng}|{chn}', description, re.IGNORECASE):
                found_functions.append(eng)
                categories.append(AnalysisCategory.FUNCTIONALITY)
        
        extracted_info['functions'] = found_functions
        
        # 提取技术要求
        if re.search(r'api|sdk|插件接口', description, re.IGNORECASE):
            categories.append(AnalysisCategory.INTEGRATION)
        
        if re.search(r'性能|速度|内存', description, re.IGNORECASE):
            categories.append(AnalysisCategory.TECHNICAL)
        
        if re.search(r'用户界面|ui|操作简便', description, re.IGNORECASE):
            categories.append(AnalysisCategory.USABILITY)
        
        return {
            "info": extracted_info,
            "categories": list(set(categories))
        }
    
    def _calculate_quality_score(self, missing_count: int, ambiguity_count: int, 
                               category_count: int) -> float:
        """计算需求质量分数"""
        # 基础分：100分
        score = 100.0
        
        # 扣分项
        score -= missing_count * 15      # 缺失元素扣分
        score -= ambiguity_count * 10    # 模糊表述扣分
        score += category_count * 5      # 覆盖面加分
        
        # 确保分数在合理范围内
        return max(0, min(100, score))
    
    def _determine_quality_level(self, score: float) -> RequirementQuality:
        """确定质量等级"""
        if score >= 85:
            return RequirementQuality.EXCELLENT
        elif score >= 70:
            return RequirementQuality.GOOD
        elif score >= 50:
            return RequirementQuality.FAIR
        else:
            return RequirementQuality.POOR
    
    def _generate_recommendations(self, missing_elements: List[str], 
                                ambiguities: List[Any], 
                                categories: List[AnalysisCategory]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于缺失元素的建议
        element_suggestions = {
            'tool_name': '请明确工具的具体名称或功能定位',
            'purpose': '请说明工具的主要用途和解决的问题',
            'target_platform': '请指定目标软件平台（如Maya、3ds Max、Unreal Engine等）',
            'input_type': '请描述工具处理的输入数据类型和格式',
            'output_format': '请说明期望的输出结果格式',
            'parameters': '请列出重要的配置参数和选项',
            'constraints': '请说明任何特殊限制或要求'
        }
        
        for element in missing_elements:
            if element in element_suggestions:
                recommendations.append(element_suggestions[element])
        
        # 基于模糊表述的建议
        if ambiguities:
            recommendations.append('请使用更具体的表述，避免使用"优化"、"增强"等模糊词汇')
            recommendations.append('建议添加量化指标，如"处理速度提升50%"、"支持1000个对象"等')
        
        # 基于类别的建议
        if AnalysisCategory.TECHNICAL not in categories:
            recommendations.append('建议补充技术实现方面的考虑')
        
        if AnalysisCategory.USABILITY not in categories:
            recommendations.append('建议考虑用户界面和操作体验设计')
        
        # AI增强建议
        if recommendations:
            ai_prompt = f"""
基于以下需求分析结果，提供具体的改进建议：

缺失元素: {', '.join(missing_elements)}
模糊表述: {len(ambiguities)}处
覆盖类别: {', '.join([cat.value for cat in categories])}

请提供3-5条具体、可操作的改进建议。
"""
            
            try:
                ai_response = self.model_interface.generate_response(ai_prompt)
                ai_recommendations = self._parse_recommendations(ai_response)
                recommendations.extend(ai_recommendations)
            except Exception as e:
                logger.warning(f"AI建议生成失败: {e}")
        
        return list(set(recommendations))[:5]  # 限制建议数量
    
    def _refine_requirement(self, original_description: str, 
                          analysis: RequirementAnalysis) -> str:
        """精炼需求描述"""
        refinement_prompt = self.analysis_prompts["refinement"].format(
            original=original_description,
            missing_elements=", ".join(analysis.missing_elements),
            ambiguities=len(analysis.ambiguities),
            categories=", ".join([cat.value for cat in analysis.categories])
        )
        
        try:
            refined = self.model_interface.generate_response(refinement_prompt)
            return refined.strip()
        except Exception as e:
            logger.warning(f"需求精炼失败: {e}")
            return original_description  # 返回原文案作为后备
    
    def _estimate_complexity(self, analysis: RequirementAnalysis) -> str:
        """估算实现复杂度"""
        complexity_factors = {
            'missing_elements': len(analysis.missing_elements),
            'ambiguities': len(analysis.ambiguities),
            'categories': len(analysis.categories),
            'quality_score': analysis.quality_score
        }
        
        # 简单的复杂度判断逻辑
        if complexity_factors['quality_score'] > 80 and complexity_factors['categories'] >= 3:
            return "high"
        elif complexity_factors['quality_score'] > 60:
            return "medium"
        else:
            return "low"
    
    def _estimate_timeline(self, analysis: RequirementAnalysis) -> str:
        """估算开发时间"""
        complexity = analysis.estimated_complexity
        
        timeline_map = {
            "low": "1-2天",
            "medium": "3-5天", 
            "high": "1-2周"
        }
        
        return timeline_map.get(complexity, "3-5天")
    
    def _create_completeness_prompt(self) -> str:
        """创建完整性分析提示词"""
        return """
请分析以下工具需求描述的完整性：

描述: {description}

已识别的元素: {found_elements}

请指出描述中缺失的重要元素，特别是：
1. 工具的具体功能和用途
2. 目标平台和兼容性要求
3. 输入输出格式和数据类型
4. 关键参数和配置选项
5. 性能要求和约束条件

只列出缺失的元素，每行一个。
"""
    
    def _create_clarity_prompt(self) -> str:
        """创建清晰度分析提示词"""
        return """
请分析以下需求描述的清晰度问题：

描述: {description}

请找出其中模糊、不明确或需要进一步澄清的表述，包括：
1. 过于宽泛的描述
2. 缺乏具体指标的要求
3. 逻辑关系不清楚的地方
4. 术语使用不准确的情况

对每个问题，请指出具体的文本位置和改进建议。
"""
    
    def _create_extraction_prompt(self) -> str:
        """创建信息提取提示词"""
        return """
从以下工具需求描述中提取关键信息：

描述: {description}

请提取：
1. 工具类型（DCC工具、UE引擎工具、通用工具）
2. 目标平台
3. 核心功能关键词
4. 技术要求
5. 用户体验要求

以结构化格式输出提取的信息。
"""
    
    def _create_refinement_prompt(self) -> str:
        """创建需求精炼提示词"""
        return """
请基于以下分析结果，将原始需求描述精炼为更完整、清晰的版本：

原始描述: {original}

分析结果:
- 缺失元素: {missing_elements}
- 模糊表述数量: {ambiguities}
- 覆盖类别: {categories}

要求：
1. 补充缺失的关键信息
2. 澄清模糊的表述
3. 保持原意的同时提高完整性和清晰度
4. 使用专业、准确的术语

输出精炼后的需求描述：
"""
    
    def _parse_missing_elements(self, response: str) -> List[str]:
        """解析缺失元素"""
        elements = []
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('1.', '2.', '3.')):
                elements.append(line)
        return elements[:5]  # 限制数量
    
    def _parse_clarity_issues(self, response: str) -> List[Dict[str, Any]]:
        """解析清晰度问题"""
        issues = []
        # 简单解析，实际项目中可能需要更复杂的处理
        if '模糊' in response or '不明确' in response:
            issues.append({
                "text": "部分内容表述模糊",
                "issue": "需要更具体的描述"
            })
        return issues
    
    def _parse_recommendations(self, response: str) -> List[str]:
        """解析AI建议"""
        recommendations = []
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # 提取建议内容
                content = re.sub(r'^[0-9\-\.]+\s*', '', line)
                if content:
                    recommendations.append(content)
        return recommendations[:3]  # 限制数量


# 使用示例
if __name__ == "__main__":
    # 创建分析器
    analyzer = RequirementAnalyzer()
    
    # 测试需求分析
    test_description = "做一个Maya的工具，能把模型优化一下"
    
    result = analyzer.analyze_requirement(test_description)
    
    print(f"原始描述: {result.original_description}")
    print(f"质量得分: {result.quality_score}")
    print(f"质量等级: {result.quality_level.value}")
    print(f"缺失元素: {result.missing_elements}")
    print(f"模糊表述: {len(result.ambiguities)}处")
    print(f"建议: {result.recommendations}")
    print(f"精炼描述: {result.refined_description}")