"""
美术友好的DCC插件管理器
专为美术同学设计的轻量级GUI应用程序
支持插件安装、分组管理、定时执行等功能
"""

import sys
import os
from pathlib import Path
import json
import threading
import time
from datetime import datetime
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tkinter.font as tkFont

class ArtisticPluginManager:
    """美术友好的插件管理器GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.framework_path = self._find_framework_path()
        self.plugins = []
        self.plugin_groups = {}
        self.scheduled_tasks = {}
        self.setup_ui()
        self.load_plugins()
        
    def _find_framework_path(self):
        """查找框架路径"""
        possible_paths = [
            Path.cwd(),
            Path(__file__).parent.parent,
            Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
        ]
        
        for path in possible_paths:
            if (path / "src" / "core").exists():
                return str(path)
        return str(Path.cwd())
    
    def setup_ui(self):
        """设置用户界面"""
        self.root.title("🎨 DCC插件管理器 - 美术专用版")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # 设置主题颜色
        self.setup_themes()
        
        # 创建主框架
        self.create_main_layout()
        
        # 创建菜单栏
        self.create_menu()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_themes(self):
        """设置界面主题"""
        # 定义颜色方案
        self.colors = {
            'bg_primary': '#2d2d2d',      # 主背景色
            'bg_secondary': '#3d3d3d',    # 次要背景色
            'accent': '#4a90e2',          # 强调色
            'text_primary': '#ffffff',    # 主文字色
            'text_secondary': '#cccccc',  # 次要文字色
            'success': '#7cb342',         # 成功色
            'warning': '#ffb300',         # 警告色
            'error': '#e53935'            # 错误色
        }
        
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义按钮样式
        style.configure('Accent.TButton', 
                       background=self.colors['accent'],
                       foreground='white',
                       padding=6)
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       padding=6)
    
    def create_main_layout(self):
        """创建主布局"""
        # 顶部标题栏
        self.create_header()
        
        # 主内容区域 - 使用PanedWindow
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧面板 - 插件列表和分组
        self.create_left_panel()
        
        # 中间面板 - 插件详情和参数配置
        self.create_center_panel()
        
        # 右侧面板 - 执行控制和日志
        self.create_right_panel()
    
    def create_header(self):
        """创建头部区域"""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(header_frame, 
                               text="🎨 DCC插件管理器", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 状态指示器
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(header_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 连接状态
        self.connection_status = ttk.Label(header_frame, 
                                          text="🟢 已连接框架",
                                          foreground=self.colors['success'])
        self.connection_status.pack(side=tk.RIGHT)
    
    def create_left_panel(self):
        """创建左侧面板"""
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)
        
        # 插件分组标签页
        self.group_notebook = ttk.Notebook(left_frame)
        self.group_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建默认分组
        self.create_plugin_group("所有插件")
        self.create_plugin_group("常用工具")
        self.create_plugin_group("网格处理")
        self.create_plugin_group("材质工具")
        
        # 分组管理按钮
        group_buttons = ttk.Frame(left_frame)
        group_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(group_buttons, text="➕ 添加分组", 
                  command=self.add_new_group).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(group_buttons, text="⚙️ 管理分组", 
                  command=self.manage_groups).pack(side=tk.LEFT)
    
    def create_center_panel(self):
        """创建中间面板"""
        center_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(center_frame, weight=2)
        
        # 插件详情区域
        detail_frame = ttk.LabelFrame(center_frame, text="插件详情", padding=10)
        detail_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 插件信息显示
        self.plugin_info_text = tk.Text(detail_frame, height=8, wrap=tk.WORD)
        info_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, 
                                   command=self.plugin_info_text.yview)
        self.plugin_info_text.configure(yscrollcommand=info_scroll.set)
        
        self.plugin_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 参数配置区域
        param_frame = ttk.LabelFrame(center_frame, text="参数配置", padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True)
        
        # 参数配置画布
        self.param_canvas = tk.Canvas(param_frame)
        param_scroll = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, 
                                    command=self.param_canvas.yview)
        self.param_scrollable = ttk.Frame(self.param_canvas)
        
        self.param_scrollable.bind(
            "<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
        )
        
        self.param_canvas.create_window((0, 0), window=self.param_scrollable, anchor="nw")
        self.param_canvas.configure(yscrollcommand=param_scroll.set)
        
        self.param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑鼠标滚轮事件
        self.param_canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def create_right_panel(self):
        """创建右侧面板"""
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)
        
        # 执行控制区域
        control_frame = ttk.LabelFrame(right_frame, text="执行控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 执行按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.run_button = ttk.Button(button_frame, text="▶️ 运行插件", 
                                    style='Accent.TButton',
                                    command=self.run_selected_plugin)
        self.run_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.test_button = ttk.Button(button_frame, text="🧪 测试运行", 
                                     command=self.test_plugin)
        self.test_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 定时执行区域
        schedule_frame = ttk.LabelFrame(control_frame, text="定时执行", padding=5)
        schedule_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 定时选项
        schedule_options = ttk.Frame(schedule_frame)
        schedule_options.pack(fill=tk.X)
        
        ttk.Label(schedule_options, text="执行时间:").pack(side=tk.LEFT)
        self.schedule_var = tk.StringVar(value="不设置")
        schedule_combo = ttk.Combobox(schedule_options, textvariable=self.schedule_var,
                                     values=["不设置", "每天", "每周", "每月", "自定义"])
        schedule_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(schedule_options, text="⏱️ 设置定时", 
                  command=self.setup_schedule).pack(side=tk.RIGHT)
        
        # 日志区域
        log_frame = ttk.LabelFrame(right_frame, text="执行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志控制按钮
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_buttons, text="清空日志", 
                  command=self.clear_logs).pack(side=tk.LEFT)
        ttk.Button(log_buttons, text="保存日志", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(log_buttons, text="导出报告", 
                  command=self.export_report).pack(side=tk.RIGHT)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新插件列表", command=self.refresh_plugins)
        file_menu.add_command(label="导入插件配置", command=self.import_config)
        file_menu.add_command(label="导出插件配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="插件市场", command=self.open_plugin_market)
        tools_menu.add_command(label="依赖管理", command=self.open_dependency_manager)
        tools_menu.add_command(label="脚本管理", command=self.open_script_manager)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="界面主题", command=self.change_theme)
        settings_menu.add_command(label="默认参数", command=self.set_default_params)
        settings_menu.add_command(label="定时任务", command=self.manage_scheduled_tasks)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_plugin_group(self, group_name):
        """创建插件分组标签页"""
        frame = ttk.Frame(self.group_notebook)
        self.group_notebook.add(frame, text=group_name)
        
        # 创建树形视图
        columns = ('name', 'version', 'status')
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=12)
        
        # 设置列
        tree.heading('#0', text='插件名称')
        tree.heading('name', text='名称')
        tree.heading('version', text='版本')
        tree.heading('status', text='状态')
        
        tree.column('#0', width=150)
        tree.column('name', width=100)
        tree.column('version', width=60)
        tree.column('status', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        tree.bind('<<TreeviewSelect>>', self.on_plugin_select)
        tree.bind('<Double-1>', self.on_plugin_double_click)
        
        # 保存引用
        self.plugin_groups[group_name] = tree
    
    def load_plugins(self):
        """加载插件列表"""
        try:
            # 扫描插件目录
            plugins_dir = Path(self.framework_path) / "src" / "plugins"
            
            for plugin_type in ['dcc', 'ue']:
                type_dir = plugins_dir / plugin_type
                if not type_dir.exists():
                    continue
                    
                for software_dir in type_dir.iterdir():
                    if not software_dir.is_dir():
                        continue
                        
                    for plugin_dir in software_dir.iterdir():
                        if not plugin_dir.is_dir():
                            continue
                            
                        self.load_plugin_info(plugin_type, software_dir.name, plugin_dir)
            
            # 更新UI
            self.populate_plugin_trees()
            self.log_message("✓ 插件列表加载完成")
            
        except Exception as e:
            self.log_message(f"✗ 加载插件失败: {e}")
    
    def load_plugin_info(self, plugin_type, software, plugin_dir):
        """加载单个插件信息"""
        try:
            config_file = plugin_dir / "config.json"
            if not config_file.exists():
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            plugin_info = {
                'id': f"{plugin_type}_{software}_{config['plugin']['name']}",
                'name': config['plugin']['name'],
                'version': config['plugin']['version'],
                'type': plugin_type,
                'software': software,
                'description': config['plugin'].get('description', ''),
                'author': config['plugin'].get('author', ''),
                'path': str(plugin_dir),
                'parameters': config.get('parameters', {}),
                'capabilities': config.get('capabilities', []),
                'status': '未安装' if plugin_type == 'dcc' else '就绪'
            }
            
            self.plugins.append(plugin_info)
            
        except Exception as e:
            self.log_message(f"加载插件信息失败 {plugin_dir}: {e}")
    
    def populate_plugin_trees(self):
        """填充插件树形视图"""
        # 清空现有项目
        for tree in self.plugin_groups.values():
            for item in tree.get_children():
                tree.delete(item)
        
        # 按分组添加插件
        for plugin in self.plugins:
            # 添加到"所有插件"分组
            all_tree = self.plugin_groups["所有插件"]
            status_color = 'green' if plugin['status'] == '就绪' else 'red'
            all_tree.insert('', 'end', 
                          iid=plugin['id'],
                          text=plugin['name'],
                          values=(plugin['name'], plugin['version'], plugin['status']),
                          tags=(status_color,))
            
            # 根据类型添加到对应分组
            if '网格' in plugin['name'] or 'mesh' in plugin['name'].lower():
                if "网格处理" in self.plugin_groups:
                    tree = self.plugin_groups["网格处理"]
                    tree.insert('', 'end', iid=plugin['id'], text=plugin['name'],
                              values=(plugin['name'], plugin['version'], plugin['status']))
            
            if '材质' in plugin['name'] or 'material' in plugin['name'].lower():
                if "材质工具" in self.plugin_groups:
                    tree = self.plugin_groups["材质工具"]
                    tree.insert('', 'end', iid=plugin['id'], text=plugin['name'],
                              values=(plugin['name'], plugin['version'], plugin['status']))
    
    def on_plugin_select(self, event):
        """插件选择事件"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        plugin = self.find_plugin_by_id(item_id)
        if plugin:
            self.display_plugin_info(plugin)
            self.create_parameter_widgets(plugin)
    
    def find_plugin_by_id(self, plugin_id):
        """根据ID查找插件"""
        for plugin in self.plugins:
            if plugin['id'] == plugin_id:
                return plugin
        return None
    
    def display_plugin_info(self, plugin):
        """显示插件详细信息"""
        info_text = f"""插件名称: {plugin['name']}
版本: {plugin['version']}
类型: {plugin['type'].upper()}
目标软件: {plugin['software']}
作者: {plugin['author']}
状态: {plugin['status']}

描述:
{plugin['description']}

功能特性:
{chr(10).join(['• ' + cap for cap in plugin['capabilities'][:5]])}
{'' if len(plugin['capabilities']) <= 5 else '...及其他功能'}
"""
        self.plugin_info_text.delete(1.0, tk.END)
        self.plugin_info_text.insert(1.0, info_text)
    
    def create_parameter_widgets(self, plugin):
        """创建参数配置控件"""
        # 清除现有控件
        for widget in self.param_scrollable.winfo_children():
            widget.destroy()
        
        self.param_vars = {}
        
        if not plugin['parameters']:
            ttk.Label(self.param_scrollable, 
                     text="该插件无需配置参数").pack(pady=20)
            return
        
        # 创建参数控件
        row = 0
        for param_name, param_info in plugin['parameters'].items():
            # 参数标签
            ttk.Label(self.param_scrollable, 
                     text=f"{param_name}:", 
                     font=('Arial', 9, 'bold')).grid(row=row, column=0, 
                                                    sticky=tk.W, pady=5, padx=(0, 10))
            
            # 参数控件
            param_type = param_info.get('type', 'string')
            default_value = param_info.get('default', '')
            
            if param_type == 'boolean':
                var = tk.BooleanVar(value=default_value)
                widget = ttk.Checkbutton(self.param_scrollable, variable=var)
            elif param_type == 'integer':
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Spinbox(self.param_scrollable, from_=param_info.get('min', 0),
                                   to=param_info.get('max', 1000), textvariable=var, width=15)
            elif param_type == 'float':
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_scrollable, textvariable=var, width=20)
            else:
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_scrollable, textvariable=var, width=30)
            
            widget.grid(row=row, column=1, sticky=tk.W, pady=5)
            
            # 参数说明
            desc = param_info.get('description', '')
            if desc:
                ttk.Label(self.param_scrollable, 
                         text=f"({desc})", 
                         foreground='gray',
                         font=('Arial', 8)).grid(row=row, column=2, sticky=tk.W, padx=(10, 0))
            
            self.param_vars[param_name] = var
            row += 1
        
        # 添加说明
        ttk.Label(self.param_scrollable, 
                 text="💡 修改参数后点击'运行插件'生效",
                 foreground=self.colors['warning']).grid(row=row, column=0, 
                                                       columnspan=3, pady=(15, 0))
    
    def run_selected_plugin(self):
        """运行选中的插件"""
        # 获取当前选中的插件
        current_tab = self.group_notebook.index(self.group_notebook.select())
        current_group = self.group_notebook.tab(current_tab, "text")
        tree = self.plugin_groups[current_group]
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个插件")
            return
        
        item_id = selection[0]
        plugin = self.find_plugin_by_id(item_id)
        if not plugin:
            messagebox.showerror("错误", "未找到选中的插件")
            return
        
        # 收集参数
        params = self.collect_parameters()
        
        # 在后台线程中执行
        def execute_plugin():
            try:
                self.status_var.set("插件运行中...")
                self.run_button.configure(state='disabled')
                
                # 执行插件逻辑
                result = self.execute_plugin_logic(plugin, params)
                
                # 更新UI
                self.root.after(0, lambda: self.on_execution_complete(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_execution_error(str(e)))
            finally:
                self.root.after(0, lambda: self.run_button.configure(state='normal'))
        
        # 启动执行线程
        thread = threading.Thread(target=execute_plugin, daemon=True)
        thread.start()
    
    def collect_parameters(self):
        """收集配置的参数"""
        params = {}
        for param_name, var in self.param_vars.items():
            try:
                # 根据变量类型获取值
                if isinstance(var, tk.BooleanVar):
                    params[param_name] = var.get()
                elif isinstance(var, tk.StringVar):
                    params[param_name] = var.get()
                else:
                    params[param_name] = var.get()
            except:
                params[param_name] = None
        return params
    
    def execute_plugin_logic(self, plugin, params):
        """执行插件核心逻辑"""
        self.log_message(f"开始执行插件: {plugin['name']}")
        self.log_message(f"参数设置: {params}")
        
        try:
            # 这里是插件执行的核心逻辑
            # 实际实现时会调用具体的插件代码
            
            # 模拟执行过程
            time.sleep(2)  # 模拟处理时间
            
            # 模拟执行结果
            result = {
                "status": "success",
                "message": f"插件 {plugin['name']} 执行完成",
                "processed_items": 3,
                "execution_time": "2.1秒"
            }
            
            self.log_message(f"执行结果: {result['message']}")
            return result
            
        except Exception as e:
            self.log_message(f"执行失败: {str(e)}")
            raise
    
    def on_execution_complete(self, result):
        """执行完成回调"""
        self.status_var.set("执行完成")
        messagebox.showinfo("执行完成", result['message'])
    
    def on_execution_error(self, error):
        """执行错误回调"""
        self.status_var.set("执行失败")
        messagebox.showerror("执行错误", f"插件执行失败:\n{error}")
        self.log_message(f"✗ 执行错误: {error}")
    
    def test_plugin(self):
        """测试插件运行"""
        messagebox.showinfo("测试", "这是测试运行功能\n实际使用时请使用'运行插件'按钮")
    
    def add_new_group(self):
        """添加新分组"""
        group_name = tk.simpledialog.askstring("添加分组", "请输入分组名称:")
        if group_name and group_name not in self.plugin_groups:
            self.create_plugin_group(group_name)
            self.log_message(f"✓ 已添加新分组: {group_name}")
    
    def manage_groups(self):
        """管理分组"""
        # 这里可以实现分组管理对话框
        groups = list(self.plugin_groups.keys())
        group_list = "\n".join([f"• {group}" for group in groups])
        messagebox.showinfo("分组管理", f"当前分组:\n{group_list}")
    
    def setup_schedule(self):
        """设置定时执行"""
        schedule_type = self.schedule_var.get()
        if schedule_type == "不设置":
            messagebox.showinfo("提示", "请选择定时执行类型")
            return
        
        messagebox.showinfo("定时设置", f"已设置{schedule_type}执行\n具体时间设置功能待完善")
        self.log_message(f"已设置定时执行: {schedule_type}")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 限制日志长度
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 500:  # 保留最多500行
            self.log_text.delete(1.0, f"{len(lines)-499}.0")
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def save_logs(self):
        """保存日志到文件"""
        log_content = self.log_text.get(1.0, tk.END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("成功", f"日志已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{e}")
    
    def export_report(self):
        """导出执行报告"""
        report = {
            "export_time": datetime.now().isoformat(),
            "plugins_count": len(self.plugins),
            "groups_count": len(self.plugin_groups),
            "log_content": self.log_text.get(1.0, tk.END)
        }
        
        messagebox.showinfo("导出报告", f"报告已生成\n插件数量: {report['plugins_count']}\n分组数量: {report['groups_count']}")
    
    def refresh_plugins(self):
        """刷新插件列表"""
        self.plugins.clear()
        self.load_plugins()
        self.log_message("✓ 插件列表已刷新")
    
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.param_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出插件管理器吗？"):
            self.root.destroy()

def main():
    """主函数"""
    try:
        app = ArtisticPluginManager()
        app.root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("启动错误", f"程序启动失败:\n{e}")

if __name__ == "__main__":
    main()