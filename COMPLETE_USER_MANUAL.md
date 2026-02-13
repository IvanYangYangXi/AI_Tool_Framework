# DCC工具框架完整使用手册

## 🎯 框架概述

DCC工具框架是一个专业的数字内容创作工具管理平台，为DCC艺术家和技术人员提供统一的插件管理、脚本部署和工作流优化解决方案。

## 🚀 快速开始

### 1. 启动框架管理器
```bash
python framework_manager.py
```

### 2. 选择使用方式
- **选项1**: 启动增强版图形界面（推荐）
- **选项2**: 使用命令行界面
- **选项3**: 管理脚本和插件
- **选项4**: 配置用户设置

## 🎨 Maya网格清理工具使用指南

### 直接在Maya中使用
```python
# Maya脚本编辑器中运行
import sys
sys.path.append(r"C:\Users\yangjili\.lingma\worktree\AI_Tool_Framework\HZ0vaV\src\plugins\dcc\maya\mesh_cleaner")
from plugin import MayaMeshCleaner

cleaner = MayaMeshCleaner()

# 选择网格对象后执行
result = cleaner.execute(
    tolerance=0.001,        # 顶点合并容差
    delete_duplicates=True, # 删除重复顶点
    merge_vertices=True,    # 合并接近顶点
    optimize_normals=True   # 优化法线
)
print("清理结果:", result)
```

### 创建Maya工具架快捷按钮
```python
# 在Maya中运行此代码创建永久按钮
import sys
import maya.cmds as cmds

framework_path = r"C:\Users\yangjili\.lingma\worktree\AI_Tool_Framework\HZ0vaV"
sys.path.append(framework_path + "/src/plugins/dcc/maya/mesh_cleaner")

def run_mesh_cleaner():
    from plugin import MayaMeshCleaner
    cleaner = MayaMeshCleaner()
    result = cleaner.execute(tolerance=0.001)
    print("网格清理完成:", result['summary'])

# 创建工具架按钮
if not cmds.shelfLayout('DCC_Tools', exists=True):
    cmds.shelfLayout('DCC_Tools', parent='ShelfLayout')

cmds.shelfButton(
    parent='DCC_Tools',
    command='run_mesh_cleaner()',
    label='网格清理',
    annotation='运行网格清理工具'
)
```

## 📋 支持的工具列表

### DCC工具
- **Maya网格清理工具** - 专业网格优化和清理
- **3ds Max材质转换工具** - 多渲染器材质格式转换
- **Blender网格优化工具** - 网格简化和LOD生成
- **Houdini程序化工具** - (预留扩展)

### 游戏引擎工具
- **UE资产优化工具** - 纹理压缩和资产处理
- **Unity资源管理工具** - (预留扩展)

### 系统工具
- **插件依赖管理器** - 自动处理插件依赖关系
- **插件市场** - 插件浏览、搜索和管理
- **脚本管理器** - 统一的脚本部署和版本控制
- **用户配置系统** - 个性化设置和偏好管理

## ⚙️ 核心功能详解

### 1. 脚本管理功能
```python
from src.core.script_manager import ScriptManager

# 创建管理器
manager = ScriptManager()

# 列出所有脚本
scripts = manager.list_scripts()
for script in scripts:
    print(f"{script['name']} v{script['version']}")

# 部署脚本
result = manager.deploy_script('dcc_maya_MayaMeshCleaner')
if result['success']:
    print("部署成功:", result['message'])

# 打包脚本
package_result = manager.package_script('dcc_maya_MayaMeshCleaner')
```

### 2. 用户配置系统
```python
from src.core.user_config import UserConfiguration

# 创建配置管理器
config = UserConfiguration()

# 设置偏好
config.set_preference('theme', 'dark')
config.set_preference('auto_save', True)

# 工作区配置
config.set_workspace_setting('window_size', [1400, 900])

# 管理收藏插件
config.add_favorite_plugin('maya_mesh_cleaner')
```

### 3. 依赖管理
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

