r"""
UE Script Listener - Auto-execute scripts from external UI

This script monitors a temp directory for pending scripts and executes them automatically.
It uses Unreal's tick mechanism instead of threading to avoid crashes.

Usage:
- Auto-start when UE launches (via init_unreal.py)
- Or manually: py "path/to/ue_script_listener.py"

Commands (in UE Output Log):
- Status: py -c "import ue_script_listener; ue_script_listener.status()"
- Stop: py -c "import ue_script_listener; ue_script_listener.stop()"
- Start: py -c "import ue_script_listener; ue_script_listener.start()"
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# 全局状态
_tick_handle = None
_is_running = False
_last_check_time = 0
_CHECK_INTERVAL = 0.5  # 检查间隔（秒）

# 脚本交换目录
SCRIPT_EXCHANGE_DIR = Path(tempfile.gettempdir()) / "DCC_UE_Scripts"
PENDING_DIR = SCRIPT_EXCHANGE_DIR / "pending"
EXECUTED_DIR = SCRIPT_EXCHANGE_DIR / "executed"
RESULT_DIR = SCRIPT_EXCHANGE_DIR / "results"  # 执行结果目录


def _ensure_directories():
    """确保所需目录存在"""
    SCRIPT_EXCHANGE_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    EXECUTED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def _write_result(script_name: str, success: bool, output: str, error: str = ""):
    """将执行结果写入文件供UI读取"""
    import json
    import time
    
    try:
        # 结果文件名与脚本名对应
        result_file = RESULT_DIR / f"{Path(script_name).stem}.result.json"
        
        result_data = {
            "script": script_name,
            "success": success,
            "output": output,
            "error": error,
            "timestamp": time.time()
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        pass  # 写入失败不影响主流程


def _execute_script(script_path: Path) -> bool:
    """执行单个脚本"""
    import io
    import sys
    
    script_name = script_path.name
    
    # 跳过测试连接文件
    if script_name.startswith("_connection_test_"):
        try:
            script_path.unlink()
        except:
            pass
        return True
    
    try:
        import unreal
        unreal.log(f"[UE Listener] Executing: {script_name}")
    except:
        pass
    
    # 捕获 print 输出
    output_buffer = io.StringIO()
    old_stdout = sys.stdout
    
    success = False
    error_msg = ""
    
    try:
        # 读取脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            script_code = f.read()
        
        # 重定向stdout捕获输出
        sys.stdout = output_buffer
        
        # 执行脚本
        exec_globals = {
            '__name__': '__main__',
            '__file__': str(script_path),
        }
        exec(compile(script_code, str(script_path), 'exec'), exec_globals)
        
        success = True
        
    except Exception as exec_error:
        error_msg = str(exec_error)
        try:
            import unreal
            unreal.log_error(f"[UE Listener] Script error: {exec_error}")
        except:
            pass
    finally:
        # 恢复stdout
        sys.stdout = old_stdout
    
    # 获取捕获的输出
    captured_output = output_buffer.getvalue()
    output_buffer.close()
    
    # 同时输出到UE日志
    if captured_output:
        try:
            import unreal
            for line in captured_output.strip().split('\n'):
                unreal.log(f"[Script] {line}")
        except:
            pass
    
    # 写入结果文件
    _write_result(script_name, success, captured_output, error_msg)
    
    # 记录成功/失败
    try:
        import unreal
        if success:
            unreal.log(f"[UE Listener] Success: {script_name}")
        else:
            unreal.log_error(f"[UE Listener] Failed: {script_name}")
    except:
        pass
    
    # 移动到已执行目录
    try:
        executed_path = EXECUTED_DIR / script_name
        if executed_path.exists():
            executed_path.unlink()
        shutil.move(str(script_path), str(executed_path))
    except:
        try:
            script_path.unlink()
        except:
            pass
    
    return success


def _on_tick(delta_time):
    """Tick回调 - 在UE主线程中执行"""
    global _last_check_time
    
    import time
    current_time = time.time()
    
    # 检查间隔
    if current_time - _last_check_time < _CHECK_INTERVAL:
        return
    
    _last_check_time = current_time
    
    # 检查待执行脚本
    try:
        if not PENDING_DIR.exists():
            return
        
        # 获取待执行脚本
        pending_scripts = list(PENDING_DIR.glob("*.py"))
        
        if pending_scripts:
            # 按时间排序，只处理第一个（避免一次处理太多）
            pending_scripts.sort(key=lambda p: p.stat().st_mtime)
            _execute_script(pending_scripts[0])
            
    except Exception as e:
        try:
            import unreal
            unreal.log_warning(f"[UE Listener] Tick error: {e}")
        except:
            pass


def start():
    """启动监听器"""
    global _tick_handle, _is_running
    
    if _is_running:
        try:
            import unreal
            unreal.log_warning("[UE Listener] Already running")
        except:
            print("[UE Listener] Already running")
        return True
    
    _ensure_directories()
    
    try:
        import unreal
        
        # 使用 register_slate_post_tick_callback 在主线程中执行
        _tick_handle = unreal.register_slate_post_tick_callback(_on_tick)
        _is_running = True
        
        unreal.log("[UE Listener] Started (using Slate tick)")
        unreal.log(f"[UE Listener] Watching: {PENDING_DIR}")
        
        return True
        
    except Exception as e:
        try:
            import unreal
            unreal.log_error(f"[UE Listener] Failed to start: {e}")
        except:
            print(f"[UE Listener] Failed to start: {e}")
        return False


def stop():
    """停止监听器"""
    global _tick_handle, _is_running
    
    if not _is_running:
        return
    
    try:
        import unreal
        
        if _tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(_tick_handle)
            _tick_handle = None
        
        _is_running = False
        unreal.log("[UE Listener] Stopped")
        
    except Exception as e:
        _is_running = False
        try:
            import unreal
            unreal.log_error(f"[UE Listener] Error stopping: {e}")
        except:
            pass


def status():
    """获取监听器状态"""
    global _is_running
    
    pending_count = len(list(PENDING_DIR.glob("*.py"))) if PENDING_DIR.exists() else 0
    
    msg = f"[UE Listener] Status: {'Running' if _is_running else 'Stopped'}"
    msg += f" | Pending: {pending_count}"
    msg += f" | Dir: {PENDING_DIR}"
    
    try:
        import unreal
        unreal.log(msg)
    except:
        print(msg)
    
    return _is_running


def clear_pending():
    """清空待执行脚本"""
    count = 0
    if PENDING_DIR.exists():
        for f in PENDING_DIR.glob("*.py"):
            try:
                f.unlink()
                count += 1
            except:
                pass
    
    try:
        import unreal
        unreal.log(f"[UE Listener] Cleared {count} pending scripts")
    except:
        print(f"[UE Listener] Cleared {count} pending scripts")


def clear_executed():
    """清空已执行脚本"""
    count = 0
    if EXECUTED_DIR.exists():
        for f in EXECUTED_DIR.glob("*"):
            try:
                f.unlink()
                count += 1
            except:
                pass
    
    try:
        import unreal
        unreal.log(f"[UE Listener] Cleared {count} executed scripts")
    except:
        print(f"[UE Listener] Cleared {count} executed scripts")


# ============================================================
# 自动启动
# ============================================================

def _is_in_unreal():
    """检测是否在Unreal Engine环境中"""
    try:
        import unreal
        return True
    except ImportError:
        return False


# 在UE环境中自动启动
if _is_in_unreal():
    start()