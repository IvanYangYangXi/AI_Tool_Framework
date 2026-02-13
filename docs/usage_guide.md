# DCC工具和UE引擎工具管理框架使用指南

## 项目概述

这是一个统一的工具管理框架，专门用于管理和扩展各种DCC软件（Maya、3ds Max、Blender等）和Unreal Engine的工具插件。

## 核心特性

- **统一管理**：集中管理所有DCC和UE工具插件
- **易扩展性**：支持快速添加新的工具插件
- **自然语言支持**：通过文字描述自动生成工具配置
- **SDD规范**：采用软件设计文档风格的工具规则描述
- **安全可靠**：插件沙箱执行，权限控制

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 或者使用poetry
poetry install
```

### 2. 运行演示

```bash
# 运行框架演示
python -m src.main

# 运行单元测试
python -m pytest tests/ -v
```

## 核心组件介绍

### 1. 插件管理器 (PluginManager)

负责插件的生命周期管理、发现和注册。

```python
from src.core import PluginManager

# 创建插件管理器
pm = PluginManager(['./plugins'])

# 发现插件
plugins = pm.discover_plugins()

# 加载插件
pm.load_plugin('MeshExporter')

# 获取插件
plugin = pm.get_plugin('MeshExporter')
```

### 2. 动态加载引擎 (DynamicLoader)

提供安全的插件加载和执行环境。

```python
from src.core import DynamicLoader

# 创建加载器
loader = DynamicLoader(sandbox_enabled=True)

# 安全加载模块
module = loader.load_module_safely('./my_plugin.py')

# 安全执行函数
result = loader.execute_function_safely(
    module.my_function, 
    arg1, arg2,
    _timeout=30
)
```

### 3. 配置管理器 (ConfigManager)

处理SDD配置文件的解析和验证。

```python
from src.core import ConfigManager

# 创建配置管理器
cm = ConfigManager(['./configs'])

# 解析SDD配置
config = cm.parse_sdd_config('./tool_config.yaml')

# 基于模板生成配置
generated_config = cm.generate_config_from_template(
    'basic_dcc_tool',
    {
        'tool_name': 'MyTool',
        'description': '我的工具',
        'author': 'Developer'
    }
)
```

### 4. 权限控制系统 (PermissionSystem)

提供基于角色的访问控制和安全验证。

```python
from src.core import PermissionSystem
from src.core.permission_system import ResourceType, PermissionLevel

# 创建权限系统
ps = PermissionSystem()

# 用户认证
token = ps.authenticate_user('admin')
payload = ps.verify_token(token)

# 权限检查
has_permission = ps.check_permission(
    'admin',
    ResourceType.PLUGIN,
    PermissionLevel.EXECUTE
)
```

## 插件开发指南

### 1. 插件基本结构

```python
# plugin.py
PLUGIN_NAME = "MyPlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "dcc"  # dcc, ue_engine, utility
PLUGIN_DESCRIPTION = "插件描述"
PLUGIN_AUTHOR = "作者"

def execute(**kwargs):
    """插件主执行函数"""
    # 插件逻辑实现
    return {"status": "success"}

def register():
    """插件注册函数"""
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "execute": execute
    }
```

### 2. SDD配置规范

```yaml
tool:
  name: "工具名称"
  version: "1.0.0"
  type: "dcc"
  description: "工具描述"

metadata:
  author: "作者"
  created_date: "2024-01-01"
  compatibility:
    - platform: "dcc"
      name: "maya"
      min_version: "2022"

configuration:
  parameters:
    - name: "output_path"
      type: "string"
      required: true
      description: "输出路径"

execution:
  entry_point: "main.py::execute"
  dependencies:
    - "numpy>=1.20.0"
  resources:
    memory_limit: "512MB"
    timeout: "30s"

integration:
  interfaces:
    - name: "UI界面"
      type: "qt"
```

## 自然语言配置生成

框架支持通过文字描述自动生成工具配置：

```
我想创建一个Maya的网格导出工具，需要支持OBJ和FBX格式，
输出路径可配置，默认导出当前选中的对象。
```

系统会自动转换为标准的SDD配置格式。

## 安全特性

### 1. 沙箱执行
- 资源限制（内存、CPU时间）
- 执行超时控制
- 环境隔离

### 2. 权限控制
- 基于角色的访问控制(RBAC)
- 代码签名验证
- 审计日志记录

### 3. 依赖管理
- 依赖关系解析
- 版本冲突检测
- 安全依赖验证

## 目录结构

```
dcc_ue_tool_framework/
├── src/
│   ├── core/                 # 核心模块
│   │   ├── plugin_manager.py
│   │   ├── dynamic_loader.py
│   │   ├── config_manager.py
│   │   └── permission_system.py
│   ├── nlp/                  # 自然语言处理
│   ├── plugins/              # 内置插件示例
│   └── main.py               # 主入口
├── configs/                  # 配置文件
│   ├── templates/           # SDD模板
│   └── plugins/             # 插件配置
├── tests/                    # 测试用例
├── docs/                     # 文档
└── examples/                 # 示例代码
```

## API参考

详细的API文档请参考 [docs/api_reference.md](./docs/api_reference.md)

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系项目维护者。