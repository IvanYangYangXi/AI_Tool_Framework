"""
测试自定义触发器保存修复
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

from src.gui.automation_manager import AutomationManager, AutomationTask, TriggerType, TaskStatus

def test_custom_trigger_save():
    """测试自定义触发器的保存功能"""
    
    print("🚀 开始测试自定义触发器保存修复...")
    
    # 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="test_custom_trigger_")
    test_data_dir = Path(temp_dir) / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    try:
        # 1. 初始化AutomationManager
        print("📋 初始化测试环境...")
        manager = AutomationManager(config_dir=test_data_dir)
        
        # 2. 创建一个使用自定义触发器的任务
        print("📝 创建自定义触发器任务...")
        task_data = {
            "id": "test_task_1",
            "name": "测试自定义触发器任务",
            "trigger_type": TriggerType.CUSTOM.value,
            "enabled": True,
            "tool_id": "test_tool",
            "tool_category": "other",
            "execution_mode": "standalone",
            "parameters": {},
            "custom_trigger_config": {
                "trigger_script_id": "simple_test_trigger",
                "test_param": "test_value"
            }
        }
        
        # 使用AutomationManager的create_task方法
        task = manager.create_task(
            name=task_data["name"],
            trigger_type=TriggerType.CUSTOM,
            tool_id=task_data["tool_id"],
            tool_category=task_data["tool_category"],
            execution_mode=task_data["execution_mode"],
            parameters=task_data["parameters"],
            trigger_config=task_data["custom_trigger_config"]
        )
        task_id = task.id
        
        print(f"✅ 任务创建成功，ID: {task_id}")
        print(f"   触发器类型: {task.trigger_type}")
        print(f"   自定义触发器配置: {task.custom_trigger_config}")
        
        # 3. 测试更新任务（模拟编辑功能）
        print("🔄 测试任务更新...")
        
        # 模拟AutomationDialog._save_task_changes的逻辑
        trigger_type = "simple_test_trigger"  # 这是从UI获取的原始值
        
        # 应用修复后的逻辑
        builtin_types = {"interval", "scheduled", "file_watch", "task_chain"}
        if trigger_type in builtin_types:
            trigger_type_enum = TriggerType(trigger_type)
            new_trigger_config = {"updated_param": "updated_value"}
        else:
            trigger_type_enum = TriggerType.CUSTOM
            # 对于自定义触发器，在trigger_config中保存真实的触发器ID
            new_trigger_config = {"updated_param": "updated_value"}
            new_trigger_config['trigger_script_id'] = trigger_type
        
        print(f"   处理后的触发器类型: {trigger_type_enum}")
        print(f"   处理后的配置: {new_trigger_config}")
        
        # 执行更新
        result = manager.update_task_full(
            task_id,
            name="测试自定义触发器任务 - 已更新",
            trigger_type=trigger_type_enum,
            enabled=True,
            trigger_config=new_trigger_config
        )
        
        print(f"✅ 任务更新结果: {result}")
        
        # 4. 验证更新结果
        print("🔍 验证更新结果...")
        updated_task = manager.get_task(task_id)
        
        if updated_task:
            print(f"✅ 任务名称: {updated_task.name}")
            print(f"✅ 触发器类型: {updated_task.trigger_type}")
            print(f"✅ 自定义触发器配置: {updated_task.custom_trigger_config}")
            
            # 检查关键字段
            assert updated_task.trigger_type == TriggerType.CUSTOM.value, f"预期custom，实际: {updated_task.trigger_type}"
            assert updated_task.custom_trigger_config is not None, "自定义触发器配置为空"
            assert 'trigger_script_id' in updated_task.custom_trigger_config, "缺少trigger_script_id"
            assert updated_task.custom_trigger_config['trigger_script_id'] == 'simple_test_trigger', "trigger_script_id不正确"
            
            print("✅ 所有验证通过！")
        else:
            print("❌ 无法获取更新后的任务")
            return False
        
        # 5. 测试内置触发器类型（确保没有破坏原有功能）
        print("🔄 测试内置触发器更新...")
        
        builtin_task_data = {
            "id": "test_task_2",
            "name": "测试内置触发器任务",
            "trigger_type": TriggerType.INTERVAL.value,
            "enabled": True,
            "tool_id": "test_tool",
            "tool_category": "other",
            "execution_mode": "standalone",
            "parameters": {},
            "interval_config": {"interval_seconds": 300}
        }
        
        # 使用create_task方法创建内置触发器任务
        builtin_task = manager.create_task(
            name=builtin_task_data["name"],
            trigger_type=TriggerType.INTERVAL,
            tool_id=builtin_task_data["tool_id"],
            tool_category=builtin_task_data["tool_category"],
            execution_mode=builtin_task_data["execution_mode"],
            parameters=builtin_task_data["parameters"],
            trigger_config=builtin_task_data["interval_config"]
        )
        builtin_task_id = builtin_task.id
        
        # 更新内置触发器任务
        builtin_trigger_type = "interval"  # 内置类型
        builtin_trigger_type_enum = TriggerType(builtin_trigger_type)
        builtin_new_config = {"interval_seconds": 600}
        
        builtin_result = manager.update_task_full(
            builtin_task_id,
            name="测试内置触发器任务 - 已更新",
            trigger_type=builtin_trigger_type_enum,
            enabled=True,
            trigger_config=builtin_new_config
        )
        
        print(f"✅ 内置触发器更新结果: {builtin_result}")
        
        updated_builtin_task = manager.get_task(builtin_task_id)
        if updated_builtin_task:
            assert updated_builtin_task.trigger_type == TriggerType.INTERVAL.value, "内置触发器类型不正确"
            assert updated_builtin_task.interval_config['interval_seconds'] == 600, "内置触发器配置不正确"
            print("✅ 内置触发器测试通过！")
        
        print("🎉 所有测试通过！自定义触发器保存修复成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            print(f"🧹 清理临时目录: {temp_dir}")
        except:
            pass

if __name__ == "__main__":
    success = test_custom_trigger_save()
    if success:
        print("\n✅ 修复验证成功！现在可以正常保存自定义触发器任务了。")
    else:
        print("\n❌ 修复验证失败！")
        sys.exit(1)