#!/bin/bash

# MCP Pytest测试服务器启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python_version() {
    print_info "检查Python版本..."
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
        print_success "Python版本满足要求: $python_version"
    else
        print_error "Python版本过低: $python_version，需要 >= $required_version"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3未安装"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "虚拟环境不存在，正在创建..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    fi
    
    print_success "依赖检查完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装依赖..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip3 install --upgrade pip
    
    # 安装依赖包
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_error "requirements.txt文件不存在"
        exit 1
    fi
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 运行数据库初始化
    python3 -c "
from src.database.connection import init_database
import asyncio

async def init():
    await init_database()
    print('数据库初始化完成')

asyncio.run(init())
"
    
    print_success "数据库初始化完成"
}

# 启动服务器
start_server() {
    print_info "启动MCP Pytest服务器..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 获取参数
    HOST=${1:-0.0.0.0}
    PORT=${2:-8000}
    DEBUG=${3:-false}
    
    print_info "服务器配置:"
    print_info "  - 主机: $HOST"
    print_info "  - 端口: $PORT"
    print_info "  - 调试模式: $DEBUG"
    
    # 设置环境变量
    export MCP_PYTEST_HOST=$HOST
    export MCP_PYTEST_PORT=$PORT
    export MCP_PYTEST_DEBUG=$DEBUG
    
    # 启动服务器
    python3 -m src.main \
        --host "$HOST" \
        --port "$PORT" \
        $( [ "$DEBUG" = "true" ] && echo "--debug" )
}

# 停止服务器
stop_server() {
    print_info "停止服务器..."
    
    # 查找并杀死相关进程
    pids=$(ps aux | grep "src.main" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        for pid in $pids; do
            kill $pid 2>/dev/null && print_info "已停止进程: $pid"
        done
        print_success "服务器已停止"
    else
        print_warning "未找到运行的服务器进程"
    fi
}

# 显示帮助
show_help() {
    echo "MCP Pytest测试服务器管理脚本"
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  start [host] [port] [debug]  启动服务器"
    echo "  stop                         停止服务器"
    echo "  init                         初始化环境"
    echo "  status                       查看服务器状态"
    echo "  help                         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                     # 使用默认配置启动"
    echo "  $0 start localhost 8080 true # 指定配置启动"
    echo "  $0 init                      # 初始化环境"
    echo "  $0 stop                      # 停止服务器"
    echo ""
}

# 检查服务器状态
check_status() {
    print_info "检查服务器状态..."
    
    # 检查进程
    pids=$(ps aux | grep "src.main" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        print_success "服务器正在运行"
        for pid in $pids; do
            print_info "  - 进程ID: $pid"
        done
    else
        print_warning "服务器未运行"
    fi
    
    # 检查端口
    if command -v lsof &> /dev/null; then
        port_status=$(lsof -i :8000 2>/dev/null)
        if [ -n "$port_status" ]; then
            print_info "端口 8000 已被占用"
        else
            print_info "端口 8000 可用"
        fi
    fi
}

# 主函数
main() {
    case "$1" in
        "start")
            check_python_version
            check_dependencies
            install_dependencies
            init_database
            start_server "$2" "$3" "$4"
            ;;
        "stop")
            stop_server
            ;;
        "init")
            check_python_version
            check_dependencies
            install_dependencies
            init_database
            ;;
        "status")
            check_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"