@echo off
cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 使用pythonw启动GUI程序（无终端窗口）
start "" pythonw "%~dp0src\gui\lightweight_manager.py"
