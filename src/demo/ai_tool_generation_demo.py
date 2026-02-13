"""
AI工具生成演示 - 展示如何使用自然语言生成工具
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_nlp import AIToolGenerator
import logging

def setup_demo_logging():
    """设置演示日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ai_tool_generation_demo.log', encoding='utf-8')
        ]
    )

def demo_basic_generation():
    """演示基本的AI工具生成"""
    print("=" * 60)
    print("AI驱动工具生成演示")
    print("=" * 60)
    
    # 创建AI工具生成器
    print("\n1. 初始化AI工具生成器...")
    generator = AIToolGenerator(model_provider="openai")  # 使用模拟模式
    print("✓ AI工具生成器初始化完成")
    
    # 测试用例1：网格清理工具
    print("\n2. 生成网格清理工具...")
    description1 = "创建一个Maya的网格清理工具，能够删除重复顶点，合并距离很近的顶点，优化网格拓扑结构，支持设置容差参数"
    
    result1 = generator.generate_tool_from_description(
        description1, 
        output_dir="./generated_tools"
    )
    
    print(f"生成结果: {'✓ 成功' if result1.success else '✗ 失败'}")
    if result1.success:
        print(f"工具名称: {result1.tool_name}")
        print(f"生成文件数: {len(result1.generated_files)}")
        print(f"配置文件: {result1.config_file}")
        print("\n生成的文件:")
        for file_path in result1.generated_files:
            print(f"  - {file_path}")
    
    # 测试用例2：材质转换工具
    print("\n3. 生成材质转换工具...")
    description2 = "创建一个Unreal Engine的材质转换工具，支持OBJ格式到MTL格式的转换，能够保留纹理坐标和材质属性"
    
    result2 = generator.generate_tool_from_description(
        description2,
        output_dir="./generated_tools"
    )
    
    print(f"生成结果: {'✓ 成功' if result2.success else '✗ 失败'}")
    if result2.success:
        print(f"工具名称: {result2.tool_name}")
        print(f"生成文件数: {len(result2.generated_files)}")
    
    # 显示执行说明
    if result1.success:
        print("\n4. 工具使用说明:")
        print(result1.execution_instructions[:500] + "..." if len(result1.execution_instructions) > 500 else result1.execution_instructions)
    
    return [result1, result2]

def demo_advanced_features():
    """演示高级功能"""
    print("\n" + "=" * 60)
    print("高级功能演示")
    print("=" * 60)
    
    generator = AIToolGenerator(model_provider="local")  # 使用本地模型
    
    # 复杂工具生成
    print("\n1. 生成复杂的数据处理工具...")
    complex_description = """
    创建一个综合的数据处理工具，具有以下功能：
    1. 支持CSV、JSON、Excel多种格式的导入导出
    2. 提供数据清洗功能（去重、空值处理、格式标准化）
    3. 支持基本的数据分析统计
    4. 可视化数据图表生成功能
    5. 批量处理能力
    参数要求包括：输入文件路径、输出格式、清洗选项、图表类型等
    """
    
    result = generator.generate_tool_from_description(
        complex_description,
        output_dir="./generated_tools"
    )
    
    print(f"生成结果: {'✓ 成功' if result.success else '✗ 失败'}")
    if result.success:
        print(f"工具名称: {result.tool_name}")
        print("AI使用的提示词:")
        print(result.ai_prompt_used[:300] + "..." if len(result.ai_prompt_used) > 300 else result.ai_prompt_used)

def demo_interactive_mode():
    """演示交互模式"""
    print("\n" + "=" * 60)
    print("交互式工具生成")
    print("=" * 60)
    
    generator = AIToolGenerator(model_provider="anthropic")  # 使用另一个提供商
    
    while True:
        print("\n请输入您想要生成的工具描述（输入'quit'退出）:")
        user_input = input("> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            print("请输入有效的描述")
            continue
        
        print(f"\n正在生成工具: {user_input[:50]}...")
        result = generator.generate_tool_from_description(
            user_input,
            output_dir="./generated_tools/user_generated"
        )
        
        if result.success:
            print(f"✓ 工具生成成功: {result.tool_name}")
            print(f"生成了 {len(result.generated_files)} 个文件")
            print(f"配置文件位置: {result.config_file}")
            
            # 显示简要的使用说明
            first_lines = result.execution_instructions.split('\n')[:10]
            print("\n使用说明预览:")
            for line in first_lines:
                if line.strip():
                    print(f"  {line}")
            print("  ...")
        else:
            print(f"✗ 工具生成失败: {result.validation_results}")

def main():
    """主演示函数"""
    setup_demo_logging()
    
    try:
        print("开始AI工具生成演示...\n")
        
        # 基本功能演示
        basic_results = demo_basic_generation()
        
        # 高级功能演示
        demo_advanced_features()
        
        # 交互模式演示
        demo_interactive_mode()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n生成的工具可以在 ./generated_tools/ 目录中找到")
        print("每个工具都包含完整的源代码、配置文件和使用说明")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        logging.exception("演示异常")

if __name__ == "__main__":
    main()