@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

title BoboBill 一键启动

echo ==========================================
echo   BoboBill 一键启动脚本
echo ==========================================
echo.

rem ---- 1. 检查 Python ----
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Python 未安装，尝试自动安装...
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements >nul 2>&1
        if !errorlevel! equ 0 (
            echo [INFO] Python 安装完成，请重新运行本脚本。
        ) else (
            echo [ERROR] 自动安装失败，请手动安装 Python https://www.python.org/downloads/
        )
        pause
        exit /b 1
    ) else (
        echo [ERROR] 未检测到 winget，请手动安装 Python https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%i in ('python --version 2^>nul') do echo [INFO] %%i
)

rem ---- 2. 检查 Node.js ----
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Node.js 未安装，尝试自动安装...
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements >nul 2>&1
        if !errorlevel! equ 0 (
            echo [INFO] Node.js 安装完成，请重新运行本脚本。
        ) else (
            echo [ERROR] 自动安装失败，请手动安装 Node.js https://nodejs.org/
        )
        pause
        exit /b 1
    ) else (
        echo [ERROR] 未检测到 winget，请手动安装 Node.js https://nodejs.org/
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%i in ('node --version 2^>nul') do echo [INFO] %%i
)

rem ---- 3. 配置后端虚拟环境 ----
echo [3/5] 配置后端 Python 虚拟环境...
cd /d "%BACKEND_DIR%"
set "USE_VENV=1"
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARN] 虚拟环境创建失败，将直接使用系统 Python
        set "USE_VENV=0"
    ) else (
        echo [INFO] 虚拟环境已创建
    )
)
if "!USE_VENV!"=="1" (
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else (
        echo [WARN] 虚拟环境不可用，将直接使用系统 Python
        set "USE_VENV=0"
    )
)

rem ---- 4. 安装后端依赖 ----
echo [4/5] 安装后端 Python 依赖...
pip install -r requirements.txt -q
if %errorlevel% equ 0 (
    echo [INFO] 后端依赖安装完成
) else (
    echo [ERROR] 后端依赖安装失败！
    pause
    exit /b 1
)

rem ---- 5. 安装前端依赖 ----
echo [5/5] 安装前端 Node.js 依赖...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    call npm install
    if !errorlevel! equ 0 (
        echo [INFO] 前端依赖安装完成
    ) else (
        echo [ERROR] 前端依赖安装失败！
        pause
        exit /b 1
    )
) else (
    echo [INFO] 前端依赖已存在，跳过安装
)

echo.
echo ==========================================
echo   所有依赖就绪，启动服务中...
echo ==========================================
echo.

rem ---- 启动后端 ----
echo [INFO] 启动后端服务 (端口 8000)...
cd /d "%BACKEND_DIR%"
if "!USE_VENV!"=="1" (
    start "BoboBill-Backend" /B cmd /c "call venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
) else (
    start "BoboBill-Backend" /B cmd /c "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
)
timeout /t 3 /nobreak >nul

rem ---- 启动前端 ----
echo [INFO] 启动前端服务 (端口 5173)...
cd /d "%FRONTEND_DIR%"
start "BoboBill-Frontend" /B cmd /c "npm run dev -- --host"

echo.
echo ==========================================
echo   后端 API:  http://localhost:8000
echo   前端页面:  http://localhost:5173
echo   API 文档:  http://localhost:8000/docs
echo ==========================================
echo   按任意键停止所有服务
echo ==========================================
echo.

pause >nul

echo [INFO] 正在关闭服务...
taskkill /FI "WINDOWTITLE eq BoboBill-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BoboBill-Frontend*" /F >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo [INFO] 服务已停止
pause
