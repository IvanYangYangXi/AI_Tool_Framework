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
import io

class LightweightDCCManager:
    """
    轻量级DCC工具管理器
    
    主要功能：
    - 提供UI界面管理脚本工具
    - 通过Git更新/管理后端脚本
    - 连接DCC软件执行脚本
    """
    
    # 本地配置文件名
    LOCAL_SETTINGS_FILE = "local_settings.json"
    
    def __init__(self):
        self.root = tk.Tk()
        self.git_repo_path = self._get_git_repo_path()
        self.connected_dcc = None
        self.is_git_up_to_date = False
        
        # 确保本地目录结构存在
        self._ensure_local_directories()
        
        # 加载本地配置
        self.local_settings = self._load_local_settings()
        
        # 加载工具分组配置
        self.tool_groups = self._load_tool_groups()
        
        # 搜索防抖变量
        self._search_after_ids = {}
        
        # 分组下拉框引用
        self.group_combos = {}
        self.search_vars = {}
        
        self.setup_ui()
        # 启动时自动检查Git更新
        self._startup_git_check()
    
    def _get_documents_base_dir(self) -> Path:
        """获取我的文档下的DCC Tool Manager目录"""
        import os
        return Path(os.path.expanduser("~")) / "Documents" / "DCC_Tool_Manager"
    
    def _ensure_local_directories(self):
        """确保本地目录结构存在"""
        base_dir = self._get_documents_base_dir()
        
        # 创建配置目录
        (base_dir / "config").mkdir(parents=True, exist_ok=True)
        
        # 创建本地脚本目录结构
        for category in ['maya', 'max', 'blender', 'ue', 'other']:
            (base_dir / "local_scripts" / category).mkdir(parents=True, exist_ok=True)
    
    def _get_local_settings_path(self) -> Path:
        """获取本地配置文件路径（我的文档/DCC_Tool_Manager/config/）"""
        return self._get_documents_base_dir() / "config" / self.LOCAL_SETTINGS_FILE
    
    def _load_local_settings(self) -> dict:
        """
        加载本地配置
        配置文件存储在 我的文档/DCC_Tool_Manager/config/local_settings.json
        """
        settings_path = self._get_local_settings_path()
        
        default_settings = {
            "ue_project_paths": [],  # 用户配置过的UE项目路径列表
            "last_ue_project": "",   # 最后使用的UE项目路径
            "maya_port": 7001,
            "max_port": 9001,
            "blender_port": 8001,
            "window_geometry": "",   # 窗口位置和大小
        }
        
        try:
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认值和已保存的值
                    default_settings.update(loaded)
        except Exception as e:
            print(f"加载本地配置失败: {e}")
        
        return default_settings
    
    def _save_local_settings(self):
        """保存本地配置"""
        settings_path = self._get_local_settings_path()
        
        try:
            # 确保目录存在
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.local_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存本地配置失败: {e}")
    
    def _add_ue_project_path(self, path: str):
        """添加UE项目路径到配置"""
        if path and path not in self.local_settings.get("ue_project_paths", []):
            if "ue_project_paths" not in self.local_settings:
                self.local_settings["ue_project_paths"] = []
            self.local_settings["ue_project_paths"].append(path)
        
        self.local_settings["last_ue_project"] = path
        self._save_local_settings()
    
    def _load_tool_groups(self) -> dict:
        """
        加载工具分组配置
        优先级：本地配置 > 默认配置
        """
        default_groups = {
            "groups": [
                {"id": "all", "name": "全部", "icon": "📋"},
                {"id": "modeling", "name": "建模", "icon": "🎨"},
                {"id": "animation", "name": "动画", "icon": "🎬"},
                {"id": "rigging", "name": "绑定", "icon": "🦴"},
                {"id": "io", "name": "导入导出", "icon": "📦"},
                {"id": "utility", "name": "通用", "icon": "🔧"},
                {"id": "custom", "name": "自定义", "icon": "⭐"},
            ],
            "tool_assignments": {}
        }
        
        # 尝试加载默认配置
        default_config_path = self.git_repo_path / "configs" / "tool_groups.json"
        if default_config_path.exists():
            try:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_groups.update(loaded)
            except Exception as e:
                print(f"加载默认分组配置失败: {e}")
        
        # 尝试加载本地配置
        local_config_path = self._get_documents_base_dir() / "config" / "tool_groups_local.json"
        if local_config_path.exists():
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_groups = json.load(f)
                    # 合并本地自定义分组
                    if "custom_groups" in local_groups:
                        for custom in local_groups["custom_groups"]:
                            if custom not in default_groups["groups"]:
                                default_groups["groups"].append(custom)
                    # 合并本地工具分配
                    if "tool_assignments" in local_groups:
                        default_groups["tool_assignments"].update(local_groups["tool_assignments"])
            except Exception as e:
                print(f"加载本地分组配置失败: {e}")
        
        return default_groups
    
    def _save_tool_groups_local(self):
        """保存本地分组配置"""
        local_config_path = self._get_documents_base_dir() / "config" / "tool_groups_local.json"
        
        # 只保存本地自定义的内容
        local_data = {
            "custom_groups": [g for g in self.tool_groups.get("groups", []) 
                             if g.get("is_custom", False)],
            "tool_assignments": self.tool_groups.get("tool_assignments", {})
        }
        
        try:
            local_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_config_path, 'w', encoding='utf-8') as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存本地分组配置失败: {e}")
    
    def get_tool_groups(self, tool_id: str) -> list:
        """获取工具的分组列表"""
        # 先检查本地分配
        if tool_id in self.tool_groups.get("tool_assignments", {}):
            return self.tool_groups["tool_assignments"][tool_id]
        
        # 从工具的config.json中获取tags
        if hasattr(self, 'tools_cache') and tool_id in self.tools_cache:
            tool_info = self.tools_cache[tool_id]
            return tool_info.get('tags', [])
        
        return []
        
    def _get_git_repo_path(self):
        """
        获取Git仓库路径
        
        优先级：
        1. 环境变量 AI_TOOL_REPO_PATH
        2. 当前脚本所在目录的上级目录
        3. 默认路径
        """
        # 尝试从环境变量获取
        env_path = os.environ.get("AI_TOOL_REPO_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # 尝试使用脚本所在目录的上级（项目根目录）
        script_dir = Path(__file__).resolve().parent.parent.parent
        if (script_dir / ".git").exists():
            return script_dir
        
        # 默认路径
        return Path.cwd()
    
    def _startup_git_check(self):
        """
        启动时自动检查Git更新
        
        如果发现本地版本落后于远程，弹窗提示用户更新
        """
        def check_and_notify():
            try:
                self.log_message("启动检查: 正在检查Git仓库状态...")
                
                # 1. 检查.git目录是否存在
                if not (self.git_repo_path / ".git").exists():
                    self.root.after(0, lambda: self._show_git_not_found_warning())
                    return
                
                # 2. 执行 git fetch 获取远程最新信息
                fetch_result = subprocess.run(
                    ["git", "fetch", "--quiet"],
                    cwd=self.git_repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if fetch_result.returncode != 0:
                    self.root.after(0, lambda: self.log_message("⚠ 无法连接到远程仓库"))
                    self.root.after(0, lambda: self.check_git_status())
                    return
                
                # 3. 检查本地是否落后于远程
                status_result = subprocess.run(
                    ["git", "status", "-uno"],
                    cwd=self.git_repo_path,
                    capture_output=True,
                    text=True
                )
                
                if status_result.returncode == 0:
                    output = status_result.stdout
                    
                    if "Your branch is behind" in output:
                        # 提取落后的提交数
                        import re
                        match = re.search(r"behind .+ by (\d+) commit", output)
                        commit_count = match.group(1) if match else "若干"
                        
                        self.is_git_up_to_date = False
                        self.root.after(0, lambda: self._show_update_available_dialog(commit_count))
                    else:
                        self.is_git_up_to_date = True
                        self.root.after(0, lambda: self.git_status_var.set("Git状态: ✓ 已是最新版本"))
                        self.root.after(0, lambda: self.log_message("✓ 当前已是最新版本"))
                else:
                    self.root.after(0, lambda: self.check_git_status())
                
                # 4. 刷新工具列表
                self.root.after(100, lambda: self.refresh_tools_list())
                
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.log_message("⚠ Git检查超时，请检查网络连接"))
                self.root.after(0, lambda: self.check_git_status())
            except FileNotFoundError:
                self.root.after(0, lambda: self._show_git_not_installed_warning())
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"⚠ 启动检查失败: {e}"))
                self.root.after(0, lambda: self.check_git_status())
        
        # 在后台线程中执行检查
        threading.Thread(target=check_and_notify, daemon=True).start()
    
    def _show_update_available_dialog(self, commit_count):
        """显示更新可用对话框"""
        self.git_status_var.set(f"Git状态: ⚠ 有 {commit_count} 个新提交可更新")
        self.log_message(f"⚠ 检测到 {commit_count} 个新提交可用")
        
        # 创建自定义更新提示对话框
        update_dialog = tk.Toplevel(self.root)
        update_dialog.title("🔔 发现新版本")
        update_dialog.geometry("450x200")
        update_dialog.resizable(False, False)
        update_dialog.transient(self.root)
        update_dialog.grab_set()
        
        # 居中显示
        update_dialog.update_idletasks()
        x = (update_dialog.winfo_screenwidth() - 450) // 2
        y = (update_dialog.winfo_screenheight() - 200) // 2
        update_dialog.geometry(f"450x200+{x}+{y}")
        
        # 内容
        content_frame = ttk.Frame(update_dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图标和消息
        ttk.Label(
            content_frame, 
            text="🔄", 
            font=('Arial', 36)
        ).pack(pady=(0, 10))
        
        ttk.Label(
            content_frame,
            text=f"检测到有 {commit_count} 个新版本更新可用！",
            font=('Arial', 11, 'bold')
        ).pack()
        
        ttk.Label(
            content_frame,
            text="建议立即更新以获取最新的工具和修复",
            font=('Arial', 9),
            foreground='gray'
        ).pack(pady=(5, 15))
        
        # 按钮
        button_frame = ttk.Frame(content_frame)
        button_frame.pack()
        
        def do_update():
            update_dialog.destroy()
            self.update_git_repo()
        
        def skip_update():
            update_dialog.destroy()
            self.log_message("用户选择稍后更新")
        
        ttk.Button(
            button_frame, 
            text="立即更新", 
            command=do_update,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="稍后提醒", 
            command=skip_update,
            width=15
        ).pack(side=tk.LEFT)
    
    def _show_git_not_found_warning(self):
        """显示Git仓库未找到警告"""
        self.git_status_var.set("Git状态: ⚠ 仓库未初始化")
        self.log_message(f"⚠ Git仓库未找到: {self.git_repo_path}")
        messagebox.showwarning(
            "Git仓库未找到",
            f"在以下路径未找到Git仓库:\n{self.git_repo_path}\n\n"
            "请确保：\n"
            "1. 已正确克隆项目仓库\n"
            "2. 或设置环境变量 AI_TOOL_REPO_PATH 指向正确路径"
        )
    
    def _show_git_not_installed_warning(self):
        """显示Git未安装警告"""
        self.git_status_var.set("Git状态: ✗ Git未安装")
        self.log_message("✗ 未检测到Git，请安装Git")
        messagebox.showerror(
            "Git未安装",
            "未检测到Git命令行工具。\n\n"
            "请安装Git后重新启动程序:\n"
            "https://git-scm.com/downloads"
        )
    
    def setup_ui(self):
        """设置轻量级用户界面"""
        self.root.title("🎨 DCC工具管理器 - 轻量版")
        self.root.geometry("1000x800")
        self.root.minsize(950, 700)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部状态栏 - 固定高度
        self.create_status_bar(main_frame)
        
        # 中间区域使用 PanedWindow 分割工具面板和日志面板
        middle_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        middle_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分 - 主要功能区域（工具列表+参数面板）
        self.create_main_panels(middle_paned)
        
        # 下半部分 - 日志和控制区域
        self.create_control_panel(middle_paned)
    
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
        # 创建包装框架
        main_tools_frame = ttk.Frame(parent)
        parent.add(main_tools_frame, weight=3)  # 工具面板占3份
        
        # 使用PanedWindow分割左右界面
        paned_window = ttk.PanedWindow(main_tools_frame, orient=tk.HORIZONTAL)
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
        self.create_tool_category("其他工具", "other")
        
        # 刷新按钮
        refresh_btn = ttk.Button(tools_frame, text="🔄 刷新工具列表", 
                                command=self.refresh_tools_list)
        refresh_btn.pack(fill=tk.X, pady=(10, 0))
    
    def create_tool_category(self, category_name, category_key):
        """创建工具分类标签页"""
        frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(frame, text=category_name)
        
        # === 筛选栏 ===
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(5, 5), padx=5)
        
        # 分组下拉框
        ttk.Label(filter_frame, text="分组:").pack(side=tk.LEFT)
        group_values = [f"{g['icon']} {g['name']}" for g in self.tool_groups.get("groups", [])]
        group_combo = ttk.Combobox(filter_frame, values=group_values, state="readonly", width=12)
        group_combo.pack(side=tk.LEFT, padx=(5, 10))
        group_combo.set(group_values[0] if group_values else "📋 全部")
        group_combo.bind('<<ComboboxSelected>>', lambda e, key=category_key: self._on_group_change(key))
        self.group_combos[category_key] = group_combo
        
        # 分组管理按钮
        ttk.Button(filter_frame, text="⚙", width=2, 
                  command=self._show_group_manager).pack(side=tk.LEFT, padx=(0, 15))
        
        # 搜索框
        ttk.Label(filter_frame, text="搜索:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_var.trace_add('write', lambda *args, key=category_key: self._on_search_change(key))
        self.search_vars[category_key] = search_var
        
        # 搜索清除按钮
        ttk.Button(filter_frame, text="✕", width=2,
                  command=lambda: search_var.set("")).pack(side=tk.LEFT)
        
        # === 工具列表 ===
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 修改列，添加执行模式
        columns = ('version', 'source', 'mode')
        tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=12)
        
        tree.heading('#0', text='工具名称')
        tree.heading('version', text='版本')
        tree.heading('source', text='来源')
        tree.heading('mode', text='执行模式')
        
        tree.column('#0', width=180)
        tree.column('version', width=50)
        tree.column('source', width=40)
        tree.column('mode', width=70)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        tree.bind('<<TreeviewSelect>>', self.on_tool_select)
        tree.bind('<Double-1>', self.on_tool_double_click)
        tree.bind('<Button-3>', lambda e, key=category_key: self._show_tool_context_menu(e, key))
        
        # 保存引用
        setattr(self, f"{category_key}_tree", tree)
    
    def create_execution_panel(self, parent):
        """创建执行面板"""
        exec_frame = ttk.Frame(parent)
        parent.add(exec_frame, weight=2)
        
        # 工具详情区域 - 可扩展
        detail_frame = ttk.LabelFrame(exec_frame, text="工具详情", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.detail_text = tk.Text(detail_frame, height=4, wrap=tk.WORD)
        detail_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, 
                                     command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 参数配置区域 - 可扩展
        param_outer_frame = ttk.LabelFrame(exec_frame, text="参数配置", padding="5")
        param_outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 参数滚动区域
        param_canvas = tk.Canvas(param_outer_frame, highlightthickness=0, height=80)
        param_scrollbar = ttk.Scrollbar(param_outer_frame, orient=tk.VERTICAL, command=param_canvas.yview)
        self.param_frame_inner = ttk.Frame(param_canvas)
        
        self.param_frame_inner.bind(
            "<Configure>",
            lambda e: param_canvas.configure(scrollregion=param_canvas.bbox("all"))
        )
        param_canvas.create_window((0, 0), window=self.param_frame_inner, anchor="nw")
        param_canvas.configure(yscrollcommand=param_scrollbar.set)
        
        param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 执行控制区域 - 固定高度
        control_frame = ttk.LabelFrame(exec_frame, text="执行控制", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 执行按钮行
        btn_row1 = ttk.Frame(control_frame)
        btn_row1.pack(fill=tk.X, pady=(0, 3))
        
        self.run_in_dcc_btn = ttk.Button(btn_row1, text="▶ DCC执行", command=self.run_in_dcc)
        self.run_in_dcc_btn.pack(side=tk.LEFT, padx=(0, 3), fill=tk.X, expand=True)
        
        self.run_standalone_btn = ttk.Button(btn_row1, text="🖥 独立运行", command=self.run_standalone)
        self.run_standalone_btn.pack(side=tk.LEFT, padx=(0, 3), fill=tk.X, expand=True)
        
        self.generate_script_btn = ttk.Button(btn_row1, text="📝 生成脚本", command=self.generate_script)
        self.generate_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # DCC连接控制 - 固定高度
        dcc_frame = ttk.LabelFrame(exec_frame, text="DCC连接", padding="5")
        dcc_frame.pack(fill=tk.X)
        
        # DCC选择行
        dcc_row1 = ttk.Frame(dcc_frame)
        dcc_row1.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(dcc_row1, text="软件:").pack(side=tk.LEFT)
        self.dcc_combo = ttk.Combobox(dcc_row1, 
                                     values=["Maya", "3ds Max", "Blender", "Unreal Engine"],
                                     state="readonly", width=12)
        self.dcc_combo.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)
        self.dcc_combo.set("选择DCC")
        
        # DCC按钮行
        dcc_row2 = ttk.Frame(dcc_frame)
        dcc_row2.pack(fill=tk.X)
        
        ttk.Button(dcc_row2, text="🔗 连接", command=self.connect_dcc).pack(side=tk.LEFT, padx=(0, 3), fill=tk.X, expand=True)
        ttk.Button(dcc_row2, text="⚡ 断开", command=self.disconnect_dcc).pack(side=tk.LEFT, padx=(0, 3), fill=tk.X, expand=True)
        ttk.Button(dcc_row2, text="⚙ 设置", command=self._show_dcc_settings).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 移除测试按钮，简化界面
        self.test_btn = None
    
    def create_control_panel(self, parent):
        """创建底部控制面板（Git管理和日志）"""
        # 底部区域包装框架
        bottom_frame = ttk.Frame(parent)
        parent.add(bottom_frame, weight=1)  # 日志面板占1份
        
        # Git控制 - 固定在顶部
        git_frame = ttk.LabelFrame(bottom_frame, text="Git管理", padding="5")
        git_frame.pack(fill=tk.X, expand=False, pady=(0, 5))
        
        ttk.Button(git_frame, text="⬇️ 更新到最新版本", 
                  command=self.update_git_repo).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(git_frame, text="🔍 检查更新", 
                  command=self.check_git_updates).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(git_frame, text="📋 查看变更日志", 
                  command=self.show_changelog).pack(side=tk.LEFT)
        
        # 日志区域 - 占据剩余空间，放在最下面
        log_frame = ttk.LabelFrame(bottom_frame, text="操作日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
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
        
        # 清空现有列表和缓存
        for category in ['maya', 'max', 'blender', 'ue', 'other']:
            tree = getattr(self, f"{category}_tree")
            for item in tree.get_children():
                tree.delete(item)
        self.tools_cache = {}
        
        # 从Git仓库扫描共享工具
        self.scan_tools_from_git()
        
        # 从本地目录扫描本地工具
        self.scan_tools_from_local()
        
        self.log_message("✓ 工具列表刷新完成")
    
    def get_local_scripts_dir(self) -> Path:
        """获取本地脚本目录（我的文档/DCC_Tool_Manager/local_scripts/）"""
        return self._get_documents_base_dir() / "local_scripts"
    
    def get_local_config_dir(self) -> Path:
        """获取本地配置目录（我的文档/DCC_Tool_Manager/config/）"""
        return self._get_documents_base_dir() / "config"
    
    def scan_tools_from_git(self):
        """从Git仓库扫描共享工具"""
        try:
            plugins_dir = self.git_repo_path / "src" / "plugins"
            
            # 扫描各个类型的工具
            tool_categories = {
                'maya': plugins_dir / 'dcc' / 'maya',
                'max': plugins_dir / 'dcc' / 'max', 
                'blender': plugins_dir / 'dcc' / 'blender',
                'ue': plugins_dir / 'ue',
                'other': plugins_dir / 'other'
            }
            
            for category, category_path in tool_categories.items():
                if category_path.exists():
                    tree = getattr(self, f"{category}_tree")
                    self.load_tools_from_directory(category_path, tree, category, source="共享")
                    
        except Exception as e:
            self.log_message(f"✗ 扫描共享工具失败: {e}")
    
    def scan_tools_from_local(self):
        """从本地目录扫描本地工具"""
        try:
            local_scripts_dir = self.get_local_scripts_dir()
            
            # 确保本地目录存在（已在初始化时调用）
            self._ensure_local_directories()
            
            # 扫描各个类型的本地工具
            tool_categories = {
                'maya': local_scripts_dir / 'maya',
                'max': local_scripts_dir / 'max', 
                'blender': local_scripts_dir / 'blender',
                'ue': local_scripts_dir / 'ue',
                'other': local_scripts_dir / 'other'
            }
            
            for category, category_path in tool_categories.items():
                if category_path.exists():
                    tree = getattr(self, f"{category}_tree")
                    self.load_tools_from_directory(category_path, tree, category, source="本地", is_local=True)
                    
        except Exception as e:
            self.log_message(f"✗ 扫描本地工具失败: {e}")
    
    def load_tools_from_directory(self, directory, tree, category, source="共享", is_local=False):
        """从目录加载工具
        
        Args:
            directory: 工具目录路径
            tree: 树形视图控件
            category: 工具分类 (maya/max/blender/ue)
            source: 来源标识 (共享/本地)
            is_local: 是否为本地工具
        """
        if not directory.exists():
            return
            
        for tool_dir in directory.iterdir():
            if tool_dir.is_dir():
                config_file = tool_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        # 本地工具使用 local_ 前缀避免ID冲突
                        id_prefix = "local_" if is_local else ""
                        
                        # 获取执行模式
                        execution_config = config.get('execution', {})
                        exec_mode = execution_config.get('mode', 'dcc')
                        tool_type = config['plugin'].get('type', category)
                        
                        # other 类型默认独立运行
                        if category == 'other' or tool_type == 'other':
                            exec_mode = execution_config.get('mode', 'standalone')
                            tool_type = 'other'
                        
                        tool_info = {
                            'id': f"{id_prefix}{category}_{tool_dir.name}",
                            'name': config['plugin']['name'],
                            'version': config['plugin']['version'],
                            'description': config['plugin'].get('description', ''),
                            'path': str(tool_dir),  # 本地工具使用绝对路径
                            'parameters': config.get('parameters', {}),
                            'status': '可用',
                            'source': source,
                            'is_local': is_local,
                            'type': tool_type,
                            'execution_mode': exec_mode,
                            'category': category
                        }
                        
                        # 添加到树形视图
                        tree.insert('', 'end',
                                  iid=tool_info['id'],
                                  text=tool_info['name'],
                                  values=(tool_info['version'], tool_info['source'], tool_info['status']))
                        
                        # 保存工具信息
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
            
            # 根据执行模式启用/禁用按钮
            self._update_execution_buttons(tool_info)
    
    def _update_execution_buttons(self, tool_info):
        """根据工具的执行模式更新按钮状态"""
        exec_mode = tool_info.get('execution_mode', 'dcc')
        tool_type = tool_info.get('type', 'dcc')
        
        # other 类型工具默认独立运行
        if tool_type == 'other':
            exec_mode = tool_info.get('execution_mode', 'standalone')
        
        # 根据执行模式设置按钮状态
        if exec_mode == 'standalone':
            self.run_in_dcc_btn.config(state='disabled')
            self.run_standalone_btn.config(state='normal')
        elif exec_mode == 'dcc':
            self.run_in_dcc_btn.config(state='normal')
            self.run_standalone_btn.config(state='disabled')
        elif exec_mode == 'both':
            self.run_in_dcc_btn.config(state='normal')
            self.run_standalone_btn.config(state='normal')
        else:
            # 默认两个都可用
            self.run_in_dcc_btn.config(state='normal')
            self.run_standalone_btn.config(state='normal')
    
    def on_tool_double_click(self, event):
        """工具双击事件"""
        # 双击时自动连接到对应的DCC软件
        tree = event.widget
        selection = tree.selection()
        if selection:
            tool_id = selection[0]
            
            # other 类型工具双击直接独立运行
            if 'other' in tool_id.lower():
                self.run_standalone()
                return
            
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
        # 获取工具分组信息
        tool_id = tool_info.get('id', '')
        tool_groups_list = self.get_tool_groups(tool_id)
        
        # 将分组ID转换为显示名称
        group_names = []
        for group_id in tool_groups_list:
            for g in self.tool_groups.get("groups", []):
                if g["id"] == group_id:
                    group_names.append(f"{g['icon']} {g['name']}")
                    break
            else:
                group_names.append(group_id)
        
        # 获取执行模式
        exec_mode = tool_info.get('execution_mode', 'dcc')
        if tool_info.get('type') == 'other':
            exec_mode = tool_info.get('execution_mode', 'standalone')
        
        exec_mode_display = {
            'dcc': '🔗 DCC中运行',
            'standalone': '🖥️ 独立运行',
            'both': '🔗 DCC / 🖥️ 独立'
        }.get(exec_mode, exec_mode)
        
        # 来源
        source = "本地" if tool_info.get('is_local') else "共享"
        
        info_text = f"""工具名称: {tool_info['name']}
版本: {tool_info['version']}
来源: {source}
执行模式: {exec_mode_display}
分组: {', '.join(group_names) if group_names else '未分组'}
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
        
        def connect_process():
            try:
                if selected_dcc == "Maya":
                    success, message = self._connect_to_maya()
                elif selected_dcc == "3ds Max":
                    success, message = self._connect_to_max()
                elif selected_dcc == "Blender":
                    success, message = self._connect_to_blender()
                elif selected_dcc == "Unreal Engine":
                    success, message = self._connect_to_ue()
                    # UE特殊处理：如果需要设置，弹出设置对话框
                    if not success and message == "NEED_SETUP":
                        self.root.after(0, self._show_ue_setup_dialog)
                        return
                else:
                    success, message = False, "暂不支持该DCC软件"
                
                if success:
                    self.root.after(0, lambda: self.on_dcc_connected(selected_dcc, message))
                else:
                    self.root.after(0, lambda: self.on_dcc_connection_failed(message))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_dcc_connection_failed(str(e)))
        
        threading.Thread(target=connect_process, daemon=True).start()
    
    def _connect_to_maya(self, host="127.0.0.1", port=7001):
        """
        连接到Maya命令端口
        
        注意：需要在Maya中先开启命令端口，在Maya脚本编辑器中执行：
        import maya.cmds as cmds
        cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
        
        Returns:
            tuple: (success: bool, message: str)
        """
        import socket
        
        try:
            # 尝试连接Maya命令端口
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            result = test_socket.connect_ex((host, port))
            
            if result == 0:
                # 发送测试命令
                test_cmd = 'print("DCC Manager Connected")\n'
                test_socket.sendall(test_cmd.encode('utf-8'))
                test_socket.close()
                
                # 保存连接信息
                self.maya_host = host
                self.maya_port = port
                
                return True, f"成功连接到Maya (端口 {port})"
            else:
                test_socket.close()
                # 连接失败，检查是否需要设置userSetup
                self.root.after(0, lambda: self._show_maya_setup_dialog())
                return False, "Maya命令端口未开启"
                
        except socket.timeout:
            self.root.after(0, lambda: self._show_maya_setup_dialog())
            return False, "Maya连接超时"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def _show_maya_setup_dialog(self):
        """显示Maya命令端口设置对话框"""
        # 检查userSetup.py是否已配置
        setup_status = self._check_maya_user_setup()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🔧 Maya命令端口设置")
        dialog.geometry("680x720")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 680) // 2
        y = (dialog.winfo_screenheight() - 720) // 2
        dialog.geometry(f"680x720+{x}+{y}")
        
        # 内容框架
        content = ttk.Frame(dialog, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(
            content,
            text="⚠️ Maya命令端口未开启",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        # 状态信息
        if setup_status['configured']:
            status_text = f"✓ userSetup.py已配置 ({setup_status.get('path', '')})\n请重启Maya使设置生效"
            status_color = "green"
        else:
            if setup_status['maya_versions']:
                status_text = f"✗ 未配置 (检测到Maya版本: {', '.join(setup_status['maya_versions'])})"
            else:
                status_text = "✗ 未找到Maya安装目录"
            status_color = "red"
        
        ttk.Label(
            content,
            text=status_text,
            foreground=status_color,
            font=('Arial', 10)
        ).pack(pady=(0, 15))
        
        # 选项说明
        ttk.Label(
            content,
            text="请选择一个解决方案：",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w')
        
        # 方案选择
        options_frame = ttk.Frame(content)
        options_frame.pack(fill=tk.X, pady=(10, 15))
        
        # 方案1：自动配置
        option1_frame = ttk.LabelFrame(options_frame, text="方案1：自动配置（推荐）", padding="10")
        option1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            option1_frame,
            text="自动在Maya启动脚本中添加命令端口配置，之后每次打开Maya都会自动开启端口。",
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor='w')
        
        # 路径指引说明
        path_hint_frame = ttk.Frame(option1_frame)
        path_hint_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Label(
            path_hint_frame,
            text="💡 如何获取正确的脚本目录？在Maya脚本编辑器中执行：",
            font=('Arial', 8),
            foreground='#666666'
        ).pack(anchor='w')
        
        hint_code = "import maya.cmds as cmds; print(cmds.internalVar(userScriptDir=True))"
        hint_entry = ttk.Entry(path_hint_frame, font=('Consolas', 8), width=65)
        hint_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(2, 0))
        hint_entry.insert(0, hint_code)
        hint_entry.configure(state='readonly')
        
        def copy_hint():
            self.root.clipboard_clear()
            self.root.clipboard_append(hint_code)
            self.log_message("路径查询代码已复制")
        
        ttk.Button(path_hint_frame, text="📋", command=copy_hint, width=3).pack(side=tk.RIGHT, padx=(5, 0), pady=(2, 0))
        
        # 目标目录设置
        path_frame = ttk.Frame(option1_frame)
        path_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(path_frame, text="脚本目录:", font=('Arial', 9)).pack(side=tk.LEFT)
        
        # 默认显示检测到的目录
        default_path = ""
        if setup_status.get('script_dirs'):
            default_path = setup_status['script_dirs'][0]
        elif setup_status['maya_versions']:
            latest_version = sorted(setup_status['maya_versions'], reverse=True)[0]
            default_path = str(Path.home() / "Documents" / "maya" / latest_version / "scripts")
        
        path_var = tk.StringVar(value=default_path)
        path_entry = ttk.Entry(path_frame, textvariable=path_var, font=('Arial', 9), width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        def browse_folder():
            from tkinter import filedialog
            initial_dir = path_var.get() if path_var.get() and Path(path_var.get()).exists() else str(Path.home() / "Documents")
            folder = filedialog.askdirectory(
                title="选择Maya脚本目录 (scripts文件夹)",
                initialdir=initial_dir
            )
            if folder:
                path_var.set(folder)
                self.log_message(f"已选择目录: {folder}")
        
        ttk.Button(path_frame, text="📂 浏览...", command=browse_folder, width=10).pack(side=tk.RIGHT)
        
        # 检测到的其他目录列表（如果有多个）
        if setup_status.get('script_dirs') and len(setup_status['script_dirs']) > 1:
            ttk.Label(
                option1_frame,
                text=f"检测到 {len(setup_status['script_dirs'])} 个脚本目录，可从下拉列表选择：",
                font=('Arial', 8),
                foreground='#888888'
            ).pack(anchor='w', pady=(5, 0))
            
            detected_combo = ttk.Combobox(
                option1_frame,
                values=setup_status['script_dirs'],
                font=('Arial', 8),
                state='readonly',
                width=70
            )
            detected_combo.pack(fill=tk.X, pady=(2, 0))
            detected_combo.set(setup_status['script_dirs'][0])
            
            def on_combo_select(event):
                path_var.set(detected_combo.get())
            detected_combo.bind('<<ComboboxSelected>>', on_combo_select)
        
        # 自动配置按钮
        def auto_setup():
            custom_path = path_var.get().strip()
            if custom_path:
                # 使用用户指定的目录
                self.log_message(f"正在配置 userSetup.py 到: {custom_path}")
                success, message = self._setup_maya_user_setup_to_path(custom_path)
            else:
                # 使用自动检测
                self.log_message("正在自动配置Maya userSetup.py...")
                success, message = self._setup_maya_user_setup()
            
            if success:
                self.log_message(f"✓ {message}", level="success")
                messagebox.showinfo("设置成功", f"{message}\n\n请完全关闭Maya后重新打开，然后重新点击\"连接\"按钮。")
                dialog.destroy()
            else:
                self.log_message(f"✗ 配置失败: {message}", level="error")
                messagebox.showerror("设置失败", f"配置失败：{message}")
        
        btn_frame = ttk.Frame(option1_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="🔧 配置到指定目录",
            command=auto_setup,
            width=20
        ).pack(side=tk.LEFT)
        
        def auto_setup_all():
            self.log_message("正在配置所有检测到的Maya版本...")
            success, message = self._setup_maya_user_setup()
            if success:
                self.log_message(f"✓ {message}", level="success")
                messagebox.showinfo("设置成功", f"{message}\n\n请重启Maya使设置生效。")
                dialog.destroy()
            else:
                self.log_message(f"✗ {message}", level="error")
                messagebox.showerror("设置失败", message)
        
        ttk.Button(
            btn_frame,
            text="🔧 配置所有Maya版本",
            command=auto_setup_all,
            width=20
        ).pack(side=tk.RIGHT)
        
        # 方案2：手动执行
        option2_frame = ttk.LabelFrame(options_frame, text="方案2：手动执行（临时）", padding="10")
        option2_frame.pack(fill=tk.X)
        
        ttk.Label(
            option2_frame,
            text="复制下面的代码到Maya脚本编辑器中执行，仅对当前Maya会话有效。",
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor='w')
        
        # 代码框架
        code_frame = ttk.Frame(option2_frame)
        code_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 代码文本框
        code_text = tk.Text(code_frame, height=5, width=60, font=('Consolas', 9), bg='#f5f5f5')
        code_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        manual_code = '''import maya.cmds as cmds
# 关闭已存在的端口
if cmds.commandPort(':7001', query=True):
    cmds.commandPort(name=':7001', close=True)
# 开启命令端口
cmds.commandPort(name=':7001', sourceType='python', echoOutput=False, noreturn=False, bufferSize=4096)
print('[OK] 命令端口 7001 已开启，现在可以连接了!')'''
        
        code_text.insert('1.0', manual_code)
        code_text.configure(state='disabled')
        
        # 复制按钮（放在代码框右侧，更醒目）
        def copy_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(manual_code)
            copy_btn.configure(text="✓ 已复制!")
            self.log_message("Maya命令端口代码已复制到剪贴板")
            # 2秒后恢复按钮文字
            dialog.after(2000, lambda: copy_btn.configure(text="📋 复制"))
        
        copy_btn = ttk.Button(
            code_frame,
            text="📋 复制",
            command=copy_code,
            width=10
        )
        copy_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 调试信息框架
        debug_frame = ttk.LabelFrame(content, text="🔍 调试信息", padding="10")
        debug_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 添加检查端口代码
        check_port_code = '''# 检查端口状态
import maya.cmds as cmds
port_open = cmds.commandPort(':7001', query=True)
print(f'端口7001状态: {"已开启" if port_open else "未开启"}')'''
        
        ttk.Label(
            debug_frame,
            text="在Maya中执行以下代码检查端口状态：",
            font=('Arial', 9)
        ).pack(anchor='w')
        
        debug_text = tk.Text(debug_frame, height=4, width=55, font=('Consolas', 9), bg='#fff8e1')
        debug_text.pack(fill=tk.X, pady=(5, 0))
        debug_text.insert('1.0', check_port_code)
        debug_text.configure(state='disabled')
        
        def copy_debug_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(check_port_code)
            self.log_message("调试代码已复制")
        
        ttk.Button(debug_frame, text="📋 复制检测代码", command=copy_debug_code).pack(anchor='e', pady=(5, 0))
        
        # 底部按钮框架
        bottom_frame = ttk.Frame(content)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 重试连接按钮
        def retry_connection():
            dialog.destroy()
            self.log_message("重试连接Maya...")
            self.connect_dcc("maya")
        
        retry_btn = ttk.Button(
            bottom_frame,
            text="🔄 重试连接",
            command=retry_connection,
            width=15
        )
        retry_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 关闭按钮
        ttk.Button(
            bottom_frame,
            text="关闭",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)
        
        # 打开Maya脚本目录按钮
        def open_maya_scripts_folder():
            # 优先打开已配置的路径所在目录
            if setup_status.get('path'):
                scripts_path = Path(setup_status['path']).parent
                os.startfile(str(scripts_path))
            elif setup_status.get('script_dirs'):
                # 打开第一个找到的脚本目录
                os.startfile(setup_status['script_dirs'][0])
            elif setup_status['maya_versions']:
                # 尝试打开最新版本的maya目录
                latest_version = sorted(setup_status['maya_versions'], reverse=True)[0]
                maya_version_path = Path.home() / "Documents" / "maya" / latest_version
                if maya_version_path.exists():
                    os.startfile(str(maya_version_path))
                else:
                    messagebox.showwarning("警告", f"目录不存在: {maya_version_path}")
            else:
                messagebox.showwarning("警告", "未找到Maya安装目录")
        
        ttk.Button(
            bottom_frame,
            text="📂 打开脚本目录",
            command=open_maya_scripts_folder,
            width=15
        ).pack(side=tk.LEFT)
    
    def _check_maya_user_setup(self) -> dict:
        """
        检查Maya的userSetup.py是否已配置命令端口
        
        Returns:
            dict: {'configured': bool, 'path': str, 'maya_versions': list, 'script_dirs': list}
        """
        result = {
            'configured': False,
            'path': None,
            'maya_versions': [],
            'script_dirs': []  # 所有找到的脚本目录
        }
        
        # 查找Maya文档目录
        user_docs = Path.home() / "Documents" / "maya"
        if not user_docs.exists():
            return result
        
        # 遍历所有Maya版本目录
        for version_dir in user_docs.iterdir():
            if version_dir.is_dir() and version_dir.name.isdigit():
                result['maya_versions'].append(version_dir.name)
                
                # 查找所有可能的scripts目录（支持语言后缀如zh_CN、en_US等）
                scripts_to_check = []
                
                # 1. 检查带语言后缀的目录
                for subdir in version_dir.iterdir():
                    if subdir.is_dir():
                        locale_scripts = subdir / "scripts"
                        if locale_scripts.exists():
                            scripts_to_check.append(locale_scripts)
                
                # 2. 检查直接的scripts目录
                direct_scripts = version_dir / "scripts"
                if direct_scripts.exists():
                    scripts_to_check.append(direct_scripts)
                
                # 检查每个scripts目录
                for scripts_dir in scripts_to_check:
                    result['script_dirs'].append(str(scripts_dir))
                    user_setup = scripts_dir / "userSetup.py"
                    
                    if user_setup.exists():
                        try:
                            content = user_setup.read_text(encoding='utf-8')
                            if 'commandPort' in content and '7001' in content:
                                result['configured'] = True
                                result['path'] = str(user_setup)
                        except:
                            pass
        
        return result
    
    def _setup_maya_user_setup_to_path(self, scripts_dir: str) -> tuple:
        """
        配置userSetup.py到指定的脚本目录
        
        Args:
            scripts_dir: Maya脚本目录路径
        
        Returns:
            tuple: (success: bool, message: str)
        """
        scripts_path = Path(scripts_dir)
        
        # 验证路径
        if not scripts_path.exists():
            try:
                scripts_path.mkdir(parents=True, exist_ok=True)
                self.log_message(f"  创建目录: {scripts_path}")
            except Exception as e:
                return False, f"无法创建目录: {e}"
        
        # 要添加的代码
        setup_code = self._get_maya_setup_code()
        
        user_setup = scripts_path / "userSetup.py"
        
        try:
            if user_setup.exists():
                existing_content = user_setup.read_text(encoding='utf-8')
                if 'DCC工具管理器自动添加' in existing_content:
                    return True, f"已配置过: {user_setup}"
                
                # 追加到文件末尾
                with open(user_setup, 'a', encoding='utf-8') as f:
                    f.write('\n' + setup_code)
                self.log_message(f"  ✓ 已追加配置到: {user_setup}")
            else:
                # 创建新文件
                with open(user_setup, 'w', encoding='utf-8') as f:
                    f.write(setup_code)
                self.log_message(f"  ✓ 已创建: {user_setup}")
            
            return True, f"配置成功: {user_setup}"
            
        except PermissionError:
            return False, f"权限不足: {user_setup}"
        except Exception as e:
            return False, f"配置失败: {e}"
    
    def _get_maya_setup_code(self) -> str:
        """获取Maya userSetup.py的配置代码"""
        return '''
# === DCC工具管理器自动添加 ===
# 启动时自动开启命令端口，用于外部工具连接
# 版本: 2.0 - 使用evalDeferred字符串方式确保执行

import maya.cmds as cmds
import maya.mel as mel

# 定义开启端口的代码（使用字符串形式的evalDeferred更可靠）
_dcc_port_setup_code = """
import maya.cmds as cmds
try:
    # 先关闭可能存在的旧端口
    if cmds.commandPort(':7001', query=True):
        cmds.commandPort(name=':7001', close=True)
    # 开启新端口 - 使用完整格式
    cmds.commandPort(name=':7001', sourceType='python', echoOutput=False, noreturn=False, bufferSize=4096)
    print('[DCC Manager] 命令端口 7001 已成功开启')
except Exception as e:
    import traceback
    print('[DCC Manager] 命令端口开启失败:')
    traceback.print_exc()
"""

# 使用evalDeferred确保在Maya完全初始化后执行
cmds.evalDeferred(_dcc_port_setup_code)
# === DCC工具管理器自动添加结束 ===
'''
    
    def _setup_maya_user_setup(self, target_versions: list = None) -> tuple:
        """
        自动配置Maya的userSetup.py以开启命令端口
        
        Args:
            target_versions: 要配置的Maya版本列表，None表示配置所有版本
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # 查找Maya文档目录
        user_docs = Path.home() / "Documents" / "maya"
        if not user_docs.exists():
            return False, "未找到Maya文档目录"
        
        # 查找所有Maya版本
        maya_versions = []
        for version_dir in user_docs.iterdir():
            if version_dir.is_dir() and version_dir.name.isdigit():
                maya_versions.append(version_dir.name)
        
        if not maya_versions:
            return False, "未找到任何Maya版本目录"
        
        # 如果指定了目标版本，只配置这些版本
        if target_versions:
            maya_versions = [v for v in maya_versions if v in target_versions]
        
        # 使用统一的配置代码
        setup_code = self._get_maya_setup_code()
        
        configured_versions = []
        skipped_versions = []
        failed_versions = []
        
        # 为每个版本配置
        for version in maya_versions:
            version_dir = user_docs / version
            
            # 查找所有可能的scripts目录（支持语言后缀如zh_CN、en_US等）
            script_dirs_to_check = []
            
            # 1. 先检查带语言后缀的目录（如 zh_CN/scripts, en_US/scripts）
            for subdir in version_dir.iterdir():
                if subdir.is_dir():
                    locale_scripts = subdir / "scripts"
                    if locale_scripts.exists() or subdir.name in ['zh_CN', 'en_US', 'ja_JP', 'ko_KR', 'zh_TW']:
                        script_dirs_to_check.append(locale_scripts)
            
            # 2. 也检查直接的scripts目录
            direct_scripts = version_dir / "scripts"
            if direct_scripts not in script_dirs_to_check:
                script_dirs_to_check.append(direct_scripts)
            
            # 如果没有找到任何已存在的scripts目录，使用直接目录
            if not script_dirs_to_check:
                script_dirs_to_check = [direct_scripts]
            
            version_configured = False
            for scripts_dir in script_dirs_to_check:
                scripts_dir.mkdir(parents=True, exist_ok=True)
                user_setup = scripts_dir / "userSetup.py"
                
                try:
                    # 如果文件已存在，检查是否已经配置
                    if user_setup.exists():
                        existing_content = user_setup.read_text(encoding='utf-8')
                        if 'DCC工具管理器自动添加' in existing_content:
                            skipped_versions.append(f"{version} ({scripts_dir.parent.name})")
                            self.log_message(f"  Maya {version} ({scripts_dir.parent.name}): 已配置，跳过")
                            version_configured = True
                            continue
                        
                        # 追加到文件末尾
                        with open(user_setup, 'a', encoding='utf-8') as f:
                            f.write('\n' + setup_code)
                    else:
                        # 创建新文件
                        with open(user_setup, 'w', encoding='utf-8') as f:
                            f.write(setup_code)
                    
                    configured_versions.append(f"{version} ({scripts_dir.parent.name})")
                    self.log_message(f"  ✓ Maya {version} ({scripts_dir.parent.name}): 配置成功 -> {user_setup}")
                    version_configured = True
                    
                except PermissionError:
                    failed_versions.append(f"{version}(权限不足)")
                    self.log_message(f"  ✗ Maya {version}: 权限不足")
                except Exception as e:
                    failed_versions.append(f"{version}({str(e)})")
                    self.log_message(f"  ✗ Maya {version}: {e}")
            
        
        # 生成结果消息
        if configured_versions:
            msg = f"已配置 Maya {', '.join(configured_versions)}"
            if skipped_versions:
                msg += f"\n已跳过(已配置): {', '.join(skipped_versions)}"
            if failed_versions:
                msg += f"\n配置失败: {', '.join(failed_versions)}"
            return True, msg
        elif skipped_versions:
            return True, f"所有版本已配置: {', '.join(skipped_versions)}"
        else:
            return False, f"配置失败: {', '.join(failed_versions)}"
    
    def _get_maya_connection_help(self):
        """获取Maya连接帮助信息"""
        return """无法连接到Maya命令端口。

请在Maya脚本编辑器中执行以下代码开启命令端口：

import maya.cmds as cmds

# 关闭旧端口（如果存在）
if cmds.commandPort(':7001', query=True):
    cmds.commandPort(name=':7001', close=True)

# 开启新端口（不带echoOutput避免编码问题）
cmds.commandPort(name=':7001', sourceType='python', echoOutput=False)
print('命令端口已开启: 7001')

然后重新点击"连接"按钮。"""
    
    def _connect_to_max(self, host="127.0.0.1", port=7002):
        """
        连接到3ds Max
        
        3ds Max通过Python或MAXScript监听端口进行连接
        默认使用端口7002
        
        Returns:
            tuple: (success: bool, message: str)
        """
        import socket
        
        try:
            # 尝试连接3ds Max Python端口
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            result = test_socket.connect_ex((host, port))
            
            if result == 0:
                # 发送测试命令
                test_cmd = 'print("DCC Manager Connected to 3ds Max")\n'
                test_socket.sendall(test_cmd.encode('utf-8'))
                test_socket.close()
                
                # 保存连接信息
                self.max_host = host
                self.max_port = port
                
                return True, f"成功连接到3ds Max (端口 {port})"
            else:
                test_socket.close()
                # 连接失败，显示设置对话框
                self.root.after(0, lambda: self._show_max_setup_dialog())
                return False, "3ds Max Python服务未开启"
                
        except socket.timeout:
            self.root.after(0, lambda: self._show_max_setup_dialog())
            return False, "3ds Max连接超时"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def _show_max_setup_dialog(self):
        """显示3ds Max连接设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔧 3ds Max连接设置")
        dialog.geometry("600x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 420) // 2
        dialog.geometry(f"600x420+{x}+{y}")
        
        # 内容框架
        content = ttk.Frame(dialog, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(
            content,
            text="⚠️ 3ds Max Python服务未开启",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        ttk.Label(
            content,
            text="请在3ds Max中执行以下步骤来开启Python监听服务：",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 15))
        
        # 方案说明
        options_frame = ttk.Frame(content)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 方案：手动执行
        option_frame = ttk.LabelFrame(options_frame, text="在3ds Max脚本监听器中执行", padding="10")
        option_frame.pack(fill=tk.X)
        
        ttk.Label(
            option_frame,
            text="1. 打开3ds Max → 脚本 → MAXScript监听器\n2. 复制下面的代码并执行",
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor='w')
        
        # 代码框架
        code_frame = ttk.Frame(option_frame)
        code_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 代码文本框
        code_text = tk.Text(code_frame, height=8, width=60, font=('Consolas', 9), bg='#f5f5f5')
        code_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        manual_code = '''-- 3ds Max Python Socket Server
-- 在MAXScript监听器中执行此代码
python.Execute "
import socket
import threading

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 7002))
    server.listen(1)
    print('3ds Max Python Server started on port 7002')
    while True:
        client, addr = server.accept()
        data = client.recv(4096).decode('utf-8')
        if data:
            try:
                exec(data)
            except Exception as e:
                print(f'Error: {e}')
        client.close()

threading.Thread(target=start_server, daemon=True).start()
"
print "Python Server Started on port 7002"'''
        
        code_text.insert('1.0', manual_code)
        code_text.configure(state='disabled')
        
        # 复制按钮
        def copy_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(manual_code)
            copy_btn.configure(text="✓ 已复制!")
            self.log_message("3ds Max连接代码已复制到剪贴板")
            dialog.after(2000, lambda: copy_btn.configure(text="📋 复制"))
        
        copy_btn = ttk.Button(
            code_frame,
            text="📋 复制",
            command=copy_code,
            width=10
        )
        copy_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 提示信息
        ttk.Label(
            content,
            text="提示：执行后3ds Max将在端口7002监听Python命令",
            font=('Arial', 9),
            foreground='blue'
        ).pack(pady=(10, 0))
        
        # 关闭按钮
        ttk.Button(
            content,
            text="关闭",
            command=dialog.destroy,
            width=15
        ).pack(pady=(15, 0))
    
    def _connect_to_blender(self, host="127.0.0.1", port=7003):
        """
        连接到Blender
        
        Blender通过Python socket监听端口进行连接
        默认使用端口7003
        
        Returns:
            tuple: (success: bool, message: str)
        """
        import socket
        
        try:
            # 尝试连接Blender Python端口
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            result = test_socket.connect_ex((host, port))
            
            if result == 0:
                # 发送测试命令
                test_cmd = 'print("DCC Manager Connected to Blender")\n'
                test_socket.sendall(test_cmd.encode('utf-8'))
                test_socket.close()
                
                # 保存连接信息
                self.blender_host = host
                self.blender_port = port
                
                return True, f"成功连接到Blender (端口 {port})"
            else:
                test_socket.close()
                # 连接失败，显示设置对话框
                self.root.after(0, lambda: self._show_blender_setup_dialog())
                return False, "Blender Python服务未开启"
                
        except socket.timeout:
            self.root.after(0, lambda: self._show_blender_setup_dialog())
            return False, "Blender连接超时"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def _show_blender_setup_dialog(self):
        """显示Blender连接设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔧 Blender连接设置")
        dialog.geometry("650x480")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 650) // 2
        y = (dialog.winfo_screenheight() - 480) // 2
        dialog.geometry(f"650x480+{x}+{y}")
        
        # 内容框架
        content = ttk.Frame(dialog, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(
            content,
            text="⚠️ Blender Python服务未开启",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        ttk.Label(
            content,
            text="请在Blender中执行以下步骤来开启Python监听服务：",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 15))
        
        # 方案说明
        options_frame = ttk.Frame(content)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 方案：手动执行
        option_frame = ttk.LabelFrame(options_frame, text="在Blender脚本编辑器中执行", padding="10")
        option_frame.pack(fill=tk.X)
        
        ttk.Label(
            option_frame,
            text="1. 打开Blender → 切换到Scripting工作区\n2. 创建新脚本，复制下面的代码并运行",
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor='w')
        
        # 代码框架
        code_frame = ttk.Frame(option_frame)
        code_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 代码文本框
        code_text = tk.Text(code_frame, height=12, width=65, font=('Consolas', 9), bg='#f5f5f5')
        code_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        manual_code = '''# Blender Python Socket Server
# 在Blender脚本编辑器中运行此代码

import bpy
import socket
import threading

def socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 7003))
    server.listen(1)
    print('Blender Python Server started on port 7003')
    
    while True:
        try:
            client, addr = server.accept()
            data = client.recv(8192).decode('utf-8')
            if data:
                try:
                    exec(data, {'bpy': bpy})
                except Exception as e:
                    print(f'Execution error: {e}')
            client.close()
        except Exception as e:
            print(f'Server error: {e}')
            break

# 启动服务器线程
server_thread = threading.Thread(target=socket_server, daemon=True)
server_thread.start()
print('Socket server is running...')'''
        
        code_text.insert('1.0', manual_code)
        code_text.configure(state='disabled')
        
        # 复制按钮
        def copy_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(manual_code)
            copy_btn.configure(text="✓ 已复制!")
            self.log_message("Blender连接代码已复制到剪贴板")
            dialog.after(2000, lambda: copy_btn.configure(text="📋 复制"))
        
        copy_btn = ttk.Button(
            code_frame,
            text="📋 复制",
            command=copy_code,
            width=10
        )
        copy_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 提示信息
        ttk.Label(
            content,
            text="提示：执行后Blender将在端口7003监听Python命令\n您也可以将此代码保存为插件实现自动启动",
            font=('Arial', 9),
            foreground='blue'
        ).pack(pady=(10, 0))
        
        # 关闭按钮
        ttk.Button(
            content,
            text="关闭",
            command=dialog.destroy,
            width=15
        ).pack(pady=(15, 0))
    
    def _send_to_max(self, python_code: str) -> tuple:
        """
        发送Python代码到3ds Max执行
        
        Args:
            python_code: 要执行的Python代码
            
        Returns:
            tuple: (success: bool, result: str)
        """
        import socket
        
        if not hasattr(self, 'max_host') or not hasattr(self, 'max_port'):
            return False, "未连接到3ds Max"
        
        try:
            max_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            max_socket.settimeout(30)
            max_socket.connect((self.max_host, self.max_port))
            
            if not python_code.endswith('\n'):
                python_code += '\n'
            
            max_socket.sendall(python_code.encode('utf-8'))
            
            import time
            time.sleep(0.5)
            
            max_socket.close()
            return True, "代码已发送到3ds Max执行"
            
        except socket.timeout:
            return False, "3ds Max响应超时"
        except ConnectionRefusedError:
            return False, "3ds Max连接被拒绝"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
    
    def _send_to_blender(self, python_code: str) -> tuple:
        """
        发送Python代码到Blender执行
        
        Args:
            python_code: 要执行的Python代码
            
        Returns:
            tuple: (success: bool, result: str)
        """
        import socket
        
        if not hasattr(self, 'blender_host') or not hasattr(self, 'blender_port'):
            return False, "未连接到Blender"
        
        try:
            blender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            blender_socket.settimeout(30)
            blender_socket.connect((self.blender_host, self.blender_port))
            
            if not python_code.endswith('\n'):
                python_code += '\n'
            
            blender_socket.sendall(python_code.encode('utf-8'))
            
            import time
            time.sleep(0.5)
            
            blender_socket.close()
            return True, "代码已发送到Blender执行"
            
        except socket.timeout:
            return False, "Blender响应超时"
        except ConnectionRefusedError:
            return False, "Blender连接被拒绝"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
    
    # ==================== Unreal Engine 连接相关方法 ====================
    
    def _connect_to_ue(self, host="127.0.0.1", port=30010):
        """
        连接到Unreal Engine
        
        流程：
        1. 检查监听器是否已配置并运行
        2. 如果监听器未运行，弹出设置对话框引导用户配置
        3. 连接成功后可通过文件交换方式执行脚本
        
        Returns:
            tuple: (success: bool, message: str)
        """
        import tempfile
        import time
        
        # 检查监听器是否在运行（通过文件测试）
        listener_running = self._check_ue_listener_running()
        
        if listener_running:
            # 监听器已运行，直接连接
            self.ue_host = host
            self.ue_port = port
            self.ue_connected = True
            return True, "✓ 已连接到Unreal Engine（监听器运行中）"
        else:
            # 监听器未运行，需要显示设置对话框
            # 返回特殊状态码让UI层处理
            return False, "NEED_SETUP"
    
    def _check_ue_listener_running(self) -> bool:
        """
        检查UE监听器是否正在运行
        通过写入测试文件并等待监听器处理来检测
        """
        import tempfile
        import time
        
        try:
            script_exchange_dir = Path(tempfile.gettempdir()) / "DCC_UE_Scripts"
            pending_dir = script_exchange_dir / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建一个测试文件（空操作脚本）
            test_file = pending_dir / f"_connection_test_{int(time.time()*1000)}.py"
            test_file.write_text("# Connection test\npass\n", encoding='utf-8')
            
            # 等待监听器处理（监听器每500ms检查一次）
            time.sleep(0.7)
            
            # 如果文件被删除，说明监听器在运行
            if not test_file.exists():
                return True
            else:
                # 清理测试文件
                try:
                    test_file.unlink()
                except:
                    pass
                return False
                
        except Exception as e:
            return False
    
    def _show_ue_setup_dialog(self):
        """显示UE监听器设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔧 Unreal Engine 设置")
        dialog.geometry("700x720")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 700) // 2
        y = (dialog.winfo_screenheight() - 720) // 2
        dialog.geometry(f"700x720+{x}+{y}")
        
        # 创建可滚动的内容区域
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        content = scrollable_frame
        
        # 标题
        ttk.Label(
            content,
            text="🎮 Unreal Engine 监听器配置",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 15))
        
        # ========== 自动配置区域（推荐，放在最前面）==========
        auto_frame = ttk.LabelFrame(content, text="🚀 一键自动配置（推荐）", padding="15")
        auto_frame.pack(fill=tk.X, pady=(0, 15))
        
        auto_text = """配置后监听器会在UE启动时自动运行，无需手动操作！
脚本会部署到UE项目的 Content/Python 目录，团队成员获取项目后即可直接使用。"""
        
        ttk.Label(
            auto_frame,
            text=auto_text,
            font=('Arial', 9),
            justify='left',
            foreground='#006400'
        ).pack(anchor='w')
        
        # UE项目路径输入
        path_frame = ttk.Frame(auto_frame)
        path_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(path_frame, text="UE项目路径:").pack(side=tk.LEFT)
        
        # 获取已配置的项目路径
        saved_paths = self.local_settings.get("ue_project_paths", [])
        last_path = self.local_settings.get("last_ue_project", "")
        
        ue_project_var = tk.StringVar(value=last_path)
        
        if saved_paths:
            # 使用Combobox显示历史路径
            ue_project_combo = ttk.Combobox(path_frame, textvariable=ue_project_var, 
                                           values=saved_paths, width=42)
            ue_project_combo.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        else:
            # 没有历史路径，使用Entry
            ue_project_entry = ttk.Entry(path_frame, textvariable=ue_project_var, width=45)
            ue_project_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        def browse_ue_project():
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="选择UE项目根目录（包含.uproject文件的目录）")
            if folder:
                ue_project_var.set(folder)
        
        ttk.Button(path_frame, text="浏览...", command=browse_ue_project, width=8).pack(side=tk.LEFT)
        
        # 按钮行
        btn_frame = ttk.Frame(auto_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 自动配置按钮
        def do_auto_setup():
            ue_path = ue_project_var.get().strip()
            if not ue_path:
                messagebox.showerror("错误", "请先选择UE项目路径")
                return
            
            success, message = self._setup_ue_auto_listener(ue_path)
            if success:
                messagebox.showinfo("配置成功", message)
            else:
                messagebox.showerror("配置失败", message)
        
        ttk.Button(
            btn_frame,
            text="🔧 一键配置/更新",
            command=do_auto_setup,
            width=18
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 更新所有已配置项目的按钮
        def update_all_projects():
            paths = self.local_settings.get("ue_project_paths", [])
            if not paths:
                messagebox.showinfo("提示", "没有已配置的UE项目")
                return
            
            updated = 0
            failed = 0
            for path in paths:
                success, _ = self._setup_ue_auto_listener(path)
                if success:
                    updated += 1
                else:
                    failed += 1
            
            messagebox.showinfo("更新完成", f"已更新 {updated} 个项目\n失败 {failed} 个")
        
        if saved_paths:
            ttk.Button(
                btn_frame,
                text="🔄 更新所有项目",
                command=update_all_projects,
                width=15
            ).pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(content, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # ========== 手动启动区域 ==========
        manual_frame = ttk.LabelFrame(content, text="📋 手动启动（可选）", padding="15")
        manual_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 获取监听器脚本路径（使用正斜杠）
        listener_path = Path(__file__).parent.parent / "plugins" / "ue" / "ue_script_listener.py"
        listener_path_str = str(listener_path.resolve()).replace('\\', '/')
        
        steps_text = f"""如果不想配置自动启动，也可以每次手动启动监听器：

1. 在UE中打开 Output Log (Window → Developer Tools → Output Log)
2. 在底部命令行执行以下命令：

   py "{listener_path_str}"

3. 看到 "[UE Listener] Started" 表示成功"""
        
        ttk.Label(
            manual_frame,
            text=steps_text,
            font=('Consolas', 9),
            justify='left'
        ).pack(anchor='w')
        
        # 复制命令按钮
        def copy_listener_cmd():
            self.root.clipboard_clear()
            self.root.clipboard_append(f'py "{listener_path_str}"')
            messagebox.showinfo("已复制", "命令已复制到剪贴板！\n在UE Output Log中粘贴执行")
        
        ttk.Button(
            manual_frame,
            text="📋 复制启动命令",
            command=copy_listener_cmd,
            width=18
        ).pack(pady=(10, 0), anchor='w')
        
        # ========== 监听器控制命令 ==========
        cmd_frame = ttk.LabelFrame(content, text="🎛️ 监听器控制命令", padding="15")
        cmd_frame.pack(fill=tk.X, pady=(0, 15))
        
        cmd_text = """查看状态: py -c "import ue_script_listener; ue_script_listener.status()"
停止监听: py -c "import ue_script_listener; ue_script_listener.stop()"
重新启动: py -c "import ue_script_listener; ue_script_listener.start()"
清空队列: py -c "import ue_script_listener; ue_script_listener.clear_pending()" """
        
        ttk.Label(
            cmd_frame,
            text=cmd_text,
            font=('Consolas', 8),
            justify='left',
            foreground='gray'
        ).pack(anchor='w')
        
        # ========== 工作原理 ==========
        how_frame = ttk.LabelFrame(content, text="💡 工作原理", padding="15")
        how_frame.pack(fill=tk.X, pady=(0, 15))
        
        how_text = """监听器采用文件交换模式（绕过Remote Control API限制）：

1. UI面板将脚本保存到: %TEMP%/DCC_UE_Scripts/pending/
2. UE中的监听器每500ms检查该目录
3. 发现新脚本时自动执行
4. 执行完成后移动到 executed/ 目录"""
        
        ttk.Label(
            how_frame,
            text=how_text,
            font=('Arial', 9),
            justify='left'
        ).pack(anchor='w')
        
        # 按钮区域
        button_frame = ttk.Frame(content)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="关闭",
            command=dialog.destroy,
            width=15
        ).pack(side=tk.LEFT)
    
    def _setup_ue_auto_listener(self, ue_project_path: str) -> tuple:
        """
        配置UE项目自动启动监听器
        
        将监听器脚本部署到UE项目的 Content/Python 目录
        如果已存在 init_unreal.py，则智能合并代码
        同时保存项目路径到本地配置
        
        Args:
            ue_project_path: UE项目根目录路径
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            ue_path = Path(ue_project_path)
            
            # 验证是否是有效的UE项目目录
            uproject_files = list(ue_path.glob("*.uproject"))
            if not uproject_files:
                return False, f"在 {ue_project_path} 中未找到 .uproject 文件\n请确保选择了正确的UE项目根目录"
            
            # 创建 Content/Python 目录
            python_dir = ue_path / "Content" / "Python"
            python_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制监听器脚本（总是更新到最新版本）
            source_listener = Path(__file__).parent.parent / "plugins" / "ue" / "ue_script_listener.py"
            dest_listener = python_dir / "ue_script_listener.py"
            
            if source_listener.exists():
                import shutil
                shutil.copy2(source_listener, dest_listener)
            else:
                return False, f"源文件不存在: {source_listener}"
            
            # 处理 init_unreal.py
            init_file = python_dir / "init_unreal.py"
            
            # 生成要添加的启动代码
            startup_code = '''
# ============================================================
# DCC Tool Manager - UE Listener Auto-Start
# This code was added by DCC Tool Manager
# ============================================================
def _start_dcc_listener():
    """启动 DCC Tool Manager 监听器"""
    try:
        import ue_script_listener
        ue_script_listener.start()
        try:
            import unreal
            unreal.log("[DCC Tool Manager] Listener started successfully")
        except:
            pass
    except Exception as e:
        try:
            import unreal
            unreal.log_warning(f"[DCC Tool Manager] Failed to start listener: {e}")
        except:
            pass

# 自动启动监听器
_start_dcc_listener()
# ============================================================
'''
            
            is_update = False
            if init_file.exists():
                # 读取现有内容
                with open(init_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # 检查是否已经包含我们的代码
                if '_start_dcc_listener' in existing_content:
                    is_update = True
                else:
                    # 追加代码到现有文件
                    with open(init_file, 'a', encoding='utf-8') as f:
                        f.write('\n' + startup_code)
            else:
                # 创建新的 init_unreal.py
                full_init_code = '''"""
UE Python Startup Script
Auto-generated by DCC Tool Manager
"""
''' + startup_code
                
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(full_init_code)
            
            # 保存UE项目路径到本地配置
            self._add_ue_project_path(ue_project_path)
            
            if is_update:
                return True, f"✓ 监听器脚本已更新到最新版本\n\n文件位置:\n{dest_listener}\n\n重启UE即可生效"
            else:
                return True, f"✓ 已配置自动启动监听器\n\n文件位置:\n{dest_listener}\n\n重启UE即可生效"
                
        except Exception as e:
            return False, f"配置失败: {str(e)}"
    
    def _retry_ue_connection(self, dialog):
        """重试UE连接"""
        dialog.destroy()
        self.connect_dcc()
    
    def _show_dcc_settings(self):
        """显示DCC设置对话框"""
        selected_dcc = self.dcc_combo.get().lower()
        
        if "unreal" in selected_dcc:
            self._show_ue_setup_dialog()
        elif "maya" in selected_dcc:
            self._show_maya_settings_dialog()
        elif "max" in selected_dcc:
            self._show_max_settings_dialog()
        elif "blender" in selected_dcc:
            self._show_blender_settings_dialog()
        else:
            messagebox.showinfo("提示", "请先选择要设置的DCC软件")
    
    def _show_maya_settings_dialog(self):
        """显示Maya设置对话框"""
        messagebox.showinfo(
            "Maya 设置",
            "Maya 通过 CommandPort 连接，默认端口 7001\n\n"
            "确保在 Maya 中执行以下命令启用 CommandPort:\n"
            "import maya.cmds as cmds\n"
            "cmds.commandPort(name=':7001', sourceType='python')"
        )
    
    def _show_max_settings_dialog(self):
        """显示3ds Max设置对话框"""
        messagebox.showinfo(
            "3ds Max 设置",
            "3ds Max 通过 Socket 连接，默认端口 9001\n\n"
            "需要在 3ds Max 中启用 Python 服务器"
        )
    
    def _show_blender_settings_dialog(self):
        """显示Blender设置对话框"""
        messagebox.showinfo(
            "Blender 设置",
            "Blender 通过 Socket 连接，默认端口 8001\n\n"
            "需要安装并启用 Blender 远程执行插件"
        )
    
    def _send_to_ue(self, python_code: str) -> tuple:
        """
        在Unreal Engine中执行Python代码
        
        直接使用文件交换模式（最稳定可靠的方法）
        会等待执行结果并返回UE的输出
        
        Args:
            python_code: 要执行的Python代码
            
        Returns:
            tuple: (success: bool, result: str, output: str)
        """
        import tempfile
        import time
        
        # 脚本交换目录
        script_exchange_dir = Path(tempfile.gettempdir()) / "DCC_UE_Scripts"
        pending_dir = script_exchange_dir / "pending"
        result_dir = script_exchange_dir / "results"
        pending_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = int(time.time() * 1000)
        script_name = f"script_{timestamp}.py"
        script_file = pending_dir / script_name
        result_file = result_dir / f"script_{timestamp}.result.json"
        
        # 清理旧的结果文件（如果存在）
        if result_file.exists():
            try:
                result_file.unlink()
            except:
                pass
        
        try:
            # 保存脚本到pending目录
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            self.log_message(f"脚本已发送，等待UE执行...")
            
            # 等待监听器处理并返回结果（最多等待5秒）
            max_wait = 5.0
            wait_interval = 0.3
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                # 检查脚本是否被处理
                if not script_file.exists():
                    # 脚本已被处理，等待结果文件
                    time.sleep(0.2)  # 额外等待结果写入
                    
                    # 读取结果
                    if result_file.exists():
                        try:
                            with open(result_file, 'r', encoding='utf-8') as f:
                                result_data = json.load(f)
                            
                            success = result_data.get("success", False)
                            output = result_data.get("output", "")
                            error = result_data.get("error", "")
                            
                            # 清理结果文件
                            try:
                                result_file.unlink()
                            except:
                                pass
                            
                            if success:
                                if output:
                                    return True, "✓ UE执行成功", output
                                else:
                                    return True, "✓ UE执行成功（无输出）", ""
                            else:
                                return False, f"✗ UE执行失败: {error}", output
                                
                        except Exception as e:
                            return True, "✓ UE执行完成（结果读取失败）", ""
                    else:
                        return True, "✓ UE执行完成", ""
            
            # 超时检查
            if script_file.exists():
                # 脚本还在，监听器可能未运行
                return True, (
                    "⚠ 脚本已保存，但监听器似乎未运行\n"
                    "请确保UE已启动并配置了监听器"
                ), ""
            else:
                return True, "✓ UE执行完成（等待超时）", ""
                
        except Exception as e:
            return False, f"执行失败: {str(e)}", ""
    
    # ==================== Unreal Engine 连接相关方法结束 ====================
    
    def _send_to_maya(self, python_code: str, receive_output: bool = True) -> tuple:
        """
        发送Python代码到Maya执行并获取返回信息
        
        Args:
            python_code: 要执行的Python代码
            receive_output: 是否接收Maya的输出
            
        Returns:
            tuple: (success: bool, result: str, output: str)
        """
        import socket
        import tempfile
        import time
        
        if not hasattr(self, 'maya_host') or not hasattr(self, 'maya_port'):
            return False, "未连接到Maya", ""
        
        # 创建临时文件用于存储Maya输出
        output_file = Path(tempfile.gettempdir()) / f"dcc_maya_output_{int(time.time())}.txt"
        output_file_str = str(output_file).replace('\\', '/')
        
        try:
            # 创建socket连接
            maya_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            maya_socket.settimeout(30)
            maya_socket.connect((self.maya_host, self.maya_port))
            
            # 包装代码以捕获输出到临时文件
            if receive_output:
                wrapped_code = f'''
import sys
import io

# 捕获stdout到文件
_dcc_output_file = r"{output_file_str}"
_dcc_old_stdout = sys.stdout
_dcc_capture = io.StringIO()
sys.stdout = _dcc_capture

try:
{self._indent_code(python_code, 4)}
except Exception as _dcc_e:
    import traceback
    print("[执行错误]")
    print(f"{{type(_dcc_e).__name__}}: {{_dcc_e}}")
    traceback.print_exc()
finally:
    sys.stdout = _dcc_old_stdout
    _dcc_output = _dcc_capture.getvalue()
    # 写入临时文件
    try:
        with open(_dcc_output_file, 'w', encoding='utf-8') as f:
            f.write(_dcc_output)
    except:
        pass
    # 同时打印到Maya脚本编辑器
    if _dcc_output:
        print(_dcc_output)
'''
                code_to_send = wrapped_code
            else:
                code_to_send = python_code
            
            # 确保代码以换行符结尾
            if not code_to_send.endswith('\n'):
                code_to_send += '\n'
            
            # 发送代码
            maya_socket.sendall(code_to_send.encode('utf-8'))
            maya_socket.close()
            
            # 等待Maya执行完成并读取输出文件
            maya_output = ""
            if receive_output:
                # 等待一段时间让Maya执行
                time.sleep(1.0)
                
                # 尝试读取输出文件
                max_wait = 5  # 最多等待5秒
                for _ in range(max_wait * 2):
                    if output_file.exists():
                        try:
                            maya_output = output_file.read_text(encoding='utf-8')
                            output_file.unlink()  # 删除临时文件
                            break
                        except:
                            pass
                    time.sleep(0.5)
            
            return True, "代码已发送到Maya执行", maya_output
            
        except socket.timeout:
            return False, "Maya响应超时", ""
        except ConnectionRefusedError:
            return False, "Maya连接被拒绝，请检查命令端口是否开启", ""
        except Exception as e:
            return False, f"发送失败: {str(e)}", ""
    
    def _indent_code(self, code: str, spaces: int = 4) -> str:
        """为代码添加缩进"""
        indent = ' ' * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def on_dcc_connected(self, dcc_name, message=""):
        """DCC连接成功回调（不弹窗）"""
        self.connected_dcc = dcc_name
        self.dcc_status_var.set(f"DCC连接: 已连接到 {dcc_name}")
        self.run_in_dcc_btn.configure(state='normal')
        self.log_message(f"✓ {message}", level="success")
    
    def on_dcc_connection_failed(self, error):
        """DCC连接失败回调"""
        self.dcc_status_var.set("DCC连接: 连接失败")
        self.log_message(f"✗ DCC连接失败: {error}", level="error")
        # 连接失败不弹窗，会显示设置对话框
    
    def disconnect_dcc(self):
        """断开DCC连接"""
        if self.connected_dcc:
            # 清除Maya连接信息
            if hasattr(self, 'maya_host'):
                delattr(self, 'maya_host')
            if hasattr(self, 'maya_port'):
                delattr(self, 'maya_port')
            
            self.connected_dcc = None
            self.dcc_status_var.set("DCC连接: 未连接")
            self.run_in_dcc_btn.configure(state='disabled')
            self.log_message("✓ DCC连接已断开")
    
    def _get_selected_tool(self):
        """获取当前选中的工具信息"""
        # 获取当前活动的标签页
        current_tab = self.tools_notebook.index(self.tools_notebook.select())
        category_keys = ['maya', 'max', 'blender', 'ue', 'other']
        
        if current_tab < len(category_keys):
            category_key = category_keys[current_tab]
            tree = getattr(self, f"{category_key}_tree")
            selection = tree.selection()
            
            if selection and hasattr(self, 'tools_cache'):
                tool_id = selection[0]
                return self.tools_cache.get(tool_id)
        
        return None
    
    def run_in_dcc(self):
        """在DCC中执行工具"""
        if not self.connected_dcc:
            messagebox.showwarning("警告", "请先连接到DCC软件")
            return
        
        # 获取当前选中的工具
        current_tool = self._get_selected_tool()
        if not current_tool:
            messagebox.showwarning("警告", "请先选择要执行的工具")
            return
        
        self.log_message(f"正在{self.connected_dcc}中执行工具: {current_tool['name']}...")
        
        # 根据DCC类型执行
        if self.connected_dcc == "Maya":
            self._execute_in_maya(current_tool)
        elif self.connected_dcc == "Unreal Engine":
            self._execute_in_ue(current_tool)
        else:
            messagebox.showinfo("提示", f"{self.connected_dcc}执行功能开发中...")
    
    def run_standalone(self):
        """独立运行工具（不需要连接DCC）"""
        # 获取当前选中的工具
        current_tool = self._get_selected_tool()
        if not current_tool:
            messagebox.showwarning("警告", "请先选择要执行的工具")
            return
        
        # 检查执行模式
        exec_mode = current_tool.get('execution_mode', 'dcc')
        if current_tool.get('type') == 'other':
            exec_mode = current_tool.get('execution_mode', 'standalone')
        
        if exec_mode == 'dcc':
            messagebox.showwarning("警告", "此工具不支持独立运行，请在DCC中执行")
            return
        
        # 在主线程收集参数（避免线程安全问题）
        params = self.collect_parameters()
        
        self.log_message(f"正在独立运行工具: {current_tool['name']}...")
        
        # 在后台线程中执行
        def execute():
            try:
                result = self._execute_standalone(current_tool, params)
                self.root.after(0, lambda: self._on_standalone_success(current_tool['name'], result))
            except Exception as e:
                self.root.after(0, lambda: self._on_standalone_failed(str(e)))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def _execute_standalone(self, tool_info, params):
        """执行独立运行的工具"""
        import importlib.util
        
        # 工具路径已经是绝对路径
        tool_path = Path(tool_info['path'])
        plugin_file = tool_path / "plugin.py"
        
        if not plugin_file.exists():
            raise FileNotFoundError(f"插件文件不存在: {plugin_file}")
        
        # 将参数写入临时文件，避免命令行转义问题
        # Windows 上需要先关闭文件才能让其他进程访问
        params_file_path = tempfile.mktemp(suffix='.json')
        try:
            with open(params_file_path, 'w', encoding='utf-8') as f:
                json.dump(params, f, ensure_ascii=False)
            
            # 构建执行脚本
            runner_code = f'''
import sys
import io
import json

# 设置stdout为UTF-8编码，避免Windows GBK编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, r"{str(self.git_repo_path)}")
sys.path.insert(0, r"{str(tool_path)}")

# 导入并执行工具
import importlib.util
spec = importlib.util.spec_from_file_location("tool_module", r"{str(plugin_file)}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 从临时文件读取参数
with open(r"{params_file_path}", "r", encoding="utf-8") as f:
    params = json.load(f)

# 执行
result = None
if hasattr(module, 'execute'):
    result = module.execute(**params)

# 输出结果为JSON
if result:
    print("__RESULT_START__")
    print(json.dumps(result, ensure_ascii=False, default=str))
    print("__RESULT_END__")
'''
            
            # 使用subprocess执行
            result = subprocess.run(
                [sys.executable, "-c", runner_code],
                capture_output=True,
                timeout=60,
                cwd=str(tool_path),
                encoding='utf-8',
                errors='replace'
            )
            
        finally:
            # 清理临时文件
            try:
                os.unlink(params_file_path)
            except:
                pass
        
        # 解析输出
        output = result.stdout
        stderr = result.stderr
        
        if result.returncode != 0:
            error_detail = f"返回码: {result.returncode}\nstdout: {output}\nstderr: {stderr}"
            raise RuntimeError(f"工具执行失败:\n{error_detail}")
        
        # 提取结果JSON
        parsed_result = {"status": "success", "output": output}
        
        if "__RESULT_START__" in output and "__RESULT_END__" in output:
            try:
                start = output.index("__RESULT_START__") + len("__RESULT_START__")
                end = output.index("__RESULT_END__")
                result_json = output[start:end].strip()
                parsed_result = json.loads(result_json)
            except:
                pass
        
        return parsed_result
    
    def _on_standalone_success(self, tool_name, result):
        """独立执行成功"""
        self.log_message(f"✓ 工具 {tool_name} 独立执行完成")
        
        # 显示结果
        if isinstance(result, dict):
            output = result.get('output', '')
            if output:
                # 显示完整输出（过滤内部标记行）
                lines = output.strip().split('\n')
                max_display = 100  # 最多显示100行
                displayed = 0
                for line in lines:
                    # 跳过内部标记行
                    if line.startswith('__') and line.endswith('__'):
                        continue
                    if displayed < max_display:
                        self.log_message(f"  {line}")
                        displayed += 1
                
                if len(lines) > max_display:
                    self.log_message(f"  ... (共 {len(lines)} 行输出，已显示 {max_display} 行)")
    
    def _on_standalone_failed(self, error):
        """独立执行失败"""
        self.log_message(f"✗ 独立执行失败: {error}", level="error")
        messagebox.showerror("执行失败", f"工具执行失败:\n{error}")
    
    def _execute_in_maya(self, tool_info):
        """在Maya中执行工具"""
        # 收集参数
        params = self.collect_parameters()
        
        # 构建要在Maya中执行的Python代码
        tool_path = self.git_repo_path / tool_info['path']
        plugin_file = tool_path / "plugin.py"
        
        # 生成执行代码
        maya_code = self._generate_maya_execution_code(tool_info, params, plugin_file)
        
        self.log_message(f"发送代码到Maya执行...")
        
        # 在后台线程中发送
        def send_code():
            success, message, maya_output = self._send_to_maya(maya_code)
            if success:
                self.root.after(0, lambda: self._on_maya_execution_success(tool_info['name'], maya_output))
            else:
                self.root.after(0, lambda: self._on_maya_execution_failed(message))
        
        threading.Thread(target=send_code, daemon=True).start()
    
    def _generate_maya_execution_code(self, tool_info, params, plugin_file):
        """
        生成在Maya中执行的Python代码
        
        Args:
            tool_info: 工具信息字典
            params: 参数字典
            plugin_file: 插件文件路径
        
        Returns:
            str: Maya中执行的Python代码
        """
        # 将路径转换为正斜杠（Maya兼容）
        repo_path_str = str(self.git_repo_path).replace('\\', '/')
        plugin_file_str = str(plugin_file).replace('\\', '/')
        
        # 根据工具名称确定类名和执行方式
        tool_name = tool_info['name']
        
        # 生成Maya执行代码
        code = f'''
# === DCC Manager 自动生成代码 ===
import sys
import os

# 添加项目路径
repo_path = r"{repo_path_str}"
if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

# 执行工具: {tool_name}
try:
    # 方式1: 直接执行插件
    plugin_path = r"{plugin_file_str}"
    
    if os.path.exists(plugin_path):
        # 读取并执行插件代码中的类
        import importlib.util
        spec = importlib.util.spec_from_file_location("{tool_name}", plugin_path)
        plugin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin_module)
        
        # 尝试找到并执行插件类
        plugin_class = None
        for name in dir(plugin_module):
            obj = getattr(plugin_module, name)
            if isinstance(obj, type) and hasattr(obj, 'execute'):
                plugin_class = obj
                break
        
        if plugin_class:
            plugin_instance = plugin_class()
            result = plugin_instance.execute(**{params})
            print("=" * 50)
            print("执行结果:")
            print(result)
            print("=" * 50)
        else:
            # 尝试调用 run_in_maya 函数
            if hasattr(plugin_module, 'run_in_maya'):
                result = plugin_module.run_in_maya()
                print("执行结果:", result)
            else:
                print("未找到可执行的插件类或函数")
    else:
        print(f"插件文件不存在: {{plugin_path}}")
        
except Exception as e:
    import traceback
    print("执行失败:")
    print(traceback.format_exc())
'''
        return code
    
    def _on_maya_execution_success(self, tool_name, maya_output=""):
        """Maya执行成功回调（不弹窗，只显示日志）"""
        self.log_message(f"✓ 工具 {tool_name} 已发送到Maya执行", level="success")
        
        # 显示Maya返回的输出信息
        if maya_output and maya_output.strip():
            self.log_message("--- Maya输出 ---", level="debug")
            self.log_maya_output(maya_output)
            self.log_message("--- 输出结束 ---", level="debug")
        else:
            self.log_message("(Maya未返回输出，请查看Maya脚本编辑器)", level="debug")
    
    def _on_maya_execution_failed(self, error):
        """Maya执行失败回调"""
        self.log_message(f"✗ Maya执行失败: {error}", level="error")
        # 失败时显示弹窗提醒用户
        messagebox.showerror("执行失败", f"在Maya中执行失败:\n{error}")
    
    # ==================== Unreal Engine 执行相关方法 ====================
    
    def _execute_in_ue(self, tool_info):
        """在Unreal Engine中执行工具"""
        # 收集参数
        params = self.collect_parameters()
        
        # 构建要在UE中执行的Python代码
        tool_path = self.git_repo_path / tool_info['path']
        plugin_file = tool_path / "plugin.py"
        
        # 生成执行代码
        ue_code = self._generate_ue_execution_code(tool_info, params, plugin_file)
        
        self.log_message(f"发送代码到Unreal Engine执行...")
        
        # 在后台线程中发送
        def send_code():
            success, message, ue_output = self._send_to_ue(ue_code)
            if success:
                self.root.after(0, lambda: self._on_ue_execution_success(tool_info['name'], ue_output))
            else:
                self.root.after(0, lambda: self._on_ue_execution_failed(message, ue_output))
        
        threading.Thread(target=send_code, daemon=True).start()
    
    def _generate_ue_execution_code(self, tool_info, params, plugin_file):
        """
        生成在Unreal Engine中执行的Python代码
        
        Args:
            tool_info: 工具信息字典
            params: 参数字典
            plugin_file: 插件文件路径
        
        Returns:
            str: UE中执行的Python代码
        """
        # 将路径转换为正斜杠（UE兼容）
        repo_path_str = str(self.git_repo_path).replace('\\', '/')
        plugin_file_str = str(plugin_file).replace('\\', '/')
        
        # 根据工具名称确定类名和执行方式
        tool_name = tool_info['name']
        
        # 生成UE执行代码
        code = f'''
# === DCC Manager 自动生成代码 (Unreal Engine) ===
import sys
import os
import unreal

# 添加项目路径
repo_path = r"{repo_path_str}"
if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

# 执行工具: {tool_name}
try:
    # 直接执行插件
    plugin_path = r"{plugin_file_str}"
    
    if os.path.exists(plugin_path):
        # 读取并执行插件代码中的类
        import importlib.util
        spec = importlib.util.spec_from_file_location("{tool_name}", plugin_path)
        plugin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin_module)
        
        # 尝试找到并执行插件类
        plugin_class = None
        for name in dir(plugin_module):
            obj = getattr(plugin_module, name)
            if isinstance(obj, type) and hasattr(obj, 'execute'):
                plugin_class = obj
                break
        
        if plugin_class:
            plugin_instance = plugin_class()
            result = plugin_instance.execute(**{params})
            unreal.log("=" * 50)
            unreal.log("执行结果:")
            unreal.log(str(result))
            unreal.log("=" * 50)
        else:
            # 尝试调用 run_in_unreal 函数
            if hasattr(plugin_module, 'run_in_unreal'):
                result = plugin_module.run_in_unreal()
                unreal.log(f"执行结果: {{result}}")
            else:
                unreal.log_warning("未找到可执行的插件类或函数")
    else:
        unreal.log_error(f"插件文件不存在: {{plugin_path}}")
        
except Exception as e:
    import traceback
    unreal.log_error("执行失败:")
    unreal.log_error(traceback.format_exc())
'''
        return code
    
    def _on_ue_execution_success(self, tool_name, ue_output=""):
        """UE执行成功回调"""
        
        self.log_message(f"✓ 工具 {tool_name} 已在UE中执行", level="success")
        
        # 显示UE返回的输出
        if ue_output and ue_output.strip():
            self.log_message("--- UE 输出 ---", level="debug")
            # 按行显示输出，避免单行过长
            for line in ue_output.strip().split('\n'):
                if line.strip():
                    self.log_message(f"  {line}", level="debug")
            self.log_message("--- 输出结束 ---", level="debug")
        else:
            self.log_message("(执行完成，无输出)", level="debug")
    
    def _on_ue_execution_failed(self, error, ue_output=""):
        """UE执行失败回调"""
        self.log_message(f"✗ UE执行失败: {error}", level="error")
        
        # 显示UE返回的输出（可能包含调试信息）
        if ue_output and ue_output.strip():
            self.log_message("--- UE 输出/调试信息 ---", level="debug")
            for line in ue_output.strip().split('\n'):
                if line.strip():
                    self.log_message(f"  {line}", level="debug")
            self.log_message("--- 输出结束 ---", level="debug")
        
        # 失败时显示弹窗提醒用户
        messagebox.showerror("执行失败", f"在Unreal Engine中执行失败:\n{error}")
    
    # ==================== Unreal Engine 执行相关方法结束 ====================
    
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
    
    def log_message(self, message, level="info"):
        """
        记录日志消息（支持颜色）
        
        Args:
            message: 日志消息
            level: 日志级别 - "info"(默认), "success", "warning", "error", "debug", "maya"
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 确保log_text有颜色标签配置
        self._setup_log_tags()
        
        # 根据消息内容自动判断级别
        if level == "info":
            if message.startswith("✓") or "成功" in message or "完成" in message:
                level = "success"
            elif message.startswith("✗") or "失败" in message or "错误" in message:
                level = "error"
            elif message.startswith("⚠") or "警告" in message:
                level = "warning"
            elif "[Maya]" in message or "[DCC]" in message:
                level = "maya"
        
        # 插入带颜色的日志
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        
        # 限制日志长度
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 300:  # 保留最多300行
            self.log_text.delete(1.0, f"{len(lines)-299}.0")
    
    # ===== 分组筛选和搜索功能 =====
    
    def _on_group_change(self, category_key):
        """分组下拉框变化时的回调"""
        self._filter_tools(category_key)
    
    def _on_search_change(self, category_key):
        """搜索框变化时的回调（带防抖）"""
        # 取消之前的定时器
        if category_key in self._search_after_ids:
            self.root.after_cancel(self._search_after_ids[category_key])
        
        # 设置新的定时器（300ms延迟）
        self._search_after_ids[category_key] = self.root.after(
            300, lambda: self._filter_tools(category_key)
        )
    
    def _filter_tools(self, category_key):
        """根据分组和搜索条件筛选工具列表"""
        tree = getattr(self, f"{category_key}_tree", None)
        if not tree:
            return
        
        # 获取筛选条件
        group_combo = self.group_combos.get(category_key)
        search_var = self.search_vars.get(category_key)
        
        selected_group = "all"
        if group_combo:
            group_text = group_combo.get()
            # 从 "📋 全部" 格式中提取分组ID
            for g in self.tool_groups.get("groups", []):
                if f"{g['icon']} {g['name']}" == group_text:
                    selected_group = g["id"]
                    break
        
        search_text = search_var.get().lower().strip() if search_var else ""
        
        # 清空当前列表
        for item in tree.get_children():
            tree.delete(item)
        
        # 根据分类筛选工具
        if not hasattr(self, 'tools_cache'):
            return
        
        for tool_id, tool_info in self.tools_cache.items():
            # 检查工具是否属于当前分类
            tool_type = tool_info.get('type', '')
            target_dcc = tool_info.get('target_dcc', '').lower()
            
            # 根据category_key判断
            if category_key == 'maya' and target_dcc not in ['maya', 'autodesk_maya']:
                if tool_type != 'dcc' or 'maya' not in tool_id.lower():
                    continue
            elif category_key == 'max' and target_dcc not in ['3ds_max', '3dsmax', 'max']:
                if tool_type != 'dcc' or 'max' not in tool_id.lower():
                    continue
            elif category_key == 'blender' and target_dcc not in ['blender']:
                if tool_type != 'dcc' or 'blender' not in tool_id.lower():
                    continue
            elif category_key == 'ue' and target_dcc not in ['unreal', 'ue', 'unreal_engine']:
                if tool_type != 'ue_engine' or 'ue' not in tool_id.lower():
                    continue
            elif category_key == 'other' and tool_type != 'other':
                continue
            
            # 检查分组筛选
            if selected_group != "all":
                tool_groups_list = self.get_tool_groups(tool_id)
                if selected_group not in tool_groups_list:
                    continue
            
            # 检查搜索筛选
            if search_text:
                name = tool_info.get('name', '').lower()
                desc = tool_info.get('description', '').lower()
                if search_text not in name and search_text not in desc:
                    continue
            
            # 添加到列表
            source = "本地" if tool_info.get('is_local') else "共享"
            
            # 获取执行模式显示
            exec_mode = tool_info.get('execution_mode', 'dcc')
            if tool_info.get('type') == 'other':
                exec_mode = tool_info.get('execution_mode', 'standalone')
            mode_display = {'dcc': 'DCC', 'standalone': '独立', 'both': '两者'}.get(exec_mode, '')
            
            tree.insert('', tk.END, iid=tool_id, text=tool_info['name'],
                       values=(tool_info['version'], source, mode_display))
    
    def _show_tool_context_menu(self, event, category_key):
        """显示工具右键菜单"""
        tree = getattr(self, f"{category_key}_tree", None)
        if not tree:
            return
        
        # 选中点击的项
        item = tree.identify_row(event.y)
        if not item:
            return
        tree.selection_set(item)
        
        # 获取工具信息
        if not hasattr(self, 'tools_cache') or item not in self.tools_cache:
            return
        
        tool_info = self.tools_cache[item]
        
        # 创建菜单
        menu = tk.Menu(self.root, tearoff=0)
        
        # 执行选项
        exec_mode = tool_info.get('execution_mode', 'dcc')
        if tool_info.get('type') == 'other':
            exec_mode = tool_info.get('execution_mode', 'standalone')
        
        if exec_mode in ['dcc', 'both']:
            menu.add_command(label="▶️ 在DCC中执行", command=self.run_in_dcc)
        if exec_mode in ['standalone', 'both']:
            menu.add_command(label="🖥️ 独立运行", command=self.run_standalone)
        
        menu.add_separator()
        
        # 分组设置子菜单
        group_menu = tk.Menu(menu, tearoff=0)
        current_groups = self.get_tool_groups(item)
        
        for g in self.tool_groups.get("groups", []):
            if g["id"] == "all":
                continue
            is_checked = g["id"] in current_groups
            group_menu.add_checkbutton(
                label=f"{g['icon']} {g['name']}",
                command=lambda gid=g["id"], tid=item: self._toggle_tool_group(tid, gid),
                variable=tk.BooleanVar(value=is_checked)
            )
        
        menu.add_cascade(label="📂 设置分组", menu=group_menu)
        
        menu.add_separator()
        menu.add_command(label="📋 复制路径", 
                        command=lambda: self.root.clipboard_append(tool_info.get('path', '')))
        menu.add_command(label="📁 打开所在文件夹", 
                        command=lambda: self._open_tool_folder(tool_info))
        
        # 显示菜单
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _toggle_tool_group(self, tool_id, group_id):
        """切换工具的分组"""
        if "tool_assignments" not in self.tool_groups:
            self.tool_groups["tool_assignments"] = {}
        
        current = self.tool_groups["tool_assignments"].get(tool_id, [])
        
        # 如果没有自定义分配，从工具的tags获取
        if not current and hasattr(self, 'tools_cache') and tool_id in self.tools_cache:
            current = list(self.tools_cache[tool_id].get('tags', []))
        
        if group_id in current:
            current.remove(group_id)
        else:
            current.append(group_id)
        
        self.tool_groups["tool_assignments"][tool_id] = current
        self._save_tool_groups_local()
        
        self.log_message(f"✓ 工具分组已更新")
    
    def _open_tool_folder(self, tool_info):
        """打开工具所在文件夹"""
        tool_path = Path(tool_info.get('path', ''))
        if tool_path.exists():
            if sys.platform == 'win32':
                os.startfile(tool_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(tool_path)])
            else:
                subprocess.run(['xdg-open', str(tool_path)])
    
    def _show_group_manager(self):
        """显示分组管理对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("分组管理")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 450) // 2
        dialog.geometry(f"400x450+{x}+{y}")
        
        # 标题
        ttk.Label(dialog, text="分组管理", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # 分组列表
        list_frame = ttk.LabelFrame(dialog, text="现有分组", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        listbox = tk.Listbox(list_frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)
        
        for g in self.tool_groups.get("groups", []):
            suffix = " (自定义)" if g.get("is_custom") else ""
            listbox.insert(tk.END, f"{g['icon']} {g['name']}{suffix}")
        
        # 添加分组区域
        add_frame = ttk.LabelFrame(dialog, text="添加自定义分组", padding="10")
        add_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(add_frame, text="名称:").grid(row=0, column=0, sticky=tk.W)
        name_entry = ttk.Entry(add_frame, width=20)
        name_entry.grid(row=0, column=1, padx=5, columnspan=2)
        
        ttk.Label(add_frame, text="图标:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # 图标选择区域
        icon_var = tk.StringVar(value="📁")
        icon_display = ttk.Label(add_frame, textvariable=icon_var, font=('', 16), width=3)
        icon_display.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # 可选图标列表
        available_icons = [
            "📁", "📂", "🎨", "🎬", "🔧", "⚙️", "🛠️", "📐",
            "🎮", "🎯", "💡", "⭐", "🔥", "💎", "🎪", "🎭",
            "📊", "📈", "🗂️", "📋", "✨", "🌟", "💫", "🚀",
            "🔨", "🔩", "⚡", "🎵", "🎶", "🖼️", "🖌️", "✏️"
        ]
        
        def show_icon_picker():
            """显示图标选择器"""
            picker = tk.Toplevel(dialog)
            picker.title("选择图标")
            picker.geometry("300x200")
            picker.transient(dialog)
            picker.grab_set()
            
            # 居中显示
            picker.update_idletasks()
            px = dialog.winfo_x() + (dialog.winfo_width() - 300) // 2
            py = dialog.winfo_y() + (dialog.winfo_height() - 200) // 2
            picker.geometry(f"+{px}+{py}")
            
            ttk.Label(picker, text="点击选择图标:").pack(pady=5)
            
            # 图标网格
            icons_frame = ttk.Frame(picker)
            icons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            row, col = 0, 0
            max_cols = 8
            
            for icon in available_icons:
                btn = tk.Button(
                    icons_frame, 
                    text=icon, 
                    font=('', 14),
                    width=2,
                    relief=tk.FLAT,
                    command=lambda i=icon: [icon_var.set(i), picker.destroy()]
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            ttk.Button(picker, text="取消", command=picker.destroy).pack(pady=5)
        
        ttk.Button(add_frame, text="选择...", width=6, command=show_icon_picker).grid(row=1, column=2, padx=5)
        
        def add_group():
            name = name_entry.get().strip()
            icon = icon_var.get() or "📁"
            
            if not name:
                messagebox.showwarning("提示", "请输入分组名称")
                return
            
            new_group = {"id": name.lower().replace(" ", "_"), "name": name, "icon": icon, "is_custom": True}
            self.tool_groups["groups"].append(new_group)
            self._save_tool_groups_local()
            
            # 更新列表
            listbox.insert(tk.END, f"{icon} {name} (自定义)")
            name_entry.delete(0, tk.END)
            icon_var.set("📁")
            
            # 更新所有下拉框
            self._update_all_group_comboboxes()
            
            self.log_message(f"✓ 已添加自定义分组: {name}")
        
        ttk.Button(add_frame, text="添加", command=add_group).grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # 关闭按钮
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def _update_all_group_comboboxes(self):
        """更新所有分组下拉框的选项"""
        group_values = [f"{g['icon']} {g['name']}" for g in self.tool_groups.get("groups", [])]
        for combo in self.group_combos.values():
            current = combo.get()
            combo['values'] = group_values
            if current in group_values:
                combo.set(current)
    
    def _setup_log_tags(self):
        """设置日志文本的颜色标签"""
        if hasattr(self, '_log_tags_configured'):
            return
        
        # 配置不同级别的颜色
        self.log_text.tag_configure("info", foreground="#333333")
        self.log_text.tag_configure("success", foreground="#28a745")  # 绿色
        self.log_text.tag_configure("warning", foreground="#ffc107", background="#fff8e1")  # 黄色
        self.log_text.tag_configure("error", foreground="#dc3545")  # 红色
        self.log_text.tag_configure("debug", foreground="#6c757d")  # 灰色
        self.log_text.tag_configure("maya", foreground="#0066cc")  # 蓝色 - Maya返回信息
        
        self._log_tags_configured = True
    
    def log_maya_output(self, output: str):
        """
        记录Maya输出信息（蓝色显示）
        
        Args:
            output: Maya返回的输出信息
        """
        if output and output.strip():
            for line in output.strip().split('\n'):
                if line.strip():
                    self.log_message(f"[Maya] {line.strip()}", level="maya")

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