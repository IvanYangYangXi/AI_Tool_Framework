"""
自动化任务管理对话框

提供图形界面管理自动化任务
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

import os
import subprocess
from pathlib import Path


class ToolTip:
    """
    工具提示类 - 鼠标悬停显示完整信息
    """
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.widget.bind('<Motion>', self.motion)
    
    def enter(self, event=None):
        self.schedule()
    
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    
    def motion(self, event=None):
        self.unschedule()
        self.schedule()
    
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)  # 500ms延迟
    
    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def showtip(self, event=None):
        if not self.text:
            return
        
        try:
            x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        except:
            x, y, cx, cy = 0, 0, 0, 0
        
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background='#ffffe0', relief='solid', borderwidth=1,
                        font=('tahoma', '8', 'normal'), wraplength=300)
        label.pack(ipadx=5, ipady=3)
    
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
    
    def update_text(self, text):
        self.text = text

# 解决相对导入问题
import sys
try:
    from .automation_manager import (
        AutomationManager, AutomationTask, TriggerType, TaskStatus, TaskTemplates
    )
    from .trigger_manager import TriggerManager, TriggerScriptInfo
except ImportError:
    # 直接运行或路径问题时使用绝对导入
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from gui.automation_manager import (
        AutomationManager, AutomationTask, TriggerType, TaskStatus, TaskTemplates
    )
    from gui.trigger_manager import TriggerManager, TriggerScriptInfo


# 共享辅助函数
def build_param_tooltip(param_name: str, param_def: Dict) -> str:
    """构建参数的工具提示文本"""
    tooltip_parts = []
    
    # 参数描述
    if 'description' in param_def:
        tooltip_parts.append(param_def['description'])
    
    # 参数类型
    param_type = param_def.get('type', 'str')
    tooltip_parts.append(f"类型: {param_type}")
    
    # 默认值
    if 'default' in param_def:
        tooltip_parts.append(f"默认: {param_def['default']}")
    
    # 范围限制
    if param_type in ['int', 'float']:
        if 'min' in param_def:
            tooltip_parts.append(f"最小: {param_def['min']}")
        if 'max' in param_def:
            tooltip_parts.append(f"最大: {param_def['max']}")
    
    # 选择项
    if 'choices' in param_def:
        choices_str = ', '.join(str(c) for c in param_def['choices'])
        tooltip_parts.append(f"选项: {choices_str}")
    
    return '\n'.join(tooltip_parts)


def get_actual_trigger_name_from_task(task: AutomationTask) -> str:
    """从任务中获取实际的触发器名称"""
    if task.trigger_type == "custom" and hasattr(task, 'custom_trigger_config') and task.custom_trigger_config:
        return task.custom_trigger_config.get('trigger_script_id', task.trigger_type)
    return task.trigger_type


class AutomationDialog:
    """自动化任务管理对话框"""
    
    def __init__(self, parent: tk.Tk, automation_manager: AutomationManager,
                 tools_cache: Dict = None, get_tool_callback: Callable = None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            automation_manager: 自动化管理器实例
            tools_cache: 工具缓存字典
            get_tool_callback: 获取当前选中工具的回调
        """
        self.parent = parent
        self.manager = automation_manager
        self.tools_cache = tools_cache or {}
        self.get_tool_callback = get_tool_callback
        
        self.dialog = None
        self.task_tree = None
        self.selected_task_id = None
        
        # 初始化触发器管理器
        try:
            from .trigger_manager import TriggerManager
        except ImportError:
            from gui.trigger_manager import TriggerManager
        
        self.trigger_manager = TriggerManager()
        self.discovered_triggers = self.trigger_manager.discover_triggers()
        
        # 初始化触发器显示名称映射
        self._init_trigger_display_maps()
        
    def _init_trigger_display_maps(self):
        """初始化触发器显示名称映射"""
        self.trigger_display_map = {}
        self.trigger_value_map = {}
        
        for trigger_info in self.discovered_triggers:
            # 构建显示名称，包含来源信息
            if trigger_info.source == "shared":
                display_name = f"{trigger_info.display_name}"
            else:
                display_name = f"{trigger_info.display_name} (📁 本地)"
            
            self.trigger_display_map[trigger_info.name] = display_name
            self.trigger_value_map[display_name] = trigger_info.name
        
    def show(self):
        """显示对话框"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⏰ 自动化任务管理")
        self.dialog.geometry("900x600")
        self.dialog.minsize(800, 500)
        self.dialog.transient(self.parent)
        
        self._create_ui()
        self._refresh_task_list()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 900) // 2
        y = (self.dialog.winfo_screenheight() - 600) // 2
        self.dialog.geometry(f"900x600+{x}+{y}")
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        self._create_toolbar(main_frame)
        
        # 中间区域：任务列表 + 详情
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 左侧：任务列表
        self._create_task_list(paned)
        
        # 右侧：任务详情
        self._create_detail_panel(paned)
    
    def _create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X)
        
        # 新建任务按钮
        ttk.Button(toolbar, text="➕ 新建任务", 
                  command=self._show_create_dialog).pack(side=tk.LEFT, padx=2)
        
        # 从当前工具创建
        ttk.Button(toolbar, text="📌 从当前工具创建",
                  command=self._create_from_current_tool).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 立即运行
        ttk.Button(toolbar, text="▶ 立即运行",
                  command=self._run_selected).pack(side=tk.LEFT, padx=2)
        
        # 启用/禁用
        ttk.Button(toolbar, text="⏸ 暂停/继续",
                  command=self._toggle_selected).pack(side=tk.LEFT, padx=2)
        
        # 删除
        ttk.Button(toolbar, text="🗑 删除",
                  command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        
        # 右侧：刷新
        ttk.Button(toolbar, text="🔄 刷新",
                  command=self._refresh_task_list).pack(side=tk.RIGHT, padx=2)
    
    def _create_task_list(self, parent):
        """创建任务列表"""
        list_frame = ttk.LabelFrame(parent, text="任务列表", padding="5")
        parent.add(list_frame, weight=1)
        
        # Treeview
        columns = ('trigger', 'tool', 'status', 'next_run')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        self.task_tree.heading('#0', text='任务名称')
        self.task_tree.heading('trigger', text='触发方式')
        self.task_tree.heading('tool', text='工具')
        self.task_tree.heading('status', text='状态')
        self.task_tree.heading('next_run', text='下次执行')
        
        self.task_tree.column('#0', width=150)
        self.task_tree.column('trigger', width=80)
        self.task_tree.column('tool', width=100)
        self.task_tree.column('status', width=60)
        self.task_tree.column('next_run', width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.task_tree.bind('<<TreeviewSelect>>', self._on_task_select)
        self.task_tree.bind('<Double-1>', lambda e: self._run_selected())
    
    def _create_detail_panel(self, parent):
        """创建编辑面板"""
        detail_frame = ttk.LabelFrame(parent, text="任务编辑", padding="10")
        parent.add(detail_frame, weight=1)
        
        # 使用canvas实现滚动
        canvas = tk.Canvas(detail_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.detail_inner = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=self.detail_inner, anchor='nw')
        
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        self.detail_inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', configure_scroll)
        
        # 编辑内容
        self._create_edit_content()
    
    def _create_edit_content(self):
        """创建编辑内容"""
        frame = self.detail_inner
        
        # 标题
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="任务编辑", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # 提示信息
        ttk.Label(header_frame, text="选择左侧任务进行编辑", 
                 foreground="gray", font=('Arial', 9)).pack(side=tk.RIGHT)
        
        # 基本信息
        info_frame = ttk.LabelFrame(frame, text="基本信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 任务名称
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="名称:", width=10).pack(side=tk.LEFT)
        self.detail_name_var = tk.StringVar()
        self.detail_name_entry = ttk.Entry(row1, textvariable=self.detail_name_var)
        self.detail_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 工具（只读）
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="工具:", width=10).pack(side=tk.LEFT)
        self.detail_tool_var = tk.StringVar()
        self.detail_tool_label = ttk.Label(row2, textvariable=self.detail_tool_var, foreground="blue")
        self.detail_tool_label.pack(side=tk.LEFT)
        
        # 启用状态
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="启用:", width=10).pack(side=tk.LEFT)
        self.detail_enabled_var = tk.BooleanVar()
        self.detail_enabled_check = ttk.Checkbutton(row3, variable=self.detail_enabled_var,
                                                   text="自动执行此任务")
        self.detail_enabled_check.pack(side=tk.LEFT)
        
        # 触发配置
        trigger_frame = ttk.LabelFrame(frame, text="触发配置", padding="10")
        trigger_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 触发类型选择
        trigger_type_frame = ttk.Frame(trigger_frame)
        trigger_type_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(trigger_type_frame, text="触发类型:", width=10).pack(side=tk.LEFT)
        self.detail_trigger_type_var = tk.StringVar()
        
        # 获取触发器显示值列表（映射已在__init__中初始化）
        trigger_display_values = list(self.trigger_value_map.keys())
        
        self.detail_trigger_combo = ttk.Combobox(trigger_type_frame, 
                                               textvariable=self.detail_trigger_type_var,
                                               values=trigger_display_values,
                                               state='readonly')
        self.detail_trigger_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.detail_trigger_combo.bind('<<ComboboxSelected>>', self._on_detail_trigger_change)
        
        # 触发配置编辑区域
        self.detail_trigger_config_frame = ttk.Frame(trigger_frame)
        self.detail_trigger_config_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 执行历史（只读信息）
        history_frame = ttk.LabelFrame(frame, text="执行状态", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        hist_grid = ttk.Frame(history_frame)
        hist_grid.pack(fill=tk.X)
        
        # 第一行：运行次数和状态
        row1 = ttk.Frame(hist_grid)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="运行次数:", width=12).pack(side=tk.LEFT)
        self.detail_run_count_var = tk.StringVar(value="0")
        ttk.Label(row1, textvariable=self.detail_run_count_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="状态:", width=10).pack(side=tk.LEFT, padx=(20, 0))
        self.detail_status_var = tk.StringVar()
        self.detail_status_label = ttk.Label(row1, textvariable=self.detail_status_var, font=('Arial', 9, 'bold'))
        self.detail_status_label.pack(side=tk.LEFT, padx=5)
        
        # 第二行：上次运行
        row2 = ttk.Frame(hist_grid)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="上次运行:", width=12).pack(side=tk.LEFT)
        self.detail_last_run_var = tk.StringVar(value="-")
        ttk.Label(row2, textvariable=self.detail_last_run_var).pack(side=tk.LEFT, padx=5)
        
        # 第三行：下次运行
        row3 = ttk.Frame(hist_grid)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="下次运行:", width=12).pack(side=tk.LEFT)
        self.detail_next_run_var = tk.StringVar(value="-")
        ttk.Label(row3, textvariable=self.detail_next_run_var).pack(side=tk.LEFT, padx=5)
        
        # 错误信息（如有）
        self.error_frame = ttk.LabelFrame(frame, text="错误信息", padding="10")
        self.detail_error_var = tk.StringVar(value="")
        self.error_label = ttk.Label(self.error_frame, textvariable=self.detail_error_var, 
                                   foreground='red', wraplength=400)
        self.error_label.pack(fill=tk.X)
        
        # 按钮区域
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.save_btn = ttk.Button(btn_frame, text="💾 保存修改", 
                                  command=self._save_task_changes, state='disabled')
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(btn_frame, text="❌ 取消", 
                                    command=self._cancel_edit, state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT)
        
        # 存储触发配置编辑控件的引用
        self.trigger_edit_widgets = {}
    
    # ============================================
    # 事件处理
    # ============================================
    
    def _refresh_task_list(self):
        """刷新任务列表"""
        # 清空列表
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # 添加任务
        for task in self.manager.get_all_tasks():
            status_icon = self._get_status_icon(task.status)
            trigger_name = self._get_trigger_name(task)
            
            next_run = task.next_run or "-"
            if next_run not in ["-", "文件变更时", "手动触发"]:
                try:
                    dt = datetime.fromisoformat(next_run)
                    next_run = dt.strftime("%m-%d %H:%M")
                except:
                    pass
            
            # 插入任务项
            item_id = self.task_tree.insert('', 'end', iid=task.id,
                                           text=f"{'✓' if task.enabled else '○'} {task.name}",
                                           values=(trigger_name, task.tool_id, 
                                                  status_icon, next_run))
            
            # 设置状态列的背景色
            bg_color, fg_color = self._get_status_color(task.status)
            try:
                self.task_tree.set(item_id, 'status', status_icon)
                # 为整行设置标签，用于样式控制
                self.task_tree.item(item_id, tags=(f'status_{task.status}',))
            except:
                pass
        
        # 配置标签样式
        self._configure_status_styles()
    
    def _configure_status_styles(self):
        """配置状态样式"""
        statuses = ['idle', 'waiting', 'running', 'paused', 'error', 'completed']
        
        for status in statuses:
            bg_color, fg_color = self._get_status_color(status)
            try:
                self.task_tree.tag_configure(f'status_{status}', background=bg_color, foreground=fg_color)
            except:
                pass
    
    def _on_task_select(self, event):
        """任务选择事件"""
        selection = self.task_tree.selection()
        if not selection:
            # 清空编辑面板
            self._clear_edit_panel()
            return
        
        self.selected_task_id = selection[0]
        task = self.manager.get_task(self.selected_task_id)
        if task:
            self._load_task_for_edit(task)
    
    def _clear_edit_panel(self):
        """清空编辑面板"""
        self.detail_name_var.set("")
        self.detail_tool_var.set("未选择任务")
        self.detail_status_var.set("")
        self.detail_enabled_var.set(False)
        self.detail_trigger_type_var.set("")
        self.detail_run_count_var.set("0")
        self.detail_last_run_var.set("-")
        self.detail_next_run_var.set("-")
        self.detail_error_var.set("")
        
        # 隐藏错误信息框
        self.error_frame.pack_forget()
        
        # 清空触发配置编辑区域
        for widget in self.detail_trigger_config_frame.winfo_children():
            widget.destroy()
        
        # 禁用按钮
        self.save_btn.configure(state='disabled')
        self.cancel_btn.configure(state='disabled')
    
    def _load_task_for_edit(self, task: AutomationTask):
        """加载任务到编辑面板"""
        # 基本信息
        self.detail_name_var.set(task.name)
        self.detail_tool_var.set(f"{task.tool_id} ({task.tool_category})")
        self.detail_status_var.set(self._get_status_text(task.status))
        self.detail_enabled_var.set(task.enabled)
        
        # 执行状态信息
        self.detail_run_count_var.set(str(task.run_count))
        
        # 上次运行
        if task.last_run:
            try:
                dt = datetime.fromisoformat(task.last_run)
                self.detail_last_run_var.set(dt.strftime("%Y-%m-%d %H:%M:%S"))
            except:
                self.detail_last_run_var.set(task.last_run)
        else:
            self.detail_last_run_var.set("-")
        
        # 下次运行
        self.detail_next_run_var.set(task.next_run or "-")
        
        # 错误信息
        if task.last_error:
            self.detail_error_var.set(task.last_error)
            self.error_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.error_frame.pack_forget()
        
        # 设置触发类型
        trigger_display_name = self._get_trigger_name(task)
        self.detail_trigger_type_var.set(trigger_display_name)
        
        # 加载触发器配置
        self._load_trigger_config_for_edit(task)
        
        # 启用按钮
        self.save_btn.configure(state='normal')
        self.cancel_btn.configure(state='normal')
        
        # 记录原始任务状态（用于取消编辑）
        self.original_task_data = {
            'name': task.name,
            'enabled': task.enabled,
            'trigger_type': task.trigger_type,
            'trigger_config': self._get_task_trigger_config(task)
        }
    
    def _get_task_trigger_config(self, task: AutomationTask) -> dict:
        """获取任务的触发配置"""
        if task.trigger_type == TriggerType.SCHEDULED.value:
            return task.scheduled_config or {}
        elif task.trigger_type == TriggerType.INTERVAL.value:
            return task.interval_config or {}
        elif task.trigger_type == TriggerType.FILE_WATCH.value:
            return task.file_watch_config or {}
        elif task.trigger_type == TriggerType.TASK_CHAIN.value:
            return task.task_chain_config or {}
        elif task.trigger_type == TriggerType.CUSTOM.value or task.trigger_type == "custom":
            return task.custom_trigger_config or {}
        return {}
    
    def _load_trigger_config_for_edit(self, task: AutomationTask):
        """加载触发配置到编辑区域"""
        # 清空现有配置区域
        for widget in self.detail_trigger_config_frame.winfo_children():
            widget.destroy()
        
        trigger_type = task.trigger_type
        config = self._get_task_trigger_config(task)
        
        # 初始化配置控件容器（如果不存在）
        if not hasattr(self, 'trigger_config_widgets'):
            self.trigger_config_widgets = {}
        
        # 根据触发类型创建编辑控件
        if trigger_type == TriggerType.SCHEDULED.value:
            self._create_scheduled_edit_widgets(config)
        elif trigger_type == TriggerType.INTERVAL.value:
            self._create_interval_edit_widgets(config)
        elif trigger_type == TriggerType.FILE_WATCH.value:
            self._create_file_watch_edit_widgets(config)
        elif trigger_type == TriggerType.TASK_CHAIN.value:
            self._create_task_chain_edit_widgets(config)
        elif trigger_type == TriggerType.CUSTOM.value or trigger_type == "custom":
            # 获取trigger_script_id
            trigger_script_id = config.get('trigger_script_id')
            if trigger_script_id:
                self._create_custom_edit_widgets(trigger_script_id, config)
    
    def _create_interval_edit_widgets(self, config: dict):
        """创建间隔触发编辑控件"""
        frame = self.detail_trigger_config_frame
        
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=5)
        
        ttk.Label(row, text="每隔").pack(side=tk.LEFT)
        
        value_var = tk.StringVar(value=str(config.get('value', 30)))
        ttk.Entry(row, textvariable=value_var, width=10).pack(side=tk.LEFT, padx=5)
        
        unit_var = tk.StringVar(value=config.get('unit', 'minutes'))
        unit_combo = ttk.Combobox(row, textvariable=unit_var,
                                values=['seconds', 'minutes', 'hours'],
                                state='readonly', width=10)
        unit_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row, text="执行一次").pack(side=tk.LEFT, padx=5)
        
        self.trigger_config_widgets = {
            'interval_value': value_var,
            'interval_unit': unit_var
        }
    
    def _create_scheduled_edit_widgets(self, config: dict):
        """创建定时触发编辑控件"""
        frame = self.detail_trigger_config_frame
        
        # 时间设置
        time_row = ttk.Frame(frame)
        time_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_row, text="执行时间:").pack(side=tk.LEFT)
        
        time_str = config.get('time', '09:00')
        hour, minute = time_str.split(':') if ':' in time_str else ('09', '00')
        
        hour_var = tk.StringVar(value=hour)
        ttk.Spinbox(time_row, from_=0, to=23, textvariable=hour_var,
                   width=3, format="%02.0f").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_row, text=":").pack(side=tk.LEFT)
        
        minute_var = tk.StringVar(value=minute)
        ttk.Spinbox(time_row, from_=0, to=59, textvariable=minute_var,
                   width=3, format="%02.0f").pack(side=tk.LEFT, padx=5)
        
        # 日期选择
        day_row = ttk.Frame(frame)
        day_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(day_row, text="执行日期:").pack(side=tk.LEFT)
        
        days_var = tk.StringVar(value=','.join(config.get('days', ['everyday'])))
        ttk.Entry(day_row, textvariable=days_var, width=30).pack(side=tk.LEFT, padx=5)
        
        self.trigger_config_widgets = {
            'scheduled_hour': hour_var,
            'scheduled_minute': minute_var,
            'scheduled_days': days_var
        }
    
    def _create_file_watch_edit_widgets(self, config: dict):
        """创建文件监控编辑控件"""
        frame = self.detail_trigger_config_frame
        
        ttk.Label(frame, text="监控路径:").pack(anchor=tk.W, pady=(0, 5))
        
        paths_var = tk.StringVar(value='\n'.join(config.get('watch_paths', [])))
        paths_text = tk.Text(frame, height=4, width=50)
        paths_text.pack(fill=tk.X, pady=(0, 5))
        paths_text.insert('1.0', paths_var.get())
        
        debounce_row = ttk.Frame(frame)
        debounce_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(debounce_row, text="防抖延迟(秒):").pack(side=tk.LEFT)
        debounce_var = tk.StringVar(value=str(config.get('debounce_seconds', 5)))
        ttk.Entry(debounce_row, textvariable=debounce_var, width=10).pack(side=tk.LEFT, padx=5)
        
        self.trigger_config_widgets = {
            'watch_paths_text': paths_text,
            'debounce_seconds': debounce_var
        }
    
    def _create_task_chain_edit_widgets(self, config: dict):
        """创建任务链编辑控件"""
        frame = self.detail_trigger_config_frame
        
        ttk.Label(frame, text="任务列表（每行一个任务ID）:").pack(anchor=tk.W, pady=(0, 5))
        
        tasks_var = tk.StringVar(value='\n'.join(config.get('tasks', [])))
        tasks_text = tk.Text(frame, height=4, width=50)
        tasks_text.pack(fill=tk.X, pady=(0, 5))
        tasks_text.insert('1.0', tasks_var.get())
        
        self.trigger_config_widgets = {
            'tasks_text': tasks_text
        }
    
    def _create_custom_edit_widgets(self, trigger_script_id: str, config: dict):
        """创建自定义触发器编辑控件"""
        frame = self.detail_trigger_config_frame
        
        # 获取触发器类
        if hasattr(self, 'trigger_manager') and self.trigger_manager:
            trigger_cls = self.trigger_manager._trigger_classes.get(trigger_script_id)
            if trigger_cls and hasattr(trigger_cls, 'TRIGGER_PARAMETERS'):
                params = trigger_cls.TRIGGER_PARAMETERS
                widgets = {}
                
                for param_name, param_def in params.items():
                    param_row = ttk.Frame(frame)
                    param_row.pack(fill=tk.X, pady=2)
                    
                    desc = param_def.get('description', param_name)
                    ttk.Label(param_row, text=f"{desc}:").pack(side=tk.LEFT, anchor=tk.W, width=15)
                    
                    value = config.get(param_name, param_def.get('default', ''))
                    
                    if param_def.get('type') == 'boolean':
                        var = tk.BooleanVar(value=bool(value))
                        ttk.Checkbutton(param_row, variable=var).pack(side=tk.LEFT, padx=5)
                    elif param_def.get('type') == 'integer':
                        var = tk.IntVar(value=int(value) if str(value).isdigit() else 0)
                        ttk.Spinbox(param_row, textvariable=var, from_=0, to=9999, width=10).pack(side=tk.LEFT, padx=5)
                    elif param_def.get('type') == 'choice':
                        var = tk.StringVar(value=str(value))
                        choices = list(param_def.get('choices', {}).keys())
                        ttk.Combobox(param_row, textvariable=var, values=choices, state='readonly').pack(side=tk.LEFT, padx=5)
                    else:
                        var = tk.StringVar(value=str(value))
                        ttk.Entry(param_row, textvariable=var, width=20).pack(side=tk.LEFT, padx=5)
                    
                    widgets[param_name] = var
                
                # 添加trigger_script_id到配置
                widgets['trigger_script_id'] = tk.StringVar(value=trigger_script_id)
                self.trigger_config_widgets = widgets
        
    def _collect_trigger_config_from_widgets(self) -> dict:
        """从控件收集触发器配置"""
        if not hasattr(self, 'trigger_config_widgets') or not self.trigger_config_widgets:
            return {}
        
        config = {}
        widgets = self.trigger_config_widgets
        
        # 间隔触发器
        if 'interval_value' in widgets:
            config['value'] = int(widgets['interval_value'].get())
            config['unit'] = widgets['interval_unit'].get()
        
        # 定时触发器
        elif 'scheduled_hour' in widgets:
            hour = widgets['scheduled_hour'].get().zfill(2)
            minute = widgets['scheduled_minute'].get().zfill(2)
            config['time'] = f"{hour}:{minute}"
            days_str = widgets['scheduled_days'].get()
            config['days'] = [d.strip() for d in days_str.split(',') if d.strip()]
        
        # 文件监控
        elif 'watch_paths_text' in widgets:
            paths_text = widgets['watch_paths_text'].get('1.0', tk.END).strip()
            config['watch_paths'] = [p.strip() for p in paths_text.split('\n') if p.strip()]
            config['debounce_seconds'] = int(widgets['debounce_seconds'].get())
        
        # 任务链
        elif 'tasks_text' in widgets:
            tasks_text = widgets['tasks_text'].get('1.0', tk.END).strip()
            config['tasks'] = [t.strip() for t in tasks_text.split('\n') if t.strip()]
        
        # 自定义触发器
        elif 'trigger_script_id' in widgets:
            for name, var in widgets.items():
                if name == 'trigger_script_id':
                    config[name] = var.get()
                else:
                    value = var.get()
                    config[name] = value
        
        return config
    
    def _format_config_parameters(self, title: str, config: dict) -> str:
        """格式化配置参数显示"""
        if not config:
            return ""
        
        result = f"\n{title}:\n"
        for key, value in config.items():
            # 跳过一些内部字段
            if key in ['trigger_script_id']:
                continue
            
            # 格式化值
            if isinstance(value, bool):
                display_value = "是" if value else "否"
            elif isinstance(value, list):
                if len(value) > 3:
                    display_value = f"[{', '.join(map(str, value[:3]))}...] ({len(value)}项)"
                else:
                    display_value = f"[{', '.join(map(str, value))}]"
            elif isinstance(value, dict):
                display_value = f"{{...}} ({len(value)}项)"
            else:
                display_value = str(value)
            
            result += f"  • {key}: {display_value}\n"
        
        return result
    
    def _get_status_icon(self, status: str) -> str:
        """获取状态图标"""
        icons = {
            'idle': '💤 空闲',
            'waiting': '⏳ 等待中',
            'running': '▶️ 运行中',
            'paused': '⏸️ 已暂停',
            'error': '❌ 错误',
            'completed': '✅ 已完成'
        }
        return icons.get(status, '❓ 未知')
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        texts = {
            'idle': '空闲',
            'waiting': '等待中',
            'running': '运行中',
            'paused': '已暂停',
            'error': '错误',
            'completed': '已完成'
        }
        return texts.get(status, status)
    
    def _get_status_color(self, status: str) -> tuple:
        """获取状态颜色 (背景色, 文字色)"""
        colors = {
            'idle': ('#f0f0f0', '#666666'),
            'waiting': ('#e8f5e8', '#2e7d32'),
            'running': ('#e3f2fd', '#1565c0'),
            'paused': ('#fff8e1', '#f57f17'),
            'error': ('#ffebee', '#c62828'),
            'completed': ('#e8f5e8', '#2e7d32')
        }
        return colors.get(status, ('#f0f0f0', '#666666'))
    
    def _get_trigger_name(self, task_or_trigger_type) -> str:
        """获取触发器名称"""
        # 兼容旧的调用方式（直接传入trigger_type字符串）
        if isinstance(task_or_trigger_type, str):
            trigger_type = task_or_trigger_type
            names = {
                'scheduled': '⏰ 定时',
                'interval': '🔄 间隔',
                'file_watch': '📁 文件监控',
                'task_chain': '🔗 任务链'
            }
            return names.get(trigger_type, trigger_type)
        
        # 新的调用方式（传入完整的任务对象）
        task = task_or_trigger_type
        actual_trigger_name = get_actual_trigger_name_from_task(task)
        
        # 查找显示名称映射
        display_name = self.trigger_display_map.get(actual_trigger_name, actual_trigger_name)
        return display_name
    
    # ============================================
    # 操作方法
    # ============================================
    
    def _run_selected(self):
        """立即运行选中的任务"""
        if not self.selected_task_id:
            messagebox.showwarning("提示", "请先选择一个任务")
            return
        
        if self.manager.run_task_now(self.selected_task_id):
            messagebox.showinfo("提示", "任务已开始执行")
        else:
            messagebox.showerror("错误", "任务执行失败")
    
    def _toggle_selected(self):
        """切换任务启用状态"""
        if not self.selected_task_id:
            messagebox.showwarning("提示", "请先选择一个任务")
            return
        
        task = self.manager.get_task(self.selected_task_id)
        if task:
            self.manager.set_task_enabled(self.selected_task_id, not task.enabled)
            self._refresh_task_list()
            self._show_task_detail(self.manager.get_task(self.selected_task_id))
            # 强制更新UI
            self.dialog.update_idletasks()
    
    def _delete_selected(self):
        """删除选中的任务"""
        if not self.selected_task_id:
            messagebox.showwarning("提示", "请先选择一个任务")
            return
        
        task = self.manager.get_task(self.selected_task_id)
        if not task:
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除任务 '{task.name}' 吗？"):
            self.manager.delete_task(self.selected_task_id)
            self.selected_task_id = None
            self._refresh_task_list()
            # 强制更新UI
            self.dialog.update_idletasks()
    
        self.save_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
        
        # 显示只读文本，隐藏编辑控件
        self.detail_trigger_config_frame.pack_forget()
        self.detail_trigger_text.pack(fill=tk.X)
        
        # 清除编辑控件
        for widget in self.detail_trigger_config_frame.winfo_children():
            widget.destroy()
        self.trigger_edit_widgets.clear()
    
    def _cancel_edit(self):
        """取消编辑"""
        if self.selected_task_id and hasattr(self, 'original_task_data'):
            # 恢复原始数据
            self.detail_name_var.set(self.original_task_data['name'])
            self.detail_enabled_var.set(self.original_task_data['enabled'])
            
            # 重新加载任务
            task = self.manager.get_task(self.selected_task_id)
            if task:
                self._load_task_for_edit(task)
    
    def _on_detail_trigger_change(self, event):
        """触发类型变更"""
        if self.selected_task_id:
            task = self.manager.get_task(self.selected_task_id)
            if task:
                # 获取新选择的触发器类型
                selected_display = self.detail_trigger_type_var.get()
                selected_trigger = self.trigger_value_map.get(selected_display, selected_display)
                
                # 创建对应的配置控件（使用默认配置）
                self._create_trigger_config_widgets_by_type(selected_trigger)
    
    def _create_trigger_config_widgets_by_type(self, trigger_type: str):
        """根据触发器类型创建配置控件"""
        # 清空现有控件
        for widget in self.detail_trigger_config_frame.winfo_children():
            widget.destroy()
        
        # 根据类型创建控件（使用默认配置）
        if trigger_type == TriggerType.SCHEDULED.value:
            self._create_scheduled_edit_widgets({})
        elif trigger_type == TriggerType.INTERVAL.value:
            self._create_interval_edit_widgets({})
        elif trigger_type == TriggerType.FILE_WATCH.value:
            self._create_file_watch_edit_widgets({})
        elif trigger_type == TriggerType.TASK_CHAIN.value:
            self._create_task_chain_edit_widgets({})
        elif trigger_type in self.trigger_value_map.values():
            # 查找自定义触发器
            for display_name, script_id in self.trigger_value_map.items():
                if script_id == trigger_type:
                    self._create_custom_edit_widgets(script_id, {})
                    break
    
    
    def _create_interval_edit_config(self, task: AutomationTask):
        """创建间隔触发编辑配置"""
        frame = self.detail_trigger_config_frame
        config = task.interval_config or {}
        
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=5)
        
        ttk.Label(row, text="每隔").pack(side=tk.LEFT)
        
        self.edit_interval_value = tk.StringVar(value=str(config.get('value', 30)))
        ttk.Entry(row, textvariable=self.edit_interval_value, width=8).pack(side=tk.LEFT, padx=5)
        
        self.edit_interval_unit = tk.StringVar(value=config.get('unit', 'minutes'))
        ttk.Combobox(row, textvariable=self.edit_interval_unit,
                    values=["seconds", "minutes", "hours"],
                    state="readonly", width=10).pack(side=tk.LEFT)
        
        ttk.Label(row, text="执行一次").pack(side=tk.LEFT, padx=5)
        
        # 预设按钮（与新建面板保持一致）
        preset_frame = ttk.Frame(frame)
        preset_frame.pack(fill=tk.X, pady=10)
        ttk.Label(preset_frame, text="快捷预设:").pack(side=tk.LEFT)
        
        presets = [("5分钟", 5, "minutes"), ("30分钟", 30, "minutes"), 
                   ("1小时", 1, "hours"), ("2小时", 2, "hours")]
        for text, val, unit in presets:
            ttk.Button(preset_frame, text=text, width=8,
                      command=lambda v=val, u=unit: self._set_edit_interval(v, u)).pack(side=tk.LEFT, padx=2)
        
        self.trigger_edit_widgets['interval'] = {
            'value': self.edit_interval_value,
            'unit': self.edit_interval_unit
        }
    
    def _set_edit_interval(self, value, unit):
        """设置编辑模式的间隔值"""
        self.edit_interval_value.set(str(value))
        self.edit_interval_unit.set(unit)
    
    def _create_scheduled_edit_config(self, task: AutomationTask):
        """创建定时触发编辑配置"""
        frame = self.detail_trigger_config_frame
        config = task.scheduled_config or {}
        
        # 时间设置
        time_row = ttk.Frame(frame)
        time_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_row, text="执行时间:").pack(side=tk.LEFT)
        
        time_str = config.get('time', '09:00')
        hour, minute = time_str.split(':') if ':' in time_str else ('09', '00')
        
        self.edit_scheduled_hour = tk.StringVar(value=hour)
        ttk.Spinbox(time_row, from_=0, to=23, width=3,
                   textvariable=self.edit_scheduled_hour, format="%02.0f").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_row, text=":").pack(side=tk.LEFT)
        
        self.edit_scheduled_minute = tk.StringVar(value=minute)
        ttk.Spinbox(time_row, from_=0, to=59, width=3,
                   textvariable=self.edit_scheduled_minute, format="%02.0f").pack(side=tk.LEFT, padx=5)
        
        # 星期选择
        ttk.Label(frame, text="执行日期:").pack(anchor=tk.W, pady=(10, 5))
        
        days_frame = ttk.Frame(frame)
        days_frame.pack(fill=tk.X)
        
        selected_days = config.get('days', [])
        self.edit_day_vars = {}
        days = [("mon", "周一"), ("tue", "周二"), ("wed", "周三"), 
                ("thu", "周四"), ("fri", "周五"), ("sat", "周六"), ("sun", "周日")]
        
        for day_id, day_name in days:
            var = tk.BooleanVar(value=day_id in selected_days)
            self.edit_day_vars[day_id] = var
            ttk.Checkbutton(days_frame, text=day_name, variable=var).pack(side=tk.LEFT, padx=3)
        
        # 快捷按钮（与新建面板保持一致）
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(quick_frame, text="工作日", 
                  command=lambda: self._set_edit_days(["mon","tue","wed","thu","fri"])).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="每天",
                  command=lambda: self._set_edit_days(["mon","tue","wed","thu","fri","sat","sun"])).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="周末",
                  command=lambda: self._set_edit_days(["sat","sun"])).pack(side=tk.LEFT, padx=2)
        
        self.trigger_edit_widgets['scheduled'] = {
            'hour': self.edit_scheduled_hour,
            'minute': self.edit_scheduled_minute,
            'days': self.edit_day_vars
        }
    
    def _set_edit_days(self, days: List[str]):
        """设置编辑模式的执行日期"""
        # 先清空所有
        for day_var in self.edit_day_vars.values():
            day_var.set(False)
        # 设置选中的日期
        for day in days:
            if day in self.edit_day_vars:
                self.edit_day_vars[day].set(True)
    
    def _create_file_watch_edit_config(self, task: AutomationTask):
        """创建文件监控编辑配置"""
        frame = self.detail_trigger_config_frame
        config = task.file_watch_config or {}
        
        ttk.Label(frame, text="监控路径 (每行一个):").pack(anchor=tk.W)
        
        self.edit_watch_paths = tk.Text(frame, height=5, width=50)
        self.edit_watch_paths.pack(fill=tk.X, pady=5)
        
        # 填充现有路径
        paths = config.get('watch_paths', [])
        self.edit_watch_paths.insert('1.0', '\n'.join(paths))
        
        # 防抖设置
        debounce_row = ttk.Frame(frame)
        debounce_row.pack(fill=tk.X, pady=10)
        
        ttk.Label(debounce_row, text="防抖时间:").pack(side=tk.LEFT)
        self.edit_debounce = tk.StringVar(value=str(config.get('debounce_seconds', 5)))
        ttk.Entry(debounce_row, textvariable=self.edit_debounce, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(debounce_row, text="秒").pack(side=tk.LEFT)
        
        self.trigger_edit_widgets['file_watch'] = {
            'paths': self.edit_watch_paths,
            'debounce': self.edit_debounce
        }
    
    def _create_task_chain_edit_config(self, task: AutomationTask):
        """创建任务链编辑配置"""
        frame = self.detail_trigger_config_frame
        config = task.task_chain_config or {}
        
        ttk.Label(frame, text="选择要依次执行的任务:").pack(anchor=tk.W)
        
        # 任务列表
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.edit_chain_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.edit_chain_listbox.yview)
        self.edit_chain_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.edit_chain_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充任务并选择已配置的
        selected_tasks = config.get('tasks', [])
        for idx, task_obj in enumerate(self.manager.get_all_tasks()):
            if task_obj.trigger_type != TriggerType.TASK_CHAIN.value and task_obj.id != task.id:
                self.edit_chain_listbox.insert(tk.END, f"{task_obj.name} ({task_obj.id})")
                if task_obj.id in selected_tasks:
                    self.edit_chain_listbox.selection_set(idx)
        
        # 选项
        opt_frame = ttk.Frame(frame)
        opt_frame.pack(fill=tk.X, pady=5)
        
        self.edit_stop_on_error = tk.BooleanVar(value=config.get('stop_on_error', True))
        ttk.Checkbutton(opt_frame, text="出错时停止后续任务", 
                       variable=self.edit_stop_on_error).pack(side=tk.LEFT)
        
        ttk.Label(opt_frame, text="任务间隔:").pack(side=tk.LEFT, padx=(20, 0))
        self.edit_chain_delay = tk.StringVar(value=str(config.get('delay_between', 2)))
        ttk.Entry(opt_frame, textvariable=self.edit_chain_delay, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(opt_frame, text="秒").pack(side=tk.LEFT)
        
        self.trigger_edit_widgets['task_chain'] = {
            'listbox': self.edit_chain_listbox,
            'stop_on_error': self.edit_stop_on_error,
            'delay': self.edit_chain_delay
        }
    
    def _create_dynamic_trigger_edit_config(self, task, trigger_info):
        """创建动态触发器编辑配置（基于TriggerManager发现的触发器）"""
        frame = self.detail_trigger_config_frame
        
        try:
            # 显示触发器信息
            info_frame = ttk.Frame(frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            script_name = Path(trigger_info.file_path).name
            ttk.Label(info_frame, text=f"脚本: {script_name}", 
                     foreground='gray').pack(anchor=tk.W)
            
            # 检查触发器参数信息
            if not trigger_info.parameters:
                ttk.Label(frame, text="此触发器无需配置参数").pack(anchor=tk.W, pady=10)
                return
            
            # 获取触发器配置
            current_config = {}
            if hasattr(task, 'custom_trigger_config') and task.custom_trigger_config:
                current_config = task.custom_trigger_config
            elif task.trigger_type == 'interval' and task.interval_config:
                current_config = task.interval_config
            elif task.trigger_type == 'scheduled' and task.scheduled_config:
                current_config = task.scheduled_config
            elif task.trigger_type == 'file_watch' and task.file_watch_config:
                current_config = task.file_watch_config
            elif task.trigger_type == 'task_chain' and task.task_chain_config:
                current_config = task.task_chain_config
            
            # 参数配置标题
            ttk.Label(frame, text="参数配置:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            
            # 参数配置区域
            params_frame = ttk.Frame(frame)
            params_frame.pack(fill=tk.X)
            
            # 创建参数编辑界面（与新建界面保持一致）
            self.trigger_edit_widgets[trigger_info.name] = {}
            
            for param_name, param_def in trigger_info.parameters.items():
                row = ttk.Frame(params_frame)
                row.pack(fill=tk.X, pady=3)
                
                # 参数标签
                param_type = param_def.get('type', 'string')
                param_desc = param_def.get('description', param_name)
                current_value = current_config.get(param_name, param_def.get('default', ''))
                
                # 创建参数标签并添加工具提示
                label = ttk.Label(row, text=f"{param_desc}:", width=15)
                label.pack(side=tk.LEFT)
                
                # 构建工具提示文本
                tooltip_text = build_param_tooltip(param_name, param_def)
                if tooltip_text:
                    ToolTip(label, tooltip_text)
                
                # 根据类型创建不同的控件（与新建界面完全一致）
                if param_type == 'bool':
                    var = tk.BooleanVar(value=current_value if isinstance(current_value, bool) else False)
                    widget = ttk.Checkbutton(row, variable=var)
                    widget.pack(side=tk.LEFT)
                    self.trigger_edit_widgets[trigger_info.name][param_name] = ('bool', var)
                    
                elif param_type == 'int':
                    var = tk.StringVar(value=str(current_value))
                    min_val = param_def.get('min', 0)
                    max_val = param_def.get('max', 9999)
                    widget = ttk.Spinbox(row, from_=min_val, to=max_val, textvariable=var, width=10)
                    widget.pack(side=tk.LEFT)
                    self.trigger_edit_widgets[trigger_info.name][param_name] = ('int', var)
                    
                elif param_type == 'float':
                    var = tk.StringVar(value=str(current_value))
                    widget = ttk.Entry(row, textvariable=var, width=15)
                    widget.pack(side=tk.LEFT)
                    self.trigger_edit_widgets[trigger_info.name][param_name] = ('float', var)
                    
                elif param_type == 'choice':
                    choices = param_def.get('choices', [])
                    var = tk.StringVar(value=current_value if current_value in choices else (choices[0] if choices else ''))
                    widget = ttk.Combobox(row, textvariable=var, values=choices, state='readonly', width=15)
                    widget.pack(side=tk.LEFT)
                    self.trigger_edit_widgets[trigger_info.name][param_name] = ('choice', var)
                    
                else:  # string 或其他
                    var = tk.StringVar(value=str(current_value))
                    widget = ttk.Entry(row, textvariable=var, width=25)
                    widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    self.trigger_edit_widgets[trigger_info.name][param_name] = ('string', var)
                
                # 为控件也添加工具提示
                if tooltip_text:
                    ToolTip(widget, tooltip_text)
            
            # 添加编辑脚本按钮
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=(15, 0))
            
            ttk.Button(
                btn_frame, 
                text="📝 编辑触发器脚本",
                command=lambda: self._open_trigger_script(trigger_info.file_path)
            ).pack(side=tk.LEFT)
            
        except Exception as e:
            ttk.Label(frame, text=f"❌ 配置界面创建失败: {str(e)}").pack()
            print(f"[ERROR] 创建动态触发器编辑配置失败: {e}")
    
    def _save_task_changes(self):
        """保存任务修改"""
        if not self.selected_task_id:
            return
        
        try:
            # 基本信息
            new_name = self.detail_name_var.get().strip()
            if not new_name:
                messagebox.showwarning("提示", "任务名称不能为空")
                return
            
            enabled = self.detail_enabled_var.get()
            trigger_display = self.detail_trigger_type_var.get()
            # 将显示值转换回内部值
            trigger_type = self.trigger_value_map.get(trigger_display, trigger_display)
            
            # 收集触发配置（复用CreateTaskDialog的方法）
            trigger_config = {}
            if hasattr(self, 'trigger_config_widgets') and self.trigger_config_widgets:
                trigger_config = self._collect_trigger_config_from_widgets()
            
            # 更新任务
            self.manager.update_task_full(
                self.selected_task_id,
                name=new_name,
                trigger_type=TriggerType(trigger_type),
                enabled=enabled,
                trigger_config=trigger_config
            )
            
            # 刷新界面
            self._refresh_task_list()
            task = self.manager.get_task(self.selected_task_id)
            if task:
                self._load_task_for_edit(task)
            
            # 强制更新UI
            self.dialog.update_idletasks()
            
            messagebox.showinfo("提示", "保存成功")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _collect_trigger_config(self, trigger_type: str) -> Optional[Dict]:
        """收集触发配置"""
        try:
            if trigger_type == 'interval':
                widgets = self.trigger_edit_widgets.get('interval', {})
                return {
                    "value": int(widgets['value'].get()),
                    "unit": widgets['unit'].get()
                }
            
            elif trigger_type == 'scheduled':
                widgets = self.trigger_edit_widgets.get('scheduled', {})
                hour = widgets['hour'].get().zfill(2)
                minute = widgets['minute'].get().zfill(2)
                days = [day for day, var in widgets['days'].items() if var.get()]
                if not days:
                    messagebox.showwarning("提示", "请至少选择一天")
                    return None
                return {
                    "time": f"{hour}:{minute}",
                    "days": days
                }
            
            elif trigger_type == 'file_watch':
                widgets = self.trigger_edit_widgets.get('file_watch', {})
                paths_text = widgets['paths'].get('1.0', tk.END).strip()
                paths = [p.strip() for p in paths_text.split('\n') if p.strip()]
                if not paths:
                    messagebox.showwarning("提示", "请添加监控路径")
                    return None
                return {
                    "watch_paths": paths,
                    "debounce_seconds": int(widgets['debounce'].get())
                }
            
            elif trigger_type == 'task_chain':
                widgets = self.trigger_edit_widgets.get('task_chain', {})
                listbox = widgets['listbox']
                selected = listbox.curselection()
                if not selected:
                    messagebox.showwarning("提示", "请选择要执行的任务")
                    return None
                
                task_ids = []
                for idx in selected:
                    text = listbox.get(idx)
                    import re
                    match = re.search(r'\((task_\w+)\)$', text)
                    if match:
                        task_ids.append(match.group(1))
                
                return {
                    "tasks": task_ids,
                    "stop_on_error": widgets['stop_on_error'].get(),
                    "delay_between": int(widgets['delay'].get())
                }
            
            else:
                # 检查是否是动态触发器
                widgets = self.trigger_edit_widgets.get(trigger_type, {})
                if widgets:
                    config = {}
                    for param_name, widget in widgets.items():
                        if hasattr(widget, 'get'):
                            value = widget.get()
                            # 尝试转换数值类型
                            try:
                                if isinstance(value, str) and value.isdigit():
                                    value = int(value)
                                elif isinstance(value, str) and '.' in value:
                                    value = float(value)
                            except:
                                pass
                            config[param_name] = value
                    return config
            
            return {}
            
        except (ValueError, KeyError) as e:
            messagebox.showwarning("提示", f"配置参数错误: {e}")
            return None
    
    def _create_from_current_tool(self):
        """从当前选中的工具创建任务"""
        if not self.get_tool_callback:
            messagebox.showwarning("提示", "无法获取当前工具")
            return
        
        tool_info = self.get_tool_callback()
        if not tool_info:
            messagebox.showwarning("提示", "请先在主界面选择一个工具")
            return
        
        self._show_create_dialog(prefill_tool=tool_info)
    
    def _show_create_dialog(self, prefill_tool: Dict = None):
        """显示创建任务对话框"""
        print("[AutomationDialog] 新建任务按钮被点击！")
        try:
            CreateTaskDialog(self.dialog, self.manager, self.tools_cache, 
                            prefill_tool, self._refresh_task_list)
        except Exception as e:
            print(f"[AutomationDialog] 创建对话框失败: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _open_trigger_script(self, script_path: str):
        """打开触发器脚本进行编辑"""
        import subprocess
        import os
        
        try:
            if os.path.exists(script_path):
                # 使用系统默认编辑器打开文件
                os.startfile(script_path)
            else:
                messagebox.showwarning("提示", f"脚本文件不存在: {script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开脚本文件: {e}")


class CreateTaskDialog:
    """创建任务对话框"""
    
    def __init__(self, parent, manager: AutomationManager, 
                 tools_cache: Dict, prefill_tool: Dict = None,
                 on_created: Callable = None):
        self.parent = parent
        self.manager = manager
        self.tools_cache = tools_cache
        self.prefill_tool = prefill_tool
        self.on_created = on_created
        
        # 初始化触发器管理器 - 添加详细调试
        print(f"[CreateTaskDialog] 开始初始化TriggerManager...")
        print(f"[CreateTaskDialog] 当前工作目录: {os.getcwd()}")
        print(f"[CreateTaskDialog] sys.path前5项: {sys.path[:5]}")
        
        try:
            self.trigger_manager = TriggerManager()
            print(f"[CreateTaskDialog] TriggerManager创建成功")
            
            self.custom_triggers = self.trigger_manager.discover_triggers()
            print(f"[CreateTaskDialog] 触发器发现完成，数量: {len(self.custom_triggers)}")
            
            if len(self.custom_triggers) == 0:
                print(f"[CreateTaskDialog] ❌ 警告：没有发现任何触发器!")
                print(f"[CreateTaskDialog] 共享目录: {self.trigger_manager.shared_triggers_dir}")
                print(f"[CreateTaskDialog] 本地目录: {self.trigger_manager.triggers_dir}")
                
                # 检查目录是否存在和文件列表
                if os.path.exists(self.trigger_manager.shared_triggers_dir):
                    files = os.listdir(self.trigger_manager.shared_triggers_dir)
                    print(f"[CreateTaskDialog] 共享目录文件: {files}")
                else:
                    print(f"[CreateTaskDialog] 共享目录不存在!")
                    
                if os.path.exists(self.trigger_manager.triggers_dir):
                    files = os.listdir(self.trigger_manager.triggers_dir)
                    print(f"[CreateTaskDialog] 本地目录文件: {files}")
                else:
                    print(f"[CreateTaskDialog] 本地目录不存在!")
            else:
                print(f"[CreateTaskDialog] ✅ 成功发现触发器:")
                for trigger in self.custom_triggers:
                    print(f"[CreateTaskDialog]   - {trigger.display_name} (来源: {trigger.source})")
            
        except Exception as e:
            print(f"[CreateTaskDialog] ❌ 触发器初始化异常: {e}")
            import traceback
            traceback.print_exc()
            # 创建空列表避免后续错误
            self.custom_triggers = []
            
        self.custom_param_widgets = {}  # 存储自定义参数控件
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("➕ 创建自动化任务")
        self.dialog.geometry("520x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
        
        # 居中
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 520) // 2
        y = (self.dialog.winfo_screenheight() - 600) // 2
        self.dialog.geometry(f"520x600+{x}+{y}")
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务名称
        ttk.Label(main_frame, text="任务名称:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=50).pack(fill=tk.X, pady=(0, 10))
        
        # 工具选择
        ttk.Label(main_frame, text="选择工具:").pack(anchor=tk.W)
        tool_frame = ttk.Frame(main_frame)
        tool_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 分类
        ttk.Label(tool_frame, text="分类:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="maya")
        category_combo = ttk.Combobox(tool_frame, textvariable=self.category_var,
                                      values=["maya", "max", "blender", "ue", "other"],
                                      state="readonly", width=10)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self._on_category_change)
        
        # 工具
        ttk.Label(tool_frame, text="工具:").pack(side=tk.LEFT, padx=(10, 0))
        self.tool_var = tk.StringVar()
        self.tool_combo = ttk.Combobox(tool_frame, textvariable=self.tool_var, 
                                       state="readonly", width=25)
        self.tool_combo.pack(side=tk.LEFT, padx=5)
        
        # 执行模式
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(mode_frame, text="执行模式:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="standalone")
        ttk.Radiobutton(mode_frame, text="独立运行", variable=self.mode_var, 
                       value="standalone").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="DCC内运行", variable=self.mode_var,
                       value="dcc").pack(side=tk.LEFT)
        
        # 触发类型 - 使用下拉选择
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        trigger_header = ttk.Frame(main_frame)
        trigger_header.pack(fill=tk.X)
        
        ttk.Label(trigger_header, text="触发类型:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # 构建触发器选项列表（内置 + 自定义）
        self.trigger_options = self._build_trigger_options()
        
        # 显示名称变量（用于UI显示）
        self.trigger_display_var = tk.StringVar()
        # 触发器ID变量（用于内部逻辑）
        self.trigger_var = tk.StringVar()
        
        self.trigger_combo = ttk.Combobox(
            trigger_header, 
            textvariable=self.trigger_display_var,
            values=[opt[1] for opt in self.trigger_options],
            state="readonly",
            width=25
        )
        self.trigger_combo.pack(side=tk.LEFT, padx=10)
        
        # 设置默认选项（间隔执行）
        if self.trigger_options:
            default_display = self.trigger_options[0][1]  # 第一个选项的显示名
            self.trigger_combo.set(default_display)
            self.trigger_display_var.set(default_display)
            self.trigger_var.set(self.trigger_options[0][0])  # 对应的ID
        
        self.trigger_combo.bind('<<ComboboxSelected>>', self._on_trigger_combo_change)
        
        # 打开触发器脚本目录按钮
        ttk.Button(
            trigger_header, 
            text="📂 脚本目录", 
            command=self._open_trigger_scripts_folder
        ).pack(side=tk.LEFT, padx=2)
        
        # 刷新触发器按钮
        ttk.Button(
            trigger_header,
            text="🔄",
            width=3,
            command=self._refresh_triggers
        ).pack(side=tk.LEFT)
        
        # 触发器描述
        self.trigger_desc_var = tk.StringVar(value="")
        self.trigger_desc_label = ttk.Label(
            main_frame, 
            textvariable=self.trigger_desc_var,
            foreground='gray',
            wraplength=480
        )
        self.trigger_desc_label.pack(fill=tk.X, pady=(2, 5))
        self._update_trigger_description()
        
        # 触发配置区域
        self.config_frame = ttk.LabelFrame(main_frame, text="触发配置", padding="10")
        self.config_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 初始化触发配置（基于默认选择）
        self._on_trigger_change()
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="创建", command=self._create_task).pack(side=tk.RIGHT)
        
        # 预填充
        if self.prefill_tool:
            self.name_var.set(f"自动执行 - {self.prefill_tool.get('name', '')}")
            self.category_var.set(self.prefill_tool.get('category', 'maya'))
            self._on_category_change(None)
            self.tool_var.set(self.prefill_tool.get('id', ''))
        else:
            self._on_category_change(None)
    
    def _build_trigger_options(self) -> List[tuple]:
        """构建触发器选项列表"""
        options = []
        
        # 所有触发器（包括内置和自定义）都来自 trigger_manager 的发现结果
        for trigger_info in self.custom_triggers:
            # 使用 display_name 作为显示名称，并添加来源标识
            source_label = "📁 共享" if trigger_info.source == "shared" else "💻 本地"
            display_name = f"{trigger_info.display_name} ({source_label})"
            
            options.append((
                trigger_info.name,         # trigger ID
                display_name,              # 中文显示名 + 来源标识
                trigger_info.description,  # 描述
                trigger_info.file_path     # 脚本文件路径
            ))
        
        return options
    
    def _update_trigger_description(self):
        """更新触发器描述"""
        display_name = self.trigger_combo.get()
        for opt in self.trigger_options:
            if opt[1] == display_name:
                self.trigger_desc_var.set(opt[2])
                break
    
    def _get_trigger_value_from_display(self, display_name: str) -> str:
        """从显示名称获取触发器值"""
        for opt in self.trigger_options:
            if opt[1] == display_name:
                return opt[0]
        return "interval"
    
    def _on_trigger_combo_change(self, event):
        """触发器下拉选择变更"""
        display_name = self.trigger_combo.get()
        trigger_value = self._get_trigger_value_from_display(display_name)
        self.trigger_var.set(trigger_value)
        self._update_trigger_description()
        self._on_trigger_change()
    
    def _open_trigger_scripts_folder(self):
        """打开当前选择的触发器脚本所在目录（并选中该脚本文件）"""
        display_name = self.trigger_combo.get()
        
        # 查找当前选择的触发器对应的脚本路径
        script_path = None
        for opt in self.trigger_options:
            if opt[1] == display_name and len(opt) > 3:
                script_path = opt[3]  # 第四个元素是脚本路径
                break
        
        # 如果是自定义触发器，打开脚本所在目录并选中文件
        if script_path:
            script_file = Path(script_path)
            if script_file.exists():
                try:
                    if os.name == 'nt':  # Windows - 使用 explorer /select 选中文件
                        subprocess.run(['explorer', '/select,', str(script_file)], check=False)
                    elif os.name == 'posix':  # macOS/Linux
                        subprocess.run(['xdg-open', str(script_file.parent)], check=True)
                    return
                except Exception as e:
                    messagebox.showerror("错误", f"无法打开目录: {e}")
                    return
        
        # 如果是内置触发器或没有脚本路径，打开触发器脚本根目录
        trigger_dir = self.trigger_manager.triggers_dir
        trigger_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(trigger_dir))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['xdg-open', str(trigger_dir)], check=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {e}\n路径: {trigger_dir}")
    
    def _refresh_triggers(self):
        """刷新触发器列表"""
        self.custom_triggers = self.trigger_manager.discover_triggers()
        self.trigger_options = self._build_trigger_options()
        self.trigger_combo['values'] = [opt[1] for opt in self.trigger_options]
        messagebox.showinfo("提示", f"已刷新触发器列表，发现 {len(self.custom_triggers)} 个自定义触发器")
    
    def _on_category_change(self, event):
        """分类变更"""
        category = self.category_var.get()
        tools = []
        
        for tool_id, info in self.tools_cache.items():
            if info.get('category') == category:
                tools.append(tool_id)
        
        self.tool_combo['values'] = tools
        if tools:
            self.tool_combo.set(tools[0])
    
    def _on_trigger_change(self):
        """触发类型变更"""
        # 清空配置区域
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        
        # 清空自定义参数控件引用
        self.custom_param_widgets = {}
        
        trigger = self.trigger_var.get()
        
        # 统一处理所有触发器 - 现在所有触发器都基于脚本
        # 不再区分内置和自定义，统一使用自定义触发器配置界面
        self._create_custom_trigger_config(trigger)
    
    def _create_custom_trigger_config(self, trigger_value: str):
        """创建自定义触发器配置界面"""
        frame = self.config_frame
        trigger_name = trigger_value.replace("custom:", "")
        
        # 找到对应的触发器信息
        trigger_info = None
        for t in self.custom_triggers:
            if t.name == trigger_name:
                trigger_info = t
                break
        
        if not trigger_info:
            ttk.Label(frame, text="无法加载触发器配置", foreground='red').pack()
            return
        
        # 显示触发器信息
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        script_name = Path(trigger_info.file_path).name
        ttk.Label(info_frame, text=f"脚本: {script_name}", 
                 foreground='gray').pack(anchor=tk.W)
        
        # 如果没有参数，显示提示
        if not trigger_info.parameters:
            ttk.Label(frame, text="此触发器无需配置参数").pack(anchor=tk.W, pady=10)
            return
        
        # 参数配置
        ttk.Label(frame, text="参数配置:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        params_frame = ttk.Frame(frame)
        params_frame.pack(fill=tk.X)
        
        for param_name, param_def in trigger_info.parameters.items():
            row = ttk.Frame(params_frame)
            row.pack(fill=tk.X, pady=3)
            
            # 参数标签
            param_type = param_def.get('type', 'string')
            param_default = param_def.get('default', '')
            param_desc = param_def.get('description', param_name)
            
            # 创建参数标签并添加工具提示
            label = ttk.Label(row, text=f"{param_desc}:", width=15)
            label.pack(side=tk.LEFT)
            
            # 构建工具提示文本
            tooltip_text = build_param_tooltip(param_name, param_def)
            if tooltip_text:
                ToolTip(label, tooltip_text)
            
            # 根据类型创建不同的控件
            if param_type == 'bool':
                var = tk.BooleanVar(value=param_default if isinstance(param_default, bool) else False)
                widget = ttk.Checkbutton(row, variable=var)
                widget.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('bool', var)
                
            elif param_type == 'int':
                var = tk.StringVar(value=str(param_default))
                min_val = param_def.get('min', 0)
                max_val = param_def.get('max', 9999)
                widget = ttk.Spinbox(row, from_=min_val, to=max_val, textvariable=var, width=10)
                widget.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('int', var)
                
            elif param_type == 'float':
                var = tk.StringVar(value=str(param_default))
                widget = ttk.Entry(row, textvariable=var, width=15)
                widget.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('float', var)
                
            elif param_type == 'choice':
                choices = param_def.get('choices', [])
                var = tk.StringVar(value=param_default if param_default in choices else (choices[0] if choices else ''))
                widget = ttk.Combobox(row, textvariable=var, values=choices, state='readonly', width=15)
                widget.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('choice', var)
                
            else:  # string 或其他
                var = tk.StringVar(value=str(param_default))
                widget = ttk.Entry(row, textvariable=var, width=25)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.custom_param_widgets[param_name] = ('string', var)
            
            # 为控件也添加工具提示
            if tooltip_text:
                ToolTip(widget, tooltip_text)
        
        # 添加编辑脚本按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame, 
            text="📝 编辑触发器脚本",
            command=lambda: self._open_trigger_script(trigger_info.file_path)
        ).pack(side=tk.LEFT)
    
    
    def _edit_current_trigger_script(self):
        """编辑当前选中的触发器脚本"""
        display_name = self.trigger_combo.get()
        
        # 查找当前选择的触发器对应的脚本路径
        script_path = None
        for opt in self.trigger_options:
            if opt[1] == display_name and len(opt) > 3:
                script_path = opt[3]  # 第四个元素是脚本路径
                break
        
        if script_path:
            self._open_trigger_script(script_path)
        else:
            messagebox.showwarning("提示", "无法找到当前触发器的脚本文件")
    
    def _open_trigger_script(self, script_path: str):
        """打开触发器脚本进行编辑"""
        try:
            script_file = Path(script_path)
            
            if not script_file.exists():
                messagebox.showerror("错误", f"脚本文件不存在: {script_file}")
                return
            
            success = False
            
            if os.name == 'nt':  # Windows
                try:
                    # 优先使用记事本打开（最可靠）
                    subprocess.run(['notepad.exe', str(script_file)], check=True)
                    success = True
                except Exception:
                    try:
                        # 备选：使用默认关联程序
                        os.startfile(str(script_file))
                        success = True
                    except Exception:
                        try:
                            # 最后：用资源管理器选中文件
                            subprocess.run(['explorer', '/select,', str(script_file)], check=True)
                            success = True
                        except Exception:
                            pass
            
            elif os.name == 'posix':  # macOS/Linux
                try:
                    subprocess.run(['xdg-open', str(script_file)], check=True)
                    success = True
                except Exception:
                    pass
            
            if not success:
                # 如果所有方法都失败，提供手动方式
                result = messagebox.askyesno(
                    "打开失败", 
                    f"无法自动打开文件。\n\n文件路径:\n{script_file.absolute()}\n\n是否复制路径到剪贴板？"
                )
                if result:
                    self.dialog.clipboard_clear()
                    self.dialog.clipboard_append(str(script_file.absolute()))
                    messagebox.showinfo("已复制", "文件路径已复制到剪贴板，您可以手动打开")
                    
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")
    
    def _create_interval_config(self):
        """创建间隔执行配置"""
        frame = self.config_frame
        
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=5)
        
        ttk.Label(row, text="每隔").pack(side=tk.LEFT)
        self.interval_value_var = tk.StringVar(value="30")
        ttk.Entry(row, textvariable=self.interval_value_var, width=8).pack(side=tk.LEFT, padx=5)
        
        self.interval_unit_var = tk.StringVar(value="minutes")
        ttk.Combobox(row, textvariable=self.interval_unit_var,
                    values=["seconds", "minutes", "hours"],
                    state="readonly", width=10).pack(side=tk.LEFT)
        
        ttk.Label(row, text="执行一次").pack(side=tk.LEFT, padx=5)
        
        # 预设
        preset_frame = ttk.Frame(frame)
        preset_frame.pack(fill=tk.X, pady=10)
        ttk.Label(preset_frame, text="快捷预设:").pack(side=tk.LEFT)
        
        presets = [("5分钟", 5, "minutes"), ("30分钟", 30, "minutes"), 
                   ("1小时", 1, "hours"), ("2小时", 2, "hours")]
        for text, val, unit in presets:
            ttk.Button(preset_frame, text=text, width=8,
                      command=lambda v=val, u=unit: self._set_interval(v, u)).pack(side=tk.LEFT, padx=2)
    
    def _set_interval(self, value, unit):
        """设置间隔预设"""
        self.interval_value_var.set(str(value))
        self.interval_unit_var.set(unit)
    
    def _create_scheduled_config(self):
        """创建定时执行配置"""
        frame = self.config_frame
        
        # 时间选择
        time_row = ttk.Frame(frame)
        time_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_row, text="执行时间:").pack(side=tk.LEFT)
        self.scheduled_hour_var = tk.StringVar(value="09")
        hour_spin = ttk.Spinbox(time_row, from_=0, to=23, width=3,
                               textvariable=self.scheduled_hour_var, format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_row, text=":").pack(side=tk.LEFT)
        
        self.scheduled_minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(time_row, from_=0, to=59, width=3,
                                 textvariable=self.scheduled_minute_var, format="%02.0f")
        minute_spin.pack(side=tk.LEFT, padx=5)
        
        # 星期选择
        ttk.Label(frame, text="执行日期:").pack(anchor=tk.W, pady=(10, 5))
        
        days_frame = ttk.Frame(frame)
        days_frame.pack(fill=tk.X)
        
        self.day_vars = {}
        days = [("mon", "周一"), ("tue", "周二"), ("wed", "周三"), 
                ("thu", "周四"), ("fri", "周五"), ("sat", "周六"), ("sun", "周日")]
        
        for day_id, day_name in days:
            var = tk.BooleanVar(value=day_id not in ["sat", "sun"])
            self.day_vars[day_id] = var
            ttk.Checkbutton(days_frame, text=day_name, variable=var).pack(side=tk.LEFT, padx=3)
        
        # 快捷按钮
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(quick_frame, text="工作日", 
                  command=lambda: self._set_days(["mon","tue","wed","thu","fri"])).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="每天",
                  command=lambda: self._set_days(["mon","tue","wed","thu","fri","sat","sun"])).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="周末",
                  command=lambda: self._set_days(["sat","sun"])).pack(side=tk.LEFT, padx=2)
    
    def _set_days(self, days: List[str]):
        """设置日期"""
        for day_id, var in self.day_vars.items():
            var.set(day_id in days)
    
    def _create_file_watch_config(self):
        """创建文件监控配置"""
        frame = self.config_frame
        
        ttk.Label(frame, text="监控路径 (每行一个):").pack(anchor=tk.W)
        
        self.watch_paths_text = tk.Text(frame, height=5, width=50)
        self.watch_paths_text.pack(fill=tk.X, pady=5)
        
        browse_btn = ttk.Button(frame, text="📁 浏览添加", command=self._browse_watch_path)
        browse_btn.pack(anchor=tk.W)
        
        # 防抖设置
        debounce_row = ttk.Frame(frame)
        debounce_row.pack(fill=tk.X, pady=10)
        
        ttk.Label(debounce_row, text="防抖时间:").pack(side=tk.LEFT)
        self.debounce_var = tk.StringVar(value="5")
        ttk.Entry(debounce_row, textvariable=self.debounce_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(debounce_row, text="秒 (文件变化后等待此时间再触发)").pack(side=tk.LEFT)
    
    def _browse_watch_path(self):
        """浏览选择监控路径"""
        from tkinter import filedialog
        path = filedialog.askdirectory(parent=self.dialog)
        if path:
            current = self.watch_paths_text.get('1.0', tk.END).strip()
            if current:
                self.watch_paths_text.insert(tk.END, f"\n{path}")
            else:
                self.watch_paths_text.insert('1.0', path)
    
    def _create_task_chain_config(self):
        """创建任务链配置"""
        frame = self.config_frame
        
        ttk.Label(frame, text="选择要依次执行的任务:").pack(anchor=tk.W)
        
        # 任务列表
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chain_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.chain_listbox.yview)
        self.chain_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.chain_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充现有任务
        for task in self.manager.get_all_tasks():
            if task.trigger_type != TriggerType.TASK_CHAIN.value:
                self.chain_listbox.insert(tk.END, f"{task.name} ({task.id})")
        
        # 选项
        opt_frame = ttk.Frame(frame)
        opt_frame.pack(fill=tk.X, pady=5)
        
        self.stop_on_error_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="出错时停止后续任务", 
                       variable=self.stop_on_error_var).pack(side=tk.LEFT)
        
        ttk.Label(opt_frame, text="任务间隔:").pack(side=tk.LEFT, padx=(20, 0))
        self.chain_delay_var = tk.StringVar(value="2")
        ttk.Entry(opt_frame, textvariable=self.chain_delay_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(opt_frame, text="秒").pack(side=tk.LEFT)
    
    def _create_task(self):
        """创建任务"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入任务名称")
            return
        
        tool_id = self.tool_var.get()
        if not tool_id:
            messagebox.showwarning("提示", "请选择工具")
            return
        
        category = self.category_var.get()
        mode = self.mode_var.get()
        trigger = self.trigger_var.get()
        
        # 收集触发配置
        trigger_config = {}
        
        # 触发器已经是正确的类型名称，无需映射
        # 内置触发器的name就是其类型名
        builtin_types = {"interval", "scheduled", "file_watch", "task_chain"}
        
        # 对于动态发现的触发器，保持原名称而不是设为 "custom"
        actual_trigger_type = trigger
        
        # 统一从自定义参数收集配置（现在所有触发器都使用这种方式）
        if actual_trigger_type in builtin_types:
            # 内置触发器类型，需要转换参数格式
            custom_params = {}
            for param_name, (param_type, var) in self.custom_param_widgets.items():
                try:
                    if param_type == 'bool':
                        custom_params[param_name] = var.get()
                    elif param_type == 'int':
                        custom_params[param_name] = int(var.get())
                    elif param_type == 'float':
                        custom_params[param_name] = float(var.get())
                    else:
                        custom_params[param_name] = var.get()
                except ValueError:
                    messagebox.showwarning("提示", f"参数 '{param_name}' 值无效")
                    return
            
            # 根据触发器类型转换参数格式
            if actual_trigger_type == "interval":
                trigger_config = {
                    "value": custom_params.get("interval_value", 30),
                    "unit": custom_params.get("interval_unit", "minutes")
                }
            elif actual_trigger_type == "scheduled":
                time_str = custom_params.get("time", "09:00")
                days_str = custom_params.get("days", "周一,周二,周三,周四,周五")
                
                # 如果是中文格式，需要转换为英文
                if "周" in days_str:
                    day_map = {
                        "周一": "mon", "周二": "tue", "周三": "wed", "周四": "thu", 
                        "周五": "fri", "周六": "sat", "周日": "sun"
                    }
                    chinese_days = [d.strip() for d in days_str.split(",") if d.strip()]
                    english_days = [day_map.get(d, d) for d in chinese_days]
                else:
                    english_days = [d.strip() for d in days_str.split(",") if d.strip()]
                
                trigger_config = {
                    "time": time_str,
                    "days": english_days
                }
            elif actual_trigger_type == "file_watch":
                paths_str = custom_params.get("watch_paths", "")
                # 监控路径用分号分隔（根据参数描述）
                path_list = [p.strip() for p in paths_str.split(";") if p.strip()] if paths_str else []
                trigger_config = {
                    "watch_paths": path_list,
                    "debounce_seconds": custom_params.get("debounce_seconds", 5)
                }
            elif actual_trigger_type == "task_chain":
                tasks_str = custom_params.get("tasks", "")
                # 任务ID列表用分号分隔（根据参数描述）
                task_list = [t.strip() for t in tasks_str.split(";") if t.strip()] if tasks_str else []
                trigger_config = {
                    "tasks": task_list,
                    "stop_on_error": custom_params.get("stop_on_error", True),
                    "delay_between": custom_params.get("delay_between", 2)
                }
        else:
            # 动态触发器（保持原名称）
            # actual_trigger_type 已经正确设置为触发器的真实名称
            
            # 收集自定义参数
            custom_params = {}
            for param_name, (param_type, var) in self.custom_param_widgets.items():
                try:
                    if param_type == 'bool':
                        custom_params[param_name] = var.get()
                    elif param_type == 'int':
                        custom_params[param_name] = int(var.get())
                    elif param_type == 'float':
                        custom_params[param_name] = float(var.get())
                    else:
                        custom_params[param_name] = var.get()
                except ValueError:
                    messagebox.showwarning("提示", f"参数 '{param_name}' 值无效")
                    return
            
            trigger_config = {
                "trigger_script_id": trigger,
                "trigger_parameters": custom_params
            }
        
        # 创建任务
        try:
            # 对于动态触发器，使用CUSTOM类型，但在config中保存真实名称
            if actual_trigger_type in builtin_types:
                trigger_type = TriggerType(actual_trigger_type)
            else:
                trigger_type = TriggerType.CUSTOM
            task = self.manager.create_task(
                name=name,
                trigger_type=trigger_type,
                tool_id=tool_id,
                tool_category=category,
                execution_mode=mode,
                trigger_config=trigger_config
            )
            
            # 调试信息 - 检查创建的任务
            print(f"[DEBUG] 创建任务成功:")
            print(f"  任务名: {task.name}")
            print(f"  触发器类型: {task.trigger_type}")
            print(f"  actual_trigger_type: {actual_trigger_type}")
            print(f"  原始trigger: {trigger}")
            
            messagebox.showinfo("成功", f"任务 '{name}' 创建成功！")
            
            if self.on_created:
                self.on_created()
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败: {e}")
