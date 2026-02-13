"""
DCC工具框架统一GUI界面
为DCC艺术家提供友好的图形操作界面
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    USE_PYSIDE = True
except ImportError:
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
        USE_PYSIDE = False
    except ImportError:
        # 如果都没有，使用基本的tkinter界面
        import tkinter as tk
        from tkinter import ttk, messagebox
        USE_PYTHON_GUI = True

class DCCFrameworkGUI:
    """DCC工具框架主界面"""
    
    def __init__(self):
        self.app = None
        self.window = None
        self.framework_path = self._find_framework_path()
        self.plugins = self._load_plugins()
        self.user_settings = self._load_user_settings()
        
    def _find_framework_path(self):
        """寻找框架路径"""
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
        """加载所有可用插件"""
        plugins = []
        plugins_dir = Path(self.framework_path) / "src" / "plugins"
        
        # 加载DCC插件
        dcc_dir = plugins_dir / "dcc"
        if dcc_dir.exists():
            for software_dir in dcc_dir.iterdir():
                if software_dir.is_dir():
                    for plugin_dir in software_dir.iterdir():
                        if plugin_dir.is_dir():
                            config_file = plugin_dir / "config.json"
                            if config_file.exists():
                                try:
                                    with open(config_file, 'r', encoding='utf-8') as f:
                                        config = json.load(f)
                                        plugins.append({
                                            'name': config['plugin']['name'],
                                            'type': 'dcc',
                                            'software': software_dir.name,
                                            'path': str(plugin_dir),
                                            'config': config
                                        })
                                except Exception as e:
                                    print(f"加载插件配置失败 {plugin_dir}: {e}")
        
        # 加载UE插件
        ue_dir = plugins_dir / "ue"
        if ue_dir.exists():
            for plugin_dir in ue_dir.iterdir():
                if plugin_dir.is_dir():
                    config_file = plugin_dir / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                                plugins.append({
                                    'name': config['plugin']['name'],
                                    'type': 'ue',
                                    'path': str(plugin_dir),
                                    'config': config
                                })
                        except Exception as e:
                            print(f"加载UE插件配置失败 {plugin_dir}: {e}")
        
        return plugins
    
    def _load_user_settings(self):
        """加载用户设置"""
        settings_file = Path.home() / ".dcc_framework" / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认设置
        return {
            "recent_plugins": [],
            "favorite_plugins": [],
            "window_geometry": [100, 100, 800, 600],
            "theme": "default"
        }
    
    def _save_user_settings(self):
        """保存用户设置"""
        settings_dir = Path.home() / ".dcc_framework"
        settings_dir.mkdir(exist_ok=True)
        
        settings_file = settings_dir / "settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def show(self):
        """显示主界面"""
        if USE_PYTHON_GUI:
            self._show_tkinter_gui()
        else:
            self._show_qt_gui()
    
    def _show_tkinter_gui(self):
        """使用tkinter显示界面"""
        root = tk.Tk()
        root.title("DCC工具框架")
        root.geometry("800x600")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="DCC工具框架", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左侧插件列表
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        ttk.Label(left_frame, text="可用工具", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        
        # 创建插件列表框
        plugin_listbox = tk.Listbox(left_frame, width=30, height=20)
        plugin_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=plugin_listbox.yview)
        plugin_listbox.configure(yscrollcommand=plugin_scrollbar.set)
        
        # 添加插件到列表
        for plugin in self.plugins:
            plugin_listbox.insert(tk.END, f"{plugin['name']} ({plugin.get('software', 'UE')})")
        
        plugin_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plugin_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧详细信息和操作区域
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 插件详细信息
        info_frame = ttk.LabelFrame(right_frame, text="插件信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=8, wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作按钮
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="运行插件", command=self._run_selected_plugin).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="查看文档", command=self._show_documentation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="设置参数", command=self._configure_plugin).pack(side=tk.LEFT)
        
        # 绑定选择事件
        plugin_listbox.bind('<<ListboxSelect>>', self._on_plugin_select)
        
        # 底部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 显示窗口
        root.mainloop()
    
    def _show_qt_gui(self):
        """使用PyQt/PySide显示界面"""
        if USE_PYSIDE:
            from PySide2.QtWidgets import QApplication
        else:
            from PyQt5.QtWidgets import QApplication
        
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # 创建主窗口
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle("DCC工具框架")
        self.window.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.window.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        
        # 左侧插件树
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # 插件分类树
        self.plugin_tree = QtWidgets.QTreeWidget()
        self.plugin_tree.setHeaderLabels(["插件名称", "类型"])
        self.plugin_tree.setMinimumWidth(250)
        
        # 填充插件树
        self._populate_plugin_tree()
        
        left_layout.addWidget(QtWidgets.QLabel("可用工具"))
        left_layout.addWidget(self.plugin_tree)
        
        # 右侧面板
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # 插件信息显示
        self.info_display = QtWidgets.QTextEdit()
        self.info_display.setMaximumHeight(150)
        
        # 参数配置区域
        self.param_widget = QtWidgets.QWidget()
        param_layout = QtWidgets.QFormLayout(self.param_widget)
        
        # 操作按钮
        button_layout = QtWidgets.QHBoxLayout()
        run_button = QtWidgets.QPushButton("运行插件")
        doc_button = QtWidgets.QPushButton("查看文档")
        config_button = QtWidgets.QPushButton("设置参数")
        
        run_button.clicked.connect(self._run_selected_plugin)
        doc_button.clicked.connect(self._show_documentation)
        config_button.clicked.connect(self._configure_plugin)
        
        button_layout.addWidget(run_button)
        button_layout.addWidget(doc_button)
        button_layout.addWidget(config_button)
        button_layout.addStretch()
        
        # 日志显示区域
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        
        # 添加到右侧面板
        right_layout.addWidget(QtWidgets.QLabel("插件信息"))
        right_layout.addWidget(self.info_display)
        right_layout.addWidget(QtWidgets.QLabel("参数配置"))
        right_layout.addWidget(self.param_widget)
        right_layout.addLayout(button_layout)
        right_layout.addWidget(QtWidgets.QLabel("运行日志"))
        right_layout.addWidget(self.log_display)
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        main_layout.setStretch(1, 1)
        
        # 连接信号
        self.plugin_tree.itemSelectionChanged.connect(self._on_plugin_select)
        
        # 显示窗口
        self.window.show()
        self.app.exec_()
    
    def _populate_plugin_tree(self):
        """填充插件树"""
        # 按类型分组
        dcc_plugins = [p for p in self.plugins if p['type'] == 'dcc']
        ue_plugins = [p for p in self.plugins if p['type'] == 'ue']
        
        # 创建DCC分支
        dcc_item = QtWidgets.QTreeWidgetItem(self.plugin_tree, ["DCC工具"])
        for plugin in dcc_plugins:
            item = QtWidgets.QTreeWidgetItem(dcc_item, [plugin['name'], plugin.get('software', '').upper()])
            item.setData(0, QtCore.Qt.UserRole, plugin)
        
        # 创建UE分支
        ue_item = QtWidgets.QTreeWidgetItem(self.plugin_tree, ["UE工具"])
        for plugin in ue_plugins:
            item = QtWidgets.QTreeWidgetItem(ue_item, [plugin['name'], "UNREAL"])
            item.setData(0, QtCore.Qt.UserRole, plugin)
    
    def _on_plugin_select(self, event=None):
        """插件选择事件"""
        if USE_PYTHON_GUI:
            selection = event.widget.curselection()
            if selection:
                plugin = self.plugins[selection[0]]
                self._display_plugin_info(plugin)
        else:
            selected_items = self.plugin_tree.selectedItems()
            if selected_items:
                plugin = selected_items[0].data(0, QtCore.Qt.UserRole)
                if plugin:
                    self._display_plugin_info(plugin)
    
    def _display_plugin_info(self, plugin):
        """显示插件信息"""
        info_text = f"""名称: {plugin['name']}
