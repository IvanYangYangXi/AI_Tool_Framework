# DCC工具框架使用入门指南

## 🎯 快速开始

### 1. 环境验证
```bash
# 验证框架完整性
python verification.py
```

### 2. 直接使用现有插件

#### Maya网格清理工具
```python
# 使用示例
import sys
sys.path.append("src/plugins/dcc/maya/mesh_cleaner")

from plugin import MayaMeshCleaner

# 创建插件实例
cleaner = MayaMeshCleaner()

# 查看插件信息
info = cleaner.get_info()
print(f"插件: {info['name']} v{info['version']}")

# 验证参数
params = {
    "tolerance": 0.001,
    "delete_duplicates": True,
    "merge_vertices": True
}
validated_params = cleaner.validate_parameters(params)
```

#### Blender网格优化工具
```python
# 使用示例
import sys
sys.path.append("src/plugins/dcc/blender/mesh_optimizer")

from plugin import BlenderMeshOptimizer

optimizer = BlenderMeshOptimizer()
info = optimizer.get_info()
print(f"支持的Blender版本: {info['min_version']}-{info['max_version']}")
```

### 3. 依赖管理使用
```python
from src.core.dependency_manager import PluginDependencyManager

# 创建依赖管理器
manager = PluginDependencyManager("src/plugins")

# 分析依赖关系
dependencies = manager.analyze_dependencies()

# 检测冲突
conflicts = manager.detect_conflicts()

# 获取安装顺序
install_order = manager.get_installation_order()
```

### 4. 插件市场使用
```python
from src.core.plugin_market import PluginMarketplace

# 创建市场实例
market = PluginMarketplace()

# 搜索插件
plugins = market.search_plugins(query="maya", sort_by="rating")

# 获取热门插件
popular = market.get_popular_plugins(limit=5)

# 获取插件详情
plugin_details = market.get_plugin_details("maya_mesh_cleaner")
```

## 📁 项目结构说明

```
src/
├── core/                    # 核心组件
│   ├── dcc_plugin_interface.py    # DCC插件接口
│   ├── ue_plugin_interface.py     # UE插件接口
│   ├── dependency_manager.py      # 依赖管理器
│   └── plugin_market.py           # 插件市场
│
├── plugins/                 # 插件目录
│   ├── dcc/                # DCC工具插件
│   │   ├── maya/mesh_cleaner/     # Maya网格清理
│   │   ├── max/material_converter/ # 3ds Max材质转换
│   │   └── blender/mesh_optimizer/ # Blender网格优化
│   │
│   └── ue/                 # UE引擎插件
│       └── asset_optimizer/       # UE资产优化
│
└── demo/                   # 使用示例
    └── framework_usage_demo.py    # 使用演示
```

## 🔧 开发新插件

### 1. 选择模板
根据目标软件选择相应的插件模板：
- Maya插件: 复制 `src/plugins/dcc/maya/mesh_cleaner/`
- 3ds Max插件: 复制 `src/plugins/dcc/max/material_converter/`
- Blender插件: 复制 `src/plugins/dcc/blender/mesh_optimizer/`
- UE插件: 复制 `src/plugins/ue/asset_optimizer/`

### 2. 修改配置文件
编辑 `config.json` 文件：
```json
{
  "plugin": {
    "name": "YourPluginName",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "Your Name"
  }
}
```

### 3. 实现核心功能
在 `plugin.py` 中实现具体功能：
```python
from ...core.dcc_plugin_interface import DCCPluginInterface, dcc_plugin

@dcc_plugin(name="YourPlugin", version="1.0.0", ...)
class YourPlugin(DCCPluginInterface):
    def execute(self, **kwargs):
        # 实现主要功能
        pass
    
    def get_info(self):
        # 返回插件信息
        pass
```

## 📚 学习资源

1. **查看现有插件源码** - 学习最佳实践
2. **阅读接口文档** - 了解标准规范
3. **运行测试脚本** - 验证功能正确性
4. **参考配置示例** - 掌握配置方法

## 💡 实用技巧

- 使用 `verification.py` 定期检查框架完整性
- 通过依赖管理器确保插件兼容性
- 利用插件市场的搜索功能快速找到需要的工具
- 参考README文档了解详细的使用方法

现在您可以开始使用这个强大的DCC工具框架了！