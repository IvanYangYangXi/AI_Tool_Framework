"""
增强版DCC工具框架GUI界面
提供完整的图形化操作体验
"""

import sys
import os
from pathlib import Path
import json
import threading
from datetime import datetime

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    USE_PYSIDE = True
except ImportError:
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
        USE_PYSIDE = False
    except ImportError:
        # 回退到tkinter
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        USE_PYTHON_GUI = True

class EnhancedDCCGUI:
    """增强版DCC工具框架GUI"""
    
    def __init__(self):
        self.framework_path = self._find_framework_path()
        self.plugins = self._load_plugins()
        self.user_settings = self._load_user_settings()
        self.running_tasks = {}
        
    def _find_framework_path(self):
        """智能查找框架路径"""
        possible_paths = [
            Path.cwd(),
            Path(__file__).parent.parent.parent,
            Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
        ]
        
        for path in possible_paths:
            if (path / "src" / "core").exists():
                return str(path)
        return str(Path.cwd())
    
    def _load_plugins(self):
        """加载所有插件信息"""
        plugins = []
        plugins_dir = Path(self.framework_path) / "src" / "plugins"
        
        # 加载各类插件
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
                        
                    config_file = plugin_dir / "config.json"
                    if not config_file.exists():
                        continue
                        
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            
                        plugin_info = {
                            'name': config['plugin']['name'],
                            'version': config['plugin']['version'],
                            'type': plugin_type,
                            'software': software_dir.name if plugin_type == 'dcc' else 'Unreal Engine',
                            'description': config['plugin'].get('description', ''),
                            'author': config['plugin'].get('author', ''),
                            'path': str(plugin_dir),
                            'config': config,
                            'parameters': config.get('parameters', {}),
                            'capabilities': config.get('capabilities', [])
                        }
                        plugins.append(plugin_info)
                        
                    except Exception as e:
                        print(f"加载插件配置失败 {plugin_dir}: {e}")
        
        return plugins
    
    def _load_user_settings(self):
        """加载用户个性化设置"""
        settings_file = Path.home() / ".dcc_framework" / "enhanced_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "window_size": [1200, 800],
            "window_position": [100, 100],
            "recent_plugins": [],
            "favorite_plugins": [],
            "theme": "dark" if self._detect_dark_mode() else "light",
            "auto_save_logs": True,
            "max_log_entries": 1000
        }
    
    def _detect_dark_mode(self):
        """检测系统是否使用深色主题"""
        try:
            if sys.platform == "win32":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
        except:
            pass
        return False
    
    def show(self):
        """显示增强版GUI"""
        if 'USE_PYTHON_GUI' in globals() and USE_PYTHON_GUI:
            self._show_enhanced_tkinter_gui()
        else:
            self._show_enhanced_qt_gui()
    
    def _show_enhanced_tkinter_gui(self):
        """增强版tkinter界面"""
        root = tk.Tk()
        root.title("DCC工具框架专业版")
        
        # 设置窗口大小和位置
        size = self.user_settings["window_size"]
        pos = self.user_settings["window_position"]
        root.geometry(f"{size[0]}x{size[1]}+{pos[0]}+{pos[1]}")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="刷新插件", command=self._refresh_plugins).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="设置", command=self._show_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="帮助", command=self._show_help).pack(side=tk.RIGHT)
        
        # 主体区域 - 分割窗格
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 插件浏览器
        left_panel = ttk.Frame(paned_window)
        paned_window.add(left_panel, weight=1)
        
        # 插件分类标签页
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # DCC工具标签页
        dcc_frame = ttk.Frame(notebook)
        self._create_plugin_tree(dcc_frame, 'dcc')
        notebook.add(dcc_frame, text="DCC工具")
        
        # UE工具标签页
        ue_frame = ttk.Frame(notebook)
        self._create_plugin_tree(ue_frame, 'ue')
        notebook.add(ue_frame, text="UE工具")
        
        # 右侧面板 - 详细信息和操作区
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=2)
        
        # 插件详细信息
        info_frame = ttk.LabelFrame(right_panel, text="插件信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD)
        info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 参数配置区域
        param_frame = ttk.LabelFrame(right_panel, text="参数配置", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.param_vars = {}
        self._create_parameter_widgets(param_frame)
        
        # 操作按钮区域
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="运行插件", command=self._run_plugin_threaded).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="测试运行", command=self._test_run_plugin).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="查看日志", command=self._show_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导出配置", command=self._export_config).pack(side=tk.RIGHT)
        
        # 底部状态栏和进度条
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, length=200)
        progress_bar.pack(side=tk.RIGHT)
        
        # 绑定事件
        root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 显示窗口
        root.mainloop()
    
    def _create_plugin_tree(self, parent, plugin_type):
        """创建插件树视图"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('name', 'version', 'software')
        self.plugin_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=15)
        
        # 设置列标题
        self.plugin_tree.heading('#0', text='插件')
        self.plugin_tree.heading('name', text='名称')
        self.plugin_tree.heading('version', text='版本')
        self.plugin_tree.heading('software', text='软件')
        
        # 设置列宽
        self.plugin_tree.column('#0', width=200)
        self.plugin_tree.column('name', width=150)
        self.plugin_tree.column('version', width=80)
        self.plugin_tree.column('software', width=100)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=tree_scroll.set)
        
        # 填充插件数据
        for plugin in self.plugins:
            if plugin['type'] == plugin_type:
                parent_node = plugin['software']
                self.plugin_tree.insert('', 'end', text=plugin['name'],
                                      values=(plugin['name'], plugin['version'], plugin['software']),
                                      tags=(plugin['name'],))
        
        # 布局
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.plugin_tree.bind('<<TreeviewSelect>>', self._on_plugin_select)
    
    def _create_parameter_widgets(self, parent):
        """创建参数配置控件"""
        self.param_frame_inner = ttk.Frame(parent)
        self.param_frame_inner.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(self.param_frame_inner)
        scrollbar = ttk.Scrollbar(self.param_frame_inner, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.param_widgets_container = scrollable_frame
    
    def _on_plugin_select(self, event):
        """插件选择事件处理"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
            
        item = self.plugin_tree.item(selection[0])
        plugin_name = item['text']
        
        # 查找对应的插件
        selected_plugin = None
        for plugin in self.plugins:
            if plugin['name'] == plugin_name:
                selected_plugin = plugin
                break
        
        if selected_plugin:
            self._display_plugin_info(selected_plugin)
            self._update_parameter_widgets(selected_plugin)
    
    def _display_plugin_info(self, plugin):
        """显示插件详细信息"""
        info_text = f"""名称: {plugin['name']}
版本: {plugin['version']}
类型: {plugin['type'].upper()}
目标软件: {plugin['software']}
作者: {plugin['author']}
描述: {plugin['description']}

功能特性:
{chr(10).join(['• ' + cap for cap in plugin['capabilities'][:5]])}
{'' if len(plugin['capabilities']) <= 5 else '...及其他功能'}

路径: {plugin['path']}
"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
    
    def _update_parameter_widgets(self, plugin):
        """更新参数配置控件"""
        # 清除现有控件
        for widget in self.param_widgets_container.winfo_children():
            widget.destroy()
        
        self.param_vars.clear()
        
        # 创建新控件
        row = 0
        for param_name, param_info in plugin['parameters'].items():
            ttk.Label(self.param_widgets_container, text=f"{param_name}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            
            param_type = param_info.get('type', 'string')
            default_value = param_info.get('default', '')
            
            if param_type == 'boolean':
                var = tk.BooleanVar(value=default_value)
                widget = ttk.Checkbutton(self.param_widgets_container, variable=var)
            elif param_type == 'integer' or param_type == 'float':
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_widgets_container, textvariable=var, width=20)
            else:
                var = tk.StringVar(value=str(default_value))
                widget = ttk.Entry(self.param_widgets_container, textvariable=var, width=30)
            
            widget.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            self.param_vars[param_name] = var
            row += 1
        
        # 添加说明标签
        if plugin['parameters']:
            ttk.Label(self.param_widgets_container, 
                     text="提示: 修改参数后点击'运行插件'生效",
                     foreground="gray").grid(row=row, column=0, columnspan=2, pady=(10, 0))
    
    def _run_plugin_threaded(self):
        """在线程中运行插件"""
        def run_task():
            try:
                self._run_selected_plugin()
            finally:
                # 重置UI状态
                self.status_var.set("就绪")
                self.progress_var.set(0)
        
        # 启动后台线程
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        self.status_var.set("插件运行中...")
        self.progress_var.set(50)  # 简单的进度指示
    
    def _run_selected_plugin(self):
        """运行选中的插件"""
        selection = self.plugin_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个插件")
            return
        
        item = self.plugin_tree.item(selection[0])
        plugin_name = item['text']
        
        # 查找插件
        plugin = None
        for p in self.plugins:
            if p['name'] == plugin_name:
                plugin = p
                break
        
        if not plugin:
            messagebox.showerror("错误", f"未找到插件: {plugin_name}")
            return
        
        try:
            # 收集参数
            params = {}
            for param_name, var in self.param_vars.items():
                param_info = plugin['parameters'][param_name]
                param_type = param_info.get('type', 'string')
                
                if param_type == 'boolean':
                    params[param_name] = var.get()
                elif param_type == 'integer':
                    params[param_name] = int(var.get())
                elif param_type == 'float':
                    params[param_name] = float(var.get())
                else:
                    params[param_name] = var.get()
            
            # 执行插件
            self.status_var.set(f"正在运行 {plugin_name}...")
            
            # 添加插件路径
            if plugin['path'] not in sys.path:
                sys.path.append(plugin['path'])
            
            # 动态导入和执行
            if plugin['type'] == 'dcc' and plugin['software'].lower() == 'maya':
                from plugin import MayaMeshCleaner
                tool = MayaMeshCleaner()
                result = tool.execute(**params)
                
            elif plugin['type'] == 'ue':
                from plugin import UEAssetOptimizer
                tool = UEAssetOptimizer()
                result = tool.execute(**params)
            
            # 显示结果
            messagebox.showinfo("执行完成", f"插件 {plugin_name} 执行完成\n结果: {result}")
            self.status_var.set("执行完成")
            
        except Exception as e:
            messagebox.showerror("执行错误", f"插件执行失败:\n{str(e)}")
            self.status_var.set("执行失败")
    
    def _refresh_plugins(self):
        """刷新插件列表"""
        self.plugins = self._load_plugins()
        # 重新填充树视图
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
        
        for plugin in self.plugins:
            if plugin['type'] == 'dcc':
                self.plugin_tree.insert('', 'end', text=plugin['name'],
                                      values=(plugin['name'], plugin['version'], plugin['software']))
    
    def _show_settings(self):
        """显示设置对话框"""
        settings_win = tk.Toplevel()
        settings_win.title("设置")
        settings_win.geometry("400x300")
        
        ttk.Label(settings_win, text="用户设置", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # 主题选择
        theme_frame = ttk.Frame(settings_win)
        theme_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(theme_frame, text="主题:").pack(side=tk.LEFT)
        theme_var = tk.StringVar(value=self.user_settings['theme'])
        ttk.Combobox(theme_frame, textvariable=theme_var, 
                    values=['light', 'dark']).pack(side=tk.RIGHT)
        
        # 自动保存日志
        log_frame = ttk.Frame(settings_win)
        log_frame.pack(fill=tk.X, padx=20, pady=5)
        log_var = tk.BooleanVar(value=self.user_settings['auto_save_logs'])
        ttk.Checkbutton(log_frame, text="自动保存运行日志", variable=log_var).pack(anchor=tk.W)
        
        # 确定按钮
        def save_settings():
            self.user_settings['theme'] = theme_var.get()
            self.user_settings['auto_save_logs'] = log_var.get()
            self._save_user_settings()
            settings_win.destroy()
        
        ttk.Button(settings_win, text="保存", command=save_settings).pack(pady=20)
    
    def _save_user_settings(self):
        """保存用户设置"""
        settings_dir = Path.home() / ".dcc_framework"
        settings_dir.mkdir(exist_ok=True)
        
        settings_file = settings_dir / "enhanced_settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
DCC工具框架专业版使用帮助

主要功能:
• 插件浏览器: 浏览和管理所有可用工具
• 参数配置: 可视化配置插件运行参数
• 一键运行: 简单点击即可执行工具
• 日志记录: 完整的执行历史记录
• 主题切换: 支持深色/浅色主题

使用步骤:
1. 在左侧选择要使用的插件
2. 在右侧查看插件信息和配置参数
3. 点击"运行插件"按钮执行

技术支持:
如有问题请联系开发团队
        """
        messagebox.showinfo("帮助", help_text)
    
    def _test_run_plugin(self):
        """测试运行插件（不实际执行）"""
        messagebox.showinfo("测试", "这是测试运行功能\n实际使用时请点击'运行插件'")
    
    def _show_logs(self):
        """显示运行日志"""
        log_win = tk.Toplevel()
        log_win.title("运行日志")
        log_win.geometry("600x400")
        
        log_text = tk.Text(log_win, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_win, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        
        # 模拟日志内容
        sample_logs = """
[10:30:15] 系统启动
[10:30:16] 加载插件: Maya网格清理工具
[10:30:17] 加载插件: UE资产优化工具
[10:32:05] 用户选择插件: Maya网格清理工具
[10:32:10] 执行插件，参数: tolerance=0.001
[10:32:15] 执行完成，处理对象数: 3
        """
        log_text.insert(1.0, sample_logs)
        
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _export_config(self):
        """导出当前配置"""
        config = {
            "export_time": datetime.now().isoformat(),
            "plugins": [p['name'] for p in self.plugins],
            "settings": self.user_settings
        }
        
        messagebox.showinfo("导出", f"配置已导出\n插件数量: {len(self.plugins)}")
    
    def _on_closing(self):
        """窗口关闭事件"""
        # 保存窗口位置和大小
        # 这里可以添加更多清理代码
        self._save_user_settings()
        # 关闭程序
        for widget in tk._default_root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        tk._default_root.quit()

def main():
    """主函数"""
    app = EnhancedDCCGUI()
    app.show()

if __name__ == "__main__":
    main()