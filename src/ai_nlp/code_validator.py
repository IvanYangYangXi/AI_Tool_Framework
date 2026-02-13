"""
代码验证器 - 验证生成的工具代码质量和正确性
"""

import ast
import logging
import subprocess
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeValidator:
    """
    代码验证器
    负责验证生成的Python代码的质量和正确性
    """
    
    def __init__(self):
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        验证单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证结果字典
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "valid": False,
                    "error": f"文件不存在: {file_path}",
                    "issues": []
                }
            
            content = path.read_text(encoding='utf-8')
            
            # 根据文件类型选择验证方法
            if path.suffix == '.py':
                return self._validate_python_file(content, file_path)
            elif path.suffix in ['.yaml', '.yml']:
                return self._validate_yaml_file(content, file_path)
            elif path.suffix == '.md':
                return self._validate_markdown_file(content, file_path)
            else:
                return self._validate_generic_file(content, file_path)
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "issues": []
            }
    
    def _validate_python_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """验证Python文件"""
        issues = []
        valid = True
        
        # 1. 语法检查
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "line": e.lineno,
                "message": f"语法错误: {e.msg}",
                "severity": "critical"
            })
            valid = False
        
        # 2. 基本结构检查
        structure_issues = self._check_python_structure(content, file_path)
        issues.extend(structure_issues)
        
        # 3. 代码质量检查
        quality_issues = self._check_code_quality(content, file_path)
        issues.extend(quality_issues)
        
        # 4. 插件规范检查
        plugin_issues = self._check_plugin_convention(content, file_path)
        issues.extend(plugin_issues)
        
        # 更新有效性状态
        critical_issues = [issue for issue in issues if issue.get('severity') == 'critical']
        if critical_issues:
            valid = False
        
        return {
            "valid": valid,
            "file": file_path,
            "language": "python",
            "issues": issues,
            "metrics": self._calculate_metrics(content)
        }
    
    def _check_python_structure(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查Python文件结构"""
        issues = []
        lines = content.split('\n')
        
        # 检查必需的插件元素
        required_elements = {
            'PLUGIN_NAME': '插件名称常量',
            'PLUGIN_VERSION': '插件版本常量',
            'PLUGIN_TYPE': '插件类型常量',
            'execute': '执行函数',
            'register': '注册函数'
        }
        
        # 对于插件文件的特殊检查
        if 'plugin.py' in file_path.lower():
            for element, description in required_elements.items():
                if element not in content:
                    issues.append({
                        "type": "missing_element",
                        "message": f"缺少必需元素: {element} ({description})",
                        "severity": "warning"
                    })
        
        # 检查编码声明
        if not any('coding' in line.lower() for line in lines[:3]):
            issues.append({
                "type": "encoding",
                "message": "建议添加编码声明: # -*- coding: utf-8 -*-",
                "severity": "info"
            })
        
        # 检查模块文档字符串
        if content.strip() and not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            issues.append({
                "type": "docstring",
                "message": "建议添加模块级文档字符串",
                "severity": "info"
            })
        
        return issues
    
    def _check_code_quality(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查代码质量"""
        issues = []
        
        # 检查行长
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    "type": "line_length",
                    "line": i,
                    "message": f"行长度超过120字符 ({len(line)} chars)",
                    "severity": "info"
                })
        
        # 检查缩进一致性
        indent_issues = self._check_indentation(lines)
        issues.extend(indent_issues)
        
        # 检查命名约定
        naming_issues = self._check_naming_conventions(content)
        issues.extend(naming_issues)
        
        # 检查异常处理
        exception_issues = self._check_exception_handling(content)
        issues.extend(exception_issues)
        
        return issues
    
    def _check_indentation(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查缩进一致性"""
        issues = []
        expected_indent = 4  # 期望4个空格缩进
        
        for i, line in enumerate(lines, 1):
            if line.strip():  # 跳过空行
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % expected_indent != 0 and leading_spaces > 0:
                    issues.append({
                        "type": "indentation",
                        "line": i,
                        "message": f"缩进不一致: {leading_spaces}个空格",
                        "severity": "warning"
                    })
        
        return issues
    
    def _check_naming_conventions(self, content: str) -> List[Dict[str, Any]]:
        """检查命名约定"""
        issues = []
        
        # 检查常量命名（全大写）
        constants = ['PLUGIN_NAME', 'PLUGIN_VERSION', 'PLUGIN_TYPE', 'PLUGIN_DESCRIPTION']
        for const in constants:
            pattern = f"{const}\\s*=\\s*[\"'][^\"']+[\"']"
            if const in content:
                # 这里可以添加更详细的检查逻辑
                pass
        
        # 检查函数命名（小写加下划线）
        # 可以使用正则表达式进行更复杂的检查
        
        return issues
    
    def _check_exception_handling(self, content: str) -> List[Dict[str, Any]]:
        """检查异常处理"""
        issues = []
        
        # 检查是否有适当的异常处理
        if 'try:' in content and 'except' not in content:
            issues.append({
                "type": "exception_handling",
                "message": "发现try语句但缺少except子句",
                "severity": "warning"
            })
        
        # 检查裸露的except
        if 'except:' in content and 'except Exception:' not in content:
            issues.append({
                "type": "bare_except",
                "message": "发现裸露的except子句，建议捕获具体异常",
                "severity": "warning"
            })
        
        return issues
    
    def _check_plugin_convention(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查插件约定"""
        issues = []
        
        if 'plugin.py' in file_path.lower():
            # 检查execute函数签名
            if 'def execute(' in content:
                if '**kwargs' not in content and '*args' not in content:
                    issues.append({
                        "type": "function_signature",
                        "message": "execute函数应该接受**kwargs参数",
                        "severity": "warning"
                    })
            
            # 检查返回值结构
            if 'return' in content:
                # 可以添加更复杂的返回值检查
                pass
            
            # 检查必需的常量值
            plugin_types = ['dcc', 'ue_engine', 'utility']
            if 'PLUGIN_TYPE' in content:
                has_valid_type = any(ptype in content for ptype in plugin_types)
                if not has_valid_type:
                    issues.append({
                        "type": "plugin_type",
                        "message": f"PLUGIN_TYPE应该是以下之一: {', '.join(plugin_types)}",
                        "severity": "warning"
                    })
        
        return issues
    
    def _validate_yaml_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """验证YAML文件"""
        issues = []
        valid = True
        
        try:
            import yaml
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append({
                "type": "yaml_error",
                "message": f"YAML语法错误: {str(e)}",
                "severity": "critical"
            })
            valid = False
        
        return {
            "valid": valid,
            "file": file_path,
            "language": "yaml",
            "issues": issues
        }
    
    def _validate_markdown_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """验证Markdown文件"""
        issues = []
        valid = True
        
        # 基本的Markdown检查
        if not content.strip():
            issues.append({
                "type": "empty_file",
                "message": "文件为空",
                "severity": "info"
            })
        
        # 检查基本结构
        if '#' not in content:
            issues.append({
                "type": "structure",
                "message": "缺少标题",
                "severity": "info"
            })
        
        return {
            "valid": valid,
            "file": file_path,
            "language": "markdown",
            "issues": issues
        }
    
    def _validate_generic_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """验证通用文件"""
        return {
            "valid": True,
            "file": file_path,
            "language": "generic",
            "issues": [],
            "size": len(content)
        }
    
    def _calculate_metrics(self, content: str) -> Dict[str, Any]:
        """计算代码指标"""
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
            "functions": content.count('def '),
            "classes": content.count('class ')
        }
    
    def validate_project(self, project_dir: str) -> Dict[str, Any]:
        """
        验证整个项目
        
        Args:
            project_dir: 项目目录路径
            
        Returns:
            项目验证结果
        """
        project_path = Path(project_dir)
        if not project_path.exists():
            return {
                "valid": False,
                "error": f"项目目录不存在: {project_dir}",
                "files": []
            }
        
        results = []
        total_valid = 0
        total_files = 0
        
        # 遍历所有文件
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                total_files += 1
                result = self.validate_file(str(file_path))
                results.append(result)
                if result['valid']:
                    total_valid += 1
        
        # 计算总体统计
        critical_issues = sum(
            len([issue for issue in result['issues'] if issue.get('severity') == 'critical'])
            for result in results
        )
        
        return {
            "valid": critical_issues == 0,
            "summary": {
                "total_files": total_files,
                "valid_files": total_valid,
                "invalid_files": total_files - total_valid,
                "critical_issues": critical_issues
            },
            "files": results
        }
    
    def get_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """
        生成验证报告
        
        Args:
            validation_result: 验证结果
            
        Returns:
            格式化的报告字符串
        """
        if 'summary' in validation_result:
            # 项目级报告
            summary = validation_result['summary']
            report = f"""项目验证报告
{'='*50}
总文件数: {summary['total_files']}
有效文件: {summary['valid_files']}
无效文件: {summary['invalid_files']}
严重问题: {summary['critical_issues']}

状态: {'✓ 通过' if validation_result['valid'] else '✗ 失败'}
"""
            
            # 添加文件详情
            if summary['invalid_files'] > 0:
                report += "\n无效文件详情:\n"
                for result in validation_result['files']:
                    if not result['valid']:
                        report += f"- {result['file']}: {len(result['issues'])} 个问题\n"
            
            return report
        else:
            # 单文件报告
            report = f"""文件验证报告: {validation_result['file']}
{'='*50}
语言: {validation_result['language']}
状态: {'✓ 有效' if validation_result['valid'] else '✗ 无效'}

问题列表:
"""
            
            for issue in validation_result['issues']:
                severity = issue.get('severity', 'info')
                line_info = f"(第{issue.get('line', '?')}行) " if 'line' in issue else ""
                report += f"- [{severity.upper()}] {line_info}{issue['message']}\n"
            
            if 'metrics' in validation_result:
                metrics = validation_result['metrics']
                report += f"\n代码指标:\n"
                report += f"- 总行数: {metrics['total_lines']}\n"
                report += f"- 代码行: {metrics['code_lines']}\n"
                report += f"- 函数数: {metrics['functions']}\n"
                report += f"- 类数: {metrics['classes']}\n"
            
            return report


# 测试代码
if __name__ == "__main__":
    validator = CodeValidator()
    
    # 测试Python代码验证
    test_code = '''
"""
测试插件
"""

PLUGIN_NAME = "TestPlugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "utility"

def execute(**kwargs):
    """执行函数"""
    try:
        print("执行测试插件")
        return {"status": "success"}
    except Exception as e:
        print(f"错误: {e}")
        return {"status": "error"}

def register():
    """注册函数"""
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION
    }
'''
    
    result = validator.validate_file_content(test_code, "test_plugin.py")
    print(validator.get_validation_report(result))