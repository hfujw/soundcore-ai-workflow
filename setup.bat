@echo off
chcp 65001 >nul
REM ============================================================
REM 一键环境安装脚本
REM 同学 clone 之后只需要跑一次这个脚本
REM ============================================================

echo ========================================
echo   环境安装中...
echo ========================================

REM ── 第1步：检测 Python 3.10+ ──
echo [1/4] 检查 Python...

set PYTHON_EXE=

REM 策略A：试试 python / python3 命令
for %%p in (python3 python) do (
    where %%p >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        %%p --version 2>&1 | findstr "3.1" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set PYTHON_EXE=%%p
            goto :found_python
        )
        %%p --version 2>&1 | findstr "3.11" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set PYTHON_EXE=%%p
        %%p --version 2>&1 | findstr "3.12" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set PYTHON_EXE=%%p
        %%p --version 2>&1 | findstr "3.13" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set PYTHON_EXE=%%p
    )
)

REM 策略B：Windows Apps 别名可能指向商店，检查实际安装
if "%PYTHON_EXE%"=="" (
    REM 尝试 Python Launcher
    where py >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        REM py -3.12 --version 检查；但因chcp 65001导致奇怪行为，直接找安装目录
    )

    REM 直接查找常见的 Python 安装路径
    set "CANDIDATE1=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    set "CANDIDATE2=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    set "CANDIDATE3=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    set "CANDIDATE4=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

    if exist "%CANDIDATE1%" set "PYTHON_EXE=%CANDIDATE1%"
    if exist "%CANDIDATE2%" if "%PYTHON_EXE%"=="" set "PYTHON_EXE=%CANDIDATE2%"
    if exist "%CANDIDATE3%" if "%PYTHON_EXE%"=="" set "PYTHON_EXE=%CANDIDATE3%"
    if exist "%CANDIDATE4%" if "%PYTHON_EXE%"=="" set "PYTHON_EXE=%CANDIDATE4%"
)

REM 策略C：扫描 Program Files / Python 目录
if "%PYTHON_EXE%"=="" (
    for %%d in (%SystemDrive%\Program Files\Python*\python.exe) do (
        if "%PYTHON_EXE%"=="" set "PYTHON_EXE=%%d"
    )
)

:found_python

if "%PYTHON_EXE%"=="" (
    echo.
    echo ❌ 未找到 Python 3.10+
    echo.
    echo 请下载 Python 3.10 并安装:
    echo   https://mirrors.huaweicloud.com/python/3.10.11/python-3.10.11-amd64.exe
    echo.
    echo 安装时:
    echo   - 勾选 "Add Python to PATH"
    echo   - 或者安装到: %LOCALAPPDATA%\Programs\Python\
    echo.
    pause
    exit /b 1
)

echo   找到: %PYTHON_EXE%
%PYTHON_EXE% --version

REM ── 第2步：创建虚拟环境 ──
echo.
echo [2/4] 创建虚拟环境...
if exist env\Scripts\python.exe (
    echo   虚拟环境已存在，跳过
) else (
    %PYTHON_EXE% -m venv env
    echo   创建完成
)

REM ── 第3步：安装 Python 依赖 ──
echo.
echo [3/4] 安装 Python 依赖...
call env\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install crawl4ai -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul || echo   ⚠️ crawl4ai 安装失败（可选依赖，不影响核心功能）

REM ── 第4步：下载 Chromium ──
echo.
echo [4/4] 下载 Chromium 浏览器（到项目文件夹内）...
set PLAYWRIGHT_BROWSERS_PATH=%CD%\browsers
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
python -m playwright install chromium

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 启动后端:
echo   call env\Scripts\activate
echo   cd backend
echo   python main.py
echo.
pause
