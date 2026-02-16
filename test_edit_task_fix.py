#!/usr/bin/env python3
"""
测试编辑任务触发器配置修复效果
验证编辑任务时触发器切换不会导致参数控件消失
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path
import json

# 添加项目根路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.gui.automation_manager import AutomationManager, AutomationTask, TriggerType
from src.gui.automation_dialog import AutomationDialog


def create_test_task():
    """创建一个测试任务"""
    return AutomationTask(
        id="test_task_001",
        name="测试任务",
        enabled=True,
        trigger_type=TriggerType.INTERVAL.value,
        tool_id="mesh_cleaner",
        tool_category="maya",
        execution_mode="standalone",
        parameters={},
        interval_config={
            "interval_value": 30,
            "interval_unit": "minutes"
        },
        status="idle",
        created_at="2024-01-01T00:00:00",
        last_run=None,
        next_run=None
    )


def test_edit_task_trigger_switching():
    """测试编辑任务中的触发器切换"""
    
    print("🧪 开始测试编辑任务触发器切换修复")
    
    # 创建测试任务
    test_task = create_test_task()
    
    # 确保任务目录存在
    tasks_dir = project_root / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    
    # 保存测试任务到AutomationManager期望的格式
    task_file = tasks_dir / "automation_tasks.json"
    tasks_data = {
        "version": "1.0",
        "updated_at": "2024-01-01T00:00:00",
        "tasks": [test_task.to_dict()]
    }
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 创建测试任务: {test_task.name} (ID: {test_task.id})")
    print(f"   任务文件: {task_file}")
    print(f"   初始触发器类型: {test_task.trigger_type}")
    
    # 创建GUI进行手动测试
    root = tk.Tk()
    root.title("编辑任务触发器切换测试")
    root.geometry("800x600")
    
    # 创建说明标签
    info_frame = ttk.Frame(root)
    info_frame.pack(fill=tk.X, padx=10, pady=10)
    
    info_text = """
测试步骤：
1. 点击下面的"打开自动化管理器"按钮
2. 在任务列表中找到"测试任务"
3. 双击"测试任务"进入编辑模式
4. 在编辑面板中切换触发器类型（间隔 → 定时 → 文件监控）
5. 验证参数控件是否保持显示，不消失

预期结果：
- ✅ 切换触发器类型时，参数配置区域应该正确更新
- ✅ 参数控件不应该消失或变成空白
- ✅ 每种触发器类型的参数都能正确显示
"""
    
    info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                          font=("Arial", 10), foreground="blue")
    info_label.pack(anchor=tk.W)
    
    # 按钮框架
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def open_automation_manager():
        """打开自动化管理器"""
        try:
            # 创建自动化管理器实例（后端）
            manager = AutomationManager(
                config_dir=tasks_dir,
                execute_callback=None  # 测试不需要实际执行
            )
            
            # 创建自动化对话框窗口（前端GUI）
            dialog_window = tk.Toplevel(root)
            dialog_window.title("自动化管理器 - 编辑测试")
            dialog_window.geometry("1000x700")
            
            # 创建自动化对话框实例
            dialog = AutomationDialog(
                dialog_window,
                automation_manager=manager,
                tools_cache={},  # 测试不需要工具缓存
                get_tool_callback=None
            )
            
            print("✅ 自动化管理器已打开")
            print("   请在任务列表中找到并双击'测试任务'进行编辑测试")
            
        except Exception as e:
            print(f"❌ 打开自动化管理器失败: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup_test():
        """清理测试数据"""
        try:
            if task_file.exists():
                task_file.unlink()
                print(f"🗑️  已删除测试任务文件: {task_file}")
            root.quit()
        except Exception as e:
            print(f"⚠️  清理测试数据时出错: {e}")
            root.quit()
    
    # 按钮
    ttk.Button(button_frame, text="打开自动化管理器", 
               command=open_automation_manager).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="完成测试并清理", 
               command=cleanup_test).pack(side=tk.LEFT, padx=5)
    
    # 状态标签
    status_frame = ttk.LabelFrame(root, text="测试状态", padding=10)
    status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    status_text = tk.Text(status_frame, height=15, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=status_text.yview)
    status_text.configure(yscrollcommand=scrollbar.set)
    
    status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 添加测试指导
    test_guide = """
💡 测试重点 - 编辑任务触发器切换修复:

问题现象:
- 编辑任务时，切换触发器类型后参数控件消失
- 配置区域变成空白
- 无法设置触发器参数

修复原理:
- 避免错误删除 TriggerConfigWidget 实例
- 使用统一的触发器配置组件
- 正确管理控件生命周期

测试要点:
1. 编辑任务面板的触发器类型下拉菜单
2. 切换不同触发器类型时的参数显示
3. 参数输入框是否正常工作
4. 数据保存是否正确

如果修复成功，您应该看到:
✅ 触发器切换流畅，无闪烁
✅ 参数控件始终正确显示
✅ 不同类型的参数配置正确加载
"""
    
    status_text.insert(tk.END, test_guide)
    status_text.config(state=tk.DISABLED)
    
    print("🚀 GUI测试界面已启动")
    print("   请按照界面说明进行手动测试")
    
    root.mainloop()


if __name__ == "__main__":
    test_edit_task_trigger_switching()