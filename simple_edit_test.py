#!/usr/bin/env python3
"""
直接测试编辑任务修复 - 简化版本
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

# 添加项目根路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.gui.automation_manager import AutomationManager, AutomationTask, TriggerType
from src.gui.automation_dialog import AutomationDialog


def test_simple():
    """简单直接测试"""
    
    print("🧪 简单测试开始")
    
    # 创建临时任务目录
    tasks_dir = project_root / "temp_test"
    tasks_dir.mkdir(exist_ok=True)
    
    # 创建自动化管理器实例
    manager = AutomationManager(
        config_dir=tasks_dir,
        execute_callback=None
    )
    
    # 手动创建一个测试任务
    test_task = AutomationTask(
        id="simple_test",
        name="简单测试任务", 
        trigger_type=TriggerType.INTERVAL.value,
        tool_id="test_tool",
        tool_category="maya",
        interval_config={"interval_value": 15, "interval_unit": "minutes"}
    )
    
    # 直接添加到管理器
    manager.tasks[test_task.id] = test_task
    manager._save_tasks()
    
    print(f"✅ 手动创建了任务: {test_task.name}")
    print(f"   管理器中的任务数量: {len(manager.get_all_tasks())}")
    
    # 创建GUI
    root = tk.Tk()
    root.title("简单编辑测试")
    root.geometry("900x600")
    
    # 创建对话框
    dialog = AutomationDialog(
        root,
        automation_manager=manager,
        tools_cache={},
        get_tool_callback=None
    )
    
    print("✅ 对话框已创建")
    print("   现在应该能看到'简单测试任务'在列表中")
    print("   请双击任务进行编辑测试")
    
    def cleanup():
        import shutil
        shutil.rmtree(tasks_dir, ignore_errors=True)
        print("🗑️  临时文件已清理")
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", cleanup)
    
    root.mainloop()


if __name__ == "__main__":
    test_simple()