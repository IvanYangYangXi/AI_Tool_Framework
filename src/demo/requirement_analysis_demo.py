"""
智能需求分析专用演示
展示AI驱动的需求分析和引导功能
"""

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入所需模块
sys.path.insert(0, str(project_root / "src"))

from requirement_analysis.requirement_analyzer import RequirementAnalyzer
from requirement_analysis.guidance_system import GuidanceSystem

def setup_demo_logging():
    """设置演示日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('requirement_analysis_demo.log', encoding='utf-8')
        ]
    )

def demo_static_analysis():
    """演示静态需求分析"""
    print("=" * 60)
    print("智能需求分析演示 - 静态分析")
    print("=" * 60)
    
    # 创建分析器
    print("\n1. 初始化需求分析器...")
    analyzer = RequirementAnalyzer(ai_provider="openai")
    print("✓ 需求分析器初始化完成")
    
    # 测试用例
    test_cases = [
        {
            "description": "做一个Maya的工具，能把模型优化一下",
            "name": "模糊需求示例"
        },
        {
            "description": "创建一个Maya网格清理工具，删除重复顶点，合并距离小于0.001的顶点，支持OBJ和FBX格式，输出优化后的网格文件",
            "name": "较完整需求示例"
        },
        {
            "description": "开发Unreal Engine的材质转换插件，将OBJ材质转换为UE材质球，支持纹理贴图映射，提供批量处理功能，参数包括：容差值(0.001-0.1)、输出路径、材质命名规则",
            "name": "详细需求示例"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n2.{i} 分析测试用例: {test_case['name']}")
        print(f"   需求描述: {test_case['description']}")
        
        # 执行分析
        result = analyzer.analyze_requirement(test_case['description'])
        
        print(f"   质量得分: {result.quality_score:.1f}/100")
        print(f"   质量等级: {result.quality_level.value.upper()}")
        print(f"   覆盖类别: {[cat.value for cat in result.categories]}")
        print(f"   缺失元素: {result.missing_elements}")
        print(f"   模糊表述: {len(result.ambiguities)} 处")
        print(f"   复杂度预估: {result.estimated_complexity}")
        print(f"   时间预估: {result.estimated_timeline}")
        
        if result.recommendations:
            print("   改进建议:")
            for j, rec in enumerate(result.recommendations[:3], 1):
                print(f"     {j}. {rec}")
        
        print(f"   精炼描述: {result.refined_description}")

def demo_interactive_guidance():
    """演示交互式引导"""
    print("\n" + "=" * 60)
    print("智能需求分析演示 - 交互式引导")
    print("=" * 60)
    
    # 创建分析器和引导系统
    print("\n1. 初始化引导系统...")
    analyzer = RequirementAnalyzer(ai_provider="openai")
    guidance = GuidanceSystem(analyzer)
    print("✓ 引导系统初始化完成")
    
    # 开始引导
    print("\n2. 启动交互引导...")
    response = guidance.start_guidance()
    print("引导开始:")
    print(format_message(response['message']))
    
    # 模拟用户交互流程
    interaction_flow = [
        ("我想做一个Maya的网格清理工具", "描述工具功能"),
        ("Maya", "选择目标平台"),
        ("清理重复顶点，合并接近的顶点，优化网格拓扑结构", "详细功能描述"),
        ("处理OBJ和FBX格式的3D模型文件", "输入输出格式"),
        ("容差值可调(0.001-0.1)，支持批量处理，可以预览结果", "参数和特性")
    ]
    
    for i, (user_input, description) in enumerate(interaction_flow, 1):
        print(f"\n--- 第{i}轮交互: {description} ---")
        print(f"用户输入: {user_input}")
        
        response = guidance.process_user_input(user_input)
        print("系统响应:")
        print(format_message(response['message']))
        
        if response.get('is_complete'):
            print("✓ 需求引导完成")
            break
    
    # 显示最终结果
    final_result = guidance._get_final_result()
    print("\n" + "=" * 40)
    print("最终需求分析结果:")
    print("=" * 40)
    print(f"完整需求描述:\n{final_result['complete_description']}")
    
    if final_result['analysis_result']:
        analysis = final_result['analysis_result']
        print(f"\n质量分析:")
        print(f"  • 最终得分: {analysis.quality_score:.1f}/100")
        print(f"  • 质量等级: {analysis.quality_level.value.upper()}")
        print(f"  • 主要建议: {analysis.recommendations[0] if analysis.recommendations else '无'}")

def demo_quality_comparison():
    """演示需求质量对比"""
    print("\n" + "=" * 60)
    print("需求质量对比分析")
    print("=" * 60)
    
    analyzer = RequirementAnalyzer(ai_provider="openai")
    
    # 对比不同质量的需求描述
    quality_samples = [
        {
            "level": "Poor - 模糊描述",
            "description": "做个工具处理模型"
        },
        {
            "level": "Fair - 基本描述", 
            "description": "Maya工具，优化网格"
        },
        {
            "level": "Good - 较完整描述",
            "description": "Maya网格清理工具，删除重复顶点，合并接近顶点"
        },
        {
            "level": "Excellent - 详细描述",
            "description": "开发Maya网格优化插件，功能包括：1)删除重复顶点(容差<0.001)；2)合并距离小于0.01的顶点；3)重建网格法线；4)支持OBJ/FBX格式；5)提供GUI界面；6)批量处理模式；参数：容差值、处理模式、输出选项"
        }
    ]
    
    print("\n质量评分对比:")
    print("-" * 80)
    print(f"{'描述质量':<20} {'得分':<8} {'等级':<10} {'缺失元素':<15} {'建议数量':<10}")
    print("-" * 80)
    
    for sample in quality_samples:
        result = analyzer.analyze_requirement(sample['description'])
        print(f"{sample['level']:<20} {result.quality_score:<8.1f} {result.quality_level.value.upper():<10} "
              f"{len(result.missing_elements):<15} {len(result.recommendations):<10}")

def format_message(message):
    """格式化消息显示，处理特殊字符"""
    if isinstance(message, str):
        # 简单处理，实际项目中可能需要更复杂的字符处理
        lines = message.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip():
                formatted_lines.append(f"  {line}")
        return '\n'.join(formatted_lines)
    return str(message)

def main():
    """主演示函数"""
    setup_demo_logging()
    
    try:
        print("开始智能需求分析演示...\n")
        
        # 静态分析演示
        demo_static_analysis()
        
        # 交互引导演示
        demo_interactive_guidance()
        
        # 质量对比演示
        demo_quality_comparison()
        
        print("\n" + "=" * 60)
        print("智能需求分析演示完成！")
        print("=" * 60)
        print("\n核心功能总结:")
        print("✓ 需求质量自动评估")
        print("✓ 缺失元素智能识别")
        print("√ 模糊表述检测")
        print("✓ 改进建议生成")
        print("✓ 交互式需求引导")
        print("✓ 需求描述精炼")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        logging.exception("演示异常")

if __name__ == "__main__":
    main()