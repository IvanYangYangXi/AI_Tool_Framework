# IDE集成开发指南

## 概述

本文档详细介绍如何在VSCode和Lingma环境中高效开发和调试DCC/UE工具。

## VSCode集成

### 1. 扩展安装

#### 自动安装
```bash
# 在项目根目录执行
cd ide_integration/vscode_extension
npm install
npm run compile
```

#### 手动安装
1. 打开VSCode
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 "Extensions: Install from VSIX"
4. 选择编译好的 `.vsix` 文件

### 2. 功能特性

#### 命令面板功能
- `Create DCC/UE Tool from Description` - 通过自然语言创建工具
- `Generate SDD Config from Selection` - 选中文本生成SDD配置
- `Validate Current Tool` - 验证当前工具代码质量
- `Run Current Tool` - 运行当前工具
- `Debug Tool` - 调试工具

#### 右键菜单
- 在编辑器中选中文本 → `Generate SDD Config`
- 在文件夹上右键 → `Validate Tool`

#### 侧边栏视图
- **Tools Explorer** - 工具资源管理器
- **AI Assistant** - AI助手面板

### 3. 配置设置

在VSCode设置中配置：

```json
{
    "dccue.aiProvider": "openai",
    "dccue.apiKey": "your-api-key",
    "dccue.defaultOutputDir": "./generated_tools",
    "dccue.enableAutoValidation": true
}
```

### 4. 调试配置

扩展自动创建以下调试配置：

```json
{
    "name": "DCC/UE Tool Debug",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/src/main.py",
    "console": "integratedTerminal"
}
```

## Lingma智能助手集成

### 1. 服务启动

```bash
cd ide_integration/lingma_assistant
npm install
npm start
```

服务将在 `http://localhost:3000` 启动

### 2. 功能特性

#### 实时工具生成
```javascript
// Socket.IO 客户端示例
const socket = io('http://localhost:3000');

socket.emit('generate-tool', {
    description: '创建一个网格清理工具',
    options: {
        type: 'dcc',
        platform: 'maya'
    }
});

socket.on('generation-progress', (data) => {
    console.log('生成进度:', data.message);
});

socket.on('generation-complete', (result) => {
    console.log('工具生成完成:', result);
});
```

#### 代码智能分析
- 实时代码质量检查
- 复杂度分析
- 最佳实践建议
- 安全性扫描

#### 交互式调试
- 断点管理
- 变量监视
- 调用栈跟踪
- 实时表达式求值

### 3. API接口

#### 工具生成API
```bash
POST /api/generate
Content-Type: application/json

{
    "description": "工具描述",
    "options": {
        "type": "dcc|ue_engine|utility",
        "output_dir": "./generated_tools"
    }
}
```

#### 代码分析API
```bash
POST /api/analyze
Content-Type: application/json

{
    "code": "Python代码",
    "file_path": "文件路径"
}
```

## 开发工具套件

### 1. 环境设置

```bash
python ide_integration/dev_tools/dev_toolkit.py setup
```

这将：
- 创建开发目录结构
- 安装开发依赖
- 配置VSCode调试环境
- 生成模板文件

### 2. 模板创建

```bash
python ide_integration/dev_tools/dev_toolkit.py create-template --name MyTool --type dcc
```

生成的模板包含：
```
MyTool_dev/
├── plugin.py              # 插件主文件
├── main.py                # 执行入口
├── mytool_tool.py         # 工具类
├── test_mytool.py         # 测试用例
├── requirements.txt       # 依赖文件
├── README.md             # 开发文档
└── .vscode/              # VSCode配置
    └── launch.json
```

### 3. 测试运行

```bash
# 运行所有测试
python ide_integration/dev_tools/dev_toolkit.py test

# 运行特定工具测试
python ide_integration/dev_tools/dev_toolkit.py test --path ./generated_tools/MyTool

# 生成覆盖率报告
python -m pytest --cov=src --cov-report=html
```

### 4. 调试会话

```bash
# 启动调试
python ide_integration/dev_tools/dev_toolkit.py debug --path ./generated_tools/MyTool/main.py --port 5678

# VSCode中连接调试器
# 配置: Python: Remote Attach
# 主机: localhost
# 端口: 5678
```

### 5. 代码质量分析

```bash
python ide_integration/dev_tools/dev_toolkit.py analyze --path ./src/core
```

分析内容包括：
- Flake8 代码规范检查
- Black 代码格式化检查
- Mypy 类型注解检查
- 安全性扫描

## 开发工作流

### 1. 新工具开发流程

