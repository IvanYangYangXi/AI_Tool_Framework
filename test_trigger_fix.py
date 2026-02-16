#!/usr/bin/env python3
"""
测试触发器配置修复效果
验证新建任务中的触发器参数是否正确显示和保持
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path

# 添加项目根路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.gui.trigger_config_widget import TriggerConfigWidget


def test_trigger_config():
    """测试触发器配置控件"""
    
    root = tk.Tk()
    root.title("触发器配置修复测试")
    root.geometry("600x500")
    
    # 创建主框架
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 标题
    title_label = ttk.Label(main_frame, text="触发器配置测试", font=("Arial", 14, "bold"))
    title_label.pack(pady=10)
    
    # 创建触发器配置控件
    config_frame = ttk.LabelFrame(main_frame, text="触发器配置", padding=10)
    config_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    trigger_config = TriggerConfigWidget(config_frame)
    
    # 测试按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    def test_interval():
        """测试间隔触发"""
        trigger_config.clear_widgets()
        trigger_config.current_trigger_type = "interval"
        trigger_config.create_interval_config()
        print("设置为间隔触发")
    
    def test_scheduled():
        """测试定时触发"""
        trigger_config.clear_widgets()
        trigger_config.current_trigger_type = "scheduled"
        trigger_config.create_scheduled_config()
        print("设置为定时触发")
    
    def test_file_watch():
        """测试文件监控触发"""
        trigger_config.clear_widgets()
        trigger_config.current_trigger_type = "file_watch"
        trigger_config.create_file_watch_config()
        print("设置为文件监控触发")
    
    def collect_data():
        """收集配置数据"""
        try:
            config = trigger_config.collect_config()
            print("=== 收集到的配置数据 ===")
            for key, value in config.items():
                print(f"  {key}: {value}")
            print("========================")
        except Exception as e:
            print(f"❌ 收集配置失败: {e}")
    
    # 测试按钮
    ttk.Button(button_frame, text="间隔触发", command=test_interval).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="定时触发", command=test_scheduled).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="文件监控", command=test_file_watch).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="收集配置", command=collect_data).pack(side=tk.LEFT, padx=5)
    
    # 说明文字
    info_label = ttk.Label(main_frame, 
                          text="测试步骤：\n1. 点击触发器类型按钮\n2. 修改参数值\n3. 切换其他触发器类型\n4. 点击'收集配置'查看数据",
                          justify=tk.LEFT)
    info_label.pack(pady=10)
    
    # 默认设置为间隔触发
    root.after(100, test_interval)
    
    print("🧪 触发器配置测试启动")
    print("请在GUI中测试触发器参数的显示和切换功能")
    
    root.mainloop()


if __name__ == "__main__":
    test_trigger_config()