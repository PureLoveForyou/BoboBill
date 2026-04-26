#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
    info "正在关闭服务..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

check_command() {
    if ! command -v "$1" &>/dev/null; then
        return 1
    fi
    return 0
}

install_python() {
    warn "Python3 未安装，尝试自动安装..."
    if check_command apt-get; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv
    elif check_command yum; then
        sudo yum install -y -q python3 python3-pip
    elif check_command brew; then
        brew install python3
    else
        error "无法自动安装 Python3，请手动安装后重试。"
        exit 1
    fi
    info "Python3 安装完成"
}

install_node() {
    warn "Node.js 未安装，尝试自动安装..."
    if check_command apt-get; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y -qq nodejs
    elif check_command yum; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo -E bash -
        sudo yum install -y -q nodejs
    elif check_command brew; then
        brew install node@20
    else
        error "无法自动安装 Node.js，请手动安装后重试。"
        exit 1
    fi
    info "Node.js 安装完成"
}

info "========== BoboBill 一键启动脚本 =========="

info "1. 检查 Python3 环境..."
if check_command python3; then
    info "   Python3 $(python3 --version | cut -d' ' -f2)"
else
    install_python
fi

if ! check_command pip3 && ! check_command pip; then
    warn "pip3 未安装，正在安装..."
    python3 -m ensurepip --upgrade || sudo apt-get install -y -qq python3-pip
fi
PIP_CMD=$(check_command pip3 && echo "pip3" || echo "pip")

info "2. 检查 Node.js 环境..."
if check_command node; then
    info "   Node.js $(node --version)"
else
    install_node
fi
if ! check_command npm; then
    error "npm 未安装，请检查 Node.js 安装。"
    exit 1
fi
info "   npm $(npm --version)"

info "3. 配置后端 Python 虚拟环境..."
cd "$BACKEND_DIR"
USE_VENV=true
if [ ! -d "venv" ]; then
    python3 -m venv venv 2>/dev/null || {
        warn "   创建虚拟环境失败，尝试安装 python3-venv..."
        if check_command apt-get; then
            sudo apt-get install -y -qq python3-venv 2>/dev/null
        fi
        python3 -m venv venv 2>/dev/null || {
            warn "   虚拟环境不可用，将使用系统 Python"
            USE_VENV=false
        }
    }
    if [ "$USE_VENV" = true ]; then
        info "   虚拟环境已创建"
    fi
fi

if [ "$USE_VENV" = true ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PIP_CMD="venv/bin/pip"
else
    USE_VENV=false
    warn "   将直接使用系统 Python (不隔离依赖)"
fi

info "4. 安装后端 Python 依赖..."
$PIP_CMD install -r requirements.txt -q
info "   依赖安装完成"

info "5. 安装前端 Node.js 依赖..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    npm install
    info "   依赖安装完成"
else
    info "   依赖已存在，跳过安装"
fi

info "6. 启动后端服务 (端口 8000)..."
cd "$BACKEND_DIR"
if [ "$USE_VENV" = true ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2

if kill -0 "$BACKEND_PID" 2>/dev/null; then
    info "   后端服务已启动 (PID $BACKEND_PID)"
else
    error "   后端服务启动失败！"
    exit 1
fi

info "7. 启动前端服务 (端口 5173)..."
cd "$FRONTEND_DIR"
npm run dev -- --host &
FRONTEND_PID=$!

info ""
info "=========================================="
info "  后端 API:  http://localhost:8000"
info "  前端页面:  http://localhost:5173"
info "  API 文档:  http://localhost:8000/docs"
info "=========================================="
info "  按 Ctrl+C 停止所有服务"
info "=========================================="

wait
