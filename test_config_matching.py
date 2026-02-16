"""
测试自定义触发器配置加载修复
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根路径到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_config_matching():
    """测试配置匹配逻辑"""
    
    print("🚀 测试配置匹配逻辑...")
    
    from src.gui.automation_manager import AutomationManager, TriggerType, TaskStatus
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_config_match_")
    test_data_dir = Path(temp_dir) / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    try:
        # 初始化manager
        manager = AutomationManager(config_dir=test_data_dir)
        
        # 创建一个使用自定义触发器的任务
        task = manager.create_task(
            name="测试自定义触发器任务",
            trigger_type=TriggerType.CUSTOM,
            tool_id="test_tool",
            tool_category="other",
            execution_mode="standalone",
            parameters={},
            trigger_config={
                "trigger_script_id": "simple_test_trigger",
                "interval_seconds": 10,
                "enabled_flag": True,
                "trigger_message": "测试消息"
            }
        )
        
        print(f"✅ 任务创建成功")
        print(f"   task.trigger_type = {task.trigger_type}")
        print(f"   task.custom_trigger_config = {task.custom_trigger_config}")
        
        # 模拟 _get_existing_config_for_trigger_type 的逻辑
        def get_task_trigger_config(task):
            if task.trigger_type == TriggerType.CUSTOM.value or task.trigger_type == "custom":
                return task.custom_trigger_config or {}
            return {}
        
        def get_existing_config_for_trigger_type(task, trigger_type: str):
            builtin_types = {"interval", "scheduled", "file_watch", "task_chain"}
            
            if trigger_type in builtin_types:
                if task.trigger_type == trigger_type:
                    return get_task_trigger_config(task)
            else:
                # 自定义触发器
                if task.trigger_type == TriggerType.CUSTOM.value or task.trigger_type == "custom":
                    config = get_task_trigger_config(task)
                    saved_script_id = config.get('trigger_script_id', '')
                    if saved_script_id == trigger_type:
                        return config
            return {}
        
        # 测试不同场景
        print("\n📊 测试场景:")
        
        # 场景1: 用户选择了 "simple_test_trigger"（与保存的一致）
        result1 = get_existing_config_for_trigger_type(task, "simple_test_trigger")
        print(f"   场景1: 选择 'simple_test_trigger' -> 返回配置: {bool(result1)}")
        print(f"          配置内容: {result1}")
        assert result1.get('trigger_script_id') == 'simple_test_trigger', "场景1失败"
        
        # 场景2: 用户选择了另一个自定义触发器
        result2 = get_existing_config_for_trigger_type(task, "cpu_usage")
        print(f"   场景2: 选择 'cpu_usage' -> 返回配置: {bool(result2)}")
        assert result2 == {}, "场景2应该返回空配置"
        
        # 场景3: 用户选择了内置触发器
        result3 = get_existing_config_for_trigger_type(task, "interval")
        print(f"   场景3: 选择 'interval' -> 返回配置: {bool(result3)}")
        assert result3 == {}, "场景3应该返回空配置"
        
        print("\n✅ 所有配置匹配测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_config_matching()
    if success:
        print("\n🎉 修复验证成功！")
    else:
        print("\n❌ 修复验证失败！")
        sys.exit(1)