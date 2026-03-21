# Goose 集成指南

本文档介绍如何将 MCP Pytest 测试服务器集成到 Goose 中，使 Goose 能够通过工具调用执行 pytest 测试并将结果存储到数据库。

## 1. 配置 Goose 使用 MCP 服务器

### 1.1 在 Goose 配置中添加 MCP 服务器

编辑 Goose 的配置文件（通常是 `~/.goose/config.yaml` 或项目中的 `.goose/config.yaml`），添加以下内容：

```yaml
# Goose 配置文件
mcp_servers:
  pytest_test_server:
    command: "python"
    args: 
      - "-m"
      - "src.main"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8000"
    env:
      MCP_PYTEST_DATABASE_URL: "sqlite:///./test_results.db"
      MCP_PYTEST_DEBUG: "false"
    # 或者使用启动脚本
    # command: "./start.sh"
    # args: ["start", "0.0.0.0", "8000", "false"]
```

### 1.2 使用环境变量配置

也可以通过环境变量配置：

```bash
export GOOSE_MCP_SERVERS='{
  "pytest_test_server": {
    "command": "python",
    "args": ["-m", "src.main"],
    "env": {
      "MCP_PYTEST_DATABASE_URL": "sqlite:///./test_results.db"
    }
  }
}'
```

## 2. 在 Goose 中使用 MCP 工具

### 2.1 启动 Goose 并连接 MCP 服务器

启动 Goose 时，它会自动连接到配置的 MCP 服务器。你可以通过以下方式验证连接：

```bash
# 启动 Goose
goose

# 在 Goose 会话中，你可以询问可用的工具
# Goose 会自动发现 MCP 服务器提供的工具
```

### 2.2 使用工具执行测试

在 Goose 会话中，你可以直接使用 MCP 工具：

```
用户：执行 pytest 测试

Goose：我可以帮你执行 pytest 测试。请告诉我测试路径：

用户：tests/test_example.py

Goose：正在执行测试...
（Goose 会调用 run_pytest_tests 工具）
```

### 2.3 工具调用示例

Goose 会自动将用户请求转换为工具调用。以下是工具调用的内部流程：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_pytest_tests",
    "arguments": {
      "test_path": "tests/test_example.py",
      "project_name": "my_project",
      "pytest_options": ["-v", "--tb=short"]
    }
  }
}
```

## 3. 工具详细说明

### 3.1 run_pytest_tests - 执行 pytest 测试

**描述**: 执行指定的 pytest 测试并将结果存储到数据库

**参数**:
- `test_path` (必需): 测试路径或文件
- `project_name` (可选): 项目名称，默认为 "default"
- `pytest_options` (可选): pytest 选项列表，默认为 `["-v", "--tb=short"]`
- `environment` (可选): 环境变量字典
- `store_to_db` (可选): 是否存储到数据库，默认为 true

**示例用法**:
```
用户：请运行 tests/ 目录下的所有测试

Goose：好的，我将执行 tests/ 目录下的所有测试。
正在调用 run_pytest_tests 工具...
```

### 3.2 get_test_history - 获取测试历史记录

**描述**: 获取项目的测试历史记录

**参数**:
- `project_name` (可选): 项目名称
- `days` (可选): 查询天数，默认为 7
- `limit` (可选): 限制数量，默认为 50

**示例用法**:
```
用户：查看最近一周的测试历史

Goose：正在获取测试历史记录...
```

### 3.3 get_project_stats - 获取项目统计信息

**描述**: 获取项目的测试统计信息

**参数**:
- `project_name` (必需): 项目名称
- `days` (可选): 统计天数，默认为 30

**示例用法**:
```
用户：查看 my_project 项目的测试统计

Goose：正在获取 my_project 项目的统计信息...
```

### 3.4 get_test_run_details - 获取测试运行详情

**描述**: 获取特定测试运行的详细信息

**参数**:
- `run_id` (必需): 测试运行 ID

**示例用法**:
```
用户：查看测试运行 123 的详情

Goose：正在获取测试运行 123 的详细信息...
```

## 4. 高级集成

### 4.1 自定义工具提示

你可以在 Goose 配置中添加工具的描述，帮助 Goose 更好地理解何时使用这些工具：

```yaml
mcp_servers:
  pytest_test_server:
    command: "python"
    args: ["-m", "src.main"]
    tools:
      run_pytest_tests:
        description: "执行 pytest 测试并存储结果"
        usage_hints:
          - "当用户想要运行测试时"
          - "当用户提到 pytest 时"
          - "当用户需要执行自动化测试时"
```

### 4.2 集成到工作流中

你可以创建 Goose 工作流，将测试执行集成到开发流程中：

```yaml
# 工作流示例
workflows:
  test_and_report:
    steps:
      - name: "运行测试"
        tool: "run_pytest_tests"
        args:
          test_path: "tests/"
          project_name: "{{project}}"
      
      - name: "生成报告"
        tool: "get_project_stats"
        args:
          project_name: "{{project}}"
      
      - name: "通知结果"
        action: "notify"
        args:
          message: "测试完成！查看结果：{{results_url}}"
