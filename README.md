# DCC工具和UE引擎工具管理框架

这是一个统一的工具管理框架，用于管理和扩展各种DCC软件（Maya、3ds Max、Blender等）和Unreal Engine的工具插件。

## 核心特性

- **统一管理**：集中管理所有DCC和UE工具插件
- **易扩展性**：支持快速添加新的工具插件
- **自然语言支持**：通过文字描述自动生成工具配置
- **SDD规范**：采用软件设计文档风格的工具规则描述
- **安全可靠**：插件沙箱执行，权限控制

## 快速开始

```bash
# 安装依赖
pip install poetry
poetry install

# 运行测试
poetry run pytest

# 启动框架
poetry run python -m src.main
```

## 文档

详细文档请参考 [docs](./docs) 目录。

## 许可证

MIT License