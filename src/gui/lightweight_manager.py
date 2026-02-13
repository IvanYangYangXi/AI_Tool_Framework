"""
轻量级DCC工具管理器前端
专为美术人员设计的GUI界面，通过Git管理后端脚本
"""

import sys
import os
from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import threading
from datetime import datetime
import tempfile

class LightweightDCCManager:
    """轻量级DCC工具管理器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.git_repo_path = self._get_git_repo_path()
        self.connected_dcc = None
        self.setup_ui()
        self.check_git_status()
        
    def _get_git_repo_path(self):
        """获取Git仓库路径"""
        # 使用当前工作区路径
        return Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
    
    def setup_ui(self):
        """设置轻量级用户界面"""
        self.root.title("🎨 DCC工具管理器 - 轻量版")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部状态栏
        self.create_status_bar(main_frame)
        
        # 主要功能区域
        self.create_main_panels(main_frame)
        
        # 底部控制区域
        self.create_control_panel(main_frame)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Git状态
        self.git_status_var = tk.StringVar(value="Git状态: 检查中...")
        git_label = ttk.Label(status_frame, textvariable=self.git_status_var)
        git_label.pack(side=tk.LEFT)
        
        # DCC连接状态
        self.dcc_status_var = tk.StringVar(value="DCC连接: 未连接")
        dcc_label = ttk.Label(status_frame, textvariable=self.dcc_status_var)
        dcc_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 版本信息
        version_label = ttk.Label(status_frame, text="v1.0.0", foreground="gray")
        version_label.pack(side=tk.RIGHT)
    
    def create_main_panels(self, parent):
        """创建主要面板"""
        # 使用PanedWindow分割界面
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 工具列表
        self.create_tools_panel(paned_window)
        
        # 右侧面板 - 参数配置和执行
        self.create_execution_panel(paned_window)
    
    def create_tools_panel(self, parent):
        """创建工具列表面板"""
        tools_frame = ttk.LabelFrame(parent, text="可用工具", padding="10")
        parent.add(tools_frame, weight=1)
        
        # 工具分类标签页
        self.tools_notebook = ttk.Notebook(tools_frame)
        self.tools_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建工具分类
        self.create_tool_category("Maya工具", "maya")
        self.create_tool_category("3ds Max工具", "max")
        self.create_tool_category("Blender工具", "blender")
        self.create_tool_category("UE工具", "ue")
        
        # 刷新按钮
        refresh_btn = ttk.Button(tools_frame, text="🔄 刷新工具列表", 
                                command=self.refresh_tools_list)
        refresh_btn.pack(fill=tk.X, pady=(10, 0))
    
    def create_tool_category(self, category_name, category_key):
        """创建工具分类标签页"""
        frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(frame, text=category_name)
        
        # 工具列表
        columns = ('name', 'version', 'status')
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=12)
        
        tree.heading('#0', text='工具名称')
        tree.heading('name', text='名称')
        tree.heading('version', text='版本')
        tree.heading('status', text='状态')
        
        tree.column('#0', width=180)
        tree.column('name', width=120)
        tree.column('version', width=80)
        tree.column('status', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        tree.bind('<<TreeviewSelect>>', self.on_tool_select)
        tree.bind('<Double-1>', self.on_tool_double_click)
        
        # 保存引用
        setattr(self, f"{category_key}_tree", tree)
    
    def create_execution_panel(self, parent):
        """创建执行面板"""
        exec_frame = ttk.Frame(parent)
        parent.add(exec_frame, weight=2)
        
        # 工具详情区域
        detail_frame = ttk.LabelFrame(exec_frame, text="工具详情", padding="10")
        detail_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.detail_text = tk.Text(detail_frame, height=6, wrap=tk.WORD)
        detail_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, 
                                     command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 参数配置区域
        param_frame = ttk.LabelFrame(exec_frame, text="参数配置", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 参数配置画布
        self.param_canvas = tk.Canvas(param_frame)
        param_scroll = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, 
                                    command=self.param_canvas.yview)
        self.param_frame_inner = ttk.Frame(self.param_canvas)
        
        self.param_frame_inner.bind(
            "<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
        )
        
        self.param_canvas.create_window((0, 0), window=self.param_frame_inner, anchor="nw")
        self.param_canvas.configure(yscrollcommand=param_scroll.set)
        
        self.param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 执行控制区域
        control_frame = ttk.LabelFrame(exec_frame, text="执行控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 执行按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.run_in_dcc_btn = ttk.Button(button_frame, text="▶️ 在DCC中执行", 
                                        command=self.run_in_dcc)
        self.run_in_dcc_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.generate_script_btn = ttk.Button(button_frame, text="📝 生成脚本文件", 
                                             command=self.generate_script)
        self.generate_script_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.test_btn = ttk.Button(button_frame, text="🧪 测试参数", 
                                  command=self.test_parameters)
        self.test_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # DCC连接控制
        dcc_frame = ttk.Frame(control_frame)
        dcc_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(dcc_frame, text="DCC连接:").pack(side=tk.LEFT)
        self.dcc_combo = ttk.Combobox(dcc_frame, 
                                     values=["Maya", "3ds Max", "Blender", "Unreal Engine"],
                                     state="readonly")
        self.dcc_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.dcc_combo.set("选择DCC软件")
        
        ttk.Button(dcc_frame, text="🔗 连接", 
                  command=self.connect_dcc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(dcc_frame, text="끊 断开", 
                  command=self.disconnect_dcc).pack(side=tk.LEFT)
    
    def create_control_panel(self, parent):
        """创建底部控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Git控制
        git_frame = ttk.LabelFrame(control_frame, text="Git管理", padding="5")
        git_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(git_frame, text="⬇️ 更新到最新版本", 
                  command=self.update_git_repo).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(git_frame, text="🔍 检查更新", 
                  command=self.check_git_updates).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(git_frame, text="📋 查看变更日志", 
                  command=self.show_changelog).pack(side=tk.LEFT)
        
        # 日志区域
        log_frame = ttk.LabelFrame(control_frame, text="操作日志", padding="5")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def check_git_status(self):
        """检查Git仓库状态"""
        def check_status():
            try:
                # 检查是否有未提交的更改
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.git_repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    if result.stdout.strip():
                        self.git_status_var.set("Git状态: 有未提交更改")
                    else:
                        self.git_status_var.set("Git状态: 代码已同步")
                else:
                    self.git_status_var.set("Git状态: 无法连接仓库")
                    
            except Exception as e:
                self.git_status_var.set(f"Git状态: 错误 - {str(e)}")
        
        # 在后台线程中检查
        threading.Thread(target=check_status, daemon=True).start()
    
    def refresh_tools_list(self):
        """刷新工具列表"""
        self.log_message("正在刷新工具列表...")
        
        # 清空现有列表
        for category in ['maya', 'max', 'blender', 'ue']:
            tree = getattr(self, f"{category}_tree")
            for item in tree.get_children():
                tree.delete(item)
        
        # 从Git仓库扫描工具
        self.scan_tools_from_git()
        
        self.log_message("✓ 工具列表刷新完成")
    
    def scan_tools_from_git(self):
        """从Git仓库扫描工具"""
        try:
            plugins_dir = self.git_repo_path / "src" / "plugins"
            
            # 扫描各个类型的工具
            tool_categories = {
                'maya': plugins_dir / 'dcc' / 'maya',
                'max': plugins_dir / 'dcc' / 'max', 
                'blender': plugins_dir / 'dcc' / 'blender',
                'ue': plugins_dir / 'ue'
            }
            
            for category, category_path in tool_categories.items():
                if category_path.exists():
                    tree = getattr(self, f"{category}_tree")
                    self.load_tools_from_directory(category_path, tree, category)
                    
        except Exception as e:
            self.log_message(f"✗ 扫描工具失败: {e}")
    
    def load_tools_from_directory(self, directory, tree, category):
        """从目录加载工具"""
        for tool_dir in directory.iterdir():
            if tool_dir.is_dir():
                config_file = tool_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        tool_info = {
                            'id': f"{category}_{tool_dir.name}",
                            'name': config['plugin']['name'],
                            'version': config['plugin']['version'],
                            'description': config['plugin'].get('description', ''),
                            'path': str(tool_dir.relative_to(self.git_repo_path)),
                            'parameters': config.get('parameters', {}),
                            'status': '可用'
                        }
                        
                        # 添加到树形视图
                        tree.insert('', 'end',
                                  iid=tool_info['id'],
                                  text=tool_info['name'],
                                  values=(tool_info['name'], tool_info['version'], tool_info['status']))
                        
                        # 保存工具信息
                        if not hasattr(self, 'tools_cache'):
                            self.tools_cache = {}
                        self.tools_cache[tool_info['id']] = tool_info
                        
                    except Exception as e:
                        self.log_message(f"加载工具失败 {tool_dir}: {e}")
    
    def on_tool_select(self, event):
        """工具选择事件"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        
        tool_id = selection[0]
        if hasattr(self, 'tools_cache') and tool_id in self.tools_cache:
            tool_info = self.tools_cache[tool_id]
            self.display_tool_info(tool_info)
            self.create_parameter_widgets(tool_info)
    
    def on_tool_double_click(self, event):
        """工具双击事件"""
        # 双击时自动连接到对应的DCC软件
        tree = event.widget
        selection = tree.selection()
        if selection:
            tool_id = selection[0]
            if 'maya' in tool_id.lower():
                self.dcc_combo.set("Maya")
            elif 'max' in tool_id.lower():
                self.dcc_combo.set("3ds Max")
            elif 'blender' in tool_id.lower():
                self.dcc_combo.set("Blender")
            elif 'ue' in tool_id.lower():
                self.dcc_combo.set("Unreal Engine")
            
            self.connect_dcc()
    
    def display_tool_info(self, tool_info):
        """显示工具详细信息"""
        info_text = f"""工具名称: {tool_info['name']}