类型: {plugin['type'].upper()}
软件: {plugin.get('software', 'Unreal Engine')}
版本: {plugin['config']['plugin']['version']}
描述: {plugin['config']['plugin']['description']}
作者: {plugin['config']['plugin']['author']}
路径: {plugin['path']}"""
        
        if USE_PYTHON_GUI:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
        else:
            self.info_display.setText(info_text)
    
    def _run_selected_plugin(self):
        """运行选中的插件"""
        try:
            if USE_PYTHON_GUI:
                # tkinter版本的运行逻辑
                selected_idx = self.info_text.index(tk.END).split('.')[0]
                if selected_idx and int(selected_idx) > 0:
                    plugin = self.plugins[int(selected_idx) - 1]
                    self._execute_plugin(plugin)
            else:
                # Qt版本的运行逻辑
                selected_items = self.plugin_tree.selectedItems()
                if selected_items:
                    plugin = selected_items[0].data(0, QtCore.Qt.UserRole)
                    if plugin:
                        self._execute_plugin(plugin)
        except Exception as e:
            self._log_message(f"运行插件失败: {e}")
    
    def _execute_plugin(self, plugin):
        """执行插件"""
        try:
            self._log_message(f"正在运行插件: {plugin['name']}")
            
            # 添加插件路径到Python路径
            plugin_path = plugin['path']
            if plugin_path not in sys.path:
                sys.path.append(plugin_path)
            
            # 动态导入插件
            if plugin['type'] == 'dcc' and plugin.get('software') == 'maya':
                # Maya插件特殊处理
                from plugin import MayaMeshCleaner
                tool_instance = MayaMeshCleaner()
                
                # 在Maya环境中执行
                result = tool_instance.execute()
                self._log_message(f"执行结果: {result}")
                
            elif plugin['type'] == 'ue':
                # UE插件处理
                from plugin import UEAssetOptimizer
                tool_instance = UEAssetOptimizer()
                result = tool_instance.execute()
                self._log_message(f"执行结果: {result}")
            
            self._log_message(f"插件 {plugin['name']} 执行完成")
            
        except Exception as e:
            self._log_message(f"插件执行错误: {e}")
    
    def _show_documentation(self):
        """显示插件文档"""
        self._log_message("显示文档功能待实现")
    
    def _configure_plugin(self):
        """配置插件参数"""
        self._log_message("参数配置功能待实现")
    
    def _log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if USE_PYTHON_GUI:
            # 在状态栏显示
            if hasattr(self, 'status_label'):
                self.status_label.config(text=message[:50] + "..." if len(message) > 50 else message)
        else:
            # 在日志区域显示
            if hasattr(self, 'log_display'):
                self.log_display.append(log_entry)

def main():
    """主函数"""
    gui = DCCFrameworkGUI()
    gui.show()

if __name__ == "__main__":
    main()