```mermaid
graph LR
    A[需求分析] --> B[VSCode创建模板]
    B --> C[实现核心功能]
    C --> D[编写测试用例]
    D --> E[本地测试]
    E --> F[代码质量检查]
    F --> G[调试优化]
    G --> H[集成到框架]
    H --> I[最终验证]
```

### 2. 日常开发循环

1. **编码** - 在VSCode中开发
2. **实时验证** - 保存时自动检查
3. **测试** - 一键运行测试
4. **调试** - 断点调试问题
5. **优化** - 根据建议改进

### 3. 团队协作

#### Git钩子配置
```bash
# pre-commit 钩子
#!/bin/bash
python ide_integration/dev_tools/dev_toolkit.py analyze --path src/
python -m pytest tests/
```

#### CI/CD集成
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python ide_integration/dev_tools/dev_toolkit.py test
      - name: Code quality check
        run: |
          python ide_integration/dev_tools/dev_toolkit.py analyze --path src/
```

## 高级功能

### 1. 自定义代码片段

在VSCode中创建自定义片段：

```json
{
    "DCC Plugin": {
        "prefix": "dccplugin",
        "body": [
            "\"\"\"",
            "$1 - $2",
            "\"\"\"",
            "",
            "PLUGIN_NAME = \"$1\"",
            "PLUGIN_VERSION = \"1.0.0\"",
            "PLUGIN_TYPE = \"dcc\"",
            "PLUGIN_DESCRIPTION = \"$2\"",
            "PLUGIN_AUTHOR = \"${3:Author}\"",
            "",
            "def execute(**kwargs):",
            "    \"\"\"执行函数\"\"\"",
            "    pass",
            "",
            "def register():",
            "    \"\"\"注册函数\"\"\"",
            "    return {",
            "        \"name\": PLUGIN_NAME,",
            "        \"version\": PLUGIN_VERSION,",
            "        \"execute\": execute",
            "    }"
        ],
        "description": "DCC插件模板"
    }
}
```

### 2. 任务自动化

创建VSCode任务：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Generate Tool",
            "type": "shell",
            "command": "python",
            "args": [
                "ide_integration/dev_tools/dev_toolkit.py",
                "create-template",
                "--name", "${input:toolName}",
                "--type", "${input:toolType}"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always"
            }
        }
    ],
    "inputs": [
        {
            "id": "toolName",
            "type": "promptString",
            "description": "工具名称"
        },
        {
            "id": "toolType",
            "type": "pickString",
            "description": "工具类型",
            "options": ["dcc", "ue_engine", "utility"]
        }
    ]
}
```

### 3. 远程开发

配置远程开发环境：

```json
// .devcontainer/devcontainer.json
{
    "name": "DCC/UE Tool Development",
    "image": "python:3.8",
    "extensions": [
        "ms-python.python",
        "ms-python.debugpy",
        "redhat.vscode-yaml"
    ],
    "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
    },
    "postCreateCommand": "pip install -r requirements.txt && python ide_integration/dev_tools/dev_toolkit.py setup"
}
```

## 故障排除

### 常见问题

1. **扩展无法加载**
   ```bash
   # 检查Node.js版本
   node --version  # 需要 >= 14.0
   
   # 重新编译扩展
   cd ide_integration/vscode_extension
   npm run compile
   ```

2. **调试连接失败**
   ```bash
   # 检查端口占用
   netstat -an | grep 5678
   
   # 重启调试服务
   killall python
   python -m debugpy --listen 5678 main.py
   ```

3. **AI服务调用失败**
   ```bash
   # 检查API密钥配置
   echo $OPENAI_API_KEY
   
   # 测试网络连接
   curl https://api.openai.com/v1/models
   ```

### 日志查看

```bash
# VSCode扩展日志
code --log trace

# Python调试日志
export DEBUGPY_LOG_DIR=./logs
python -m debugpy --log-to ./logs main.py

# 开发工具日志
tail -f dev_tools.log
```

## 最佳实践

### 1. 代码组织
```
src/
├── core/                 # 核心框架
├── ai_nlp/              # AI组件
├── plugins/             # 插件示例
└── utils/               # 工具函数

generated_tools/
├── tool_name_dev/       # 开发模板
└── tool_name_final/     # 最终版本

tests/
├── unit/                # 单元测试
├── integration/         # 集成测试
└── performance/         # 性能测试
```

### 2. 版本控制
```gitignore
# .gitignore
*.pyc
__pycache__/
.vscode/
logs/
*.log
.env
debug_sessions/
```

### 3. 文档维护
- 每个工具都有README.md
- API文档使用Sphinx生成
- 示例代码包含详细注释
- 变更日志及时更新

这套完整的IDE集成方案让DCC/UE工具开发变得更加高效和专业化！