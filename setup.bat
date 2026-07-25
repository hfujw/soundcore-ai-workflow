@echo off
REM ============================================================
REM 一键环境安装脚本（Windows）
REM 作用：创建虚拟环境 + 安装全部依赖 + 下载Playwright浏览器
REM 后面两个开发者只要运行这个脚本一次，环境就完全一致
REM ============================================================

echo ========================================
echo   环境安装中...
echo ========================================

REM 第1步：创建虚拟环境（在项目文件夹内，不污染系统）
echo [1/3] 创建虚拟环境...
python -m venv env

REM 第2步：激活虚拟环境 + 安装Python包
echo [2/3] 安装Python依赖...
call env\Scripts\activate
pip install -r requirements.txt

REM 第3步：下载Chromium浏览器（Playwright需要，自动下载到项目内）
echo [3/3] 下载 Chromium 浏览器...
python -m playwright install chromium

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
