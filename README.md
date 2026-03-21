# MCP Pytest 测试服务器

一个基于 Model Context Protocol (MCP) 的测试执行服务器，支持执行 pytest 测试并将结果存储到 QA 平台数据库。

## 功能特性

- ✅ 支持 MCP 协议标准接口
- ✅ 执行 pytest 测试套件
- ✅ 解析测试结果并生成报告
- ✅ 将测试结果存储到数据库
- ✅ 提供工具调用接口供 Goose 使用
- ✅ 支持异步执行和进度跟踪

## 架构设计

```
mcp-pytest-server/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # FastAPI 主应用
│   ├── mcp/               # MCP 协议实现
│   ├── pytest_executor/   # pytest 执行器
│   ├── database/          # 数据库操作
│   └── tools/             # 工具定义
├── tests/                 # 测试代码
├── config/                # 配置文件
├── docs/                  # 文档
└── requirements.txt       # 依赖包
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `config/database.yaml` 配置数据库连接。

### 3. 启动服务器

```bash
python -m src.main
```

### 4. 在 Goose 中配置

在 Goose 配置中添加 MCP 服务器：

```yaml
mcp_servers:
  pytest_server:
    command: "python"
    args: ["-m", "src.main"]
    env:
      DATABASE_URL: "sqlite:///./test_results.db"
```

## API 接口

### MCP 标准接口

- `POST /initialize` - 初始化连接
- `POST /tools/list` - 列出可用工具
- `POST /tools/call` - 调用工具
- `POST /resources/list` - 列出资源
- `POST /resources/read` - 读取资源

### 自定义工具

1. **run_pytest_tests** - 执行 pytest 测试
   - 参数: `test_path` (测试路径), `options` (pytest 选项)
   - 返回: 测试执行结果和报告

2. **store_test_results** - 存储测试结果到数据库
   - 参数: `test_results` (测试结果数据)
   - 返回: 存储状态和记录ID

3. **get_test_history** - 获取历史测试记录
   - 参数: `limit` (限制数量), `project` (项目名称)
   - 返回: 历史测试记录列表

## 数据库设计

```sql
CREATE TABLE test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    test_path TEXT NOT NULL,
    total_tests INTEGER,
    passed INTEGER,
    failed INTEGER,
    skipped INTEGER,
    duration REAL,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    test_name TEXT NOT NULL,
    status TEXT,
    duration REAL,
    error_message TEXT,
    stack_trace TEXT,
    FOREIGN KEY (run_id) REFERENCES test_runs (id)
);
```

## 开发指南

### 添加新工具

1. 在 `src/tools/` 目录下创建新的工具模块
2. 实现工具函数并添加装饰器
3. 在 `src/tools/__init__.py` 中注册工具

### 扩展数据库模型

1. 在 `src/database/models.py` 中添加新模型
2. 更新数据库迁移脚本
3. 添加相应的 CRUD 操作

## 许可证

MIT License