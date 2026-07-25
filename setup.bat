@echo off
chcp 65001 >nul
REM ============================================================
REM 一键环境安装脚本
REM 同学 clone 之后只需要跑一次这个脚本
REM ============================================================

echo ========================================
echo   环境安装中...
echo ========================================

REM 第1步：检查Python版本（需要3.10+）
echo [1/4] 检查 Python...

set PYTHON_EXE=
for %%p in (python3 python) do (
    where %%p >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f "tokens=*" %%v in ('%%p --version 2^>^&1') do set PY_VER=%%v
        echo %%v | find "3.1" >nul 2>&1
        if !ERRORLEVEL! EQU 0 set PYTHON_EXE=%%p
        if !ERRORLEVEL! NEQ 0 (
            echo %%v | find "3.11" >nul && set PYTHON_EXE=%%p
            echo %%v | find "3.12" >nul && set PYTHON_EXE=%%p
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo.
    echo ❌ 未找到 Python 3.10+
    echo.
    echo 请下载 Python 3.10 并安装:
    echo   https://mirrors.huaweicloud.com/python/3.10.11/python-3.10.11-amd64.exe
    echo.
    echo 安装时:
    echo   - 勾选 "Add Python to PATH"
    echo   - 或者安装到: %CD%\python310
    echo.
    pause
    exit /b 1
)

echo   找到: %PYTHON_EXE%
%PYTHON_EXE% --version

REM 第2步：创建虚拟环境
echo.
echo [2/4] 创建虚拟环境...
if exist env\Scripts\python.exe (
    echo   虚拟环境已存在，跳过
) else (
    %PYTHON_EXE% -m venv env
    echo   创建完成
)

REM 第3步：安装 Python 依赖
echo.
echo [3/4] 安装 Python 依赖（使用清华镜像）...
call env\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install crawl4ai -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 第4步：下载 Chromium 浏览器到项目文件夹内
echo.
echo [4/4] 下载 Chromium 浏览器（到项目文件夹内）...
set PLAYWRIGHT_BROWSERS_PATH=%CD%\browsers
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
