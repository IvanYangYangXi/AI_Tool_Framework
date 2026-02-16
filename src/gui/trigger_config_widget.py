"""
触发器配置UI组件

提供可重用的触发器配置界面组件，避免代码重复
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Callable
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


class TriggerConfigWidget:
    """
    触发器配置控件
    
    可重用的触发器配置界面组件，支持：
    - 内置触发器类型（间隔、定时、文件监控、任务链）
    - 自定义触发器脚本
    - 参数验证和收集
    - 工具提示显示
    """
    
    def __init__(self, parent_frame: ttk.Frame, trigger_manager=None):
        """
        初始化触发器配置控件
        
        Args:
            parent_frame: 父级Frame容器
            trigger_manager: 触发器管理器实例
        """
        self.parent = parent_frame
        self.trigger_manager = trigger_manager
        
        # 控件存储
        self.config_widgets = {}  # 存储配置控件引用
        self.current_trigger_type = None
        
        # 创建主容器
        self.container = ttk.Frame(parent_frame)
        self.container.pack(fill=tk.BOTH, expand=True)
    
    def clear_widgets(self):
        """清空所有配置控件"""
        try:
            for widget in self.container.winfo_children():
                widget.destroy()
        except tk.TclError:
            # 容器可能已经被销毁
            pass
        self.config_widgets.clear()
    
    def create_interval_config(self, config: Dict = None) -> Dict[str, tk.Variable]:
        """创建间隔触发配置"""
        config = config or {}
        self.clear_widgets()
        self.current_trigger_type = "interval"
        
        # 检查容器是否有效
        try:
            if not self.container.winfo_exists():
                return {}
        except tk.TclError:
            return {}
        
        # 主要配置行
        row = ttk.Frame(self.container)
        row.pack(fill=tk.X, pady=5)
        
        ttk.Label(row, text="每隔").pack(side=tk.LEFT)
        
        # 数值输入 - 兼容多种键名
        interval_value = config.get('interval_value', config.get('value', 30))
        value_var = tk.StringVar(value=str(interval_value))
        value_entry = ttk.Entry(row, textvariable=value_var, width=10)
        value_entry.pack(side=tk.LEFT, padx=5)
        
        # 单位选择 - 兼容多种键名  
        interval_unit = config.get('interval_unit', config.get('unit', 'minutes'))
        unit_var = tk.StringVar(value=interval_unit)
        unit_combo = ttk.Combobox(row, textvariable=unit_var,
                                values=['seconds', 'minutes', 'hours'],
                                state='readonly', width=10)
        unit_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row, text="执行一次").pack(side=tk.LEFT, padx=5)
        
        # 快捷预设按钮
        preset_frame = ttk.Frame(self.container)
        preset_frame.pack(fill=tk.X, pady=10)
        ttk.Label(preset_frame, text="快捷预设:").pack(side=tk.LEFT)
        
        presets = [("5分钟", 5, "minutes"), ("30分钟", 30, "minutes"), 
                   ("1小时", 1, "hours"), ("2小时", 2, "hours")]
        
        for text, val, unit in presets:
            def set_preset(v=val, u=unit):
                value_var.set(str(v))
                unit_var.set(u)
            
            ttk.Button(preset_frame, text=text, width=8,
                      command=set_preset).pack(side=tk.LEFT, padx=2)
        
        # 存储控件引用 - 格式：(type, variable)
        self.config_widgets = {
            'interval_value': ('int', value_var),
            'interval_unit': ('string', unit_var)
        }
        
        return self.config_widgets
    
    def create_scheduled_config(self, config: Dict = None) -> Dict[str, tk.Variable]:
        """创建定时触发配置"""
        config = config or {}
        self.clear_widgets()
        self.current_trigger_type = "scheduled"
        
        # 时间设置
        time_row = ttk.Frame(self.container)
        time_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_row, text="执行时间:").pack(side=tk.LEFT)
        
        time_str = config.get('time', '09:00')
        hour, minute = time_str.split(':') if ':' in time_str else ('09', '00')
        
        # 小时
        hour_var = tk.StringVar(value=hour)
        hour_spin = ttk.Spinbox(time_row, from_=0, to=23, textvariable=hour_var,
                               width=3, format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_row, text=":").pack(side=tk.LEFT)
        
        # 分钟
        minute_var = tk.StringVar(value=minute)
        minute_spin = ttk.Spinbox(time_row, from_=0, to=59, textvariable=minute_var,
                                 width=3, format="%02.0f")
        minute_spin.pack(side=tk.LEFT, padx=5)
        
        # 日期选择
        ttk.Label(self.container, text="执行日期:").pack(anchor=tk.W, pady=(10, 5))
        
        days_frame = ttk.Frame(self.container)
        days_frame.pack(fill=tk.X)
        
        selected_days = config.get('days', [])
        day_vars = {}
        days = [("mon", "周一"), ("tue", "周二"), ("wed", "周三"), 
                ("thu", "周四"), ("fri", "周五"), ("sat", "周六"), ("sun", "周日")]
        
        for day_id, day_name in days:
            var = tk.BooleanVar(value=day_id in selected_days)
            ttk.Checkbutton(days_frame, text=day_name, variable=var).pack(side=tk.LEFT, padx=5)
            day_vars[f'day_{day_id}'] = var
        
        # 存储控件引用 - 格式：(type, variable)
        self.config_widgets = {
            'scheduled_hour': ('string', hour_var),
            'scheduled_minute': ('string', minute_var),
        }
        # 添加日期变量
        for day_key, day_var in day_vars.items():
            self.config_widgets[day_key] = ('bool', day_var)
        
        return self.config_widgets
    
    def create_file_watch_config(self, config: Dict = None) -> Dict[str, tk.Variable]:
        """创建文件监控配置"""
        config = config or {}
        self.clear_widgets()
        self.current_trigger_type = "file_watch"
        
        # 监控路径
        path_row = ttk.Frame(self.container)
        path_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_row, text="监控路径:").pack(side=tk.LEFT)
        path_var = tk.StringVar(value=config.get('watch_path', ''))
        ttk.Entry(path_row, textvariable=path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 浏览按钮
        def browse_folder():
            from tkinter import filedialog
            folder = filedialog.askdirectory(initialdir=path_var.get() or '.')
            if folder:
                path_var.set(folder)
        
        ttk.Button(path_row, text="浏览", command=browse_folder).pack(side=tk.LEFT)
        
        # 文件模式
        pattern_row = ttk.Frame(self.container)
        pattern_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(pattern_row, text="文件模式:").pack(side=tk.LEFT)
        pattern_var = tk.StringVar(value=config.get('pattern', '*.*'))
        ttk.Entry(pattern_row, textvariable=pattern_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # 递归监控
        recursive_var = tk.BooleanVar(value=config.get('recursive', False))
        ttk.Checkbutton(pattern_row, text="包含子目录", variable=recursive_var).pack(side=tk.LEFT, padx=10)
        
        # 存储控件引用 - 格式：(type, variable)
        self.config_widgets = {
            'watch_path': ('string', path_var),
            'pattern': ('string', pattern_var),
            'recursive': ('bool', recursive_var)
        }
        
        return self.config_widgets
    
    def create_task_chain_config(self, config: Dict = None, 
                                 available_tasks: List[Dict] = None,
                                 available_tools: List[Dict] = None) -> Dict[str, tk.Variable]:
        """
        创建任务链配置 - 支持添加多个脚本按顺序执行
        
        Args:
            config: 现有配置（编辑模式时）
            available_tasks: 可用任务列表（暂不使用）
            available_tools: 可用工具列表 [{"id": "xxx", "name": "工具名", "category": "分类"}, ...]
        """
        config = config or {}
        self.clear_widgets()
        self.current_trigger_type = "task_chain"
        
        # 检查容器是否有效
        try:
            if not self.container.winfo_exists():
                return {}
        except tk.TclError:
            return {}
        
        # 处理传入的工具列表
        if available_tools is None:
            available_tools = config.get('available_tools', [])
        
        # 确保是列表类型
        if isinstance(available_tools, list) and len(available_tools) > 0:
            if isinstance(available_tools[0], str):
                available_tools = [{"id": t, "name": t, "category": ""} for t in available_tools]
        
        # =========== 说明标签 ===========
        info_frame = ttk.Frame(self.container)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(info_frame, text="📋 任务链：添加脚本，任务触发时按顺序执行", 
                  foreground='#0066cc').pack(anchor=tk.W)
        
        # =========== 工具选择下拉框（第一行：下拉框） ===========
        select_frame = ttk.Frame(self.container)
        select_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(select_frame, text="选择脚本:").pack(side=tk.LEFT)
        
        # 构建工具选项列表
        tool_options = []
        self._tool_id_map = {}  # 显示名 -> ID
        self._tool_category_map = {}  # 显示名 -> category
        for tool_info in available_tools:
            if isinstance(tool_info, dict):
                tool_id = tool_info.get('id', '')
                tool_name = tool_info.get('name', tool_id)
                tool_category = tool_info.get('category', '')
                display_name = f"{tool_name}" + (f" ({tool_category})" if tool_category else "")
            else:
                tool_id = str(tool_info)
                tool_category = ''
                display_name = str(tool_info)
            
            tool_options.append(display_name)
            self._tool_id_map[display_name] = tool_id
            self._tool_category_map[display_name] = tool_category
        
        if not tool_options:
            tool_options = ["(暂无可用工具)"]
        
        self._tool_select_var = tk.StringVar()
        tool_combo = ttk.Combobox(select_frame, textvariable=self._tool_select_var,
                                   values=tool_options, state='readonly')
        tool_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # =========== 运行模式选择（第二行） ===========
        mode_frame = ttk.Frame(self.container)
        mode_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mode_frame, text="运行模式:").pack(side=tk.LEFT)
        
        self._chain_mode_var = tk.StringVar(value="standalone")
        ttk.Radiobutton(mode_frame, text="独立运行", variable=self._chain_mode_var, 
                       value="standalone").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="DCC内运行", variable=self._chain_mode_var,
                       value="dcc").pack(side=tk.LEFT, padx=5)
        
        # 添加按钮
        add_btn = ttk.Button(mode_frame, text="添加 ➕", width=10,
                             command=lambda: self._add_chain_tool())
        add_btn.pack(side=tk.RIGHT)
        
        # =========== 已添加的脚本列表 ===========
        list_label_frame = ttk.Frame(self.container)
        list_label_frame.pack(fill=tk.X, pady=(10, 2))
        ttk.Label(list_label_frame, text="执行顺序 (从上到下依次执行):").pack(anchor=tk.W)
        
        # 列表框和滚动条
        list_frame = ttk.Frame(self.container)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._chain_listbox = tk.Listbox(list_frame, height=6, 
                                          yscrollcommand=scrollbar.set,
                                          selectmode=tk.SINGLE)
        self._chain_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._chain_listbox.yview)
        
        # 存储脚本链数据: [(display_name, tool_id), ...]
        self._chain_tools = []
        
        # 加载现有配置
        existing_chain = config.get('chain_tools', [])
        for item in existing_chain:
            if isinstance(item, dict):
                tool_id = item.get('id', '')
                tool_name = item.get('name', tool_id)
                tool_category = item.get('category', '')
                execution_mode = item.get('mode', 'standalone')
            else:
                tool_id = str(item)
                tool_name = str(item)
                tool_category = ''
                execution_mode = 'standalone'
            
            # 查找显示名
            display_name = tool_name
            for dn, tid in self._tool_id_map.items():
                if tid == tool_id:
                    display_name = dn
                    break
            
            # 运行模式显示名
            mode_label = "独立" if execution_mode == "standalone" else "DCC"
            
            # 存储完整的4元组
            self._chain_tools.append((display_name, tool_id, tool_category, execution_mode))
            display_text = f"  {len(self._chain_tools)}. [{mode_label}] {display_name}"
            self._chain_listbox.insert(tk.END, display_text)
        
        # =========== 操作按钮 ===========
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="⬆ 上移", width=8,
                   command=lambda: self._move_chain_tool(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⬇ 下移", width=8,
                   command=lambda: self._move_chain_tool(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑 删除", width=8,
                   command=lambda: self._remove_chain_tool()).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="清空全部", width=8,
                   command=lambda: self._clear_chain_tools()).pack(side=tk.RIGHT, padx=2)
        
        # =========== 执行选项 ===========
        option_frame = ttk.LabelFrame(self.container, text="执行选项")
        option_frame.pack(fill=tk.X, pady=10)
        
        # 错误处理选项
        error_row = ttk.Frame(option_frame)
        error_row.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(error_row, text="遇到错误时:", width=12).pack(side=tk.LEFT)
        
        self._on_error_var = tk.StringVar(value=config.get('on_error', 'stop'))
        ttk.Radiobutton(error_row, text="停止执行", variable=self._on_error_var, 
                        value='stop').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(error_row, text="继续执行下一个", variable=self._on_error_var, 
                        value='continue').pack(side=tk.LEFT, padx=5)
        
        # 执行间隔
        delay_row = ttk.Frame(option_frame)
        delay_row.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(delay_row, text="执行间隔:", width=12).pack(side=tk.LEFT)
        self._delay_var = tk.StringVar(value=str(config.get('delay_seconds', 0)))
        ttk.Entry(delay_row, textvariable=self._delay_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(delay_row, text="秒 (每个脚本执行后等待)").pack(side=tk.LEFT)
        
        # =========== 存储控件引用（用于collect_config） ===========
        self.config_widgets = {
            'on_error': ('string', self._on_error_var),
            'delay_seconds': ('int', self._delay_var)
        }
        
        return self.config_widgets
    
    def _add_chain_tool(self):
        """添加工具到任务链"""
        selected = self._tool_select_var.get()
        if not selected or selected == "(暂无可用工具)":
            return
        
        # 获取真实ID和运行模式
        tool_id = self._tool_id_map.get(selected, selected)
        tool_category = self._tool_category_map.get(selected, '')
        execution_mode = self._chain_mode_var.get()
        
        # 运行模式显示名
        mode_label = "独立" if execution_mode == "standalone" else "DCC"
        
        # 添加到列表 (display_name, tool_id, category, mode)
        self._chain_tools.append((selected, tool_id, tool_category, execution_mode))
        display_text = f"  {len(self._chain_tools)}. [{mode_label}] {selected}"
        self._chain_listbox.insert(tk.END, display_text)
        
        # 清空选择
        self._tool_select_var.set('')
    
    def _remove_chain_tool(self):
        """从任务链中删除选中的工具"""
        selection = self._chain_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        self._chain_tools.pop(idx)
        self._refresh_chain_listbox()
    
    def _move_chain_tool(self, direction: int):
        """移动选中的工具（-1=上移, 1=下移）"""
        selection = self._chain_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        new_idx = idx + direction
        
        if 0 <= new_idx < len(self._chain_tools):
            # 交换位置
            self._chain_tools[idx], self._chain_tools[new_idx] = \
                self._chain_tools[new_idx], self._chain_tools[idx]
            self._refresh_chain_listbox()
            # 保持选中状态
            self._chain_listbox.selection_set(new_idx)
    
    def _clear_chain_tools(self):
        """清空所有任务链工具"""
        self._chain_tools = []
        self._refresh_chain_listbox()
    
    def _refresh_chain_listbox(self):
        """刷新任务链列表显示"""
        self._chain_listbox.delete(0, tk.END)
        for i, item in enumerate(self._chain_tools, 1):
            # 兼容旧格式(2元组)和新格式(4元组)
            if len(item) >= 4:
                display_name, tool_id, category, mode = item
                mode_label = "独立" if mode == "standalone" else "DCC"
                display_text = f"  {i}. [{mode_label}] {display_name}"
            else:
                display_name = item[0]
                display_text = f"  {i}. {display_name}"
            self._chain_listbox.insert(tk.END, display_text)
    
    def create_custom_trigger_config(self, trigger_info, config: Dict = None) -> Dict[str, tk.Variable]:
        """创建自定义触发器配置"""
        config = config or {}
        self.clear_widgets()
        self.current_trigger_type = f"custom:{trigger_info.name}"
        
        # 检查容器是否有效
        try:
            if not self.container.winfo_exists():
                return {}
        except tk.TclError:
            return {}
        
        # 显示触发器信息
        info_frame = ttk.Frame(self.container)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        script_name = Path(trigger_info.file_path).name
        ttk.Label(info_frame, text=f"脚本: {script_name}", 
                 foreground='gray').pack(anchor=tk.W)
        
        widgets = {}
        
        # 如果没有参数，显示提示
        if not trigger_info.parameters:
            ttk.Label(self.container, text="此触发器无需配置参数").pack(anchor=tk.W, pady=10)
            return widgets
        
        # 参数配置
        ttk.Label(self.container, text="参数配置:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        params_frame = ttk.Frame(self.container)
        params_frame.pack(fill=tk.X)
        
        for param_name, param_def in trigger_info.parameters.items():
            param_widget = self._create_parameter_widget(
                params_frame, param_name, param_def, 
                config.get(param_name, param_def.get('default'))
            )
            if param_widget:
                widgets[param_name] = param_widget
        
        # 添加编辑脚本按钮
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame, 
            text="📝 编辑触发器脚本",
            command=lambda: self._open_script_file(trigger_info.file_path)
        ).pack(side=tk.LEFT)
        
        self.config_widgets.update(widgets)
        return widgets
    
    def _create_parameter_widget(self, parent, param_name: str, param_def: Dict, 
                                current_value=None) -> Optional[tuple]:
        """
        创建参数控件
        
        Returns:
            tuple: (param_type, tk.Variable) 或 None
        """
        row = ttk.Frame(parent)
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
        
        # 确定控件的值
        widget_value = current_value if current_value is not None else param_default
        
        # 根据类型创建不同的控件
        if param_type == 'bool':
            var = tk.BooleanVar(value=widget_value if isinstance(widget_value, bool) else False)
            widget = ttk.Checkbutton(row, variable=var)
            widget.pack(side=tk.LEFT)
            result = ('bool', var)
            
        elif param_type == 'int':
            var = tk.StringVar(value=str(widget_value))
            min_val = param_def.get('min', 0)
            max_val = param_def.get('max', 9999)
            widget = ttk.Spinbox(row, from_=min_val, to=max_val, textvariable=var, width=10)
            widget.pack(side=tk.LEFT)
            result = ('int', var)
            
        elif param_type == 'float':
            var = tk.StringVar(value=str(widget_value))
            widget = ttk.Entry(row, textvariable=var, width=15)
            widget.pack(side=tk.LEFT)
            result = ('float', var)
            
        elif param_type == 'choice':
            choices = param_def.get('choices', [])
            var = tk.StringVar(value=widget_value if widget_value in choices else (choices[0] if choices else ''))
            widget = ttk.Combobox(row, textvariable=var, values=choices, state='readonly', width=15)
            widget.pack(side=tk.LEFT)
            result = ('choice', var)
            
        else:  # string 或其他
            var = tk.StringVar(value=str(widget_value))
            widget = ttk.Entry(row, textvariable=var, width=25)
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            result = ('string', var)
        
        # 为控件也添加工具提示
        if tooltip_text:
            ToolTip(widget, tooltip_text)
        
        return result
    
    def _open_script_file(self, script_path: str):
        """打开脚本文件进行编辑"""
        import os
        import subprocess
        from tkinter import messagebox
        
        try:
            script_file = Path(script_path)
            
            if not script_file.exists():
                messagebox.showerror("错误", f"脚本文件不存在: {script_file}")
                return
            
            if os.name == 'nt':  # Windows
                try:
                    subprocess.run(['notepad.exe', str(script_file)], check=True)
                except Exception:
                    os.startfile(str(script_file))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['xdg-open', str(script_file)], check=True)
                
        except Exception as e:
            messagebox.showerror("错误", f"无法打开脚本文件: {e}")
    
    def collect_config(self) -> Dict[str, Any]:
        """收集当前配置的值"""
        result = {}
        
        # 收集原始控件值
        raw_config = {}
        for param_name, (param_type, variable) in self.config_widgets.items():
            try:
                if param_type == 'bool':
                    raw_config[param_name] = variable.get()
                elif param_type == 'int':
                    raw_config[param_name] = int(variable.get())
                elif param_type == 'float':
                    raw_config[param_name] = float(variable.get())
                else:  # string, choice
                    raw_config[param_name] = variable.get()
            except (ValueError, TypeError):
                # 使用默认值或空值
                if param_type == 'bool':
                    raw_config[param_name] = False
                elif param_type in ['int', 'float']:
                    raw_config[param_name] = 0
                else:
                    raw_config[param_name] = ''
        
        # 根据触发器类型转换键名
        if self.current_trigger_type == "interval":
            # 间隔触发器：interval_value 和 interval_unit
            result['interval_value'] = raw_config.get('interval_value', 30)
            result['interval_unit'] = raw_config.get('interval_unit', 'minutes')
            
        elif self.current_trigger_type == "scheduled":
            # 定时触发器：time 和 days
            hour = raw_config.get('scheduled_hour', '09')
            minute = raw_config.get('scheduled_minute', '00')
            
            # 确保格式化为字符串
            try:
                hour_str = f"{int(hour):02d}"
                minute_str = f"{int(minute):02d}"
                result['time'] = f"{hour_str}:{minute_str}"
            except (ValueError, TypeError):
                result['time'] = "09:00"
            
            # 收集选中的日期
            selected_days = []
            for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                if raw_config.get(f'day_{day}', False):
                    selected_days.append(day)
            result['days'] = selected_days
            
        elif self.current_trigger_type == "file_watch":
            # 文件监控：watch_path, pattern, recursive
            result['watch_path'] = raw_config.get('watch_path', '')
            result['pattern'] = raw_config.get('pattern', '*.*')
            result['recursive'] = raw_config.get('recursive', False)
            
        elif self.current_trigger_type == "task_chain":
            # 任务链：收集脚本列表和执行选项
            chain_tools = []
            if hasattr(self, '_chain_tools'):
                for item in self._chain_tools:
                    # 兼容旧格式(2元组)和新格式(4元组)
                    if len(item) >= 4:
                        display_name, tool_id, category, mode = item
                    else:
                        display_name, tool_id = item[0], item[1]
                        category = ''
                        mode = 'standalone'
                    
                    chain_tools.append({
                        'id': tool_id,
                        'name': display_name,
                        'category': category,
                        'mode': mode
                    })
            
            result['chain_tools'] = chain_tools
            result['on_error'] = raw_config.get('on_error', 'stop')
            result['delay_seconds'] = raw_config.get('delay_seconds', 0)
            
        else:
            # 自定义触发器或其他：直接返回原始配置
            result = raw_config
        
        return result
    
    def validate_config(self) -> tuple[bool, str]:
        """
        验证当前配置
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            config = self.collect_config()
            
            # 根据触发器类型进行特定验证
            if self.current_trigger_type == "interval":
                if 'interval_value' in config:
                    value = int(config.get('interval_value', 0))
                    if value <= 0:
                        return False, "间隔时间必须大于0"
            
            elif self.current_trigger_type == "scheduled":
                # 验证至少选择了一天
                days = config.get('days', [])
                if not days:
                    return False, "请至少选择一个执行日期"
            
            elif self.current_trigger_type == "file_watch":
                watch_path = config.get('watch_path', '').strip()
                if not watch_path:
                    return False, "请设置监控路径"
                
                # 检查路径是否存在
                if not Path(watch_path).exists():
                    return False, f"监控路径不存在: {watch_path}"
            
            elif self.current_trigger_type == "task_chain":
                # 验证至少添加了一个脚本
                chain_tools = config.get('chain_tools', [])
                if not chain_tools:
                    return False, "请至少添加一个脚本到任务链"
            
            return True, ""
            
        except Exception as e:
            return False, f"配置验证失败: {e}"