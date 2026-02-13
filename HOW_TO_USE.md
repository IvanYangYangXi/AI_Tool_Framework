# DCC工具框架使用说明

## 快速开始

### 1. 验证框架完整性
```bash
python verification.py
```

### 2. Maya网格清理工具使用方法

**在Maya脚本编辑器中运行:**
```python
# 添加框架路径
import sys
framework_path = r"C:\Users\yangjili\.lingma\worktree\AI_Tool_Framework\HZ0vaV"
sys.path.append(framework_path + "/src/plugins/dcc/maya/mesh_cleaner")

# 导入并使用工具
from plugin import MayaMeshCleaner
cleaner = MayaMeshCleaner()

# 查看工具信息
info = cleaner.get_info()
print("工具名称:", info['name'])
print("版本:", info['version'])

# 使用工具（需先在Maya中选择网格对象）
result = cleaner.execute(
    tolerance=0.001,        # 顶点合并容差
    delete_duplicates=True, # 删除重复顶点
    merge_vertices=True,    # 合并接近顶点
    optimize_normals=True,  # 优化法线
    preserve_uvs=True       # 保持UV坐标
)

print("执行结果:", result)
```

### 3. 创建Maya工具架按钮

```python
# 在Maya脚本编辑器中运行此代码创建快捷按钮
import sys
import maya.cmds as cmds

framework_path = r"C:\Users\yangjili\.lingma\worktree\AI_Tool_Framework\HZ0vaV"
sys.path.append(framework_path + "/src/plugins/dcc/maya/mesh_cleaner")

def run_mesh_cleaner():
    from plugin import MayaMeshCleaner
    cleaner = MayaMeshCleaner()
    result = cleaner.execute(
        tolerance=0.001,
        delete_duplicates=True,
        merge_vertices=True,
        optimize_normals=True
    )
    print("清理完成:", result['summary'])

# 创建工具架按钮
if not cmds.shelfLayout('DCC_Tools', exists=True):
    cmds.shelfLayout('DCC_Tools', parent='ShelfLayout')

cmds.shelfButton(
    parent='DCC_Tools',
    command='run_mesh_cleaner()',
    label='网格清理',
    annotation='运行网格清理工具',
    imageOverlayLabel='Clean'
)
```

### 4. 常用参数设置

**精细清理（高质量）:**
```python
result = cleaner.execute(
    tolerance=0.0001,    # 更严格的容差
    delete_duplicates=True,
    merge_vertices=True,
    optimize_normals=True
)
```

**快速清理（高性能）:**
```python
result = cleaner.execute(
    tolerance=0.01,      # 更宽松的容差
    delete_duplicates=True,
    merge_vertices=False, # 跳过顶点合并
    optimize_normals=False # 跳过法线优化
)
```

## 支持的工具

### DCC工具
- **Maya网格清理工具** - 删除重复顶点，优化网格拓扑
- **3ds Max材质转换工具** - 多渲染器间材质格式转换
- **Blender网格优化工具** - 网格简化和LOD生成
- **UE资产优化工具** - 纹理压缩和资产处理

### 系统工具
- **依赖管理器** - 插件依赖关系分析
- **插件市场** - 插件浏览和管理

## 文件结构
```
框架目录/
├── src/
│   ├── core/                    # 核心组件
│   ├── plugins/                 # 插件目录
│   │   ├── dcc/                 # DCC工具
│   │   │   ├── maya/            # Maya工具
│   │   │   ├── max/             # 3ds Max工具
│   │   │   └── blender/         # Blender工具
│   │   └── ue/                  # UE工具
│   └── gui/                     # 图形界面
├── installers/                  # 安装脚本
└── verification.py              # 框架验证脚本
```

## 故障排除

### 常见问题

1. **导入错误**
   - 确保使用正确的路径分隔符
   - 检查Python路径是否正确添加

2. **Maya环境问题**
   - 确认在Maya脚本编辑器中运行
   - 检查Maya版本兼容性（支持2022-2025）

3. **权限问题**
   - 确保对框架目录有读取权限
   - 以管理员身份运行Maya（如需要）

### 获取帮助
- 查看各插件目录下的README.md文件
- 运行verification.py检查框架状态
- 查看插件的get_info()方法获取详细信息

## 开发者信息
- 框架版本: 1.0.0
- 支持平台: Windows, macOS, Linux
- Python要求: 3.7+
- 开发团队: DCC Tool Framework Team