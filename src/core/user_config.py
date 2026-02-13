"""
用户配置系统
管理用户偏好设置、工作区配置和个人化选项
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib

class UserConfiguration:
    """用户配置管理系统"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or self._get_current_user_id()
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / f"user_config_{self.user_id}.json"
        self.backup_dir = self.config_dir / "backups"
        self.current_config = self._load_user_config()
        
    def _get_current_user_id(self) -> str:
        """获取当前用户标识"""
        try:
            # 尝试获取系统用户名
            import getpass
            username = getpass.getuser()
        except:
            username = "anonymous"
        
        # 生成用户ID哈希
        user_hash = hashlib.md5(username.encode()).hexdigest()[:8]
        return f"user_{user_hash}"
    
    def _get_config_directory(self) -> Path:
        """获取配置文件存储目录"""
        if sys.platform == "win32":
            config_base = Path.home() / "AppData" / "Local" / "DCCToolFramework"
        elif sys.platform == "darwin":  # macOS
            config_base = Path.home() / "Library" / "Application Support" / "DCCToolFramework"
        else:  # Linux
            config_base = Path.home() / ".config" / "dcctoolframework"
        
        config_dir = config_base / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir
    
    def _load_user_config(self) -> Dict[str, Any]:
        """加载用户配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 验证配置版本
                if config.get("version") != "1.0":
                    print("配置版本不匹配，使用默认配置")
                    return self._get_default_config()
                
                return config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self._get_default_config()
        else:
            # 创建默认配置
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "user_id": self.user_id,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "preferences": {
                "theme": "auto",  # auto, light, dark
                "language": "zh-CN",
                "auto_save": True,
                "backup_frequency": "daily",  # never, daily, weekly
                "max_recent_files": 10,
                "show_tooltips": True,
                "animation_speed": "normal"  # slow, normal, fast
            },
            "workspace": {
                "window_size": [1200, 800],
                "window_position": [100, 100],
                "panels": {
                    "plugin_browser": {"visible": True, "width": 300},
                    "parameter_editor": {"visible": True, "height": 200},
                    "log_viewer": {"visible": True, "height": 150}
                },
                "recent_projects": [],
                "favorite_plugins": [],
                "custom_shortcuts": {}
            },
            "plugin_settings": {
                "default_parameters": {},
                "plugin_specific": {}
            },
            "deployment": {
                "default_target": "local",
                "auto_deploy": False,
                "backup_before_deploy": True,
                "deployment_history": []
            },
            "security": {
                "require_confirmation": True,
                "log_sensitive_operations": True,
                "auto_lock_timeout": 30  # 分钟
            }
        }
    
    def _save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置到文件"""
        try:
            config_to_save = config or self.current_config
            config_to_save["last_updated"] = datetime.now().isoformat()
            
            # 创建备份
            if self.config_file.exists():
                self._create_backup()
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            self.current_config = config_to_save
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def _create_backup(self) -> str:
        """创建配置备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.config_file, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"创建备份失败: {e}")
            return ""
    
    def get_preference(self, key: str, default=None):
        """获取用户偏好设置"""
        keys = key.split('.')
        value = self.current_config["preferences"]
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def set_preference(self, key: str, value: Any) -> bool:
        """设置用户偏好"""
        keys = key.split('.')
        config_section = self.current_config["preferences"]
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]
        
        # 设置值
        config_section[keys[-1]] = value
        return self._save_config()
    
    def get_workspace_setting(self, key: str, default=None):
        """获取工作区设置"""
        keys = key.split('.')
        value = self.current_config["workspace"]
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def set_workspace_setting(self, key: str, value: Any) -> bool:
        """设置工作区配置"""
        keys = key.split('.')
        config_section = self.current_config["workspace"]
        
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]
        
        config_section[keys[-1]] = value
        return self._save_config()
    
    def add_recent_project(self, project_path: str):
        """添加最近项目"""
        recent_projects = self.current_config["workspace"]["recent_projects"]
        
        # 移除已存在的项目
        if project_path in recent_projects:
            recent_projects.remove(project_path)
        
        # 添加到开头
        recent_projects.insert(0, project_path)
        
        # 限制数量
        max_recent = self.get_preference("max_recent_files", 10)
        self.current_config["workspace"]["recent_projects"] = recent_projects[:max_recent]
        
        self._save_config()
    
    def add_favorite_plugin(self, plugin_id: str):
        """添加收藏插件"""
        favorites = self.current_config["workspace"]["favorite_plugins"]
        if plugin_id not in favorites:
            favorites.append(plugin_id)
            self._save_config()
    
    def remove_favorite_plugin(self, plugin_id: str):
        """移除收藏插件"""
        favorites = self.current_config["workspace"]["favorite_plugins"]
        if plugin_id in favorites:
            favorites.remove(plugin_id)
            self._save_config()
    
    def set_plugin_parameter(self, plugin_id: str, param_name: str, value: Any):
        """设置插件参数偏好"""
        if "plugin_specific" not in self.current_config["plugin_settings"]:
            self.current_config["plugin_settings"]["plugin_specific"] = {}
        
        if plugin_id not in self.current_config["plugin_settings"]["plugin_specific"]:
            self.current_config["plugin_settings"]["plugin_specific"][plugin_id] = {}
        
        self.current_config["plugin_settings"]["plugin_specific"][plugin_id][param_name] = value
        self._save_config()
    
    def get_plugin_parameters(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件参数偏好"""
        return self.current_config["plugin_settings"]["plugin_specific"].get(plugin_id, {})
    
    def export_configuration(self, export_path: str = None) -> Dict[str, Any]:
        """导出用户配置"""
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = str(self.config_dir / f"user_config_export_{timestamp}.json")
        
        try:
            export_data = {
                "export_info": {
                    "user_id": self.user_id,
                    "export_time": datetime.now().isoformat(),
                    "framework_version": "1.0.0"
                },
                "configuration": self.current_config
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "export_path": export_path,
                "message": "配置导出成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"导出失败: {str(e)}"
            }
    
    def import_configuration(self, import_path: str) -> Dict[str, Any]:
        """导入用户配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证导入数据
            if "configuration" not in import_data:
                return {"success": False, "error": "无效的配置文件格式"}
            
            imported_config = import_data["configuration"]
            
            # 合并配置（保留用户ID等关键信息）
            merged_config = self.current_config.copy()
            merged_config.update(imported_config)
            merged_config["user_id"] = self.user_id  # 保持当前用户ID
            merged_config["last_updated"] = datetime.now().isoformat()
            
            # 保存合并后的配置
            if self._save_config(merged_config):
                return {
                    "success": True,
                    "message": "配置导入成功",
                    "imported_sections": list(imported_config.keys())
                }
            else:
                return {"success": False, "error": "保存配置失败"}
                
        except Exception as e:
            return {
                "success": False,
                "error": f"导入失败: {str(e)}"
            }
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        default_config = self._get_default_config()
        return self._save_config(default_config)
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        
        return {
            "user_id": self.user_id,
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "config_path": str(self.config_file),
            "backup_path": str(self.backup_dir),
            "last_updated": self.current_config.get("last_updated"),
            "total_favorites": len(self.current_config["workspace"]["favorite_plugins"]),
            "recent_projects_count": len(self.current_config["workspace"]["recent_projects"])
        }
    
    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """清理旧的配置备份"""
        try:
            import time
            
            current_time = time.time()
            removed_count = 0
            
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > (keep_days * 24 * 3600):  # 转换为秒
                    backup_file.unlink()
                    removed_count += 1
            
            return {
                "success": True,
                "removed_count": removed_count,
                "message": f"已清理 {removed_count} 个旧备份文件"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清理备份失败: {str(e)}"
            }

# 使用示例和测试
def main():
    """用户配置系统演示"""
    print("=== DCC工具框架用户配置系统 ===\n")
    
    # 创建配置管理器
    config_manager = UserConfiguration()
    
    print("1. 用户信息:")
    system_info = config_manager.get_system_info()
    print(f"   用户ID: {system_info['user_id']}")
    print(f"   平台: {system_info['platform']}")
    print(f"   配置路径: {system_info['config_path']}")
    
    print("\n2. 当前偏好设置:")
    print(f"   主题: {config_manager.get_preference('theme')}")
    print(f"   语言: {config_manager.get_preference('language')}")
    print(f"   自动保存: {config_manager.get_preference('auto_save')}")
    
    print("\n3. 工作区设置:")
    print(f"   窗口大小: {config_manager.get_workspace_setting('window_size')}")
    print(f"   最近项目数: {system_info['recent_projects_count']}")
    print(f"   收藏插件数: {system_info['total_favorites']}")
    
    # 演示设置修改
    print("\n4. 修改偏好设置:")
    config_manager.set_preference('theme', 'dark')
    print(f"   主题已设置为: {config_manager.get_preference('theme')}")
    
    # 演示工作区配置
    print("\n5. 修改工作区设置:")
    config_manager.set_workspace_setting('window_size', [1400, 900])
    print(f"   窗口大小已更新: {config_manager.get_workspace_setting('window_size')}")
    
    # 演示收藏功能
    print("\n6. 收藏插件管理:")
    config_manager.add_favorite_plugin('maya_mesh_cleaner')
    config_manager.add_favorite_plugin('ue_asset_optimizer')
    favorites = config_manager.current_config["workspace"]["favorite_plugins"]
    print(f"   当前收藏插件: {favorites}")
    
    # 演示配置导出
    print("\n7. 配置导出:")
    export_result = config_manager.export_configuration()
    if export_result['success']:
        print(f"   ✓ {export_result['message']}")
        print(f"     导出路径: {export_result['export_path']}")
    else:
        print(f"   ✗ {export_result['error']}")
    
    print("\n用户配置系统演示完成!")

if __name__ == "__main__":
    main()