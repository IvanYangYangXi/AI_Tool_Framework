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
        """创建详情面板"""
        detail_frame = ttk.LabelFrame(parent, text="任务详情", padding="10")
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
        
        # 详情内容
        self._create_detail_content()
    
    def _create_detail_content(self):
        """创建详情内容"""
        frame = self.detail_inner
        
        # 基本信息
        info_frame = ttk.LabelFrame(frame, text="基本信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 任务名称
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="名称:", width=10).pack(side=tk.LEFT)
        self.detail_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.detail_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 工具
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="工具:", width=10).pack(side=tk.LEFT)
        self.detail_tool_var = tk.StringVar()
        ttk.Label(row2, textvariable=self.detail_tool_var).pack(side=tk.LEFT)
        
        # 状态
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="状态:", width=10).pack(side=tk.LEFT)
        self.detail_status_var = tk.StringVar()
        ttk.Label(row3, textvariable=self.detail_status_var).pack(side=tk.LEFT)
        
        # 触发配置
        trigger_frame = ttk.LabelFrame(frame, text="触发配置", padding="10")
        trigger_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.detail_trigger_text = tk.Text(trigger_frame, height=6, wrap=tk.WORD)
        self.detail_trigger_text.pack(fill=tk.X)
        self.detail_trigger_text.configure(state='disabled')
        
        # 执行历史
        history_frame = ttk.LabelFrame(frame, text="执行历史", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        hist_row1 = ttk.Frame(history_frame)
        hist_row1.pack(fill=tk.X, pady=2)
        ttk.Label(hist_row1, text="运行次数:").pack(side=tk.LEFT)
        self.detail_run_count_var = tk.StringVar(value="0")
        ttk.Label(hist_row1, textvariable=self.detail_run_count_var).pack(side=tk.LEFT, padx=5)
        
        hist_row2 = ttk.Frame(history_frame)
        hist_row2.pack(fill=tk.X, pady=2)
        ttk.Label(hist_row2, text="上次运行:").pack(side=tk.LEFT)
        self.detail_last_run_var = tk.StringVar(value="-")
        ttk.Label(hist_row2, textvariable=self.detail_last_run_var).pack(side=tk.LEFT, padx=5)
        
        hist_row3 = ttk.Frame(history_frame)
        hist_row3.pack(fill=tk.X, pady=2)
        ttk.Label(hist_row3, text="下次运行:").pack(side=tk.LEFT)
        self.detail_next_run_var = tk.StringVar(value="-")
        ttk.Label(hist_row3, textvariable=self.detail_next_run_var).pack(side=tk.LEFT, padx=5)
        
        # 错误信息
        error_frame = ttk.LabelFrame(frame, text="错误信息", padding="10")
        error_frame.pack(fill=tk.X)
        
        self.detail_error_var = tk.StringVar(value="-")
        ttk.Label(error_frame, textvariable=self.detail_error_var, 
                 foreground='red', wraplength=300).pack(fill=tk.X)
        
        # 保存按钮
        ttk.Button(frame, text="💾 保存修改", 
                  command=self._save_task_changes).pack(fill=tk.X, pady=(10, 0))
    
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
            trigger_name = self._get_trigger_name(task.trigger_type)
            
            next_run = task.next_run or "-"
            if next_run not in ["-", "文件变更时", "手动触发"]:
                try:
                    dt = datetime.fromisoformat(next_run)
                    next_run = dt.strftime("%m-%d %H:%M")
                except:
                    pass
            
            self.task_tree.insert('', 'end', iid=task.id,
                                 text=f"{'✓' if task.enabled else '○'} {task.name}",
                                 values=(trigger_name, task.tool_id, 
                                        status_icon, next_run))
    
    def _on_task_select(self, event):
        """任务选择事件"""
        selection = self.task_tree.selection()
        if not selection:
            return
        
        self.selected_task_id = selection[0]
        task = self.manager.get_task(self.selected_task_id)
        if task:
            self._show_task_detail(task)
    
    def _show_task_detail(self, task: AutomationTask):
        """显示任务详情"""
        self.detail_name_var.set(task.name)
        self.detail_tool_var.set(f"{task.tool_id} ({task.tool_category})")
        self.detail_status_var.set(self._get_status_text(task.status))
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
        self.detail_error_var.set(task.last_error or "-")
        
        # 触发配置
        self.detail_trigger_text.configure(state='normal')
        self.detail_trigger_text.delete('1.0', tk.END)
        
        trigger_info = f"触发类型: {self._get_trigger_name(task.trigger_type)}\n\n"
        
        if task.trigger_type == TriggerType.SCHEDULED.value:
            config = task.scheduled_config or {}
            trigger_info += f"执行时间: {config.get('time', '09:00')}\n"
            trigger_info += f"执行日期: {', '.join(config.get('days', ['everyday']))}"
        
        elif task.trigger_type == TriggerType.INTERVAL.value:
            config = task.interval_config or {}
            unit_map = {'seconds': '秒', 'minutes': '分钟', 'hours': '小时'}
            trigger_info += f"间隔: 每 {config.get('value', 30)} {unit_map.get(config.get('unit', 'minutes'), '分钟')}"
        
        elif task.trigger_type == TriggerType.FILE_WATCH.value:
            config = task.file_watch_config or {}
            trigger_info += f"监控路径:\n"
            for path in config.get('watch_paths', []):
                trigger_info += f"  - {path}\n"
            trigger_info += f"防抖: {config.get('debounce_seconds', 5)}秒"
        
        elif task.trigger_type == TriggerType.TASK_CHAIN.value:
            config = task.task_chain_config or {}
            trigger_info += f"任务链:\n"
            for tid in config.get('tasks', []):
                t = self.manager.get_task(tid)
                trigger_info += f"  - {t.name if t else tid}\n"
        
        self.detail_trigger_text.insert('1.0', trigger_info)
        self.detail_trigger_text.configure(state='disabled')
    
    def _get_status_icon(self, status: str) -> str:
        """获取状态图标"""
        icons = {
            'idle': '⚪',
            'waiting': '🟢',
            'running': '🔵',
            'paused': '🟡',
            'error': '🔴',
            'completed': '✅'
        }
        return icons.get(status, '⚪')
    
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
    
    def _get_trigger_name(self, trigger_type: str) -> str:
        """获取触发器名称"""
        names = {
            'scheduled': '⏰ 定时',
            'interval': '🔄 间隔',
            'file_watch': '📁 文件监控',
            'task_chain': '🔗 任务链'
        }
        return names.get(trigger_type, trigger_type)
    
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
    
    def _save_task_changes(self):
        """保存任务修改"""
        if not self.selected_task_id:
            return
        
        new_name = self.detail_name_var.get().strip()
        if new_name:
            self.manager.update_task(self.selected_task_id, name=new_name)
            self._refresh_task_list()
            messagebox.showinfo("提示", "保存成功")
    
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
            # 使用 display_name 作为显示名称（已经是中文）
            display_name = trigger_info.display_name
            options.append((
                trigger_info.name,         # trigger ID
                display_name,              # 中文显示名
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
            
            ttk.Label(row, text=f"{param_desc}:", width=15).pack(side=tk.LEFT)
            
            # 根据类型创建不同的控件
            if param_type == 'bool':
                var = tk.BooleanVar(value=param_default if isinstance(param_default, bool) else False)
                ttk.Checkbutton(row, variable=var).pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('bool', var)
                
            elif param_type == 'int':
                var = tk.StringVar(value=str(param_default))
                min_val = param_def.get('min', 0)
                max_val = param_def.get('max', 9999)
                spin = ttk.Spinbox(row, from_=min_val, to=max_val, textvariable=var, width=10)
                spin.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('int', var)
                
            elif param_type == 'float':
                var = tk.StringVar(value=str(param_default))
                entry = ttk.Entry(row, textvariable=var, width=15)
                entry.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('float', var)
                
            elif param_type == 'choice':
                choices = param_def.get('choices', [])
                var = tk.StringVar(value=param_default if param_default in choices else (choices[0] if choices else ''))
                combo = ttk.Combobox(row, textvariable=var, values=choices, state='readonly', width=15)
                combo.pack(side=tk.LEFT)
                self.custom_param_widgets[param_name] = ('choice', var)
                
            else:  # string 或其他
                var = tk.StringVar(value=str(param_default))
                entry = ttk.Entry(row, textvariable=var, width=25)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.custom_param_widgets[param_name] = ('string', var)
        
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
        actual_trigger_type = trigger  # 实际存储的触发类型
        
        if trigger == "interval":
            try:
                value = int(self.interval_value_var.get())
            except ValueError:
                messagebox.showwarning("提示", "间隔值必须是数字")
                return
            trigger_config = {
                "value": value,
                "unit": self.interval_unit_var.get()
            }
        
        elif trigger == "scheduled":
            hour = self.scheduled_hour_var.get().zfill(2)
            minute = self.scheduled_minute_var.get().zfill(2)
            days = [d for d, v in self.day_vars.items() if v.get()]
            if not days:
                messagebox.showwarning("提示", "请至少选择一天")
                return
            trigger_config = {
                "time": f"{hour}:{minute}",
                "days": days
            }
        
        elif trigger == "file_watch":
            paths = [p.strip() for p in self.watch_paths_text.get('1.0', tk.END).strip().split('\n') if p.strip()]
            if not paths:
                messagebox.showwarning("提示", "请添加监控路径")
                return
            try:
                debounce = int(self.debounce_var.get())
            except ValueError:
                debounce = 5
            trigger_config = {
                "watch_paths": paths,
                "debounce_seconds": debounce
            }
        
        elif trigger == "task_chain":
            selected = self.chain_listbox.curselection()
            if not selected:
                messagebox.showwarning("提示", "请选择要执行的任务")
                return
            
            task_ids = []
            for idx in selected:
                text = self.chain_listbox.get(idx)
                # 提取task_id
                import re
                match = re.search(r'\((task_\w+)\)$', text)
                if match:
                    task_ids.append(match.group(1))
            
            try:
                delay = int(self.chain_delay_var.get())
            except ValueError:
                delay = 2
            
            trigger_config = {
                "tasks": task_ids,
                "stop_on_error": self.stop_on_error_var.get(),
                "delay_between": delay
            }
        
        else:
            # 其他触发器（包括新的内置触发器）当作自定义触发器处理
            actual_trigger_type = "custom"
            trigger_name = trigger
            
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
                "trigger_name": trigger_name,
                "parameters": custom_params
            }
        
        # 创建任务
        try:
            trigger_type = TriggerType(actual_trigger_type)
            task = self.manager.create_task(
                name=name,
                trigger_type=trigger_type,
                tool_id=tool_id,
                tool_category=category,
                execution_mode=mode,
                trigger_config=trigger_config
            )
            
            messagebox.showinfo("成功", f"任务 '{name}' 创建成功！")
            
            if self.on_created:
                self.on_created()
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败: {e}")
