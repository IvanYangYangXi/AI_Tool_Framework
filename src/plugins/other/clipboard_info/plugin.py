"""
剪贴板信息工具 - 获取并打印剪贴板内容

功能：
- 检测剪贴板中的文件路径（复制的文件）
- 检测剪贴板中的文本内容
- 显示剪贴板内容类型和详细信息
"""

import os
import sys
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 插件元信息
PLUGIN_NAME = "剪贴板信息工具"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "other"
PLUGIN_DESCRIPTION = "获取并打印剪贴板中的内容，支持文本和文件列表"
PLUGIN_AUTHOR = "DCC Tool Team"


def get_clipboard_files() -> Optional[List[str]]:
    """
    获取剪贴板中的文件列表（使用PowerShell）
    
    Returns:
        文件路径列表，如果没有文件则返回None
    """
    try:
        # 使用PowerShell获取剪贴板中的文件（设置UTF-8编码输出以支持中文路径）
        ps_script = '''
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
$files = [System.Windows.Forms.Clipboard]::GetFileDropList()
if ($files.Count -gt 0) {
    $files | ForEach-Object { Write-Output $_ }
}
'''
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return files if files else None
        
        return None
        
    except Exception as e:
        logger.error(f"获取剪贴板文件失败: {e}")
        return None


def get_clipboard_text() -> Optional[str]:
    """
    获取剪贴板中的文本内容（使用PowerShell）
    
    Returns:
        文本内容，如果没有文本则返回None
    """
    try:
        # 使用PowerShell获取剪贴板文本（指定UTF-8编码输出）
        ps_script = '''
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
$text = [System.Windows.Forms.Clipboard]::GetText()
if ($text) { Write-Output $text }
'''
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and result.stdout:
            return result.stdout.rstrip('\n')  # 保留内部换行，只去除末尾
        
        return None
        
    except Exception as e:
        logger.error(f"获取剪贴板文本失败: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def execute(**kwargs) -> Dict[str, Any]:
    """
    执行插件主功能
    
    Args:
        show_preview: 是否显示内容预览
        max_files: 最多显示的文件数量
        
    Returns:
        执行结果字典
    """
    show_preview = kwargs.get('show_preview', True)
    max_files = int(kwargs.get('max_files', 50))  # 确保是整数
    
    result = {
        "status": "success",
        "tool": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "clipboard_type": None,
        "content": None,
        "details": {}
    }
    
    output_lines = []
    output_lines.append("=" * 50)
    output_lines.append(f"📋 {PLUGIN_NAME} v{PLUGIN_VERSION}")
    output_lines.append("=" * 50)
    
    # 1. 首先检查是否有文件
    files = get_clipboard_files()
    
    if files:
        result["clipboard_type"] = "files"
        result["content"] = files
        result["details"]["file_count"] = len(files)
        
        output_lines.append(f"\n📁 剪贴板类型: 文件列表")
        output_lines.append(f"📊 文件数量: {len(files)}")
        output_lines.append("")
        
        # 统计信息
        total_size = 0
        file_types = {}
        dirs_count = 0
        files_count = 0
        
        display_files = files[:max_files]
        
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                if path.is_dir():
                    dirs_count += 1
                else:
                    files_count += 1
                    ext = path.suffix.lower() or "(无扩展名)"
                    file_types[ext] = file_types.get(ext, 0) + 1
                    try:
                        total_size += path.stat().st_size
                    except:
                        pass
            else:
                files_count += 1
        
        output_lines.append(f"📂 文件夹: {dirs_count} 个")
        output_lines.append(f"📄 文件: {files_count} 个")
        output_lines.append(f"💾 总大小: {format_file_size(total_size)}")
        
        if file_types:
            output_lines.append(f"\n📑 文件类型统计:")
            for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
                output_lines.append(f"   {ext}: {count} 个")
        
        output_lines.append(f"\n📋 文件列表:")
        output_lines.append("-" * 40)
        
        for i, file_path in enumerate(display_files, 1):
            path = Path(file_path)
            icon = "📂" if path.is_dir() else "📄"
            output_lines.append(f"{i:3}. {icon} {path.name}")
            output_lines.append(f"     路径: {file_path}")
        
        if len(files) > max_files:
            output_lines.append(f"\n... 还有 {len(files) - max_files} 个文件未显示")
        
        result["details"]["dirs_count"] = dirs_count
        result["details"]["files_count"] = files_count
        result["details"]["total_size"] = total_size
        result["details"]["file_types"] = file_types
        
    else:
        # 2. 检查是否有文本
        text = get_clipboard_text()
        
        if text:
            result["clipboard_type"] = "text"
            result["content"] = text
            result["details"]["char_count"] = len(text)
            result["details"]["line_count"] = text.count('\n') + 1
            result["details"]["word_count"] = len(text.split())
            
            output_lines.append(f"\n📝 剪贴板类型: 文本")
            output_lines.append(f"📊 字符数: {len(text)}")
            output_lines.append(f"📊 行数: {result['details']['line_count']}")
            output_lines.append(f"📊 词数: {result['details']['word_count']}")
            
            if show_preview:
                output_lines.append(f"\n📋 内容预览:")
                output_lines.append("-" * 40)
                preview = text[:500]
                if len(text) > 500:
                    preview += f"\n\n... (共 {len(text)} 字符，仅显示前500字符)"
                output_lines.append(preview)
        else:
            result["clipboard_type"] = "empty"
            result["content"] = None
            output_lines.append(f"\n⚠️ 剪贴板为空或不包含支持的格式")
            output_lines.append("支持的格式: 文件列表、文本")
    
    output_lines.append("\n" + "=" * 50)
    
    # 打印输出（处理Windows GBK编码问题）
    output_text = "\n".join(output_lines)
    try:
        # 尝试直接打印
        print(output_text)
    except UnicodeEncodeError:
        # 如果编码失败，使用UTF-8强制输出
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(output_text.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\n')
        else:
            # 备选方案：替换无法编码的字符
            print(output_text.encode('gbk', errors='replace').decode('gbk'))
    
    result["output"] = output_text
    
    return result


# 独立运行测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = execute(show_preview=True, max_files=20)
    print(f"\n返回结果类型: {result['clipboard_type']}")