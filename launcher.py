"""
DCC插件管理器启动脚本
为美术用户提供简单直观的启动方式
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

class LauncherGUI:
    """启动器GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_ui()
    
    def setup_ui(self):
        """设置启动器界面"""
        self.root.title("🎮 DCC插件管理器启动器")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, 
                               text="🎮 DCC插件管理器", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, 
                                  text="专为美术人员设计的插件管理工具",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 30))
        
        # 功能按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 主要功能按钮
        ttk.Button(button_frame, 
                  text="🎨 启动插件管理器", 
                  command=self.launch_manager,
                  width=30).pack(pady=5)
        
        ttk.Button(button_frame, 
                  text="🔧 验证框架完整性", 
                  command=self.verify_framework,
                  width=30).pack(pady=5)
        
        ttk.Button(button_frame, 
                  text="📋 查看使用说明", 
                  command=self.show_manual,
                  width=30).pack(pady=5)
        
        ttk.Button(button_frame, 
                  text="📦 打包为exe程序", 
                  command=self.build_executable,
                  width=30).pack(pady=5)
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)
        
        # 状态信息
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        ttk.Label(status_frame, 
                 text="当前状态:", 
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.status_text = tk.Text(status_frame, height=6, width=50)
        status_scroll = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, 
                                     command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始化状态
        self.update_status("启动器已就绪\n等待用户操作...")
    
    def launch_manager(self):
        """启动插件管理器"""
        self.update_status("正在启动插件管理器...")
        
        try:
            # 尝试启动完整版管理器
            manager_script = Path("src/gui/artistic_plugin_manager.py")
            if manager_script.exists():
                subprocess.Popen([sys.executable, str(manager_script)])
                self.update_status("✓ 已启动完整版插件管理器")
                messagebox.showinfo("启动成功", "插件管理器已启动！")
            else:
                # 启动简化版
                simple_script = Path("src/gui/simple_artistic_manager.py")
                if simple_script.exists():
                    subprocess.Popen([sys.executable, str(simple_script)])
                    self.update_status("✓ 已启动简化版插件管理器")
                    messagebox.showinfo("启动成功", "插件管理器已启动！")
                else:
                    raise FileNotFoundError("未找到插件管理器脚本")
                    
        except Exception as e:
            self.update_status(f"✗ 启动失败: {e}")
            messagebox.showerror("启动失败", f"无法启动插件管理器:\n{e}")
    
    def verify_framework(self):
        """验证框架完整性"""
        self.update_status("正在验证框架完整性...")
        
        try:
            verify_script = Path("verification.py")
            if verify_script.exists():
                result = subprocess.run([sys.executable, str(verify_script)], 
                                      capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    self.update_status("✓ 框架验证通过")
                    messagebox.showinfo("验证结果", "框架完整性验证通过！")
                else:
                    self.update_status("✗ 框架验证失败")
                    messagebox.showerror("验证失败", f"框架存在问题:\n{result.stderr}")
            else:
                raise FileNotFoundError("未找到验证脚本")
                
        except Exception as e:
            self.update_status(f"✗ 验证过程出错: {e}")
            messagebox.showerror("验证错误", f"验证过程出错:\n{e}")
    
    def show_manual(self):
        """显示使用说明"""
        self.update_status("正在打开使用说明...")
        
        try:
            manual_file = Path("COMPLETE_USER_MANUAL.md")
            if manual_file.exists():
                # 在默认应用中打开
                import webbrowser
                webbrowser.open(str(manual_file.absolute()))
                self.update_status("✓ 已打开使用说明")
            else:
                # 显示简单的帮助信息
                help_text = """
DCC插件管理器使用指南:

🎨 主要功能:
• 插件浏览和管理
• 参数可视化配置  
• 一键执行工具
• 执行日志记录

🚀 快速开始:
1. 点击"启动插件管理器"
2. 选择需要的插件
3. 配置相关参数
4. 点击"运行插件"

🔧 技术支持:
• 确保Python环境正常
• 检查框架完整性
• 查看详细文档获取帮助
        """
                messagebox.showinfo("使用说明", help_text)
                self.update_status("✓ 已显示使用说明")
                
        except Exception as e:
            self.update_status(f"✗ 显示说明失败: {e}")
            messagebox.showerror("错误", f"无法显示使用说明:\n{e}")
    
    def build_executable(self):
        """打包为exe程序"""
        self.update_status("正在准备打包...")
        
        try:
            build_script = Path("build_exe.py")
            if build_script.exists():
                result = subprocess.run([sys.executable, str(build_script)], 
                                      capture_output=True, text=True, cwd=Path.cwd())
                
                if result.returncode == 0:
                    self.update_status("✓ exe打包完成")
                    messagebox.showinfo("打包完成", "exe程序打包成功！\n请查看dist目录")
                else:
                    self.update_status("✗ 打包失败")
                    messagebox.showerror("打包失败", f"打包过程出错:\n{result.stderr}")
            else:
                raise FileNotFoundError("未找到打包脚本")
                
        except Exception as e:
            self.update_status(f"✗ 打包过程出错: {e}")
            messagebox.showerror("打包错误", f"打包过程出错:\n{e}")
    
    def update_status(self, message):
        """更新状态信息"""
        timestamp = self.get_timestamp()
        status_entry = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, status_entry)
        self.status_text.see(tk.END)
        
        # 限制状态记录数量
        lines = self.status_text.get(1.0, tk.END).split('\n')
        if len(lines) > 20:
            self.status_text.delete(1.0, f"{len(lines)-19}.0")
    
    def get_timestamp(self):
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

def main():
    """主函数"""
    try:
        app = LauncherGUI()
        app.root.mainloop()
    except Exception as e:
        print(f"启动器启动失败: {e}")
        messagebox.showerror("启动错误", f"启动器启动失败:\n{e}")

if __name__ == "__main__":
    main()