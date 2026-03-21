# MCP Pytest服务器快速开始指南

## 🚀 5分钟快速开始

### 1. 下载和准备
```bash
# 进入项目目录
cd mcp-pytest-server

# 创建虚拟环境（如果还没有）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install fastapi uvicorn pytest requests
```

### 2. 启动简化版服务器
```bash
# 启动服务器
python simple_server.py

# 服务器将在 http://localhost:8000 启动
```

### 3. 快速测试
```bash
# 在新的终端中测试
curl http://localhost:8000/health
# 应该返回: {"status":"healthy"}

# 执行测试
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"test_path":"tests/test_example.py"}'
```

## 🐦 Goose集成（立即使用）

### 方法1: 使用环境变量（最简单）
```bash
# 设置环境变量
export GOOSE_MCP_SERVERS='{
  "pytest_test_server": {
    "command": "python",
    "args": ["simple_server.py"],
    "env": {
      "PYTHONPATH": "'$(pwd)'"
    }
  }
}'

# 启动Goose
goose
```

### 方法2: 使用配置文件
创建 `~/.goose/config.yaml`：
```yaml
mcp_servers:
  pytest_test_server:
    command: "python"
    args: 
      - "simple_server.py"
    env:
      PYTHONPATH: "/完整路径/to/mcp-pytest-server"
```

### 方法3: 使用项目配置
在项目根目录创建 `.goose/config.yaml`：
```yaml
mcp_servers:
  pytest_test_server:
    command: "python"
    args: 
      - "simple_server.py"
    env:
      PYTHONPATH: "."
```

## 💬 在Goose中使用

启动Goose后，你可以直接说：

### 基本命令
- **"执行pytest测试"** - 运行默认测试
- **"运行tests/目录的测试"** - 运行指定目录
- **"查看测试历史"** - 显示最近测试结果
- **"显示测试结果"** - 查看详细结果

### 高级命令
- **"运行tests/test_api.py的测试"** - 运行特定文件
- **"为my-project项目运行测试"** - 指定项目名称
- **"使用-vv选项运行测试"** - 指定pytest选项

## 🔧 完整功能服务器

如果需要完整功能（数据库存储、更多工具等）：

### 1. 安装完整依赖
```bash
# 使用修复后的依赖文件
pip install -r requirements_fixed.txt
```

### 2. 启动完整服务器
```bash
# 需要修复一些导入问题后使用
# python -m src.main
```

## 📊 验证集成

### 检查Goose是否识别MCP服务器
```bash
# 启动Goose后，它会自动显示可用的工具
goose
# 你应该看到类似的信息:
# Connected to MCP server: pytest-test-server
# Available tools: run_pytest_tests, get_test_history
```

### 测试对话示例
```
用户: 执行pytest测试
Goose: 我可以帮你执行pytest测试。请告诉我测试路径，或者使用默认的tests/目录？

用户: 使用默认的
Goose: 正在执行tests/目录下的测试...
（显示测试结果）
```

## 🐛 故障排除

### 常见问题1: Goose找不到MCP服务器
```bash
# 检查服务器是否运行
curl http://localhost:8000/health

# 检查Goose配置
echo $GOOSE_MCP_SERVERS

# 重新启动Goose
goose
```

### 常见问题2: 测试执行失败
```bash
# 手动测试pytest
pytest tests/test_example.py -v

# 检查测试文件是否存在
ls -la tests/
```

### 常见问题3: 导入错误
```bash
# 确保在项目目录中
cd mcp-pytest-server

# 确保虚拟环境激活
source venv/bin/activate

# 检查Python路径
which python
```

## 🎯 快速验证脚本

运行快速验证：
```bash
python quick_test.py
```

运行完整集成测试：
```bash
python goose_integration_test.py
```

## 📁 文件说明

- `simple_server.py` - 简化版服务器，立即可用
- `src/` - 完整功能服务器源代码
- `tests/test_example.py` - 示例测试文件
- `goose_test_config.json` - Goose配置示例
- `quick_test.py` - 快速验证脚本
- `goose_integration_test.py` - 集成测试脚本

## 🆘 获取帮助

1. **查看日志**: 服务器启动时会显示日志
2. **测试连接**: `curl http://localhost:8000/health`
3. **检查工具**: `curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'`
4. **手动测试**: `pytest tests/test_example.py -v`

## 🎉 成功标志

当你可以在Goose中说 **"执行pytest测试"** 并看到测试结果时，集成就成功了！

---

**提示**: 简化版服务器 (`simple_server.py`) 已经包含了所有核心功能，适合快速开始和测试。完整版服务器 (`src/`) 提供了更多高级功能和数据库支持。