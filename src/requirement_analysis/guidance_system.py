"""
智能需求引导系统 - 交互式引导用户完善需求描述
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# 修改导入路径
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from requirement_analysis.requirement_analyzer import RequirementAnalyzer, RequirementAnalysis

logger = logging.getLogger(__name__)


class GuidanceStage(Enum):
    """引导阶段"""
    WELCOME = "welcome"           # 欢迎阶段
    PLATFORM = "platform"         # 平台选择
    FUNCTION = "function"         # 功能描述
    DETAILS = "details"           # 详细信息
    PARAMETERS = "parameters"     # 参数配置
    REVIEW = "review"             # 需求复核
    COMPLETE = "complete"         # 完成阶段


@dataclass
class GuidanceState:
    """引导状态"""
    current_stage: GuidanceStage
    user_inputs: Dict[str, Any] = field(default_factory=dict)
    analysis_result: Optional[RequirementAnalysis] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)


class GuidanceSystem:
    """
    智能需求引导系统
    
    功能：
    - 分步骤引导用户提供完整需求
    - 根据用户输入动态调整引导策略
    - 实时分析需求质量并给出建议
    - 生成标准化的需求描述
    """
    
    def __init__(self, requirement_analyzer: RequirementAnalyzer):
        """
        初始化引导系统
        
        Args:
            requirement_analyzer: 需求分析器实例
        """
        self.analyzer = requirement_analyzer
        self.state = GuidanceState(current_stage=GuidanceStage.WELCOME)
        self._setup_guidance_flows()
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
    
    def _setup_guidance_flows(self):
        """设置引导流程"""
        self.guidance_flows = {
            GuidanceStage.WELCOME: self._welcome_flow,
            GuidanceStage.PLATFORM: self._platform_flow,
            GuidanceStage.FUNCTION: self._function_flow,
            GuidanceStage.DETAILS: self._details_flow,
            GuidanceStage.PARAMETERS: self._parameters_flow,
            GuidanceStage.REVIEW: self._review_flow,
            GuidanceStage.COMPLETE: self._complete_flow
        }
    
    def start_guidance(self) -> Dict[str, Any]:
        """
        开始引导流程
        
        Returns:
            引导响应字典
        """
        logger.info("开始智能需求引导流程")
        return self._execute_current_stage()
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入并推进引导流程
        
        Args:
            user_input: 用户输入
            
        Returns:
            引导响应字典
        """
        # 记录用户输入
        self.state.conversation_history.append({
            "role": "user",
            "content": user_input,
            "stage": self.state.current_stage.value
        })
        
        # 存储用户输入
        self.state.user_inputs[self.state.current_stage.value] = user_input
        
        # 执行当前阶段的处理逻辑
        response = self._execute_current_stage(user_input)
        
        # 记录系统响应
        self.state.conversation_history.append({
            "role": "assistant",
            "content": response.get("message", ""),
            "stage": self.state.current_stage.value
        })
        
        return response
    
    def _execute_current_stage(self, user_input: str = None) -> Dict[str, Any]:
        """执行当前阶段的引导逻辑"""
        stage_handler = self.guidance_flows.get(self.state.current_stage)
        if stage_handler:
            return stage_handler(user_input)
        else:
            return self._error_response("未知的引导阶段")
    
    def _welcome_flow(self, user_input: str = None) -> Dict[str, Any]:
        """欢迎阶段"""
        welcome_message = """
👋 欢迎使用智能工具需求分析系统！

我是您的需求分析助手，将帮助您完善工具开发需求。
通过几个简单的问题，我可以帮您：
• 明确工具的功能定位
• 识别遗漏的关键信息  
• 优化需求描述的清晰度
• 估算开发复杂度和时间

让我们开始吧！请简单描述您想要开发的工具：
(例如：我想做一个Maya的网格优化工具)
"""
        
        self.state.current_stage = GuidanceStage.PLATFORM
        return {
            "stage": GuidanceStage.WELCOME.value,
            "message": welcome_message.strip(),
            "next_stage": GuidanceStage.PLATFORM.value,
            "expectations": "请描述您想开发的工具",
            "options": []
        }
    
    def _platform_flow(self, user_input: str = None) -> Dict[str, Any]:
        """平台选择阶段"""
        if not user_input:
            return self._ask_question(
                GuidanceStage.PLATFORM,
                "请问您的工具主要在哪个平台上使用？",
                [
                    " Autodesk Maya",
                    " 3ds Max",
                    " Blender",
                    " Unreal Engine",
                    " 其他DCC软件",
                    " 通用工具"
                ],
                "请从上面选择或输入具体的平台名称"
            )
        
        # 分析平台信息
        platform_info = self._extract_platform_info(user_input)
        self.state.user_inputs['platform'] = platform_info
        
        # 根据平台给出针对性建议
        platform_specific_guidance = self._get_platform_guidance(platform_info['type'])
        
        message = f"""
明白了！您选择了 {platform_info['display_name']} 平台。

{platform_specific_guidance}

接下来请详细描述工具的具体功能：
"""
        
        self.state.current_stage = GuidanceStage.FUNCTION
        return {
            "stage": GuidanceStage.PLATFORM.value,
            "message": message.strip(),
            "next_stage": GuidanceStage.FUNCTION.value,
            "platform_info": platform_info
        }
    
    def _function_flow(self, user_input: str = None) -> Dict[str, Any]:
        """功能描述阶段"""
        if not user_input:
            return self._ask_question(
                GuidanceStage.FUNCTION,
                "请详细描述工具需要实现的核心功能：",
                [
                    " 数据导入/导出",
                    " 模型处理/优化",
                    " 材质/纹理处理", 
                    " 动画/绑定处理",
                    " 渲染相关功能",
                    " 自定义功能"
                ],
                "请具体说明工具做什么，解决了什么问题"
            )
        
        # 分析功能描述
        analysis = self.analyzer.analyze_requirement(user_input)
        self.state.analysis_result = analysis
        
        # 根据分析结果调整后续引导
        if analysis.quality_level in [analysis.QualityLevel.POOR, analysis.QualityLevel.FAIR]:
            # 质量较差，需要更多引导
            self.state.current_stage = GuidanceStage.DETAILS
            next_stage = GuidanceStage.DETAILS
        else:
            # 质量较好，直接进入参数阶段
            self.state.current_stage = GuidanceStage.PARAMETERS
            next_stage = GuidanceStage.PARAMETERS
        
        quality_feedback = self._generate_quality_feedback(analysis)
        
        message = f"""
感谢您的详细描述！

{quality_feedback}

让我们继续完善需求细节：
"""
        
        return {
            "stage": GuidanceStage.FUNCTION.value,
            "message": message.strip(),
            "next_stage": next_stage.value,
            "analysis": {
                "quality_score": analysis.quality_score,
                "quality_level": analysis.quality_level.value,
                "missing_elements": analysis.missing_elements,
                "recommendations": analysis.recommendations[:3]
            }
        }
    
    def _details_flow(self, user_input: str = None) -> Dict[str, Any]:
        """详细信息阶段"""
        if not user_input:
            missing_elements = self.state.analysis_result.missing_elements if self.state.analysis_result else []
            
            detail_questions = self._generate_detail_questions(missing_elements)
            
            return self._ask_question(
                GuidanceStage.DETAILS,
                "为了更好地理解您的需求，请补充以下信息：",
                detail_questions,
                "请逐一回答上述问题，或者自由描述相关细节"
            )
        
        # 更新分析结果
        combined_description = (
            self.state.user_inputs.get(GuidanceStage.FUNCTION.value, "") + 
            " " + user_input
        )
        
        updated_analysis = self.analyzer.analyze_requirement(combined_description)
        self.state.analysis_result = updated_analysis
        
        message = "感谢您的补充！现在让我们讨论工具的参数配置："
        
        self.state.current_stage = GuidanceStage.PARAMETERS
        return {
            "stage": GuidanceStage.DETAILS.value,
            "message": message,
            "next_stage": GuidanceStage.PARAMETERS.value,
            "updated_analysis": {
                "quality_improved": updated_analysis.quality_score > 
                                  (self.state.analysis_result.quality_score if self.state.analysis_result else 0)
            }
        }
    
    def _parameters_flow(self, user_input: str = None) -> Dict[str, Any]:
        """参数配置阶段"""
        if not user_input:
            return self._ask_question(
                GuidanceStage.PARAMETERS,
                "工具可能需要哪些用户可配置的参数？",
                [
                    " 输入文件路径",
                    " 输出格式选项",
                    " 处理精度设置",
                    " 批量处理选项",
                    " 性能优化参数",
                    " 暂时不考虑参数"
                ],
                "请列出重要的配置选项，或说明不需要复杂参数"
            )
        
        # 记录参数信息
        self.state.user_inputs['parameters'] = user_input
        
        message = "很好！现在让我们回顾整理整个需求："
        
        self.state.current_stage = GuidanceStage.REVIEW
        return {
            "stage": GuidanceStage.PARAMETERS.value,
            "message": message,
            "next_stage": GuidanceStage.REVIEW.value
        }
    
    def _review_flow(self, user_input: str = None) -> Dict[str, Any]:
        """需求复核阶段"""
        # 生成完整的需求描述
        complete_description = self._synthesize_complete_requirement()
        
        # 最终分析
        final_analysis = self.analyzer.analyze_requirement(complete_description)
        
        review_message = f"""
📋 需求分析总结

生成的需求描述：
---
{final_analysis.refined_description}
---

📊 分析结果：
• 质量评分：{final_analysis.quality_score:.1f}/100
• 质量等级：{final_analysis.quality_level.value.upper()}
• 预估复杂度：{final_analysis.estimated_complexity}
• 开发时间：{final_analysis.estimated_timeline}

💡 主要建议：
{chr(10).join([f"• {rec}" for rec in final_analysis.recommendations[:3]])}

您对这个需求描述满意吗？
"""
        
        self.state.current_stage = GuidanceStage.COMPLETE
        return {
            "stage": GuidanceStage.REVIEW.value,
            "message": review_message,
            "next_stage": GuidanceStage.COMPLETE.value,
            "final_description": final_analysis.refined_description,
            "final_analysis": {
                "quality_score": final_analysis.quality_score,
                "quality_level": final_analysis.quality_level.value,
                "complexity": final_analysis.estimated_complexity,
                "timeline": final_analysis.estimated_timeline,
                "recommendations": final_analysis.recommendations
            }
        }
    
    def _complete_flow(self, user_input: str = None) -> Dict[str, Any]:
        """完成阶段"""
        complete_message = """
🎉 需求分析完成！

您的完整需求描述已经准备好，可以直接用于工具开发。
如需调整或重新开始，请随时告诉我。

您可以：
1. 使用此需求描述生成工具代码
2. 导出为SDD配置文件
3. 开始工具开发流程

有什么其他需要帮助的吗？
"""
        
        return {
            "stage": GuidanceStage.COMPLETE.value,
            "message": complete_message,
            "is_complete": True,
            "final_result": self._get_final_result()
        }
    
    def _ask_question(self, stage: GuidanceStage, question: str, 
                     options: List[str], hint: str = "") -> Dict[str, Any]:
        """通用提问方法"""
        formatted_options = [f"{i+1}. {opt}" for i, opt in enumerate(options)]
        
        message = f"""
{question}

可选答案：
{chr(10).join(formatted_options)}

{hint if hint else ''}
"""
        
        return {
            "stage": stage.value,
            "message": message.strip(),
            "options": options,
            "expects_input": True
        }
    
    def _extract_platform_info(self, user_input: str) -> Dict[str, str]:
        """提取平台信息"""
        platform_mapping = {
            'maya': {'type': 'dcc', 'name': 'maya', 'display_name': 'Autodesk Maya'},
            '3ds max': {'type': 'dcc', 'name': '3ds_max', 'display_name': '3ds Max'},
            'blender': {'type': 'dcc', 'name': 'blender', 'display_name': 'Blender'},
            'unreal': {'type': 'ue', 'name': 'unreal_engine', 'display_name': 'Unreal Engine'},
            'ue': {'type': 'ue', 'name': 'unreal_engine', 'display_name': 'Unreal Engine'},
            '虚幻': {'type': 'ue', 'name': 'unreal_engine', 'display_name': 'Unreal Engine'}
        }
        
        user_input_lower = user_input.lower()
        for key, info in platform_mapping.items():
            if key in user_input_lower:
                return info
        
        return {'type': 'utility', 'name': 'generic', 'display_name': '通用工具'}
    
    def _get_platform_guidance(self, platform_type: str) -> str:
        """获取平台特定的引导建议"""
        guidance_map = {
            'dcc': "📌 DCC工具通常涉及模型处理、动画、材质等功能",
            'ue': "📌 UE引擎工具多用于资源管理、关卡编辑、蓝图交互等",
            'utility': "📌 通用工具可以跨平台使用，功能更加灵活"
        }
        return guidance_map.get(platform_type, "📌 请详细说明工具的具体应用场景")
    
    def _generate_quality_feedback(self, analysis: RequirementAnalysis) -> str:
        """生成质量反馈"""
        if analysis.quality_level == analysis.QualityLevel.EXCELLENT:
            return "✅ 需求描述非常完整清晰！"
        elif analysis.quality_level == analysis.QualityLevel.GOOD:
            return "👍 需求描述比较完整，稍作完善就很好了。"
        else:
            return f"📝 需求还需要一些补充，发现了{len(analysis.missing_elements)}个可以完善的地方。"
    
    def _generate_detail_questions(self, missing_elements: List[str]) -> List[str]:
        """根据缺失元素生成详细问题"""
        question_mapping = {
            'tool_name': "工具的具体名称是什么？",
            'purpose': "这个工具主要解决什么问题？",
            'target_platform': "除了刚才提到的平台，还有其他兼容性要求吗？",
            'input_type': "工具需要处理什么样的输入数据？",
            'output_format': "期望的输出结果是什么格式？",
            'parameters': "有哪些重要的配置选项？",
            'constraints': "有什么特殊的性能或功能限制吗？"
        }
        
        questions = []
        for element in missing_elements[:3]:  # 限制问题数量
            if element in question_mapping:
                questions.append(question_mapping[element])
        
        return questions or ["请补充更多关于工具功能的详细信息"]
    
    def _synthesize_complete_requirement(self) -> str:
        """合成完整的需求描述"""
        parts = []
        
        # 添加平台信息
        if 'platform' in self.state.user_inputs:
            platform_name = self.state.user_inputs['platform'].get('display_name', '')
            parts.append(f"开发一个用于{platform_name}的工具")
        
        # 添加功能描述
        function_desc = self.state.user_inputs.get(GuidanceStage.FUNCTION.value, "")
        if function_desc:
            parts.append(function_desc)
        
        # 添加详细信息
        details = self.state.user_inputs.get(GuidanceStage.DETAILS.value, "")
        if details:
            parts.append(details)
        
        # 添加参数信息
        parameters = self.state.user_inputs.get('parameters', "")
        if parameters:
            parts.append(f"参数配置：{parameters}")
        
        return "，".join(parts) if parts else "待完善的需求"
    
    def _get_final_result(self) -> Dict[str, Any]:
        """获取最终结果"""
        return {
            "complete_description": self._synthesize_complete_requirement(),
            "conversation_history": self.state.conversation_history,
            "user_inputs": self.state.user_inputs,
            "analysis_result": self.state.analysis_result
        }
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            "stage": "error",
            "message": f"❌ {error_message}",
            "error": True
        }
    
    def reset(self):
        """重置引导状态"""
        self.state = GuidanceState(current_stage=GuidanceStage.WELCOME)
        logger.info("引导系统已重置")


# 使用示例
if __name__ == "__main__":
    # 创建需求分析器和引导系统
    analyzer = RequirementAnalyzer()
    guidance = GuidanceSystem(analyzer)
    
    # 开始引导
    response = guidance.start_guidance()
    print("引导开始:")
    print(response["message"])
    
    # 模拟用户交互
    test_inputs = [
        "我想做一个Maya的网格清理工具",
        "Maya",
        "清理重复顶点，优化网格拓扑",
        "处理OBJ和FBX格式的模型文件",
        "容差值可调，支持批量处理"
    ]
    
    for user_input in test_inputs:
        print(f"\n用户输入: {user_input}")
        response = guidance.process_user_input(user_input)
        print(f"系统响应: {response['message']}")
        
        if response.get("is_complete"):
            break