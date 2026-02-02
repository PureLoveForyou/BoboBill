@echo off
:: 定位到脚本所在目录下的 frontend 文件夹
cd /d "%~dp0frontend"

:: 安装依赖并启动，加上 --host 参数允许外部/局域网访问
npm install && npm run dev -- --host
