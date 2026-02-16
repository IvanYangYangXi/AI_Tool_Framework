# 🎛️ DCC工具管理框架

一个统一的工具管理平台，用于管理DCC软件（Maya、3ds Max、Blender等）和Unreal Engine的工具插件，支持自动化任务调度。

---

## ✨ 核心特性

| 功能 | 说明 |
|------|------|
| 🔌 **插件管理** | 统一管理所有DCC/UE工具插件，支持分组和标签 |
| 🤖 **自动化执行** | 定时、间隔、文件监控、任务链等多种触发方式 |
| 🔗 **DCC连接** | 与Maya、3ds Max、Blender、UE引擎实时通信 |
| 📊 **可视化界面** | 轻量级桌面GUI管理器 |
| 📁 **Git集成** | 版本控制、团队协作、一键更新 |

---

## 🚀 快速开始

### 方式一：使用启动脚本（推荐）

```
双击 启动工具管理器.bat
```

### 方式二：命令行启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动工具管理器
python src/gui/lightweight_manager.py
```

---

## 📁 项目结构

```
AI_Tool_Framework/
├── 📂 src/                         # 源代码
│   ├── 📂 core/                    # 核心模块
│   │   ├── plugin_manager.py       # 插件生命周期管理
│   │   ├── dynamic_loader.py       # 安全动态加载引擎
│   │   ├── config_manager.py       # 配置解析与验证
│   │   ├── permission_system.py    # 权限控制系统
│   │   ├── dcc_plugin_interface.py # DCC插件标准接口
│   │   └── ue_plugin_interface.py  # UE插件标准接口
│   │
│   ├── 📂 gui/                     # 图形界面
│   │   ├── lightweight_manager.py  # 主界面入口
│   │   ├── automation_manager.py   # 自动化任务调度
│   │   ├── automation_dialog.py    # 任务管理对话框
│   │   ├── trigger_config_widget.py# 触发器配置组件
│   │   └── trigger_manager.py      # 触发器类型管理
│   │
│   ├── 📂 plugins/                 # 插件目录
│   │   ├── 📂 dcc/                 # DCC软件插件
│   │   │   ├── maya/               # Maya工具
│   │   │   ├── max/                # 3ds Max工具
│   │   │   └── blender/            # Blender工具
│   │   ├── 📂 ue/                  # Unreal Engine插件
│   │   ├── 📂 other/               # 通用工具
│   │   └── 📂 triggers/            # 触发器定义
│   │
│   └── main.py                     # 命令行演示入口
│
├── 📂 configs/                     # 配置文件
│   ├── tool_groups.json            # 工具分组配置
│   └── local_settings.json         # 本地设置
│
├── 📂 docs/                        # 文档
│   ├── 系统架构与功能说明.md        # 完整架构文档（含流程图）
│   ├── 美术人员使用指南.md          # 用户手册
│   └── 📂 归档文档/                # 历史文档归档
│
├── 启动工具管理器.bat               # Windows启动脚本
├── 启动工具管理器.vbs               # 后台启动（无窗口）
├── requirements.txt                # Python依赖
└── pyproject.toml                  # Poetry配置
```

---

## 🔌 DCC软件连接

| 软件 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Maya | 7001 | TCP Socket | 通过commandPort通信 |
| 3ds Max | 7002 | TCP Socket | Python socket |
| Blender | 7003 | TCP Socket | Python socket |
| Unreal Engine | 30010 | HTTP | Remote Control API |

### Maya 命令端口设置

在Maya脚本编辑器中执行：

```python
import maya.cmds as cmds
if cmds.commandPort(':7001', query=True):
    cmds.commandPort(name=':7001', close=True)
cmds.commandPort(name=':7001', sourceType='python', echoOutput=False)
```

---

## 🤖 自动化系统

支持多种触发器类型：

| 触发器 | 说明 | 示例 |
|--------|------|------|
| ⏰ **定时触发** | 每天/每周固定时间执行 | 每天09:00执行 |
| 🔄 **间隔触发** | 按固定间隔循环执行 | 每5分钟执行一次 |
| 📁 **文件监控** | 文件变化时触发 | 监控fbx文件变化 |
| 🔗 **任务链** | 任务完成后触发下一个 | 导出完成后自动上传 |

### 任务状态

| 状态 | 图标 | 说明 |
|------|------|------|
| waiting | ⏳ | 等待触发 |
| running | ▶️ | 执行中 |
| completed | ✅ | 已完成 |
| paused | ⏸️ | 已暂停 |
| error | ❌ | 执行失败 |

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [系统架构与功能说明](./docs/系统架构与功能说明.md) | 完整架构图、流程图、状态机规则 |
| [美术人员使用指南](./docs/美术人员使用指南.md) | 面向美术的快速上手指南 |
| [AI编程规范](./.codemaker/rules/rules.mdc) | 代码风格、命名规范、接口定义 |

---

## 🔧 开发

### 代码规范

- **命名风格**: snake_case（变量/函数）、PascalCase（类）
- **类型注解**: 所有公共方法必须有类型注解
- **返回格式**: `{"status": "success|error", ...}`

### 添加新插件

1. 在 `src/plugins/dcc/<软件>/` 下创建目录
2. 添加 `config.json` 配置文件
3. 添加 `plugin.py` 实现 `execute()` 方法

详见 [AI编程规范](./.codemaker/rules/rules.mdc)

---

## 📄 许可证

MIT License

---

*版本 2.0.0 | 更新日期: 2026-02-16*