版本: {tool_info['version']}
路径: {tool_info['path']}

描述:
{tool_info['description']}

参数说明:
"""
        for param_name, param_info in tool_info['parameters'].items():
            info_text += f"• {param_name}: {param_info.get('description', '')}\n"
        
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, info_text)
    
    def create_parameter_widgets(self, tool_info):
        """创建参数配置控件"""
        # 清除现有控件
        for widget in self.param_frame_inner.winfo_children():
            widget.destroy()
        
        self.param_vars = {}
        
        if not tool_info['parameters']:
            ttk.Label(self.param_frame_inner, 
                     text="该工具无需配置参数").pack(pady=20)
            return
        
        # 创建参数控件
        row = 0
        for param_name, param_info in tool_info['parameters'].items():
            # 参数标签
            ttk.Label(self.param_frame_inner, 
                     text=f"{param_name}:", 
                     font=('Arial', 9, 'bold')).grid(row=row, column=0, 
                                                    sticky=tk.W, pady=5, padx=(0, 10))
            
            # 参数控件
            param_type = param_info.get('type', 'string')
            default_value = param_info.get('default', '')
            
            if param_type == 'boolean':
                var = tk.BooleanVar(value=default_value)
                widget = ttk.Checkbutton(self.param_frame_inner, variable=var)
            elif param_type == 'integer':
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Spinbox(self.param_frame_inner, from_=param_info.get('min', 0),
                                   to=param_info.get('max', 1000), textvariable=var, width=15)
            elif param_type == 'float':
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_frame_inner, textvariable=var, width=20)
            else:
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_frame_inner, textvariable=var, width=30)
            
            widget.grid(row=row, column=1, sticky=tk.W, pady=5)
            
            # 参数说明
            desc = param_info.get('description', '')
            if desc:
                ttk.Label(self.param_frame_inner, 
                         text=f"({desc})", 
                         foreground='gray',
                         font=('Arial', 8)).grid(row=row, column=2, sticky=tk.W, padx=(10, 0))
            
            self.param_vars[param_name] = var
            row += 1
    
    def connect_dcc(self):
        """连接到DCC软件"""
        selected_dcc = self.dcc_combo.get()
        if selected_dcc == "选择DCC软件":
            messagebox.showwarning("警告", "请先选择要连接的DCC软件")
            return
        
        self.log_message(f"正在连接到 {selected_dcc}...")
        
        # 这里实现具体的DCC连接逻辑
        # 实际实现时需要根据不同软件使用相应的API
        
        def connect_process():
            try:
                # 模拟连接过程
                import time
                time.sleep(2)
                
                # 更新UI
                self.root.after(0, lambda: self.on_dcc_connected(selected_dcc))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_dcc_connection_failed(str(e)))
        
        threading.Thread(target=connect_process, daemon=True).start()
    
    def on_dcc_connected(self, dcc_name):
        """DCC连接成功回调"""
        self.connected_dcc = dcc_name
        self.dcc_status_var.set(f"DCC连接: 已连接到 {dcc_name}")
        self.run_in_dcc_btn.configure(state='normal')
        self.log_message(f"✓ 成功连接到 {dcc_name}")
    
    def on_dcc_connection_failed(self, error):
        """DCC连接失败回调"""
        self.dcc_status_var.set("DCC连接: 连接失败")
        messagebox.showerror("连接失败", f"无法连接到DCC软件:\n{error}")
        self.log_message(f"✗ DCC连接失败: {error}")
    
    def disconnect_dcc(self):
        """断开DCC连接"""
        if self.connected_dcc:
            self.connected_dcc = None
            self.dcc_status_var.set("DCC连接: 未连接")
            self.run_in_dcc_btn.configure(state='disabled')
            self.log_message("✓ DCC连接已断开")
    
    def run_in_dcc(self):
        """在DCC中执行工具"""
        if not self.connected_dcc:
            messagebox.showwarning("警告", "请先连接到DCC软件")
            return
        
        # 获取当前选中的工具和参数
        # 实际实现时需要生成相应的执行代码并发送到DCC
        
        self.log_message(f"正在{self.connected_dcc}中执行工具...")
        messagebox.showinfo("执行", f"工具已发送到{self.connected_dcc}执行")
    
    def generate_script(self):
        """生成可在DCC中运行的脚本文件"""
        # 获取参数并生成脚本
        params = self.collect_parameters()
        
        # 生成临时脚本文件
        script_content = self.generate_dcc_script(params)
        
        # 保存脚本文件
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python脚本", "*.py"), ("所有文件", "*.*")],
            title="保存脚本文件"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                self.log_message(f"✓ 脚本已保存到: {file_path}")
                messagebox.showinfo("成功", f"脚本文件已生成:\n{file_path}")
            except Exception as e:
                self.log_message(f"✗ 保存脚本失败: {e}")
                messagebox.showerror("错误", f"保存脚本失败:\n{e}")
    
    def generate_dcc_script(self, params):
        """生成DCC脚本内容"""
        # 这里根据不同的DCC软件生成相应的脚本
        script_template = f'''# 自动生成的DCC工具脚本
# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 参数设置: {json.dumps(params, indent=2, ensure_ascii=False)}

import sys
import os

# 添加工具路径
tool_path = r"{self.git_repo_path}"
if tool_path not in sys.path:
    sys.path.append(tool_path)

# 在此处添加具体的工具执行代码
print("工具执行参数:")
for key, value in {params}.items():
    print(f"{{key}}: {{value}}")

# TODO: 添加实际的工具执行逻辑
'''
        return script_template
    
    def test_parameters(self):
        """测试参数配置"""
        params = self.collect_parameters()
        self.log_message(f"测试参数配置: {params}")
        messagebox.showinfo("参数测试", f"当前参数设置:\n{json.dumps(params, indent=2, ensure_ascii=False)}")
    
    def collect_parameters(self):
        """收集配置的参数"""
        params = {}
        if hasattr(self, 'param_vars'):
            for param_name, var in self.param_vars.items():
                try:
                    if isinstance(var, tk.BooleanVar):
                        params[param_name] = var.get()
                    else:
                        params[param_name] = var.get()
                except:
                    params[param_name] = None
        return params
    
    def update_git_repo(self):
        """更新Git仓库到最新版本"""
        self.log_message("正在更新Git仓库...")
        
        def update_process():
            try:
                # 执行git pull
                result = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=self.git_repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.root.after(0, lambda: self.on_git_update_success(result.stdout))
                else:
                    self.root.after(0, lambda: self.on_git_update_failed(result.stderr))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_git_update_failed(str(e)))
        
        threading.Thread(target=update_process, daemon=True).start()
    
    def on_git_update_success(self, output):
        """Git更新成功回调"""
        self.log_message("✓ Git仓库更新成功")
        self.log_message(f"更新输出: {output}")
        messagebox.showinfo("更新完成", "Git仓库已更新到最新版本")
        self.refresh_tools_list()  # 刷新工具列表
    
    def on_git_update_failed(self, error):
        """Git更新失败回调"""
        self.log_message(f"✗ Git更新失败: {error}")
        messagebox.showerror("更新失败", f"Git更新失败:\n{error}")
    
    def check_git_updates(self):
        """检查Git更新"""
        self.log_message("正在检查Git更新...")
        
        try:
            # 检查远程更新
            result = subprocess.run(
                ["git", "fetch"],
                cwd=self.git_repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # 检查是否有更新
                status_result = subprocess.run(
                    ["git", "status", "-uno"],
                    cwd=self.git_repo_path,
                    capture_output=True,
                    text=True
                )
                
                if "Your branch is behind" in status_result.stdout:
                    if messagebox.askyesno("发现更新", "检测到有新版本可用，是否立即更新？"):
                        self.update_git_repo()
                else:
                    messagebox.showinfo("检查结果", "当前已是最新版本")
            else:
                messagebox.showerror("检查失败", "无法检查更新")
                
        except Exception as e:
            self.log_message(f"✗ 检查更新失败: {e}")
    
    def show_changelog(self):
        """显示变更日志"""
        try:
            # 获取Git提交历史
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=self.git_repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                changelog_window = tk.Toplevel(self.root)
                changelog_window.title("变更日志")
                changelog_window.geometry("600x400")
                
                text_widget = tk.Text(changelog_window, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(changelog_window, orient=tk.VERTICAL, 
                                         command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.insert(1.0, result.stdout)
                text_widget.configure(state='disabled')
                
                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                messagebox.showerror("错误", "无法获取变更日志")
                
        except Exception as e:
            self.log_message(f"✗ 显示变更日志失败: {e}")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 限制日志长度
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 200:  # 保留最多200行
            self.log_text.delete(1.0, f"{len(lines)-199}.0")

def main():
    """主函数"""
    try:
        app = LightweightDCCManager()
        app.root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("启动错误", f"程序启动失败:\n{e}")

if __name__ == "__main__":
    main()