## 🎛️ 图形界面功能

### 增强版GUI特性
- **插件浏览器**: 分类浏览所有可用工具
- **参数配置**: 可视化配置插件运行参数
- **一键运行**: 简单点击执行工具
- **实时日志**: 完整的执行过程记录
- **主题切换**: 支持深色/浅色主题
- **工作区定制**: 可调整的面板布局

### 启动GUI
```bash
# 方法1: 通过管理器启动
python framework_manager.py
# 选择选项1

# 方法2: 直接启动
python src/gui/enhanced_gui.py
```

## 📁 项目结构说明

```
DCC工具框架/
├── src/
│   ├── core/                    # 核心组件
│   │   ├── dcc_plugin_interface.py    # DCC插件接口
│   │   ├── ue_plugin_interface.py     # UE插件接口
│   │   ├── dependency_manager.py      # 依赖管理器
│   │   ├── plugin_market.py           # 插件市场
│   │   ├── script_manager.py          # 脚本管理器
│   │   └── user_config.py             # 用户配置系统
│   │
│   ├── plugins/                 # 插件目录
│   │   ├── dcc/                 # DCC工具插件
│   │   │   ├── maya/            # Maya工具
│   │   │   ├── max/             # 3ds Max工具
│   │   │   └── blender/         # Blender工具
│   │   └── ue/                  # UE引擎插件
│   │
│   └── gui/                     # 图形界面
│       ├── main_window.py       # 基础GUI
│       └── enhanced_gui.py      # 增强版GUI
│
├── installers/                  # 安装脚本
│   └── maya_installer.py        # Maya自动安装器
│
├── framework_manager.py         # 综合管理器
├── verification.py              # 框架验证工具
├── simple_launcher.py           # 简易启动器
└── HOW_TO_USE.md               # 使用说明文档
```

## 🔧 开发者指南

### 创建新插件模板
```python
from src.core.dcc_plugin_interface import DCCPluginInterface, dcc_plugin

@dcc_plugin(
    name="MyNewTool",
    version="1.0.0",
    dcc=DCCSoftware.MAYA,
    min_version="2022"
)
class MyNewTool(DCCPluginInterface):
    PLUGIN_DESCRIPTION = "我的新工具描述"
    PLUGIN_AUTHOR = "开发者姓名"
    
    def execute(self, **kwargs):
        # 实现主要功能
        pass
    
    def get_info(self):
        # 返回插件信息
        return super().get_info()
```

### 配置文件格式
```json
{
  "plugin": {
    "name": "插件名称",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "作者",
    "type": "dcc",
    "target_dcc": "maya"
  },
  "parameters": {
    "param1": {
      "type": "float",
      "default": 0.001,
      "min": 0.0001,
      "max": 1.0
    }
  }
}
```

## 🛠️ 故障排除

### 常见问题解决方案

1. **导入错误**
   ```python
   # 确保路径正确
   import sys
   sys.path.append("正确的框架路径")
   ```

2. **Maya环境问题**
   - 确认在Maya脚本编辑器中运行
   - 检查Maya版本兼容性（2022-2025）

3. **权限问题**
   - 确保对框架目录有读写权限
   - Windows下以管理员身份运行

4. **GUI显示问题**
   ```bash
   # 尝试不同的GUI后端
   pip install PySide2  # 或 PyQt5
   ```

## 📊 性能优化建议

### 大型项目处理
- 使用批量处理模式
- 调整参数以平衡质量和性能
- 启用日志记录以便追踪问题

### 系统要求
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python版本**: 3.7+
- **内存**: 建议8GB以上
- **存储**: 至少2GB可用空间

## 🤝 技术支持

### 获取帮助
- 查看各插件的README文档
- 运行`verification.py`检查框架状态
- 使用框架管理器的问题诊断功能

### 反馈和建议
- 通过框架内的反馈系统提交
- 联系开发团队获取技术支持

---
*DCC工具框架 - 让数字创作更加高效便捷*