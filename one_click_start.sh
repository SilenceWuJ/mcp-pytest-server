#!/bin/bash

# MCP Pytest服务器一键启动脚本
# 这个脚本会自动设置环境并启动所有需要的服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_step() {
    echo -e "${CYAN}▶${NC} $1"
}

# 检查是否在项目目录中
check_project_dir() {
    if [ ! -f "simple_server.py" ] && [ ! -d "src" ]; then
        print_error "请在 mcp-pytest-server 项目目录中运行此脚本"
        exit 1
    fi
    print_success "项目目录检查通过"
}

# 检查Python环境
check_python() {
    print_step "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python版本: $python_version"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "虚拟环境不存在，正在创建..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    print_success "Python环境检查通过"
}

# 安装依赖
install_dependencies() {
    print_step "安装依赖..."
    
    # 检查是否已安装基本依赖
    if ! python3 -c "import fastapi" 2>/dev/null; then
        print_info "安装FastAPI..."
        pip install fastapi uvicorn
    fi
    
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_info "安装pytest..."
        pip install pytest
    fi
    
    if ! python3 -c "import requests" 2>/dev/null; then
        print_info "安装requests..."
        pip install requests
    fi
    
    print_success "依赖安装完成"
}

# 启动MCP服务器
start_mcp_server() {
    print_step "启动MCP服务器..."
    
    # 检查是否已有服务器在运行
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_warning "MCP服务器已经在运行 (端口 8000)"
        return
    fi
    
    # 启动服务器（后台运行）
    python3 simple_server.py > server.log 2>&1 &
    SERVER_PID=$!
    
    # 等待服务器启动
    sleep 3
    
    # 检查服务器是否启动成功
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "MCP服务器启动成功 (PID: $SERVER_PID)"
        print_info "日志文件: server.log"
        print_info "访问地址: http://localhost:8000"
    else
        print_error "MCP服务器启动失败，查看 server.log 获取详情"
        exit 1
    fi
}

# 测试服务器功能
test_server() {
    print_step "测试服务器功能..."
    
    print_info "1. 健康检查..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "健康检查通过"
    else
        print_error "健康检查失败"
        return 1
    fi
    
    print_info "2. 测试MCP协议..."
    response=$(curl -s -X POST http://localhost:8000/mcp \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}')
    
    if echo "$response" | grep -q "run_pytest_tests"; then
        print_success "MCP协议测试通过"
    else
        print_error "MCP协议测试失败"
        return 1
    fi
    
    print_info "3. 测试pytest执行..."
    response=$(curl -s -X POST http://localhost:8000/execute \
        -H "Content-Type: application/json" \
        -d '{"test_path":"tests/test_example.py"}')
    
    if echo "$response" | grep -q "total_tests"; then
        print_success "pytest执行测试通过"
    else
        print_warning "pytest执行测试可能有问题"
    fi
    
    print_success "服务器功能测试完成"
}

# 配置Goose环境
setup_goose() {
    print_step "配置Goose环境..."
    
    # 创建Goose配置文件
    cat > goose_config.yaml << EOF
# Goose MCP配置
mcp_servers:
  pytest_test_server:
    command: "$(which python3)"
    args: 
      - "simple_server.py"
    env:
      PYTHONPATH: "$(pwd)"
EOF
    
    # 创建环境变量配置脚本
    cat > setup_goose_env.sh << EOF
#!/bin/bash
# Goose MCP环境设置脚本

export GOOSE_MCP_SERVERS='{
  "pytest_test_server": {
    "command": "$(which python3)",
    "args": ["simple_server.py"],
    "env": {
      "PYTHONPATH": "$(pwd)"
    }
  }
}'

echo "Goose MCP环境已设置"
echo "现在可以启动Goose: goose"
EOF
    
    chmod +x setup_goose_env.sh
    
    print_success "Goose配置已创建:"
    print_info "  • 配置文件: goose_config.yaml"
    print_info "  • 环境设置脚本: setup_goose_env.sh"
}

# 显示使用指南
show_usage_guide() {
    print_step "使用指南"
    
    echo ""
    echo "🎉 MCP Pytest服务器已准备就绪！"
    echo ""
    echo "📊 服务器状态:"
    echo "  • 地址: http://localhost:8000"
    echo "  • 健康检查: curl http://localhost:8000/health"
    echo "  • 测试执行: curl -X POST http://localhost:8000/execute -H 'Content-Type: application/json' -d '{\"test_path\":\"tests/test_example.py\"}'"
    echo ""
    echo "🐦 Goose集成:"
    echo "  方法1: 使用环境变量"
    echo "    $ source setup_goose_env.sh"
    echo "    $ goose"
    echo ""
    echo "  方法2: 使用配置文件"
    echo "    复制 goose_config.yaml 到 ~/.goose/config.yaml 或项目中的 .goose/config.yaml"
    echo ""
    echo "💬 在Goose中尝试:"
    echo "  • \"执行pytest测试\""
    echo "  • \"运行tests/目录的测试\""
    echo "  • \"查看测试历史\""
    echo ""
    echo "📋 快速测试命令:"
    echo "  $ python quick_test.py          # 快速验证"
    echo "  $ python goose_integration_test.py  # 完整集成测试"
    echo ""
    echo "🛠️  管理命令:"
    echo "  $ pkill -f 'simple_server.py'   # 停止服务器"
    echo "  $ tail -f server.log           # 查看服务器日志"
    echo ""
    echo "📚 更多信息:"
    echo "  • 查看 README.md"
    echo "  • 查看 QUICK_START.md"
    echo "  • 查看 docs/GOOSE_INTEGRATION.md"
}

# 主函数
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║            MCP Pytest服务器一键启动脚本                  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    
    # 执行步骤
    check_project_dir
    check_python
    install_dependencies
    start_mcp_server
    test_server
    setup_goose
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    
    show_usage_guide
    
    # 保存服务器PID
    echo $SERVER_PID > .server_pid
    print_info "服务器PID已保存到 .server_pid"
    
    echo ""
    print_success "✅ 所有设置完成！"
    echo ""
}

# 清理函数
cleanup() {
    if [ -f .server_pid ]; then
        pid=$(cat .server_pid)
        if kill -0 $pid 2>/dev/null; then
            print_info "停止MCP服务器 (PID: $pid)..."
            kill $pid
            rm .server_pid
        fi
    fi
}

# 设置退出时清理
trap cleanup EXIT INT TERM

# 运行主函数
main "$@"