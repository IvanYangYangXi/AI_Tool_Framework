# DCC工具和UE引擎工具管理框架

这是一个统一的工具管理框架，用于管理和扩展各种DCC软件（Maya、3ds Max、Blender等）和Unreal Engine的工具插件。

## 核心特性

- **统一管理**：集中管理所有DCC和UE工具插件
- **可视化界面**：轻量级工具管理器，支持一键执行脚本
- **DCC连接**：自动连接Maya、3ds Max、Blender等软件
- **实时日志**：捕获并显示脚本执行输出
- **易扩展性**：支持快速添加新的工具插件

## 快速开始

### 方式一：使用启动脚本（推荐）
双击 `启动工具管理器.bat` 即可启动工具管理器界面。

### 方式二：命令行启动
```bash
# 安装依赖
pip install -r requirements.txt

# 启动工具管理器
python src/gui/lightweight_manager.py
```

## 项目目录结构

```
AI_Tool_Framework/
├── .codemaker/                     # IDE配置
│   └── rules/                      # 编码规则
│       └── rules.mdc               # AI编程指南
│
├── docs/                           # 📚 文档目录
│   ├── 美术人员使用指南.md          # 用户使用手册
│   └── 归档文档/                   # 历史文档归档
│       ├── 项目完成报告.md
│       ├── 使用指南/
│       │   ├── AI工具生成指南.md
│       │   ├── 完整用户手册.md
│       │   └── 智能需求分析指南.md
│       └── 研究报告/
│           ├── DCC与UE插件系统研究.md
│           ├── 框架设计分析.md
│           ├── 插件系统实现示例.md
│           └── 研究总结报告.md
│
├── src/                            # 📦 源代码目录
│   ├── core/                       # 核心模块
│   │   ├── __init__.py
│   │   ├── config_manager.py       # 配置管理器
│   │   ├── dcc_plugin_interface.py # DCC插件标准接口
│   │   ├── dynamic_loader.py       # 动态加载引擎
│   │   ├── permission_system.py    # 权限控制系统
│   │   ├── plugin_manager.py       # 插件生命周期管理
│   │   └── ue_plugin_interface.py  # UE插件标准接口
│   │
│   ├── gui/                        # 图形界面
│   │   └── lightweight_manager.py  # 轻量级工具管理器
│   │
│   ├── plugins/                    # 🔌 插件目录
│   │   ├── dcc/                    # DCC软件插件
│   │   │   ├── maya/               # Maya插件
│   │   │   │   └── example_print_selection/
│   │   │   ├── max/                # 3ds Max插件
│   │   │   │   └── example_print_selection/
│   │   │   └── blender/            # Blender插件
│   │   │       └── example_print_selection/
│   │   └── ue/                     # Unreal Engine插件
│   │       └── example_print_selection/
│   │
│   └── main.py                     # 主入口（命令行演示）
│
├── 启动工具管理器.bat               # Windows启动脚本
├── 启动工具管理器.vbs               # 后台启动脚本（无命令行窗口）
├── pyproject.toml                  # Poetry项目配置
├── requirements.txt                # pip依赖文件
├── README.md                       # 本文件
└── .gitignore                      # Git忽略配置
```

## 插件结构说明

每个插件包含以下文件：

```
example_print_selection/
├── config.json     # 插件配置（名称、版本、描述等）
└── plugin.py       # 插件代码（包含execute方法）
```

### 插件接口标准

```python
class PluginName:
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行插件主功能"""
        return {"status": "success", "result": ...}
    
    def get_selection(self) -> List[str]:
        """获取当前选择"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        pass
```

## DCC软件连接端口

| 软件 | 端口 | 说明 |
|------|------|------|
| Maya | 7001 | 通过commandPort通信 |
| 3ds Max | 7002 | 通过socket通信 |
| Blender | 7003 | 通过socket通信 |

## 文档

- **用户指南**: [docs/美术人员使用指南.md](./docs/美术人员使用指南.md)
- **归档文档**: [docs/归档文档/](./docs/归档文档/) - 包含研究报告和历史文档

## 许可证

MIT License