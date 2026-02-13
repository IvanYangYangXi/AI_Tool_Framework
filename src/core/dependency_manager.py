"""
插件依赖管理系统
负责管理插件之间的依赖关系、版本兼容性和冲突检测
"""

import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class DependencyType(Enum):
    """依赖类型枚举"""
    REQUIRED = "required"      # 必需依赖
    OPTIONAL = "optional"      # 可选依赖
    CONFLICT = "conflict"      # 冲突依赖


class CompatibilityStatus(Enum):
    """兼容性状态枚举"""
    COMPATIBLE = "compatible"           # 完全兼容
    PARTIALLY_COMPATIBLE = "partial"    # 部分兼容
    INCOMPATIBLE = "incompatible"       # 不兼容
    UNKNOWN = "unknown"                 # 未知


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    type: str
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    compatible_versions: List[str] = field(default_factory=list)
    author: str = ""
    description: str = ""


@dataclass
class DependencyInfo:
    """依赖信息"""
    plugin_name: str
    dependency_name: str
    dependency_type: DependencyType
    version_constraints: List[str]  # 版本约束条件
    status: CompatibilityStatus = CompatibilityStatus.UNKNOWN


class PluginDependencyManager:
    """插件依赖管理器"""
    
    def __init__(self, plugins_directory: str = "src/plugins"):
        self.plugins_directory = Path(plugins_directory)
        self.plugins_metadata: Dict[str, PluginMetadata] = {}
        self.dependencies: Dict[str, List[DependencyInfo]] = {}
        self.logger = self._setup_logger()
        self._load_all_plugins()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_all_plugins(self):
        """加载所有插件的元数据"""
        self.logger.info("开始加载插件元数据...")
        
        # 查找所有config.json文件
        config_files = self.plugins_directory.rglob("config.json")
        
        for config_file in config_files:
            try:
                self._load_plugin_config(config_file)
            except Exception as e:
                self.logger.warning(f"加载插件配置失败 {config_file}: {e}")
        
        self.logger.info(f"成功加载 {len(self.plugins_metadata)} 个插件")
    
    def _load_plugin_config(self, config_path: Path):
        """加载单个插件配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        plugin_info = config.get('plugin', {})
        plugin_name = plugin_info.get('name')
        
        if not plugin_name:
            raise ValueError("插件配置缺少名称")
        
        # 解析依赖信息
        dependencies = config.get('dependencies', {})
        required_deps = dependencies.get('required', [])
        optional_deps = dependencies.get('optional', [])
        
        # 创建插件元数据
        metadata = PluginMetadata(
            name=plugin_name,
            version=plugin_info.get('version', '1.0.0'),
            type=plugin_info.get('type', 'generic'),
            dependencies={
                'required': required_deps,
                'optional': optional_deps
            },
            conflicts=config.get('conflicts', []),
            compatible_versions=config.get('compatible_versions', []),
            author=plugin_info.get('author', ''),
            description=plugin_info.get('description', '')
        )
        
        self.plugins_metadata[plugin_name] = metadata
        self.logger.debug(f"加载插件: {plugin_name} v{metadata.version}")
    
    def analyze_dependencies(self) -> Dict[str, List[DependencyInfo]]:
        """分析所有插件的依赖关系"""
        self.logger.info("开始分析插件依赖关系...")
        
        for plugin_name, metadata in self.plugins_metadata.items():
            plugin_deps = []
            
            # 分析必需依赖
            for dep_name in metadata.dependencies.get('required', []):
                dep_info = self._analyze_dependency(plugin_name, dep_name, DependencyType.REQUIRED)
                plugin_deps.append(dep_info)
            
            # 分析可选依赖
            for dep_name in metadata.dependencies.get('optional', []):
                dep_info = self._analyze_dependency(plugin_name, dep_name, DependencyType.OPTIONAL)
                plugin_deps.append(dep_info)
            
            # 分析冲突依赖
            for conflict_name in metadata.conflicts:
                dep_info = self._analyze_dependency(plugin_name, conflict_name, DependencyType.CONFLICT)
                plugin_deps.append(dep_info)
            
            self.dependencies[plugin_name] = plugin_deps
        
        self.logger.info("依赖关系分析完成")
        return self.dependencies
    
    def _analyze_dependency(self, plugin_name: str, dependency_name: str, 
                          dep_type: DependencyType) -> DependencyInfo:
        """分析单个依赖关系"""
        # 检查依赖是否存在
        if dependency_name not in self.plugins_metadata:
            return DependencyInfo(
                plugin_name=plugin_name,
                dependency_name=dependency_name,
                dependency_type=dep_type,
                version_constraints=[],
                status=CompatibilityStatus.UNKNOWN
            )
        
        # 获取依赖插件信息
        dep_metadata = self.plugins_metadata[dependency_name]
        version_constraints = self._extract_version_constraints(plugin_name, dependency_name)
        
        # 检查版本兼容性
        compatibility_status = self._check_version_compatibility(
            plugin_name, dependency_name, version_constraints
        )
        
        return DependencyInfo(
            plugin_name=plugin_name,
            dependency_name=dependency_name,
            dependency_type=dep_type,
            version_constraints=version_constraints,
            status=compatibility_status
        )
    
    def _extract_version_constraints(self, plugin_name: str, dependency_name: str) -> List[str]:
        """提取版本约束条件"""
        # 这里可以根据配置文件或其他方式提取版本约束
        # 简化实现，返回空列表
        return []
    
    def _check_version_compatibility(self, plugin_name: str, dependency_name: str,
                                   constraints: List[str]) -> CompatibilityStatus:
        """检查版本兼容性"""
        plugin_meta = self.plugins_metadata[plugin_name]
        dep_meta = self.plugins_metadata[dependency_name]
        
        # 如果依赖插件没有指定兼容版本，则假定兼容
        if not dep_meta.compatible_versions:
            return CompatibilityStatus.COMPATIBLE
        
        # 检查当前插件版本是否在依赖的兼容版本范围内
        if plugin_meta.version in dep_meta.compatible_versions:
            return CompatibilityStatus.COMPATIBLE
        else:
            return CompatibilityStatus.INCOMPATIBLE
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图"""
        graph = {}
        
        for plugin_name, deps in self.dependencies.items():
            graph[plugin_name] = [
                dep.dependency_name for dep in deps 
                if dep.dependency_type == DependencyType.REQUIRED
            ]
        
        return graph
    
    def detect_conflicts(self) -> List[Tuple[str, str, str]]:
        """检测依赖冲突"""
        conflicts = []
        
        for plugin_name, deps in self.dependencies.items():
            for dep in deps:
                if dep.status == CompatibilityStatus.INCOMPATIBLE:
                    conflicts.append((
                        plugin_name,
                        dep.dependency_name,
                        f"版本不兼容: {dep.version_constraints}"
                    ))
                
                # 检查显式声明的冲突
                if dep.dependency_type == DependencyType.CONFLICT:
                    conflicts.append((
                        plugin_name,
                        dep.dependency_name,
                        "显式声明的冲突依赖"
                    ))
        
        return conflicts
    
    def get_installation_order(self) -> List[str]:
        """获取插件安装顺序（拓扑排序）"""
        graph = self.get_dependency_graph()
        visited = set()
        order = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            
            # 先处理依赖
            for neighbor in graph.get(node, []):
                if neighbor in self.plugins_metadata:  # 确保依赖存在
                    dfs(neighbor)
            
            order.append(node)
        
        # 对所有节点进行DFS
        for plugin_name in self.plugins_metadata.keys():
            dfs(plugin_name)
        
        return order
    
    def validate_plugin_set(self, plugin_names: List[str]) -> Dict[str, any]:
        """验证一组插件的兼容性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_dependencies": [],
            "conflicts": []
        }
        
        # 检查所有插件是否存在
        for plugin_name in plugin_names:
            if plugin_name not in self.plugins_metadata:
                validation_result["errors"].append(f"插件不存在: {plugin_name}")
                validation_result["valid"] = False
        
        if not validation_result["valid"]:
            return validation_result
        
        # 检查必需依赖
        required_deps = set()
        for plugin_name in plugin_names:
            metadata = self.plugins_metadata[plugin_name]
            required_deps.update(metadata.dependencies.get('required', []))
        
        # 检查缺失的依赖
        missing_deps = required_deps - set(plugin_names)
        for dep in missing_deps:
            if dep in self.plugins_metadata:
                validation_result["missing_dependencies"].append(dep)
                validation_result["warnings"].append(f"缺少必需依赖: {dep}")
            else:
                validation_result["errors"].append(f"必需依赖不存在: {dep}")
                validation_result["valid"] = False
        
        # 检查冲突
        conflicts = self.detect_conflicts()
        for plugin_a, plugin_b, reason in conflicts:
            if plugin_a in plugin_names and plugin_b in plugin_names:
                validation_result["conflicts"].append((plugin_a, plugin_b, reason))
                validation_result["errors"].append(f"冲突: {plugin_a} 与 {plugin_b} - {reason}")
                validation_result["valid"] = False
        
        return validation_result
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, any]]:
        """获取插件详细信息"""
        if plugin_name not in self.plugins_metadata:
            return None
        
        metadata = self.plugins_metadata[plugin_name]
        dependencies = self.dependencies.get(plugin_name, [])
        
        return {
            "name": metadata.name,
            "version": metadata.version,
            "type": metadata.type,
            "author": metadata.author,
            "description": metadata.description,
            "dependencies": [
                {
                    "name": dep.dependency_name,
                    "type": dep.dependency_type.value,
                    "status": dep.status.value,
                    "constraints": dep.version_constraints
                }
                for dep in dependencies
            ],
            "conflicts": metadata.conflicts
        }
    
    def export_dependency_report(self, output_path: str):
        """导出依赖关系报告"""
        report = {
            "summary": {
                "total_plugins": len(self.plugins_metadata),
                "analyzed_dependencies": len(self.dependencies)
            },
            "plugins": {},
            "conflicts": self.detect_conflicts(),
            "installation_order": self.get_installation_order()
        }
        
        # 添加每个插件的详细信息
        for plugin_name in self.plugins_metadata.keys():
            report["plugins"][plugin_name] = self.get_plugin_info(plugin_name)
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"依赖关系报告已导出到: {output_path}")


# 使用示例和测试
if __name__ == "__main__":
    # 创建依赖管理器
    manager = PluginDependencyManager()
    
    print("=== 插件依赖管理系统测试 ===\n")
    
    # 显示加载的插件
    print("已加载的插件:")
    for name, metadata in manager.plugins_metadata.items():
        print(f"  - {name} v{metadata.version} ({metadata.type})")
    
    print(f"\n总共加载了 {len(manager.plugins_metadata)} 个插件\n")
    
    # 分析依赖关系
    dependencies = manager.analyze_dependencies()
    
    # 显示依赖关系
    print("依赖关系分析:")
    for plugin_name, deps in dependencies.items():
        if deps:
            print(f"\n{plugin_name} 的依赖:")
            for dep in deps:
                status_icon = "✓" if dep.status == CompatibilityStatus.COMPATIBLE else "✗"
                print(f"  {status_icon} {dep.dependency_name} ({dep.dependency_type.value})")
    
    # 检测冲突
    conflicts = manager.detect_conflicts()
    if conflicts:
        print(f"\n发现 {len(conflicts)} 个冲突:")
        for plugin_a, plugin_b, reason in conflicts:
            print(f"  {plugin_a} ↔ {plugin_b}: {reason}")
    else:
        print("\n未发现依赖冲突 ✓")
    
    # 获取安装顺序
    install_order = manager.get_installation_order()
    print(f"\n推荐安装顺序:")
    for i, plugin_name in enumerate(install_order, 1):
        print(f"  {i}. {plugin_name}")
    
    # 验证插件组合
    test_plugins = list(manager.plugins_metadata.keys())[:3]  # 测试前3个插件
    if test_plugins:
        print(f"\n验证插件组合 {test_plugins}:")
        validation = manager.validate_plugin_set(test_plugins)
        print(f"  有效性: {'✓' if validation['valid'] else '✗'}")
        if validation['errors']:
            print("  错误:")
            for error in validation['errors']:
                print(f"    - {error}")
        if validation['warnings']:
            print("  警告:")
            for warning in validation['warnings']:
                print(f"    - {warning}")
    
    # 导出报告
    manager.export_dependency_report("dependency_report.json")
    print("\n依赖关系报告已生成")