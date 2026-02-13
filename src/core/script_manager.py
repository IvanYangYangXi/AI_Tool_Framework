"""
脚本管理功能模块
提供插件脚本的统一管理、版本控制和部署功能
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import zipfile

class ScriptManager:
    """脚本管理器 - 统一管理所有DCC和UE插件脚本"""
    
    def __init__(self, framework_path: str = None):
        self.framework_path = Path(framework_path) if framework_path else self._find_framework_path()
        self.scripts_dir = self.framework_path / "src" / "plugins"
        self.deploy_dir = self.framework_path / "deployed_scripts"
        self.backup_dir = self.framework_path / "backup"
        self.script_registry = {}  # 脚本注册表
        self._load_script_registry()
    
    def _find_framework_path(self) -> Path:
        """智能查找框架路径"""
        possible_paths = [
            Path.cwd(),
            Path(__file__).parent.parent.parent,
            Path("C:/Users/yangjili/.lingma/worktree/AI_Tool_Framework/HZ0vaV")
        ]
        
        for path in possible_paths:
            if (path / "src" / "core").exists():
                return path
        return Path.cwd()
    
    def _load_script_registry(self):
        """加载脚本注册表"""
        registry_file = self.framework_path / "script_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    self.script_registry = json.load(f)
            except Exception as e:
                print(f"加载脚本注册表失败: {e}")
                self.script_registry = {}
        else:
            self._initialize_registry()
    
    def _initialize_registry(self):
        """初始化脚本注册表"""
        self.script_registry = {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "scripts": {},
            "deployments": {},
            "backups": {}
        }
        self._scan_and_register_scripts()
        self._save_registry()
    
    def _scan_and_register_scripts(self):
        """扫描并注册所有脚本"""
        script_types = ['dcc', 'ue']
        
        for script_type in script_types:
            type_dir = self.scripts_dir / script_type
            if not type_dir.exists():
                continue
            
            for software_dir in type_dir.iterdir():
                if not software_dir.is_dir():
                    continue
                
                for plugin_dir in software_dir.iterdir():
                    if not plugin_dir.is_dir():
                        continue
                    
                    self._register_script(script_type, software_dir.name, plugin_dir)
    
    def _register_script(self, script_type: str, software: str, plugin_dir: Path):
        """注册单个脚本"""
        config_file = plugin_dir / "config.json"
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            script_id = f"{script_type}_{software}_{config['plugin']['name']}"
            script_info = {
                "id": script_id,
                "name": config['plugin']['name'],
                "version": config['plugin']['version'],
                "type": script_type,
                "software": software,
                "path": str(plugin_dir.relative_to(self.framework_path)),
                "description": config['plugin'].get('description', ''),
                "author": config['plugin'].get('author', ''),
                "created": datetime.now().isoformat(),
                "last_modified": datetime.fromtimestamp(plugin_dir.stat().st_mtime).isoformat(),
                "hash": self._calculate_directory_hash(plugin_dir),
                "dependencies": config.get('dependencies', {}),
                "parameters": config.get('parameters', {})
            }
            
            self.script_registry["scripts"][script_id] = script_info
            
        except Exception as e:
            print(f"注册脚本失败 {plugin_dir}: {e}")
    
    def _calculate_directory_hash(self, directory: Path) -> str:
        """计算目录哈希值"""
        hash_obj = hashlib.md5()
        
        for file_path in sorted(directory.rglob('*')):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        # 读取文件内容并更新哈希
                        while chunk := f.read(8192):
                            hash_obj.update(chunk)
                except Exception:
                    continue
        
        return hash_obj.hexdigest()
    
    def _save_registry(self):
        """保存脚本注册表"""
        registry_file = self.framework_path / "script_registry.json"
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.script_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存注册表失败: {e}")
    
    def list_scripts(self, script_type: str = None, software: str = None) -> List[Dict[str, Any]]:
        """列出符合条件的脚本"""
        scripts = []
        
        for script_info in self.script_registry["scripts"].values():
            # 应用筛选条件
            if script_type and script_info["type"] != script_type:
                continue
            if software and script_info["software"] != software:
                continue
            
            scripts.append(script_info)
        
        # 按名称排序
        return sorted(scripts, key=lambda x: x["name"])
    
    def get_script_info(self, script_id: str) -> Optional[Dict[str, Any]]:
        """获取脚本详细信息"""
        return self.script_registry["scripts"].get(script_id)
    
    def deploy_script(self, script_id: str, target_path: str = None) -> Dict[str, Any]:
        """部署脚本到目标位置"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return {"success": False, "error": "脚本不存在"}
        
        try:
            # 确定部署路径
            if target_path:
                deploy_path = Path(target_path)
            else:
                deploy_path = self.deploy_dir / script_info["type"] / script_info["software"] / script_info["name"]
            
            # 创建部署目录
            deploy_path.mkdir(parents=True, exist_ok=True)
            
            # 复制源文件
            source_path = self.framework_path / script_info["path"]
            if not source_path.exists():
                return {"success": False, "error": "源文件不存在"}
            
            # 备份现有文件（如果存在）
            if deploy_path.exists():
                backup_path = self._create_backup(deploy_path, script_id)
                print(f"已备份到: {backup_path}")
            
            # 复制文件
            shutil.copytree(source_path, deploy_path, dirs_exist_ok=True)
            
            # 记录部署信息
            deployment_info = {
                "script_id": script_id,
                "deploy_time": datetime.now().isoformat(),
                "target_path": str(deploy_path),
                "source_hash": script_info["hash"]
            }
            
            if "deployments" not in self.script_registry:
                self.script_registry["deployments"] = {}
            self.script_registry["deployments"][script_id] = deployment_info
            
            self._save_registry()
            
            return {
                "success": True,
                "deployment_info": deployment_info,
                "message": f"脚本 {script_info['name']} 部署成功"
            }
            
        except Exception as e:
            return {"success": False, "error": f"部署失败: {str(e)}"}
    
    def _create_backup(self, source_path: Path, script_id: str) -> Path:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{script_id}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        if source_path.is_file():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_path)
        else:
            shutil.copytree(source_path, backup_path)
        
        # 记录备份信息
        if "backups" not in self.script_registry:
            self.script_registry["backups"] = {}
        
        self.script_registry["backups"][backup_name] = {
            "script_id": script_id,
            "backup_time": datetime.now().isoformat(),
            "backup_path": str(backup_path)
        }
        
        return backup_path
    
    def rollback_script(self, script_id: str, backup_name: str = None) -> Dict[str, Any]:
        """回滚脚本到备份版本"""
        try:
            # 查找最新的备份
            if not backup_name:
                backups = [b for b in self.script_registry.get("backups", {}).values() 
                          if b["script_id"] == script_id]
                if not backups:
                    return {"success": False, "error": "未找到备份"}
                backup_name = sorted(backups, key=lambda x: x["backup_time"])[-1]["backup_path"]
            
            backup_info = self.script_registry["backups"][backup_name]
            backup_path = Path(backup_info["backup_path"])
            
            if not backup_path.exists():
                return {"success": False, "error": "备份文件不存在"}
            
            # 确定部署路径
            deployment_info = self.script_registry["deployments"].get(script_id)
            if not deployment_info:
                return {"success": False, "error": "未找到部署信息"}
            
            target_path = Path(deployment_info["target_path"])
            
            # 执行回滚
            if target_path.exists():
                shutil.rmtree(target_path)
            
            if backup_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, target_path)
            else:
                shutil.copytree(backup_path, target_path)
            
            return {
                "success": True,
                "message": f"脚本已回滚到备份 {backup_name}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"回滚失败: {str(e)}"}
    
    def package_script(self, script_id: str, output_path: str = None) -> Dict[str, Any]:
        """打包脚本为zip文件"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return {"success": False, "error": "脚本不存在"}
        
        try:
            source_path = self.framework_path / script_info["path"]
            if not source_path.exists():
                return {"success": False, "error": "源文件不存在"}
            
            # 确定输出路径
            if not output_path:
                output_path = str(self.framework_path / "packages" / f"{script_id}.zip")
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建zip包
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        arc_name = file_path.relative_to(source_path.parent)
                        zipf.write(file_path, arc_name)
            
            return {
                "success": True,
                "package_path": str(output_file),
                "file_size": output_file.stat().st_size,
                "message": f"脚本打包成功: {output_file.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"打包失败: {str(e)}"}
    
    def update_script(self, script_id: str) -> Dict[str, Any]:
        """更新脚本（检查并应用更改）"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return {"success": False, "error": "脚本不存在"}
        
        try:
            source_path = self.framework_path / script_info["path"]
            current_hash = self._calculate_directory_hash(source_path)
            
            if current_hash != script_info["hash"]:
                # 脚本已修改，更新注册表
                script_info["hash"] = current_hash
                script_info["last_modified"] = datetime.now().isoformat()
                script_info["version"] = self._increment_version(script_info["version"])
                
                self._save_registry()
                
                return {
                    "success": True,
                    "message": f"脚本 {script_info['name']} 已更新到版本 {script_info['version']}",
                    "new_hash": current_hash
                }
            else:
                return {
                    "success": True,
                    "message": "脚本无需更新",
                    "hash_unchanged": True
                }
                
        except Exception as e:
            return {"success": False, "error": f"更新检查失败: {str(e)}"}
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        try:
            parts = version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)
            elif len(parts) >= 2:
                parts[1] = str(int(parts[1]) + 1)
                if len(parts) > 2:
                    parts[2] = '0'
            else:
                parts[0] = str(int(parts[0]) + 1)
                if len(parts) > 1:
                    parts[1] = '0'
                if len(parts) > 2:
                    parts[2] = '0'
            return '.'.join(parts)
        except:
            return version
    
    def get_deployment_status(self, script_id: str) -> Dict[str, Any]:
        """获取脚本部署状态"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return {"error": "脚本不存在"}
        
        deployment_info = self.script_registry["deployments"].get(script_id, {})
        
        status = {
            "script_name": script_info["name"],
            "is_deployed": bool(deployment_info),
            "current_version": script_info["version"],
            "last_modified": script_info["last_modified"]
        }
        
        if deployment_info:
            status.update({
                "deploy_path": deployment_info["target_path"],
                "deploy_time": deployment_info["deploy_time"],
                "needs_update": script_info["hash"] != deployment_info.get("source_hash")
            })
        
        return status
    
    def cleanup_old_backups(self, keep_count: int = 5) -> Dict[str, Any]:
        """清理旧备份文件"""
        try:
            if not self.backup_dir.exists():
                return {"success": True, "message": "无备份文件需要清理"}
            
            # 按时间排序备份
            backups = []
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_dir():
                    backups.append((backup_file, backup_file.stat().st_mtime))
            
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出保留数量的备份
            removed_count = 0
            for backup_path, _ in backups[keep_count:]:
                shutil.rmtree(backup_path)
                removed_count += 1
            
            return {
                "success": True,
                "removed_count": removed_count,
                "remaining_count": len(backups) - removed_count,
                "message": f"已清理 {removed_count} 个旧备份"
            }
            
        except Exception as e:
            return {"success": False, "error": f"清理失败: {str(e)}"}

# 使用示例
def main():
    """脚本管理功能演示"""
    print("=== DCC工具框架脚本管理器 ===\n")
    
    # 创建管理器实例
    manager = ScriptManager()
    
    print("1. 可用脚本列表:")
    scripts = manager.list_scripts()
    for i, script in enumerate(scripts[:5], 1):  # 显示前5个
        print(f"   {i}. {script['name']} ({script['software']}) v{script['version']}")
    
    if scripts:
        # 演示部署功能
        first_script = scripts[0]
        print(f"\n2. 部署脚本示例: {first_script['name']}")
        result = manager.deploy_script(first_script['id'])
        if result['success']:
            print(f"   ✓ {result['message']}")
        else:
            print(f"   ✗ {result['error']}")
        
        # 演示打包功能
        print(f"\n3. 打包脚本示例: {first_script['name']}")
        result = manager.package_script(first_script['id'])
        if result['success']:
            print(f"   ✓ {result['message']}")
            print(f"     文件大小: {result['file_size']} bytes")
        else:
            print(f"   ✗ {result['error']}")
    
    print("\n脚本管理功能演示完成!")

if __name__ == "__main__":
    main()