```

### 4.3 使用 Goose 扩展

你可以创建 Goose 扩展来增强测试功能：

```python
# goose_extension.py
from goose import Extension, Tool

class PytestExtension(Extension):
    """Pytest 测试扩展"""
    
    def __init__(self):
        super().__init__("pytest_tester")
    
    def setup(self, goose):
        # 注册自定义命令
        goose.register_command(
            "run-tests",
            self.run_tests,
            description="运行 pytest 测试"
        )
    
    async def run_tests(self, context, test_path=None):
        """运行测试命令"""
        if not test_path:
            test_path = context.get("test_path", "tests/")
        
        # 调用 MCP 工具
        result = await context.call_tool(
            "run_pytest_tests",
            test_path=test_path,
            project_name=context.project
        )
        
        return result
```

## 5. 故障排除

### 5.1 连接问题

**问题**: Goose 无法连接到 MCP 服务器

**解决方案**:
1. 确保 MCP 服务器正在运行：
   ```bash
   ./start.sh status
   ```

2. 检查端口是否被占用：
   ```bash
   lsof -i :8000
   ```

3. 验证 Goose 配置：
   ```bash
   goose config list
   ```

### 5.2 工具不可用

**问题**: Goose 看不到 MCP 工具

**解决方案**:
1. 检查 MCP 服务器日志：
   ```bash
   # 查看服务器输出
   ```

2. 手动测试 MCP 接口：
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```

3. 重新启动 Goose 和 MCP 服务器

### 5.3 测试执行失败

**问题**: 测试执行失败或没有结果

**解决方案**:
1. 检查 pytest 是否安装：
   ```bash
   pip list | grep pytest
   ```

2. 验证测试路径：
   ```bash
   ls -la tests/
   ```

3. 查看数据库连接：
   ```bash
   # 检查数据库文件
   ls -la test_results.db
   ```

## 6. 最佳实践

### 6.1 项目结构

```
my_project/
├── .goose/
│   └── config.yaml      # Goose 配置
├── mcp-pytest-server/   # MCP 服务器
├── tests/               # 测试文件
├── src/                 # 源代码
└── README.md
```

### 6.2 配置管理

使用环境变量管理配置：

```bash
# .env 文件
MCP_PYTEST_DATABASE_URL=sqlite:///./test_results.db
MCP_PYTEST_DEBUG=false
GOOSE_MCP_SERVERS='{"pytest_test_server": {"command": "python", "args": ["-m", "src.main"]}}'
```

### 6.3 监控和日志

启用详细日志以便调试：

```bash
# 启动 MCP 服务器时启用调试
./start.sh start 0.0.0.0 8000 true

# 查看日志
tail -f logs/server.log
```

## 7. 示例对话

### 7.1 基本测试执行

```
用户：帮我运行测试

Goose：我可以帮你运行 pytest 测试。请告诉我测试路径：

用户：tests/test_api.py

Goose：正在执行 tests/test_api.py 的测试...
（调用 run_pytest_tests 工具）

Goose：测试完成！
✓ 总测试数: 15
✓ 通过: 14
✗ 失败: 1
⏭ 跳过: 0
⏱ 耗时: 2.34秒
📊 成功率: 93.3%

失败的测试：
- test_user_login: AssertionError: Expected status 200, got 401
```

### 7.2 查看历史记录

```
用户：查看最近一周的测试结果

Goose：正在获取测试历史记录...
（调用 get_test_history 工具）

Goose：最近一周的测试历史：
1. 2024-01-15: 20/20 通过 (100%)
2. 2024-01-14: 18/20 通过 (90%)
3. 2024-01-13: 19/20 通过 (95%)
4. 2024-01-12: 20/20 通过 (100%)
5. 2024-01-11: 17/20 通过 (85%)
```

### 7.3 项目统计

```
用户：my_project 项目的测试统计如何？

Goose：正在获取 my_project 项目的统计信息...
（调用 get_project_stats 工具）

Goose：my_project 项目统计（最近30天）：
📈 总运行次数: 45
🧪 总测试用例: 900
✅ 通过: 855 (95%)
❌ 失败: 45 (5%)
⏭ 跳过: 0
⏱ 平均执行时间: 12.3秒
📊 平均成功率: 95%
📊 最近成功率: 96%
```

## 8. 总结

通过将 MCP Pytest 测试服务器集成到 Goose 中，你可以：

1. **自动化测试执行**: Goose 可以自动执行 pytest 测试
2. **结果存储**: 测试结果自动保存到数据库
3. **历史追踪**: 查看测试历史记录和趋势
4. **智能交互**: 通过自然语言与测试系统交互
5. **集成工作流**: 将测试集成到开发工作流中

这种集成大大提高了测试自动化的效率和便利性，使开发者能够更专注于编写代码而不是管理测试基础设施。